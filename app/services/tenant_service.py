from sqlalchemy.orm import Session
from datetime import date

from app.repository.tenant_repository import tenant_repository
from app.repository.bed_Repository import bed_repository
from app.schemas.tenant_schema import TenantUpdate
from app.repository.bed_allocation_repository import bed_allocation_repository
from app.models.tenant_model import TenantStatus
from app.models.bed_allocation_model import AllocationStatus
from app.models.bed_model import BedStatus


class TenantService:

    def add_tenant(self, db: Session, bed_id: int, tenant_data, owner_id : int ):

        # Check bed exists
        bed = bed_repository.get_bed_by_id(db, bed_id)

        if not bed:
            return {
                "success": False,
                "message": "Bed not found."
            }

        # Check bed belongs to owner
        owner_bed = bed_repository.is_bed_owned_by_owner(
            db=db,
            bed_id=bed_id,
            owner_id=owner_id
        )

        if not owner_bed:
            return {
                "success": False,
                "message": "You don't have permission to use this bed."
            }

        # Check bed is active
        if owner_bed.status == BedStatus.INACTIVE:
            return {
                "success": False,
                "message": "Cannot add tenant to an inactive bed."
            }


        # Check bed already has tenant
        allocation = bed_allocation_repository.get_active_allocation_by_bed_id(db=db, bed_id=bed_id)

        if allocation:
            return {
                "success": False,
                "message": "Bed already has a tenant."
            }

        # Check phone number is not already used by another active tenant
        existing_tenant = tenant_repository.get_active_tenant_by_phone(
            db=db,
            owner_id=owner_id,
            phone=tenant_data.phone
        )

        # if any duplciate numeber exist it will return friendly error message
        if existing_tenant:
            return {
                "success": False,
                "message": "Phone number is already used by another active tenant."
            }
        
        try :
            # Create tenant
            new_tenant = tenant_repository.create_tenant(db, tenant_data, owner_id)

            new_allocation = bed_allocation_repository.create_allocation(
                db=db,
                bed_id=bed_id,
                tenant_id=new_tenant.id,
                check_in_date=tenant_data.check_in_date,
                rent=tenant_data.rent,
                security_deposit=tenant_data.security_deposit
            )

            db.commit()

        except Exception:
            # Undo Tenant + BedAllocation changes
            db.rollback()
            raise


        return {
            "success": True,
            "message": "Tenant added successfully.",
            "tenant": new_tenant,
            "allocation": new_allocation
        }

    # this function is update all tenant information which is comes through edit endpoint 
    def update_tenant(self, db : Session,  tenant_id : int, tenant_data : TenantUpdate, owner_id: int ):

        tenant = tenant_repository.get_active_tenant_by_id_and_owner(
            db=db,
            tenant_id=tenant_id,
            owner_id=owner_id
        )

        if not tenant:
            return {
                "success": False,
                "message": "Active tenant not found."
            }

        # 2. Get only fields sent by frontend
        update_data = tenant_data.model_dump(exclude_unset=True)

        # Check whether frontend sent any data for update
        if not update_data:
            return {
                "success": False,
                "message": "No data provided for update."
            }
        
        # Check phone number only when frontend sends phone
        if "phone" in update_data:

            existing_tenant = tenant_repository.get_other_active_tenant_by_phone(
                db=db,
                owner_id=owner_id,
                phone=update_data["phone"],
                tenant_id=tenant_id
            )

            if existing_tenant:
                return {
                    "success": False,
                    "message": "Phone number is already used by another active tenant."
                }
            
        #  Fields that belong to Tenant table
        tenant_fields = {
            "full_name",
            "phone",
            "gender",
            "permanent_address",
            "emergency_contact_phone",
            "aadhaar_number"
        }

        # it will collect all updated data for tenant table , when for loop execute
        tenant_data_to_update = {}

    
        for key, value in update_data.items():

            if key in tenant_fields:
                tenant_data_to_update[key] = value


        # Fields that belong to bed_allocation table
        allocation_fields = {
            "check_in_date",
            "rent",
            "security_deposit"
        }

        # it will collect all updated data for bed_allocation table , when for loop execute
        allocation_data_to_update = {}

        
        for key, value in update_data.items():

            if  key in allocation_fields:
                allocation_data_to_update[key] = value 


        allocation = None

        if allocation_data_to_update:

            # Get current active allocation of this tenant
            allocation = bed_allocation_repository.get_active_allocation_by_tenant_id(
                db=db,
                tenant_id=tenant_id
            )

            if not allocation:
                return {
                    "success": False,
                    "message": "Active allocation not found."
                }

        try :
            if tenant_data_to_update:

                tenant_repository.update_tenant(
                    db=db,
                    tenant_id=tenant_id,
                    data=tenant_data_to_update
                )

            # update active bedallocation information
            if allocation_data_to_update:

                bed_allocation_repository.update_allocation(
                    db=db,
                    allocation_id=allocation.id,
                    data=allocation_data_to_update
                )
            # Save Tenant + BedAllocation changes together
            db.commit()

        except Exception:

            # Undo all changes if any update fails
            db.rollback()

            raise

        
        return {
            "success": True,
            "message": "Tenant updated successfully."
        }


    def remove_tenant(self, db: Session, tenant_id: int, owner_id: int):

        # Check tenant exists and belongs to owner
        tenant = tenant_repository.get_active_tenant_by_id(
            db=db,
            tenant_id=tenant_id,
            owner_id=owner_id
        )

        if not tenant:
            return {
                "success": False,
                "message": "Active tenant not found."
            }

        # Find active bed allocation
        allocation = bed_allocation_repository.get_active_allocation_by_tenant_id(
            db=db,
            tenant_id=tenant_id
        )

        if not allocation:
            return {
                "success": False,
                "message": "Active bed allocation not found."
            }

        try:
            # Make tenant inactive
            tenant.status = TenantStatus.INACTIVE

            # Mark allocation as checked out
            allocation.status = AllocationStatus.CHECKED_OUT
            allocation.actual_check_out_date = date.today()

            # Commit both changes together
            db.commit()

            db.refresh(tenant)
            db.refresh(allocation)

        except Exception:
            db.rollback()
            raise

        return {
            "success": True,
            "message": "Tenant removed successfully.",
            "tenant": tenant,
            "allocation": allocation
        }

    # Get current tenant information of a bed
    def get_bed_tenant(
        self,
        db: Session,
        bed_id: int,
        owner_id: int
    ):

        # 1. Check whether this bed belongs to the owner
        bed = bed_repository.is_bed_owned_by_owner(
            db=db,
            bed_id=bed_id,
            owner_id=owner_id
        )

        if not bed:
            return {
                "success": False,
                "message": "Bed not found."
            }

        # 2. Find active allocation of this bed
        allocation = bed_allocation_repository.get_active_allocation_by_bed_id(
            db=db,
            bed_id=bed_id
        )

        if not allocation:
            return {
                "success": False,
                "message": "No active tenant found for this bed."
            }

        # 3. Get active tenant using tenant_id
        tenant = tenant_repository.get_active_tenant_by_id_and_owner(
            db=db,
            tenant_id=allocation.tenant_id,
            owner_id=owner_id
        )

        if not tenant:
            return {
                "success": False,
                "message": "Active tenant not found."
            }

        return {
            "success": True,
            "tenant": tenant,
            "allocation": allocation
        }

tenant_service = TenantService()