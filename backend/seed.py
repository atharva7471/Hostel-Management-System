import asyncio
from datetime import datetime, timezone
import random
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

load_dotenv("backend/.env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MONGO_DETAILS = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.hostelos

def get_password_hash(password):
    return pwd_context.hash(password)

async def seed_demo_data():
    print("Seeding demo data...")

    # 1. Accounts
    await db.users.delete_many({})
    await db.students.delete_many({})
    await db.hostels.delete_many({})
    await db.rooms.delete_many({})

    print("Cleared existing users, students, hostels, and rooms.")

    # Create Management Account
    await db.users.insert_one({
        "email": "management@hostelos.com",
        "hashed_password": get_password_hash("password"),
        "role": "MANAGEMENT",
        "name": "Hostel Manager"
    })

    # Student Names & Details
    students_data = [
        {"name": "Atharva Bhosale", "email": "student@hostelos.com", "course": "BE AIML", "year": "4th Year", "sid": "CS2026-001", "status": "ACTIVE_RESIDENT", "app": "APPROVED"},
        {"name": "Siddhesh H.", "email": "siddhesh@hostelos.com", "course": "BE IT", "year": "4th Year", "sid": "IT2026-002", "status": "ACTIVE_RESIDENT", "app": "APPROVED"},
        {"name": "Rahul Patil", "email": "rahul@hostelos.com", "course": "BE COMP", "year": "3rd Year", "sid": "CS2027-003", "status": "ACTIVE_RESIDENT", "app": "APPROVED"},
        {"name": "Aditya Kulkarni", "email": "aditya@hostelos.com", "course": "BE EXTC", "year": "3rd Year", "sid": "EX2027-004", "status": "ACTIVE_RESIDENT", "app": "APPROVED"},
        {"name": "Omkar Jadhav", "email": "omkar@hostelos.com", "course": "BE CIVIL", "year": "2nd Year", "sid": "CV2028-005", "status": "ACTIVE_RESIDENT", "app": "APPROVED"},
        {"name": "Rohan Shinde", "email": "rohan@hostelos.com", "course": "BE MECH", "year": "2nd Year", "sid": "ME2028-006", "status": "ACTIVE_RESIDENT", "app": "APPROVED"},
        {"name": "Sneha Pawar", "email": "sneha@hostelos.com", "course": "BE COMP", "year": "1st Year", "sid": "CS2029-007", "status": "ACTIVE_RESIDENT", "app": "APPROVED"},
        {"name": "Pranav Deshmukh", "email": "pranav@hostelos.com", "course": "BE AIML", "year": "3rd Year", "sid": "AI2027-008", "status": "ACTIVE", "app": "APPROVED"},
        {"name": "Akash More", "email": "akash@hostelos.com", "course": "BE IT", "year": "2nd Year", "sid": "IT2028-009", "status": "ACTIVE", "app": "APPROVED"},
        {"name": "Neha Joshi", "email": "neha@hostelos.com", "course": "BE EXTC", "year": "1st Year", "sid": "EX2029-010", "status": "ACTIVE", "app": "UNDER_REVIEW"},
        {"name": "Vikram Singh", "email": "vikram@hostelos.com", "course": "BE COMP", "year": "4th Year", "sid": "CS2026-011", "status": "ACTIVE", "app": "UNDER_REVIEW"},
        {"name": "Pooja Sharma", "email": "pooja@hostelos.com", "course": "BE CIVIL", "year": "3rd Year", "sid": "CV2027-012", "status": "ACTIVE", "app": "UNDER_REVIEW"},
    ]

    for sd in students_data:
        await db.users.insert_one({
            "email": sd["email"],
            "hashed_password": get_password_hash("password"),
            "role": "STUDENT",
            "name": sd["name"]
        })

    # Create Hostels
    hostels_info = [
        {"name": "Boys Hostel A", "building": "Block A", "floors": 2, "desc": "Main boys hostel"},
        {"name": "Boys Hostel B", "building": "Block B", "floors": 2, "desc": "New boys hostel"}
    ]
    
    hostel_docs = []
    for h in hostels_info:
        res = await db.hostels.insert_one(h)
        hostel_docs.append({"_id": str(res.inserted_id), "name": h["name"]})

    print("Created Hostels:", [h["name"] for h in hostel_docs])

    # Create Rooms
    room_docs = []
    for h in hostel_docs:
        prefix = "A" if "A" in h["name"] else "B"
        for floor in [1, 2]:
            for r in [1, 2, 3, 4]:
                room_number = f"{prefix}-{floor}0{r}"
                capacity = 4 if r % 2 == 0 else 3 # mixed capacities
                
                beds = []
                for b in range(1, capacity + 1):
                    beds.append({
                        "bed_number": f"B{b}",
                        "status": "AVAILABLE",
                        "student_email": None,
                        "student_name": None
                    })

                # Example realistic statuses
                room_status = "AVAILABLE"
                if prefix == "A" and floor == 2 and r == 4:
                    room_status = "MAINTENANCE"
                    for bed in beds:
                        bed["status"] = "MAINTENANCE"

                res = await db.rooms.insert_one({
                    "hostel_id": h["_id"],
                    "room_number": room_number,
                    "floor": floor,
                    "capacity": capacity,
                    "status": room_status,
                    "beds": beds
                })
                room_docs.append({
                    "_id": str(res.inserted_id),
                    "room_number": room_number,
                    "hostel_id": h["_id"],
                    "beds": beds,
                    "capacity": capacity
                })

    print(f"Created {len(room_docs)} Rooms.")

    # Create Student Profiles and Allocate
    active_students = [sd for sd in students_data if sd["status"] == "ACTIVE_RESIDENT"]
    
    # We will distribute them across available beds
    allocation_index = 0
    available_beds_pool = []
    for r in room_docs:
        if r["room_number"] == "A-204": continue # maintenance
        for b in r["beds"]:
            if b["status"] == "AVAILABLE":
                available_beds_pool.append({
                    "room_id": r["_id"],
                    "room_number": r["room_number"],
                    "hostel_id": r["hostel_id"],
                    "bed_number": b["bed_number"],
                    "bed_idx": r["beds"].index(b)
                })
    
    today = datetime.now(timezone.utc).isoformat()

    resident_counter = 1
    for sd in students_data:
        profile = {
            "full_name": sd["name"],
            "student_id": sd["sid"],
            "email": sd["email"],
            "phone": "9876543210",
            "course": sd["course"],
            "year": sd["year"],
            "status": sd["status"],
            "application_status": sd["app"],
            "guardian_name": "Guardian Name",
            "guardian_phone": "9988776655",
            "preferred_hostel": "Boys Hostel A",
            "preferred_room_type": "3-Bed",
            "preferred_floor": "1",
            "special_requirements": "None"
        }
        
        if sd["status"] == "ACTIVE_RESIDENT" and allocation_index < len(available_beds_pool):
            bed_info = available_beds_pool[allocation_index]
            
            # Find hostel prefix
            hostel_name = "A" if "A" in [h["name"] for h in hostel_docs if h["_id"] == bed_info["hostel_id"]][0] else "B"
            res_id = f"HST-{hostel_name}-2026-{str(resident_counter).zfill(3)}"
            resident_counter += 1

            profile["allocated_hostel_id"] = bed_info["hostel_id"]
            profile["allocated_room_id"] = bed_info["room_id"]
            profile["allocated_room_number"] = bed_info["room_number"]
            profile["allocated_bed_number"] = bed_info["bed_number"]
            profile["resident_id"] = res_id
            profile["allocation_date"] = today
            
            # Update room document in DB
            await db.rooms.update_one(
                {"_id": bed_info["room_id"]},
                {
                    "$set": {
                        f"beds.{bed_info['bed_idx']}.status": "OCCUPIED",
                        f"beds.{bed_info['bed_idx']}.student_email": sd["email"],
                        f"beds.{bed_info['bed_idx']}.student_name": sd["name"]
                    }
                }
            )
            allocation_index += 1
            
        await db.students.insert_one(profile)

    print("Student profiles created and allocated.")
    print("Seed complete!")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
