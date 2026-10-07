from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.models import Complaint, RequestStatus, RoleEnum
from backend.auth import require_management, get_current_user
from bson import ObjectId
from datetime import datetime
from typing import Optional

router = APIRouter()

class ComplaintUpdate(BaseModel):
    status: Optional[RequestStatus] = None
    priority: Optional[str] = None

@router.get("/", response_model=list[dict])
async def get_complaints(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if not student:
            return []
        items = await db.complaints.find({"student_id": str(student["_id"])}).to_list(1000)
    else:
        items = await db.complaints.find().to_list(1000)
        
    for item in items:
        item["_id"] = str(item["_id"])
    return items

@router.get("/{id}")
async def get_complaint(id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    item = await db.complaints.find_one({"_id": ObjectId(id)})
    if not item:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if item["student_id"] != str(student["_id"]):
            raise HTTPException(status_code=403, detail="Forbidden")
            
    item["_id"] = str(item["_id"])
    return item

@router.post("/")
async def create_complaint(req: Complaint, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != RoleEnum.STUDENT.value:
        raise HTTPException(status_code=403, detail="Only students can submit complaints")
        
    student = await db.students.find_one({"email": current_user["email"]})
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    req_dict = req.model_dump(by_alias=True, exclude={"id"})
    req_dict["student_id"] = str(student["_id"])
    req_dict["student_name"] = student["full_name"]
    req_dict["created_at"] = datetime.utcnow().isoformat()
    req_dict["updated_at"] = datetime.utcnow().isoformat()
    req_dict["status"] = RequestStatus.SUBMITTED.value
    
    result = await db.complaints.insert_one(req_dict)
    req_dict["_id"] = str(result.inserted_id)
    return req_dict

@router.patch("/{id}")
async def update_complaint(id: str, req_update: ComplaintUpdate, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    existing = await db.complaints.find_one({"_id": ObjectId(id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    update_data = {}
    if req_update.status:
        update_data["status"] = req_update.status.value
    if req_update.priority:
        update_data["priority"] = req_update.priority
        
    update_data["updated_at"] = datetime.utcnow().isoformat()
        
    await db.complaints.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    
    updated = await db.complaints.find_one({"_id": ObjectId(id)})
    updated["_id"] = str(updated["_id"])
    
    if req_update.status:
        from backend.routes.notifications import create_notification
        await create_notification(
            db,
            updated["student_id"],
            "Complaint status updated",
            f"Your complaint '{updated['title']}' is now {req_update.status.value.replace('_', ' ')}.",
            "COMPLAINT",
            id
        )
        
    return updated

@router.delete("/{id}")
async def delete_complaint(id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    result = await db.complaints.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"message": "Deleted successfully"}
