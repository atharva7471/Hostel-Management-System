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
