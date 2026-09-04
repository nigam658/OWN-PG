from sqlalchemy.orm import Session

from app.repository.building_Repository import building_repository
from app.schemas.building_schema import BuildingSetupRequest
from app.repository.floor_repository import floor_repository
from app.repository.room_Repository import room_repository
from app.repository.bed_Repository import bed_repository


class BuildingService:

    def get_owner_buildings(self, db: Session, owner_id: int ):

        buildings = building_repository.get_buildings_by_owner_id(db=db,owner_id=owner_id)

        if not buildings:
            return {
                "exists": False,
                "buildings": []
            }

        buildings_data = []

        for building, total_rooms in buildings:

            building_info = {
                "id": building.id,
                "name": building.name,
                "address": building.address,
                "city": building.city,
                "total_rooms": total_rooms
            }

            buildings_data.append(building_info)

        return {
            "exists": True,
            "buildings": buildings_data
        }

    def quick_building_setup(self, db: Session, owner_id: int, setup_data: BuildingSetupRequest):

        # Validate dependency rules
        if (
            setup_data.rooms_per_floor is not None
            and setup_data.number_of_floors is None
        ):
            raise ValueError(
                "Floors are required before creating rooms."
            )

        if (
            setup_data.beds_per_room is not None
            and setup_data.rooms_per_floor is None
        ):
            raise ValueError(
                "Rooms are required before creating beds."
            )


        try:

            # 1. Create Building
            building = building_repository.create_building(
                db=db,
                owner_id=owner_id,
                name=setup_data.name,
                address=setup_data.address,
                city=setup_data.city
            )


            # 2. Create Floors
            if setup_data.number_of_floors is not None:

                for floor_number in range(
                    setup_data.number_of_floors
                ):

                    floor = floor_repository.create_floor(
                        db=db,
                        building_id=building.id,
                        floor_number=floor_number
                    )


                    # 3. Create Rooms
                    if setup_data.rooms_per_floor is not None:

                        for room_index in range(
                            1,
                            setup_data.rooms_per_floor + 1
                        ):

                            room_number = (
                                f"{floor_number}{room_index:02d}"
                            )

                            room = room_repository.create_room(
                                db=db,
                                floor_id=floor.id,
                                room_number=room_number
                            )


                            # 4. Create Beds
                            if setup_data.beds_per_room is not None:

                                for bed_index in range(
                                    1,
                                    setup_data.beds_per_room + 1
                                ):

                                    bed_number = chr(
                                        ord("A") + bed_index - 1
                                    )

                                    bed_repository.create_bed(
                                        db=db,
                                        room_id=room.id,
                                        bed_number=bed_number
                                    )


            # 5. Everything succeeded

            db.commit()

            return {
                "message": "PG setup completed successfully.",
                "building_id": building.id
            }


        except Exception:

            db.rollback()

            raise

building_service = BuildingService()