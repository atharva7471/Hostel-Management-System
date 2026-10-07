from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.models import Room, Bed, BedStatus, RoomStatus
from backend.auth import require_management
from bson import ObjectId
from typing import Optional

router = APIRouter()

@router.get("/", response_model=list[Room])
async def get_rooms(hostel_id: Optional[str] = None, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    query = {}
    if hostel_id:
        query["hostel_id"] = hostel_id
    rooms = await db.rooms.find(query).to_list(1000)
    for room in rooms:
        room["_id"] = str(room["_id"])
    return rooms

@router.post("/", response_model=Room)
async def create_room(room: Room, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    room_dict = room.model_dump(by_alias=True, exclude={"id"})
    result = await db.rooms.insert_one(room_dict)
    room_dict["_id"] = str(result.inserted_id)
    return room_dict

@router.put("/{room_id}", response_model=Room)
async def update_room(room_id: str, room_update: Room, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    room_dict = room_update.model_dump(by_alias=True, exclude={"id"})
    # Do not overwrite beds array directly to avoid losing allocation data
    existing_room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    if not existing_room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    room_dict["beds"] = existing_room.get("beds", [])
    
    result = await db.rooms.update_one({"_id": ObjectId(room_id)}, {"$set": room_dict})
    
    updated_room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    updated_room["_id"] = str(updated_room["_id"])
    return updated_room

@router.delete("/{room_id}")
async def delete_room(room_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    result = await db.rooms.delete_one({"_id": ObjectId(room_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted"}

@router.post("/{room_id}/beds", response_model=Room)
async def add_bed(room_id: str, bed: Bed, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    # Check if bed number already exists
    if any(b.get("bed_number") == bed.bed_number for b in room.get("beds", [])):
        raise HTTPException(status_code=400, detail="Bed number already exists in this room")
        
    bed_dict = bed.model_dump()
    await db.rooms.update_one({"_id": ObjectId(room_id)}, {"$push": {"beds": bed_dict}})
    
    updated_room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    updated_room["_id"] = str(updated_room["_id"])
    return updated_room

class AllocateRequest(BaseModel):
    bed_number: str
    student_id: str

@router.post("/{room_id}/allocate")
async def allocate_student(room_id: str, payload: AllocateRequest, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    student = await db.students.find_one({"_id": ObjectId(payload.student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Check bed status
    bed = next((b for b in room.get("beds", []) if b["bed_number"] == payload.bed_number), None)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    
    if bed.get("status") == BedStatus.OCCUPIED.value:
        raise HTTPException(status_code=400, detail="Bed is already occupied")
        
    if student.get("allocated_room_id"):
        raise HTTPException(status_code=400, detail="Student is already allocated to a bed")
        
    # Update room/bed
    await db.rooms.update_one(
        {"_id": ObjectId(room_id), "beds.bed_number": payload.bed_number},
        {"$set": {
            "beds.$.status": BedStatus.OCCUPIED.value,
            "beds.$.student_email": student["email"],
            "beds.$.student_name": student["full_name"]
        }}
    )
    
    # Update room occupancy status logic can be here, but let's keep it simple
    
    # Phase 6: Hostel Identity
    import uuid
    from datetime import datetime
    resident_id = f"HST-A-{datetime.utcnow().year}-{str(uuid.uuid4())[:4].upper()}"
    
    # Update student profile
    await db.students.update_one(
        {"_id": ObjectId(payload.student_id)},
        {"$set": {
            "allocated_hostel_id": room.get("hostel_id"),
            "allocated_room_id": str(room["_id"]),
            "allocated_room_number": room["room_number"],
            "allocated_bed_number": payload.bed_number,
            "resident_id": resident_id,
            "status": "ACTIVE_RESIDENT",
            "allocation_date": datetime.utcnow().isoformat()
        }}
    )
    
    # Notify student
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        payload.student_id,
        "Room Allocated",
        f"You have been allocated Bed {payload.bed_number} in Room {room['room_number']}.",
        "ALLOCATION",
        str(room["_id"])
    )
    
    return {"message": "Allocated successfully"}

class VacateRequest(BaseModel):
    bed_number: str

@router.post("/{room_id}/vacate")
async def vacate_bed(room_id: str, payload: VacateRequest, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    bed = next((b for b in room.get("beds", []) if b["bed_number"] == payload.bed_number), None)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
        
    if bed.get("status") != BedStatus.OCCUPIED.value:
        raise HTTPException(status_code=400, detail="Bed is not occupied")
        
    student_email = bed.get("student_email")
    
    # Update room/bed
    await db.rooms.update_one(
        {"_id": ObjectId(room_id), "beds.bed_number": payload.bed_number},
        {"$set": {
            "beds.$.status": BedStatus.AVAILABLE.value,
            "beds.$.student_email": None,
            "beds.$.student_name": None
        }}
    )
    
    # Update student profile if email exists
    if student_email:
        await db.students.update_one(
            {"email": student_email},
            {"$set": {
                "allocated_room_id": None,
                "allocated_room_number": None,
                "allocated_bed_number": None
            }}
        )
        
    return {"message": "Vacated successfully"}

@router.put("/{room_id}/beds/{bed_number}/status")
async def update_bed_status(room_id: str, bed_number: str, status_payload: dict, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    new_status = status_payload.get("status")
    if new_status not in [BedStatus.AVAILABLE.value, BedStatus.MAINTENANCE.value]:
        raise HTTPException(status_code=400, detail="Invalid status update manually. Use vacate for OCCUPIED.")
        
    await db.rooms.update_one(
        {"_id": ObjectId(room_id), "beds.bed_number": bed_number},
        {"$set": {
            "beds.$.status": new_status,
        }}
    )
    return {"message": "Status updated"}
