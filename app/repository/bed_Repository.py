from sqlalchemy.orm import Session
from sqlalchemy import func
 
from app.models.bed_model import Bed, BedStatus
from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building

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

bed_repository = BedRepository()