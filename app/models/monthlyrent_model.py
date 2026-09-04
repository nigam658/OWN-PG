from sqlalchemy import (Column, Integer, Date, DateTime, ForeignKey, Numeric, UniqueConstraint, Enum,)
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base


class MonthlyRentStatus(PyEnum):
    DUE = "DUE"
    PARTIAL = "PARTIAL"
    PAID = "PAID"


class MonthlyRent(Base):
    __tablename__ = "monthly_rents"

    __table_args__ = (
        UniqueConstraint(
            "bed_allocation_id",
            "due_date",
            name="uq_bed_allocation_due_date",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    bed_allocation_id = Column(Integer,ForeignKey("bed_allocations.id"),nullable=False)

    due_date = Column(Date, nullable=False)

    rent_amount = Column(Numeric(10, 2), nullable=False)

    paid_amount = Column(Numeric(10, 2),default=0, nullable=False)

    status = Column(Enum(MonthlyRentStatus), default=MonthlyRentStatus.DUE, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updated_at = Column( DateTime, default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)