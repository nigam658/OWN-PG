from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth_dependencies import get_current_user
from app.database import get_db
from app.services.floor_services import floor_service


router = APIRouter(
    prefix="/floors",
    tags=["Floors"]
)

# for building page we need avilable floors 
@router.get("/building/{building_id}")
def get_floors_by_building_id(
    building_id: int,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):
    return floor_service.get_floors_by_building_id(
        db,
        building_id
    )