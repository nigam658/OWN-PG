from sqlalchemy.orm import Session

from app.repository.room_Repository import room_repository
from app.repository.bed_Repository import bed_repository
from app.repository.tenant_repository import tenant_repository
from app.repository.bed_allocation_repository import bed_allocation_repository

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
    def get_rooms_by_floor_id(self, db: Session, floor_id: int):

        rooms = room_repository.get_rooms_by_floor_id(
            db,
            floor_id
        )

        rooms_data = []

        for room in rooms:

            beds = bed_repository.get_beds_by_room_id(
                db=db,
                room_id=room.id
            )

            rooms_data.append({
                "id": room.id,
                "room_number": room.room_number,
                "total_beds": len(beds)
            })

        return rooms_data
        

    

room_service = RoomService()
 