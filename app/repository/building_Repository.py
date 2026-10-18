from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.building_model import Building
from app.models.floor_model import Floor
from app.models.room_model import Room
from app.models.bed_model import Bed, BedStatus
from app.models.bed_allocation_model import BedAllocation, AllocationStatus


class BuildingRepository:

    def get_buildings_by_owner_id(self, db: Session, owner_id: int):

        return (
            db.query(
                Building,

                # Count only active rooms.
                # DISTINCT is important because beds/allocations can
                # create multiple rows for the same room.
                func.count(
                    func.distinct(Room.id)
                ).label("total_rooms"),

                # Count only active beds.
                # AVAILABLE and MAINTENANCE are considered active beds.
                func.count(
                    func.distinct(
                        case(
                            (
                                Bed.status.in_([
                                    BedStatus.AVAILABLE,
                                    BedStatus.MAINTENANCE
                                ]),
                                Bed.id
                            )
                        )
                    )
                ).label("total_beds"),

                # Count occupied beds.
                # Vacating tenants remain ACTIVE until actual checkout,
                # so they continue to count as occupying their beds.
                func.count(
                    func.distinct(
                        case(
                            (
                                BedAllocation.status == AllocationStatus.ACTIVE,
                                Bed.id
                            )
                        )
                    )
                ).label("occupied_beds")
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

            .outerjoin(
                Bed,
                Bed.room_id == Room.id
            )

            .outerjoin(
                BedAllocation,
                BedAllocation.bed_id == Bed.id
            )

            .filter(
                Building.owner_id == owner_id
            )

            .group_by(
                Building.id
            )

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