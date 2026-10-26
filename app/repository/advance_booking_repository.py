
from sqlalchemy.orm import Session

from app.models.advance_booking_model import PreBookingAdvance
from app.models.building_model import Building



class AdvanceBookingRepository:

    # Check whether the building belongs to the owner.
    def get_booking_building_by_owner(
        self,
        db: Session,
        building_id: int,
        owner_id: int
    ):
        return (
            db.query(Building)
            .filter(
                Building.id == building_id,
                Building.owner_id == owner_id
            )
            .first()
        )

    # Create a new advance booking.
    def create_booking(
        self,
        db: Session,
        owner_id: int,
        building_id: int,
        booking_data: dict
    ):
        booking = PreBookingAdvance(
            owner_id=owner_id,
            building_id=building_id,
            **booking_data
        )

        db.add(booking)
        db.flush()

        return booking

    # Get all advance bookings for one building and owner.
    def get_bookings_by_building(
        self,
        db: Session,
        building_id: int,
        owner_id: int
    ):
        return (
            db.query(PreBookingAdvance)
            .filter(
                PreBookingAdvance.building_id == building_id,
                PreBookingAdvance.owner_id == owner_id
            )
            .order_by(
                PreBookingAdvance.booking_date.desc(),
                PreBookingAdvance.id.desc()
            )
            .all()
        )

    # Get one booking belonging to the owner.
    def get_booking_by_id(
        self,
        db: Session,
        booking_id: int,
        owner_id: int
    ):
        return (
            db.query(PreBookingAdvance)
            .filter(
                PreBookingAdvance.id == booking_id,
                PreBookingAdvance.owner_id == owner_id
            )
            .first()
        )

    # Update an existing booking.
    def update_booking(
        self,
        db: Session,
        booking: PreBookingAdvance,
        booking_data: dict
    ):
        for field, value in booking_data.items():
            setattr(booking, field, value)

        db.flush()

        return booking

    # Delete an existing booking.
    def delete_booking(
        self,
        db: Session,
        booking: PreBookingAdvance
    ):
        db.delete(booking)
        db.flush()


advance_booking_repository = AdvanceBookingRepository()
