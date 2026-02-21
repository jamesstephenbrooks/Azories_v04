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
import aiohttp
from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
from emergentintegrations.llm.chat import LlmChat, UserMessage
import aiofiles
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

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
    series_id: Optional[str] = None
    series_order: Optional[int] = None

class SeriesCreate(BaseModel):
    name: str
    description: str = ""

class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

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
    duration: int = 5
    size: str = "1280x720"  # Valid sizes: 1280x720, 1792x1024, 1024x1792, 1024x1024
    style: Optional[str] = "animation"

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
    media_type: str = "images"  # images, videos, cinemagraphs, none
    image_style: str = "illustration"

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

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_name: str

# Admin credentials (in production, these should be in environment variables)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'azories_admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'AzoriesAdmin2024!')

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
    except Exception:
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
    book.setdefault("series_id", None)
    book.setdefault("series_order", None)
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
        "series_id": None,
        "series_order": None,
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

@api_router.get("/books/{book_id}/download")
async def download_book_pdf(book_id: str, current_user: dict = Depends(get_current_user)):
    """Download a book as interactive PDF (for the creator only)"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the book creator can download")
    
    # Get all chapters and pages
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
    for chapter in chapters:
        pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).sort("order", 1).to_list(100)
        chapter["pages"] = pages
    
    # Create PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4
    
    # Cover Page
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 200, book.get("cover_title", book["title"]))
    
    if book.get("cover_subtitle"):
        c.setFont("Helvetica", 18)
        c.drawCentredString(width / 2, height - 240, book["cover_subtitle"])
    
    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(width / 2, height - 300, f"By {book['author_name']}")
    
    # Try to add cover image
    if book.get("cover_image") and book["cover_image"].startswith("data:image"):
        try:
            img_data = book["cover_image"].split(",")[1]
            img_bytes = base64.b64decode(img_data)
            img = PILImage.open(io.BytesIO(img_bytes))
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            c.drawImage(ImageReader(img_buffer), 150, height - 600, width=300, height=250, preserveAspectRatio=True)
        except Exception:
            pass
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 50, f"Created with Azories - {book.get('age_rating', 'All Ages')}")
    c.showPage()
    
    # Back cover with description
    if book.get("back_cover_text"):
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 100, "About This Book")
        c.setFont("Helvetica", 12)
        
        # Word wrap the description
        description = book["back_cover_text"]
        lines = []
        words = description.split()
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) < 70:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        y_pos = height - 150
        for line in lines:
            c.drawCentredString(width / 2, y_pos, line)
            y_pos -= 20
        c.showPage()
    
    # Content pages
    page_num = 1
    for chapter in chapters:
        # Chapter title page
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width / 2, height / 2 + 50, chapter["title"])
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height / 2, f"Chapter {chapter['order']}")
        c.showPage()
        
        for page in chapter["pages"]:
            # Add page image if exists
            if page.get("image_url") and page["image_url"].startswith("data:image"):
                try:
                    img_data = page["image_url"].split(",")[1]
                    img_bytes = base64.b64decode(img_data)
                    img = PILImage.open(io.BytesIO(img_bytes))
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    c.drawImage(ImageReader(img_buffer), 50, height - 400, width=500, height=350, preserveAspectRatio=True)
                except Exception:
                    pass
            
            # Add text content
            if page.get("text_content"):
                c.setFont("Helvetica", 12)
                lines = []
                words = page["text_content"].split()
                current_line = ""
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if len(test_line) < 80:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                
                y_pos = 350 if page.get("image_url") else height - 100
                for line in lines:
                    c.drawString(50, y_pos, line)
                    y_pos -= 18
                    if y_pos < 80:
                        break
            
            # Page number
            c.setFont("Helvetica", 10)
            c.drawCentredString(width / 2, 30, f"Page {page_num}")
            page_num += 1
            c.showPage()
    
    # End page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height / 2, "The End")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height / 2 - 40, f"Thank you for reading {book['title']}")
    c.drawCentredString(width / 2, height / 2 - 60, "Created with Azories")
    c.showPage()
    
    c.save()
    pdf_buffer.seek(0)
    
    filename = f"{book['title'].replace(' ', '_')}_azories_book.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ============ READING PROGRESS ============

class ReadingProgressUpdate(BaseModel):
    book_id: str
    current_page: int
    total_pages: int
    chapter_id: Optional[str] = None

@api_router.post("/reading-progress")
async def update_reading_progress(progress: ReadingProgressUpdate, current_user: dict = Depends(get_current_user)):
    """Update user's reading progress for a book"""
    progress_data = {
        "user_id": current_user["id"],
        "book_id": progress.book_id,
        "current_page": progress.current_page,
        "total_pages": progress.total_pages,
        "progress_percent": round((progress.current_page / max(progress.total_pages, 1)) * 100, 1),
        "chapter_id": progress.chapter_id,
        "last_read": datetime.now(timezone.utc).isoformat(),
        "completed": progress.current_page >= progress.total_pages - 1
    }
    
    await db.reading_progress.update_one(
        {"user_id": current_user["id"], "book_id": progress.book_id},
        {"$set": progress_data},
        upsert=True
    )
    
    # Update reading streak
    today = datetime.now(timezone.utc).date().isoformat()
    await db.reading_streaks.update_one(
        {"user_id": current_user["id"]},
        {
            "$addToSet": {"reading_days": today},
            "$set": {"last_read_date": today}
        },
        upsert=True
    )
    
    return {"message": "Progress saved", "progress_percent": progress_data["progress_percent"]}

@api_router.get("/reading-progress/{book_id}")
async def get_reading_progress(book_id: str, current_user: dict = Depends(get_current_user)):
    """Get user's reading progress for a book"""
    progress = await db.reading_progress.find_one(
        {"user_id": current_user["id"], "book_id": book_id},
        {"_id": 0}
    )
    return progress or {"current_page": 0, "progress_percent": 0, "completed": False}

