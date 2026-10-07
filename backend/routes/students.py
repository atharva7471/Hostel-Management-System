from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from backend.database import get_db
from backend.models import StudentProfile, UserCreate, RoleEnum
from backend.auth import require_management, get_password_hash, get_current_user
from bson import ObjectId

router = APIRouter()

@router.get("/", response_model=list[StudentProfile])
async def get_students(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    students = await db.students.find().to_list(1000)
    for student in students:
        student["_id"] = str(student["_id"])
    return students

@router.get("/me", response_model=StudentProfile)
async def get_my_profile(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    student = await db.students.find_one({"email": current_user["email"]})
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    student["_id"] = str(student["_id"])
    return student

@router.get("/{student_id}", response_model=StudentProfile)
async def get_student(student_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student["_id"] = str(student["_id"])
    return student

@router.post("/", response_model=StudentProfile)
async def create_student(student: StudentProfile, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": student.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Create User
    user = {
        "email": student.email,
        "name": student.full_name,
        "role": RoleEnum.STUDENT,
        "hashed_password": get_password_hash("password")
    }
    await db.users.insert_one(user)

    # Create Student Profile
    student_dict = student.model_dump(by_alias=True, exclude={"id"})
    result = await db.students.insert_one(student_dict)
    student_dict["_id"] = str(result.inserted_id)
    return student_dict

@router.put("/{student_id}", response_model=StudentProfile)
async def update_student(student_id: str, student_update: StudentProfile, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    existing_student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    if current_user["role"] == RoleEnum.STUDENT.value:
        if existing_student["email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="Forbidden")
            
    student_dict = student_update.model_dump(by_alias=True, exclude={"id"})
    
    # Do not override existing room assignments directly from student PUT 
    if existing_student.get("allocated_room_id"):
        student_dict["allocated_hostel_id"] = existing_student.get("allocated_hostel_id")
        student_dict["allocated_room_id"] = existing_student["allocated_room_id"]
        student_dict["allocated_room_number"] = existing_student["allocated_room_number"]
        student_dict["allocated_bed_number"] = existing_student["allocated_bed_number"]
        
    # Maintain existing resident ID if already assigned
    if existing_student.get("resident_id"):
        student_dict["resident_id"] = existing_student["resident_id"]
        student_dict["allocation_date"] = existing_student.get("allocation_date")
        student_dict["status"] = existing_student.get("status")
        
    # Phase 6: Automatic Application Status
    if current_user["role"] == RoleEnum.STUDENT.value:
        # If student updates profile, set status to UNDER_REVIEW if it was INCOMPLETE
        if existing_student.get("application_status", "INCOMPLETE") in ["INCOMPLETE", "CHANGES_REQUESTED"]:
            student_dict["application_status"] = "UNDER_REVIEW"
        else:
            student_dict["application_status"] = existing_student.get("application_status", "INCOMPLETE")

    result = await db.students.update_one({"_id": ObjectId(student_id)}, {"$set": student_dict})
    
    # Update users collection name
    await db.users.update_one({"email": existing_student["email"]}, {"$set": {"name": student_update.full_name}})
        
    updated_student = await db.students.find_one({"_id": ObjectId(student_id)})
    updated_student["_id"] = str(updated_student["_id"])
    return updated_student

@router.delete("/{student_id}")
async def delete_student(student_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Remove from users collection
    await db.users.delete_one({"email": student["email"]})
    
    # If allocated to a bed, free it
    if student.get("allocated_room_id") and student.get("allocated_bed_number"):
        await db.rooms.update_one(
            {
                "_id": ObjectId(student["allocated_room_id"]),
                "beds.bed_number": student["allocated_bed_number"]
            },
            {
                "$set": {
                    "beds.$.status": "AVAILABLE",
                    "beds.$.student_email": None,
                    "beds.$.student_name": None
                }
            }
        )
    
    await db.students.delete_one({"_id": ObjectId(student_id)})
    return {"message": "Student deleted"}

class ApplicationReview(BaseModel):
    status: str

@router.patch("/{student_id}/application")
async def review_application(student_id: str, review: ApplicationReview, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_management)):
    from backend.models import ApplicationStatus
    if review.status not in [s.value for s in ApplicationStatus]:
        raise HTTPException(status_code=400, detail="Invalid application status")
        
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    await db.students.update_one({"_id": ObjectId(student_id)}, {"$set": {"application_status": review.status}})
    
    # Notify student
    from backend.routes.notifications import create_notification
    msg_map = {
        "APPROVED": "Your hostel application has been approved! You will be allocated a room shortly.",
        "REJECTED": "Your hostel application has been rejected. Please contact management.",
        "CHANGES_REQUESTED": "Your hostel application requires changes. Please update your profile."
    }
    if review.status in msg_map:
        await create_notification(db, student_id, f"Application {review.status.capitalize()}", msg_map[review.status], "GENERAL", student_id)
        
    updated = await db.students.find_one({"_id": ObjectId(student_id)})
    updated["_id"] = str(updated["_id"])
    return updated
