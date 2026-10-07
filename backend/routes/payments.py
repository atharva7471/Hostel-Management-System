from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.models import Payment, PaymentStatus, FeeStatus, RoleEnum
from backend.auth import require_management, get_current_user
from bson import ObjectId
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/", response_model=list[dict])
async def get_payments(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if not student:
            return []
        payments = await db.payments.find({"student_id": str(student["_id"])}).to_list(1000)
    else:
        # Management
        payments = await db.payments.find().to_list(1000)
        
    for p in payments:
        p["_id"] = str(p["_id"])
        
    return payments

@router.post("/")
async def record_payment(payment: Payment, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    payment_dict = payment.model_dump(by_alias=True, exclude={"id"})
    
    # Verify Fee exists
    fee = await db.fees.find_one({"_id": ObjectId(payment_dict["fee_id"])})
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
        
    # Prevent overpaying
    if payment_dict["amount"] > fee["remaining_amount"]:
        raise HTTPException(status_code=400, detail="Payment amount cannot exceed remaining fee amount")
        
    if payment_dict["amount"] <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")
        
    # Fetch Student Name
    student = await db.students.find_one({"_id": ObjectId(payment_dict["student_id"])})
    if student:
        payment_dict["student_name"] = student["full_name"]
    else:
        payment_dict["student_name"] = "Unknown"

    payment_dict["payment_id"] = f"MOCK-{str(uuid.uuid4())[:8].upper()}"
    payment_dict["status"] = PaymentStatus.COMPLETED.value
    payment_dict["payment_date"] = datetime.utcnow().isoformat()
    
    result = await db.payments.insert_one(payment_dict)
    payment_dict["_id"] = str(result.inserted_id)
    
    # Recalculate Fee amounts and status
    new_amount_paid = fee.get("amount_paid", 0.0) + payment_dict["amount"]
    new_remaining = fee["fee_amount"] - new_amount_paid
    
    new_status = fee["status"]
    if new_remaining == 0:
        new_status = FeeStatus.PAID.value
    else:
        new_status = FeeStatus.PARTIALLY_PAID.value
        
    await db.fees.update_one(
        {"_id": ObjectId(payment_dict["fee_id"])},
        {"$set": {
            "amount_paid": new_amount_paid,
            "remaining_amount": new_remaining,
            "status": new_status
        }}
    )
    
    # Notify student
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        payment_dict["student_id"],
        "Payment received",
        f"Your ₹{payment_dict['amount']} payment was recorded successfully.",
        "PAYMENT",
        payment_dict["_id"]
    )
    
    return payment_dict