@api_router.get("/reading-stats")
async def get_reading_stats(current_user: dict = Depends(get_current_user)):
    """Get user's overall reading statistics"""
    # Get all reading progress
    all_progress = await db.reading_progress.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    # Get reading streak
    streak_data = await db.reading_streaks.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    # Calculate current streak
    current_streak = 0
    if streak_data and streak_data.get("reading_days"):
        from datetime import date
        today = date.today()
        sorted_days = sorted(streak_data["reading_days"], reverse=True)
        for i, day_str in enumerate(sorted_days):
            day = date.fromisoformat(day_str)
            expected_day = today - timedelta(days=i)
            if day == expected_day:
                current_streak += 1
            else:
                break
    
    completed_books = sum(1 for p in all_progress if p.get("completed"))
    in_progress_books = sum(1 for p in all_progress if not p.get("completed") and p.get("current_page", 0) > 0)
    
    return {
        "total_books_started": len(all_progress),
        "completed_books": completed_books,
        "in_progress_books": in_progress_books,
        "current_streak": current_streak,
        "total_reading_days": len(streak_data.get("reading_days", [])) if streak_data else 0,
        "recent_books": all_progress[:5]
    }

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

# ============ SERIES MANAGEMENT ============

@api_router.post("/series")
async def create_series(series_data: SeriesCreate, current_user: dict = Depends(get_current_user)):
    """Create a new book series"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    series_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    series = {
        "id": series_id,
        "name": series_data.name,
        "description": series_data.description or "",
        "author_id": current_user["id"],
        "author_name": current_user["name"],
        "book_count": 0,
        "created_at": now,
        "updated_at": now
    }
    await db.series.insert_one(series)
    # Return without _id
    del series["_id"]
    return series

@api_router.get("/series")
async def get_user_series(current_user: dict = Depends(get_current_user)):
    """Get all series for the current user"""
    series_list = await db.series.find({"author_id": current_user["id"]}, {"_id": 0}).to_list(100)
    
    # Get book counts for each series
    for series in series_list:
        book_count = await db.books.count_documents({"series_id": series["id"]})
        series["book_count"] = book_count
        
        # Get books in this series
        books = await db.books.find(
            {"series_id": series["id"]}, 
            {"_id": 0, "id": 1, "title": 1, "cover_image": 1, "series_order": 1}
        ).sort("series_order", 1).to_list(100)
        series["books"] = books
    
    return series_list

@api_router.get("/series/{series_id}")
async def get_series(series_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific series with its books"""
    series = await db.series.find_one({"id": series_id}, {"_id": 0})
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    if series["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    books = await db.books.find(
        {"series_id": series_id}, 
        {"_id": 0}
    ).sort("series_order", 1).to_list(100)
    
    return {**series, "books": books}

