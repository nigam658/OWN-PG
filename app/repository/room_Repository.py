from sqlalchemy.orm import Session

from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building

class RoomRepository:

    #  for create building (quick setup)
    def create_room(self, db: Session, floor_id: int, room_number: str):

        room = Room(
            floor_id=floor_id,
            room_number=room_number
        )

        db.add(room)
        db.flush()

        return room

    # this fucntion used for checking when owner search any room , it check searched room exist or not 
    def get_room_by_number(self, db:Session, room_number:str, owner_id : int):
        return (
            db.query(Room)
            .join(Floor, Room.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .filter(
                Room.room_number == room_number,
                Building.owner_id == owner_id
            )
            .first()
        )

    def get_room_by_id_and_owner(self, db: Session, room_id: int, owner_id: int):
        return (
            db.query(Room)
            .join(
                Floor,
                Room.floor_id == Floor.id
            )
            .join(
                Building,
                Floor.building_id == Building.id
            )
            .filter(
                Room.id == room_id,
                Building.owner_id == owner_id
            )
            .first()
        )

    # showing rooms in building page 
    def get_rooms_by_floor_id(self, db: Session, floor_id: int):
        return (
            db.query(Room)
            .filter(Room.floor_id == floor_id)
            .order_by(Room.room_number)
            .all()
        )


    def get_room_for_owner(
        self,
        db: Session,
        room_id: int,
        owner_id: int
    ):
        # Get the room only if it belongs to the owner
        return (
            db.query(Room)
            .join(Floor, Room.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .filter(
                Room.id == room_id,
                Building.owner_id == owner_id
            )
            .first()
        )

room_repository = RoomRepository()