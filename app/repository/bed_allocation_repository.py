from sqlalchemy.orm import Session
from sqlalchemy import update

from app.models.bed_allocation_model import (
    BedAllocation,
    AllocationStatus
)

from app.models.tenant_model import Tenant
from app.models.bed_model import Bed
from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building

class BedAllocationRepository:

    def get_active_allocation_by_bed_id(self, db: Session, bed_id: int):
        return (
            db.query(BedAllocation)
            .filter(
                BedAllocation.bed_id == bed_id,           
                BedAllocation.status == AllocationStatus.ACTIVE
            )
            .first()
        )

    def create_allocation( self, db: Session, bed_id: int, tenant_id: int, check_in_date, rent, security_deposit):
            new_allocation = BedAllocation(
                bed_id=bed_id,
                tenant_id=tenant_id,
                check_in_date=check_in_date,
                rent=rent,
                security_deposit=security_deposit
            )
    
            db.add(new_allocation)
            db.flush()
    
            return new_allocation

    # Get active allocation using tenant id
    def get_active_allocation_by_tenant_id(self, db: Session, tenant_id: int):
        
        return (
            db.query(BedAllocation)
            .filter(
                BedAllocation.tenant_id == tenant_id,
                BedAllocation.status == AllocationStatus.ACTIVE
            )
            .first()
        )
    
    def update_allocation(self, db: Session, allocation_id: int, data: dict):

        update_query = (
            update(BedAllocation)
            .where(BedAllocation.id == allocation_id)
            .values(**data)
        )

        db.execute(update_query)

    # Get active allocation using bed id
    def get_active_allocation_by_bed_id(self, db: Session, bed_id: int):
        return (
            db.query(BedAllocation)
            .filter(
                BedAllocation.bed_id == bed_id,
                BedAllocation.status == AllocationStatus.ACTIVE
            )
            .first()
        )

    # Get the number of beds in a room that currently have an active allocation
    def get_active_allocation_count_by_room_id(
        self,
        db: Session,
        room_id: int
    ):
        return (
            db.query(BedAllocation)
            .join(Bed, BedAllocation.bed_id == Bed.id)
            .filter(
                Bed.room_id == room_id,
                BedAllocation.status == AllocationStatus.ACTIVE
            )
            .count()
        )


    # using for delete room
    # Get active allocations for a room.
    def get_active_allocations_by_room_id(
        self,
        db: Session,
        room_id: int
    ):
        return (
            db.query(BedAllocation)

            # Join beds to filter by room.
            .join(
                Bed,
                BedAllocation.bed_id == Bed.id
            )

            # Get only active allocations.
            .filter(
                Bed.room_id == room_id,
                BedAllocation.status == AllocationStatus.ACTIVE
            )

            .all()
        )


    # Get active bed allocations for a specific building
    # owned by the logged-in owner.
    def get_active_allocations_by_building_id(
        self,
        db: Session,
        owner_id: int,
        building_id: int
    ):
        return (
            db.query(BedAllocation)
            .join(Tenant, BedAllocation.tenant_id == Tenant.id)
            .join(Bed, BedAllocation.bed_id == Bed.id)
            .join(Room, Bed.room_id == Room.id)
            .join(Floor, Room.floor_id == Floor.id)
            .join(Building, Floor.building_id == Building.id)
            .filter(
                Building.id == building_id,
                Building.owner_id == owner_id,

                # Only active allocations are included.
                BedAllocation.status == AllocationStatus.ACTIVE
            )
            .all()
        )


bed_allocation_repository = BedAllocationRepository()