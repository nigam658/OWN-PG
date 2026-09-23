from pydantic import BaseModel, Field


class FloorCreateRequest(BaseModel):
    floor_number: int = Field(
        ge=0,
        le=20
    )