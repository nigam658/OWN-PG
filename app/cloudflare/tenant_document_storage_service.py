from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.tenant_model import Tenant
from app.models.tenant_document import TenantDocument
from app.cloudflare.r2_storage_service import r2_storage_service


class TenantDocumentStorageService:

    def upload_profile_photo(
        self,
        tenant: Tenant,
        file_bytes: bytes,
        uploaded_keys: list | None = None
    ) -> str:

        file_key = f"tenants/{tenant.id}/profile/{uuid4().hex}.jpg"

        if uploaded_keys is not None:
            uploaded_keys.append(file_key)

        r2_storage_service.upload_file(
            file_bytes=file_bytes,
            file_key=file_key,
            content_type="image/jpeg"
        )

        tenant.profile_photo_key = file_key

        return file_key

    def upload_document(
        self,
        db: Session,
        tenant_id: int,
        document_type: str,
        front_bytes: bytes | None = None,
        back_bytes: bytes | None = None,
        uploaded_keys: list | None = None,
        consent_at=None,
        consent_version: str | None = None
    ) -> dict:

        # At least one document side must be provided
        if not front_bytes and not back_bytes:
            raise ValueError(
                "At least one document image (front or back) is required."
            )

        # Check whether this document type already exists
        document = db.query(TenantDocument).filter(
            TenantDocument.tenant_id == tenant_id,
            TenantDocument.document_type == document_type
        ).first()

        if document:
            raise ValueError(
                "This document type already exists for this tenant."
            )

        document = TenantDocument(
            tenant_id=tenant_id,
            document_type=document_type
        )

        db.add(document)
        db.flush()

        front_key = None
        back_key = None

        # Generate keys only for uploaded sides
        if front_bytes:
            front_key = (
                f"tenants/{tenant_id}/documents/"
                f"{document_type}/{uuid4().hex}-front.jpg"
            )

        if back_bytes:
            back_key = (
                f"tenants/{tenant_id}/documents/"
                f"{document_type}/{uuid4().hex}-back.jpg"
            )

        try:
            # Upload front only when provided
            if front_bytes:
                if uploaded_keys is not None:
                    uploaded_keys.append(front_key)

                r2_storage_service.upload_file(
                    file_bytes=front_bytes,
                    file_key=front_key,
                    content_type="image/jpeg"
                )

                document.front_file_key = front_key

            # Upload back only when provided
            if back_bytes:
                if uploaded_keys is not None:
                    uploaded_keys.append(back_key)

                r2_storage_service.upload_file(
                    file_bytes=back_bytes,
                    file_key=back_key,
                    content_type="image/jpeg"
                )

                document.back_file_key = back_key

            document.consent_at = consent_at
            document.consent_version = consent_version

            db.flush()

            return {
                "document": document,
                "uploaded_keys": [
                    key for key in [front_key, back_key] if key
                ]
            }

        except Exception:
            # If no shared cleanup list was provided,
            # clean up uploaded objects here.
            if uploaded_keys is None:
                for file_key in [front_key, back_key]:
                    if file_key:
                        try:
                            r2_storage_service.delete_file(file_key)
                        except Exception:
                            pass

            raise


    
    def replace_profile_photo(
        self,
        tenant: Tenant,
        file_bytes: bytes,
        uploaded_keys: list
    ) -> str | None:

        old_key = tenant.profile_photo_key

        new_key = f"tenants/{tenant.id}/profile/{uuid4().hex}.jpg"

        uploaded_keys.append(new_key)

        r2_storage_service.upload_file(
            file_bytes=file_bytes,
            file_key=new_key,
            content_type="image/jpeg"
        )

        tenant.profile_photo_key = new_key

        return old_key

    def replace_document_image(
        self,
        db: Session,
        tenant_id: int,
        document_type: str,
        side: str,
        file_bytes: bytes,
        uploaded_keys: list
    ) -> str | None:

        document = db.query(TenantDocument).filter(
            TenantDocument.tenant_id == tenant_id,
            TenantDocument.document_type == document_type
        ).first()

        if not document:
            document = TenantDocument(
                tenant_id=tenant_id,
                document_type=document_type
            )

            db.add(document)
            db.flush()

        if side not in ("front", "back"):
            raise ValueError(
                "Document side must be front or back."
            )

        old_key = (
            document.front_file_key
            if side == "front"
            else document.back_file_key
        )

        new_key = (
            f"tenants/{tenant_id}/documents/"
            f"{document_type}/{uuid4().hex}-{side}.jpg"
        )

        uploaded_keys.append(new_key)

        r2_storage_service.upload_file(
            file_bytes=file_bytes,
            file_key=new_key,
            content_type="image/jpeg"
        )

        if side == "front":
            document.front_file_key = new_key
        else:
            document.back_file_key = new_key

        return old_key



tenant_document_storage_service = TenantDocumentStorageService()
