from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.monthlyrent_model import MonthlyRentStatus


class DueRentResponse(BaseModel):
    monthly_rent_id: int
    tenant_id: int
    tenant_name: str
    phone: str

    bed_id: int
    bed_number: str

    room_number: str

    due_date: date

    rent_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal

    status: MonthlyRentStatus


class CollectRentRequest(BaseModel):
    monthly_rent_id: int
    amount: Decimal = Field(gt=0)