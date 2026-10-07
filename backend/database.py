from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.database_name]

async def get_db():
    yield db
