from sqlalchemy import (Column, Integer, DateTime,String, ForeignKey, UniqueConstraint, Boolean)
from app.utils.time import now_ist
 
from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    __table_args__ = (
        UniqueConstraint(
            "floor_id",
            "room_number",
            name="uq_floor_room"
        ),
    )

    id = Column(Integer, primary_key=True)

    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=False)

    room_number = Column(String(10), nullable=False)

    is_active = Column( Boolean, default=True, nullable=False ) 

    deleted_at = Column( DateTime, nullable=True )

    created_at = Column(DateTime, default=now_ist, nullable=False)

    updated_at = Column(DateTime, default=now_ist, onupdate=now_ist, nullable=False)