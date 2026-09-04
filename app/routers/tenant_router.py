from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.tenant_schema import TenantCreate , TenantUpdate
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
            "status": allocation.status.value
        }
    }