from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import base64
import io
from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
from emergentintegrations.llm.chat import LlmChat, UserMessage
import aiofiles
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ElevenLabs client
eleven_client = None
try:
    eleven_client = ElevenLabs(api_key=os.environ.get('ELEVENLABS_API_KEY'))
except Exception as e:
    logging.warning(f"ElevenLabs client initialization failed: {e}")

# Emergent LLM Key for AI features
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Azories API", description="Digital Book Creation Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Age ratings
AGE_RATINGS = ["All Ages", "5+", "8+", "12+", "16+"]

# Extended voice list with categories
EXTENDED_VOICES = [
    {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "category": "Young Female", "accent": "American"},
    {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "category": "Young Female", "accent": "American"},
    {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "category": "Young Female", "accent": "American"},
    {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "category": "Young Male", "accent": "American"},
    {"voice_id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "category": "Young Female", "accent": "American"},
    {"voice_id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "category": "Young Male", "accent": "American"},
    {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "category": "Male", "accent": "American"},
    {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "category": "Male", "accent": "American"},
    {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "category": "Young Male", "accent": "American"},
    {"voice_id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "category": "Male", "accent": "British"},
    {"voice_id": "XB0fDUnXU5powFXDhCwa", "name": "Charlotte", "category": "Female", "accent": "British"},
    {"voice_id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice", "category": "Young Female", "accent": "British"},
    {"voice_id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "category": "Young Female", "accent": "British"},
    {"voice_id": "bIHbv24MWmeRgasZH58o", "name": "Will", "category": "Young Male", "accent": "British"},
    {"voice_id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica", "category": "Female", "accent": "American"},
    {"voice_id": "cjVigY5qzO86Huf0OWal", "name": "Eric", "category": "Male", "accent": "American"},
    {"voice_id": "iP95p4xoKVk53GoZ742B", "name": "Chris", "category": "Male", "accent": "American"},
    {"voice_id": "nPczCjzI2devNBz1zQrb", "name": "Brian", "category": "Male", "accent": "American"},
    {"voice_id": "N2lVS1w4EtoT3dr4eOWO", "name": "Callum", "category": "Male", "accent": "Scottish"},
    {"voice_id": "TX3LPaxmHKxFdv7VOQHJ", "name": "Liam", "category": "Male", "accent": "Irish"},
]

# ============ MODELS ============

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    subscription: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class BookCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    genre: Optional[str] = "General"
    cover_image: Optional[str] = ""
    back_cover_image: Optional[str] = ""
    cover_title: Optional[str] = ""
    cover_subtitle: Optional[str] = ""
    back_cover_text: Optional[str] = ""
    layout_mode: Optional[str] = "standard"
    narrator_voice_id: Optional[str] = ""
    age_rating: Optional[str] = "All Ages"

class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    cover_image: Optional[str] = None
    back_cover_image: Optional[str] = None
    cover_title: Optional[str] = None
    cover_subtitle: Optional[str] = None
    back_cover_text: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_best_of_week: Optional[bool] = None
    layout_mode: Optional[str] = None
    narrator_voice_id: Optional[str] = None
    age_rating: Optional[str] = None

class BookResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    description: str
    genre: str
    cover_image: str
    back_cover_image: str
    cover_title: str
    cover_subtitle: str
    back_cover_text: str
    author_id: str
    author_name: str
    is_published: bool
    is_featured: bool
    is_best_of_week: bool
    layout_mode: str
    narrator_voice_id: str
    age_rating: str
    created_at: str
    updated_at: str
    chapter_count: int = 0
    total_pages: int = 0
    view_count: int = 0
    read_count: int = 0

class ChapterCreate(BaseModel):
    title: str
    order: int = 0

class ChapterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    book_id: str
    title: str
    order: int
    created_at: str

class PageCreate(BaseModel):
    text_content: str = ""
    image_url: Optional[str] = ""
    image_url_2: Optional[str] = ""
    image_url_3: Optional[str] = ""
    image_url_4: Optional[str] = ""
    video_url: Optional[str] = ""
    audio_url: Optional[str] = ""
    order: int = 0
    layout_type: Optional[str] = "single"

class PageUpdate(BaseModel):
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    image_url_2: Optional[str] = None
    image_url_3: Optional[str] = None
    image_url_4: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    order: Optional[int] = None
    layout_type: Optional[str] = None

class PageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    chapter_id: str
    text_content: str
    image_url: str
    image_url_2: str
    image_url_3: str
    image_url_4: str
    video_url: str
    audio_url: str
    order: int
    layout_type: str
    created_at: str

class ImageGenerateRequest(BaseModel):
    prompt: str
    book_id: Optional[str] = None
    style: Optional[str] = "illustration"

class VideoGenerateRequest(BaseModel):
    prompt: str
    duration: int = 4
    size: str = "1280x720"

class TTSRequest(BaseModel):
    text: str
    voice_id: str
    stability: float = 0.5
    similarity_boost: float = 0.75

class VoiceResponse(BaseModel):
    voice_id: str
    name: str
    category: Optional[str] = None
    accent: Optional[str] = None

class UpgradeRequest(BaseModel):
    subscription: str

class AIStoryRequest(BaseModel):
    idea: str
    genre: str = "Adventure"
    age_rating: str = "All Ages"
    num_pages: int = 5
    generate_images: bool = True

class SummaryGenerateRequest(BaseModel):
    book_id: str

class AnalyticsResponse(BaseModel):
    book_id: str
    title: str
    view_count: int
    read_count: int
    unique_readers: int
    avg_completion_rate: float
    daily_reads: list

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
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
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        return user
    except:
        return None

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": "user",
        "subscription": "free",
        "created_at": now
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id, user_data.email, "user")
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=user_data.email, name=user_data.name, role="user", subscription="free", created_at=now)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"], 
            email=user["email"], 
            name=user["name"], 
            role=user["role"], 
            subscription=user.get("subscription", "free"),
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        subscription=current_user.get("subscription", "free"),
        created_at=current_user["created_at"]
    )

@api_router.post("/auth/upgrade")
async def upgrade_subscription(request: UpgradeRequest, current_user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"subscription": request.subscription}}
    )
    return {"message": f"Subscription updated to {request.subscription}", "subscription": request.subscription}

