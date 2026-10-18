from sqlalchemy.orm import Session
from datetime import date

from app.repository.bed_Repository import bed_repository
from app.repository.room_Repository import room_repository
from app.repository.bed_allocation_repository import bed_allocation_repository
from app.repository.tenant_repository import tenant_repository
from app.models.bed_model import BedStatus
from app.models.monthlyrent_model import MonthlyRentStatus
from app.models.building_model import Building
from app.repository.monthlyRent_repository import monthly_rent_repository

class BedService:

    def add_bed(self, db: Session, room_id: int, owner_id: int):


        # If room does not exist, return None
        room = room_repository.get_room_by_id_and_owner(
            db,
            room_id,
            owner_id=owner_id
        )

        if not room:
            return None

        beds = bed_repository.get_beds_by_room_id(
            db,
            room_id
        )

        # Sort beds by bed number
        beds.sort(key=lambda bed: bed.bed_number)

        # Reuse the first inactive bed
        for bed in beds:
            if bed.status == BedStatus.INACTIVE:
                bed.status = BedStatus.AVAILABLE

                db.commit()
                db.refresh(bed)

                return bed

        # No inactive bed exists → create a new bed
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
        today = date.today()


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
                "tenant": None,
                "payment_status": None,
                "unpaid_months": 0

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
                        "full_name": tenant.full_name,
                        "phone": tenant.phone,
                        "check_in_date": allocation.check_in_date.isoformat(),
                        "is_vacating": allocation.is_vacating
                    }

                
                # Get all monthly rent records for this allocation
                monthly_rents = (
                    monthly_rent_repository
                    .get_monthly_rents_by_allocation_id(
                        db=db,
                        bed_allocation_id=allocation.id
                    )
                )

                # Consider only rent records whose due date has arrived
                due_rents = [
                    rent for rent in monthly_rents
                    if rent.due_date <= today
                ]

                # No rent records are due yet → hide the payment badge
                if not due_rents:
                    bed_info["payment_status"] = None
                    bed_info["unpaid_months"] = 0

                else:
                    # Count records that are DUE or PARTIAL
                    unpaid_months = sum(
                        1
                        for rent in due_rents
                        if rent.status in (
                            MonthlyRentStatus.DUE,
                            MonthlyRentStatus.PARTIAL
                        )
                    )

                    bed_info["unpaid_months"] = unpaid_months

                    # All due records are paid
                    if unpaid_months == 0:
                        bed_info["payment_status"] = "PAID"
                    else:
                        bed_info["payment_status"] = "UNPAID"

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

    
        # Get empty beds for a building owned by the current user.
    def get_empty_beds_by_building_id(
        self,
        db: Session,
        building_id: int,
        owner_id: int
    ):
        # Verify the building exists and belongs to this owner.
        building = db.query(Building).filter(
            Building.id == building_id,
            Building.owner_id == owner_id
        ).first()

        # Return a friendly error if the building is missing or belongs to another owner.
        if not building:
            raise ValueError(
                "Building not found or you don't have permission to access it."
            )

        # Fetch eligible empty beds using the repository.
        empty_beds = bed_repository.get_empty_beds_by_building_id(
            db=db,
            building_id=building_id,
            owner_id=owner_id
        )

        # Group eligible beds by room.
        rooms = {}

        for bed, room_number in empty_beds:
            if room_number not in rooms:
                rooms[room_number] = {
                    "room_number": room_number,
                    "empty_bed_count": 0
                }

            rooms[room_number]["empty_bed_count"] += 1

        return list(rooms.values())

    
bed_service = BedService()