from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.auth import require_management
from backend.services.allocation_service import allocate_student, deallocate_student, reallocate_student
from pydantic import BaseModel

router = APIRouter()

class AllocationRequest(BaseModel):
    student_id: str
    hostel_id: str
    room_id: str
    bed_number: str

@router.post("/")
async def allocate(payload: AllocationRequest, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    return await allocate_student(
        db=db,
        student_id=payload.student_id,
        hostel_id=payload.hostel_id,
        room_id=payload.room_id,
        bed_number=payload.bed_number,
        performed_by="MANAGEMENT"
    )

@router.delete("/{student_id}")
async def deallocate(student_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    return await deallocate_student(db, student_id, performed_by="MANAGEMENT")

class ReallocationRequest(BaseModel):
    new_hostel_id: str
    new_room_id: str
    new_bed_number: str

@router.post("/{student_id}/reallocate")
async def reallocate(student_id: str, payload: ReallocationRequest, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    return await reallocate_student(
        db, 
        student_id, 
        payload.new_hostel_id, 
        payload.new_room_id, 
        payload.new_bed_number, 
        performed_by="MANAGEMENT"
    )