@api_router.post("/auth/make-admin")
async def make_admin(current_user: dict = Depends(get_current_user)):
    """Make current user an admin (for testing)"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"role": "admin"}}
    )
    return {"message": "You are now an admin", "role": "admin"}

# ============ HELPER FUNCTIONS ============

def set_book_defaults(book: dict) -> dict:
    """Set default values for book fields"""
    book.setdefault("back_cover_image", "")
    book.setdefault("cover_title", book.get("title", ""))
    book.setdefault("cover_subtitle", "")
    book.setdefault("back_cover_text", "")
    book.setdefault("is_featured", False)
    book.setdefault("is_best_of_week", False)
    book.setdefault("layout_mode", "standard")
    book.setdefault("narrator_voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default to Rachel
    book.setdefault("age_rating", "All Ages")
    book.setdefault("view_count", 0)
    book.setdefault("read_count", 0)
    return book

async def get_book_with_counts(book: dict) -> dict:
    """Add chapter and page counts to book"""
    book = set_book_defaults(book)
    chapters = await db.chapters.find({"book_id": book["id"]}, {"_id": 0}).to_list(100)
    book["chapter_count"] = len(chapters)
    total_pages = 0
    for chapter in chapters:
        pages = await db.pages.count_documents({"chapter_id": chapter["id"]})
        total_pages += pages
    book["total_pages"] = total_pages
    return book

# ============ BOOK ROUTES ============

@api_router.post("/books", response_model=BookResponse)
async def create_book(book_data: BookCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required to create books")
    
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    book = {
        "id": book_id,
        "title": book_data.title,
        "description": book_data.description or "",
        "genre": book_data.genre or "General",
        "cover_image": book_data.cover_image or "",
        "back_cover_image": book_data.back_cover_image or "",
        "cover_title": book_data.cover_title or book_data.title,
        "cover_subtitle": book_data.cover_subtitle or "",
        "back_cover_text": book_data.back_cover_text or "",
        "author_id": current_user["id"],
        "author_name": current_user["name"],
        "is_published": False,
        "is_featured": False,
        "is_best_of_week": False,
        "layout_mode": book_data.layout_mode or "standard",
        "narrator_voice_id": book_data.narrator_voice_id or "21m00Tcm4TlvDq8ikWAM",
        "age_rating": book_data.age_rating or "All Ages",
        "view_count": 0,
        "read_count": 0,
        "created_at": now,
        "updated_at": now
    }
    await db.books.insert_one(book)
    return BookResponse(**book, chapter_count=0, total_pages=0)

@api_router.get("/books", response_model=List[BookResponse])
async def get_books(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    author: Optional[str] = None,
    published_only: bool = True,
    featured: Optional[bool] = None,
    best_of_week: Optional[bool] = None,
    age_rating: Optional[str] = None
):
    query = {}
    if published_only:
        query["is_published"] = True
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"author_name": {"$regex": search, "$options": "i"}}
        ]
    if genre and genre != "All":
        query["genre"] = genre
    if author:
        query["author_name"] = {"$regex": author, "$options": "i"}
    if featured is not None:
        query["is_featured"] = featured
    if best_of_week is not None:
        query["is_best_of_week"] = best_of_week
    if age_rating:
        query["age_rating"] = age_rating
    
    books = await db.books.find(query, {"_id": 0}).to_list(100)
    result = []
    for book in books:
        book = await get_book_with_counts(book)
        result.append(BookResponse(**book))
    return result

@api_router.get("/books/featured", response_model=List[BookResponse])
async def get_featured_books():
    query = {"is_published": True, "$or": [{"is_featured": True}, {"is_best_of_week": True}]}
    books = await db.books.find(query, {"_id": 0}).to_list(20)
    result = []
    for book in books:
        book = await get_book_with_counts(book)
        result.append(BookResponse(**book))
    return result

@api_router.get("/books/my", response_model=List[BookResponse])
async def get_my_books(current_user: dict = Depends(get_current_user)):
    books = await db.books.find({"author_id": current_user["id"]}, {"_id": 0}).to_list(100)
    result = []
    for book in books:
        book = await get_book_with_counts(book)
        result.append(BookResponse(**book))
    return result

@api_router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Increment view count
    await db.books.update_one({"id": book_id}, {"$inc": {"view_count": 1}})
    book["view_count"] = book.get("view_count", 0) + 1
    
    book = await get_book_with_counts(book)
    return BookResponse(**book)

@api_router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: str, book_data: BookUpdate, current_user: dict = Depends(get_current_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in book_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.books.update_one({"id": book_id}, {"$set": update_data})
    updated = await db.books.find_one({"id": book_id}, {"_id": 0})
    updated = await get_book_with_counts(updated)
    return BookResponse(**updated)

@api_router.delete("/books/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    for chapter in chapters:
        await db.pages.delete_many({"chapter_id": chapter["id"]})
    await db.chapters.delete_many({"book_id": book_id})
    await db.books.delete_one({"id": book_id})
    await db.analytics.delete_many({"book_id": book_id})
    
    return {"message": "Book deleted"}

# ============ ANALYTICS ============

@api_router.post("/books/{book_id}/track-read")
async def track_read(book_id: str, current_user: dict = Depends(get_optional_user)):
    """Track when a user reads a book"""
    await db.books.update_one({"id": book_id}, {"$inc": {"read_count": 1}})
    
    # Record analytics
    analytics = {
        "id": str(uuid.uuid4()),
        "book_id": book_id,
        "user_id": current_user["id"] if current_user else None,
        "action": "read",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.analytics.insert_one(analytics)
    return {"message": "Read tracked"}

@api_router.get("/books/{book_id}/analytics")
async def get_book_analytics(book_id: str, current_user: dict = Depends(get_current_user)):
    """Get analytics for a book (owner only)"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get unique readers
    unique_readers = await db.analytics.distinct("user_id", {"book_id": book_id, "user_id": {"$ne": None}})
    
    # Get daily reads for last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    daily_pipeline = [
        {"$match": {"book_id": book_id, "action": "read"}},
        {"$group": {
            "_id": {"$substr": ["$timestamp", 0, 10]},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 7}
    ]
    daily_reads = await db.analytics.aggregate(daily_pipeline).to_list(7)
    
    return {
        "book_id": book_id,
        "title": book["title"],
        "view_count": book.get("view_count", 0),
        "read_count": book.get("read_count", 0),
        "unique_readers": len(unique_readers),
        "avg_completion_rate": 0.85,  # Placeholder
        "daily_reads": [{"date": d["_id"], "count": d["count"]} for d in daily_reads]
    }

