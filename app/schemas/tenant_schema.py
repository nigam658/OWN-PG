from datetime import date
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
import re

from app.models.tenant_model import Gender

class TenantCreate(BaseModel):
    # Required
    full_name: str = Field(min_length=1)
    phone: str = Field(min_length=10, max_length=15)

    # Optional
    gender: Gender | None = None
    permanent_address: str | None = None
    emergency_contact_phone: str | None = None
    aadhaar_number: str | None = None

    # Required allocation information
    check_in_date: date
    rent: Decimal

    # Optional
    security_deposit: Decimal = 0

    @field_validator("full_name", "phone")
    @classmethod
    def validate_required_text(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator(
        "permanent_address",
        "emergency_contact_phone",
        "aadhaar_number"
    )
    @classmethod
    def validate_optional_text(cls, value):
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value

    @field_validator("phone", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")

        return value

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, value):
        if value is None:
            return value

        if not value.isdigit():
            raise ValueError("Aadhaar number must contain only digits")

        return value



# this pydantic model used for update or edit a tabel
class TenantUpdate(BaseModel):

    # Tenant information
    full_name: str | None = None
    phone: str | None = None
    gender: Gender | None = None
    permanent_address: str | None = None
    emergency_contact_phone: str | None = None
    aadhaar_number: str | None = None

    # Allocation information
    check_in_date: date | None = None
    rent: Decimal | None = None
    security_deposit: Decimal | None = None

    @field_validator("full_name", "phone")
    @classmethod
    def validate_required_text(cls, value):

        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value


    @field_validator(
        "phone",
        "emergency_contact_phone",
        "aadhaar_number"
    )
    @classmethod
    def validate_digits(cls, value):

        if value is None or value == "":
            return value

        if not value.isdigit():
            raise ValueError("This field must contain only digits")

        return value