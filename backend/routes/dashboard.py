from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.database import get_db
from backend.auth import get_current_user
from backend.models import RoleEnum
from datetime import datetime

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] == RoleEnum.MANAGEMENT.value:
        total_students = await db.students.count_documents({})
        total_rooms = await db.rooms.count_documents({})
        
        # Aggregate beds across all rooms
        pipeline = [
            {"$unwind": "$beds"},
            {"$group": {
                "_id": "$beds.status",
                "count": {"$sum": 1}
            }}
        ]
        bed_stats = await db.rooms.aggregate(pipeline).to_list(None)
        
        occupied_beds = 0
        available_beds = 0
        maintenance_beds = 0
        
        for stat in bed_stats:
            if stat["_id"] == "OCCUPIED":
                occupied_beds = stat["count"]
            elif stat["_id"] == "AVAILABLE":
                available_beds = stat["count"]
            elif stat["_id"] == "MAINTENANCE":
                maintenance_beds = stat["count"]
                
        total_beds = occupied_beds + available_beds + maintenance_beds
        occupancy_rate = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0
        
        # Financial Stats
        fees = await db.fees.find().to_list(10000)
        total_fees = 0.0
        collected = 0.0
        pending = 0.0
        overdue = 0.0
        
        for fee in fees:
            total_fees += fee.get("fee_amount", 0.0)
            collected += fee.get("amount_paid", 0.0)
            if fee.get("status") == "OVERDUE":
                overdue += fee.get("remaining_amount", 0.0)
            else:
                pending += fee.get("remaining_amount", 0.0)
                
        # Phase 4: Requests Stats
        # Open Complaints
        open_complaints = await db.complaints.count_documents({"status": {"$in": ["SUBMITTED", "ASSIGNED"]}})
        # In Progress
        in_progress_requests = await db.complaints.count_documents({"status": "IN_PROGRESS"}) + await db.maintenance_requests.count_documents({"status": "IN_PROGRESS"})
        # Pending Maintenance
        pending_maintenance = await db.maintenance_requests.count_documents({"status": {"$in": ["SUBMITTED", "ASSIGNED"]}})
        # Resolved this month
        current_month = datetime.utcnow().strftime("%Y-%m")
        resolved_complaints = await db.complaints.count_documents({"status": "RESOLVED", "updated_at": {"$regex": f"^{current_month}"}})
        resolved_maintenance = await db.maintenance_requests.count_documents({"status": "RESOLVED", "updated_at": {"$regex": f"^{current_month}"}})
        resolved_this_month = resolved_complaints + resolved_maintenance
        
        # Phase 5: Announcements & Notifications
        active_announcements = await db.announcements.count_documents({})
        unread_notifications = await db.notifications.count_documents({"user_id": str(current_user["_id"]), "is_read": False})
        
        recent_announcements = await db.announcements.find().sort("created_at", -1).limit(5).to_list(5)
        for ra in recent_announcements:
            ra["_id"] = str(ra["_id"])
            
        recent_notifications = await db.notifications.find({"user_id": str(current_user["_id"])}).sort("created_at", -1).limit(5).to_list(5)
        for rn in recent_notifications:
            rn["_id"] = str(rn["_id"])
        
        return {
            "total_students": total_students,
            "total_rooms": total_rooms,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "occupancy_rate": occupancy_rate,
            "total_fees": total_fees,
            "collected": collected,
            "pending": pending,
            "overdue": overdue,
            "open_complaints": open_complaints,
            "in_progress_requests": in_progress_requests,
            "pending_maintenance": pending_maintenance,
            "resolved_this_month": resolved_this_month,
            "active_announcements": active_announcements,
            "unread_notifications": unread_notifications,
            "recent_announcements": recent_announcements,
            "recent_notifications": recent_notifications
        }
    else:
        # Student stats
        student = await db.students.find_one({"email": current_user["email"]})
        if not student:
            return {}
        
        # Student active requests
        student_id = str(student["_id"])
        active_complaints = await db.complaints.find({"student_id": student_id, "status": {"$nin": ["CLOSED"]}}).to_list(10)
        active_maintenance = await db.maintenance_requests.find({"student_id": student_id, "status": {"$nin": ["CLOSED"]}}).to_list(10)
        
        for c in active_complaints:
            c["_id"] = str(c["_id"])
        for m in active_maintenance:
            m["_id"] = str(m["_id"])
            
        student["_id"] = str(student["_id"])
        
        # Phase 5: Announcements & Notifications
        hostel_id = student.get("allocated_hostel_id")
        query = {"$or": [{"target_audience": "ALL"}]}
        if hostel_id:
            query["$or"].append({"target_audience": hostel_id})
        
        recent_announcements = await db.announcements.find(query).sort("created_at", -1).limit(5).to_list(5)
        for ra in recent_announcements:
            ra["_id"] = str(ra["_id"])
            
        unread_notifications = await db.notifications.count_documents({"user_id": student_id, "is_read": False})
        recent_notifications = await db.notifications.find({"user_id": student_id}).sort("created_at", -1).limit(5).to_list(5)
        for rn in recent_notifications:
            rn["_id"] = str(rn["_id"])
            
        return {
            "profile": student,
            "active_complaints": active_complaints,
            "active_maintenance": active_maintenance,
            "recent_announcements": recent_announcements,
            "recent_notifications": recent_notifications,
            "unread_notifications": unread_notifications
        }
