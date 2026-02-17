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
import aiofiles

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ElevenLabs client
eleven_client = ElevenLabs(api_key=os.environ.get('ELEVENLABS_API_KEY'))

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Azories API", description="Digital Book Creation Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    cover_image: Optional[str] = None
    is_published: Optional[bool] = None

class BookResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    description: str
    genre: str
    cover_image: str
    author_id: str
    author_name: str
    is_published: bool
    created_at: str
    updated_at: str
    chapter_count: int = 0
    total_pages: int = 0

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
    video_url: Optional[str] = ""
    audio_url: Optional[str] = ""
    order: int = 0

class PageUpdate(BaseModel):
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    order: Optional[int] = None

class PageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    chapter_id: str
    text_content: str
    image_url: str
    video_url: str
    audio_url: str
    order: int
    created_at: str

class ImageGenerateRequest(BaseModel):
    prompt: str
    book_id: Optional[str] = None

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
    labels: Optional[dict] = None

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
        "role": "creator",  # Default role
        "created_at": now
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id, user_data.email, "creator")
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=user_data.email, name=user_data.name, role="creator", created_at=now)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"], role=user["role"], created_at=user["created_at"])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        created_at=current_user["created_at"]
    )

# ============ BOOK ROUTES ============

@api_router.post("/books", response_model=BookResponse)
async def create_book(book_data: BookCreate, current_user: dict = Depends(get_current_user)):
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    book = {
        "id": book_id,
        "title": book_data.title,
        "description": book_data.description or "",
        "genre": book_data.genre or "General",
        "cover_image": book_data.cover_image or "",
        "author_id": current_user["id"],
        "author_name": current_user["name"],
        "is_published": False,
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
    published_only: bool = True
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
    
    books = await db.books.find(query, {"_id": 0}).to_list(100)
    
    # Get chapter and page counts
    for book in books:
        chapters = await db.chapters.find({"book_id": book["id"]}, {"_id": 0}).to_list(100)
        book["chapter_count"] = len(chapters)
        total_pages = 0
        for chapter in chapters:
            pages = await db.pages.count_documents({"chapter_id": chapter["id"]})
            total_pages += pages
        book["total_pages"] = total_pages
    
    return [BookResponse(**book) for book in books]

@api_router.get("/books/my", response_model=List[BookResponse])
async def get_my_books(current_user: dict = Depends(get_current_user)):
    books = await db.books.find({"author_id": current_user["id"]}, {"_id": 0}).to_list(100)
    
    for book in books:
        chapters = await db.chapters.find({"book_id": book["id"]}, {"_id": 0}).to_list(100)
        book["chapter_count"] = len(chapters)
        total_pages = 0
        for chapter in chapters:
            pages = await db.pages.count_documents({"chapter_id": chapter["id"]})
            total_pages += pages
        book["total_pages"] = total_pages
    
    return [BookResponse(**book) for book in books]

@api_router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    book["chapter_count"] = len(chapters)
    total_pages = 0
    for chapter in chapters:
        pages = await db.pages.count_documents({"chapter_id": chapter["id"]})
        total_pages += pages
    book["total_pages"] = total_pages
    
    return BookResponse(**book)

@api_router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: str, book_data: BookUpdate, current_user: dict = Depends(get_current_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in book_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.books.update_one({"id": book_id}, {"$set": update_data})
    updated = await db.books.find_one({"id": book_id}, {"_id": 0})
    
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    updated["chapter_count"] = len(chapters)
    total_pages = 0
    for chapter in chapters:
        pages = await db.pages.count_documents({"chapter_id": chapter["id"]})
        total_pages += pages
    updated["total_pages"] = total_pages
    
    return BookResponse(**updated)

@api_router.delete("/books/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Delete all related data
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    for chapter in chapters:
        await db.pages.delete_many({"chapter_id": chapter["id"]})
    await db.chapters.delete_many({"book_id": book_id})
    await db.books.delete_one({"id": book_id})
    
    return {"message": "Book deleted"}

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
    
    # Get max order if not provided
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
    
    # Get max order if not provided
    if page_data.order == 0:
        max_order = await db.pages.find_one({"chapter_id": chapter_id}, sort=[("order", -1)])
        page_data.order = (max_order["order"] + 1) if max_order else 1
    
    page = {
        "id": page_id,
        "chapter_id": chapter_id,
        "text_content": page_data.text_content,
        "image_url": page_data.image_url or "",
        "video_url": page_data.video_url or "",
        "audio_url": page_data.audio_url or "",
        "order": page_data.order,
        "created_at": now
    }
    await db.pages.insert_one(page)
    return PageResponse(**page)

@api_router.get("/chapters/{chapter_id}/pages", response_model=List[PageResponse])
async def get_pages(chapter_id: str):
    pages = await db.pages.find({"chapter_id": chapter_id}, {"_id": 0}).sort("order", 1).to_list(100)
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
        image_gen = OpenAIImageGeneration(api_key=os.environ.get('OPENAI_API_KEY'))
        images = await image_gen.generate_images(
            prompt=f"Children's book illustration: {request.prompt}. Style: colorful, friendly, magical, suitable for children.",
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
        video_gen = OpenAIVideoGeneration(api_key=os.environ.get('OPENAI_API_KEY'))
        video_bytes = video_gen.text_to_video(
            prompt=f"Children's animated scene: {request.prompt}. Style: colorful, friendly, magical animation suitable for children.",
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

# ============ TTS ROUTES ============

@api_router.get("/voices", response_model=List[VoiceResponse])
async def get_voices():
    try:
        voices_response = eleven_client.voices.get_all()
        voices = []
        for voice in voices_response.voices:
            voices.append(VoiceResponse(
                voice_id=voice.voice_id,
                name=voice.name,
                category=voice.category if hasattr(voice, 'category') else None,
                labels=voice.labels if hasattr(voice, 'labels') else None
            ))
        return voices
    except Exception as e:
        logger.error(f"Error fetching voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching voices: {str(e)}")

@api_router.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    try:
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
        
        # Determine content type
        content_type = file.content_type or "image/png"
        
        return {
            "image_url": f"data:{content_type};base64,{image_base64}",
            "success": True
        }
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

# ============ BOOK READING ============

@api_router.get("/books/{book_id}/full")
async def get_full_book(book_id: str):
    """Get complete book with all chapters and pages for reading"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
    
    full_chapters = []
    for chapter in chapters:
        pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).sort("order", 1).to_list(100)
        full_chapters.append({
            **chapter,
            "pages": pages
        })
    
    return {
        **book,
        "chapters": full_chapters
    }

# ============ GENRES ============

@api_router.get("/genres")
async def get_genres():
    return {
        "genres": [
            "Adventure", "Fantasy", "Science Fiction", "Mystery", 
            "Fairy Tales", "Animals", "Friendship", "Family",
            "Educational", "Humor", "Nature", "Sports", "General"
        ]
    }

# ============ ROOT ============

@api_router.get("/")
async def root():
    return {"message": "Welcome to Azories API", "version": "1.0.0"}

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
