from sqlalchemy.orm import Session
from sqlalchemy import func, and_
 
from app.models.bed_model import Bed, BedStatus
from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building
from app.models.bed_allocation_model import BedAllocation, AllocationStatus

class BedRepository:

    # beds are creating for quick building create
    def create_bed(self, db: Session, room_id: int, bed_number: str):

        bed = Bed(
            room_id=room_id,
            bed_number=bed_number
        )

        db.add(bed)
        db.flush()

        return bed
    
    # get how many beds in a room id
    def get_beds_number_by_room_id(self, db:Session, room_id : int):
        return (
            db.query(func.count(Bed.id))
            .filter(Bed.room_id == room_id)
            .scalar()
        )

    #fetch all beds using a room id
    def get_beds_by_room_id(self, db: Session, room_id):
        return (
            db.query(Bed).filter(Bed.room_id == room_id).all()
        )

    def get_active_bed_count_by_room_id(self, db: Session, room_id: int):
        return (
            db.query(Bed)
            .filter(
                Bed.room_id == room_id,
                Bed.status.in_([
                    BedStatus.AVAILABLE,
                    BedStatus.MAINTENANCE
                ])
            )
            .count()
        )

        
    # create new bed
    def create_new_bed(self, db: Session, room_id: int, bed_number: str):

        new_bed = Bed(
            room_id=room_id,
            bed_number=bed_number
        )

        db.add(new_bed)
        db.commit()
        db.refresh(new_bed)

        return new_bed

    # get bed for checking bed is exist or not , for create new tenant information
    def get_bed_by_id(self, db: Session, bed_id: int):
        return (
            db.query(Bed)
            .filter(Bed.id == bed_id)
            .first()
        )

    # check given bed id belongs to requested owner or not
    def is_bed_owned_by_owner(
        self,
        db: Session,
        bed_id: int,
        owner_id: int
    ):
        return (
            db.query(Bed)
            .join(Room, Bed.room_id == Room.id)
            .join(Floor, Room.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .filter(
                Bed.id == bed_id,
                Building.owner_id == owner_id
            )
            .first()
        )

    # delete bed / deactivate bed
    def deactivate_bed(self, db: Session, bed_id: int):

        bed = (
            db.query(Bed)
            .filter(Bed.id == bed_id)
            .first()
        )

        if not bed:
            return None

        bed.status = BedStatus.INACTIVE

        db.commit()
        db.refresh(bed)

        return bed

    # Fetch room beds in bed-number order.
    def get_beds_by_room_id_ordered(
        self,
        db: Session,
        room_id: int
    ):
        return (
            db.query(Bed)
            .filter(Bed.room_id == room_id)
            .order_by(Bed.bed_number)
            .all()
        )

    # Get the building ID of a bed.
    # Used only during tenant bed switching to make sure
    # the new bed belongs to the same building.
    def get_building_id_for_bed_switch(
        self,
        db: Session,
        bed_id: int
    ):
        return (
            db.query(Building.id)
            .join(Floor, Building.id == Floor.building_id)
            .join(Room, Floor.id == Room.floor_id)
            .join(Bed, Room.id == Bed.room_id)
            .filter(Bed.id == bed_id)
            .scalar()
        )


    
    # Get eligible empty beds for a building in one database query.
    # Only active floors, active rooms, and AVAILABLE/MAINTENANCE beds.
    # Exclude beds with an active tenant allocation.
    def get_empty_beds_by_building_id(
        self,
        db: Session,
        building_id: int,
        owner_id: int
    ):
        return (
            db.query(Bed, Room.room_number)
            .join(Room, Bed.room_id == Room.id)
            .join(Floor, Room.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .outerjoin(
                BedAllocation,
                and_(
                    BedAllocation.bed_id == Bed.id,
                    BedAllocation.status == AllocationStatus.ACTIVE
                )
            )
            .filter(
                # Only the requested building belonging to this owner.
                Building.id == building_id,
                Building.owner_id == owner_id,

                # Only active floors that haven't been soft-deleted.
                Floor.is_active.is_(True),
                Floor.deleted_at.is_(None),

                # Only active rooms that haven't been soft-deleted.
                Room.is_active.is_(True),
                Room.deleted_at.is_(None),

                # Exclude INACTIVE beds.
                Bed.status.in_([
                    BedStatus.AVAILABLE,
                    BedStatus.MAINTENANCE
                ]),

                # Exclude beds that have an active allocation.
                BedAllocation.id.is_(None)
            )
            .order_by(Room.room_number, Bed.bed_number)
            .all()
        )

bed_repository = BedRepository()