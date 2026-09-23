from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Boolean

from app.utils.time import now_ist
from app.database import Base


class Floor(Base):
    __tablename__ = "floors"

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "floor_number",
            name="uq_building_floor"
        ),
    )

    id = Column(Integer, primary_key=True) 

    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)

    floor_number = Column(Integer, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=now_ist, nullable=False)

    updated_at = Column(DateTime,default=now_ist, onupdate=now_ist, nullable=False)