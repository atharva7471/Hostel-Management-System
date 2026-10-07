from datetime import datetime
import uuid
from bson import ObjectId
from fastapi import HTTPException
from backend.models import BedStatus, RoomStatus, StudentStatus

async def allocate_student(db, student_id: str, hostel_id: str, room_id: str, bed_number: str, performed_by: str = "MANAGEMENT"):
    # 1. Fetch Student
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    if student.get("status") == StudentStatus.ACTIVE_RESIDENT.value and student.get("allocated_bed_number"):
        raise HTTPException(status_code=400, detail="Student is already an active resident. Please reallocate instead.")
        
    # 2. Fetch Hostel
    hostel = await db.hostels.find_one({"_id": ObjectId(hostel_id)})
    if not hostel:
        raise HTTPException(status_code=404, detail="Hostel not found")
        
    # 3. Fetch Room
    room = await db.rooms.find_one({"_id": ObjectId(room_id), "hostel_id": hostel_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found in this hostel")
        
    # 4. Fetch Bed
    beds = room.get("beds", [])
    target_bed_idx = -1
    for i, b in enumerate(beds):
        if b["bed_number"] == bed_number:
            target_bed_idx = i
            break
            
    if target_bed_idx == -1:
        raise HTTPException(status_code=404, detail="Bed not found in this room")
        
    bed = beds[target_bed_idx]
    if bed.get("status") != BedStatus.AVAILABLE.value or bed.get("student_id"):
        raise HTTPException(status_code=400, detail=f"Bed {bed_number} is already occupied or under maintenance.")
        
    # 5. Calculate Resident ID (if not exists)
    res_id = student.get("resident_id")
    if not res_id:
        hostel_prefix = "A" if "A" in hostel["name"] else ("B" if "B" in hostel["name"] else "X")
        res_id = f"HST-{hostel_prefix}-{datetime.utcnow().year}-{str(uuid.uuid4())[:4].upper()}"

    now = datetime.utcnow().isoformat()
    
    # 6. Update bed status
    beds[target_bed_idx]["status"] = BedStatus.OCCUPIED.value
    beds[target_bed_idx]["student_id"] = student_id
    beds[target_bed_idx]["student_email"] = student.get("email")
    beds[target_bed_idx]["student_name"] = student.get("full_name")
    
    # Recalculate room occupancy
    occupied_count = sum(1 for b in beds if b.get("status") == BedStatus.OCCUPIED.value)
    capacity = room.get("capacity", len(beds))
    
    if occupied_count >= capacity:
        room_status = RoomStatus.FULL.value
    else:
        room_status = RoomStatus.AVAILABLE.value
        
    # Update room
    await db.rooms.update_one(
        {"_id": ObjectId(room_id)},
        {"$set": {
            "beds": beds,
            "status": room_status
        }}
    )
    
    # 7. Update Student
    student_updates = {
        "allocated_hostel_id": hostel_id,
        "allocated_room_id": room_id,
        "allocated_room_number": room.get("room_number"),
        "allocated_bed_number": bed_number,
        "status": StudentStatus.ACTIVE_RESIDENT.value,
        "resident_id": res_id,
        "allocation_date": now
    }
    
    await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": student_updates}
    )
    
    # 8. History
    await db.allocation_history.insert_one({
        "student_id": student_id,
        "resident_id": res_id,
        "hostel_id": hostel_id,
        "room_id": room_id,
        "bed_number": bed_number,
        "action": "ALLOCATED",
        "performed_by": performed_by,
        "timestamp": now
    })
    
    updated_student = await db.students.find_one({"_id": ObjectId(student_id)})
    updated_student["_id"] = str(updated_student["_id"])
    
    updated_room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    updated_room["_id"] = str(updated_room["_id"])
    updated_bed = next((b for b in updated_room["beds"] if b["bed_number"] == bed_number), None)
    
    hostel["_id"] = str(hostel["_id"])
    # 9. Notify student
    from backend.routes.notifications import create_notification
    await create_notification(
        db,
        student_id,
        "Room Allocated",
        f"You have been allocated Bed {bed_number} in Room {room.get('room_number')}.",
        "ALLOCATION",
        str(room_id)
    )
    
    return {
        "success": True,
        "student": updated_student,
        "hostel": hostel,
        "room": updated_room,
        "bed": updated_bed,
        "resident": {
            "resident_id": res_id,
            "student_id": student_id,
            "hostel_id": hostel_id,
            "room_id": room_id,
            "bed_number": bed_number,
            "status": "ACTIVE_RESIDENT",
            "allocated_at": now
        }
    }

async def deallocate_student(db, student_id: str, performed_by: str = "MANAGEMENT"):
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    room_id = student.get("allocated_room_id")
    bed_number = student.get("allocated_bed_number")
    
    if not room_id or not bed_number:
        raise HTTPException(status_code=400, detail="Student is not currently allocated to a bed.")
        
    room = await db.rooms.find_one({"_id": ObjectId(room_id)})
    if room:
        beds = room.get("beds", [])
        for b in beds:
            if b["bed_number"] == bed_number:
                b["status"] = BedStatus.AVAILABLE.value
                b["student_id"] = None
                b["student_email"] = None
                b["student_name"] = None
                break
                
        occupied_count = sum(1 for b in beds if b.get("status") == BedStatus.OCCUPIED.value)
        capacity = room.get("capacity", len(beds))
        room_status = RoomStatus.FULL.value if occupied_count >= capacity else RoomStatus.AVAILABLE.value
        
        await db.rooms.update_one(
            {"_id": ObjectId(room_id)},
            {"$set": {
                "beds": beds,
                "status": room_status
            }}
        )
        
    student_updates = {
        "allocated_hostel_id": None,
        "allocated_room_id": None,
        "allocated_room_number": None,
        "allocated_bed_number": None,
        "status": StudentStatus.ACTIVE.value
    }
    
    await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": student_updates}
    )
    
    now = datetime.utcnow().isoformat()
    await db.allocation_history.insert_one({
        "student_id": student_id,
        "resident_id": student.get("resident_id"),
        "hostel_id": student.get("allocated_hostel_id"),
        "room_id": room_id,
        "bed_number": bed_number,
        "action": "DEALLOCATED",
        "performed_by": performed_by,
        "timestamp": now
    })
    
    return {"success": True, "message": "Student successfully deallocated"}

async def reallocate_student(db, student_id: str, new_hostel_id: str, new_room_id: str, new_bed_number: str, performed_by: str = "MANAGEMENT"):
    # First validate new allocation
    # Let's verify the new bed is available before releasing the current bed
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    if not student.get("allocated_room_id"):
        raise HTTPException(status_code=400, detail="Student is not currently allocated. Use allocate instead.")
        
    new_room = await db.rooms.find_one({"_id": ObjectId(new_room_id), "hostel_id": new_hostel_id})
    if not new_room:
        raise HTTPException(status_code=404, detail="Target room not found")
        
    new_bed = next((b for b in new_room.get("beds", []) if b["bed_number"] == new_bed_number), None)
    if not new_bed:
        raise HTTPException(status_code=404, detail="Target bed not found")
        
    if new_bed.get("status") != BedStatus.AVAILABLE.value or new_bed.get("student_id"):
        raise HTTPException(status_code=400, detail="Target bed is not available")
        
    # Proceed to deallocate
    await deallocate_student(db, student_id, performed_by)
    
    # Then allocate
    return await allocate_student(db, student_id, new_hostel_id, new_room_id, new_bed_number, performed_by)