# ============ ADMIN CMS ROUTES ============

@api_router.get("/admin/books")
async def admin_get_all_books(current_user: dict = Depends(get_current_user)):
    """Admin endpoint to get all books for CMS"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    books = await db.books.find({}, {"_id": 0}).to_list(200)
    result = []
    for book in books:
        book = await get_book_with_counts(book)
        result.append(book)
    return result

@api_router.post("/admin/books/{book_id}/feature")
async def toggle_featured(book_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_featured", False)
    await db.books.update_one({"id": book_id}, {"$set": {"is_featured": new_status}})
    return {"is_featured": new_status}

@api_router.post("/admin/books/{book_id}/best-of-week")
async def toggle_best_of_week(book_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_best_of_week", False)
    await db.books.update_one({"id": book_id}, {"$set": {"is_best_of_week": new_status}})
    return {"is_best_of_week": new_status}

@api_router.post("/admin/books/{book_id}/age-rating")
async def set_age_rating(book_id: str, age_rating: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if age_rating not in AGE_RATINGS:
        raise HTTPException(status_code=400, detail=f"Invalid age rating. Must be one of: {AGE_RATINGS}")
    
    await db.books.update_one({"id": book_id}, {"$set": {"age_rating": age_rating}})
    return {"age_rating": age_rating}

@api_router.delete("/admin/books/{book_id}")
async def admin_delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Admin can delete any book"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    for chapter in chapters:
        await db.pages.delete_many({"chapter_id": chapter["id"]})
    await db.chapters.delete_many({"book_id": book_id})
    await db.books.delete_one({"id": book_id})
    return {"message": "Book deleted by admin"}

@api_router.get("/admin/analytics")
async def admin_get_analytics(current_user: dict = Depends(get_current_user)):
    """Get platform-wide analytics"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_books = await db.books.count_documents({})
    published_books = await db.books.count_documents({"is_published": True})
    total_users = await db.users.count_documents({})
    pro_users = await db.users.count_documents({"subscription": "pro"})
    
    # Top books by reads
    top_books = await db.books.find({"is_published": True}, {"_id": 0}).sort("read_count", -1).limit(10).to_list(10)
    
    return {
        "total_books": total_books,
        "published_books": published_books,
        "total_users": total_users,
        "pro_users": pro_users,
        "top_books": [{"id": b["id"], "title": b["title"], "reads": b.get("read_count", 0)} for b in top_books]
    }

