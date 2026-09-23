from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric
from datetime import datetime

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    # Links this payment to a specific monthly rent.
    monthly_rent_id = Column(
        Integer,
        ForeignKey("monthly_rents.id"),
        nullable=False
    )

    # Amount actually collected from the tenant.
    amount = Column(Numeric(10, 2), nullable=False)

    # Date and time when the owner collected the money.
    payment_date = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )