from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.auth import require_management, get_current_user
from backend.models import Movement, MovementCreate, MovementStatus, StudentProfile, RoleEnum, PresenceStatus
from bson import ObjectId
from typing import Optional
from datetime import datetime

router = APIRouter()

@router.post("/")
async def create_movement(
    payload: MovementCreate, 
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != RoleEnum.STUDENT.value:
        raise HTTPException(status_code=403, detail="Only students can create movement requests.")

    student = await db.students.find_one({"email": current_user["email"]})
    if not student or student.get("status") != "ACTIVE_RESIDENT":
        raise HTTPException(status_code=403, detail="Only active residents can create movement requests.")
        
    # Check if there is already a pending or active movement
    existing = await db.movements.find_one({
        "student_id": str(student["_id"]),
        "status": {"$in": [MovementStatus.PENDING.value, MovementStatus.APPROVED.value, MovementStatus.OUTSIDE.value]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active or pending movement request.")
        
    now = datetime.utcnow().isoformat()
    movement_doc = {
        "student_id": str(student["_id"]),
        "resident_id": student.get("resident_id", ""),
        "hostel_id": student.get("allocated_hostel_id", ""),
        "room_id": student.get("allocated_room_id", ""),
        "bed_id": student.get("allocated_bed_number", ""),
        "student_name": student.get("full_name", ""),
        "reason": payload.reason.value,
        "destination": payload.destination,
        "expected_exit": payload.expected_exit,
        "expected_return": payload.expected_return,
        "note": payload.note,
        "status": MovementStatus.PENDING.value,
        "requested_at": now,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.movements.insert_one(movement_doc)
    movement_doc["_id"] = str(result.inserted_id)
    
    # Notify management
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        "MANAGEMENT", # Global management notification or specific hostel manager
        "New Movement Request",
        f"{student.get('full_name')} requested to exit to {payload.destination}.",
        "MOVEMENT",
        movement_doc["_id"]
    )
    
    return {"message": "Movement request created", "movement": movement_doc}

@router.get("/")
async def get_movements(
    hostel_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        query["student_id"] = str(student["_id"])
    else:
        if hostel_id:
            query["hostel_id"] = hostel_id
        if status:
            query["status"] = status
            
    movements = await db.movements.find(query).sort("created_at", -1).to_list(1000)
    for m in movements:
        m["_id"] = str(m["_id"])
    return movements

@router.get("/{movement_id}")
async def get_movement(
    movement_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    movement = await db.movements.find_one({"_id": ObjectId(movement_id)})
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if str(student["_id"]) != movement["student_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
            
    movement["_id"] = str(movement["_id"])
    return movement

@router.patch("/{movement_id}/approve")
async def approve_movement(
    movement_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: dict = Depends(require_management)
):
    movement = await db.movements.find_one({"_id": ObjectId(movement_id)})
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    if movement["status"] != MovementStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Only pending requests can be approved")
        
    now = datetime.utcnow().isoformat()
    await db.movements.update_one(
        {"_id": ObjectId(movement_id)},
        {"$set": {
            "status": MovementStatus.APPROVED.value,
            "approved_by": current_user.get("name", "Management"),
            "updated_at": now
        }}
    )
    
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        movement["student_id"],
        "Movement Request Approved",
        f"Your request to go to {movement['destination']} has been approved.",
        "MOVEMENT",
        movement_id
    )
    
    return {"message": "Movement approved"}

@router.patch("/{movement_id}/reject")
async def reject_movement(
    movement_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: dict = Depends(require_management)
):
    movement = await db.movements.find_one({"_id": ObjectId(movement_id)})
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    if movement["status"] != MovementStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Only pending requests can be rejected")
        
    now = datetime.utcnow().isoformat()
    await db.movements.update_one(
        {"_id": ObjectId(movement_id)},
        {"$set": {
            "status": MovementStatus.REJECTED.value,
            "updated_at": now
        }}
    )
    
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        movement["student_id"],
        "Movement Request Rejected",
        f"Your request to go to {movement['destination']} was rejected.",
        "MOVEMENT",
        movement_id
    )
    
    return {"message": "Movement rejected"}

@router.patch("/{movement_id}/checkout")
async def checkout_movement(
    movement_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    movement = await db.movements.find_one({"_id": ObjectId(movement_id)})
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    # Check permissions
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if str(student["_id"]) != movement["student_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
            
    if movement["status"] != MovementStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Only approved requests can be checked out")
        
    now = datetime.utcnow().isoformat()
    await db.movements.update_one(
        {"_id": ObjectId(movement_id)},
        {"$set": {
            "status": MovementStatus.OUTSIDE.value,
            "actual_exit": now,
            "updated_at": now
        }}
    )
    
    await db.students.update_one(
        {"_id": ObjectId(movement["student_id"])},
        {"$set": {"presence_status": PresenceStatus.OUTSIDE.value}}
    )
    
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        movement["student_id"],
        "Checked Out",
        f"You have checked out of the hostel.",
        "MOVEMENT",
        movement_id
    )
    
    return {"message": "Checked out successfully"}

@router.patch("/{movement_id}/checkin")
async def checkin_movement(
    movement_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    movement = await db.movements.find_one({"_id": ObjectId(movement_id)})
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    if current_user["role"] == RoleEnum.STUDENT.value:
        student = await db.students.find_one({"email": current_user["email"]})
        if str(student["_id"]) != movement["student_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
            
    if movement["status"] != MovementStatus.OUTSIDE.value:
        raise HTTPException(status_code=400, detail="Movement must be OUTSIDE to check in")
        
    now = datetime.utcnow().isoformat()
    
    # Check if late
    expected_return = movement.get("expected_return")
    is_late = False
    if expected_return and now > expected_return:
        is_late = True
        
    new_status = MovementStatus.LATE_RETURN.value if is_late else MovementStatus.RETURNED.value
        
    await db.movements.update_one(
        {"_id": ObjectId(movement_id)},
        {"$set": {
            "status": new_status,
            "actual_return": now,
            "updated_at": now
        }}
    )
    
    await db.students.update_one(
        {"_id": ObjectId(movement["student_id"])},
        {"$set": {"presence_status": PresenceStatus.INSIDE.value}}
    )
    
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        movement["student_id"],
        "Checked In",
        f"You have successfully checked back in.",
        "MOVEMENT",
        movement_id
    )
    
    if is_late:
        await create_notification(
            db,
            "MANAGEMENT",
            "Late Return",
            f"Student {movement.get('student_name')} returned late.",
            "MOVEMENT",
            movement_id
        )
    
    return {"message": "Checked in successfully", "status": new_status}
