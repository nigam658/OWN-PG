from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.payment_model import Payment
from app.models.monthlyrent_model import MonthlyRent
from app.models.bed_allocation_model import BedAllocation
from app.models.bed_model import Bed
from app.models.room_model import Room
from app.models.floor_model import Floor


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


payment_repository = PaymentRepository()