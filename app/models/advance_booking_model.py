from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric

from app.database import Base
from app.utils.time import now_ist


class PreBookingAdvance(Base):
    __tablename__ = "advance_bookings"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(
        Integer,
        ForeignKey("owners.id"),
        nullable=False,
        index=True
    )

    building_id = Column(
        Integer,
        ForeignKey("buildings.id"),
        nullable=False,
        index=True
    )

    tenant_name = Column(String(100), nullable=False)

    phone = Column(String(15), nullable=True)

    room_number = Column(String(10), nullable=False)

    booking_date = Column(Date, nullable=False)

    advance_amount = Column(Numeric(10, 2), nullable=True)

    created_at = Column(DateTime, default=now_ist, nullable=False)

    updated_at = Column(
        DateTime,
        default=now_ist,
        onupdate=now_ist,
        nullable=False
    )
