from pydantic import BaseModel, Field, field_validator


class BuildingSetupRequest(BaseModel):

    name: str = Field(min_length=1, max_length=100)

    address: str = Field(min_length=1, max_length=255)

    city: str = Field(min_length=1, max_length=100)

    number_of_floors: int | None = Field(default=None, gt=0)

    rooms_per_floor: int | None = Field(default=None, gt=0)

    beds_per_room: int | None = Field(default=None, gt=0)

    @field_validator("name", "address", "city")
    @classmethod
    def validate_text_fields(cls, value: str):
        if not value.strip():
            raise ValueError("This field cannot contain only spaces.")

        return value.strip()