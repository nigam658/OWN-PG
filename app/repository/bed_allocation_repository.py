from sqlalchemy.orm import Session
from sqlalchemy import update

from app.models.bed_allocation_model import (
    BedAllocation,
    AllocationStatus
)

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


bed_allocation_repository = BedAllocationRepository()