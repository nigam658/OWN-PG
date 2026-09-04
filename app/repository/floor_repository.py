from sqlalchemy.orm import Session

from app.models.floor_model import Floor


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


floor_repository = FloorRepository()