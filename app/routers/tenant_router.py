from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.tenant_schema import TenantCreate , TenantUpdate, SwitchTenantBed, VacatingUpdate
from app.services.tenant_service import tenant_service
from app.dependencies.auth_dependencies import get_current_user

router = APIRouter(
    prefix="/tenants",
    tags=["Tenant"]
)


# this router take all information of a tenant for create new tenant 
@router.post("/beds/{bed_id}/tenant")
def add_tenant_endpoint(bed_id: int, tenant_data : TenantCreate, db : Session = Depends(get_db),current_user = Depends(get_current_user)):
    
    result = tenant_service.add_tenant(
            db=db,
            bed_id=bed_id,
            tenant_data=tenant_data,
            owner_id=current_user
        )


    if not result["success"]:
        return {
            "exists": False,
            "message": result["message"]
        }

    tenant = result["tenant"]
    allocation = result["allocation"]

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
            "aadhaar_number": tenant.aadhaar_number
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


# this router edit/update tenant information
@router.put("/{tenant_id}/edit")
def edit_tenant_endpoint(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = tenant_service.update_tenant(
        db=db,
        tenant_id=tenant_id,
        tenant_data=tenant_data,
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

    return {
        "exists": True,
        "tenant": {
            "id": tenant.id,
            "full_name": tenant.full_name,
            "phone": tenant.phone,
            "gender": tenant.gender.value,
            "permanent_address": tenant.permanent_address,
            "emergency_contact_phone": tenant.emergency_contact_phone,
            "aadhaar_number": tenant.aadhaar_number
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
        "next_rent_date": result["next_rent_date"]

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