import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from backend.models import BedStatus, RoomStatus
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def repair_data():
    MONGO_URL = os.getenv("MONGODB_URI", os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.hostelos
    
    print("Starting data repair migration...")
    
    # 1. Reset all beds to available and recalculate rooms
    print("Resetting all beds...")
    rooms = await db.rooms.find().to_list(1000)
    for room in rooms:
        for bed in room.get("beds", []):
            if bed.get("status") == BedStatus.OCCUPIED.value:
                bed["status"] = BedStatus.AVAILABLE.value
                bed["student_id"] = None
                bed["student_email"] = None
                bed["student_name"] = None
                
        await db.rooms.update_one(
            {"_id": room["_id"]},
            {"$set": {
                "beds": room.get("beds", []),
                "status": RoomStatus.AVAILABLE.value
            }}
        )
        
    print("Re-allocating ACTIVE_RESIDENT students...")
    # 2. Re-allocate all ACTIVE_RESIDENT students based on their recorded allocation
    students = await db.students.find({"status": "ACTIVE_RESIDENT"}).to_list(1000)
    
    for student in students:
        room_id = student.get("allocated_room_id")
        bed_number = student.get("allocated_bed_number")
        hostel_id = student.get("allocated_hostel_id")
        
        if not room_id or not bed_number:
            print(f"Warning: Student {student.get('full_name')} is ACTIVE_RESIDENT but missing allocation data.")
            continue
            
        room = await db.rooms.find_one({"_id": ObjectId(room_id)})
        if not room:
            print(f"Error: Room {room_id} not found for student {student.get('full_name')}.")
            continue
            
        beds = room.get("beds", [])
        for bed in beds:
            if bed["bed_number"] == bed_number:
                bed["status"] = BedStatus.OCCUPIED.value
                bed["student_id"] = str(student["_id"])
                bed["student_email"] = student.get("email")
                bed["student_name"] = student.get("full_name")
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
        print(f"Re-allocated {student.get('full_name')} to Room {room.get('room_number')} Bed {bed_number}")
        
    print("Migration complete!")
    client.close()
    
if __name__ == "__main__":
    asyncio.run(repair_data())
