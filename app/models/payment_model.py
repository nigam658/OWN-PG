from sqlalchemy import (Column, Integer, DateTime, ForeignKey, Numeric, String, Enum,)
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base


class PaymentMode(PyEnum):
    CASH = "CASH"
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(PyEnum):
    ACTIVE = "ACTIVE"
    VOID = "VOID"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    monthly_rent_id = Column(Integer, ForeignKey("monthly_rents.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)

    payment_mode = Column(Enum(PaymentMode), nullable=False)

    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    transaction_id = Column(String(100), nullable=True)

    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.ACTIVE, nullable=False)

    remarks = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)