from sqlalchemy.orm import Session

from app.repository.floor_repository import floor_repository


class FloorService:

    def get_floors_by_building_id(self, db: Session, building_id: int):
        
        floors = floor_repository.get_floors_by_building_id(db, building_id)

        return [
            {
                "floor_id": floor.id,
                "floor_number": floor.floor_number
            }
            for floor in floors
        ]



floor_service = FloorService()