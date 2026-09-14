from datetime import date
from sqlalchemy.orm import Session

from app.repository.bed_allocation_repository import bed_allocation_repository
from app.repository.monthlyRent_repository import monthly_rent_repository
from app.utils.date_utils import get_next_due_date

from app.schemas.monthlyRent_schema import CollectRentRequest
from app.schemas.monthlyRent_schema import DueRentResponse

from app.models.monthlyrent_model import MonthlyRentStatus


class MonthlyRentService:

    # Generate all missing monthly rent records for a building's
    # active and notice-period bed allocations.
    def generate_missing_rents_for_building(
        self,
        db: Session,
        owner_id: int,
        building_id: int
    ):

        # Get all active and notice-period bed allocations
        # that belong to this specific building.
        allocations = (
            bed_allocation_repository.get_active_allocations_by_building_id(
                db=db,
                owner_id=owner_id,
                building_id=building_id
            )
        )

        created_rents = []

        # Process each bed allocation separately.
        for allocation in allocations:

            # Get all monthly rent records already created
            # for this bed allocation.
            monthly_rents = (
                monthly_rent_repository.get_monthly_rents_by_allocation_id(
                    db=db,
                    bed_allocation_id=allocation.id
                )
            )

            # If there is no monthly rent record, skip this allocation.
            # The first monthly rent is created when the tenant is added.
            if not monthly_rents:
                continue

            # Get the latest existing rent due date.
            last_due_date = monthly_rents[-1].due_date

            # Keep creating missing monthly rent records
            # until the next due date is in the future.
            while True:

                # Calculate the next month's due date.
                next_due_date = get_next_due_date(
                    current_due_date=last_due_date,
                    original_rent_day=allocation.check_in_date.day
                )

                # If the next due date has not arrived yet,
                # there is nothing to create.
                if next_due_date > date.today():
                    break

                # Create the missing monthly rent record.
                new_monthly_rent = (
                    monthly_rent_repository.create_monthly_rent(
                        db=db,
                        bed_allocation_id=allocation.id,
                        due_date=next_due_date,
                        rent_amount=allocation.rent
                    )
                )

                # Keep track of newly created rent records.
                created_rents.append(new_monthly_rent)

                # Use the newly created due date to calculate
                # the following month's due date.
                last_due_date = next_due_date

        try:
            db.commit()
        except Exception:
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

        try:

            db.commit()

        except Exception:

            db.rollback()

            raise

        return {
            "success": True,
            "message": "Rent collected successfully."
        }

monthly_rent_service = MonthlyRentService()