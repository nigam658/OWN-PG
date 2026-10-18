from sqlalchemy.orm import Session
from datetime import date

from app.repository.tenant_repository import tenant_repository
from app.repository.bed_Repository import bed_repository
from app.schemas.tenant_schema import TenantUpdate
from app.repository.bed_allocation_repository import bed_allocation_repository
from app.models.tenant_model import TenantStatus
from app.models.bed_allocation_model import AllocationStatus
from app.models.bed_model import BedStatus
from app.repository.monthlyRent_repository import monthly_rent_repository
from app.utils.date_utils import get_next_due_date

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

            # Create bed allocation
            new_allocation = bed_allocation_repository.create_allocation(
                db=db,
                bed_id=bed_id,
                tenant_id=new_tenant.id,
                check_in_date=tenant_data.check_in_date,
                rent=tenant_data.rent,
                security_deposit=tenant_data.security_deposit
            )

            # Create the first monthly rent only when the tenant's
            # check-in date has arrived or has already passed.
            if tenant_data.check_in_date <= date.today():

                monthly_rent_repository.create_monthly_rent(
                    db=db,
                    bed_allocation_id=new_allocation.id,
                    due_date=tenant_data.check_in_date,
                    rent_amount=tenant_data.rent
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

        
        # Validate that the check-in date stays within its original month and year.
        if "check_in_date" in allocation_data_to_update:
            new_check_in_date = allocation_data_to_update["check_in_date"]

            # A check-in date cannot be empty.
            if new_check_in_date is None:
                return {
                    "success": False,
                    "message": "Check-in date cannot be empty."
                }

            # Get the currently saved check-in date as the reference.
            current_check_in_date = allocation.check_in_date

            # Reject any date belonging to a different month or year.
            if (
                new_check_in_date.month != current_check_in_date.month
                or new_check_in_date.year != current_check_in_date.year
            ):
                return {
                    "success": False,
                    "message": (
                        "Check-in date must remain within "
                        f"{current_check_in_date.strftime('%B %Y')}."
                    )
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


    # Switch an active tenant to another bed.
    #
    # Important:
    # - Only the BedAllocation.bed_id is changed.
    # - Tenant information is not changed.
    # - Check-in date is not changed.
    # - Rent is not changed.
    # - MonthlyRent is not changed.
    # - The new bed must belong to the same building.
    def switch_tenant_bed(self, db: Session, tenant_id: int, new_bed_id: int, owner_id: int):

        # 1. Check whether the tenant exists,
        #    is active, and belongs to the logged-in owner.
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

        # 2. Get the tenant's current active bed allocation.
        allocation = bed_allocation_repository.get_active_allocation_by_tenant_id(
            db=db,
            tenant_id=tenant_id
        )

        if not allocation:
            return {
                "success": False,
                "message": "Active bed allocation not found."
            }

        # 3. Prevent switching to the same bed.
        if allocation.bed_id == new_bed_id:
            return {
                "success": False,
                "message": "Tenant is already assigned to this bed."
            }

        # 4. Check whether the new bed exists.
        new_bed = bed_repository.get_bed_by_id(
            db=db,
            bed_id=new_bed_id
        )

        if not new_bed:
            return {
                "success": False,
                "message": "New bed not found."
            }

        # 5. Check that the new bed belongs to the logged-in owner.
        owner_bed = bed_repository.is_bed_owned_by_owner(
            db=db,
            bed_id=new_bed_id,
            owner_id=owner_id
        )

        if not owner_bed:
            return {
                "success": False,
                "message": "You don't have permission to use this bed."
            }

        # 6. The new bed must not be inactive.
        #
        # AVAILABLE      -> allowed
        # MAINTENANCE    -> allowed
        # INACTIVE       -> not allowed
        if new_bed.status == BedStatus.INACTIVE:
            return {
                "success": False,
                "message": "Cannot switch tenant to an inactive bed."
            }

        # 7. Check whether another active tenant
        #    is already using the new bed.
        existing_allocation = (
            bed_allocation_repository.get_active_allocation_by_bed_id(
                db=db,
                bed_id=new_bed_id
            )
        )

        if existing_allocation:
            return {
                "success": False,
                "message": "New bed already has a tenant."
            }

        # 8. Get the building of the current bed.
        current_building_id = bed_repository.get_building_id_for_bed_switch(
            db=db,
            bed_id=allocation.bed_id
        )

        # 9. Get the building of the new bed.
        new_building_id = bed_repository.get_building_id_for_bed_switch(
            db=db,
            bed_id=new_bed_id
        )

        # 10. Tenant can only be moved within the same building.
        if current_building_id != new_building_id:
            return {
                "success": False,
                "message": "Tenant can only be moved within the same building."
            }

        try:

            # Store the old bed ID before changing the allocation.
            old_bed_id = allocation.bed_id

            # 11. Change ONLY the bed assignment.
            allocation.bed_id = new_bed_id

            # 12. Commit the bed switch.
            #
            # Tenant, rent, check-in date, and MonthlyRent
            # remain unchanged.
            db.commit()

            # Refresh allocation so the returned object
            # contains the latest database values.
            db.refresh(allocation)

        except Exception:

            # Undo the bed switch if anything goes wrong.
            db.rollback()

            raise

        return {
            "success": True,
            "message": "Tenant bed switched successfully.",
            "old_bed_id": old_bed_id,
            "new_bed_id": new_bed_id,
            "allocation": allocation
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
                "message": "Tenant not found."
            }

        # Calculate the next scheduled rent date using the original
        # check-in day and the same billing rule as rent generation.
        today = date.today()
        next_rent_date = allocation.check_in_date

        # Find the first scheduled rent date strictly after today.
        while next_rent_date <= today:
            next_rent_date = get_next_due_date(
                current_due_date=next_rent_date,
                original_rent_day=allocation.check_in_date.day
            )

        return {
            "success": True,
            "tenant": tenant,
            "allocation": allocation,
            "next_rent_date": next_rent_date.isoformat()
        }
    

    
    # Mark an active tenant as vacating or cancel their vacating status.
    # This only updates the allocation flag; existing rents and payments
    # are never changed by this method.
    def set_tenant_vacating(
        self,
        db: Session,
        tenant_id: int,
        owner_id: int,
        is_vacating: bool,
        expected_checkout_date: date | None
    ):
        # Confirm the tenant exists, is active, and belongs to this owner.
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

        # Find the tenant's current active bed allocation.
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
            # Update only the vacating flag.
            allocation.is_vacating = is_vacating

            # Save or clear the expected checkout date.
            allocation.expected_check_out_date = (
                expected_checkout_date if is_vacating else None
            )

            # Save the change without modifying rents or payments.
            db.commit()
            db.refresh(allocation)

        except Exception:
            # Undo the change if saving fails.
            db.rollback()
            raise

        return {
            "success": True,
            "message": (
                "Tenant marked as vacating."
                if is_vacating
                else "Tenant vacating status cancelled."
            ),
            "tenant_id": tenant_id,
            "is_vacating": allocation.is_vacating,
            # Return the saved expected checkout date to the API.
            "expected_checkout_date": allocation.expected_check_out_date
        }



    def get_vacating_tenants_by_building(
        self,
        db: Session,
        building_id: int,
        owner_id: int,
    ):
        # Fetch vacating tenants for this owner and selected building.
        tenants = tenant_repository.get_vacating_tenants_by_building(
            db=db,
            building_id=building_id,
            owner_id=owner_id,
        )

        # Convert the database rows into dictionaries for the API response.
        return [
            {
                "tenant_id": tenant.tenant_id,
                "full_name": tenant.full_name,
                "phone": tenant.phone,
                "bed_id": tenant.bed_id,
                "room_number": tenant.room_number,
                "building_id": tenant.building_id,
                "building_name": tenant.building_name,
                "expected_checkout_date": (
                    tenant.expected_check_out_date.isoformat()
                    if tenant.expected_check_out_date
                    else None
                ),
            }
            for tenant in tenants
        ]


tenant_service = TenantService()