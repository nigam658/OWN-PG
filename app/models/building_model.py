from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey)
from app.utils.time import now_ist

from app.database import Base

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True)

    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)

    name = Column(String(100), nullable=False)

    address = Column(String(255), nullable=False)

    city = Column(String(100), nullable=False)

    created_at = Column(DateTime, default=now_ist, nullable=False)
    
    updated_at = Column(DateTime, default=now_ist, onupdate=now_ist, nullable=False)