# ============ CHAPTER ROUTES ============

@api_router.post("/books/{book_id}/chapters", response_model=ChapterResponse)
async def create_chapter(book_id: str, chapter_data: ChapterCreate, current_user: dict = Depends(get_current_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    chapter_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    if chapter_data.order == 0:
        max_order = await db.chapters.find_one({"book_id": book_id}, sort=[("order", -1)])
        chapter_data.order = (max_order["order"] + 1) if max_order else 1
    
    chapter = {
        "id": chapter_id,
        "book_id": book_id,
        "title": chapter_data.title,
        "order": chapter_data.order,
        "created_at": now
    }
    await db.chapters.insert_one(chapter)
    return ChapterResponse(**chapter)

@api_router.get("/books/{book_id}/chapters", response_model=List[ChapterResponse])
async def get_chapters(book_id: str):
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
    return [ChapterResponse(**c) for c in chapters]

@api_router.delete("/chapters/{chapter_id}")
async def delete_chapter(chapter_id: str, current_user: dict = Depends(get_current_user)):
    chapter = await db.chapters.find_one({"id": chapter_id}, {"_id": 0})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    book = await db.books.find_one({"id": chapter["book_id"]}, {"_id": 0})
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.pages.delete_many({"chapter_id": chapter_id})
    await db.chapters.delete_one({"id": chapter_id})
    return {"message": "Chapter deleted"}

# ============ PAGE ROUTES ============

@api_router.post("/chapters/{chapter_id}/pages", response_model=PageResponse)
async def create_page(chapter_id: str, page_data: PageCreate, current_user: dict = Depends(get_current_user)):
    chapter = await db.chapters.find_one({"id": chapter_id}, {"_id": 0})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    book = await db.books.find_one({"id": chapter["book_id"]}, {"_id": 0})
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    page_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    if page_data.order == 0:
        max_order = await db.pages.find_one({"chapter_id": chapter_id}, sort=[("order", -1)])
        page_data.order = (max_order["order"] + 1) if max_order else 1
    
    page = {
        "id": page_id,
        "chapter_id": chapter_id,
        "text_content": page_data.text_content,
        "image_url": page_data.image_url or "",
        "image_url_2": page_data.image_url_2 or "",
        "image_url_3": page_data.image_url_3 or "",
        "image_url_4": page_data.image_url_4 or "",
        "video_url": page_data.video_url or "",
        "audio_url": page_data.audio_url or "",
        "order": page_data.order,
        "layout_type": page_data.layout_type or "single",
        "created_at": now
    }
    await db.pages.insert_one(page)
    return PageResponse(**page)

@api_router.get("/chapters/{chapter_id}/pages", response_model=List[PageResponse])
async def get_pages(chapter_id: str):
    pages = await db.pages.find({"chapter_id": chapter_id}, {"_id": 0}).sort("order", 1).to_list(100)
    for page in pages:
        page.setdefault("image_url_2", "")
        page.setdefault("image_url_3", "")
        page.setdefault("image_url_4", "")
        page.setdefault("layout_type", "single")
    return [PageResponse(**p) for p in pages]

@api_router.put("/pages/{page_id}", response_model=PageResponse)
async def update_page(page_id: str, page_data: PageUpdate, current_user: dict = Depends(get_current_user)):
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    chapter = await db.chapters.find_one({"id": page["chapter_id"]}, {"_id": 0})
    book = await db.books.find_one({"id": chapter["book_id"]}, {"_id": 0})
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in page_data.model_dump().items() if v is not None}
    await db.pages.update_one({"id": page_id}, {"$set": update_data})
    updated = await db.pages.find_one({"id": page_id}, {"_id": 0})
    updated.setdefault("image_url_2", "")
    updated.setdefault("image_url_3", "")
    updated.setdefault("image_url_4", "")
    updated.setdefault("layout_type", "single")
    return PageResponse(**updated)

@api_router.delete("/pages/{page_id}")
async def delete_page(page_id: str, current_user: dict = Depends(get_current_user)):
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    chapter = await db.chapters.find_one({"id": page["chapter_id"]}, {"_id": 0})
    book = await db.books.find_one({"id": chapter["book_id"]}, {"_id": 0})
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.pages.delete_one({"id": page_id})
    return {"message": "Page deleted"}

# ============ AI GENERATION ROUTES ============

@api_router.post("/ai/generate-image")
async def generate_image(request: ImageGenerateRequest, current_user: dict = Depends(get_current_user)):
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        style_prompts = {
            "illustration": "Children's book illustration style, colorful, friendly, magical, whimsical, suitable for children",
            "comic": "Comic book panel style, bold lines, dynamic, colorful, speech bubble friendly, manga-inspired",
            "realistic": "Photorealistic style, detailed, cinematic lighting, professional photography"
        }
        style_desc = style_prompts.get(request.style, style_prompts["illustration"])
        full_prompt = f"{request.prompt}. Style: {style_desc}"
        
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return {"image_base64": image_base64, "success": True}
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

@api_router.post("/ai/generate-video")
async def generate_video(request: VideoGenerateRequest, current_user: dict = Depends(get_current_user)):
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        video_gen = OpenAIVideoGeneration(api_key=api_key)
        video_bytes = video_gen.text_to_video(
            prompt=f"Children's animated scene: {request.prompt}. Style: colorful, friendly, magical animation.",
            model="sora-2",
            size=request.size,
            duration=request.duration,
            max_wait_time=600
        )
        
        if video_bytes:
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
            return {"video_base64": video_base64, "success": True}
        else:
            raise HTTPException(status_code=500, detail="No video was generated")
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating video: {str(e)}")

@api_router.post("/ai/generate-story")
async def generate_story(request: AIStoryRequest, current_user: dict = Depends(get_current_user)):
    """Generate a complete story from an idea using AI"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    try:
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI not configured")
        
        # Generate story structure
        story_prompt = f"""Create a children's story based on this idea: "{request.idea}"
        
        Genre: {request.genre}
        Age Rating: {request.age_rating}
        Number of pages: {request.num_pages}
        
        Return a JSON object with this structure:
        {{
            "title": "Story Title",
            "description": "Brief description for the book",
            "back_cover_text": "Engaging back cover summary (2-3 sentences)",
            "pages": [
                {{
                    "page_number": 1,
                    "text": "Page text content (2-4 sentences appropriate for children)",
                    "image_prompt": "Detailed image prompt for illustration"
                }}
            ]
        }}
        
        Make it engaging, age-appropriate for {request.age_rating}, and ensure NO inappropriate content, violence, or bad language.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a children's book author. Create engaging, safe, age-appropriate stories."},
                {"role": "user", "content": story_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        story_data = json.loads(response.choices[0].message.content)
        
        # Create the book
        book_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        book = {
            "id": book_id,
            "title": story_data["title"],
            "description": story_data["description"],
            "genre": request.genre,
            "cover_image": "",
            "back_cover_image": "",
            "cover_title": story_data["title"],
            "cover_subtitle": "",
            "back_cover_text": story_data["back_cover_text"],
            "author_id": current_user["id"],
            "author_name": current_user["name"],
            "is_published": False,
            "is_featured": False,
            "is_best_of_week": False,
            "layout_mode": "standard",
            "narrator_voice_id": "21m00Tcm4TlvDq8ikWAM",
            "age_rating": request.age_rating,
            "view_count": 0,
            "read_count": 0,
            "created_at": now,
            "updated_at": now
        }
        await db.books.insert_one(book)
        
        # Create chapter
        chapter_id = str(uuid.uuid4())
        chapter = {
            "id": chapter_id,
            "book_id": book_id,
            "title": "Chapter 1",
            "order": 1,
            "created_at": now
        }
        await db.chapters.insert_one(chapter)
        
        # Create pages
        pages_created = []
        for idx, page_data in enumerate(story_data["pages"]):
            page_id = str(uuid.uuid4())
            page = {
                "id": page_id,
                "chapter_id": chapter_id,
                "text_content": page_data["text"],
                "image_url": "",
                "image_url_2": "",
                "image_url_3": "",
                "image_url_4": "",
                "video_url": "",
                "audio_url": "",
                "order": idx + 1,
                "layout_type": "single",
                "created_at": now,
                "image_prompt": page_data["image_prompt"]  # Store for image generation
            }
            await db.pages.insert_one(page)
            pages_created.append({
                "page_id": page_id,
                "order": idx + 1,
                "text": page_data["text"],
                "image_prompt": page_data["image_prompt"]
            })
        
        return {
            "success": True,
            "book_id": book_id,
            "title": story_data["title"],
            "pages_created": len(pages_created),
            "pages": pages_created,
            "message": "Story created! Navigate to editor to generate images."
        }
        
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating story: {str(e)}")

@api_router.post("/ai/generate-summary")
async def generate_summary(request: SummaryGenerateRequest, current_user: dict = Depends(get_current_user)):
    """Generate an AI summary for the back cover"""
    try:
        book = await db.books.find_one({"id": request.book_id}, {"_id": 0})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        if book["author_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get all page content
        chapters = await db.chapters.find({"book_id": request.book_id}, {"_id": 0}).to_list(100)
        all_text = []
        for chapter in chapters:
            pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).to_list(100)
            for page in pages:
                if page.get("text_content"):
                    all_text.append(page["text_content"])
        
        if not all_text:
            raise HTTPException(status_code=400, detail="Book has no content to summarize")
        
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI not configured")
        
        summary_prompt = f"""Create an engaging back cover summary for a children's book.

Book Title: {book['title']}
Genre: {book.get('genre', 'General')}
Age Rating: {book.get('age_rating', 'All Ages')}

Book content:
{' '.join(all_text[:2000])}

Write a captivating 2-3 sentence summary that would make children want to read this book. Keep it age-appropriate and exciting!"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You write engaging book summaries for children's books."},
                {"role": "user", "content": summary_prompt}
            ]
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Update book with summary
        await db.books.update_one(
            {"id": request.book_id},
            {"$set": {"back_cover_text": summary}}
        )
        
        return {"success": True, "summary": summary}
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

# ============ TTS ROUTES ============

@api_router.get("/voices", response_model=List[VoiceResponse])
async def get_voices():
    """Get extended list of voices"""
    try:
        if eleven_client:
            try:
                voices_response = eleven_client.voices.get_all()
                voices = []
                for voice in voices_response.voices:
                    voices.append(VoiceResponse(
                        voice_id=voice.voice_id,
                        name=voice.name,
                        category=voice.category if hasattr(voice, 'category') else "General",
                        accent="American"
                    ))
                if voices:
                    return voices
            except:
                pass
        
        # Return extended fallback voices
        return [VoiceResponse(**v) for v in EXTENDED_VOICES]
    except Exception as e:
        logger.error(f"Error fetching voices: {str(e)}")
        return [VoiceResponse(**v) for v in EXTENDED_VOICES]

@api_router.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    try:
        if not eleven_client:
            raise HTTPException(status_code=500, detail="TTS service not available")
        
        voice_settings = VoiceSettings(
            stability=request.stability,
            similarity_boost=request.similarity_boost
        )
        
        audio_generator = eleven_client.text_to_speech.convert(
            text=request.text,
            voice_id=request.voice_id,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings
        )
        
        audio_data = b""
        for chunk in audio_generator:
            audio_data += chunk
        
        audio_b64 = base64.b64encode(audio_data).decode()
        return {"audio_base64": audio_b64, "success": True}
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

# ============ FILE UPLOAD ============

@api_router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode('utf-8')
        content_type = file.content_type or "image/png"
        return {
            "image_url": f"data:{content_type};base64,{image_base64}",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@api_router.post("/upload/video")
async def upload_video(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        contents = await file.read()
        video_base64 = base64.b64encode(contents).decode('utf-8')
        content_type = file.content_type or "video/mp4"
        return {
            "video_url": f"data:{content_type};base64,{video_base64}",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

# ============ BOOK READING ============

@api_router.get("/books/{book_id}/full")
async def get_full_book(book_id: str, current_user: dict = Depends(get_optional_user)):
    """Get complete book - requires auth for full content"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = set_book_defaults(book)
    
    # If not logged in, only return book info (not pages content)
    if not current_user:
        return {
            **book,
            "chapters": [],
            "requires_auth": True,
            "message": "Sign in to read this book"
        }
    
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
    
    full_chapters = []
    for chapter in chapters:
        pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).sort("order", 1).to_list(100)
        for page in pages:
            page.setdefault("image_url_2", "")
            page.setdefault("image_url_3", "")
            page.setdefault("image_url_4", "")
            page.setdefault("layout_type", "single")
        full_chapters.append({
            **chapter,
            "pages": pages
        })
    
    return {
        **book,
        "chapters": full_chapters,
        "requires_auth": False
    }

@api_router.get("/books/{book_id}/preview")
async def get_book_preview(book_id: str):
    """Get book preview (cover + summary only) - no auth required"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = set_book_defaults(book)
    
    return {
        "id": book["id"],
        "title": book["title"],
        "description": book["description"],
        "cover_image": book["cover_image"],
        "back_cover_image": book["back_cover_image"],
        "cover_title": book["cover_title"],
        "cover_subtitle": book["cover_subtitle"],
        "back_cover_text": book["back_cover_text"],
        "author_name": book["author_name"],
        "genre": book["genre"],
        "age_rating": book["age_rating"],
        "narrator_voice_id": book["narrator_voice_id"]
    }

# ============ GENRES & RATINGS ============

@api_router.get("/genres")
async def get_genres():
    return {
        "genres": [
            "Adventure", "Fantasy", "Science Fiction", "Mystery", 
            "Fairy Tales", "Animals", "Friendship", "Family",
            "Educational", "Humor", "Nature", "Sports", "General",
            "Comic", "Superhero", "Horror", "Romance"
        ]
    }

@api_router.get("/age-ratings")
async def get_age_ratings():
    return {"age_ratings": AGE_RATINGS}

# ============ ROOT ============

@api_router.get("/")
async def root():
    return {"message": "Welcome to Azories API", "version": "1.1.0"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
