from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,UniqueConstraint ,Enum)
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base


class TenantStatus(PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Gender(PyEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class Tenant(Base):
    __tablename__ = "tenants"
    

    id = Column(Integer, primary_key=True)

    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)

    full_name = Column(String(100), nullable=False)

    phone = Column(String(15), nullable=False)

    gender = Column(Enum(Gender),nullable=True)

    permanent_address = Column(String(500),nullable=True)

    emergency_contact_phone = Column(String(15),nullable=True)

    aadhaar_number = Column(String(12), nullable=True)

    # aadhaar_front = Column(String(255), nullable=True)

    # aadhaar_back = Column(String(255),nullable=True)

    # profile_photo = Column(String(255),nullable=True)

    # occupation = Column(String(100),nullable=True)

    # company_name = Column(String(100),nullable=True)

    status = Column(Enum(TenantStatus),default=TenantStatus.ACTIVE,nullable=False)

    created_at = Column(DateTime,default=datetime.utcnow,nullable=False)

    updated_at = Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)