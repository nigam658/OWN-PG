from sqlalchemy import (Column, Integer, Date, DateTime, ForeignKey, Numeric, Enum)
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base


class AllocationStatus(PyEnum):
    ACTIVE = "ACTIVE"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    CHECKED_OUT = "CHECKED_OUT"


class BedAllocation(Base):
    __tablename__ = "bed_allocations"

    id = Column(Integer, primary_key=True)

    bed_id = Column(Integer, ForeignKey("beds.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    check_in_date = Column(Date, nullable=False)
    expected_check_out_date = Column(Date, nullable=True)
    actual_check_out_date = Column(Date, nullable=True)

    rent = Column(Numeric(10, 2), nullable=False)
    security_deposit = Column(Numeric(10, 2), default=0, nullable=False)

    status = Column(Enum(AllocationStatus), default=AllocationStatus.ACTIVE, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)