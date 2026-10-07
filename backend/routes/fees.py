from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.models import Fee, FeeStatus, RoleEnum
from backend.auth import require_management, get_current_user
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=list[dict])
async def get_fees(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if not student:
            return []
        fees = await db.fees.find({"student_id": str(student["_id"])}).to_list(1000)
    else:
        # Management
        fees = await db.fees.find().to_list(1000)
        
    for fee in fees:
        fee["_id"] = str(fee["_id"])
        
    return fees

@router.get("/{fee_id}")
async def get_fee(fee_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    fee = await db.fees.find_one({"_id": ObjectId(fee_id)})
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")
        
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if fee["student_id"] != str(student["_id"]):
            raise HTTPException(status_code=403, detail="Forbidden")
            
    fee["_id"] = str(fee["_id"])
    return fee

@router.post("/")
async def create_fee(fee: Fee, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    fee_dict = fee.model_dump(by_alias=True, exclude={"id"})
    
    # Calculate initial values
    fee_dict["remaining_amount"] = fee_dict["fee_amount"]
    fee_dict["amount_paid"] = 0.0
    fee_dict["status"] = FeeStatus.PENDING.value
    
    # Ensure student exists
    student = await db.students.find_one({"_id": ObjectId(fee_dict["student_id"])})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    fee_dict["student_name"] = student["full_name"]
    fee_dict["student_sid"] = student["student_id"]
    
    result = await db.fees.insert_one(fee_dict)
    fee_dict["_id"] = str(result.inserted_id)
    return fee_dict

@router.put("/{fee_id}")
async def update_fee(fee_id: str, fee_update: Fee, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    existing_fee = await db.fees.find_one({"_id": ObjectId(fee_id)})
    if not existing_fee:
        raise HTTPException(status_code=404, detail="Fee not found")
        
    fee_dict = fee_update.model_dump(by_alias=True, exclude={"id"})
    
    # Recalculate based on existing paid amount (only total amount or due date can be updated usually)
    # If they update fee_amount, remaining amount must change
    amount_paid = existing_fee.get("amount_paid", 0.0)
    new_fee_amount = fee_dict["fee_amount"]
    remaining = new_fee_amount - amount_paid
    
    if remaining < 0:
        raise HTTPException(status_code=400, detail="Fee amount cannot be less than already paid amount")
        
    fee_dict["remaining_amount"] = remaining
    fee_dict["amount_paid"] = amount_paid
    
    if remaining == 0:
        fee_dict["status"] = FeeStatus.PAID.value
    elif amount_paid > 0:
        fee_dict["status"] = FeeStatus.PARTIALLY_PAID.value
    else:
        fee_dict["status"] = FeeStatus.PENDING.value
        
    # Check if overdue
    due_date = datetime.fromisoformat(fee_dict["due_date"].replace('Z', '+00:00'))
    if remaining > 0 and datetime.utcnow() > due_date:
         fee_dict["status"] = FeeStatus.OVERDUE.value
        
    await db.fees.update_one({"_id": ObjectId(fee_id)}, {"$set": fee_dict})
    
    updated_fee = await db.fees.find_one({"_id": ObjectId(fee_id)})
    updated_fee["_id"] = str(updated_fee["_id"])
    return updated_fee
