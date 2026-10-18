from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.payment_model import Payment
from app.models.monthlyrent_model import MonthlyRent
from app.models.bed_allocation_model import BedAllocation
from app.models.bed_model import Bed
from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building
from app.models.tenant_model import Tenant


class PaymentRepository:

    def create_payment(
        self,
        db: Session,
        monthly_rent_id: int,
        amount,
        payment_date
    ):
        # Create a record for the money actually collected.
        payment = Payment(
            monthly_rent_id=monthly_rent_id,
            amount=amount,
            payment_date=payment_date
        )

        db.add(payment)
        db.flush()

        return payment

    def get_current_month_collection(
        self,
        db: Session,
        building_id: int,
        start_date,
        end_date
    ):
        # Calculate rent collected during the current month.
        total = (
            db.query(
                func.coalesce(func.sum(Payment.amount), 0)
            )
            .join(
                MonthlyRent,
                Payment.monthly_rent_id == MonthlyRent.id
            )
            .join(
                BedAllocation,
                MonthlyRent.bed_allocation_id == BedAllocation.id
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
            .filter(
                Floor.building_id == building_id,
                Payment.payment_date >= start_date,
                Payment.payment_date < end_date
            )
            .scalar()
        )

        return total


    def get_building_payments_for_period(
        self,
        db: Session,
        owner_id: int,
        building_id: int,
        start_date: datetime,
        end_date: datetime,
    ):
        # Fetch each actual payment row, including partial payments.
        # payment_date is the timestamp already saved in the database.
        return (
            db.query(
                Payment.id.label("payment_id"),
                Payment.amount.label("amount"),
                Payment.payment_date.label("payment_date"),
                Tenant.id.label("tenant_id"),
                Tenant.full_name.label("tenant_name"),
            )
            .join(
                MonthlyRent,
                Payment.monthly_rent_id == MonthlyRent.id,
            )
            .join(
                BedAllocation,
                MonthlyRent.bed_allocation_id == BedAllocation.id,
            )
            .join(
                Bed,
                BedAllocation.bed_id == Bed.id,
            )
            .join(
                Room,
                Bed.room_id == Room.id,
            )
            .join(
                Floor,
                Room.floor_id == Floor.id,
            )
            .join(
                Building,
                Floor.building_id == Building.id,
            )
            .join(
                Tenant,
                BedAllocation.tenant_id == Tenant.id,
            )
            .filter(
                Building.id == building_id,
                Building.owner_id == owner_id,
                Payment.payment_date >= start_date,
                Payment.payment_date < end_date,
            )
            .order_by(Payment.payment_date.desc())
            .all()
        )

    def get_total_collected_for_period(
        self,
        db: Session,
        owner_id: int,
        building_id: int,
        start_date: datetime,
        end_date: datetime,
    ):
        # Sum individual payment records, not cumulative paid_amount.
        # This counts every partial payment exactly once.
        return (
            db.query(
                func.coalesce(func.sum(Payment.amount), 0)
            )
            .join(
                MonthlyRent,
                Payment.monthly_rent_id == MonthlyRent.id,
            )
            .join(
                BedAllocation,
                MonthlyRent.bed_allocation_id == BedAllocation.id,
            )
            .join(
                Bed,
                BedAllocation.bed_id == Bed.id,
            )
            .join(
                Room,
                Bed.room_id == Room.id,
            )
            .join(
                Floor,
                Room.floor_id == Floor.id,
            )
            .join(
                Building,
                Floor.building_id == Building.id,
            )
            .filter(
                Building.id == building_id,
                Building.owner_id == owner_id,
                Payment.payment_date >= start_date,
                Payment.payment_date < end_date,
            )
            .scalar()
        )


payment_repository = PaymentRepository()