from  sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date

from app.models.monthlyrent_model import MonthlyRent, MonthlyRentStatus

from app.models.bed_allocation_model import BedAllocation, AllocationStatus
from app.models.tenant_model import Tenant
from app.models.bed_model import Bed
from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building

class MonthlyRentRepository:

    def create_monthly_rent( 
        self,
        db: Session,
        bed_allocation_id: int,
        due_date,
        rent_amount
    ):
        new_monthly_rent = MonthlyRent(
            bed_allocation_id=bed_allocation_id,
            due_date=due_date,
            rent_amount=rent_amount,
            paid_amount=0,
            status=MonthlyRentStatus.DUE
        )

        db.add(new_monthly_rent)
        db.flush()

        return new_monthly_rent 


    # Get all monthly rent records for a bed allocation
    def get_monthly_rents_by_allocation_id(
        self,
        db: Session,
        bed_allocation_id: int
    ):
        return (
            db.query(MonthlyRent)
            .filter(
                MonthlyRent.bed_allocation_id == bed_allocation_id
            )
            .order_by(MonthlyRent.due_date.asc())
            .all()
        )

    # Get a rent record for one specific allocation and billing month.
    # This helps us check whether the selected month already has rent.
    def get_monthly_rent_by_allocation_and_billing_month(
        self,
        db: Session,
        bed_allocation_id: int,
        billing_month: date
    ):
        # Normalize the requested date to the first day of its month.
        billing_month = billing_month.replace(day=1)

        return (
            db.query(MonthlyRent)
            .filter(
                MonthlyRent.bed_allocation_id == bed_allocation_id,
                MonthlyRent.billing_month == billing_month
            )
            .first()
        )

    # Get one monthly rent record that belongs to an owner
    def get_monthly_rent_by_id_and_owner(
        self,
        db: Session,
        monthly_rent_id: int,
        owner_id: int
    ):
        return (
            db.query(MonthlyRent)
            .join(
                BedAllocation,
                MonthlyRent.bed_allocation_id == BedAllocation.id
            )
            .join(
                Tenant,
                BedAllocation.tenant_id == Tenant.id
            )
            .filter(
                MonthlyRent.id == monthly_rent_id,
                Tenant.owner_id == owner_id
            )
            .first()
        )


    def get_due_monthly_rents_by_building(
        self,
        db: Session,
        owner_id: int,
        building_id: int,
        today: date
    ):
        return (
            db.query(
                MonthlyRent,
                Tenant.id.label("tenant_id"),
                Tenant.full_name.label("tenant_name"),
                Tenant.phone.label("phone"),
                Bed.id.label("bed_id"),
                Bed.bed_number.label("bed_number"),
                Room.room_number.label("room_number"),
            )
            .join(
                BedAllocation,
                MonthlyRent.bed_allocation_id == BedAllocation.id
            )
            .join(
                Tenant,
                BedAllocation.tenant_id == Tenant.id
            )
            .join(
                Bed,
                BedAllocation.bed_id == Bed.id
            )
            .join(
                Room,
                Bed.room_id == Room.id
            )
            .join(
                Floor,
                Room.floor_id == Floor.id
            )
            .join(
                Building,
                Floor.building_id == Building.id
            )
            .filter(
                # Security: building must belong to logged-in owner
                Building.owner_id == owner_id,

                # Only the requested building
                Building.id == building_id,

                # Only active allocations are included
                BedAllocation.status == AllocationStatus.ACTIVE,

                # Rent due date has arrived
                MonthlyRent.due_date <= today,

                # Exclude fully paid rent
                MonthlyRent.paid_amount < MonthlyRent.rent_amount
            )
            .order_by(MonthlyRent.due_date.desc())
            .all()
        )


    # Get the number of tenants in a room who currently have unpaid rent
    def get_unpaid_tenant_count_by_room_id(
        self,
        db: Session,
        room_id: int,
        today: date
    ):
        return (
            db.query(BedAllocation.tenant_id)
            .join(
                MonthlyRent,
                MonthlyRent.bed_allocation_id == BedAllocation.id
            )
            .join(
                Bed,
                BedAllocation.bed_id == Bed.id
            )
            .filter(
                Bed.room_id == room_id,

                # Tenant is active or in notice period
                BedAllocation.status.in_([
                    AllocationStatus.ACTIVE
                    
                ]),

                # Rent is due
                MonthlyRent.due_date <= today,

                # Rent is not fully paid
                MonthlyRent.paid_amount < MonthlyRent.rent_amount
            )
            .distinct()
            .count()
        )


monthly_rent_repository = MonthlyRentRepository()