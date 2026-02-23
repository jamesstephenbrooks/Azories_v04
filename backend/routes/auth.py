"""
Authentication routes for Azories API
Handles user registration, login, and authentication
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Get database from main app
db = None

def set_db(database):
    global db
    db = database

# Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    subscription: str
    credits: int
    created_at: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    favorite_genres: Optional[list] = None
    reading_goals: Optional[dict] = None
    achievements: Optional[list] = None
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    books_count: Optional[int] = 0
    is_vip: Optional[bool] = False
    pro_trial: Optional[bool] = False
    pro_trial_expires_at: Optional[str] = None
    trial_days_remaining: Optional[int] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# VIP email addresses (exempt from credit charges)
VIP_EMAILS = ["arianamillb@icloud.com", "jamesstephenbrooks@outlook.com"]

# JWT settings
JWT_SECRET = os.environ.get("JWT_SECRET", "azories-secret-key-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        if credentials and credentials.credentials:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
            return user
    except:
        pass
    return None

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if VIP email
    is_vip = user_data.email.lower() in [e.lower() for e in VIP_EMAILS]
    
    # Pro trial for all new users
    trial_expires = datetime.utcnow() + timedelta(days=30)
    
    user = {
        "id": str(uuid.uuid4()),
        "email": user_data.email.lower(),
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": "user",
        "subscription": "pro",  # Start with pro for trial
        "credits": 200 if is_vip else 0,  # VIPs get credits, others start with 0
        "is_vip": is_vip,
        "pro_trial": True,
        "pro_trial_expires_at": trial_expires.isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "avatar_url": None,
        "bio": None,
        "favorite_genres": [],
        "reading_goals": {"daily_pages": 10, "weekly_books": 1},
        "achievements": []
    }
    
    await db.users.insert_one(user)
    
    token = create_token(user["id"], user["email"], user["role"])
    
    # Calculate trial days remaining
    trial_days = (trial_expires - datetime.utcnow()).days
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            **{k: v for k, v in user.items() if k != "password"},
            "trial_days_remaining": trial_days
        }
    }

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email.lower()}, {"_id": 0})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    
    # Calculate trial days remaining
    trial_days = None
    if user.get("pro_trial") and user.get("pro_trial_expires_at"):
        try:
            expires = datetime.fromisoformat(user["pro_trial_expires_at"].replace("Z", "+00:00"))
            trial_days = max(0, (expires - datetime.utcnow()).days)
        except:
            pass
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            **{k: v for k, v in user.items() if k != "password"},
            "trial_days_remaining": trial_days
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    # Calculate trial days remaining
    trial_days = None
    if current_user.get("pro_trial") and current_user.get("pro_trial_expires_at"):
        try:
            expires = datetime.fromisoformat(current_user["pro_trial_expires_at"].replace("Z", "+00:00"))
            trial_days = max(0, (expires - datetime.utcnow()).days)
        except:
            pass
    
    return {
        **{k: v for k, v in current_user.items() if k != "password"},
        "trial_days_remaining": trial_days
    }
