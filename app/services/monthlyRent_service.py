from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.bed_allocation_model import BedAllocation
from app.models.tenant_model import Tenant
from app.models.bed_model import Bed
from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building
from app.repository.bed_allocation_repository import bed_allocation_repository
from app.repository.monthlyRent_repository import monthly_rent_repository
from app.repository.payment_repository import payment_repository
from app.utils.date_utils import get_next_due_date
from app.utils.time import now_ist

from app.schemas.monthlyRent_schema import CollectRentRequest
from app.schemas.monthlyRent_schema import DueRentResponse

from app.models.monthlyrent_model import MonthlyRentStatus


class MonthlyRentService:


    def generate_missing_rents_for_building(
        self,
        db: Session,
        owner_id: int,
        building_id: int
    ):
        # Get all active allocations in this building.
        allocations = (
            bed_allocation_repository.get_active_allocations_by_building_id(
                db=db,
                owner_id=owner_id,
                building_id=building_id
            )
        )

        created_rents = []
        today = date.today()

        try:
            # Process each allocation separately.
            for allocation in allocations:

                # Skip automatic generation for tenants marked as vacating.
                if allocation.is_vacating:
                    continue

                # Do not generate rent before the check-in date.
                if allocation.check_in_date > today:
                    continue

                # Fetch all existing rent records for this allocation.
                existing_rents = (
                    monthly_rent_repository.get_monthly_rents_by_allocation_id(
                        db=db,
                        bed_allocation_id=allocation.id
                    )
                )

                # Store the calendar months that already have rent records.
                existing_months = {
                    rent.billing_month for rent in existing_rents
                }

                # Start from the original check-in date.
                expected_due_date = allocation.check_in_date

                # Check every expected billing month up to today.
                while expected_due_date <= today:

                    # Identify the calendar month for this rent.
                    billing_month = expected_due_date.replace(day=1)

                    # Create a rent only when that month is missing.
                    if billing_month not in existing_months:

                        new_rent = (
                            monthly_rent_repository.create_monthly_rent(
                                db=db,
                                bed_allocation_id=allocation.id,
                                due_date=expected_due_date,
                                rent_amount=allocation.rent
                            )
                        )

                        # Record the newly created rent.
                        created_rents.append(new_rent)

                        # Mark the month as handled.
                        existing_months.add(billing_month)

                    # Move to the next month's due date while preserving
                    # the original rent day (including the 31st).
                    expected_due_date = get_next_due_date(
                        current_due_date=expected_due_date,
                        original_rent_day=allocation.check_in_date.day
                    )

            # Save newly created rents.
            db.commit()

        except Exception:
            # Undo this transaction if an error occurs.
            db.rollback()
            raise

        return created_rents



    # Get all unpaid and partially paid rent records
    # that belong to the logged-in owner and specific building.
    def get_building_due_rents(self, db: Session, owner_id: int, building_id: int):

        # First make sure all monthly rent records
        # that should already exist have been created.
        self.generate_missing_rents_for_building(
            db=db,
            owner_id=owner_id,
            building_id=building_id
        )

        # Get only rents that are due and not fully paid.
        # The repository also checks that the tenant belongs
        # to this owner and the allocation is still active
        # or in notice period.
        due_rents = (
            monthly_rent_repository.get_due_monthly_rents_by_building(
                db=db,
                owner_id=owner_id,
                building_id=building_id,
                today=date.today()
            )
        )

        response = []

        # Convert each database result into
        # the response format required by frontend.
        for row in due_rents:

            monthly_rent = row[0]

            # Calculate how much money is still remaining.
            remaining_amount = (
                monthly_rent.rent_amount
                - monthly_rent.paid_amount
            )

            response.append(
                DueRentResponse(
                    monthly_rent_id=monthly_rent.id,
                    tenant_id=row.tenant_id,
                    tenant_name=row.tenant_name,
                    phone=row.phone,
                    bed_id=row.bed_id,
                    bed_number=row.bed_number,
                    room_number=row.room_number,
                    due_date=monthly_rent.due_date,
                    rent_amount=monthly_rent.rent_amount,
                    paid_amount=monthly_rent.paid_amount,
                    remaining_amount=remaining_amount,
                    status=monthly_rent.status
                )
            )

        return response

    # Collect rent from a tenant for a specific monthly rent record.
    def collect_rent(
        self,
        db: Session,
        owner_id: int,
        rent_data: CollectRentRequest
    ):

        # Get the monthly rent and make sure
        # it belongs to the logged-in owner.
        monthly_rent = (
            monthly_rent_repository.get_monthly_rent_by_id_and_owner(
                db=db,
                monthly_rent_id=rent_data.monthly_rent_id,
                owner_id=owner_id
            )
        )

        if not monthly_rent:
            return {
                "success": False,
                "message": "Monthly rent not found."
            }

        # Don't allow payment for an already paid rent.
        if monthly_rent.status == MonthlyRentStatus.PAID:
            return {
                "success": False,
                "message": "This rent is already fully paid."
            }

        # Calculate how much is still remaining.
        remaining_amount = (
            monthly_rent.rent_amount
            - monthly_rent.paid_amount
        )

        # Don't allow collecting more than the remaining rent.
        if rent_data.amount > remaining_amount:
            return {
                "success": False,
                "message": "Collection amount cannot be greater than remaining rent."
            }

        # Add the newly collected amount.
        monthly_rent.paid_amount += rent_data.amount

        # Determine the new payment status.
        if monthly_rent.paid_amount == monthly_rent.rent_amount:

            monthly_rent.status = MonthlyRentStatus.PAID

        else:

            monthly_rent.status = MonthlyRentStatus.PARTIAL

        # Record the actual money collected.
        payment_repository.create_payment(
            db=db,
            monthly_rent_id=monthly_rent.id,
            amount=rent_data.amount,
            payment_date=now_ist()
        )


        try:

            db.commit()

        except Exception:

            db.rollback()

            raise

        return {
            "success": True,
            "message": "Rent collected successfully."
        }


    def get_current_month_collection(
        self,
        db: Session,
        owner_id: int,
        building_id: int
    ):
        # Make sure the building belongs to the logged-in owner.
        building = (
            db.query(Building)
            .filter(
                Building.id == building_id,
                Building.owner_id == owner_id
            )
            .first()
        )

        if building is None:
            raise HTTPException(
                status_code=404,
                detail="Building not found"
            )

        # Get the first day of the current month.
        today = date.today()
        start_date = today.replace(day=1)

        # Get the first day of the next month.
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1)
        else:
            end_date = date(today.year, today.month + 1, 1)

        # Get actual rent money collected for this building.
        total_collected = payment_repository.get_current_month_collection(
            db=db,
            building_id=building_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "building_id": building_id,
            "total_collected": total_collected
        }


    def get_missing_rent_months(
        self,
        db: Session,
        owner_id: int,
        tenant_id: int
    ):
        # Get the tenant's active allocation.
        # The owner check is performed separately below.
        allocation = (
            bed_allocation_repository.get_active_allocation_by_tenant_id(
                db=db,
                tenant_id=tenant_id
            )
        )

        if allocation is None:
            raise HTTPException(
                status_code=404,
                detail="Active tenant allocation not found."
            )

        # Manual rent generation is allowed only for tenants
        # who have been marked as vacating.
        if not allocation.is_vacating:
            raise HTTPException(
                status_code=400,
                detail="Manual rent generation is allowed only for vacating tenants."
            )

        # Validate that this allocation belongs to the logged-in owner.
        # Join through the tenant and building to prevent cross-owner access.
        allocation_belongs_to_owner = (
            db.query(BedAllocation.id)
            .join(Tenant, BedAllocation.tenant_id == Tenant.id)
            .join(Bed, BedAllocation.bed_id == Bed.id)
            .join(Room, Bed.room_id == Room.id)
            .join(Floor, Room.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .filter(
                BedAllocation.id == allocation.id,
                Tenant.owner_id == owner_id,
                Building.owner_id == owner_id
            )
            .first()
        )

        if allocation_belongs_to_owner is None:
            raise HTTPException(
                status_code=404,
                detail="Tenant allocation not found."
            )

        # Use the application's IST date for due-date validation.
        today = now_ist().date()

        # A future check-in date must not produce any rent months.
        if allocation.check_in_date > today:
            return {
                "tenant_id": tenant_id,
                "missing_count": 0,
                "missing_months": []
            }

        # Retrieve all existing rent records for this allocation.
        existing_rents = (
            monthly_rent_repository.get_monthly_rents_by_allocation_id(
                db=db,
                bed_allocation_id=allocation.id
            )
        )

        # Use the complete year and month to identify existing billing months.
        existing_months = {
            rent.billing_month for rent in existing_rents
        }

        # Determine the final month that can be considered.
        # Never return months after the current month.
        last_allowed_month = today.replace(day=1)

        # Start with the original check-in date so the rent day is preserved.
        expected_due_date = allocation.check_in_date
        missing_months = []

        # Calculate missing billing months across year boundaries.
        while expected_due_date.replace(day=1) <= last_allowed_month:

            billing_month = expected_due_date.replace(day=1)

            # Only return months whose actual due date has arrived
            # and which do not already have a rent record.
            if (
                expected_due_date <= today
                and billing_month not in existing_months
            ):
                missing_months.append({
                    "billing_month": billing_month,
                    "due_date": expected_due_date,
                    "rent_amount": allocation.rent
                })

            # Advance to the next month while preserving the original rent day.
            expected_due_date = get_next_due_date(
                current_due_date=expected_due_date,
                original_rent_day=allocation.check_in_date.day
            )

        return {
            "tenant_id": tenant_id,
            "missing_count": len(missing_months),
            "missing_months": missing_months
        }


    def generate_selected_missing_rent(
        self,
        db: Session,
        owner_id: int,
        tenant_id: int,
        billing_month: date
    ):
        # Normalize the selected billing month to its first day.
        billing_month = billing_month.replace(day=1)

        # Find the tenant's active allocation.
        allocation = (
            bed_allocation_repository.get_active_allocation_by_tenant_id(
                db=db,
                tenant_id=tenant_id
            )
        )

        if allocation is None:
            raise HTTPException(
                status_code=404,
                detail="Active tenant allocation not found."
            )

        # Only tenants marked as vacating can use manual rent generation.
        if not allocation.is_vacating:
            raise HTTPException(
                status_code=400,
                detail="Manual rent generation is allowed only for vacating tenants."
            )

        # Verify that both the tenant and building belong to this owner.
        allocation_belongs_to_owner = (
            db.query(BedAllocation.id)
            .join(Tenant, BedAllocation.tenant_id == Tenant.id)
            .join(Bed, BedAllocation.bed_id == Bed.id)
            .join(Room, Bed.room_id == Room.id)
            .join(Floor, Room.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .filter(
                BedAllocation.id == allocation.id,
                Tenant.owner_id == owner_id,
                Building.owner_id == owner_id
            )
            .first()
        )

        if allocation_belongs_to_owner is None:
            raise HTTPException(
                status_code=404,
                detail="Tenant allocation not found."
            )

        # Use the application's IST date for due-date validation.
        today = now_ist().date()

        # Reject tenants whose check-in date is still in the future.
        if allocation.check_in_date > today:
            raise HTTPException(
                status_code=400,
                detail="Rent cannot be generated before the tenant's check-in date."
            )

        # Recalculate the expected due date from the original check-in date.
        expected_due_date = allocation.check_in_date

        while expected_due_date.replace(day=1) < billing_month:
            expected_due_date = get_next_due_date(
                current_due_date=expected_due_date,
                original_rent_day=allocation.check_in_date.day
            )

        # The selected month must match an actual expected due date.
        if expected_due_date.replace(day=1) != billing_month:
            raise HTTPException(
                status_code=400,
                detail="The selected billing month is not valid for this tenant."
            )

        # Do not generate rent before its expected due date arrives.
        if expected_due_date > today:
            raise HTTPException(
                status_code=400,
                detail="Rent cannot be generated before its due date."
            )

        # Check whether rent already exists for this allocation and month.
        existing_rent = (
            monthly_rent_repository
            .get_monthly_rent_by_allocation_and_billing_month(
                db=db,
                bed_allocation_id=allocation.id,
                billing_month=billing_month
            )
        )

        if existing_rent is not None:
            raise HTTPException(
                status_code=409,
                detail="Rent already exists for the selected month."
            )

        try:
            # Create exactly one rent record for the selected month.
            monthly_rent_repository.create_monthly_rent(
                db=db,
                bed_allocation_id=allocation.id,
                due_date=expected_due_date,
                rent_amount=allocation.rent
            )

            # Save the newly created rent record.
            db.commit()

            return {
                "success": True,
                "message": "Rent generated successfully.",
                "tenant_id": tenant_id,
                "billing_month": billing_month,
                "due_date": expected_due_date,
                "rent_amount": allocation.rent
            }

        except Exception as exc:
            # Roll back any incomplete transaction if creation fails.
            db.rollback()

            # Preserve FastAPI validation errors.
            if isinstance(exc, HTTPException):
                raise

            # Log details on the server while returning a safe error.
            raise HTTPException(
                status_code=500,
                detail="Failed to generate rent. Please try again."
            ) from exc


    
    def get_building_payment_history(
        self,
        db: Session,
        owner_id: int,
        building_id: int
    ):
        # Verify that the selected building belongs to this owner.
        building = (
            db.query(Building)
            .filter(
                Building.id == building_id,
                Building.owner_id == owner_id
            )
            .first()
        )

        if building is None:
            raise HTTPException(
                status_code=404,
                detail="Building not found"
            )

        # Get the current date.
        today = date.today()

        # Start from the first day of the current month.
        start_date = today.replace(day=1)

        # Calculate the first day of the next month.
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1)
        else:
            end_date = date(today.year, today.month + 1, 1)

        # Fetch individual payments for this building and month.
        payments = payment_repository.get_building_payments_for_period(
            db=db,
            owner_id=owner_id,
            building_id=building_id,
            start_date=start_date,
            end_date=end_date
        )

        # Calculate the total from actual payment transactions.
        total_collected = payment_repository.get_total_collected_for_period(
            db=db,
            owner_id=owner_id,
            building_id=building_id,
            start_date=start_date,
            end_date=end_date
        )

        # Convert query rows into API-friendly dictionaries.
        transactions = [
            {
                "payment_id": payment.payment_id,
                "tenant_id": payment.tenant_id,
                "tenant_name": payment.tenant_name,
                "amount": payment.amount,
                "payment_date": payment.payment_date,
            }
            for payment in payments
        ]

        return {
            "building_id": building_id,
            "month": start_date.strftime("%Y-%m"),
            "total_collected": total_collected,
            "transactions": transactions
        }


monthly_rent_service = MonthlyRentService()