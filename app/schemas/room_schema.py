from pydantic import BaseModel, Field

class SearchRoom(BaseModel):
    roomNUmber : str



class RoomCreate(BaseModel):
    floor_id: int
    room_number: str = Field(min_length=1, max_length=10)
    number_of_beds: int = Field(gt=0)