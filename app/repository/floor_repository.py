from sqlalchemy.orm import Session

from app.models.floor_model import Floor
from app.models.building_model import Building


class FloorRepository:
    # for quick building setup
    def create_floor(self, db: Session, building_id: int, floor_number: int):

        floor = Floor(
            building_id=building_id,
            floor_number=floor_number
        )

        db.add(floor)
        db.flush()

        return floor

    # in building page showing floors 
    def get_floors_by_building_id(self, db: Session, building_id: int):
        return (
            db.query(Floor)
            .filter(Floor.building_id == building_id)
            .order_by(Floor.floor_number)
            .all()
        )

    def get_floor_by_id_and_owner_id(
        self,
        db: Session,
        floor_id: int,
        owner_id: int
    ):
        return (
            db.query(Floor)
            .join(Building, Floor.building_id == Building.id)
            .filter(
                Floor.id == floor_id,
                Building.owner_id == owner_id
            )
            .first()
        )


floor_repository = FloorRepository()