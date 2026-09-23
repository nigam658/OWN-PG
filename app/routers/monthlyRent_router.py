from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.monthlyRent_service import monthly_rent_service
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.monthlyRent_schema import DueRentResponse, CollectRentRequest


router = APIRouter(
    prefix="/monthly-rents",
    tags=["Monthly Rents"]
)


@router.get("/building/{building_id}/due", response_model=list[DueRentResponse])
def get_building_due_monthly_rents(building_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):

    owner_id = current_user

    due_rents = monthly_rent_service.get_building_due_rents(
        db=db,
        owner_id=owner_id,
        building_id=building_id
    )

    return due_rents


@router.post("/collect")
def collect_rent(
    rent_data: CollectRentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    owner_id = current_user

    result = monthly_rent_service.collect_rent(
        db=db,
        owner_id=owner_id,
        rent_data=rent_data
    )

    return result

# current month collected money dashboard
@router.get("/building/{building_id}/current-month-collection")
def get_current_month_collection(
    building_id: int,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):
    return monthly_rent_service.get_current_month_collection(
        db=db,
        owner_id=owner_id,
        building_id=building_id
    )