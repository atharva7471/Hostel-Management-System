from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.models import Announcement, RoleEnum
from backend.auth import get_current_user, require_management
from backend.routes.notifications import create_notification
from bson import ObjectId
from datetime import datetime
from typing import Optional

router = APIRouter()

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    target_audience: Optional[str] = None

@router.get("/", response_model=list[dict])
async def get_announcements(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        hostel_id = student.get("allocated_hostel_id") if student else None
        
        query = {"$or": [{"target_audience": "ALL"}]}
        if hostel_id:
            query["$or"].append({"target_audience": hostel_id})
            
        items = await db.announcements.find(query).sort("created_at", -1).to_list(100)
    else:
        items = await db.announcements.find().sort("created_at", -1).to_list(100)
        
    for item in items:
        item["_id"] = str(item["_id"])
    return items

@router.get("/{id}")
async def get_announcement(id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    item = await db.announcements.find_one({"_id": ObjectId(id)})
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item["_id"] = str(item["_id"])
    return item

@router.post("/")
async def create_announcement(req: Announcement, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    req_dict = req.model_dump(by_alias=True, exclude={"id"})
    req_dict["created_at"] = datetime.utcnow().isoformat()
    
    result = await db.announcements.insert_one(req_dict)
    req_dict["_id"] = str(result.inserted_id)
    
    # Notify students
    query = {}
    if req.target_audience != "ALL":
        query["allocated_hostel_id"] = req.target_audience
        
    students = await db.students.find(query, {"_id": 1}).to_list(10000)
    for student in students:
        await create_notification(
            db, 
            str(student["_id"]), 
            f"📢 {req.title}", 
            req.description[:100] + "..." if len(req.description) > 100 else req.description,
            "ANNOUNCEMENT", 
            str(result.inserted_id)
        )
        
    return req_dict

@router.put("/{id}")
async def update_announcement(id: str, req_update: AnnouncementUpdate, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    existing = await db.announcements.find_one({"_id": ObjectId(id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")
        
    update_data = {k: v for k, v in req_update.model_dump().items() if v is not None}
    if not update_data:
        return existing
        
    await db.announcements.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    updated = await db.announcements.find_one({"_id": ObjectId(id)})
    updated["_id"] = str(updated["_id"])
    return updated

@router.delete("/{id}")
async def delete_announcement(id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    result = await db.announcements.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Deleted successfully"}
