from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.models import Notification, RoleEnum
from backend.auth import get_current_user, require_management
from bson import ObjectId

router = APIRouter()

@router.get("/", response_model=list[dict])
async def get_notifications(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    notifications = await db.notifications.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    for n in notifications:
        n["_id"] = str(n["_id"])
    return notifications

@router.patch("/{id}/read")
async def mark_read(id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    result = await db.notifications.update_one(
        {"_id": ObjectId(id), "user_id": user_id},
        {"$set": {"is_read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}

@router.patch("/read-all")
async def mark_all_read(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    await db.notifications.update_many(
        {"user_id": user_id, "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All marked as read"}

# Helper function to create notification programmatically
async def create_notification(db: AsyncIOMotorDatabase, user_id: str, title: str, message: str, type: str, related_id: str = None):
    from datetime import datetime
    notif = {
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": type,
        "is_read": False,
        "related_id": related_id,
        "created_at": datetime.utcnow().isoformat()
    }
    await db.notifications.insert_one(notif)
