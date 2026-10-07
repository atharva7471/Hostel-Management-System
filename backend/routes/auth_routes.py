from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from backend.database import get_db
from backend.models import UserResponse, Token
from backend.auth import verify_password, create_access_token, oauth2_scheme, get_current_user
from backend.config import settings
from datetime import timedelta
import jwt

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    from backend.models import RoleEnum, ApplicationStatus
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user = {
        "email": req.email,
        "name": req.name,
        "role": RoleEnum.STUDENT.value,
        "hashed_password": get_password_hash(req.password)
    }
    await db.users.insert_one(user)
    
    student_profile = {
        "full_name": req.name,
        "email": req.email,
        "student_id": "",
        "phone": "",
        "course": "",
        "year": "",
        "status": "ACTIVE",
        "application_status": ApplicationStatus.INCOMPLETE.value
    }
    await db.students.insert_one(student_profile)
    return {"message": "Registration successful"}
