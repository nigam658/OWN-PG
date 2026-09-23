from sqlalchemy.orm import Session
from sqlalchemy import update

from app.models.tenant_model import Tenant, TenantStatus
from app.models.bed_allocation_model import BedAllocation


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

tenant_repository = TenantRepository()