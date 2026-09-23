from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth_dependencies import get_current_user
from app.database import get_db
from app.schemas.floor_schema import FloorCreateRequest
from app.services.floor_services import floor_service


router = APIRouter(
    prefix="/floors",
    tags=["Floors"]
)

# for building page we need avilable floors 
@router.get("/building/{building_id}")
def get_floors_by_building_id(building_id: int, db: Session = Depends(get_db), owner_id: int = Depends(get_current_user)):
    return floor_service.get_floors_by_building_id(
        db,
        building_id
    )


# Add or reuse floor
@router.post("/{building_id}")
def add_floor(
    building_id: int,
    request: FloorCreateRequest,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):
    return floor_service.add_floor(
        db=db,
        building_id=building_id,
        floor_number=request.floor_number,
        owner_id=owner_id
    )


# delete floor
@router.delete("/{floor_id}")
def delete_floor(floor_id: int, db: Session = Depends(get_db), owner_id: int = Depends(get_current_user)):

    return floor_service.delete_floor(
        db=db,
        floor_id=floor_id,
        owner_id=owner_id
    )