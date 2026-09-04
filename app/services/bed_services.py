from sqlalchemy.orm import Session

from app.repository.bed_Repository import bed_repository
from app.repository.room_Repository import room_repository
from app.repository.bed_allocation_repository import bed_allocation_repository
from app.repository.tenant_repository import tenant_repository

class BedService:

    def add_bed(self, db: Session, room_id: int):

        owner_id = 1

        # if room not exist return None 
        room = room_repository.get_room_by_id_and_owner(db, room_id, owner_id=owner_id)

        if not room:
            return None

        beds = bed_repository.get_beds_by_room_id(
            db,
            room_id
        )

        existing_bed_numbers = set()

        for bed in beds:
            existing_bed_numbers.add(bed.bed_number)

        bed_number = "A"

        while bed_number in existing_bed_numbers:
            bed_number = chr(ord(bed_number) + 1)

        new_bed = bed_repository.create_new_bed(
            db,
            room_id,
            bed_number
        )

        return new_bed

    #fetch Beds information for Bed page
    def get_beds_information_by_room_id(self, db: Session, room_id: int, owner_id: int):

        # Get room only if it belongs to the owner
        room = room_repository.get_room_for_owner(
            db=db,
            room_id=room_id,
            owner_id=owner_id
        )

        if not room:
            raise ValueError("Room not found.")


        # Get all beds in the room
        beds = bed_repository.get_beds_by_room_id(
            db=db,
            room_id=room_id
        )

        beds_data = []

        for bed in beds:

            # Get active allocation for this bed
            allocation = (
                bed_allocation_repository
                .get_active_allocation_by_bed_id(
                    db=db,
                    bed_id=bed.id
                )
            )

            # Basic bed information
            bed_info = {
                "bed_id": bed.id,
                "bed_number": bed.bed_number,
                "status": bed.status.value,
                "rent": None,
                "tenant": None
            }

            # Add tenant information if an active allocation exists
            if allocation:
                bed_info["rent"] = float(allocation.rent)
                tenant = tenant_repository.get_tenant_by_id(
                    db=db,
                    tenant_id=allocation.tenant_id
                )

                if tenant:
                    bed_info["tenant"] = {
                        "tenant_id": tenant.id,
                        "full_name": tenant.full_name
                    }

            beds_data.append(bed_info)

        return beds_data


    # Delete bed / Deactivate bed
    def deactivate_bed(self, db: Session, bed_id: int, owner_id: int):

        # Check bed exists and belongs to owner
        bed = bed_repository.is_bed_owned_by_owner(
            db=db,
            bed_id=bed_id,
            owner_id=owner_id
        )

        if not bed:
            return {
                "success": False,
                "message": "Bed not found."
            }

        # Check active tenant
        allocation = (
            bed_allocation_repository
            .get_active_allocation_by_bed_id(
                db=db,
                bed_id=bed_id
            )
        )

        if allocation:
            return {
                "success": False,
                "message": "Cannot delete bed. Remove tenant first."
            }

        # Deactivate bed
        bed_repository.deactivate_bed(
            db=db,
            bed_id=bed_id
        )

        return {
            "success": True,
            "message": "Bed deleted successfully."
        }
    
bed_service = BedService()