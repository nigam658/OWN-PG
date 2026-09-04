from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Numeric, UniqueConstraint, Enum)
from enum import Enum as PyEnum

from app.database import Base
from app.utils.time import now_ist

class BedStatus(PyEnum):
    AVAILABLE = "AVAILABLE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class Bed(Base):
    __tablename__ = "beds"

    __table_args__ = (
        UniqueConstraint("room_id", "bed_number", name="uq_room_bed"),
    )

    id = Column(Integer, primary_key=True)

    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)

    bed_number = Column(String(5), nullable=False)

    status = Column(Enum(BedStatus), default=BedStatus.AVAILABLE, nullable=False)

    created_at = Column(DateTime, default=now_ist,nullable=False  )

    updated_at = Column(DateTime, default=now_ist, onupdate=now_ist, nullable=False)