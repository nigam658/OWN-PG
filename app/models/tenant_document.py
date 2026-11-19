from sqlalchemy import (
    Column, Integer, String, DateTime,
    ForeignKey, UniqueConstraint
)
from datetime import datetime

from app.database import Base


class TenantDocument(Base):
    __tablename__ = "tenant_documents"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )

    document_type = Column(String(30), nullable=False)

    front_file_key = Column(String(500), nullable=True)
    back_file_key = Column(String(500), nullable=True)

    consent_at = Column(DateTime, nullable=True)
    consent_version = Column(String(30), nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "document_type",
            name="uq_tenant_document_type"
        ),
    )