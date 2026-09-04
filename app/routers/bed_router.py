from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.bed_services import bed_service
from app.dependencies.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/beds",
    tags=["Beds"]
)

@router.post("/rooms/{room_id}/beds")
def add_bed(room_id: int, db: Session = Depends(get_db)):

    # add new bed
    new_bed = bed_service.add_bed(db, room_id)

    if not new_bed:
        return {
            "exists": False,
            "message": "Room not found."
        }

    return {
        "exists": True,
        "message": "Bed added successfully.",
        "bed": {
            "id": new_bed.id,
            "room_id": new_bed.room_id,
            "bed_number": new_bed.bed_number
        }
    }


@router.get("/room/{room_id}")
def get_beds_information(
    room_id: int,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):

    try:

        return bed_service.get_beds_information_by_room_id(
            db=db,
            room_id=room_id,
            owner_id=owner_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# delete bed endpoint 
@router.delete("/{bed_id}")
def delete_bed(
    bed_id: int,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_current_user)
):

    result = bed_service.deactivate_bed(
        db=db,
        bed_id=bed_id,
        owner_id=owner_id
    )

    if not result["success"]:
        return {
            "exists": False,
            "message": result["message"]
        }

    return {
        "exists": True,
        "message": "Bed deleted successfully."
    }