from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.models import Hostel
from backend.auth import require_management
from bson import ObjectId

router = APIRouter()

@router.get("/", response_model=list[Hostel])
async def get_hostels(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    hostels = await db.hostels.find().to_list(1000)
    for hostel in hostels:
        hostel["_id"] = str(hostel["_id"])
    return hostels

@router.get("/{hostel_id}", response_model=Hostel)
async def get_hostel(hostel_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    hostel = await db.hostels.find_one({"_id": ObjectId(hostel_id)})
    if not hostel:
        raise HTTPException(status_code=404, detail="Hostel not found")
    hostel["_id"] = str(hostel["_id"])
    return hostel

@router.post("/", response_model=Hostel)
async def create_hostel(hostel: Hostel, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    hostel_dict = hostel.model_dump(by_alias=True, exclude={"id"})
    result = await db.hostels.insert_one(hostel_dict)
    hostel_dict["_id"] = str(result.inserted_id)
    return hostel_dict

@router.put("/{hostel_id}", response_model=Hostel)
async def update_hostel(hostel_id: str, hostel_update: Hostel, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    hostel_dict = hostel_update.model_dump(by_alias=True, exclude={"id"})
    result = await db.hostels.update_one({"_id": ObjectId(hostel_id)}, {"$set": hostel_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Hostel not found")
    
    updated_hostel = await db.hostels.find_one({"_id": ObjectId(hostel_id)})
    updated_hostel["_id"] = str(updated_hostel["_id"])
    return updated_hostel

@router.delete("/{hostel_id}")
async def delete_hostel(hostel_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    result = await db.hostels.delete_one({"_id": ObjectId(hostel_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Hostel not found")
    return {"message": "Hostel deleted"}
