import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings
from backend.auth import get_password_hash

async def seed_db():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    count = await db.users.count_documents({})
    if count > 0:
        print("Database already seeded. Skipping.")
        return

    users = [
        {
            "email": "management@hostelos.com",
            "name": "Management Admin",
            "role": "MANAGEMENT",
            "hashed_password": get_password_hash("password")
        },
        {
            "email": "student@hostelos.com",
            "name": "Student User",
            "role": "STUDENT",
            "hashed_password": get_password_hash("password")
        }
    ]

    await db.users.insert_many(users)
    print("Database seeded with demo users:")
    print(" - management@hostelos.com / password")
    print(" - student@hostelos.com / password")

if __name__ == "__main__":
    asyncio.run(seed_db())
