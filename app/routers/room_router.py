from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.room_services import room_service
from app.dependencies.auth_dependencies import get_current_user

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)

# search room
@router.get("/roomsearch")
def search_room_endpoint(room_number: str, db : Session = Depends(get_db), owner_id: int = Depends(get_current_user)):

    return room_service.search_room(
        db=db,
        room_number=room_number,
        owner_id=owner_id
    )

# this show all rooms in building page
@router.get("/floor/{floor_id}")
def get_rooms_by_floor_id(floor_id: int, db: Session = Depends(get_db), owner_id: int = Depends(get_current_user)):

    return room_service.get_rooms_by_floor_id(
        db,
        floor_id
    )

