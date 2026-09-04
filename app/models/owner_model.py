from sqlalchemy import Column, String, Integer, DateTime
from app.database import Base
from datetime import datetime

class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(225), unique=True, nullable=False)

    phone = Column(String(15), unique=True, nullable=False)

    password = Column(String(250), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)