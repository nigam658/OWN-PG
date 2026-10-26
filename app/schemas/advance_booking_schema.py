
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


# Request schema for creating an advance booking
class AdvanceBookingCreate(BaseModel):
    tenant_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=15)
    room_number: str = Field(min_length=1, max_length=10)
    booking_date: date
    advance_amount: Decimal | None = Field(default=None, ge=0)

    @field_validator("tenant_name", "room_number")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")

        if not 10 <= len(value) <= 15:
            raise ValueError("Phone number must contain 10 to 15 digits")

        return value


# Request schema for editing an existing advance booking
class AdvanceBookingUpdate(BaseModel):
    tenant_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=15)
    room_number: str | None = Field(default=None, min_length=1, max_length=10)
    booking_date: date | None = None
    advance_amount: Decimal | None = Field(default=None, ge=0)

    @field_validator("tenant_name", "room_number")
    @classmethod
    def validate_optional_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")

        if not 10 <= len(value) <= 15:
            raise ValueError("Phone number must contain 10 to 15 digits")

        return value


# Response schema for returning an advance booking
class AdvanceBookingResponse(BaseModel):
    id: int
    owner_id: int
    building_id: int
    tenant_name: str
    phone: str | None
    room_number: str
    booking_date: date
    advance_amount: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
