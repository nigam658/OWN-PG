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

                # Tenant must still be active or in notice period
                BedAllocation.status.in_([
                    AllocationStatus.ACTIVE,
                    AllocationStatus.NOTICE_PERIOD
                ]),

                # Rent due date has arrived
                MonthlyRent.due_date <= today,

                # Exclude fully paid rent
                MonthlyRent.paid_amount < MonthlyRent.rent_amount
            )
            .order_by(MonthlyRent.due_date.desc())
            .all()
        )


monthly_rent_repository = MonthlyRentRepository()