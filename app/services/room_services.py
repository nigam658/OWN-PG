from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date

from app.repository.room_Repository import room_repository
from app.repository.bed_Repository import bed_repository
from app.repository.tenant_repository import tenant_repository
from app.repository.bed_allocation_repository import bed_allocation_repository
from app.repository.floor_repository import floor_repository
from app.repository.monthlyRent_repository import monthly_rent_repository
from app.models.tenant_model import TenantStatus
from app.models.bed_allocation_model import AllocationStatus
from app.models.bed_model import BedStatus

from app.utils.time import now_ist



class RoomService :
    # this fucntion return the room if exist (Leter)
    def search_room(self, db : Session, room_number : str, owner_id ):
        
        room = room_repository.get_room_by_number(db=db, room_number=room_number, owner_id=owner_id)

        if room is None:
            return {
                "exists": False,
                "message": "Room not found."
            }
        
        # collect all beds using room_id
        beds = bed_repository.get_beds_by_room_id(db=db, room_id=room.id)

        # store all bed datails when bed loop running
        beds_data = []


        for bed in beds:
            # Find active allocation for this bed
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
                "status": bed.status.value,  #bug#..........🪲
                "tenant": None
            }
 
            if allocation:
 
                tenant = tenant_repository.get_tenant_by_id(
                    db=db,
                    tenant_id=allocation.tenant_id
                )

                if tenant:

                    bed_info["tenant"] = {
                        "tenant_id": tenant.id,
                        "full_name": tenant.full_name,
                        "phone": tenant.phone,
                        "check_in_date": allocation.check_in_date
                    }


            beds_data.append(bed_info)


        return {
            "exists": True,
            "room": {
                "id": room.id,
                "room_number": room.room_number,
                "total_beds": len(beds)
            },
            "beds" : beds_data
        }
    
    # showing rooms in building page
    def get_rooms_by_floor_id(self, db: Session, floor_id: int, owner_id: int):

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

        rooms = room_repository.get_rooms_by_floor_id(
            db,
            floor_id
        )

        rooms_data = []

        for room in rooms:

            total_beds = bed_repository.get_active_bed_count_by_room_id(
                db=db,
                room_id=room.id
            )

            occupied_beds = (
                bed_allocation_repository
                .get_active_allocation_count_by_room_id(
                    db=db,
                    room_id=room.id
                )
            )

            unpaid_tenants = (
                monthly_rent_repository
                .get_unpaid_tenant_count_by_room_id(
                    db=db,
                    room_id=room.id,
                    today=date.today()
                )
            )

            rooms_data.append({
                "id": room.id,
                "room_number": room.room_number,
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "unpaid_tenants": unpaid_tenants
            })

        return rooms_data


    # Delete a room and close its active tenant allocations.
    def delete_room(
        self,
        db: Session,
        room_id: int,
        owner_id: int
    ):

        # Check room ownership.
        room = room_repository.get_room_for_owner(
            db=db,
            room_id=room_id,
            owner_id=owner_id
        )

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )

        # Prevent deleting an already deleted room.
        if not room.is_active:
            raise HTTPException(
                status_code=400,
                detail="Room is already deleted"
            )

        try:
            # Get active allocations in this room.
            allocations = (
                bed_allocation_repository
                .get_active_allocations_by_room_id(
                    db=db,
                    room_id=room.id
                )
            )

            # Check out active tenants and allocations.
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

                # Deactivate the tenant.
                tenant.status = TenantStatus.INACTIVE

                allocation.status = AllocationStatus.CHECKED_OUT
                allocation.actual_check_out_date = date.today()

            # Deactivate all beds in the room.
            beds = bed_repository.get_beds_by_room_id(
                db=db,
                room_id=room.id
            )

            for bed in beds:
                if bed.status != BedStatus.INACTIVE:
                    bed.status = BedStatus.INACTIVE


            # Soft-delete the room.
            room.is_active = False
            room.deleted_at = now_ist()

            # Save all changes together.
            db.commit()

            db.refresh(room)

        except Exception:
            # Roll back all changes if anything fails.
            db.rollback()
            raise

        return {
            "success": True,
            "message": "Room deleted successfully.",
            "room": {
                "id": room.id,
                "room_number": room.room_number
            }
        }

    def add_room(self, db: Session, data, owner_id: int):

        # Check if the floor belongs to the owner.
        floor = floor_repository.get_floor_by_id_and_owner_id(
            db=db,
            floor_id=data.floor_id,
            owner_id=owner_id
        )

        if floor is None:
            raise HTTPException(
                status_code=404,
                detail="Floor not found"
            )

        # Validate room number format.
        if not data.room_number.isdigit() or len(data.room_number) != 3:
            raise HTTPException(
                status_code=400,
                detail="Room number must be exactly 3 digits."
            )

        # Room number must belong to the selected floor.
        if int(data.room_number[0]) != floor.floor_number:
            raise HTTPException(
                status_code=400,
                detail="Room number does not belong to this floor."
            )

        # Check whether the room number already exists.
        room = room_repository.get_room_by_floor_and_number(
            db=db,
            floor_id=data.floor_id,
            room_number=data.room_number
        )

        # Active room cannot be created again.
        if room is not None and room.is_active:
            raise HTTPException(
                status_code=400,
                detail="Room already exists"
            )

        try:
            # Reuse a previously deleted room.
            if room is not None:
                room.is_active = True
                room.deleted_at = None

            # Create a new room if it does not exist.
            if room is None:
                room = room_repository.create_room(
                    db=db,
                    floor_id=data.floor_id,
                    room_number=data.room_number
                )

            # Get existing beds for this room.
            beds = bed_repository.get_beds_by_room_id_ordered(
                db=db,
                room_id=room.id
            )

            # Reactivate inactive beds or create new beds.
            for index in range(data.number_of_beds):

                if index < len(beds):
                    bed = beds[index]

                    if bed.status == BedStatus.INACTIVE:
                        bed.status = BedStatus.AVAILABLE
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail="Bed data is inconsistent"
                        )

                else:
                    # Create a new bed.
                    bed_number = chr(65 + index)
                    
                    bed_repository.create_bed(
                        db=db,
                        room_id=room.id,
                        bed_number=bed_number
                    )

            # Keep extra historical beds inactive.
            for bed in beds[data.number_of_beds:]:
                bed.status = BedStatus.INACTIVE
                
            db.commit()
            db.refresh(room)

        except Exception:
            db.rollback()
            raise

        return {
            "success": True,
            "message": "Room created successfully.",
            "room": {
                "id": room.id,
                "room_number": room.room_number,
                "number_of_beds": data.number_of_beds
            }
        }


room_service = RoomService()
 