@api_router.put("/series/{series_id}")
async def update_series(series_id: str, series_data: SeriesUpdate, current_user: dict = Depends(get_current_user)):
    """Update a series"""
    series = await db.series.find_one({"id": series_id})
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    if series["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in series_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.series.update_one({"id": series_id}, {"$set": update_data})
    updated = await db.series.find_one({"id": series_id}, {"_id": 0})
    return updated

@api_router.delete("/series/{series_id}")
async def delete_series(series_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a series (books will be unlinked, not deleted)"""
    series = await db.series.find_one({"id": series_id})
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    if series["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Unlink all books from this series
    await db.books.update_many(
        {"series_id": series_id},
        {"$set": {"series_id": None, "series_order": None}}
    )
    
    await db.series.delete_one({"id": series_id})
    return {"message": "Series deleted"}

@api_router.post("/series/{series_id}/books/{book_id}")
async def add_book_to_series(series_id: str, book_id: str, order: int = 0, current_user: dict = Depends(get_current_user)):
    """Add a book to a series"""
    series = await db.series.find_one({"id": series_id})
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if series["author_id"] != current_user["id"] or book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # If no order specified, put at the end
    if order == 0:
        max_order = await db.books.find_one(
            {"series_id": series_id},
            sort=[("series_order", -1)]
        )
        order = (max_order.get("series_order", 0) + 1) if max_order else 1
    
    await db.books.update_one(
        {"id": book_id},
        {"$set": {"series_id": series_id, "series_order": order}}
    )
    
    return {"message": "Book added to series", "order": order}

@api_router.delete("/series/{series_id}/books/{book_id}")
async def remove_book_from_series(series_id: str, book_id: str, current_user: dict = Depends(get_current_user)):
    """Remove a book from a series"""
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.books.update_one(
        {"id": book_id},
        {"$set": {"series_id": None, "series_order": None}}
    )
    
    return {"message": "Book removed from series"}

# ============ ADMIN CMS ROUTES (Separate Admin Auth) ============

# Admin-specific authentication
async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if not payload.get("admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid admin token")

@api_router.post("/admin/login", response_model=AdminResponse)
async def admin_login(login_data: AdminLogin):
    """Separate admin login endpoint"""
    if login_data.username != ADMIN_USERNAME or login_data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    # Create admin JWT token
    expiration = datetime.now(timezone.utc) + timedelta(hours=8)
    token_data = {
        "admin": True,
        "username": login_data.username,
        "exp": expiration
    }
    token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return AdminResponse(
        access_token=token,
        admin_name=login_data.username
    )

@api_router.get("/admin/verify")
async def verify_admin(admin: dict = Depends(get_admin_user)):
    """Verify admin token is valid"""
    return {"valid": True, "username": admin.get("username")}

@api_router.get("/admin/books")
async def admin_get_all_books(admin: dict = Depends(get_admin_user)):
    """Admin endpoint to get all books for CMS"""
    books = await db.books.find({}, {"_id": 0}).to_list(200)
    result = []
    for book in books:
        book = await get_book_with_counts(book)
        result.append(book)
    return result

@api_router.get("/admin/users")
async def admin_get_all_users(admin: dict = Depends(get_admin_user)):
    """Admin endpoint to get all users"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.post("/admin/books/{book_id}/feature")
async def toggle_featured(book_id: str, admin: dict = Depends(get_admin_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_featured", False)
    await db.books.update_one({"id": book_id}, {"$set": {"is_featured": new_status}})
    return {"is_featured": new_status}

@api_router.post("/admin/books/{book_id}/best-of-week")
async def toggle_best_of_week(book_id: str, admin: dict = Depends(get_admin_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_best_of_week", False)
    await db.books.update_one({"id": book_id}, {"$set": {"is_best_of_week": new_status}})
    return {"is_best_of_week": new_status}

@api_router.post("/admin/books/{book_id}/age-rating")
async def set_age_rating(book_id: str, age_rating: str, admin: dict = Depends(get_admin_user)):
    if age_rating not in AGE_RATINGS:
        raise HTTPException(status_code=400, detail=f"Invalid age rating. Must be one of: {AGE_RATINGS}")
    
    await db.books.update_one({"id": book_id}, {"$set": {"age_rating": age_rating}})
    return {"age_rating": age_rating}

@api_router.post("/admin/books/{book_id}/publish")
async def admin_publish_book(book_id: str, admin: dict = Depends(get_admin_user)):
    """Admin can publish/unpublish any book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_published", False)
    await db.books.update_one({"id": book_id}, {"$set": {"is_published": new_status}})
    return {"is_published": new_status}

@api_router.delete("/admin/books/{book_id}")
async def admin_delete_book(book_id: str, admin: dict = Depends(get_admin_user)):
    """Admin can delete any book"""
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    for chapter in chapters:
        await db.pages.delete_many({"chapter_id": chapter["id"]})
    await db.chapters.delete_many({"book_id": book_id})
    await db.books.delete_one({"id": book_id})
    return {"message": "Book deleted by admin"}

@api_router.get("/admin/analytics")
async def admin_get_analytics(admin: dict = Depends(get_admin_user)):
    """Get platform-wide analytics"""
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
            "realistic": "Photorealistic style, detailed, cinematic lighting, professional photography",
            "scifi": "Science fiction style, futuristic, space themes, neon colors, advanced technology, cosmic landscapes, sleek spacecraft, alien worlds, holographic elements",
            "sketch": "Hand-drawn pencil sketch style, black and white with subtle shading, artistic hatching, rough texture, storyboard feel",
            "watercolor": "Watercolor painting style, soft blended colors, artistic brush strokes, dreamy atmosphere, gentle gradients",
            "anime": "Japanese anime style, big expressive eyes, vibrant colors, clean lines, manga-inspired character design",
            "fantasy": "Epic fantasy art style, magical lighting, dramatic composition, detailed environments, mystical creatures",
            "pixar": "3D animated Pixar style, smooth textures, expressive characters, warm lighting, playful and appealing design",
            "storybook": "Classic storybook illustration, vintage children's book style, warm earthy tones, gentle and cozy atmosphere"
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
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        style_prompts = {
            "animation": "colorful, friendly, magical animation suitable for children",
            "scifi": "futuristic science fiction style with space themes, neon colors, advanced technology, cosmic visuals",
            "realistic": "photorealistic cinematic style with professional lighting",
            "comic": "animated comic book style with bold colors and dynamic movement",
            "anime": "Japanese anime animation style with vibrant colors and expressive characters",
            "fantasy": "magical fantasy style with enchanted worlds and mystical creatures",
            "pixar": "3D animated Pixar-style with smooth textures and expressive characters",
            "watercolor": "dreamy watercolor animation with soft blended colors and artistic brush strokes"
        }
        style_desc = style_prompts.get(request.style, style_prompts["animation"])
        
        video_gen = OpenAIVideoGeneration(api_key=EMERGENT_LLM_KEY)
        video_bytes = video_gen.text_to_video(
            prompt=f"{request.prompt}. Style: {style_desc}",
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
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        # Generate story structure using Emergent LLM Chat
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
        Return ONLY the JSON object, no other text."""
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"story-gen-{current_user['id']}-{str(uuid.uuid4())[:8]}",
            system_message="You are a children's book author. Create engaging, safe, age-appropriate stories. Always respond with valid JSON only."
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=story_prompt))
        
        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            story_data = json.loads(response_text.strip())
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                story_data = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail="Failed to parse story data")
        
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

class GenerateAllImagesRequest(BaseModel):
    book_id: str
    style: Optional[str] = "illustration"

class GenerateImagesFromTextRequest(BaseModel):
    book_id: str
    style: Optional[str] = "illustration"

@api_router.post("/ai/generate-all-images")
async def generate_all_images(request: GenerateAllImagesRequest, current_user: dict = Depends(get_current_user)):
    """Generate AI images for all pages in a book that don't have images"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    book = await db.books.find_one({"id": request.book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    try:
        
        style_prompts = {
            "illustration": "Children's book illustration style, colorful, friendly, magical, whimsical",
            "comic": "Comic book panel style, bold lines, dynamic, colorful",
            "realistic": "Photorealistic style, detailed, cinematic lighting",
            "scifi": "Science fiction style, futuristic, space themes, neon colors, advanced technology"
        }
        style_desc = style_prompts.get(request.style, style_prompts["illustration"])
        
        # Get all pages that need images
        chapters = await db.chapters.find({"book_id": request.book_id}, {"_id": 0}).to_list(100)
        pages_updated = []
        
        for chapter in chapters:
            pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).to_list(100)
            for page in pages:
                # Skip pages that already have images
                if page.get("image_url"):
                    continue
                
                # Generate image from stored prompt or text content
                prompt = page.get("image_prompt") or page.get("text_content", "A magical scene")
                
                try:
                    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
                    images = await image_gen.generate_images(
                        prompt=f"{prompt}. Style: {style_desc}",
                        model="gpt-image-1",
                        number_of_images=1
                    )
                    
                    if images and len(images) > 0:
                        image_base64 = base64.b64encode(images[0]).decode('utf-8')
                        image_url = f"data:image/png;base64,{image_base64}"
                        
                        await db.pages.update_one(
                            {"id": page["id"]},
                            {"$set": {"image_url": image_url}}
                        )
                        pages_updated.append({"page_id": page["id"], "order": page["order"]})
                except Exception as img_error:
                    logger.error(f"Error generating image for page {page['id']}: {str(img_error)}")
                    continue
        
        return {
            "success": True,
            "pages_updated": len(pages_updated),
            "pages": pages_updated,
            "message": f"Generated images for {len(pages_updated)} pages"
        }
        
    except Exception as e:
        logger.error(f"Error generating all images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating images: {str(e)}")

@api_router.post("/ai/generate-images-from-text")
async def generate_images_from_text(request: GenerateImagesFromTextRequest, current_user: dict = Depends(get_current_user)):
    """Generate AI images for all pages based on their text content"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    book = await db.books.find_one({"id": request.book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    try:
        
        style_prompts = {
            "illustration": "Children's book illustration style, colorful, friendly, magical, whimsical",
            "comic": "Comic book panel style, bold lines, dynamic, colorful",
            "realistic": "Photorealistic style, detailed, cinematic lighting",
            "scifi": "Science fiction style, futuristic, space themes, neon colors, advanced technology"
        }
        style_desc = style_prompts.get(request.style, style_prompts["illustration"])
        
        # Get all pages with text content
        chapters = await db.chapters.find({"book_id": request.book_id}, {"_id": 0}).to_list(100)
        pages_updated = []
        
        for chapter in chapters:
            pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).to_list(100)
            for page in pages:
                text_content = page.get("text_content", "").strip()
                if not text_content:
                    continue
                
                # First, generate an image prompt from the text
                try:
                    chat = LlmChat(
                        api_key=EMERGENT_LLM_KEY,
                        session_id=f"img-prompt-{current_user['id']}-{str(uuid.uuid4())[:8]}",
                        system_message="You create detailed image prompts for children's book illustrations. Keep them safe and appropriate."
                    ).with_model("openai", "gpt-4o-mini")
                    
                    prompt_response = await chat.send_message(UserMessage(
                        text=f"Create a detailed illustration prompt for this children's book page text. Only output the prompt, no explanation:\n\n{text_content}"
                    ))
                    image_prompt = prompt_response.strip()
                    
                    # Generate the image
                    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
                    images = await image_gen.generate_images(
                        prompt=f"{image_prompt}. Style: {style_desc}",
                        model="gpt-image-1",
                        number_of_images=1
                    )
                    
                    if images and len(images) > 0:
                        image_base64 = base64.b64encode(images[0]).decode('utf-8')
                        image_url = f"data:image/png;base64,{image_base64}"
                        
                        await db.pages.update_one(
                            {"id": page["id"]},
                            {"$set": {"image_url": image_url, "image_prompt": image_prompt}}
                        )
                        pages_updated.append({"page_id": page["id"], "order": page["order"]})
                except Exception as img_error:
                    logger.error(f"Error generating image for page {page['id']}: {str(img_error)}")
                    continue
        
        return {
            "success": True,
            "pages_updated": len(pages_updated),
            "pages": pages_updated,
            "message": f"Generated images for {len(pages_updated)} pages based on text content"
        }
        
    except Exception as e:
        logger.error(f"Error generating images from text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating images: {str(e)}")

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
        
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        summary_prompt = f"""Create an engaging back cover summary for a children's book.

Book Title: {book['title']}
Genre: {book.get('genre', 'General')}
Age Rating: {book.get('age_rating', 'All Ages')}

Book content:
{' '.join(all_text[:2000])}

Write a captivating 2-3 sentence summary that would make children want to read this book. Keep it age-appropriate and exciting!"""
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"summary-gen-{current_user['id']}-{str(uuid.uuid4())[:8]}",
            system_message="You write engaging book summaries for children's books."
        ).with_model("openai", "gpt-4o-mini")
        
        summary = await chat.send_message(UserMessage(text=summary_prompt))
        summary = summary.strip()
        
        # Update book with summary
        await db.books.update_one(
            {"id": request.book_id},
            {"$set": {"back_cover_text": summary}}
        )
        
        return {"success": True, "summary": summary}
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


# ============ AI READING BUDDY ============

class ReadingBuddyRequest(BaseModel):
    book_id: str
    book_title: str
    book_genre: Optional[str] = "General"
    current_page: int = 0
    book_context: str = ""
    question: str
    chat_history: List[dict] = []

@api_router.post("/ai/reading-buddy")
async def ai_reading_buddy(request: ReadingBuddyRequest):
    """AI Reading Buddy - helps readers understand and engage with the story"""
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        # Build context for the AI
        system_prompt = f"""You are a friendly and enthusiastic reading buddy for children and young readers. 
You're helping someone read "{request.book_title}" (a {request.book_genre} book).

Your role is to:
- Help explain parts of the story they don't understand
- Make predictions about what might happen next (without spoilers if you don't know)
- Discuss characters, themes, and plot points
- Keep readers engaged and excited about the story
- Use age-appropriate language and be encouraging
- Be warm, supportive, and fun!

Keep your responses concise (2-4 sentences usually) and conversational.
If asked about something not in the provided context, be honest that you only know what's been read so far."""

        # Build the conversation
        messages = []
        
        # Add context about what's been read
        if request.book_context:
            context_msg = f"Here's what the reader has read so far (they're on page {request.current_page + 1}):\n\n{request.book_context}"
            messages.append({"role": "system", "content": context_msg})
        
        # Add chat history
        for msg in request.chat_history[-4:]:  # Last 4 messages for context
            messages.append(msg)
        
        # Create the chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"reading-buddy-{request.book_id}-{str(uuid.uuid4())[:8]}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o-mini")
        
        # Send the question
        response = await chat.send_message(UserMessage(text=request.question))
        
        return {"response": response.strip()}
        
    except Exception as e:
        logger.error(f"Error in AI Reading Buddy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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
            except Exception:
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

# ============ SEED TEST DATA ============

@api_router.post("/admin/seed-test-books")
async def seed_test_books(admin: dict = Depends(get_admin_user)):
    """Seed the database with test books for development"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Create test author if not exists
    test_author = await db.users.find_one({"email": "testauthor@azories.com"}, {"_id": 0})
    if not test_author:
        author_id = str(uuid.uuid4())
        test_author = {
            "id": author_id,
            "email": "testauthor@azories.com",
            "password": bcrypt.hashpw("TestAuthor123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "name": "Azories Team",
            "role": "user",
            "subscription": "pro",
            "created_at": now
        }
        await db.users.insert_one(test_author)
    
    author_id = test_author["id"]
    author_name = test_author["name"]
    
    # Test books data
    test_books = [
        {
            "title": "The Dragon's Secret",
            "description": "A young wizard discovers a baby dragon and must protect it from evil hunters.",
            "genre": "Fantasy",
            "cover_image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400",
            "back_cover_text": "When 10-year-old Maya finds a dragon egg in the forest, her life changes forever. Join her magical adventure!",
            "age_rating": "7-9 years"
        },
        {
            "title": "Space Explorers: Mission to Mars",
            "description": "Three kids embark on humanity's first mission to Mars.",
            "genre": "Science Fiction",
            "cover_image": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400",
            "back_cover_text": "In 2050, three brave children become the youngest astronauts to travel to Mars. An exciting sci-fi adventure!",
            "age_rating": "10-12 years"
        },
        {
            "title": "The Mystery of the Missing Cookies",
            "description": "Detective Dog and Cat solve the biggest mystery in Petville.",
            "genre": "Mystery",
            "cover_image": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
            "back_cover_text": "Who took the cookies from the cookie jar? Join Detective Dog in this fun mystery!",
            "age_rating": "All Ages"
        },
        {
            "title": "Friendship Island",
            "description": "Five friends get stranded on an island and learn about teamwork.",
            "genre": "Adventure",
            "cover_image": "https://images.unsplash.com/photo-1559128010-7c1ad6e1b6a5?w=400",
            "back_cover_text": "When their boat drifts away, five friends must work together to survive on a mysterious island.",
            "age_rating": "7-9 years"
        },
        {
            "title": "The Robot Who Wanted Friends",
            "description": "A lonely robot learns what it means to have friends.",
            "genre": "Science Fiction",
            "cover_image": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400",
            "back_cover_text": "ROBO-7 was built to work, but all he wants is a friend. A heartwarming story about friendship.",
            "age_rating": "All Ages"
        },
        {
            "title": "Princess and the Enchanted Forest",
            "description": "Princess Luna discovers a magical forest full of talking animals.",
            "genre": "Fairy Tales",
            "cover_image": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=400",
            "back_cover_text": "Beyond the castle walls lies a forest where animals talk and magic is real. Join Princess Luna's adventure!",
            "age_rating": "All Ages"
        },
        {
            "title": "The Dinosaur Time Machine",
            "description": "Two siblings accidentally travel back to the age of dinosaurs.",
            "genre": "Adventure",
            "cover_image": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=400",
            "back_cover_text": "When Sam and Emma fix grandpa's old machine, they didn't expect to meet real dinosaurs!",
            "age_rating": "7-9 years"
        },
        {
            "title": "Ocean Wonders",
            "description": "Explore the magical world beneath the waves.",
            "genre": "Educational",
            "cover_image": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "back_cover_text": "Dive deep into the ocean and discover amazing creatures you never knew existed!",
            "age_rating": "All Ages"
        },
        {
            "title": "The Superhero School",
            "description": "A regular kid discovers they have superpowers on their first day at a new school.",
            "genre": "Superhero",
            "cover_image": "https://images.unsplash.com/photo-1531259683007-016a7b628fc3?w=400",
            "back_cover_text": "Jake thought he was ordinary until his first day at Hero Academy revealed his true powers!",
            "age_rating": "10-12 years"
        },
        {
            "title": "Cooking Adventures with Chef Cat",
            "description": "Chef Cat teaches kids fun and easy recipes.",
            "genre": "Educational",
            "cover_image": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400",
            "back_cover_text": "Learn to make delicious treats with Chef Cat's simple recipes that kids can make!",
            "age_rating": "All Ages"
        },
        {
            "title": "The Haunted Treehouse",
            "description": "Three friends investigate strange sounds coming from an old treehouse.",
            "genre": "Mystery",
            "cover_image": "https://images.unsplash.com/photo-1520637836993-a071674a76e7?w=400",
            "back_cover_text": "Is the old treehouse really haunted? Join the Mystery Kids as they find out the truth!",
            "age_rating": "7-9 years"
        },
        {
            "title": "Galaxy Racers",
            "description": "Kids from different planets compete in the ultimate space race.",
            "genre": "Science Fiction",
            "cover_image": "https://images.unsplash.com/photo-1454789548928-9efd52dc4031?w=400",
            "back_cover_text": "In the year 3000, the biggest race in the galaxy is about to begin. Who will win?",
            "age_rating": "10-12 years"
        }
    ]
    
    created_books = []
    for book_data in test_books:
        # Check if book already exists
        existing = await db.books.find_one({"title": book_data["title"]}, {"_id": 0})
        if existing:
            continue
            
        book_id = str(uuid.uuid4())
        book = {
            "id": book_id,
            "title": book_data["title"],
            "description": book_data["description"],
            "genre": book_data["genre"],
            "cover_image": book_data["cover_image"],
            "back_cover_image": "",
            "cover_title": book_data["title"],
            "cover_subtitle": "",
            "back_cover_text": book_data["back_cover_text"],
            "author_id": author_id,
            "author_name": author_name,
            "is_published": True,
            "is_featured": book_data["genre"] in ["Fantasy", "Science Fiction"],
            "is_best_of_week": book_data["genre"] == "Adventure",
            "layout_mode": "standard",
            "narrator_voice_id": "21m00Tcm4TlvDq8ikWAM",
            "age_rating": book_data["age_rating"],
            "view_count": 0,
            "read_count": 0,
            "created_at": now,
            "updated_at": now
        }
        await db.books.insert_one(book)
        
        # Create a chapter with sample pages
        chapter_id = str(uuid.uuid4())
        chapter = {
            "id": chapter_id,
            "book_id": book_id,
            "title": "Chapter 1: The Beginning",
            "order": 1,
            "created_at": now
        }
        await db.chapters.insert_one(chapter)
        
        # Create sample pages
        sample_texts = [
            "Once upon a time, in a world not so different from ours, an adventure was about to begin...",
            "Our hero looked around nervously. Something amazing was about to happen.",
            "And that's when everything changed forever. The End."
        ]
        
        for i, text in enumerate(sample_texts):
            page = {
                "id": str(uuid.uuid4()),
                "chapter_id": chapter_id,
                "text_content": text,
                "image_url": book_data["cover_image"] if i == 0 else "",
                "image_url_2": "",
                "image_url_3": "",
                "image_url_4": "",
                "video_url": "",
                "audio_url": "",
                "order": i + 1,
                "layout_type": "single",
                "created_at": now
            }
            await db.pages.insert_one(page)
        
        created_books.append({"id": book_id, "title": book_data["title"]})
    
    return {
        "message": f"Created {len(created_books)} test books",
        "books": created_books
    }



# ============ PROXY FOR 3D MODELS (CORS BYPASS) ============

@api_router.get("/proxy/glb")
async def proxy_glb_model(url: str):
    """Proxy GLB model files to bypass CORS issues"""
    try:
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout for large files
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch model")
                
                content = await response.read()
                content_length = len(content)
                
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type="model/gltf-binary",
                    headers={
                        "Content-Length": str(content_length),
                        "Content-Disposition": "inline",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "public, max-age=86400"
                    }
                )
    except aiohttp.ClientError as e:
        logger.error(f"Client error proxying GLB: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch model: {str(e)}")
    except Exception as e:
        logger.error(f"Error proxying GLB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Audio proxy endpoint for ambient sounds
@api_router.get("/proxy/audio")
async def proxy_audio(url: str):
    """Proxy audio files to bypass CORS issues"""
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch audio")
                
                content = await response.read()
                content_length = len(content)
                content_type = response.headers.get('Content-Type', 'audio/mpeg')
                
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type=content_type,
                    headers={
                        "Content-Length": str(content_length),
                        "Content-Disposition": "inline",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "public, max-age=86400"
                    }
                )
    except aiohttp.ClientError as e:
        logger.error(f"Client error proxying audio: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch audio: {str(e)}")
    except Exception as e:
        logger.error(f"Error proxying audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Predefined ambient sounds - using working URLs from Soundbible and other free sources
AMBIENT_SOUND_URLS = {
    "rain": "https://soundbible.com/grab.php?id=2065&type=mp3",  # Rain Inside House
    "fireplace": "https://soundbible.com/grab.php?id=2178&type=mp3",  # Fireplace
    "forest": "https://soundbible.com/grab.php?id=1818&type=mp3",  # Rainforest Ambience with birds
    "ocean": "https://soundbible.com/grab.php?id=1935&type=mp3",  # Ocean Waves
    "cafe": "https://soundbible.com/grab.php?id=1664&type=mp3",  # Restaurant Ambience
    "night": "https://soundbible.com/grab.php?id=2083&type=mp3",  # Night Crickets
    "wind": "https://soundbible.com/grab.php?id=2033&type=mp3",  # Wind Sound
    "library": "https://soundbible.com/grab.php?id=1996&type=mp3"  # Soft Background
}

@api_router.get("/ambient-sounds/{sound_name}")
async def get_ambient_sound(sound_name: str):
    """Get ambient sound - proxied through backend to avoid CORS"""
    if sound_name not in AMBIENT_SOUND_URLS:
        raise HTTPException(status_code=404, detail="Sound not found")
    
    url = AMBIENT_SOUND_URLS[sound_name]
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch audio")
                
                content = await response.read()
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type="audio/mpeg",
                    headers={
                        "Content-Length": str(len(content)),
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "public, max-age=86400"
                    }
                )
    except Exception as e:
        logger.error(f"Error fetching ambient sound {sound_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ USER PROFILE & SOCIAL ROUTES ============

class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    avatar: Optional[str] = None

@api_router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str, current_user: dict = Depends(get_optional_user)):
    """Get a user's public profile"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get profile data
    profile = await db.profiles.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get follower/following counts
    followers_count = await db.follows.count_documents({"following_id": user_id})
    following_count = await db.follows.count_documents({"follower_id": user_id})
    
    # Get published books count and total reads
    books = await db.books.find({"author_id": user_id, "is_published": True}, {"_id": 0}).to_list(100)
    books_count = len(books)
    total_reads = sum(b.get("read_count", 0) for b in books)
    
    # Check if current user is following this user
    is_following = False
    if current_user and current_user["id"] != user_id:
        follow = await db.follows.find_one({"follower_id": current_user["id"], "following_id": user_id})
        is_following = follow is not None
    
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"] if current_user and current_user["id"] == user_id else None,
        "display_name": profile.get("display_name", user["name"]) if profile else user["name"],
        "bio": profile.get("bio", "") if profile else "",
        "location": profile.get("location", "") if profile else "",
        "website": profile.get("website", "") if profile else "",
        "twitter": profile.get("twitter", "") if profile else "",
        "avatar": profile.get("avatar") if profile else None,
        "subscription": user.get("subscription", "free"),
        "created_at": user.get("created_at"),
        "followers_count": followers_count,
        "following_count": following_count,
        "books_count": books_count,
        "total_reads": total_reads,
        "is_following": is_following
    }

@api_router.put("/users/profile")
async def update_user_profile(profile_data: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update current user's profile"""
    update_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}
    update_data["user_id"] = current_user["id"]
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.profiles.update_one(
        {"user_id": current_user["id"]},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Profile updated"}

@api_router.get("/users/{user_id}/books")
async def get_user_books(user_id: str):
    """Get a user's published books"""
    books = await db.books.find(
        {"author_id": user_id, "is_published": True}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for book in books:
        book = set_book_defaults(book)
    
    return books

@api_router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Follow a user"""
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing = await db.follows.find_one({
        "follower_id": current_user["id"],
        "following_id": user_id
    })
    
    if existing:
        return {"message": "Already following"}
    
    # Create follow relationship
    follow = {
        "id": str(uuid.uuid4()),
        "follower_id": current_user["id"],
        "following_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.follows.insert_one(follow)
    
    return {"message": "Now following user"}

@api_router.delete("/users/{user_id}/follow")
async def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Unfollow a user"""
    result = await db.follows.delete_one({
        "follower_id": current_user["id"],
        "following_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not following this user")
    
    return {"message": "Unfollowed user"}

@api_router.get("/users/{user_id}/followers")
async def get_user_followers(user_id: str, current_user: dict = Depends(get_optional_user)):
    """Get a user's followers"""
    follows = await db.follows.find({"following_id": user_id}, {"_id": 0}).to_list(100)
    
    followers = []
    for follow in follows:
        user = await db.users.find_one({"id": follow["follower_id"]}, {"_id": 0, "password": 0})
        if user:
            profile = await db.profiles.find_one({"user_id": user["id"]}, {"_id": 0})
            followers.append({
                "id": user["id"],
                "name": user["name"],
                "display_name": profile.get("display_name", user["name"]) if profile else user["name"],
                "avatar": profile.get("avatar") if profile else None
            })
    
    return followers

@api_router.get("/users/{user_id}/following")
async def get_user_following(user_id: str, current_user: dict = Depends(get_optional_user)):
    """Get users that a user is following"""
    follows = await db.follows.find({"follower_id": user_id}, {"_id": 0}).to_list(100)
    
    following = []
    for follow in follows:
        user = await db.users.find_one({"id": follow["following_id"]}, {"_id": 0, "password": 0})
        if user:
            profile = await db.profiles.find_one({"user_id": user["id"]}, {"_id": 0})
            following.append({
                "id": user["id"],
                "name": user["name"],
                "display_name": profile.get("display_name", user["name"]) if profile else user["name"],
                "avatar": profile.get("avatar") if profile else None
            })
    
    return following

# ============ BOOK REVIEWS & RATINGS ============

class ReviewCreate(BaseModel):
    book_id: str
    rating: int = Field(ge=1, le=5)
    content: str = ""

@api_router.post("/reviews")
async def create_review(review_data: ReviewCreate, current_user: dict = Depends(get_current_user)):
    """Create or update a book review"""
    book = await db.books.find_one({"id": review_data.book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if user has already reviewed this book
    existing = await db.reviews.find_one({
        "book_id": review_data.book_id,
        "user_id": current_user["id"]
    })
    
    now = datetime.now(timezone.utc).isoformat()
    
    if existing:
        # Update existing review
        await db.reviews.update_one(
            {"id": existing["id"]},
            {"$set": {
                "rating": review_data.rating,
                "content": review_data.content,
                "updated_at": now
            }}
        )
        return {"message": "Review updated", "id": existing["id"]}
    
    # Create new review
    review_id = str(uuid.uuid4())
    review = {
        "id": review_id,
        "book_id": review_data.book_id,
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "rating": review_data.rating,
        "content": review_data.content,
        "created_at": now,
        "updated_at": now
    }
    await db.reviews.insert_one(review)
    
    return {"message": "Review created", "id": review_id}

@api_router.get("/books/{book_id}/reviews")
async def get_book_reviews(book_id: str):
    """Get all reviews for a book"""
    reviews = await db.reviews.find({"book_id": book_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Calculate average rating
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    else:
        avg_rating = 0
    
    # Get user profiles for reviews
    for review in reviews:
        profile = await db.profiles.find_one({"user_id": review["user_id"]}, {"_id": 0})
        review["user_display_name"] = profile.get("display_name", review["user_name"]) if profile else review["user_name"]
        review["user_avatar"] = profile.get("avatar") if profile else None
    
    return {
        "reviews": reviews,
        "average_rating": round(avg_rating, 1),
        "total_reviews": len(reviews)
    }

@api_router.delete("/reviews/{review_id}")
async def delete_review(review_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a review (owner only)"""
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.reviews.delete_one({"id": review_id})
    return {"message": "Review deleted"}


# ============ READING STREAKS & BADGES ============

BADGE_REQUIREMENTS = {
    'first_book': {'type': 'books_completed', 'count': 1},
    'bookworm': {'type': 'books_completed', 'count': 5},
    'streak_3': {'type': 'streak', 'count': 3},
    'streak_7': {'type': 'streak', 'count': 7},
    'streak_30': {'type': 'streak', 'count': 30},
    'night_owl': {'type': 'reading_time', 'hour_start': 0, 'hour_end': 4},
    'early_bird': {'type': 'reading_time', 'hour_start': 5, 'hour_end': 7},
    'genre_explorer': {'type': 'genres_read', 'count': 5},
    'supporter': {'type': 'following', 'count': 5},
    'creator': {'type': 'books_published', 'count': 1}
}

@api_router.get("/user/reading-stats")
async def get_reading_stats(current_user: dict = Depends(get_current_user)):
    """Get user's reading statistics including streak and badges"""
    user_id = current_user["id"]
    
    # Get or create reading stats
    stats = await db.reading_stats.find_one({"user_id": user_id})
    if not stats:
        stats = {
            "user_id": user_id,
            "streak": 0,
            "last_read_date": None,
            "total_books_read": 0,
            "total_time_read": 0,
            "genres_read": [],
            "badges": [],
            "reading_history": []
        }
        await db.reading_stats.insert_one(stats)
    
    return {
        "streak": stats.get("streak", 0),
        "badges": stats.get("badges", []),
        "total_books_read": stats.get("total_books_read", 0),
        "total_time_read": stats.get("total_time_read", 0),
        "genres_read": stats.get("genres_read", [])
    }

class RecordReadingRequest(BaseModel):
    book_id: str
    time_spent: int = 0  # in seconds
    completed: bool = False

@api_router.post("/user/record-reading")
async def record_reading(request: RecordReadingRequest, current_user: dict = Depends(get_current_user)):
    """Record reading activity and update streaks/badges"""
    user_id = current_user["id"]
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    current_hour = now.hour
    
    # Get book info for genre tracking
    book = await db.books.find_one({"id": request.book_id})
    book_genre = book.get("genre", "General") if book else "General"
    
    # Get or create stats
    stats = await db.reading_stats.find_one({"user_id": user_id})
    if not stats:
        stats = {
            "user_id": user_id,
            "streak": 0,
            "last_read_date": None,
            "total_books_read": 0,
            "total_time_read": 0,
            "genres_read": [],
            "badges": [],
            "reading_history": []
        }
    
    new_badges = []
    
    # Update streak
    last_read = stats.get("last_read_date")
    if last_read:
        last_date = datetime.fromisoformat(last_read).date() if isinstance(last_read, str) else last_read.date()
        today_date = now.date()
        days_diff = (today_date - last_date).days
        
        if days_diff == 0:
            # Same day, streak continues
            pass
        elif days_diff == 1:
            # Next day, increment streak
            stats["streak"] = stats.get("streak", 0) + 1
        else:
            # Streak broken, reset to 1
            stats["streak"] = 1
    else:
        # First time reading
        stats["streak"] = 1
    
    stats["last_read_date"] = today
    stats["total_time_read"] = stats.get("total_time_read", 0) + request.time_spent
    
    # Update genres read
    if book_genre and book_genre not in stats.get("genres_read", []):
        stats.setdefault("genres_read", []).append(book_genre)
    
    # If book completed
    if request.completed:
        stats["total_books_read"] = stats.get("total_books_read", 0) + 1
    
    # Check for new badges
    current_badges = set(stats.get("badges", []))
    
    # Streak badges
    streak = stats["streak"]
    if streak >= 3 and 'streak_3' not in current_badges:
        new_badges.append('streak_3')
    if streak >= 7 and 'streak_7' not in current_badges:
        new_badges.append('streak_7')
    if streak >= 30 and 'streak_30' not in current_badges:
        new_badges.append('streak_30')
    
    # Books completed badges
    books_read = stats["total_books_read"]
    if books_read >= 1 and 'first_book' not in current_badges:
        new_badges.append('first_book')
    if books_read >= 5 and 'bookworm' not in current_badges:
        new_badges.append('bookworm')
    
    # Time-based badges
    if 0 <= current_hour < 5 and 'night_owl' not in current_badges:
        new_badges.append('night_owl')
    if 5 <= current_hour < 8 and 'early_bird' not in current_badges:
        new_badges.append('early_bird')
    
    # Genre explorer
    if len(stats.get("genres_read", [])) >= 5 and 'genre_explorer' not in current_badges:
        new_badges.append('genre_explorer')
    
    # Check creator badge
    user_books = await db.books.count_documents({"author_id": user_id, "status": "published"})
    if user_books >= 1 and 'creator' not in current_badges:
        new_badges.append('creator')
    
    # Check supporter badge
    user = await db.users.find_one({"id": user_id})
    if len(user.get("following", [])) >= 5 and 'supporter' not in current_badges:
        new_badges.append('supporter')
    
    # Add new badges
    if new_badges:
        stats["badges"] = list(current_badges | set(new_badges))
    
    # Save stats
    await db.reading_stats.update_one(
        {"user_id": user_id},
        {"$set": stats},
        upsert=True
    )
    
    return {
        "streak": stats["streak"],
        "new_badge": new_badges[0] if new_badges else None,
        "all_badges": stats["badges"]
    }

@api_router.get("/user/recommendations")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    """Get personalized book recommendations"""
    user_id = current_user["id"]
    
    # Get user's reading stats
    stats = await db.reading_stats.find_one({"user_id": user_id})
    genres_read = stats.get("genres_read", []) if stats else []
    
    # Get user's read books
    read_books = await db.reading_history.find({"user_id": user_id}).to_list(100)
    read_book_ids = [r["book_id"] for r in read_books]
    
    recommendations = []
    
    # Get books from genres user has read (excluding already read)
    if genres_read:
        genre_books = await db.books.find({
            "id": {"$nin": read_book_ids},
            "genre": {"$in": genres_read},
            "status": "published"
        }, {"_id": 0}).sort("views", -1).limit(6).to_list(6)
        recommendations.extend(genre_books)
    
    # Get featured/popular books if not enough recommendations
    if len(recommendations) < 10:
        popular_books = await db.books.find({
            "id": {"$nin": read_book_ids + [b["id"] for b in recommendations]},
            "status": "published"
        }, {"_id": 0}).sort("views", -1).limit(10 - len(recommendations)).to_list(10)
        recommendations.extend(popular_books)
    
    return {
        "recommendations": recommendations,
        "based_on": genres_read if genres_read else ["Popular books"]
    }



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
