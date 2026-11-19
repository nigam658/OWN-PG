from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from sqlalchemy.orm import Session


from app.database import get_db
from app.cloudflare.image_validation_service import image_validation_service
from app.schemas.tenant_schema import TenantCreate , TenantUpdate, SwitchTenantBed, VacatingUpdate
from app.services.tenant_service import tenant_service
from app.dependencies.auth_dependencies import get_current_user
from pydantic import ValidationError
from datetime import date
from decimal import Decimal
from app.models.tenant_model import Gender

router = APIRouter(
    prefix="/tenants",
    tags=["Tenant"]
)



@router.post("/beds/{bed_id}/tenant")
async def add_tenant_endpoint(
    bed_id: int,

    # Tenant information
    full_name: str = Form(...),
    phone: str = Form(...),
    gender: Gender = Form(...),
    permanent_address: str | None = Form(None),
    emergency_contact_phone: str | None = Form(None),
    aadhaar_number: str | None = Form(None),
    check_in_date: date = Form(...),
    rent: Decimal = Form(...),
    security_deposit: Decimal = Form(...),

    # Optional images
    profile_photo: UploadFile | None = File(None),
    document_front: UploadFile | None = File(None),
    document_back: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Check which document sides were uploaded
    has_front = document_front is not None and bool(document_front.filename)
    has_back = document_back is not None and bool(document_back.filename)

    # --------------------------------
    # 1. Read and validate profile photo
    # --------------------------------
    profile_photo_bytes = None

    if profile_photo and profile_photo.filename:
        profile_photo_bytes = await profile_photo.read()

        image_validation_service.validate_image(profile_photo_bytes)

    # --------------------------------
    # 2. Read and validate front document
    # --------------------------------
    document_front_bytes = None

    if has_front:
        document_front_bytes = await document_front.read()

        image_validation_service.validate_image(document_front_bytes)

    # --------------------------------
    # 3. Read and validate back document
    # --------------------------------
    document_back_bytes = None

    if has_back:
        document_back_bytes = await document_back.read()

        image_validation_service.validate_image(document_back_bytes)

    # --------------------------------
    # 4. Create TenantCreate schema
    # --------------------------------
    try:
        tenant_data = TenantCreate(
            full_name=full_name,
            phone=phone,
            gender=gender,
            permanent_address=permanent_address,
            emergency_contact_phone=emergency_contact_phone,
            aadhaar_number=aadhaar_number,
            check_in_date=check_in_date,
            rent=rent,
            security_deposit=security_deposit
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    # --------------------------------
    # 5. Call tenant service
    # --------------------------------
    result = tenant_service.add_tenant(
        db=db,
        bed_id=bed_id,
        tenant_data=tenant_data,
        owner_id=current_user,
        profile_photo_bytes=profile_photo_bytes,
        document_front_bytes=document_front_bytes,
        document_back_bytes=document_back_bytes
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    tenant = result["tenant"]
    allocation = result["allocation"]

    # --------------------------------
    # 6. Return response
    # --------------------------------
    return {
        "exists": True,
        "message": "Tenant added successfully.",

        "tenant": {
            "id": tenant.id,
            "full_name": tenant.full_name,
            "phone": tenant.phone,
            "gender": tenant.gender.value,
            "permanent_address": tenant.permanent_address,
            "emergency_contact_phone": tenant.emergency_contact_phone,
            "aadhaar_number": tenant.aadhaar_number,

            "profile_photo_uploaded": bool(tenant.profile_photo_key),

            "document_uploaded": bool(
                document_front_bytes or document_back_bytes
            ),

            "document_front_uploaded": bool(document_front_bytes),
            "document_back_uploaded": bool(document_back_bytes)
        },

        "allocation": {
            "id": allocation.id,
            "bed_id": allocation.bed_id,
            "check_in_date": allocation.check_in_date,
            "rent": float(allocation.rent),
            "security_deposit": float(allocation.security_deposit),
            "status": allocation.status.value
        }
    }




# Edit tenant information and replace tenant images
@router.put("/{tenant_id}/edit")
async def edit_tenant_endpoint(
    tenant_id: int,

    # Existing TenantUpdate schema using multipart form data
    tenant_data: TenantUpdate = Depends(TenantUpdate.as_form),

    # Optional image uploads
    profile_photo: UploadFile | None = File(None),
    document_front: UploadFile | None = File(None),
    document_back: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. Read and validate profile photo
    profile_photo_bytes = None

    if profile_photo and profile_photo.filename:
        profile_photo_bytes = await profile_photo.read()

        image_validation_service.validate_image(
            profile_photo_bytes
        )

    # 2. Read and validate Aadhaar front
    document_front_bytes = None

    if document_front and document_front.filename:
        document_front_bytes = await document_front.read()

        image_validation_service.validate_image(
            document_front_bytes
        )

    # 3. Read and validate Aadhaar back
    document_back_bytes = None

    if document_back and document_back.filename:
        document_back_bytes = await document_back.read()

        image_validation_service.validate_image(
            document_back_bytes
        )

    # 4. Update tenant through existing service
    result = tenant_service.update_tenant(
        db=db,
        tenant_id=tenant_id,
        tenant_data=tenant_data,
        owner_id=current_user,
        profile_photo_bytes=profile_photo_bytes,
        document_front_bytes=document_front_bytes,
        document_back_bytes=document_back_bytes
    )

    # 5. Handle errors
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    # 6. Return response
    return {
        "exists": True,
        "message": result["message"]
    }



# Remove an active tenant
@router.delete("/{tenant_id}")
def remove_tenant_endpoint(tenant_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    result = tenant_service.remove_tenant(
        db=db,
        tenant_id=tenant_id,
        owner_id=current_user
    )

    if not result["success"]:
        return {
            "exists": False,
            "message": result["message"]
        }

    return {
        "exists": True,
        "message": result["message"]
    }


@router.patch("/{tenant_id}/bed")
def switch_tenant_bed(
    tenant_id: int,
    bed_data: SwitchTenantBed,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Switch an active tenant to another bed.

    The tenant remains the same.
    Only the bed assignment is changed.
    """

    result = tenant_service.switch_tenant_bed(
        db=db,
        tenant_id=tenant_id,
        new_bed_id=bed_data.bed_id,
        owner_id=current_user
    )

    return result


@router.get("/{bed_id}/tenant")
def get_bed_tenant_endpoint(
    bed_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = tenant_service.get_bed_tenant(
        db=db,
        bed_id=bed_id,
        owner_id=current_user
    )

    if not result["success"]:
        return {
            "exists": False,
            "message": result["message"]
        }

    tenant = result["tenant"]
    allocation = result["allocation"]
    profile_photo_url = result["profile_photo_url"]
    document_front_url = result["document_front_url"]
    document_back_url = result["document_back_url"]

    return {
        "exists": True,
        "tenant": {
            "id": tenant.id,
            "full_name": tenant.full_name,
            "phone": tenant.phone,
            "gender": tenant.gender.value,
            "permanent_address": tenant.permanent_address,
            "emergency_contact_phone": tenant.emergency_contact_phone,
            "aadhaar_number": tenant.aadhaar_number,
            "profile_photo_url": profile_photo_url
        },
        "allocation": {
            "id": allocation.id,
            "check_in_date": allocation.check_in_date,
            "rent": float(allocation.rent),
            "security_deposit": float(allocation.security_deposit),
            "status": allocation.status.value,
            # NEW: Tell the frontend whether this tenant is vacating.
            "is_vacating": allocation.is_vacating
        },

        # NEW: Provide the next scheduled rent date for the confirmation popup.
        "next_rent_date": result["next_rent_date"],
        "rent_history": result["rent_history"],
        "document_front_url": document_front_url,
        "document_back_url": document_back_url,

    }



# Mark a tenant as vacating or cancel their vacating status.
@router.patch("/{tenant_id}/vacating")
def set_tenant_vacating_endpoint(
    tenant_id: int,
    vacating_data: VacatingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Call the service with the tenant ID and owner's ID.
    result = tenant_service.set_tenant_vacating(
        db=db,
        tenant_id=tenant_id,
        owner_id=current_user,
        is_vacating=vacating_data.is_vacating,
        expected_checkout_date=vacating_data.expected_checkout_date
    )

    # Return an error response if the operation fails.
    if not result["success"]:
        return {
            "exists": False,
            "message": result["message"]
        }

    # Return the updated vacating status.
    return {
        "exists": True,
        "message": result["message"],
        "tenant_id": result["tenant_id"],
        "is_vacating": result["is_vacating"],
        "expected_checkout_date": result.get("expected_checkout_date")
    }



# Fetch vacating tenants for a selected building.
@router.get("/vacating/building/{building_id}")
def get_vacating_tenants_by_building_endpoint(
    building_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Fetch tenants using the authenticated owner's ID.
    tenants = tenant_service.get_vacating_tenants_by_building(
        db=db,
        building_id=building_id,
        owner_id=current_user,
    )

    # Return the tenants and their total count.
    return {
        "success": True,
        "building_id": building_id,
        "count": len(tenants),
        "tenants": tenants,
    }