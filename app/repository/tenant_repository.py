from sqlalchemy.orm import Session
from sqlalchemy import update, case

from app.models.tenant_model import Tenant, TenantStatus
from app.models.bed_allocation_model import BedAllocation, AllocationStatus
from app.models.bed_model import Bed
from app.models.room_model import Room
from app.models.floor_model import Floor
from app.models.building_model import Building


class TenantRepository():

    def get_tenant_by_id(self, db : Session, tenant_id : int):
        return( 
            db.query(Tenant)
            .filter(Tenant.id == tenant_id)
            .first()
        )

    def create_tenant(self, db: Session, tenant_data , owner_id : int ):

        new_tenant = Tenant(
            owner_id=owner_id,
            full_name=tenant_data.full_name,
            phone=tenant_data.phone,
            gender=tenant_data.gender,
            permanent_address=tenant_data.permanent_address,
            emergency_contact_phone=tenant_data.emergency_contact_phone,
            aadhaar_number=tenant_data.aadhaar_number
        )


        db.add(new_tenant)
        db.flush()
        return new_tenant

    # update a tenant 
    def update_tenant(self, db: Session, tenant_id: int, data: dict):

        update_query = (
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(**data)
        )

        db.execute(update_query)


    # Mark a tenant as inactive.
    def deactivate_tenant(self, db: Session, tenant_id: int):

        update_query = (
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(status=TenantStatus.INACTIVE)
        )

        db.execute(update_query)


    def get_active_tenant_by_id_and_owner(
        self,
        db: Session,
        tenant_id: int,
        owner_id: int
    ):
        return (
            db.query(Tenant)
            .filter(
                Tenant.id == tenant_id,
                Tenant.owner_id == owner_id,
                Tenant.status == TenantStatus.ACTIVE
            )
            .first()
        )

    # Find another active tenant with the same phone number
    def get_active_tenant_by_phone(self, db: Session, owner_id: int, phone: str):
        return (
            db.query(Tenant)
            .filter(
                Tenant.owner_id == owner_id,
                Tenant.phone == phone,
                Tenant.status == TenantStatus.ACTIVE
            )
            .first()
        )

    # Get an active tenant belonging to the owner
    def get_active_tenant_by_id(
        self,
        db: Session,
        tenant_id: int,
        owner_id: int
    ):
        return (
            db.query(Tenant)
            .filter(
                Tenant.id == tenant_id,
                Tenant.owner_id == owner_id,
                Tenant.status == TenantStatus.ACTIVE
            )
            .first()
        )
    
    # Does another active tenant of this owner already have this phone?
    def get_other_active_tenant_by_phone(
        self,
        db: Session,
        owner_id: int,
        phone: str,
        tenant_id: int
    ):
        return (
            db.query(Tenant)
            .filter(
                Tenant.owner_id == owner_id,
                Tenant.phone == phone,
                Tenant.status == TenantStatus.ACTIVE,
                Tenant.id != tenant_id
            )
            .first()
        )


    def get_vacating_tenants_by_building(
        self,
        db: Session,
        building_id: int,
        owner_id: int,
    ):
        # Fetch only vacating tenants belonging to this owner
        # and the selected building.
        return (
            db.query(
                Tenant.id.label("tenant_id"),
                Tenant.full_name,
                Tenant.phone,
                Bed.id.label("bed_id"),
                Room.room_number,
                Building.id.label("building_id"),
                Building.name.label("building_name"),
                BedAllocation.expected_check_out_date,
            )
            # Connect the tenant's allocation to its bed and room.
            .join(
                BedAllocation,
                BedAllocation.tenant_id == Tenant.id,
            )
            .join(Bed, Bed.id == BedAllocation.bed_id)
            .join(Room, Room.id == Bed.room_id)
            .join(Floor, Floor.id == Room.floor_id)
            .join(Building, Building.id == Floor.building_id)
            # Enforce owner and building boundaries.
            .filter(
                Tenant.owner_id == owner_id,
                Building.id == building_id,
                Building.owner_id == owner_id,
                Tenant.status == TenantStatus.ACTIVE,
                BedAllocation.status == AllocationStatus.ACTIVE,
                BedAllocation.is_vacating.is_(True),
                Room.is_active.is_(True),
                Room.deleted_at.is_(None),
                Floor.is_active.is_(True),
                Floor.deleted_at.is_(None),
            )
            # Put dated tenants first, with the oldest checkout
            # dates first. Tenants without a date appear last.
            .order_by(
                case(
                    (BedAllocation.expected_check_out_date.is_(None), 1),
                    else_=0,
                ),
                BedAllocation.expected_check_out_date.asc(),
                Tenant.full_name.asc(),
            )
            .all()
        )

    

tenant_repository = TenantRepository()