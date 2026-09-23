from datetime import date

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.building_model import Building
from app.models.floor_model import Floor
from app.models.room_model import Room
from app.models.bed_model import BedStatus
from app.models.bed_allocation_model import AllocationStatus
from app.models.tenant_model import TenantStatus

from app.utils.time import now_ist

from app.repository.floor_repository import floor_repository
from app.repository.bed_Repository import bed_repository
from app.repository.bed_allocation_repository import bed_allocation_repository
from app.repository.tenant_repository import tenant_repository


class FloorService:

    def get_floors_by_building_id(self, db: Session, building_id: int):

        floors = floor_repository.get_floors_by_building_id(
            db,
            building_id
        )

        return [
            {
                "floor_id": floor.id,
                "floor_number": floor.floor_number
            }
            for floor in floors
            if floor.is_active
        ]

    def add_floor(self, db: Session, building_id: int, floor_number: int, owner_id: int):

        building = (
            db.query(Building)
            .filter(
                Building.id == building_id,
                Building.owner_id == owner_id
            )
            .first()
        )

        if building is None:
            raise HTTPException(
                status_code=404,
                detail="Building not found"
            )

        floor = (
            db.query(Floor)
            .filter(
                Floor.building_id == building_id,
                Floor.floor_number == floor_number
            )
            .first()
        )

        if floor and floor.is_active:
            raise HTTPException(
                status_code=400,
                detail="Floor already exists"
            )

        try:
            if floor:
                # Reuse deleted floor
                floor.is_active = True
                floor.deleted_at = None

            else:
                # Create new floor
                floor = Floor(
                    building_id=building_id,
                    floor_number=floor_number
                )
                db.add(floor)

            db.commit()
            db.refresh(floor)

            return floor

        except Exception:
            db.rollback()
            raise

    def delete_floor(self, db: Session, floor_id: int, owner_id: int):

        floor = floor_repository.get_floor_by_id_and_owner_id(
            db=db,
            floor_id=floor_id,
            owner_id=owner_id
        )

        if floor is None:
            raise HTTPException(
                status_code=404,
                detail="Floor not found"
            )

        if not floor.is_active:
            raise HTTPException(
                status_code=400,
                detail="Floor is already deleted"
            )

        try:
            rooms = (
                db.query(Room)
                .filter(Room.floor_id == floor.id)
                .all()
            )

            # 1. Check out all active tenants
            for room in rooms:

                allocations = (
                    bed_allocation_repository
                    .get_active_allocations_by_room_id(
                        db=db,
                        room_id=room.id
                    )
                )

                for allocation in allocations:

                    tenant = tenant_repository.get_tenant_by_id(
                        db=db,
                        tenant_id=allocation.tenant_id
                    )

                    if tenant is None:
                        raise HTTPException(
                            status_code=500,
                            detail="Tenant data is inconsistent"
                        )

                    allocation.status = AllocationStatus.CHECKED_OUT
                    allocation.actual_check_out_date = date.today()

                    # 2. Make tenant inactive
                    tenant.status = TenantStatus.INACTIVE

            # 3. Make all beds inactive
            for room in rooms:

                beds = bed_repository.get_beds_by_room_id(
                    db=db,
                    room_id=room.id
                )

                for bed in beds:
                    if bed.status != BedStatus.INACTIVE:
                        bed.status = BedStatus.INACTIVE

            # 4. Soft delete all rooms
            for room in rooms:

                if room.is_active:
                    room.is_active = False
                    room.deleted_at = now_ist()

            # 5. Soft delete floor
            floor.is_active = False
            floor.deleted_at = now_ist()

            # Save everything together
            db.commit()
            db.refresh(floor)

            return floor

        except Exception:
            db.rollback()
            raise


floor_service = FloorService()