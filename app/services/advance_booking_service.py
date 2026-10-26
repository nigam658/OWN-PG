
from sqlalchemy.orm import Session

from app.repository.advance_booking_repository import (
    advance_booking_repository
)
from app.schemas.building_schema import BuildingSetupRequest
from app.schemas.advance_booking_schema import (
    AdvanceBookingCreate,
    AdvanceBookingUpdate
)


class AdvanceBookingService:

    def create_booking(
        self,
        db: Session,
        owner_id: int,
        building_id: int,
        booking_data: AdvanceBookingCreate
    ):
        # Verify that the building belongs to the logged-in owner.
        building = advance_booking_repository.get_booking_building_by_owner(
            db=db,
            building_id=building_id,
            owner_id=owner_id
        )

        if not building:
            raise ValueError("Building not found or access denied.")

        try:
            booking = advance_booking_repository.create_booking(
                db=db,
                owner_id=owner_id,
                building_id=building_id,
                booking_data=booking_data.model_dump()
            )

            db.commit()
            db.refresh(booking)

            return booking

        except Exception:
            db.rollback()
            raise

    def get_bookings_by_building(
        self,
        db: Session,
        owner_id: int,
        building_id: int
    ):
        building = advance_booking_repository.get_booking_building_by_owner(
            db=db,
            building_id=building_id,
            owner_id=owner_id
        )

        if not building:
            raise ValueError("Building not found or access denied.")

        return advance_booking_repository.get_bookings_by_building(
            db=db,
            building_id=building_id,
            owner_id=owner_id
        )

    def update_booking(
        self,
        db: Session,
        owner_id: int,
        booking_id: int,
        booking_data: AdvanceBookingUpdate
    ):
        booking = advance_booking_repository.get_booking_by_id(
            db=db,
            booking_id=booking_id,
            owner_id=owner_id
        )

        if not booking:
            raise ValueError("Advance booking not found or access denied.")

        try:
            update_data = booking_data.model_dump(exclude_unset=True)

            advance_booking_repository.update_booking(
                db=db,
                booking=booking,
                booking_data=update_data
            )

            db.commit()
            db.refresh(booking)

            return booking

        except Exception:
            db.rollback()
            raise

    def delete_booking(
        self,
        db: Session,
        owner_id: int,
        booking_id: int
    ):
        booking = advance_booking_repository.get_booking_by_id(
            db=db,
            booking_id=booking_id,
            owner_id=owner_id
        )

        if not booking:
            raise ValueError("Advance booking not found or access denied.")

        try:
            advance_booking_repository.delete_booking(
                db=db,
                booking=booking
            )

            db.commit()

            return {"message": "Advance booking deleted successfully."}

        except Exception:
            db.rollback()
            raise


advance_booking_service = AdvanceBookingService()
