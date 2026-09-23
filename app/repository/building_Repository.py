from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.building_model import Building
from app.models.floor_model import Floor
from app.models.room_model import Room


class BuildingRepository:

    def get_buildings_by_owner_id(self, db: Session, owner_id: int):

        return (
            db.query(
                Building,
                func.count(Room.id).label("total_rooms")
            )
            .outerjoin(
                Floor,
                Floor.building_id == Building.id
            )
            .outerjoin(
                Room,
                (Room.floor_id == Floor.id) &
                (Room.is_active.is_(True))
            )
            .filter(Building.owner_id == owner_id)
            .group_by(Building.id)
            .all()
        )

    def create_building(self, db: Session, owner_id: int, name: str, address: str, city: str):

        building = Building(
            owner_id=owner_id,
            name=name,
            address=address,
            city=city
        )

        db.add(building)
        db.flush()

        return building



building_repository = BuildingRepository()