from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.building_services import building_service
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.building_schema import BuildingSetupRequest


router = APIRouter(
    prefix="/buildings",
    tags=["Buildings"]
)


@router.get("/my-buildings")
def get_my_buildings(db: Session = Depends(get_db), owner_id: int = Depends(get_current_user)):

    return building_service.get_owner_buildings(
        db=db,
        owner_id=owner_id
    )

@router.post("/quick_building_setup")
def quick_building_setup(setup_data: BuildingSetupRequest, db: Session = Depends(get_db), owner_id: int = Depends(get_current_user)):

    try:
        return building_service.quick_building_setup(
            db=db,
            owner_id=owner_id,
            setup_data=setup_data
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )