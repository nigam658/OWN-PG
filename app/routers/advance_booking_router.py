
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.services.advance_booking_service import advance_booking_service
from app.schemas.advance_booking_schema import (
    AdvanceBookingCreate,
    AdvanceBookingUpdate,
    AdvanceBookingResponse
)

router = APIRouter(
    prefix="/advance-bookings",
    tags=["Advance Bookings"]
)


@router.post(
    "/buildings/{building_id}",
    response_model=AdvanceBookingResponse
)
def create_advance_booking(
    building_id: int,
    booking_data: AdvanceBookingCreate,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):
    try:
        return advance_booking_service.create_booking(
            db=db,
            owner_id=owner_id,
            building_id=building_id,
            booking_data=booking_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/buildings/{building_id}",
    response_model=list[AdvanceBookingResponse]
)
def get_advance_bookings(
    building_id: int,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):
    try:
        return advance_booking_service.get_bookings_by_building(
            db=db,
            owner_id=owner_id,
            building_id=building_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/{booking_id}",
    response_model=AdvanceBookingResponse
)
def update_advance_booking(
    booking_id: int,
    booking_data: AdvanceBookingUpdate,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):
    try:
        return advance_booking_service.update_booking(
            db=db,
            owner_id=owner_id,
            booking_id=booking_id,
            booking_data=booking_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{booking_id}")
def delete_advance_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):
    try:
        return advance_booking_service.delete_booking(
            db=db,
            owner_id=owner_id,
            booking_id=booking_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
