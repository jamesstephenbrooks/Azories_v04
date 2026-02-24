from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import secrets
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict
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
from emergentintegrations.llm.openai import OpenAITextToSpeech
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import aiofiles
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import email service
from services.email_service import (
    send_email, is_configured as email_configured,
    get_welcome_email_html, get_password_reset_email_html, 
    get_password_changed_email_html, generate_reset_token, get_token_expiry
)

# Import fal.ai service AFTER dotenv loads
try:
    from fal_service import (
        generate_image_flux,
        generate_with_face_id,
        train_character_lora,
        check_training_status,
        generate_with_lora,
        upload_image_to_fal,
        generate_video_from_image,
        get_available_models as get_fal_models
    )
    FAL_KEY = os.environ.get('FAL_KEY')
    FAL_AVAILABLE = bool(FAL_KEY)
    if FAL_AVAILABLE:
        os.environ["FAL_KEY"] = FAL_KEY  # Ensure fal_client can see it
except ImportError as e:
    logging.warning(f"fal.ai service not available: {e}")
    FAL_AVAILABLE = False

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

# In-memory task store for long-running operations
# Maps task_id -> {"status": "pending"|"completed"|"failed", "result": any, "error": str, "created_at": datetime}
import asyncio
TASK_STORE: Dict[str, dict] = {}

async def cleanup_old_tasks():
    """Remove tasks older than 1 hour"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    expired = [tid for tid, task in TASK_STORE.items() if task.get("created_at", datetime.now(timezone.utc)) < cutoff]
    for tid in expired:
        del TASK_STORE[tid]

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
    credits: Optional[int] = 0
    created_at: str
    pro_trial: Optional[bool] = False
    pro_trial_expires_at: Optional[str] = None
    trial_days_remaining: Optional[int] = None
    
# Credit costs for Pro Studio features
CREDIT_COSTS = {
    "flux_generate": 1,        # Basic FLUX generation
    "flux_pro_generate": 2,    # FLUX Pro generation
    "pulid_generate": 3,       # Face ID preservation
    "lora_training": 50,       # Train LoRA model
    "lora_generate": 2,        # Generate with trained LoRA
    "video_generate": 10,      # Video generation
    "shots_generate": 5,       # 9 angle shots generation
    "expression_generate": 2,  # Expression generation
}

# Actual costs to us (for tracking VIP usage)
ACTUAL_COSTS = {
    "flux_generate": 0.025,    # $0.025 per image
    "flux_pro_generate": 0.05, # $0.05 per image
    "pulid_generate": 0.08,    # $0.08 per image
    "lora_training": 2.00,     # $2.00 per training
    "lora_generate": 0.05,     # $0.05 per image
    "video_generate": 0.50,    # $0.50 per video (5 second)
    "shots_generate": 0.25,    # $0.25 for 9 shots
    "expression_generate": 0.05, # $0.05 per expression
}

# VIP users who get unlimited free credits (but we track usage)
VIP_USERS = [
    "arianamillb@icloud.com",
    "jamesstephenbrooks@outlook.com"
]

def check_budget_error(error_msg: str) -> bool:
    """Check if an error is related to Emergent LLM Key budget"""
    budget_keywords = ["budget has been exceeded", "budget exceeded", "max budget", "current cost"]
    return any(keyword in error_msg.lower() for keyword in budget_keywords)

def get_budget_error_response():
    """Return a helpful error message for budget exceeded"""
    return HTTPException(
        status_code=503,
        detail="AI service budget limit reached. To continue using AI features, please add balance to your Universal Key: Go to Profile > Universal Key > Add Balance. You can also enable auto-top-up to avoid interruptions."
    )

# Credit packages for purchase (with 50% profit margin)
CREDIT_PACKAGES = {
    "starter": {
        "credits": 100,
        "price": 5.00,
        "currency": "gbp",
        "description": "~10 AI images or 1 video",
        "popular": False
    },
    "creator": {
        "credits": 500,
        "price": 18.00,
        "currency": "gbp",
        "description": "~50 AI images or 5 videos",
        "popular": True
    },
    "pro": {
        "credits": 1000,
        "price": 30.00,
        "currency": "gbp",
        "description": "~100 AI images or 1 LoRA training",
        "popular": False
    },
    "studio": {
        "credits": 5000,
        "price": 120.00,
        "currency": "gbp",
        "description": "~500 AI images or 50 videos",
        "popular": False
    }
}

# Stripe configuration
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

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
    narrator_voice_locked: Optional[bool] = False
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
    # is_published removed - users must go through review process
    is_featured: Optional[bool] = None
    is_best_of_week: Optional[bool] = None
    layout_mode: Optional[str] = None
    narrator_voice_id: Optional[str] = None
    narrator_voice_locked: Optional[bool] = None
    age_rating: Optional[str] = None
    series_id: Optional[str] = None
    series_order: Optional[int] = None
    # publish_status cannot be set directly by users

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
    publish_status: str = "draft"  # draft, pending_review, published, rejected
    moderation_flags: Optional[List[str]] = []
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
    # Image position controls (0-100, where 50 is center)
    image_position_x: Optional[int] = 50
    image_position_y: Optional[int] = 50
    image_fit: Optional[str] = "cover"  # cover, contain, fill
    # Text formatting
    font_family: Optional[str] = "default"
    font_size: Optional[str] = "medium"
    text_align: Optional[str] = "left"

class PageUpdate(BaseModel):
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    image_url_2: Optional[str] = None
    image_url_3: Optional[str] = None
    image_url_4: Optional[str] = None
    video_url: Optional[str] = None
    use_video: Optional[bool] = None
    audio_url: Optional[str] = None
    order: Optional[int] = None
    layout_type: Optional[str] = None
    image_position_x: Optional[int] = None
    image_position_y: Optional[int] = None
    image_fit: Optional[str] = None
    # Text formatting
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    text_align: Optional[str] = None

class PageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    chapter_id: str
    text_content: str
    image_url: str
    image_url_2: str = ""
    image_url_3: str = ""
    image_url_4: str = ""
    video_url: str = ""
    use_video: bool = False
    audio_url: str = ""
    order: int
    layout_type: str = "standard"
    image_position_x: int = 50
    image_position_y: int = 50
    image_fit: str = "cover"
    font_family: str = "default"
    font_size: str = "medium"
    text_align: str = "left"
    created_at: str

class ImageGenerateRequest(BaseModel):
    prompt: str
    book_id: Optional[str] = None
    style: Optional[str] = "illustration"

class VideoGenerateRequest(BaseModel):
    prompt: str
    duration: int = 4  # Valid durations: 4, 8, 12 seconds
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

# Pro Studio Models - Character Styles and Genres
CHARACTER_STYLES = [
    {"id": "photorealistic", "name": "Photorealistic", "description": "Lifelike, realistic human appearance"},
    {"id": "illustration", "name": "Illustration", "description": "Hand-drawn, artistic book illustration style"},
    {"id": "anime", "name": "Anime/Manga", "description": "Japanese animation style"},
    {"id": "cartoon", "name": "Cartoon", "description": "Stylized, exaggerated cartoon style"},
    {"id": "3d-render", "name": "3D Render", "description": "Modern 3D animated movie style (Pixar/Disney)"},
    {"id": "watercolor", "name": "Watercolor", "description": "Soft, painterly watercolor style"},
    {"id": "comic", "name": "Comic Book", "description": "Bold lines, superhero comic style"},
    {"id": "fantasy", "name": "Fantasy Art", "description": "Epic fantasy painting style"},
    {"id": "scifi", "name": "Sci-Fi/Futuristic", "description": "Sleek, technological, futuristic aesthetic"},
    {"id": "cyberpunk", "name": "Cyberpunk", "description": "Neon-lit, dystopian future style"},
    {"id": "chibi", "name": "Chibi/Cute", "description": "Super-deformed cute style"},
    {"id": "noir", "name": "Noir/Dramatic", "description": "High contrast, dramatic lighting"},
    {"id": "storybook", "name": "Children's Storybook", "description": "Warm, friendly children's book style"},
    {"id": "vintage", "name": "Vintage/Retro", "description": "Classic, nostalgic illustration style"},
    {"id": "concept-art", "name": "Concept Art", "description": "Professional game/film concept art style"},
    {"id": "steampunk", "name": "Steampunk", "description": "Victorian-era with steam-powered technology"},
]

CHARACTER_GENRES = [
    {"id": "fantasy", "name": "Fantasy", "examples": "elves, wizards, dragons, magical creatures"},
    {"id": "scifi", "name": "Sci-Fi", "examples": "aliens, cyborgs, space explorers, futuristic"},
    {"id": "futuristic", "name": "Futuristic", "examples": "advanced technology, AI beings, space age"},
    {"id": "cyberpunk", "name": "Cyberpunk", "examples": "hackers, augmented humans, neon cities"},
    {"id": "space-opera", "name": "Space Opera", "examples": "galactic heroes, starship crews, alien races"},
    {"id": "contemporary", "name": "Contemporary", "examples": "modern day people, everyday settings"},
    {"id": "historical", "name": "Historical", "examples": "period characters, historical figures"},
    {"id": "horror", "name": "Horror/Dark", "examples": "monsters, vampires, gothic characters"},
    {"id": "adventure", "name": "Adventure", "examples": "explorers, pirates, treasure hunters"},
    {"id": "romance", "name": "Romance", "examples": "romantic leads, emotional characters"},
    {"id": "mystery", "name": "Mystery/Thriller", "examples": "detectives, spies, mysterious figures"},
    {"id": "superhero", "name": "Superhero", "examples": "heroes, villains, powered beings"},
    {"id": "post-apocalyptic", "name": "Post-Apocalyptic", "examples": "survivors, mutants, wasteland warriors"},
    {"id": "steampunk", "name": "Steampunk", "examples": "inventors, airship pilots, clockwork beings"},
    {"id": "animal", "name": "Animals/Creatures", "examples": "anthropomorphic, talking animals, mythical beasts"},
    {"id": "childrens", "name": "Children's", "examples": "friendly characters, educational, whimsical"},
    {"id": "mecha", "name": "Mecha/Robots", "examples": "giant robots, pilots, mechanical beings"},
]

class CharacterCreate(BaseModel):
    name: str
    reference_images: List[str] = []  # Base64 or URL images (optional now)
    description_prompt: Optional[str] = None  # User's description of the character
    style: Optional[str] = "illustration"  # Character visual style
    genre: Optional[str] = "fantasy"  # Story genre
    physical_traits: Optional[dict] = None  # Age, gender, hair, eyes, etc.
    personality: Optional[str] = None  # Character personality for consistency
    backstory: Optional[str] = None  # Character background
    special_features: Optional[str] = None  # Unique features (scars, tattoos, wings, etc.)

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    description_prompt: Optional[str] = None
    style: Optional[str] = None
    genre: Optional[str] = None
    physical_traits: Optional[dict] = None
    personality: Optional[str] = None
    backstory: Optional[str] = None
    special_features: Optional[str] = None
    add_reference_images: Optional[List[str]] = None  # Add more reference images

# Scene Consistency Models
class SceneCreate(BaseModel):
    name: str
    description: str  # Scene description (location, time of day, atmosphere)
    style: Optional[str] = "illustration"
    genre: Optional[str] = "fantasy"
    reference_images: Optional[List[str]] = []  # Reference images for the scene
    lighting: Optional[str] = None  # Lighting conditions
    mood: Optional[str] = None  # Emotional mood
    time_of_day: Optional[str] = None  # Morning, afternoon, night, etc.
    weather: Optional[str] = None  # Weather conditions
    location_type: Optional[str] = None  # Indoor, outdoor, urban, nature, etc.

class SceneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    style: Optional[str] = None
    genre: Optional[str] = None
    lighting: Optional[str] = None
    mood: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    location_type: Optional[str] = None
    add_reference_images: Optional[List[str]] = None

# fal.ai Character Consistency Models
class FalTrainLoraRequest(BaseModel):
    character_name: str
    reference_images: List[str]  # Base64 or URL images (3-20 images)
    trigger_word: Optional[str] = None
    steps: Optional[int] = 1000

class FalGenerateWithFaceRequest(BaseModel):
    prompt: str
    reference_image: str  # Face reference image (base64 or URL)
    id_weight: Optional[float] = 1.0
    image_size: Optional[str] = "landscape_16_9"
    seed: Optional[int] = None

class FalGenerateWithLoraRequest(BaseModel):
    prompt: str
    lora_url: str
    trigger_word: str
    lora_scale: Optional[float] = 1.0
    image_size: Optional[str] = "landscape_16_9"
    seed: Optional[int] = None

class FalGenerateImageRequest(BaseModel):
    prompt: str
    model: Optional[str] = "flux-dev"  # flux-dev, flux-pro
    image_size: Optional[str] = "landscape_16_9"
    num_images: Optional[int] = 1
    seed: Optional[int] = None

class ProStudioImageRequest(BaseModel):
    prompt: str
    character_id: Optional[str] = None
    camera: Optional[str] = "arri-alexa-35"
    lens: Optional[str] = "panavision-series"
    focal_length: Optional[str] = "35mm"
    lighting: Optional[str] = "natural"
    aspect_ratio: Optional[str] = "16:9"

class GenerateShotsRequest(BaseModel):
    source_image: str  # Base64 encoded image
    character_id: Optional[str] = None

class GenerateExpressionRequest(BaseModel):
    character_id: str
    expression: str
    base_prompt: Optional[str] = ""

class AnimateHeroRequest(BaseModel):
    image_url: str
    motion_prompt: str = "subtle cinematic movement"
    model: str = "sora-2"
    duration: int = 5

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

# Admin credentials - dedicated admin login
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Routetofreedom')

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
async def register(user_data: UserCreate, background_tasks: BackgroundTasks):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    # 30-day free Pro trial for all new users
    trial_expires = (now + timedelta(days=30)).isoformat()
    
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": "user",
        "subscription": "pro",  # Start with Pro
        "pro_trial": True,  # Mark as trial user
        "pro_trial_expires_at": trial_expires,  # Trial expiration
        "created_at": now_iso
    }
    await db.users.insert_one(user)
    
    # Send welcome email in background
    if email_configured():
        welcome_html = get_welcome_email_html(user_data.name)
        background_tasks.add_task(send_email, user_data.email, "Welcome to Azories! 🎉", welcome_html)
    
    token = create_token(user_id, user_data.email, "user")
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id, 
            email=user_data.email, 
            name=user_data.name, 
            role="user", 
            subscription="pro", 
            created_at=now_iso,
            pro_trial=True,
            pro_trial_expires_at=trial_expires,
            trial_days_remaining=30
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if trial has expired
    subscription = user.get("subscription", "free")
    pro_trial = user.get("pro_trial", False)
    trial_expires = user.get("pro_trial_expires_at")
    trial_days_remaining = None
    
    if pro_trial and trial_expires:
        expiry_date = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        if now > expiry_date:
            # Trial expired - downgrade to free
            subscription = "free"
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"subscription": "free", "pro_trial": False}}
            )
            pro_trial = False
        else:
            trial_days_remaining = (expiry_date - now).days
    
    token = create_token(user["id"], user["email"], user["role"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"], 
            email=user["email"], 
            name=user["name"], 
            role=user["role"], 
            subscription=subscription,
            created_at=user["created_at"],
            pro_trial=pro_trial,
            pro_trial_expires_at=trial_expires,
            trial_days_remaining=trial_days_remaining
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    # Check trial status
    subscription = current_user.get("subscription", "free")
    pro_trial = current_user.get("pro_trial", False)
    trial_expires = current_user.get("pro_trial_expires_at")
    trial_days_remaining = None
    
    if pro_trial and trial_expires:
        expiry_date = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        if now > expiry_date:
            subscription = "free"
            pro_trial = False
        else:
            trial_days_remaining = (expiry_date - now).days
    
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        subscription=subscription,
        credits=current_user.get("credits", 0),
        created_at=current_user["created_at"],
        pro_trial=pro_trial,
        pro_trial_expires_at=trial_expires,
        trial_days_remaining=trial_days_remaining
    )

# ============ PASSWORD RESET ============

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Request a password reset email"""
    user = await db.users.find_one({"email": request.email.lower()}, {"_id": 0})
    
    # Always return success to prevent email enumeration attacks
    if not user:
        return {"message": "If this email exists, a reset link has been sent."}
    
    # Generate reset token
    reset_token = generate_reset_token()
    expiry = get_token_expiry()
    
    # Store reset token in database
    await db.password_resets.delete_many({"user_id": user["id"]})  # Remove old tokens
    await db.password_resets.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token": reset_token,
        "expires_at": expiry.isoformat(),
        "created_at": datetime.utcnow().isoformat()
    })
    
    # Get app URL for reset link
    app_url = os.environ.get("APP_URL", "https://shots-gallery-1.preview.emergentagent.com")
    reset_url = f"{app_url}/reset-password?token={reset_token}"
    
    # Send reset email
    if email_configured():
        reset_html = get_password_reset_email_html(user["name"], reset_token, reset_url)
        background_tasks.add_task(send_email, request.email, "Reset Your Azories Password", reset_html)
        logger.info(f"Password reset email queued for {request.email}")
    else:
        logger.warning(f"Email not configured - reset token for {request.email}: {reset_token}")
    
    return {"message": "If this email exists, a reset link has been sent."}

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, background_tasks: BackgroundTasks):
    """Reset password using a valid token"""
    # Find the reset token
    reset_record = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token has expired
    expiry = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.utcnow() > expiry:
        await db.password_resets.delete_one({"token": request.token})
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Get user
    user = await db.users.find_one({"id": reset_record["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Update password
    new_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password": new_hash}}
    )
    
    # Delete used token
    await db.password_resets.delete_one({"token": request.token})
    
    # Send confirmation email
    if email_configured():
        changed_html = get_password_changed_email_html(user["name"])
        background_tasks.add_task(send_email, user["email"], "Your Azories Password Has Been Changed", changed_html)
    
    logger.info(f"Password reset completed for user {user['id']}")
    return {"message": "Password has been reset successfully. You can now log in."}

@api_router.get("/auth/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verify if a password reset token is valid"""
    reset_record = await db.password_resets.find_one({"token": token}, {"_id": 0})
    
    if not reset_record:
        return {"valid": False, "message": "Invalid token"}
    
    expiry = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.utcnow() > expiry:
        return {"valid": False, "message": "Token has expired"}
    
    return {"valid": True, "message": "Token is valid"}

@api_router.get("/credits/balance")
async def get_credit_balance(current_user: dict = Depends(get_current_user)):
    """Get user's credit balance and costs"""
    return {
        "credits": current_user.get("credits", 0),
        "costs": CREDIT_COSTS
    }

@api_router.post("/credits/add")
async def add_credits(amount: int = 100, current_user: dict = Depends(get_current_user)):
    """Add credits - ADMIN/VIP ONLY for manual additions. Regular users must purchase via Stripe."""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin"
    is_vip = user_email in [v.lower() for v in VIP_USERS]
    
    # Only admins and VIP users can add credits directly (for testing/comp)
    # Regular users must purchase via Stripe checkout
    if not is_admin and not is_vip:
        raise HTTPException(
            status_code=403, 
            detail="Credits must be purchased through the store. Please use the Buy Credits page."
        )
    
    current_credits = current_user.get("credits", 0)
    new_balance = current_credits + amount
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"credits": new_balance}}
    )
    
    # Log the manual credit addition
    await db.credit_additions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_email": user_email,
        "amount": amount,
        "previous_balance": current_credits,
        "new_balance": new_balance,
        "added_by": "admin" if is_admin else "vip_self",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "previous_balance": current_credits,
        "added": amount,
        "new_balance": new_balance
    }

async def deduct_credits(user_id: str, operation: str) -> bool:
    """Deduct credits for an operation. Returns True if successful."""
    cost = CREDIT_COSTS.get(operation, 0)
    actual_cost = ACTUAL_COSTS.get(operation, 0)
    
    if cost == 0:
        return True
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        return False
    
    user_email = user.get("email", "")
    
    # Check if user is VIP (unlimited credits but track usage)
    if user_email.lower() in [v.lower() for v in VIP_USERS]:
        # Log VIP usage for tracking costs
        await db.vip_usage.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_email": user_email,
            "operation": operation,
            "credits_would_cost": cost,
            "actual_cost_usd": actual_cost,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"VIP user {user_email} used {operation} (${actual_cost} cost)")
        return True
    
    current_credits = user.get("credits", 0)
    if current_credits < cost:
        return False
    
    # Deduct credits and log the transaction
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"credits": current_credits - cost}}
    )
    
    # Log credit usage for analytics
    await db.credit_usage.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "operation": operation,
        "credits_spent": cost,
        "balance_before": current_credits,
        "balance_after": current_credits - cost,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return True

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

# ============ ASYNC TASK ENDPOINTS ============

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # "pending", "completed", "failed"
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[int] = None  # 0-100

@api_router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, current_user: dict = Depends(get_current_user)):
    """Poll for task status"""
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify task belongs to user
    if task.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this task")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        progress=task.get("progress", 0)
    )

async def run_shots_generation_task(task_id: str, user_id: str, source_image: str, character_id: Optional[str]):
    """Background task to generate 9 shots"""
    try:
        from emergentintegrations.llm.openai import LlmChat, UserMessage, ImageContent
        
        TASK_STORE[task_id]["status"] = "processing"
        TASK_STORE[task_id]["progress"] = 5
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"shots-{user_id}-{str(uuid.uuid4())[:8]}",
            system_message="You are an expert at analyzing images. Describe subjects precisely for regeneration."
        ).with_model("openai", "gpt-4o")
        
        # Handle source image - could be base64 data URI or URL
        logger.info(f"Task {task_id}: Processing source image...")
        
        # If it's a URL, download and convert to base64
        if source_image.startswith('http://') or source_image.startswith('https://'):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source_image) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        else:
                            raise Exception(f"Failed to download image: HTTP {resp.status}")
            except Exception as dl_error:
                logger.error(f"Task {task_id}: Failed to download source image: {dl_error}")
                TASK_STORE[task_id]["status"] = "failed"
                TASK_STORE[task_id]["error"] = "Could not access the source image URL"
                return
        elif source_image.startswith('data:'):
            if ',' in source_image:
                image_base64 = source_image.split(',')[1]
            else:
                image_base64 = source_image.replace('data:image/png;base64,', '').replace('data:image/jpeg;base64,', '')
        else:
            image_base64 = source_image
        
        # Validate the base64
        try:
            missing_padding = len(image_base64) % 4
            if missing_padding:
                image_base64 += '=' * (4 - missing_padding)
            decoded = base64.b64decode(image_base64)
            if len(decoded) < 100:
                raise ValueError("Image too small")
            logger.info(f"Task {task_id}: Decoded image successfully, size={len(decoded)} bytes")
        except Exception as b64_error:
            logger.error(f"Task {task_id}: Invalid base64 image: {b64_error}")
            TASK_STORE[task_id]["status"] = "failed"
            TASK_STORE[task_id]["error"] = "Invalid image format"
            return
        
        TASK_STORE[task_id]["progress"] = 10
        
        # Analyze the image
        user_msg = UserMessage(
            text="Describe this person/subject in detail for image generation. Include: gender, age, hair, eyes, skin, clothing, setting. Be very specific. Respond in one paragraph.",
            file_contents=[ImageContent(image_base64=image_base64)]
        )
        analysis = await chat.send_message(user_msg)
        base_description = analysis.strip() if isinstance(analysis, str) else str(analysis)
        
        logger.info(f"Task {task_id}: Image analysis complete: {base_description[:100]}...")
        TASK_STORE[task_id]["progress"] = 20
        
        # Generate 9 shots
        shots = []
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        for i, shot_prompt in enumerate(SHOT_TYPE_PROMPTS):
            full_prompt = f"{base_description}, {shot_prompt}, professional portrait photography, consistent lighting, high quality"
            logger.info(f"Task {task_id}: Generating shot {i+1}/9...")
            
            try:
                images = await image_gen.generate_images(
                    prompt=full_prompt,
                    model="gpt-image-1",
                    number_of_images=1
                )
                
                if images and len(images) > 0:
                    img_base64 = base64.b64encode(images[0]).decode('utf-8')
                    shots.append({
                        "url": f"data:image/png;base64,{img_base64}",
                        "type": f"shot_{i+1}"
                    })
            except Exception as shot_error:
                logger.error(f"Task {task_id}: Error generating shot {i+1}: {str(shot_error)}")
                # Check for budget error
                if check_budget_error(str(shot_error)):
                    TASK_STORE[task_id]["status"] = "failed"
                    TASK_STORE[task_id]["error"] = "AI service budget limit reached. Please add balance to your Universal Key."
                    return
                continue
            
            TASK_STORE[task_id]["progress"] = 20 + int((i + 1) * 80 / 9)
        
        logger.info(f"Task {task_id}: Completed with {len(shots)} shots")
        TASK_STORE[task_id]["status"] = "completed"
        TASK_STORE[task_id]["result"] = {"shots": shots, "total": len(shots)}
        TASK_STORE[task_id]["progress"] = 100
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task {task_id}: Error: {error_msg}")
        TASK_STORE[task_id]["status"] = "failed"
        if check_budget_error(error_msg):
            TASK_STORE[task_id]["error"] = "AI service budget limit reached. Please add balance to your Universal Key."
        else:
            TASK_STORE[task_id]["error"] = f"Error generating shots: {error_msg}"

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
        "publish_status": "draft",  # New: draft, pending_review, published, rejected
        "moderation_flags": [],
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


# ============ COLLABORATION ROUTES ============

class CollaboratorInvite(BaseModel):
    email: str
    role: str = "editor"  # editor, viewer

class CollaboratorRoleUpdate(BaseModel):
    role: str = "editor"  # editor, viewer


@api_router.post("/books/{book_id}/collaborators/invite")
async def invite_collaborator(book_id: str, invite: CollaboratorInvite, current_user: dict = Depends(get_current_user)):
    """Invite a collaborator to a book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can invite collaborators")
    
    # Find the user by email
    invitee = await db.users.find_one({"email": invite.email}, {"_id": 0})
    if not invitee:
        raise HTTPException(status_code=404, detail="User not found. They need to create an account first.")
    
    if invitee["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="You can't invite yourself")
    
    # Check if already a collaborator
    collaborators = book.get("collaborators", [])
    if any(c["user_id"] == invitee["id"] for c in collaborators):
        raise HTTPException(status_code=400, detail="User is already a collaborator")
    
    # Add collaborator
    new_collaborator = {
        "user_id": invitee["id"],
        "email": invitee["email"],
        "name": invitee.get("name", invitee["email"]),
        "role": invite.role,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.books.update_one(
        {"id": book_id},
        {"$push": {"collaborators": new_collaborator}}
    )
    
    return {"success": True, "message": f"Invited {invitee['email']} as {invite.role}"}


class InviteLinkRequest(BaseModel):
    role: str = "editor"


@api_router.post("/books/{book_id}/invite-link")
async def generate_invite_link(book_id: str, request: InviteLinkRequest, current_user: dict = Depends(get_current_user)):
    """Generate a shareable invite link for a book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can generate invite links")
    
    # Generate a unique invite token
    invite_token = str(uuid.uuid4())
    
    # Store the invite in database
    invite_data = {
        "id": invite_token,
        "book_id": book_id,
        "role": request.role,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "used": False
    }
    await db.invites.insert_one(invite_data)
    
    # Generate the link (frontend will handle this route)
    base_url = os.environ.get('FRONTEND_URL', 'https://shots-gallery-1.preview.emergentagent.com')
    invite_link = f"{base_url}/invite/{invite_token}"
    
    return {"invite_link": invite_link, "token": invite_token}


@api_router.get("/books/{book_id}/collaborators")
async def get_collaborators(book_id: str, current_user: dict = Depends(get_current_user)):
    """Get all collaborators for a book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if user has access
    is_owner = book["author_id"] == current_user["id"]
    is_collaborator = any(c["user_id"] == current_user["id"] for c in book.get("collaborators", []))
    
    if not is_owner and not is_collaborator:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {"collaborators": book.get("collaborators", [])}


@api_router.put("/books/{book_id}/collaborators/{user_id}")
async def update_collaborator_role(book_id: str, user_id: str, update: CollaboratorRoleUpdate, current_user: dict = Depends(get_current_user)):
    """Update a collaborator's role"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can update roles")
    
    await db.books.update_one(
        {"id": book_id, "collaborators.user_id": user_id},
        {"$set": {"collaborators.$.role": update.role}}
    )
    
    return {"success": True}


@api_router.delete("/books/{book_id}/collaborators/{user_id}")
async def remove_collaborator(book_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    """Remove a collaborator from a book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can remove collaborators")
    
    await db.books.update_one(
        {"id": book_id},
        {"$pull": {"collaborators": {"user_id": user_id}}}
    )
    
    return {"success": True}


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

# Book Image Library endpoint - save workflow outputs to book
@api_router.post("/books/{book_id}/images")
async def save_image_to_book(book_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Save an image from the Art Studio workflow to a book's image library"""
    data = await request.json()
    image_url = data.get("image_url")
    name = data.get("name", "Workflow Image")
    image_type = data.get("type", "illustration")  # character, scene, illustration
    style = data.get("style", "fantasy")
    metadata = data.get("metadata", {})
    
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    # Verify user has access to this book
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if user is author or collaborator
    is_author = book["author_id"] == current_user["id"]
    collaborators = book.get("collaborators", [])
    is_collaborator = any(c.get("user_id") == current_user["id"] for c in collaborators)
    
    if not is_author and not is_collaborator:
        raise HTTPException(status_code=403, detail="Not authorized to add images to this book")
    
    # Create book image entry
    book_image = {
        "id": str(uuid.uuid4()),
        "book_id": book_id,
        "user_id": current_user["id"],
        "image_url": image_url,
        "name": name,
        "type": image_type,
        "style": style,
        "metadata": metadata,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.book_images.insert_one(book_image)
    
    # Return without _id
    book_image.pop("_id", None)
    return {"success": True, "image": book_image}

@api_router.get("/books/{book_id}/images")
async def get_book_images(book_id: str, current_user: dict = Depends(get_current_user)):
    """Get all images in a book's library"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check access
    is_author = book["author_id"] == current_user["id"]
    collaborators = book.get("collaborators", [])
    is_collaborator = any(c.get("user_id") == current_user["id"] for c in collaborators)
    
    if not is_author and not is_collaborator:
        raise HTTPException(status_code=403, detail="Not authorized to view this book's images")
    
    images = await db.book_images.find({"book_id": book_id}, {"_id": 0}).to_list(500)
    return {"images": images}

@api_router.delete("/books/{book_id}/images/{image_id}")
async def delete_book_image(book_id: str, image_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an image from a book's library"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the book author can delete images")
    
    result = await db.book_images.delete_one({"id": image_id, "book_id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {"success": True}

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

class ReorderBookRequest(BaseModel):
    new_order: int

@api_router.put("/series/{series_id}/books/{book_id}/order")
async def reorder_book_in_series(series_id: str, book_id: str, request: ReorderBookRequest, current_user: dict = Depends(get_current_user)):
    """Reorder a book within a series"""
    book = await db.books.find_one({"id": book_id, "series_id": series_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found in this series")
    
    if book["author_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    old_order = book.get("series_order", 1)
    new_order = request.new_order
    
    # Get all books in the series
    series_books = await db.books.find({"series_id": series_id}).sort("series_order", 1).to_list(100)
    
    # Update orders for all affected books
    for i, b in enumerate(series_books):
        current_order = b.get("series_order", i + 1)
        
        if b["id"] == book_id:
            # This is the book being moved
            await db.books.update_one({"id": book_id}, {"$set": {"series_order": new_order}})
        elif old_order < new_order:
            # Moving down - shift books up
            if current_order > old_order and current_order <= new_order:
                await db.books.update_one({"id": b["id"]}, {"$set": {"series_order": current_order - 1}})
        else:
            # Moving up - shift books down
            if current_order >= new_order and current_order < old_order:
                await db.books.update_one({"id": b["id"]}, {"$set": {"series_order": current_order + 1}})
    
    return {"message": "Book order updated", "new_order": new_order}

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
    """Admin can publish/unpublish any book directly"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_published", False)
    update_data = {
        "is_published": new_status,
        "publish_status": "published" if new_status else "draft"
    }
    await db.books.update_one({"id": book_id}, {"$set": update_data})
    return {"is_published": new_status, "publish_status": update_data["publish_status"]}

@api_router.delete("/admin/books/{book_id}")
async def admin_delete_book(book_id: str, admin: dict = Depends(get_admin_user)):
    """Admin can delete any book"""
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    for chapter in chapters:
        await db.pages.delete_many({"chapter_id": chapter["id"]})
    await db.chapters.delete_many({"book_id": book_id})
    await db.books.delete_one({"id": book_id})
    return {"message": "Book deleted by admin"}

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
        page.setdefault("image_position_x", 50)
        page.setdefault("image_position_y", 50)
        page.setdefault("image_fit", "cover")
        page.setdefault("font_family", "default")
        page.setdefault("font_size", "medium")
        page.setdefault("text_align", "left")
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
    updated.setdefault("use_video", False)
    updated.setdefault("layout_type", "single")
    updated.setdefault("image_position_x", 50)
    updated.setdefault("image_position_y", 50)
    updated.setdefault("image_fit", "cover")
    updated.setdefault("font_family", "default")
    updated.setdefault("font_size", "medium")
    updated.setdefault("text_align", "left")
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
        
        # Validate duration - Sora 2 only supports 4, 8, or 12 seconds
        valid_durations = [4, 8, 12]
        duration = request.duration
        if duration not in valid_durations:
            # Round to nearest valid duration
            duration = min(valid_durations, key=lambda x: abs(x - duration))
        
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
            duration=duration,
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

# Image Animation Request Model
class AnimateImageRequest(BaseModel):
    image_url: str  # URL or base64 of the image to animate
    motion_prompt: str = "gentle subtle movement, breathing, hair flowing"  # How to animate
    duration: int = 4  # 4, 8, or 12 seconds
    style: str = "natural"  # natural, dramatic, subtle

# In-memory job storage for animation jobs
animation_jobs = {}

@api_router.post("/art-studio/animate-image")
async def animate_image(request: AnimateImageRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Start an image animation job - returns immediately with job_id for polling"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    animation_jobs[job_id] = {
        "status": "starting",
        "progress": 0,
        "message": "Initializing animation...",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user["id"]
    }
    
    # Start background task
    background_tasks.add_task(
        process_animation_job,
        job_id,
        request.image_url,
        request.motion_prompt,
        request.duration,
        request.style,
        current_user["id"]
    )
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Animation job started. Poll for progress."
    }

async def process_animation_job(job_id: str, image_url: str, motion_prompt: str, duration: int, style: str, user_id: str):
    """Background task to process animation"""
    try:
        animation_jobs[job_id]["status"] = "analyzing"
        animation_jobs[job_id]["progress"] = 10
        animation_jobs[job_id]["message"] = "Analyzing image..."
        
        from emergentintegrations.llm.openai import LlmChat, UserMessage, ImageContent
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"animate-{user_id}-{job_id[:8]}",
            system_message="You are an image analysis expert. Describe images in detail for video animation."
        ).with_model("openai", "gpt-4o")
        
        analysis_prompt = """Analyze this image and describe it in detail for video animation. 
        Include: subject, pose, expression, clothing, background, lighting, art style.
        Be specific and detailed. Format as a single paragraph."""
        
        if image_url.startswith('data:'):
            if ',' in image_url:
                image_base64 = image_url.split(',')[1]
            else:
                image_base64 = image_url
        else:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30)
                image_bytes = response.content
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        animation_jobs[job_id]["progress"] = 20
        animation_jobs[job_id]["message"] = "Understanding image content..."
        
        user_msg = UserMessage(
            text=analysis_prompt,
            file_contents=[ImageContent(image_base64=image_base64)]
        )
        image_description = await chat.send_message(user_msg)
        
        animation_jobs[job_id]["status"] = "generating"
        animation_jobs[job_id]["progress"] = 30
        animation_jobs[job_id]["message"] = "Starting Sora 2 video generation (2-5 minutes)..."
        
        motion_styles = {
            "natural": "natural subtle movement, gentle breathing, soft hair movement, slight eye blinks",
            "dramatic": "dramatic cinematic movement, wind blowing, dynamic camera motion, emotional expression changes",
            "subtle": "very subtle almost still, only slight breathing movement, peaceful and calm"
        }
        motion_desc = motion_styles.get(style, motion_styles["natural"])
        
        # Build comprehensive animation prompt using the detailed image description
        animation_prompt = f"""Create a video animation of this exact scene with {motion_desc}:

{image_description}

Motion details: {motion_prompt}

Important: Maintain exact visual consistency with the description above. The character, setting, colors, lighting, and art style must match precisely. Only add natural movement and animation while preserving the original appearance."""
        
        video_gen = OpenAIVideoGeneration(api_key=EMERGENT_LLM_KEY)
        
        animation_jobs[job_id]["progress"] = 40
        animation_jobs[job_id]["message"] = "Sora 2 is generating your animation..."
        
        # Generate video (text-to-video without reference image as Sora 2 API doesn't support image input)
        video_bytes = video_gen.text_to_video(
            prompt=animation_prompt,
            model="sora-2",
            size="1280x720",
            duration=duration,
            max_wait_time=900
        )
        
        if video_bytes:
            animation_jobs[job_id]["progress"] = 90
            animation_jobs[job_id]["message"] = "Finalizing video..."
            
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
            video_id = str(uuid.uuid4())
            
            animation_jobs[job_id] = {
                "status": "completed",
                "progress": 100,
                "message": "Animation complete!",
                "video_base64": video_base64,
                "video_id": video_id,
                "user_id": user_id
            }
        else:
            animation_jobs[job_id] = {
                "status": "failed",
                "progress": 0,
                "message": "Animation generation failed - no video returned",
                "user_id": user_id
            }
            
    except Exception as e:
        logger.error(f"Animation job {job_id} failed: {str(e)}")
        animation_jobs[job_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Animation failed: {str(e)}",
            "user_id": user_id
        }

@api_router.get("/art-studio/animation-status/{job_id}")
async def get_animation_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Poll for animation job status"""
    if job_id not in animation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = animation_jobs[job_id]
    
    if job.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if job["status"] != "completed":
        return {
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"]
        }
    
    return {
        "status": "completed",
        "progress": 100,
        "message": job["message"],
        "video_base64": job.get("video_base64"),
        "video_id": job.get("video_id")
    }

# ============ PRO STUDIO ROUTES ============

# Camera and lens configurations for Cinema Studio
CAMERA_CONFIGS = {
    "arri-alexa-35": "shot on ARRI Alexa 35, rich colors, natural skin tones, filmic look",
    "arri-alexa-mini": "shot on ARRI Alexa Mini, cinematic quality, portable feel",
    "red-v-raptor": "shot on RED V-Raptor 8K, ultra sharp, vibrant colors, documentary style",
    "red-komodo": "shot on RED Komodo 6K, clean modern look, great dynamic range",
    "sony-venice-2": "shot on Sony Venice 2, excellent low light, natural colors",
    "blackmagic-ursa": "shot on Blackmagic URSA Mini Pro 12K, high resolution, film-like grain",
    "canon-c500": "shot on Canon C500 Mark II, warm tones, pleasing skin, classic look"
}

LENS_CONFIGS = {
    "panavision-series": "Panavision C Series lens, dreamy bokeh, classic Hollywood look, soft edges",
    "panavision-primo": "Panavision Primo 70 lens, ultra sharp center, smooth falloff, modern cinema",
    "cooke-s4": "Cooke S4/i lens, warm creamy Cooke Look, beautiful skin rendering",
    "cooke-anamorphic": "Cooke Anamorphic/i lens, oval bokeh, lens flares, epic widescreen",
    "zeiss-supreme": "Zeiss Supreme Prime lens, clean neutral high contrast modern look",
    "hawk-v-lite": "Hawk V-Lite lens, anamorphic flares, warm highlights, vintage feel",
    "helios-44": "Helios 44-2 lens, swirly bokeh, character, dreamy distortion",
    "petzval-lens": "Petzval 85mm lens, extreme swirly bokeh, artistic blur, vintage portrait",
    "leica-summilux": "Leica Summilux-C lens, precise crisp subtle warmth documentary style"
}

LIGHTING_CONFIGS = {
    "natural": "natural daylight, soft shadows, realistic",
    "golden-hour": "golden hour lighting, warm sunset glow, soft",
    "blue-hour": "blue hour twilight, cool tones, atmospheric",
    "studio": "professional studio lighting, clean, even",
    "dramatic": "dramatic lighting, high contrast, shadows",
    "neon": "neon lights, colorful glow, cyberpunk lighting",
    "candlelight": "warm candlelight, intimate, flickering",
    "moonlight": "soft moonlight, nighttime, ethereal glow",
    "overcast": "overcast sky, soft diffused light, no harsh shadows",
    "backlit": "backlit rim lighting, silhouette edge, dramatic"
}

EXPRESSION_PROMPTS = {
    "neutral": "neutral expression, calm face",
    "happy": "happy expression, warm smile, joyful",
    "smiling": "gentle smile, friendly expression",
    "laughing": "laughing, genuine joy, bright expression",
    "serious": "serious expression, focused, determined",
    "thoughtful": "thoughtful expression, contemplative, pondering",
    "surprised": "surprised expression, wide eyes, amazed",
    "sad": "sad expression, melancholy, emotional",
    "angry": "angry expression, intense, fierce",
    "confident": "confident expression, self-assured, powerful",
    "shy": "shy expression, bashful, looking away slightly",
    "mysterious": "mysterious expression, enigmatic, intriguing"
}

SHOT_TYPE_PROMPTS = [
    "front facing, looking at camera, eye contact",
    "three quarter view from left, slight turn",
    "three quarter view from right, slight turn",
    "side profile view from left, looking left",
    "side profile view from right, looking right",
    "looking upward, low angle perspective",
    "looking downward, high angle perspective",
    "over the shoulder view, back partially visible",
    "back view, showing from behind"
]

@api_router.get("/pro-studio/characters")
async def get_characters(current_user: dict = Depends(get_current_user)):
    """Get all characters for the current user"""
    characters = await db.pro_studio_characters.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0}
    ).to_list(100)
    return {"characters": characters}

@api_router.get("/pro-studio/character-styles")
async def get_character_styles():
    """Get available character styles"""
    return {"styles": CHARACTER_STYLES}

@api_router.get("/pro-studio/character-genres")
async def get_character_genres():
    """Get available character genres"""
    return {"genres": CHARACTER_GENRES}

@api_router.get("/pro-studio/characters/{character_id}")
async def get_character(character_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific character"""
    character = await db.pro_studio_characters.find_one(
        {"id": character_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"character": character}

@api_router.post("/pro-studio/characters")
async def create_character(request: CharacterCreate, current_user: dict = Depends(get_current_user)):
    """Create a new character - from reference images AND/OR description prompt
    
    Characters can be created with:
    1. Upload reference images - AI will analyze and create consistent description
    2. Provide description prompt - AI will generate character from your description
    3. BOTH images AND description together for maximum control
    """
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    # Need at least one of: reference images OR description prompt
    has_images = len(request.reference_images) > 0
    has_description = bool(request.description_prompt)
    
    if not has_images and not has_description:
        raise HTTPException(status_code=400, detail="Provide reference images and/or a description prompt")
    
    try:
        description = ""
        thumbnail = None
        style_info = next((s for s in CHARACTER_STYLES if s["id"] == request.style), {"name": request.style})
        genre_info = next((g for g in CHARACTER_GENRES if g["id"] == request.genre), {"name": request.genre})
        
        description_parts = [
            f"Character: {request.name}",
            f"Style: {style_info.get('name', request.style)} - {style_info.get('description', '')}",
            f"Genre: {genre_info.get('name', request.genre)}",
        ]
        
        # If we have a description prompt, add it
        if has_description:
            description_parts.append(f"\nAppearance: {request.description_prompt}")
            
            if request.physical_traits:
                traits = request.physical_traits
                trait_str = ", ".join([f"{k}: {v}" for k, v in traits.items() if v])
                if trait_str:
                    description_parts.append(f"Physical traits: {trait_str}")
            
            if request.special_features:
                description_parts.append(f"Special features: {request.special_features}")
            
            if request.personality:
                description_parts.append(f"Personality: {request.personality}")
        
        # If we have reference images, analyze them and enhance description
        if has_images and EMERGENT_LLM_KEY:
            try:
                from emergentintegrations.llm.openai import LlmChat, UserMessage, ImageContent
                
                chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=f"char-{current_user['id']}-{str(uuid.uuid4())[:8]}",
                    system_message="You are an expert at analyzing images and describing characters in detail for AI image generation."
                ).with_model("openai", "gpt-4o")
                
                analysis_prompt = f"""Analyze this character image and provide a detailed description for consistent AI image generation.
                
                Character Style: {style_info.get('name', request.style)} ({style_info.get('description', '')})
                Genre: {genre_info.get('name', request.genre)}
                {"User's description: " + request.description_prompt if has_description else ""}
                
                Include:
                - Gender and apparent age
                - Hair color, style, and length
                - Eye color and shape
                - Skin tone and complexion
                - Face shape and distinctive features
                - Body type (if visible)
                - Clothing style
                - Any unique features (scars, tattoos, accessories, etc.)
                
                Respond in a detailed paragraph that can be used as a prompt prefix for generating consistent images of this character."""
                
                first_image = request.reference_images[0]
                
                if first_image.startswith('data:'):
                    if ',' in first_image:
                        image_base64 = first_image.split(',')[1]
                    else:
                        image_base64 = first_image
                    
                    user_msg = UserMessage(
                        text=analysis_prompt,
                        file_contents=[ImageContent(image_base64=image_base64)]
                    )
                    image_analysis = await chat.send_message(user_msg)
                    description_parts.append(f"\nImage Analysis: {image_analysis}")
                elif first_image.startswith('http'):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(first_image) as resp:
                            if resp.status == 200:
                                image_data = await resp.read()
                                image_base64 = base64.b64encode(image_data).decode('utf-8')
                                user_msg = UserMessage(
                                    text=analysis_prompt,
                                    file_contents=[ImageContent(image_base64=image_base64)]
                                )
                                image_analysis = await chat.send_message(user_msg)
                                description_parts.append(f"\nImage Analysis: {image_analysis}")
                else:
                    user_msg = UserMessage(
                        text=analysis_prompt,
                        file_contents=[ImageContent(image_base64=first_image)]
                    )
                    image_analysis = await chat.send_message(user_msg)
                    description_parts.append(f"\nImage Analysis: {image_analysis}")
                
                # Use first reference image as thumbnail if no generated one
                thumbnail = first_image
            except Exception as e:
                logger.warning(f"Could not analyze reference image: {e}")
                if has_images:
                    thumbnail = request.reference_images[0]
        elif has_images:
            # No LLM key, just use reference image as thumbnail
            thumbnail = request.reference_images[0]
        
        description = "\n".join(description_parts)
        
        # Generate a thumbnail image if we have description but no images
        if not thumbnail and has_description and FAL_AVAILABLE:
            try:
                gen_prompt = f"{request.description_prompt}, {style_info.get('name', '')} style, character portrait, detailed face"
                result = await generate_image_flux(
                    prompt=gen_prompt,
                    model="flux-dev",
                    image_size="square_hd",
                    num_images=1
                )
                if result.get("images"):
                    thumbnail = result["images"][0].get("url")
            except Exception as e:
                logger.warning(f"Could not generate thumbnail: {e}")
        
        # Create character record
        char_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        character = {
            "id": char_id,
            "user_id": current_user["id"],
            "name": request.name,
            "description": description.strip() if isinstance(description, str) else str(description),
            "description_prompt": request.description_prompt,
            "style": request.style,
            "genre": request.genre,
            "physical_traits": request.physical_traits,
            "personality": request.personality,
            "backstory": request.backstory,
            "special_features": request.special_features,
            "reference_images": request.reference_images[:20] if request.reference_images else [],
            "thumbnail": thumbnail,
            "created_at": now,
            "updated_at": now
        }
        
        # If we generated a thumbnail but have no reference images, 
        # add the thumbnail as the first reference image (enables PuLID later)
        if thumbnail and not character.get("reference_images"):
            character["reference_images"] = [thumbnail]
        
        await db.pro_studio_characters.insert_one(character)
        
        character.pop("_id", None)
        return {"character": character, "success": True}
        
    except Exception as e:
        logger.error(f"Error creating character: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating character: {str(e)}")

@api_router.put("/pro-studio/characters/{character_id}")
async def update_character(character_id: str, request: CharacterUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing character - add more images, update description, etc."""
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    update_data = {}
    
    if request.name:
        update_data["name"] = request.name
    if request.description_prompt is not None:
        update_data["description_prompt"] = request.description_prompt
    if request.style:
        update_data["style"] = request.style
    if request.genre:
        update_data["genre"] = request.genre
    if request.physical_traits:
        update_data["physical_traits"] = request.physical_traits
    if request.personality is not None:
        update_data["personality"] = request.personality
    if request.backstory:
        update_data["backstory"] = request.backstory
    if request.special_features is not None:
        update_data["special_features"] = request.special_features
    
    # Add new reference images to existing ones
    if request.add_reference_images:
        existing_images = character.get("reference_images", [])
        new_images = existing_images + request.add_reference_images
        update_data["reference_images"] = new_images[:20]  # Cap at 20
        
        # Update thumbnail if we didn't have one
        if not character.get("thumbnail") and new_images:
            update_data["thumbnail"] = new_images[0]
    
    # Rebuild description if key fields changed
    if any(k in update_data for k in ['description_prompt', 'style', 'genre', 'special_features', 'name']):
        style_info = next((s for s in CHARACTER_STYLES if s["id"] == update_data.get("style", character.get("style"))), {"name": "illustration"})
        genre_info = next((g for g in CHARACTER_GENRES if g["id"] == update_data.get("genre", character.get("genre"))), {"name": "fantasy"})
        
        desc_parts = [
            f"Character: {update_data.get('name', character.get('name'))}",
            f"Style: {style_info.get('name', '')} - {style_info.get('description', '')}",
            f"Genre: {genre_info.get('name', '')}",
        ]
        desc_prompt = update_data.get('description_prompt') or character.get('description_prompt')
        if desc_prompt:
            desc_parts.append(f"\nAppearance: {desc_prompt}")
        special = update_data.get('special_features') or character.get('special_features')
        if special:
            desc_parts.append(f"Special features: {special}")
        pers = update_data.get('personality') or character.get('personality')
        if pers:
            desc_parts.append(f"Personality: {pers}")
        
        update_data["description"] = "\n".join(desc_parts)
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.pro_studio_characters.update_one(
        {"id": character_id},
        {"$set": update_data}
    )
    
    # Get updated character
    updated = await db.pro_studio_characters.find_one({"id": character_id}, {"_id": 0})
    return {"character": updated, "success": True}

@api_router.post("/pro-studio/characters/{character_id}/generate-thumbnail")
async def generate_character_thumbnail(character_id: str, current_user: dict = Depends(get_current_user)):
    """Generate or regenerate a thumbnail for a character"""
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="Image generation not available")
    
    try:
        style_info = next((s for s in CHARACTER_STYLES if s["id"] == character.get("style")), {"name": "illustration"})
        
        # Build generation prompt from character data
        prompt_parts = []
        if character.get("description"):
            prompt_parts.append(character["description"][:500])
        elif character.get("description_prompt"):
            prompt_parts.append(character["description_prompt"])
        
        prompt_parts.append(f"{style_info.get('name', '')} style")
        prompt_parts.append("character portrait, detailed face, high quality")
        
        gen_prompt = ", ".join(prompt_parts)
        
        result = await generate_image_flux(
            prompt=gen_prompt,
            model="flux-dev",
            image_size="square_hd",
            num_images=1
        )
        
        if result.get("images"):
            thumbnail_url = result["images"][0].get("url")
            await db.pro_studio_characters.update_one(
                {"id": character_id},
                {"$set": {"thumbnail": thumbnail_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return {"thumbnail": thumbnail_url, "success": True}
        
        raise HTTPException(status_code=500, detail="Failed to generate thumbnail")
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/pro-studio/characters/{character_id}")
async def delete_character(character_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a character"""
    result = await db.pro_studio_characters.delete_one({
        "id": character_id, 
        "user_id": current_user["id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")
    # Also delete all gallery images for this character
    await db.character_gallery.delete_many({
        "character_id": character_id,
        "user_id": current_user["id"]
    })
    return {"success": True}

# Character Gallery/Folder endpoints
@api_router.get("/pro-studio/characters/{character_id}/gallery")
async def get_character_gallery(character_id: str, current_user: dict = Depends(get_current_user)):
    """Get all generated images for a character (character folder)"""
    # Verify character belongs to user
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get all images in this character's gallery
    images = await db.character_gallery.find(
        {"character_id": character_id, "user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"images": images, "character_id": character_id, "count": len(images)}

@api_router.post("/pro-studio/characters/{character_id}/gallery")
async def add_to_character_gallery(character_id: str, request: dict, current_user: dict = Depends(get_current_user)):
    """Save a generated image to a character's folder/gallery"""
    # Verify character belongs to user
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    image_url = request.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    now = datetime.now(timezone.utc).isoformat()
    gallery_item = {
        "id": str(uuid.uuid4()),
        "character_id": character_id,
        "user_id": current_user["id"],
        "image_url": image_url,
        "prompt": request.get("prompt", ""),
        "type": request.get("type", "generated"),  # 'generated', 'expression', 'consistent', etc.
        "created_at": now
    }
    
    await db.character_gallery.insert_one(gallery_item)
    gallery_item.pop("_id", None)
    
    return {"success": True, "item": gallery_item}

@api_router.delete("/pro-studio/characters/{character_id}/gallery/{image_id}")
async def delete_from_character_gallery(character_id: str, image_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an image from a character's gallery"""
    result = await db.character_gallery.delete_one({
        "id": image_id,
        "character_id": character_id,
        "user_id": current_user["id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"success": True}

@api_router.post("/pro-studio/characters/{character_id}/add-reference")
async def add_reference_image(character_id: str, request: dict, current_user: dict = Depends(get_current_user)):
    """Add an image to a character's reference images (for LoRA training)
    
    This allows users to build up their reference image collection
    from generated images to eventually train a LoRA model.
    """
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    image_url = request.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    # Add to reference images (max 20)
    ref_images = character.get("reference_images", [])
    if image_url not in ref_images:  # Avoid duplicates
        ref_images.append(image_url)
        if len(ref_images) > 20:
            ref_images = ref_images[:20]
        
        await db.pro_studio_characters.update_one(
            {"id": character_id},
            {"$set": {
                "reference_images": ref_images,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    # Check if now eligible for LoRA training
    can_train_lora = len(ref_images) >= 3
    
    return {
        "success": True,
        "reference_images_count": len(ref_images),
        "can_train_lora": can_train_lora,
        "message": f"Reference image added. {len(ref_images)}/3 images for LoRA training." if len(ref_images) < 3 else "You can now train a LoRA model for this character!"
    }

@api_router.post("/pro-studio/characters/{character_id}/regenerate-thumbnail")
async def regenerate_character_thumbnail(character_id: str, current_user: dict = Depends(get_current_user)):
    """Regenerate the thumbnail for a character using fal.ai
    
    This creates a new thumbnail that may better match subsequent generations.
    """
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    try:
        thumbnail = None
        style_info = next((s for s in CHARACTER_STYLES if s["id"] == character.get("style")), {"name": "illustration"})
        
        # Build a detailed prompt from character info
        prompt_parts = [character.get("description_prompt", f"Portrait of {character['name']}")]
        prompt_parts.append(f"{style_info.get('name', '')} style")
        prompt_parts.append("character portrait, detailed face, high quality")
        
        if character.get("special_features"):
            prompt_parts.append(character["special_features"])
        
        gen_prompt = ", ".join(prompt_parts)
        
        # Try fal.ai first for consistency
        if FAL_AVAILABLE:
            result = await generate_image_flux(
                prompt=gen_prompt,
                model="flux-dev",
                image_size="square_hd",
                num_images=1
            )
            if result.get("images"):
                thumbnail = result["images"][0].get("url")
        
        # Fallback to OpenAI
        if not thumbnail and EMERGENT_LLM_KEY:
            image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
            images = await image_gen.generate_images(
                prompt=gen_prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            if images and len(images) > 0:
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                thumbnail = f"data:image/png;base64,{image_base64}"
        
        if thumbnail:
            await db.pro_studio_characters.update_one(
                {"id": character_id},
                {"$set": {"thumbnail": thumbnail, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return {"success": True, "thumbnail": thumbnail}
        else:
            raise HTTPException(status_code=500, detail="Could not generate thumbnail")
            
    except Exception as e:
        logger.error(f"Thumbnail regeneration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Scene Consistency Endpoints ====================

SCENE_TYPES = [
    {"id": "indoor", "name": "Indoor", "description": "Interior spaces like rooms, buildings"},
    {"id": "outdoor", "name": "Outdoor", "description": "Exterior natural or urban environments"},
    {"id": "urban", "name": "Urban", "description": "City streets, buildings, modern settings"},
    {"id": "nature", "name": "Nature", "description": "Forests, mountains, beaches, natural landscapes"},
    {"id": "fantasy", "name": "Fantasy", "description": "Magical, otherworldly locations"},
    {"id": "scifi", "name": "Sci-Fi", "description": "Futuristic, technological environments"},
]

LIGHTING_OPTIONS = [
    {"id": "natural", "name": "Natural Light"},
    {"id": "golden_hour", "name": "Golden Hour"},
    {"id": "blue_hour", "name": "Blue Hour"},
    {"id": "dramatic", "name": "Dramatic"},
    {"id": "soft", "name": "Soft/Diffused"},
    {"id": "neon", "name": "Neon/Cyberpunk"},
    {"id": "candlelight", "name": "Candlelight"},
    {"id": "moonlight", "name": "Moonlight"},
]

MOOD_OPTIONS = [
    {"id": "peaceful", "name": "Peaceful"},
    {"id": "mysterious", "name": "Mysterious"},
    {"id": "adventurous", "name": "Adventurous"},
    {"id": "romantic", "name": "Romantic"},
    {"id": "tense", "name": "Tense"},
    {"id": "whimsical", "name": "Whimsical"},
    {"id": "dark", "name": "Dark"},
    {"id": "cheerful", "name": "Cheerful"},
]

@api_router.get("/pro-studio/scene-options")
async def get_scene_options():
    """Get available scene configuration options"""
    return {
        "location_types": SCENE_TYPES,
        "lighting": LIGHTING_OPTIONS,
        "moods": MOOD_OPTIONS
    }

@api_router.post("/pro-studio/scenes")
async def create_scene(request: SceneCreate, current_user: dict = Depends(get_current_user)):
    """Create a new scene for consistent backgrounds/environments"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    try:
        # Build scene description
        style_info = next((s for s in CHARACTER_STYLES if s["id"] == request.style), {"name": request.style})
        genre_info = next((g for g in CHARACTER_GENRES if g["id"] == request.genre), {"name": request.genre})
        location_info = next((loc for loc in SCENE_TYPES if loc["id"] == request.location_type), {"name": request.location_type or "location"})
        lighting_info = next((lit for lit in LIGHTING_OPTIONS if lit["id"] == request.lighting), {"name": request.lighting or "natural"})
        mood_info = next((m for m in MOOD_OPTIONS if m["id"] == request.mood), {"name": request.mood or ""})
        
        desc_parts = [
            f"Scene: {request.name}",
            f"Description: {request.description}",
            f"Style: {style_info.get('name', request.style)}",
            f"Genre: {genre_info.get('name', request.genre)}",
            f"Location: {location_info.get('name', '')}",
            f"Lighting: {lighting_info.get('name', '')}",
        ]
        if request.time_of_day:
            desc_parts.append(f"Time: {request.time_of_day}")
        if request.weather:
            desc_parts.append(f"Weather: {request.weather}")
        if mood_info.get('name'):
            desc_parts.append(f"Mood: {mood_info.get('name')}")
        
        full_description = "\n".join(desc_parts)
        
        # Generate a thumbnail for the scene (optional - don't fail if this errors)
        thumbnail = None
        gen_prompt = f"{request.description}, {style_info.get('name', '')} style, {location_info.get('name', '')} scene, {lighting_info.get('name', '')} lighting, {genre_info.get('name', '')} genre, no characters, background environment, scenic, detailed"
        
        if FAL_AVAILABLE:
            try:
                result = await generate_image_flux(
                    prompt=gen_prompt,
                    model="flux-dev",
                    image_size="landscape_16_9",
                    num_images=1
                )
                if result.get("images"):
                    thumbnail = result["images"][0].get("url")
            except Exception as thumb_err:
                logger.warning(f"Could not generate scene thumbnail: {thumb_err}")
        
        scene_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        scene = {
            "id": scene_id,
            "user_id": current_user["id"],
            "name": request.name,
            "description": full_description,
            "description_prompt": request.description,
            "style": request.style,
            "genre": request.genre,
            "location_type": request.location_type,
            "lighting": request.lighting,
            "mood": request.mood,
            "time_of_day": request.time_of_day,
            "weather": request.weather,
            "reference_images": request.reference_images[:10] if request.reference_images else [],
            "thumbnail": thumbnail,
            "created_at": now,
            "updated_at": now
        }
        
        # Add thumbnail as first reference if we have one
        if thumbnail and not scene.get("reference_images"):
            scene["reference_images"] = [thumbnail]
        
        await db.pro_studio_scenes.insert_one(scene)
        scene.pop("_id", None)
        
        return {"scene": scene, "success": True}
        
    except Exception as e:
        logger.error(f"Scene creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pro-studio/scenes")
async def get_scenes(current_user: dict = Depends(get_current_user)):
    """Get user's saved scenes"""
    scenes = await db.pro_studio_scenes.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"scenes": scenes}

@api_router.get("/pro-studio/scenes/{scene_id}")
async def get_scene(scene_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific scene"""
    scene = await db.pro_studio_scenes.find_one(
        {"id": scene_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"scene": scene}

@api_router.put("/pro-studio/scenes/{scene_id}")
async def update_scene(scene_id: str, request: SceneUpdate, current_user: dict = Depends(get_current_user)):
    """Update a scene"""
    scene = await db.pro_studio_scenes.find_one({"id": scene_id, "user_id": current_user["id"]})
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    update_data = {k: v for k, v in request.dict().items() if v is not None and k != 'add_reference_images'}
    
    if request.add_reference_images:
        existing = scene.get("reference_images", [])
        update_data["reference_images"] = (existing + request.add_reference_images)[:10]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.pro_studio_scenes.update_one({"id": scene_id}, {"$set": update_data})
    
    updated = await db.pro_studio_scenes.find_one({"id": scene_id}, {"_id": 0})
    return {"scene": updated, "success": True}

@api_router.delete("/pro-studio/scenes/{scene_id}")
async def delete_scene(scene_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a scene"""
    result = await db.pro_studio_scenes.delete_one({"id": scene_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scene not found")
    # Also delete scene gallery
    await db.scene_gallery.delete_many({"scene_id": scene_id, "user_id": current_user["id"]})
    return {"success": True}

# Scene Gallery/Folder endpoints
@api_router.get("/pro-studio/scenes/{scene_id}/gallery")
async def get_scene_gallery(scene_id: str, current_user: dict = Depends(get_current_user)):
    """Get all generated images for a scene (scene folder)"""
    scene = await db.pro_studio_scenes.find_one({"id": scene_id, "user_id": current_user["id"]})
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    images = await db.scene_gallery.find(
        {"scene_id": scene_id, "user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"images": images, "scene_id": scene_id, "count": len(images)}

@api_router.post("/pro-studio/scenes/{scene_id}/gallery")
async def add_to_scene_gallery(scene_id: str, request: dict, current_user: dict = Depends(get_current_user)):
    """Save a generated image to a scene's folder/gallery"""
    scene = await db.pro_studio_scenes.find_one({"id": scene_id, "user_id": current_user["id"]})
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    image_url = request.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    now = datetime.now(timezone.utc).isoformat()
    gallery_item = {
        "id": str(uuid.uuid4()),
        "scene_id": scene_id,
        "user_id": current_user["id"],
        "image_url": image_url,
        "prompt": request.get("prompt", ""),
        "type": request.get("type", "generated"),
        "character_id": request.get("character_id"),
        "created_at": now
    }
    
    await db.scene_gallery.insert_one(gallery_item)
    gallery_item.pop("_id", None)
    
    return {"success": True, "item": gallery_item}

@api_router.delete("/pro-studio/scenes/{scene_id}/gallery/{image_id}")
async def delete_from_scene_gallery(scene_id: str, image_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an image from a scene's gallery"""
    result = await db.scene_gallery.delete_one({
        "id": image_id,
        "scene_id": scene_id,
        "user_id": current_user["id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"success": True}

@api_router.post("/pro-studio/scenes/{scene_id}/generate")
async def generate_scene_image(scene_id: str, request: dict, current_user: dict = Depends(get_current_user)):
    """Generate an image using the scene's style and settings"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    scene = await db.pro_studio_scenes.find_one({"id": scene_id, "user_id": current_user["id"]})
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    try:
        additional_prompt = request.get("prompt", "")
        character_id = request.get("character_id")
        
        # Build scene prompt
        style_info = next((s for s in CHARACTER_STYLES if s["id"] == scene.get("style")), {"name": "illustration"})
        lighting_info = next((lit for lit in LIGHTING_OPTIONS if lit["id"] == scene.get("lighting")), {"name": ""})
        mood_info = next((m for m in MOOD_OPTIONS if m["id"] == scene.get("mood")), {"name": ""})
        
        prompt_parts = [scene.get("description_prompt", "")]
        if additional_prompt:
            prompt_parts.insert(0, additional_prompt)
        prompt_parts.extend([
            f"{style_info.get('name', '')} style",
            f"{lighting_info.get('name', '')} lighting" if lighting_info.get('name') else "",
            f"{mood_info.get('name', '')} mood" if mood_info.get('name') else "",
            scene.get("time_of_day", ""),
            scene.get("weather", ""),
            "detailed background, scenic"
        ])
        
        # If a character is specified, add character to the scene
        if character_id:
            character = await db.pro_studio_characters.find_one(
                {"id": character_id, "user_id": current_user["id"]}
            )
            if character:
                prompt_parts.insert(0, f"{character.get('description_prompt', character['name'])}, ")
        
        full_prompt = ", ".join([p for p in prompt_parts if p])
        
        # Generate image
        if FAL_AVAILABLE:
            result = await generate_image_flux(
                prompt=full_prompt,
                model="flux-dev",
                image_size=request.get("image_size", "landscape_16_9"),
                num_images=1
            )
            if result.get("images"):
                return {"success": True, "image_url": result["images"][0].get("url"), "prompt": full_prompt}
        
        # Fallback to OpenAI
        if EMERGENT_LLM_KEY:
            image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
            images = await image_gen.generate_images(prompt=full_prompt, model="gpt-image-1", number_of_images=1)
            if images:
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                return {"success": True, "image_url": f"data:image/png;base64,{image_base64}", "prompt": full_prompt}
        
        raise HTTPException(status_code=500, detail="No generation method available")
        
    except Exception as e:
        logger.error(f"Scene generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/pro-studio/generate-image")
async def pro_studio_generate_image(request: ProStudioImageRequest, current_user: dict = Depends(get_current_user)):
    """Generate a hero frame with Cinema Studio settings"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    try:
        # Build full prompt with cinema settings
        prompt_parts = [request.prompt]
        
        # Add character description if provided
        if request.character_id:
            character = await db.pro_studio_characters.find_one(
                {"id": request.character_id, "user_id": current_user["id"]},
                {"_id": 0}
            )
            if character and character.get("description"):
                prompt_parts.insert(0, character["description"])
        
        # Add camera settings
        camera_desc = CAMERA_CONFIGS.get(request.camera, "")
        if camera_desc:
            prompt_parts.append(camera_desc)
        
        # Add lens settings
        lens_desc = LENS_CONFIGS.get(request.lens, "")
        if lens_desc:
            prompt_parts.append(f"{lens_desc}, {request.focal_length}")
        
        # Add lighting
        lighting_desc = LIGHTING_CONFIGS.get(request.lighting, "")
        if lighting_desc:
            prompt_parts.append(lighting_desc)
        
        # Add quality enhancers
        prompt_parts.append("professional photography, 8K resolution, masterfully composed")
        
        full_prompt = ", ".join(prompt_parts)
        
        # Determine size based on aspect ratio
        aspect_sizes = {
            "1:1": "1024x1024",
            "16:9": "1536x1024",
            "9:16": "1024x1536",
            "4:3": "1024x768",
            "3:4": "768x1024",
            "21:9": "1536x640",
            "2:3": "683x1024"
        }
        size = aspect_sizes.get(request.aspect_ratio, "1024x1024")
        
        # Generate image
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            image_url = f"data:image/png;base64,{image_base64}"
            return {"image_url": image_url, "success": True}
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
            
    except Exception as e:
        logger.error(f"Error generating pro studio image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

class GenerateVariantRequest(BaseModel):
    source_image: str
    prompt: str
    camera: Optional[str] = None
    lens: Optional[str] = None
    focal_length: Optional[str] = None
    lighting: Optional[str] = None
    aspect_ratio: Optional[str] = "16:9"
    strength: Optional[float] = 0.7  # How much to keep from original (0-1)

@api_router.post("/pro-studio/generate-variant")
async def generate_variant(request: GenerateVariantRequest, current_user: dict = Depends(get_current_user)):
    """Generate a variant of an existing image with new cinema settings"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    # Deduct credits
    if not await deduct_credits(current_user["id"], "pulid_generate"):
        credits_needed = CREDIT_COSTS.get("pulid_generate", 3)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Variant generation requires {credits_needed} credits.")
    
    try:
        from emergentintegrations.llm.openai import LlmChat, UserMessage, ImageContent
        
        # First, analyze the source image to get a description
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"variant-{current_user['id']}-{str(uuid.uuid4())[:8]}",
            system_message="You are an expert at analyzing images. Describe subjects precisely for regeneration."
        ).with_model("openai", "gpt-4o")
        
        # Handle source image
        source_image = request.source_image
        if source_image.startswith('http://') or source_image.startswith('https://'):
            async with aiohttp.ClientSession() as session:
                async with session.get(source_image) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    else:
                        raise Exception("Failed to download source image")
        elif source_image.startswith('data:'):
            image_base64 = source_image.split(',')[1] if ',' in source_image else source_image
        else:
            image_base64 = source_image
        
        # Analyze the image
        user_msg = UserMessage(
            text="Describe this image in detail. Include: subjects, setting, colors, mood, composition. Be specific and detailed.",
            file_contents=[ImageContent(image_base64=image_base64)]
        )
        analysis = await chat.send_message(user_msg)
        image_description = analysis.strip() if isinstance(analysis, str) else str(analysis)
        
        # Build full prompt with cinema settings
        prompt_parts = [image_description, request.prompt]
        
        # Add camera settings
        camera_desc = CAMERA_CONFIGS.get(request.camera, "")
        if camera_desc:
            prompt_parts.append(camera_desc)
        
        # Add lens settings
        lens_desc = LENS_CONFIGS.get(request.lens, "")
        if lens_desc:
            prompt_parts.append(f"{lens_desc}, {request.focal_length}")
        
        # Add lighting
        lighting_desc = LIGHTING_CONFIGS.get(request.lighting, "")
        if lighting_desc:
            prompt_parts.append(lighting_desc)
        
        # Add quality enhancers
        prompt_parts.append("professional photography, 8K resolution, masterfully composed")
        
        full_prompt = ", ".join(filter(None, prompt_parts))
        
        # Determine size based on aspect ratio
        aspect_sizes = {
            "1:1": "1024x1024",
            "16:9": "1536x1024",
            "9:16": "1024x1536",
            "4:3": "1024x768",
            "3:4": "768x1024",
            "21:9": "1536x640",
            "2:3": "683x1024"
        }
        size = aspect_sizes.get(request.aspect_ratio, "1024x1024")
        
        # Generate new image
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            image_url = f"data:image/png;base64,{image_base64}"
            return {"image_url": image_url, "success": True, "prompt_used": full_prompt}
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating variant: {error_msg}")
        if check_budget_error(error_msg):
            raise get_budget_error_response()
        raise HTTPException(status_code=500, detail=f"Error generating variant: {error_msg}")

@api_router.post("/pro-studio/generate-shots")
async def generate_shots(request: GenerateShotsRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Generate 9 different angle shots from one source image - returns task_id for polling"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    # Deduct credits first
    if not await deduct_credits(current_user["id"], "shots_generate"):
        credits_needed = CREDIT_COSTS.get("shots_generate", 5)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Shots generation requires {credits_needed} credits. Please purchase more credits.")
    
    # Create task and return immediately
    task_id = str(uuid.uuid4())
    TASK_STORE[task_id] = {
        "status": "pending",
        "user_id": current_user["id"],
        "type": "shots",
        "created_at": datetime.now(timezone.utc),
        "progress": 0,
        "result": None,
        "error": None
    }
    
    logger.info(f"Shots generation task {task_id} created for user {current_user['id']}")
    
    # Start background task
    background_tasks.add_task(
        run_shots_generation_task,
        task_id,
        current_user["id"],
        request.source_image,
        request.character_id
    )
    
    # Return task ID immediately (HTTP 202 Accepted)
    return {"task_id": task_id, "status": "pending", "message": "Shots generation started. Poll /api/tasks/{task_id} for status."}

@api_router.post("/pro-studio/generate-expression")
async def generate_expression(request: GenerateExpressionRequest, current_user: dict = Depends(get_current_user)):
    """Generate character with a specific expression"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    try:
        # Get character
        character = await db.pro_studio_characters.find_one(
            {"id": request.character_id, "user_id": current_user["id"]},
            {"_id": 0}
        )
        
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Build prompt with expression
        expression_desc = EXPRESSION_PROMPTS.get(request.expression, "neutral expression")
        
        prompt_parts = [
            character.get("description", f"Portrait of {character['name']}"),
            expression_desc,
            request.base_prompt if request.base_prompt else "",
            "professional portrait photography, high quality, consistent appearance"
        ]
        
        full_prompt = ", ".join(filter(None, prompt_parts))
        
        # Generate image
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            image_url = f"data:image/png;base64,{image_base64}"
            return {"image_url": image_url, "success": True, "expression": request.expression}
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
            
    except Exception as e:
        logger.error(f"Error generating expression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating expression: {str(e)}")

@api_router.post("/pro-studio/animate-hero")
async def animate_hero_frame(request: AnimateHeroRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Animate a hero frame to video using fal.ai Kling - returns task_id for polling"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    # Credits check for video generation
    if not await deduct_credits(current_user["id"], "video_generate"):
        credits_needed = CREDIT_COSTS.get("video_generate", 10)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Video generation requires {credits_needed} credits.")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="Video generation service not available (fal.ai not configured)")
    
    # Create task and return immediately
    task_id = str(uuid.uuid4())
    TASK_STORE[task_id] = {
        "status": "pending",
        "user_id": current_user["id"],
        "type": "video",
        "created_at": datetime.now(timezone.utc),
        "progress": 0,
        "result": None,
        "error": None
    }
    
    logger.info(f"Video generation task {task_id} created for user {current_user['id']}")
    
    # Start background task
    background_tasks.add_task(
        run_video_generation_task,
        task_id,
        current_user["id"],
        request.image_url,
        request.motion_prompt,
        request.duration
    )
    
    return {"task_id": task_id, "status": "pending", "message": "Video generation started. Poll /api/tasks/{task_id} for status."}

async def run_video_generation_task(task_id: str, user_id: str, image_url: str, motion_prompt: str, duration: int):
    """Background task to generate video with Kling"""
    try:
        TASK_STORE[task_id]["status"] = "processing"
        TASK_STORE[task_id]["progress"] = 10
        
        logger.info(f"Task {task_id}: Starting Kling video generation")
        
        result = await generate_video_from_image(
            image_url=image_url,
            prompt=motion_prompt or "gentle breathing, subtle natural movement, soft hair motion",
            duration=min(duration, 10),
            aspect_ratio="16:9",
            model="kling"
        )
        
        TASK_STORE[task_id]["progress"] = 90
        
        if result.get("success") and result.get("video_url"):
            TASK_STORE[task_id]["status"] = "completed"
            TASK_STORE[task_id]["result"] = {
                "video_url": result["video_url"],
                "model": "kling"
            }
            TASK_STORE[task_id]["progress"] = 100
            logger.info(f"Task {task_id}: Video generation completed")
        else:
            TASK_STORE[task_id]["status"] = "failed"
            TASK_STORE[task_id]["error"] = "No video URL returned"
            logger.error(f"Task {task_id}: No video URL returned")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task {task_id}: Video generation failed: {error_msg}")
        TASK_STORE[task_id]["status"] = "failed"
        TASK_STORE[task_id]["error"] = f"Video generation failed: {error_msg}"

# ==================== FAL.AI CHARACTER CONSISTENCY ENDPOINTS ====================

@api_router.get("/fal/models")
async def get_fal_available_models():
    """Get list of available fal.ai models"""
    if not FAL_AVAILABLE:
        return {"models": [], "available": False, "message": "fal.ai not configured"}
    return {"models": get_fal_models(), "available": True}

@api_router.post("/fal/generate")
async def fal_generate_image(request: FalGenerateImageRequest, current_user: dict = Depends(get_current_user)):
    """Generate image using fal.ai FLUX models"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="fal.ai service not available")
    
    # Credits check for Pro Studio operations
    operation = "flux_pro_generate" if request.model == "flux-pro" else "flux_generate"
    if not await deduct_credits(current_user["id"], operation):
        credits_needed = CREDIT_COSTS.get(operation, 1)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. This operation requires {credits_needed} credits.")
    
    try:
        result = await generate_image_flux(
            prompt=request.prompt,
            model=request.model,
            image_size=request.image_size,
            num_images=request.num_images,
            seed=request.seed
        )
        return result
    except Exception as e:
        logger.error(f"fal.ai generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/fal/generate-with-face")
async def fal_generate_with_face(request: FalGenerateWithFaceRequest, current_user: dict = Depends(get_current_user)):
    """Generate image while preserving face identity using PuLID
    
    This is the key endpoint for consistent character generation.
    It takes a reference face image and generates new images
    that maintain the same facial identity.
    """
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="fal.ai service not available")
    
    # Credits check for PuLID face preservation
    if not await deduct_credits(current_user["id"], "pulid_generate"):
        credits_needed = CREDIT_COSTS.get("pulid_generate", 3)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. This operation requires {credits_needed} credits.")
    
    try:
        result = await generate_with_face_id(
            prompt=request.prompt,
            reference_image_url=request.reference_image,
            id_weight=request.id_weight,
            image_size=request.image_size,
            seed=request.seed
        )
        return result
    except Exception as e:
        logger.error(f"fal.ai face ID generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/fal/train-lora")
async def fal_train_character_lora(request: FalTrainLoraRequest, current_user: dict = Depends(get_current_user)):
    """Train a custom LoRA model for consistent character generation
    
    This creates a persistent model that can generate the same
    character consistently across unlimited images.
    Training takes 5-15 minutes.
    """
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="fal.ai service not available")
    
    if len(request.reference_images) < 3:
        raise HTTPException(status_code=400, detail="At least 3 reference images required")
    
    # Credits check for LoRA training (expensive operation)
    if not await deduct_credits(current_user["id"], "lora_training"):
        credits_needed = CREDIT_COSTS.get("lora_training", 50)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. LoRA training requires {credits_needed} credits.")
    
    try:
        result = await train_character_lora(
            character_name=request.character_name,
            reference_images=request.reference_images,
            trigger_word=request.trigger_word,
            steps=request.steps
        )
        
        # Store the training job in the character record
        char_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Create or update character with training info
        await db.pro_studio_characters.update_one(
            {"user_id": current_user["id"], "name": request.character_name},
            {
                "$set": {
                    "lora_training_job_id": result.get("job_id"),
                    "lora_trigger_word": result.get("trigger_word"),
                    "lora_status": "training",
                    "lora_started_at": now
                }
            },
            upsert=False
        )
        
        return result
    except Exception as e:
        logger.error(f"fal.ai LoRA training error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/fal/training-status/{job_id}")
async def fal_check_training_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Check the status of a LoRA training job"""
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="fal.ai service not available")
    
    try:
        result = await check_training_status(job_id)
        
        # If training completed, update the character record
        if result.get("status") == "completed" and result.get("lora_url"):
            await db.pro_studio_characters.update_one(
                {"user_id": current_user["id"], "lora_training_job_id": job_id},
                {
                    "$set": {
                        "lora_url": result.get("lora_url"),
                        "lora_config_url": result.get("config_url"),
                        "lora_status": "completed",
                        "lora_completed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        elif result.get("status") == "failed":
            await db.pro_studio_characters.update_one(
                {"user_id": current_user["id"], "lora_training_job_id": job_id},
                {"$set": {"lora_status": "failed"}}
            )
        
        return result
    except Exception as e:
        logger.error(f"fal.ai training status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/fal/generate-with-lora")
async def fal_generate_with_lora(request: FalGenerateWithLoraRequest, current_user: dict = Depends(get_current_user)):
    """Generate image using a trained character LoRA
    
    This produces highly consistent character images once
    the LoRA has been trained.
    """
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="fal.ai service not available")
    
    try:
        result = await generate_with_lora(
            prompt=request.prompt,
            lora_url=request.lora_url,
            trigger_word=request.trigger_word,
            lora_scale=request.lora_scale,
            image_size=request.image_size,
            seed=request.seed
        )
        return result
    except Exception as e:
        logger.error(f"fal.ai LoRA generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/pro-studio/characters/train-consistency")
async def train_character_consistency(character_id: str, current_user: dict = Depends(get_current_user)):
    """Start LoRA training for an existing character
    
    This takes a character's reference images and trains
    a custom LoRA model for highly consistent generation.
    """
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="fal.ai service not available")
    
    # Get the character
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if not character.get("reference_images") or len(character.get("reference_images", [])) < 3:
        raise HTTPException(status_code=400, detail="Character needs at least 3 reference images")
    
    # Check if already training or has LoRA
    if character.get("lora_status") == "training":
        return {
            "status": "already_training",
            "job_id": character.get("lora_training_job_id"),
            "message": "LoRA training already in progress"
        }
    
    try:
        result = await train_character_lora(
            character_name=character["name"],
            reference_images=character["reference_images"],
            trigger_word=character["name"].lower().replace(" ", "_"),
            steps=1000
        )
        
        # Update character with training info
        await db.pro_studio_characters.update_one(
            {"id": character_id},
            {
                "$set": {
                    "lora_training_job_id": result.get("job_id"),
                    "lora_trigger_word": result.get("trigger_word"),
                    "lora_status": "training",
                    "lora_started_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            **result,
            "character_id": character_id,
            "character_name": character["name"]
        }
    except Exception as e:
        logger.error(f"Character LoRA training error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/pro-studio/characters/{character_id}/generate-consistent")
async def generate_consistent_character_image(
    character_id: str,
    prompt: str = Form(...),
    image_size: str = Form("landscape_16_9"),
    seed: Optional[int] = Form(None),
    scene_id: Optional[str] = Form(None),
    id_strength: str = Form("high"),  # "high", "medium", "low" - face similarity strength
    current_user: dict = Depends(get_current_user)
):
    """Generate a consistent image of a character, optionally in a scene
    
    Uses the best available method:
    1. Trained LoRA (most consistent) - if available
    2. PuLID face ID - if LoRA not trained
    3. Prompt-based - fallback
    
    Args:
        character_id: The character to generate
        prompt: Action/pose description (e.g., "running through forest", "standing heroically")
        scene_id: Optional scene to place character in
        id_strength: Face similarity - "high" (strict match), "medium", "low" (more artistic)
    """
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    # Get the character
    character = await db.pro_studio_characters.find_one({
        "id": character_id,
        "user_id": current_user["id"]
    })
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get scene if specified
    scene_context = ""
    if scene_id:
        scene = await db.pro_studio_scenes.find_one({
            "id": scene_id,
            "user_id": current_user["id"]
        })
        if scene:
            scene_context = f"Setting: {scene.get('description', '')}. Environment: {scene.get('location_type', '')} with {scene.get('lighting', 'natural')} lighting, {scene.get('mood', '')} mood, {scene.get('time_of_day', 'day')} time, {scene.get('weather', 'clear')} weather."
    
    try:
        # Determine which method will be used and charge appropriate credits
        if FAL_AVAILABLE and character.get("lora_status") == "completed" and character.get("lora_url"):
            credit_operation = "lora_generate"
        elif FAL_AVAILABLE and character.get("reference_images"):
            credit_operation = "pulid_generate"
        else:
            credit_operation = "flux_generate"
        
        # Deduct credits
        if not await deduct_credits(current_user["id"], credit_operation):
            credits_needed = CREDIT_COSTS.get(credit_operation, 2)
            raise HTTPException(status_code=402, detail=f"Insufficient credits. This operation requires {credits_needed} credits.")
        
        # Method 1: Use trained LoRA (best consistency)
        if FAL_AVAILABLE and character.get("lora_status") == "completed" and character.get("lora_url"):
            logger.info(f"Generating with LoRA for character {character['name']}")
            
            # Include character style in the prompt for style consistency
            style_desc = character.get('style', 'illustration')
            genre_desc = character.get('genre', 'fantasy')
            
            # Build prompt with style information
            styled_prompt = f"{prompt}, {style_desc} style, {genre_desc} genre, high quality"
            
            result = await generate_with_lora(
                prompt=styled_prompt,
                lora_url=character["lora_url"],
                trigger_word=character.get("lora_trigger_word", character["name"].lower()),
                lora_scale=1.0,
                image_size=image_size,
                seed=seed
            )
            return {
                **result,
                "method": "lora",
                "character_id": character_id,
                "style_used": style_desc
            }
        
        # Method 2: Use PuLID face ID
        if FAL_AVAILABLE and character.get("reference_images"):
            logger.info(f"Generating with PuLID for character {character['name']}")
            # Get first reference image (should be best quality face shot)
            ref_image = character["reference_images"][0]
            
            # Get character attributes for the prompt
            char_name = character.get('name', 'character')
            style_desc = character.get('style', 'illustration')
            genre_desc = character.get('genre', 'fantasy')
            
            # Build character appearance string from stored traits
            physical_traits = character.get('physical_traits', {})
            appearance_parts = []
            if physical_traits.get('hair_color'):
                appearance_parts.append(f"{physical_traits['hair_color']} hair")
            if physical_traits.get('hair_style'):
                appearance_parts.append(f"{physical_traits['hair_style']}")
            if physical_traits.get('eye_color'):
                appearance_parts.append(f"{physical_traits['eye_color']} eyes")
            if physical_traits.get('skin_tone'):
                appearance_parts.append(f"{physical_traits['skin_tone']} skin")
            if character.get('special_features'):
                appearance_parts.append(character['special_features'])
            
            # Use stored description if no physical traits
            if not appearance_parts and character.get('description'):
                appearance_parts.append(character['description'][:200])
            
            character_appearance = ", ".join(appearance_parts) if appearance_parts else None
            
            # Map id_strength to actual weight values (max is 1.0)
            id_weight_map = {
                "high": 1.0,    # Maximum face similarity
                "medium": 0.8,  # Balanced (increased from 0.7)
                "low": 0.5      # More artistic freedom (increased from 0.4)
            }
            id_weight = id_weight_map.get(id_strength, 1.0)
            
            # Build a focused prompt for PuLID
            if scene_context:
                # Character in a scene
                full_prompt = f"A person {prompt}. {scene_context}"
            else:
                # Character action/pose without specific scene
                full_prompt = f"A person {prompt}, full body shot showing the scene and environment"
            
            result = await generate_with_face_id(
                prompt=full_prompt,
                reference_image_url=ref_image,
                id_weight=id_weight,
                image_size=image_size,
                seed=seed,
                mode="fidelity" if id_strength == "high" else "style",
                character_appearance=character_appearance,
                art_style=f"{style_desc}, {genre_desc} genre"
            )
            return {
                **result,
                "method": "pulid",
                "character_id": character_id,
                "style_used": style_desc,
                "scene_id": scene_id,
                "id_strength": id_strength,
                "appearance_enforced": character_appearance
            }
        
        # Method 3: Fallback to OpenAI with character description
        if EMERGENT_LLM_KEY:
            char_name = character['name']
            logger.info(f"Generating with OpenAI for character {char_name}")
            char_description = character.get('description', f'Portrait of {char_name}')
            full_prompt = f"{char_description} {prompt}"
            image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            
            if images and len(images) > 0:
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                return {
                    "success": True,
                    "images": [{"url": f"data:image/png;base64,{image_base64}"}],
                    "method": "openai",
                    "character_id": character_id
                }
        
        raise HTTPException(status_code=500, detail="No generation method available")
        
    except Exception as e:
        logger.error(f"Consistent character generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== END FAL.AI ENDPOINTS ====================


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


class AzoraLibrarianRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None
    context: Optional[str] = ""
    chat_history: List[dict] = []


@api_router.post("/ai/azora")
async def azora_librarian(request: AzoraLibrarianRequest):
    """Azora - AI Librarian for the 3D Library"""
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        default_system_prompt = """You are Azora, a friendly and magical AI librarian assistant in a beautiful digital library called Azories. You are a young witch with magical powers who loves books. You are designed to help children and young readers.

Your personality:
- Warm, encouraging, and slightly whimsical
- You speak simply but not in a condescending way
- You love books and get excited when recommending them
- You use occasional gentle emojis (✨📚🌟)

Your capabilities:
- Help users find books based on their interests
- Describe any book in the library
- Answer questions about stories, characters, or themes
- Suggest books similar to ones they've enjoyed
- Make reading feel like a magical adventure

Rules:
- Keep responses concise (2-3 sentences usually)
- Be helpful and positive
- Never give inappropriate content
- Encourage reading and imagination"""
        
        system_prompt = request.system_prompt or default_system_prompt
        
        # Create the chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"azora-{str(uuid.uuid4())[:8]}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o-mini")
        
        # Add context if provided
        full_message = request.message
        if request.context:
            full_message = f"Context: {request.context}\n\nUser question: {request.message}"
        
        # Send the question
        response = await chat.send_message(UserMessage(text=full_message))
        
        return {"response": response.strip()}
        
    except Exception as e:
        logger.error(f"Error in Azora Librarian: {str(e)}")
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
    """Generate TTS audio using OpenAI TTS (via Emergent LLM Key)"""
    try:
        emergent_key = os.environ.get("EMERGENT_LLM_KEY")
        if not emergent_key:
            raise HTTPException(status_code=500, detail="TTS service not configured")
        
        # Map ElevenLabs voice IDs to OpenAI voices
        voice_mapping = {
            "21m00Tcm4TlvDq8ikWAM": "nova",      # Rachel -> nova (warm, friendly)
            "AZnzlk1XvdvUeBnXmlld": "shimmer",   # Domi -> shimmer (bright)
            "EXAVITQu4vr4xnSDxMaL": "alloy",     # Bella -> alloy (neutral)
            "ErXwobaYiN019PkySvjV": "onyx",      # Antoni -> onyx (deep)
            "MF3mGyEYCl7XYWbV9V6O": "coral",     # Elli -> coral (warm)
            "TxGEqnHWrfWFTfGW9XjX": "echo",      # Josh -> echo (smooth)
            "VR6AewLTigWG4xSOukaG": "fable",     # Arnold -> fable (expressive)
            "pNInz6obpgDQGcFmaJgB": "sage",      # Adam -> sage (wise)
            "yoZ06aMxZJJ28mfd3POQ": "ash",       # Sam -> ash (clear)
        }
        
        # Get OpenAI voice name (default to nova for storytelling)
        openai_voice = voice_mapping.get(request.voice_id, "nova")
        
        # Initialize OpenAI TTS
        tts = OpenAITextToSpeech(api_key=emergent_key)
        
        # Generate speech as base64
        audio_base64 = await tts.generate_speech_base64(
            text=request.text,
            model="tts-1",  # Use standard for faster response
            voice=openai_voice,
            response_format="mp3"
        )
        
        return {"audio_base64": audio_base64, "success": True}
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

# ============ SPEECH TO TEXT (WHISPER) ============

@api_router.post("/speech-to-text")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "en",
    current_user: dict = Depends(get_current_user)
):
    """
    Transcribe audio to text using OpenAI Whisper.
    Used for voice narration feature in book editor.
    Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm (max 25MB)
    """
    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        
        emergent_key = os.environ.get("EMERGENT_LLM_KEY")
        if not emergent_key:
            raise HTTPException(status_code=500, detail="Speech-to-text service not configured")
        
        # Check file size (25MB limit)
        contents = await file.read()
        if len(contents) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio file too large. Maximum size is 25MB.")
        
        # Check file type
        valid_types = ["audio/mp3", "audio/mp4", "audio/mpeg", "audio/mpga", "audio/m4a", "audio/wav", "audio/webm", "audio/ogg", "video/webm"]
        if file.content_type and file.content_type not in valid_types:
            # Also accept by extension
            if not any(file.filename.lower().endswith(ext) for ext in ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg']):
                raise HTTPException(status_code=400, detail=f"Unsupported audio format: {file.content_type}")
        
        # Initialize Whisper STT
        stt = OpenAISpeechToText(api_key=emergent_key)
        
        # Create file-like object from bytes
        import io
        audio_file = io.BytesIO(contents)
        audio_file.name = file.filename or "audio.webm"
        
        # Transcribe
        response = await stt.transcribe(
            file=audio_file,
            model="whisper-1",
            language=language,
            response_format="json",
            prompt="This is a story being narrated for a children's book. Transcribe it clearly with proper punctuation."
        )
        
        return {
            "text": response.text,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

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
            page.setdefault("video_url", "")
            page.setdefault("use_video", False)
            page.setdefault("layout_type", "single")
            page.setdefault("image_position_x", 50)
            page.setdefault("image_position_y", 50)
            page.setdefault("image_fit", "cover")
            page.setdefault("font_family", "default")
            page.setdefault("font_size", "medium")
            page.setdefault("text_align", "left")
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
    "wind": "https://soundbible.com/grab.php?id=1810&type=mp3",  # Gentle Wind Blowing
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



# ============ STRIPE PAYMENTS ============

class CreateCheckoutRequest(BaseModel):
    package_id: str
    origin_url: str

class PaymentTransaction(BaseModel):
    id: str
    user_id: str
    user_email: str
    package_id: str
    credits: int
    amount: float
    currency: str
    session_id: str
    status: str
    payment_status: str
    created_at: str
    completed_at: Optional[str] = None

@api_router.get("/payments/packages")
async def get_credit_packages():
    """Get available credit packages"""
    return {
        "packages": CREDIT_PACKAGES,
        "credit_costs": CREDIT_COSTS
    }

@api_router.post("/payments/create-checkout")
async def create_checkout_session(request: CreateCheckoutRequest, http_request: Request, current_user: dict = Depends(get_current_user)):
    """Create a Stripe checkout session for purchasing credits"""
    package = CREDIT_PACKAGES.get(request.package_id)
    if not package:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    # Build URLs from frontend origin
    success_url = f"{request.origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/credits"
    
    # Initialize Stripe
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=float(package["price"]),
        currency=package.get("currency", "gbp"),
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["id"],
            "user_email": current_user.get("email", ""),
            "package_id": request.package_id,
            "credits": str(package["credits"])
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create pending transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_email": current_user.get("email", ""),
        "package_id": request.package_id,
        "credits": package["credits"],
        "amount": package["price"],
        "currency": "gbp",
        "session_id": session.session_id,
        "status": "pending",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, http_request: Request, current_user: dict = Depends(get_current_user)):
    """Check payment status and add credits if successful"""
    # Find the transaction
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Verify user owns this transaction
    if transaction["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # If already completed, return status
    if transaction["payment_status"] == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "credits_added": transaction["credits"],
            "message": "Payment already processed"
        }
    
    # Check with Stripe
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    checkout_status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction status
    now = datetime.now(timezone.utc).isoformat()
    
    if checkout_status.payment_status == "paid":
        # Check if we already processed this (prevent double-crediting)
        existing = await db.payment_transactions.find_one({
            "session_id": session_id,
            "payment_status": "paid"
        })
        
        if not existing:
            # Add credits to user
            user = await db.users.find_one({"id": current_user["id"]})
            current_credits = user.get("credits", 0)
            new_credits = current_credits + transaction["credits"]
            
            await db.users.update_one(
                {"id": current_user["id"]},
                {"$set": {"credits": new_credits}}
            )
            
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "status": "complete",
                    "payment_status": "paid",
                    "completed_at": now
                }}
            )
            
            logger.info(f"Credits added: {transaction['credits']} to user {current_user['email']}")
            
            return {
                "status": "complete",
                "payment_status": "paid",
                "credits_added": transaction["credits"],
                "new_balance": new_credits,
                "message": "Payment successful! Credits added to your account."
            }
        else:
            return {
                "status": "complete",
                "payment_status": "paid",
                "credits_added": transaction["credits"],
                "message": "Payment already processed"
            }
    
    elif checkout_status.status == "expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "expired",
                "payment_status": "expired"
            }}
        )
        return {
            "status": "expired",
            "payment_status": "expired",
            "message": "Payment session expired"
        }
    
    return {
        "status": checkout_status.status,
        "payment_status": checkout_status.payment_status,
        "message": "Payment is being processed"
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            metadata = webhook_response.metadata
            
            # Find and update transaction
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if transaction and transaction.get("payment_status") != "paid":
                user_id = metadata.get("user_id")
                credits = int(metadata.get("credits", 0))
                
                # Add credits
                user = await db.users.find_one({"id": user_id})
                if user:
                    current_credits = user.get("credits", 0)
                    await db.users.update_one(
                        {"id": user_id},
                        {"$set": {"credits": current_credits + credits}}
                    )
                
                # Update transaction
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "complete",
                        "payment_status": "paid",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

# ============ ADMIN ANALYTICS ============

@api_router.get("/admin/analytics")
async def get_admin_analytics(current_user: dict = Depends(get_current_user)):
    """Get admin analytics dashboard data"""
    # Check if user is admin or VIP
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin"
    is_vip = user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin and not is_vip:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # User stats
    total_users = await db.users.count_documents({})
    users_today = await db.users.count_documents({"created_at": {"$gte": today_start.isoformat()}})
    users_this_week = await db.users.count_documents({"created_at": {"$gte": week_ago.isoformat()}})
    
    # Book stats
    total_books = await db.books.count_documents({})
    published_books = await db.books.count_documents({"is_published": True})
    
    # Revenue stats
    total_revenue_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_result = await db.payment_transactions.aggregate(total_revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Revenue this month
    month_revenue_pipeline = [
        {"$match": {"payment_status": "paid", "completed_at": {"$gte": month_ago.isoformat()}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    month_revenue_result = await db.payment_transactions.aggregate(month_revenue_pipeline).to_list(1)
    month_revenue = month_revenue_result[0]["total"] if month_revenue_result else 0
    
    # Credits purchased
    credits_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$credits"}}}
    ]
    credits_result = await db.payment_transactions.aggregate(credits_pipeline).to_list(1)
    total_credits_purchased = credits_result[0]["total"] if credits_result else 0
    
    # VIP usage costs
    vip_cost_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$actual_cost_usd"}}}
    ]
    vip_cost_result = await db.vip_usage.aggregate(vip_cost_pipeline).to_list(1)
    vip_total_cost = vip_cost_result[0]["total"] if vip_cost_result else 0
    
    # Credit usage stats
    credit_usage_pipeline = [
        {"$group": {
            "_id": "$operation",
            "count": {"$sum": 1},
            "total_credits": {"$sum": "$credits_spent"}
        }}
    ]
    usage_by_operation = await db.credit_usage.aggregate(credit_usage_pipeline).to_list(100)
    
    # Recent transactions
    recent_transactions = await db.payment_transactions.find(
        {"payment_status": "paid"},
        {"_id": 0}
    ).sort("completed_at", -1).limit(10).to_list(10)
    
    # Most active users
    active_users_pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_spent": {"$sum": "$credits_spent"}
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": 10}
    ]
    active_users = await db.credit_usage.aggregate(active_users_pipeline).to_list(10)
    
    # Add user details to active users
    for user_stat in active_users:
        user = await db.users.find_one({"id": user_stat["_id"]}, {"_id": 0, "email": 1, "name": 1})
        if user:
            user_stat["email"] = user.get("email", "")
            user_stat["name"] = user.get("name", "")
    
    # Page views (book reads)
    total_reads = await db.reading_progress.count_documents({})
    
    # Book completion rate
    completed_books = await db.reading_progress.count_documents({"completed": True})
    completion_rate = (completed_books / total_reads * 100) if total_reads > 0 else 0
    
    return {
        "users": {
            "total": total_users,
            "today": users_today,
            "this_week": users_this_week
        },
        "books": {
            "total": total_books,
            "published": published_books
        },
        "revenue": {
            "total": total_revenue,
            "this_month": month_revenue,
            "currency": "GBP"
        },
        "credits": {
            "total_purchased": total_credits_purchased,
            "usage_by_operation": usage_by_operation
        },
        "vip_costs": {
            "total_cost_usd": round(vip_total_cost, 2),
            "note": "Cost of VIP user operations"
        },
        "engagement": {
            "total_reads": total_reads,
            "completed_books": completed_books,
            "completion_rate": round(completion_rate, 1)
        },
        "recent_transactions": recent_transactions,
        "active_users": active_users
    }

@api_router.get("/admin/vip-usage")
async def get_vip_usage(current_user: dict = Depends(get_current_user)):
    """Get VIP user usage statistics"""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin"
    is_vip = user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin and not is_vip:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get VIP usage grouped by user
    pipeline = [
        {"$group": {
            "_id": "$user_email",
            "total_operations": {"$sum": 1},
            "total_cost_usd": {"$sum": "$actual_cost_usd"},
            "operations": {"$push": {
                "operation": "$operation",
                "cost": "$actual_cost_usd",
                "timestamp": "$timestamp"
            }}
        }}
    ]
    
    vip_usage = await db.vip_usage.aggregate(pipeline).to_list(100)
    
    # Get recent VIP operations
    recent_ops = await db.vip_usage.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    return {
        "vip_users": VIP_USERS,
        "usage_by_user": vip_usage,
        "recent_operations": recent_ops
    }

# ============ LEGAL PAGES ============

@api_router.get("/legal/terms")
async def get_terms_of_service():
    """Get Terms of Service"""
    return {
        "title": "Terms of Service",
        "last_updated": "2026-02-23",
        "content": """
# Terms of Service

Welcome to Azories! By using our platform, you agree to these terms.

## 1. Service Description
Azories is a digital storytelling platform where users can create, read, and share illustrated books using AI-powered tools.

## 2. User Accounts
- You must be at least 13 years old to create an account
- You are responsible for maintaining the security of your account
- You must provide accurate information when registering

## 3. Content Guidelines
- All content must be appropriate for the selected age rating
- No inappropriate, violent, or harmful content is allowed
- You retain ownership of content you create, but grant us license to display it

## 4. Credits and Payments
- Credits are used for Pro Studio AI features
- Credits are non-refundable once purchased
- Prices are subject to change with notice

## 5. Intellectual Property
- AI-generated content is owned by the user who created it
- You may not use the platform to infringe on others' copyrights

## 6. Termination
We reserve the right to terminate accounts that violate these terms.

## 7. Contact
For questions, contact us at books@azories.com
"""
    }

@api_router.get("/legal/privacy")
async def get_privacy_policy():
    """Get Privacy Policy"""
    return {
        "title": "Privacy Policy",
        "last_updated": "2026-02-23",
        "content": """
# Privacy Policy

Your privacy is important to us. This policy explains how we collect, use, and protect your information.

## 1. Information We Collect
- Account information (email, name)
- Content you create (books, images)
- Usage data (pages viewed, features used)
- Payment information (processed securely via Stripe)

## 2. How We Use Your Information
- To provide and improve our services
- To process payments
- To communicate with you about your account
- To analyze usage patterns and improve the platform

## 3. Data Storage
- Your data is stored securely on our servers
- We use industry-standard encryption
- We do not sell your personal information

## 4. Cookies
We use cookies to:
- Keep you logged in
- Remember your preferences
- Analyze site traffic

## 5. Third-Party Services
We use:
- Stripe for payments
- fal.ai for image generation
- OpenAI for text and video generation

## 6. Your Rights
You can:
- Access your data
- Request deletion of your account
- Opt out of marketing communications

## 7. Contact
For privacy concerns, contact us at books@azories.com
"""
    }

@api_router.post("/contact")
async def submit_contact_form(
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...)
):
    """Submit a contact form message"""
    contact = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contact_messages.insert_one(contact)
    
    return {
        "success": True,
        "message": "Thank you for your message! We'll get back to you soon."
    }

@api_router.get("/admin/contact-messages")
async def get_contact_messages(current_user: dict = Depends(get_current_user)):
    """Get contact form messages (admin only)"""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin"
    is_vip = user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin and not is_vip:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    messages = await db.contact_messages.find({}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return {"messages": messages}


# ============ ROOT ============

@api_router.get("/")
async def root():
    return {"message": "Welcome to Azories API", "version": "1.1.0"}

# ==================== ART STUDIO ENDPOINTS ====================

class ArtStudioGenerateRequest(BaseModel):
    prompt: str
    negativePrompt: Optional[str] = None  # Things to avoid in generation
    style: str = "fantasy"
    type: str = "character"  # character, scene, or workflow
    characterData: Optional[dict] = None
    sceneData: Optional[dict] = None
    referenceImage: Optional[str] = None  # Legacy: single reference image
    styleReferenceImage: Optional[str] = None  # For art style/look and feel
    characterReferenceImage: Optional[str] = None  # For character appearance consistency
    bookId: Optional[str] = None  # Book to assign the image to
    workflowName: Optional[str] = None  # Name of workflow if from Expert Mode
    transparentBackground: Optional[bool] = False  # Generate with transparent background
    aspectRatio: Optional[str] = "1:1"  # 1:1, 16:9, 9:16, 4:3, 3:4
    qualityLevel: Optional[str] = "high"  # low, medium, high, ultra
    quality: Optional[str] = "high"  # Alias for qualityLevel
    customStyleDescription: Optional[str] = None  # User's custom style text
    lightingPreset: Optional[str] = "natural"  # natural, neon-pink-blue, golden-hour, dramatic, soft-glow, studio
    expertMode: Optional[bool] = False  # Expert/Node mode flag for enhanced generation

class ArtStudioSaveRequest(BaseModel):
    image_url: str
    name: str = "Untitled"
    type: str = "character"
    style: str = "fantasy"
    characterData: Optional[dict] = None
    sceneData: Optional[dict] = None
    bookId: Optional[str] = None  # Book to assign the image to

class CharacterProfileRequest(BaseModel):
    name: str
    description: str  # Detailed character description
    reference_images: List[str] = []  # List of base64 or URL images
    traits: Optional[dict] = None  # Character traits (gender, age, hair, etc.)
    style_preferences: Optional[List[str]] = None  # Preferred art styles
    seed: Optional[int] = None  # Generation seed for consistency
    book_id: Optional[str] = None  # Associated book

# Character Profile Endpoints for Consistency
@api_router.post("/art-studio/character-profiles")
async def create_character_profile(request: CharacterProfileRequest, current_user: dict = Depends(get_current_user)):
    """Create a character profile for consistent generation"""
    user = current_user
    
    try:
        import random
        
        # Generate a unique seed if not provided
        seed = request.seed if request.seed else random.randint(1, 2147483647)
        
        profile = {
            "user_id": user["id"],
            "name": request.name,
            "description": request.description,
            "reference_images": request.reference_images[:5],  # Max 5 reference images
            "traits": request.traits or {},
            "style_preferences": request.style_preferences or [],
            "seed": seed,
            "book_id": request.book_id,
            "generation_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        result = await db.character_profiles.insert_one(profile)
        
        return {
            "id": str(result.inserted_id),
            "name": request.name,
            "seed": seed,
            "message": "Character profile created. Use this profile for consistent character generation."
        }
        
    except Exception as e:
        logging.error(f"Character profile creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create character profile")

@api_router.get("/art-studio/character-profiles")
async def get_character_profiles(current_user: dict = Depends(get_current_user)):
    """Get all character profiles for the user"""
    user = current_user
    
    try:
        profiles = await db.character_profiles.find(
            {"user_id": user["id"]},
            {"_id": 0, "user_id": 0}
        ).sort("created_at", -1).to_list(50)
        
        # Add ID back as string
        for idx, profile in enumerate(profiles):
            cursor = db.character_profiles.find({"user_id": user["id"]}).sort("created_at", -1)
            docs = await cursor.to_list(50)
            if idx < len(docs):
                profiles[idx]["id"] = str(docs[idx]["_id"])
        
        return {"profiles": profiles}
        
    except Exception as e:
        logging.error(f"Character profiles fetch error: {e}")
        return {"profiles": []}

@api_router.get("/art-studio/character-profiles/{profile_id}")
async def get_character_profile(profile_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific character profile"""
    user = current_user
    
    try:
        from bson import ObjectId
        profile = await db.character_profiles.find_one(
            {"_id": ObjectId(profile_id), "user_id": user["id"]}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Character profile not found")
        
        return {
            "id": str(profile["_id"]),
            "name": profile["name"],
            "description": profile["description"],
            "reference_images": profile.get("reference_images", []),
            "traits": profile.get("traits", {}),
            "style_preferences": profile.get("style_preferences", []),
            "seed": profile.get("seed"),
            "book_id": profile.get("book_id"),
            "generation_count": profile.get("generation_count", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Character profile fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch character profile")

@api_router.post("/art-studio/generate-consistent")
async def generate_consistent_character(
    profile_id: str,
    prompt: str,
    scene: Optional[str] = None,
    style: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate an image with character consistency using a saved profile"""
    user = current_user
    
    try:
        from bson import ObjectId
        
        # Get the character profile
        profile = await db.character_profiles.find_one(
            {"_id": ObjectId(profile_id), "user_id": user["id"]}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Character profile not found")
        
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        # Build consistency-enhanced prompt
        char_desc = profile["description"]
        traits = profile.get("traits", {})
        
        # Add trait details to description
        trait_parts = []
        if traits.get("gender"):
            trait_parts.append(traits["gender"])
        if traits.get("age"):
            trait_parts.append(f"{traits['age']} years old")
        if traits.get("hairColor"):
            trait_parts.append(f"{traits['hairColor']} hair")
        if traits.get("hairStyle"):
            trait_parts.append(f"{traits['hairStyle']} hairstyle")
        if traits.get("eyeColor"):
            trait_parts.append(f"{traits['eyeColor']} eyes")
        if traits.get("skinTone"):
            trait_parts.append(f"{traits['skinTone']} skin")
        
        traits_desc = ", ".join(trait_parts) if trait_parts else ""
        
        # Build the full prompt with consistency anchors
        full_prompt = f"Character: {profile['name']}. "
        full_prompt += f"Exact appearance: {char_desc}"
        if traits_desc:
            full_prompt += f", {traits_desc}"
        full_prompt += ". "
        
        if scene:
            full_prompt += f"Scene: {scene}. "
        
        full_prompt += f"Action/Pose: {prompt}. "
        
        # Add style
        style_to_use = style or (profile.get("style_preferences", ["fantasy"])[0] if profile.get("style_preferences") else "fantasy")
        style_prompts = {
            "realistic": "Photorealistic style, detailed, cinematic lighting",
            "anime": "Japanese anime style, vibrant colors, clean lines",
            "fantasy": "Epic fantasy art style, magical lighting, detailed",
            "cartoon": "Colorful cartoon style, bold outlines",
            "watercolor": "Watercolor painting style, soft blended colors"
        }
        full_prompt += style_prompts.get(style_to_use, "Epic fantasy art style, detailed")
        
        # Add consistency keywords
        full_prompt += ". IMPORTANT: Maintain exact character appearance, same face structure, same proportions, consistent identity throughout."
        
        # Generate the image
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            image_url = f"data:image/png;base64,{image_base64}"
            
            # Update generation count
            await db.character_profiles.update_one(
                {"_id": ObjectId(profile_id)},
                {
                    "$inc": {"generation_count": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
            
            # Save to generations
            generation_record = {
                "user_id": user["id"],
                "image_url": image_url,
                "prompt": prompt,
                "enhanced_prompt": full_prompt,
                "style": style_to_use,
                "type": "consistent_character",
                "character_profile_id": profile_id,
                "character_name": profile["name"],
                "scene": scene,
                "seed": profile.get("seed"),
                "book_id": profile.get("book_id"),
                "created_at": datetime.now(timezone.utc)
            }
            await db.art_studio_generations.insert_one(generation_record)
            
            return {
                "image_url": image_url,
                "prompt_used": full_prompt,
                "character_name": profile["name"],
                "seed": profile.get("seed")
            }
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Consistent character generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@api_router.post("/art-studio/generate")
async def art_studio_generate(request: ArtStudioGenerateRequest, current_user: dict = Depends(get_current_user)):
    """Generate an image using AI based on character/scene settings - DeepAI quality approach"""
    user = current_user
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        # DEEPAI-STYLE QUALITY ENHANCEMENT SYSTEM
        # Key principles: Detailed descriptors, compositional cues, style-specific boosters
        
        # Style enhancement mapping - ENHANCED for variations and quality
        style_prompts = {
            # SCI-FI & FUTURISTIC STYLES - Stylized digital art for stories
            "scifi-portrait": "highly stylized sci-fi digital portrait, chrome metallic elements on clothing or accessories, flowing silky hair, ethereal atmospheric background, doll-like stylized features, smooth porcelain skin, professional concept art, trending on ArtStation, 8K ultra detailed",
            "stylized-digital": "highly stylized digital art portrait, doll-like features, smooth porcelain skin texture, flowing detailed hair, soft ethereal background, NOT photorealistic, artistic stylization, professional digital painting, elegant composition",
            "concept-portrait": "AAA game concept art portrait, professional character design, stylized yet detailed, cinematic composition, dramatic lighting, trending on ArtStation, industry quality concept art",
            "chrome-aesthetic": "chrome aesthetic portrait, liquid metal elements, reflective chrome surfaces, metallic skin accents, futuristic fashion, smooth stylized features, professional digital art, 8K quality",
            "ethereal-scifi": "ethereal sci-fi portrait, dreamy soft atmosphere, flowing hair with subtle iridescence, smooth stylized skin, delicate features, soft color palette with pink and silver tones, professional digital art, painterly quality",
            "cyberpunk": "cyberpunk neon masterpiece, futuristic dystopian aesthetic, detailed tech elements, Blade Runner quality, neon-lit rain, holographic displays, chrome implants",
            
            # ADVANCED PORTRAIT STYLES - Hyper-detailed digital art
            "neon-portrait": "hyper-detailed digital portrait, dramatic neon pink and blue split lighting, flowing detailed hair with individual strands visible, extremely polished skin, professional digital art, 8K ultra HD, trending on ArtStation, glossy finish, studio quality, cinematic color grading, volumetric lighting, rim light glow",
            "surreal-portrait": "surreal double exposure portrait, fantasy castle in background, dramatic sunset sky reflected in glasses, flowing wavy hair with purple and teal highlights, extremely detailed face, hyper-realistic digital painting, dreamy ethereal atmosphere, 8K ultra HD, trending on ArtStation, masterpiece quality",
            "hyper-digital": "hyper-detailed digital art portrait, extremely polished rendering, every hair strand visible, porcelain skin texture, professional studio lighting, 8K resolution, photorealistic yet stylized, trending on ArtStation, premium digital painting, subsurface scattering, rim lighting",
            "aesthetic-portrait": "aesthetic portrait, soft pastel color grading, trendy e-girl/e-boy aesthetic, soft glow effect, detailed flowing hair, smooth skin, professional digital art, dreamy atmosphere, 8K quality, Instagram aesthetic, soft bokeh background",
            "fantasy-portrait": "fantasy portrait, magical ethereal lighting, flowing detailed hair with fantasy colors, luminous skin, otherworldly beauty, extremely detailed eyes with reflections, professional fantasy art, 8K HD, trending on ArtStation, volumetric god rays",
            "dramatic-glamour": "high fashion glamour portrait, dramatic studio lighting, extreme detail, magazine cover quality, professional photography aesthetic, sharp focus, bokeh background, 8K resolution, runway model quality, perfect makeup and styling",
            
            # STANDARD STYLES
            "realistic": "ultra photorealistic, hyperdetailed, studio photography, 8K UHD, DSLR quality, sharp focus, depth of field, bokeh background, professional lighting, Ray tracing",
            "anime": "premium anime art, detailed cel shading, Studio Ghibli quality, vibrant saturated colors, clean precise lineart, expressive detailed eyes, anime key visual, trending on Pixiv",
            "cartoon": "premium cartoon illustration, bold clean vector outlines, vibrant saturated colors, Disney/Pixar quality character design, smooth gradients, appealing proportions",
            "watercolor": "masterful traditional watercolor, wet-on-wet technique, soft color blending, visible brushstrokes, artistic texture, gallery quality painting, delicate washes",
            "oil-painting": "museum quality oil painting, rich impasto texture, masterful brushwork, Rembrandt lighting, fine art canvas texture, classical composition",
            "pixel-art": "premium pixel art, clean pixel work, 16-bit aesthetic, detailed sprite work, smooth color gradients, retro game masterpiece",
            "comic": "professional comic book art, dynamic ink linework, bold colors, Marvel/DC quality illustration, action composition, graphic novel style",
            "fantasy": "epic high fantasy digital art, magical atmosphere, cinematic dramatic lighting, extremely detailed, professional concept art, trending on ArtStation, masterwork quality",
            "3d-render": "premium 3D render, photorealistic materials, subsurface scattering, ray traced lighting, Octane/Blender quality, volumetric effects",
            "sketch": "professional pencil sketch, detailed crosshatching, artistic shading, master artist quality, fine art drawing, museum piece",
            "ethereal-fantasy": "ethereal dreamy digital painting, soft luminous glow, mystical atmosphere, flowing ethereal elements, fantasy art masterpiece, magical realism",
            "surreal-dreamscape": "surreal dreamscape masterpiece, impossible geometry, soft ethereal lighting, Salvador Dali inspired, dreamlike quality",
            "luminous-ethereal": "luminous ethereal fantasy, celestial divine quality, cosmic atmosphere, highly polished digital art, volumetric god rays, angelic lighting",
            "celestial-fantasy": "celestial divine fantasy art, cosmic ethereal beauty, nebula starry atmosphere, luminous polished rendering, otherworldly masterpiece",
            "dark-fantasy": "dark gothic fantasy masterpiece, dramatic chiaroscuro lighting, moody atmospheric, detailed dark art, Berserk/Dark Souls quality",
            "steampunk": "steampunk Victorian masterpiece, intricate brass machinery, detailed clockwork mechanisms, premium steampunk illustration, antique quality",
            "concept-art": "professional concept art, industry AAA quality, detailed character design, cinematic composition, trending on ArtStation",
            "storybook": "beautiful children's book illustration, whimsical charming style, warm inviting colors, professional storybook art, enchanting quality",
            "portrait": "professional portrait photography, Hasselblad quality, studio lighting, sharp focus, 8K detail, beautiful composition, bokeh",
            "cinematic": "cinematic movie still, anamorphic lens, dramatic lighting, film grain, professional cinematography, blockbuster quality, 35mm film",
            "disney": "Disney animation quality, charming character design, expressive features, appealing proportions, professional Disney studio style",
            "pixar": "Pixar 3D animation quality, appealing stylized design, professional rendering, subsurface scattering skin, modern 3D animation",
            "manga": "professional manga illustration, detailed dynamic linework, screentone shading, Japanese manga quality, Shonen Jump style",
            "digital-art": "premium digital art, professional illustration, detailed rendering, trending on ArtStation, DeviantArt featured quality",
            "hyperrealistic": "hyperrealistic CGI, extreme photorealistic detail, 8K UHD resolution, skin pore detail, professional quality"
        }
        style_desc = style_prompts.get(request.style, "premium professional illustration, highly detailed, masterwork quality")
        
        # DEEPAI-STYLE QUALITY BOOSTERS
        # These create variation potential and consistent high quality
        QUALITY_TAGS = "masterpiece, best quality, highly detailed, sharp focus, high resolution, professional"
        CHARACTER_QUALITY = "beautiful detailed face, detailed expressive eyes, natural skin texture, perfect anatomy, well-proportioned"
        COMPOSITION_TAGS = "dynamic composition, perfect framing, rule of thirds, visual hierarchy"
        LIGHTING_TAGS = "perfect lighting, professional lighting setup, rim lighting, ambient occlusion"
        
        # STRONG NEGATIVE PROMPTS - DeepAI uses these heavily for clean output
        DEFAULT_NEGATIVE = "blurry, out of focus, low quality, lowres, bad anatomy, bad hands, extra fingers, missing fingers, deformed, disfigured, mutation, mutated, ugly, poorly drawn face, poorly drawn hands, watermark, signature, text, logo, jpeg artifacts, compression artifacts, cropped, worst quality, low quality, normal quality"
        
        # BUILD THE ENHANCED PROMPT - UI SETTINGS FIRST, then style, then written description
        # The user_prompt already contains UI settings first (from buildCharacterPrompt)
        user_prompt = request.prompt.strip()
        
        # Extract character data to emphasize UI settings
        char_data = request.characterData or {}
        clothing_desc = char_data.get('clothing', '')
        
        # Clothing enhancement mapping
        clothing_prompts = {
            'Futuristic': 'wearing sleek futuristic sci-fi attire, chrome metallic elements, high-tech fashion',
            'Sci-Fi': 'wearing advanced sci-fi outfit, futuristic technology elements, space-age fashion',
            'Cyberpunk': 'wearing cyberpunk streetwear, neon accents, tech-wear, futuristic urban fashion',
            'Fantasy': 'wearing elegant fantasy attire, magical aesthetic, ethereal clothing',
            'Medieval': 'wearing medieval period clothing, historical fantasy attire',
            'Victorian': 'wearing Victorian era fashion, elegant period dress',
            'Armor': 'wearing detailed armor, warrior aesthetic, battle-ready',
            'Streetwear': 'wearing modern trendy streetwear, urban fashion, stylish casual'
        }
        clothing_enhancement = clothing_prompts.get(clothing_desc, '')
        
        if request.type == "character":
            # CHARACTER GENERATION: UI settings FIRST, then style
            # Structure: [UI Settings] -> [Clothing Enhancement] -> [Style] -> [Quality]
            if clothing_enhancement:
                enhanced_prompt = f"""{user_prompt}. {clothing_enhancement}. {style_desc}. {CHARACTER_QUALITY}. {QUALITY_TAGS}. {LIGHTING_TAGS}"""
            else:
                enhanced_prompt = f"""{user_prompt}. {style_desc}. {CHARACTER_QUALITY}. {QUALITY_TAGS}. {LIGHTING_TAGS}"""
            
        elif request.type == "scene":
            # Scene generation: Environment details first
            SCENE_QUALITY = "breathtaking environment, immersive atmosphere, depth and scale"
            enhanced_prompt = f"""{user_prompt}. {SCENE_QUALITY}. {style_desc}. {QUALITY_TAGS}. {LIGHTING_TAGS}. cinematic wide shot"""
            
        elif request.type == "workflow":
            # Expert Mode: User prompt is EXACT specification - highest priority
            enhanced_prompt = f"""{user_prompt}. {style_desc}. {QUALITY_TAGS}. {CHARACTER_QUALITY}. {LIGHTING_TAGS}"""
        else:
            enhanced_prompt = f"{user_prompt}. {style_desc}. {QUALITY_TAGS}"
        
        # LIGHTING PRESETS - Add dramatic lighting effects
        lighting_prompts = {
            "natural": "",  # No extra lighting, use style default
            "neon-pink-blue": "dramatic neon lighting, pink and blue split lighting, cyberpunk glow, neon rim light, colored light reflections on skin",
            "golden-hour": "golden hour lighting, warm sunset glow, soft orange light, magical hour photography",
            "dramatic": "dramatic chiaroscuro lighting, strong shadows, high contrast, cinematic spotlight",
            "soft-glow": "soft diffused lighting, ethereal glow, gentle luminescence, dreamy soft light",
            "studio": "professional studio lighting, three-point lighting setup, softbox, clean white background lighting"
        }
        lighting_desc = lighting_prompts.get(request.lightingPreset or "natural", "")
        if lighting_desc:
            enhanced_prompt += f". {lighting_desc}"
        
        # CUSTOM STYLE DESCRIPTION - User can add their own style details
        if request.customStyleDescription:
            enhanced_prompt += f". {request.customStyleDescription}"
        
        # Handle dual reference images for consistency
        if hasattr(request, 'styleReferenceImage') and request.styleReferenceImage:
            enhanced_prompt += ". Match the art style and visual aesthetic of the reference"
        if hasattr(request, 'characterReferenceImage') and request.characterReferenceImage:
            enhanced_prompt += ". Maintain exact same character appearance, same face and features as reference"
        
        # Legacy single reference support
        if request.referenceImage:
            enhanced_prompt += ". Maintain visual consistency with the provided reference"
        
        # Add transparent background instruction if requested
        if request.transparentBackground:
            enhanced_prompt += ". Isolated subject on pure transparent background, PNG cutout, no background elements"
        
        # Combine user's negative prompt with defaults for cleaner output
        final_negative = DEFAULT_NEGATIVE
        if request.negativePrompt:
            final_negative = f"{request.negativePrompt}, {DEFAULT_NEGATIVE}"
        
        # Append negative prompts at end (DALL-E handles these internally)
        enhanced_prompt += f". Negative: {final_negative}"
        
        # Log the prompt for debugging
        logging.info(f"Art Studio Generate - Final prompt: {enhanced_prompt[:500]}...")
        
        # Map aspect ratio to size
        aspect_ratio_sizes = {
            "1:1": "1024x1024",
            "16:9": "1536x1024",   # Landscape wide
            "9:16": "1024x1536",   # Portrait tall
            "4:3": "1024x768",     # Classic landscape (will use 1024x1024 as closest)
            "3:4": "768x1024"      # Classic portrait (will use 1024x1024 as closest)
        }
        # Note: image_size not used currently as emergent library doesn't support size param
        _ = aspect_ratio_sizes.get(request.aspectRatio, "1024x1024")
        
        # Use OpenAI image generation via Emergent
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        # Map quality level to API parameter
        quality_map = {
            'low': 'low',
            'medium': 'low',  # emergent library accepts low/medium/high
            'high': 'low',    # Use low for faster generation, quality is in prompt
            'ultra': 'low'    # Ultra quality achieved through prompt engineering
        }
        api_quality = quality_map.get(request.qualityLevel, 'low')
        
        # Note: Size parameter not supported by emergent library
        # Transparent background is achieved via prompt instructions (already added above)
        
        images = await image_gen.generate_images(
            prompt=enhanced_prompt,
            model="gpt-image-1",
            number_of_images=1,
            quality=api_quality
        )
        
        if images and len(images) > 0:
            # Convert to base64 data URL
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            image_url = f"data:image/png;base64,{image_base64}"
            
            # Save to user's generation history
            generation_record = {
                "user_id": user["id"],
                "image_url": image_url,
                "prompt": request.prompt,
                "enhanced_prompt": enhanced_prompt,
                "negative_prompt": request.negativePrompt,
                "style": request.style,
                "type": request.type,
                "aspect_ratio": request.aspectRatio,
                "quality_level": request.qualityLevel,
                "character_data": request.characterData,
                "scene_data": request.sceneData,
                "book_id": request.bookId,
                "workflow_name": request.workflowName,
                "has_reference": bool(request.referenceImage),
                "transparent_background": request.transparentBackground,
                "created_at": datetime.now(timezone.utc)
            }
            await db.art_studio_generations.insert_one(generation_record)
            
            return {"image_url": image_url, "prompt_used": enhanced_prompt}
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
        
    except Exception as e:
        logging.error(f"Art Studio generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@api_router.post("/art-studio/save")
async def art_studio_save(request: ArtStudioSaveRequest, current_user: dict = Depends(get_current_user)):
    """Save an image to user's gallery"""
    user = current_user
    
    try:
        gallery_item = {
            "user_id": user["id"],
            "image_url": request.image_url,
            "name": request.name,
            "type": request.type,
            "style": request.style,
            "character_data": request.characterData,
            "scene_data": request.sceneData,
            "book_id": request.bookId,
            "created_at": datetime.now(timezone.utc)
        }
        result = await db.art_studio_gallery.insert_one(gallery_item)
        
        return {"success": True, "id": str(result.inserted_id)}
        
    except Exception as e:
        logging.error(f"Art Studio save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save image")

class AnalyzeImageRequest(BaseModel):
    image_url: str
    analysis_type: str = "style"  # "style" or "character"

@api_router.post("/art-studio/analyze-image")
async def analyze_image(request: AnalyzeImageRequest, current_user: dict = Depends(get_current_user)):
    """Analyze an image and extract a prompt that could recreate it"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
        import httpx
        import uuid
        
        # Download image and convert to base64
        async with httpx.AsyncClient() as client:
            img_response = await client.get(request.image_url, timeout=30.0)
            image_bytes = img_response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Initialize the chat with vision model
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=str(uuid.uuid4()),
            system_message="You are an expert image analyst. Provide detailed, accurate descriptions."
        ).with_model("openai", "gpt-4o")
        
        if request.analysis_type == "style":
            analysis_prompt = """Analyze this image and describe its artistic style in detail. 
            Focus on: art style/medium, color palette, lighting style, mood/atmosphere, texture, composition style.
            Output a concise prompt (under 100 words) that captures the visual style that could be used to generate similar images.
            Format: Just the style description, no explanations."""
        else:
            analysis_prompt = """Analyze this character image in detail.
            Focus on: physical appearance, facial features, hair style/color, clothing, pose, expression, distinctive features.
            Output a concise prompt (under 100 words) describing the character that could be used to recreate them.
            Format: Just the character description, no explanations."""
        
        # Create message with image
        image_content = ImageContent(image_base64=image_base64)
        user_message = UserMessage(
            text=analysis_prompt,
            file_contents=[image_content]
        )
        
        # Send and get response
        response = await chat.send_message(user_message)
        extracted_prompt = response.strip() if response else ""
        
        return {"extracted_prompt": extracted_prompt}
        
    except Exception as e:
        logging.error(f"Image analysis error: {e}")
        # Return a fallback description if analysis fails
        return {"extracted_prompt": "", "error": str(e)}

class ConsistentCharacterRequest(BaseModel):
    prompt: str  # What the character should be doing/wearing
    characterReferenceImage: str  # URL or base64 of reference image
    styleReferenceImage: Optional[str] = None  # Optional style reference
    style: str = "fantasy"
    scene: Optional[str] = None
    transparentBackground: bool = False

@api_router.post("/art-studio/generate-with-reference")
async def generate_with_reference(request: ConsistentCharacterRequest, current_user: dict = Depends(get_current_user)):
    """
    IP-Adapter style generation - analyzes reference image and generates consistent character.
    Uses GPT-4V to extract character details, then generates with strong consistency prompts.
    """
    user = current_user
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        import httpx
        import uuid
        import base64 as base64_module
        
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        # Download character reference image
        async with httpx.AsyncClient() as client:
            char_response = await client.get(request.characterReferenceImage, timeout=30.0)
            char_base64 = base64_module.b64encode(char_response.content).decode('utf-8')
        
        # Initialize chat for analysis
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=str(uuid.uuid4()),
            system_message="You are an expert at analyzing images for AI recreation."
        ).with_model("openai", "gpt-4o")
        
        # Step 1: Analyze character reference for detailed description
        char_image = ImageContent(image_base64=char_base64)
        char_message = UserMessage(
            text="""Analyze this character image EXTREMELY thoroughly.
            Describe with EXACT precision:
            - Face shape, exact eye shape and color, nose shape, lip shape
            - Exact hair color (with highlights/lowlights), length, style, texture
            - Skin tone (be specific: pale porcelain, warm tan, deep brown, etc.)
            - Distinctive features (freckles, moles, scars, dimples, etc.)
            - Body type and proportions
            - Current clothing/outfit in detail
            - Expression and pose
            Output as a detailed prompt. Be extremely specific to enable recreation.""",
            file_contents=[char_image]
        )
        char_analysis = await chat.send_message(char_message)
        char_description = char_analysis.strip() if char_analysis else ""
        
        # Step 2: Analyze style reference if provided
        style_description = ""
        if request.styleReferenceImage:
            async with httpx.AsyncClient() as client:
                style_response = await client.get(request.styleReferenceImage, timeout=30.0)
                style_base64 = base64_module.b64encode(style_response.content).decode('utf-8')
            
            style_chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=str(uuid.uuid4()),
                system_message="You are an expert at analyzing artistic styles."
            ).with_model("openai", "gpt-4o")
            
            style_image = ImageContent(image_base64=style_base64)
            style_message = UserMessage(
                text="""Describe this image's artistic style:
                - Art medium/technique (digital painting, watercolor, anime, etc.)
                - Color palette and temperature
                - Lighting style and direction
                - Texture and brush strokes
                - Overall mood/atmosphere
                Output as style tags for image generation.""",
                file_contents=[style_image]
            )
            style_analysis = await style_chat.send_message(style_message)
            style_description = style_analysis.strip() if style_analysis else ""
        
        # Step 3: Build the ultimate consistency prompt
        style_prompts = {
            "realistic": "hyperrealistic, photographic quality, 8K detail",
            "anime": "anime style, vibrant colors, clean linework",
            "fantasy": "fantasy digital art, magical lighting, highly detailed",
            "cartoon": "cartoon illustration style, bold outlines",
            "watercolor": "watercolor painting style, soft blending"
        }
        base_style = style_prompts.get(request.style, "highly detailed, professional illustration")
        
        # Combine everything for maximum consistency
        full_prompt = f"""EXACT CHARACTER RECREATION - MUST MATCH REFERENCE PRECISELY:
        {char_description}
        
        SCENE/ACTION: {request.prompt}
        {f'ENVIRONMENT: {request.scene}' if request.scene else ''}
        
        ART STYLE: {style_description if style_description else base_style}
        
        QUALITY: masterpiece, best quality, ultra detailed, sharp focus, professional lighting,
        beautiful detailed face, detailed eyes, {base_style}
        
        CRITICAL: Maintain EXACT same face, hair, features as reference. Same person, different pose/scene.
        """
        
        if request.transparentBackground:
            full_prompt += " isolated on transparent background, PNG cutout"
        
        full_prompt += " AVOID: different face, wrong hair color, inconsistent features, blurry, low quality"
        
        # Step 4: Generate the image
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=full_prompt.replace('\n', ' ').strip(),
            model="gpt-image-1",
            number_of_images=1,
            quality="low"
        )
        
        if images and len(images) > 0:
            image_base64 = base64_module.b64encode(images[0]).decode('utf-8')
            image_url = f"data:image/png;base64,{image_base64}"
            
            # Save to history
            await db.art_studio_generations.insert_one({
                "user_id": user["id"],
                "image_url": image_url,
                "prompt": request.prompt,
                "character_description": char_description,
                "style_description": style_description,
                "generation_type": "consistent_character",
                "created_at": datetime.now(timezone.utc)
            })
            
            return {
                "image_url": image_url,
                "character_description": char_description,
                "style_description": style_description
            }
        else:
            raise HTTPException(status_code=500, detail="No image generated")
            
    except Exception as e:
        logging.error(f"Consistent character generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@api_router.get("/art-studio/gallery")
async def art_studio_gallery(
    book_id: Optional[str] = None,
    type_filter: Optional[str] = None,  # 'image', 'animation', or None for all
    current_user: dict = Depends(get_current_user)
):
    """Get user's saved gallery items, optionally filtered by book or type"""
    user = current_user
    
    try:
        # Build query
        query = {"user_id": user["id"]}
        if book_id:
            query["book_id"] = book_id
        if type_filter:
            if type_filter == "image":
                query["type"] = {"$ne": "animation"}  # All non-animation types
            elif type_filter == "animation":
                query["type"] = "animation"
        
        cursor = db.art_studio_gallery.find(query).sort("created_at", -1).limit(100)
        
        images = []
        async for item in cursor:
            images.append({
                "_id": str(item["_id"]),
                "id": str(item["_id"]),
                "image_url": item["image_url"],
                "name": item.get("name", "Untitled"),
                "type": item.get("type", "character"),
                "style": item.get("style", "fantasy"),
                "book_id": item.get("book_id"),
                "motion_prompt": item.get("motion_prompt", ""),
                "prompt": item.get("prompt", ""),  # Original generation prompt
                "character_data": item.get("character_data"),
                "scene_data": item.get("scene_data"),
                "source": item.get("source", "art_studio"),  # art_studio or pro_studio
                "created_at": item.get("created_at", datetime.now(timezone.utc)).isoformat()
            })
        
        return {"images": images}
        
    except Exception as e:
        logging.error(f"Art Studio gallery error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load gallery")


@api_router.post("/art-studio/gallery/migrate-sources")
async def migrate_gallery_sources(current_user: dict = Depends(get_current_user)):
    """Migrate gallery items to have correct source based on type"""
    try:
        # Update items with type='character' or type='scene' that have wrong source
        result = await db.art_studio_gallery.update_many(
            {
                "user_id": current_user["id"],
                "$or": [
                    {"type": "character"},
                    {"type": "scene"}
                ],
                "source": {"$ne": "pro_studio"}
            },
            {"$set": {"source": "pro_studio"}}
        )
        
        return {
            "success": True,
            "modified": result.modified_count,
            "message": f"Updated {result.modified_count} items to pro_studio source"
        }
    except Exception as e:
        logging.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail="Migration failed")


@api_router.post("/art-studio/gallery")
async def add_to_art_studio_gallery(request: dict, current_user: dict = Depends(get_current_user)):
    """Save an image to the Art Studio gallery"""
    user = current_user
    
    image_url = request.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    try:
        now = datetime.now(timezone.utc)
        gallery_item = {
            "user_id": user["id"],
            "image_url": image_url,
            "name": request.get("name", request.get("prompt", "Untitled")),
            "prompt": request.get("prompt", ""),
            "type": request.get("type", "image"),
            "style": request.get("style", ""),
            "model": request.get("model", ""),
            "book_id": request.get("book_id"),
            "source": request.get("source", "art_studio"),  # art_studio or pro_studio
            "created_at": now
        }
        
        result = await db.art_studio_gallery.insert_one(gallery_item)
        
        return {
            "success": True,
            "id": str(result.inserted_id),
            "message": "Image saved to gallery"
        }
        
    except Exception as e:
        logging.error(f"Art Studio gallery save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save to gallery")

@api_router.delete("/art-studio/gallery/{image_id}")
async def art_studio_delete(image_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an image from user's gallery"""
    user = current_user
    
    try:
        # Try both id formats
        result = await db.art_studio_gallery.delete_one({
            "id": image_id,
            "user_id": user["id"]
        })
        
        if result.deleted_count == 0:
            # Try with MongoDB ObjectId
            try:
                from bson import ObjectId
                result = await db.art_studio_gallery.delete_one({
                    "_id": ObjectId(image_id),
                    "user_id": user["id"]
                })
            except:
                pass
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"success": True, "message": "Deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Art Studio delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete image")


class GalleryItemUpdate(BaseModel):
    book_id: Optional[str] = None
    name: Optional[str] = None


@api_router.put("/art-studio/gallery/{image_id}")
async def art_studio_update(image_id: str, update: GalleryItemUpdate, current_user: dict = Depends(get_current_user)):
    """Update a gallery item (assign to book, rename, etc.)"""
    user = current_user
    
    try:
        from bson import ObjectId
        
        update_data = {}
        if update.book_id is not None:
            update_data["book_id"] = update.book_id if update.book_id else None
        if update.name is not None:
            update_data["name"] = update.name
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        result = await db.art_studio_gallery.update_one(
            {"_id": ObjectId(image_id), "user_id": user["id"]},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"success": True}
        
    except Exception as e:
        logging.error(f"Art Studio update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update gallery item")


@api_router.get("/art-studio/gallery/book/{book_id}")
async def get_book_gallery(book_id: str, current_user: dict = Depends(get_current_user)):
    """Get all gallery images assigned to a specific book"""
    user = current_user
    
    try:
        images = []
        cursor = db.art_studio_gallery.find({
            "user_id": user["id"],
            "book_id": book_id
        }).sort("created_at", -1)
        
        async for img in cursor:
            images.append({
                "id": str(img["_id"]),
                "image_url": img.get("image_url"),
                "name": img.get("name"),
                "type": img.get("type"),
                "style": img.get("style"),
                "character_data": img.get("character_data"),
                "scene_data": img.get("scene_data"),
                "book_id": img.get("book_id"),
                "created_at": img.get("created_at").isoformat() if img.get("created_at") else None
            })
        
        return {"images": images}
        
    except Exception as e:
        logging.error(f"Book gallery error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load book gallery")

# Starter Library Images - Pre-made images for new users (100+ diverse images)
STARTER_LIBRARY_IMAGES = [
    # Fantasy Characters
    {"id": "starter_1", "url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800", "name": "Fantasy Princess", "category": "character", "tags": ["fantasy", "princess", "female", "portrait"]},
    {"id": "starter_2", "url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800", "name": "Young Heroine", "category": "character", "tags": ["portrait", "female", "young", "hero"]},
    {"id": "starter_3", "url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800", "name": "Noble Knight", "category": "character", "tags": ["fantasy", "knight", "male", "portrait"]},
    {"id": "starter_4", "url": "https://images.unsplash.com/photo-1552058544-f2b08422138a?w=800", "name": "Wise Elder", "category": "character", "tags": ["elder", "wizard", "male", "portrait"]},
    {"id": "starter_5", "url": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800", "name": "Mystical Maiden", "category": "character", "tags": ["fantasy", "mystical", "female", "portrait"]},
    # Children Characters
    {"id": "starter_6", "url": "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800", "name": "Curious Child", "category": "character", "tags": ["child", "curious", "adventure"]},
    {"id": "starter_7", "url": "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=800", "name": "Happy Boy", "category": "character", "tags": ["child", "boy", "happy", "young"]},
    {"id": "starter_8", "url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=800", "name": "Confident Teen", "category": "character", "tags": ["teen", "confident", "male"]},
    {"id": "starter_9", "url": "https://images.unsplash.com/photo-1765635648081-73f1e9e2189a?w=800", "name": "Superhero Kid", "category": "character", "tags": ["child", "superhero", "costume", "adventure"]},
    # Fantasy Scenes
    {"id": "starter_10", "url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800", "name": "Enchanted Forest", "category": "scene", "tags": ["forest", "fantasy", "magical", "nature"]},
    {"id": "starter_11", "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800", "name": "Majestic Mountain", "category": "scene", "tags": ["mountain", "epic", "landscape", "nature"]},
    {"id": "starter_12", "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800", "name": "Tropical Beach", "category": "scene", "tags": ["beach", "tropical", "ocean", "paradise"]},
    {"id": "starter_13", "url": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=800", "name": "Outer Space", "category": "scene", "tags": ["space", "cosmic", "stars", "scifi"]},
    {"id": "starter_14", "url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800", "name": "Underwater World", "category": "scene", "tags": ["underwater", "ocean", "coral", "sea"]},
    {"id": "starter_15", "url": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800", "name": "Ancient Library", "category": "scene", "tags": ["library", "books", "magical", "indoor"]},
    # Nature & Adventure
    {"id": "starter_16", "url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800", "name": "Sunset Cliffs", "category": "scene", "tags": ["sunset", "cliffs", "dramatic", "nature"]},
    {"id": "starter_17", "url": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800", "name": "Northern Lights", "category": "scene", "tags": ["aurora", "arctic", "magical", "night"]},
    {"id": "starter_18", "url": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800", "name": "Cherry Blossoms", "category": "scene", "tags": ["japan", "spring", "flowers", "peaceful"]},
    # Magical Elements
    {"id": "starter_19", "url": "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=800", "name": "Moonlit Lake", "category": "scene", "tags": ["moon", "lake", "night", "peaceful"]},
    {"id": "starter_20", "url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800", "name": "Floating Islands", "category": "scene", "tags": ["fantasy", "islands", "sky", "magical"]},
    # Animals
    {"id": "starter_21", "url": "https://images.unsplash.com/photo-1474511320723-9a56873571b7?w=800", "name": "Majestic Lion", "category": "character", "tags": ["lion", "animal", "majestic", "wildlife"]},
    {"id": "starter_22", "url": "https://images.unsplash.com/photo-1425082661705-1834bfd09dca?w=800", "name": "Wise Owl", "category": "character", "tags": ["owl", "animal", "wise", "bird"]},
    {"id": "starter_23", "url": "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?w=800", "name": "Sea Turtle", "category": "character", "tags": ["turtle", "ocean", "animal", "peaceful"]},
    {"id": "starter_24", "url": "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=800", "name": "Friendly Dragon", "category": "character", "tags": ["dragon", "fantasy", "creature", "magical"]},
    # More Characters
    {"id": "starter_25", "url": "https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=800", "name": "Robot Friend", "category": "character", "tags": ["robot", "scifi", "friendly", "future"]},
    {"id": "starter_26", "url": "https://images.unsplash.com/photo-1608889825103-eb5ed706fc64?w=800", "name": "Pixar Style Kid", "category": "character", "tags": ["cartoon", "pixar", "kid", "animated"]},
    # More Scenes
    {"id": "starter_27", "url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800", "name": "Galaxy View", "category": "scene", "tags": ["space", "galaxy", "stars", "cosmic"]},
    {"id": "starter_28", "url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "name": "Castle Interior", "category": "scene", "tags": ["castle", "interior", "medieval", "grand"]},
    {"id": "starter_29", "url": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=800", "name": "Secret Garden", "category": "scene", "tags": ["garden", "flowers", "magical", "nature"]},
    {"id": "starter_30", "url": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=800", "name": "Desert Oasis", "category": "scene", "tags": ["desert", "oasis", "adventure", "warm"]},
    # Fairy Tale Castles
    {"id": "starter_31", "url": "https://images.unsplash.com/photo-1754901690791-0658f9a36cdf?w=800", "name": "Fairy Tale Castle", "category": "scene", "tags": ["castle", "fantasy", "fairy tale", "magical"]},
    {"id": "starter_32", "url": "https://images.unsplash.com/photo-1766156555244-572b9757433b?w=800", "name": "Colorful Castle", "category": "scene", "tags": ["castle", "colorful", "fantasy", "fairytale"]},
    {"id": "starter_33", "url": "https://images.pexels.com/photos/14811896/pexels-photo-14811896.jpeg?w=800", "name": "Night Castle", "category": "scene", "tags": ["castle", "night", "purple", "magical"]},
    # Children Adventure
    {"id": "starter_34", "url": "https://images.unsplash.com/photo-1763819089956-5749bf52653c?w=800", "name": "Tree Climber", "category": "character", "tags": ["child", "adventure", "nature", "climbing"]},
    {"id": "starter_35", "url": "https://images.pexels.com/photos/5604965/pexels-photo-5604965.jpeg?w=800", "name": "Forest Explorers", "category": "character", "tags": ["children", "camping", "adventure", "forest"]},
    {"id": "starter_36", "url": "https://images.unsplash.com/photo-1762921602540-fcd477689f52?w=800", "name": "Running Child", "category": "character", "tags": ["child", "running", "outdoor", "happy"]},
    # Mystical Forest
    {"id": "starter_37", "url": "https://images.unsplash.com/photo-1719457842736-96ee8082a524?w=800", "name": "Forest Stream", "category": "scene", "tags": ["forest", "stream", "peaceful", "nature"]},
    {"id": "starter_38", "url": "https://images.pexels.com/photos/15022098/pexels-photo-15022098.jpeg?w=800", "name": "Forest Fairy", "category": "character", "tags": ["fairy", "forest", "magical", "fantasy"]},
    {"id": "starter_39", "url": "https://images.unsplash.com/photo-1573689705959-7786e029b31e?w=800", "name": "Magical Trees", "category": "scene", "tags": ["forest", "trees", "mystical", "nature"]},
    # Cute Animals
    {"id": "starter_40", "url": "https://images.unsplash.com/photo-1706745262357-5ecaa3154433?w=800", "name": "Fluffy Puppy", "category": "character", "tags": ["dog", "puppy", "cute", "pet"]},
    {"id": "starter_41", "url": "https://images.unsplash.com/photo-1767101607738-c93754ce5220?w=800", "name": "Curious Puppy", "category": "character", "tags": ["dog", "puppy", "curious", "cute"]},
    {"id": "starter_42", "url": "https://images.pexels.com/photos/28990269/pexels-photo-28990269.jpeg?w=800", "name": "Maltipoo Puppy", "category": "character", "tags": ["dog", "puppy", "fluffy", "cute"]},
    {"id": "starter_43", "url": "https://images.unsplash.com/photo-1594653283108-953a4f93400e?w=800", "name": "White Dog", "category": "character", "tags": ["dog", "white", "pet", "friendly"]},
    # Adventure Scenes
    {"id": "starter_44", "url": "https://images.pexels.com/photos/30104945/pexels-photo-30104945.jpeg?w=800", "name": "Pirate Ship", "category": "scene", "tags": ["ship", "pirate", "adventure", "ocean"]},
    {"id": "starter_45", "url": "https://images.unsplash.com/photo-1760875658787-ff2474c6385c?w=800", "name": "Sailing Ship", "category": "scene", "tags": ["ship", "sailing", "ocean", "adventure"]},
    {"id": "starter_46", "url": "https://images.pexels.com/photos/28830053/pexels-photo-28830053.jpeg?w=800", "name": "Pirate Captain", "category": "character", "tags": ["pirate", "captain", "adventure", "ocean"]},
    # Rainbow & Fantasy
    {"id": "starter_47", "url": "https://images.unsplash.com/photo-1759670944001-430986689b77?w=800", "name": "Rainbow Girl", "category": "character", "tags": ["rainbow", "colorful", "fantasy", "child"]},
    {"id": "starter_48", "url": "https://images.pexels.com/photos/10098871/pexels-photo-10098871.jpeg?w=800", "name": "Unicorn Baby", "category": "character", "tags": ["unicorn", "baby", "cute", "costume"]},
    # More Portraits
    {"id": "starter_49", "url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=800", "name": "Smiling Woman", "category": "character", "tags": ["woman", "smile", "portrait", "happy"]},
    {"id": "starter_50", "url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=800", "name": "Young Man", "category": "character", "tags": ["man", "young", "portrait", "confident"]},
    # Nature Scenes
    {"id": "starter_51", "url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800", "name": "Misty Valley", "category": "scene", "tags": ["valley", "mist", "nature", "peaceful"]},
    {"id": "starter_52", "url": "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=800", "name": "Waterfall", "category": "scene", "tags": ["waterfall", "nature", "dramatic", "water"]},
    {"id": "starter_53", "url": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=800", "name": "Green Hills", "category": "scene", "tags": ["hills", "green", "nature", "landscape"]},
    {"id": "starter_54", "url": "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800", "name": "Forest Path", "category": "scene", "tags": ["forest", "path", "nature", "adventure"]},
    # City & Urban
    {"id": "starter_55", "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800", "name": "City Skyline", "category": "scene", "tags": ["city", "skyline", "urban", "modern"]},
    {"id": "starter_56", "url": "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=800", "name": "Street Scene", "category": "scene", "tags": ["street", "urban", "city", "life"]},
    # Animals - Wildlife
    {"id": "starter_57", "url": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=800", "name": "Fox Portrait", "category": "character", "tags": ["fox", "animal", "wildlife", "cute"]},
    {"id": "starter_58", "url": "https://images.unsplash.com/photo-1474511320723-9a56873571b7?w=800", "name": "Wild Cat", "category": "character", "tags": ["cat", "wild", "animal", "predator"]},
    {"id": "starter_59", "url": "https://images.unsplash.com/photo-1551969014-7d2c4cddf0b6?w=800", "name": "Bunny Rabbit", "category": "character", "tags": ["rabbit", "bunny", "cute", "animal"]},
    {"id": "starter_60", "url": "https://images.unsplash.com/photo-1474511320723-9a56873571b7?w=800", "name": "Deer in Forest", "category": "character", "tags": ["deer", "forest", "wildlife", "peaceful"]},
    # Space & Cosmos
    {"id": "starter_61", "url": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=800", "name": "Nebula", "category": "scene", "tags": ["space", "nebula", "cosmic", "colorful"]},
    {"id": "starter_62", "url": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=800", "name": "Milky Way", "category": "scene", "tags": ["space", "milky way", "stars", "night"]},
    {"id": "starter_63", "url": "https://images.unsplash.com/photo-1454789548928-9efd52dc4031?w=800", "name": "Earth from Space", "category": "scene", "tags": ["earth", "space", "planet", "cosmic"]},
    # Beach & Ocean
    {"id": "starter_64", "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800", "name": "Paradise Beach", "category": "scene", "tags": ["beach", "paradise", "tropical", "ocean"]},
    {"id": "starter_65", "url": "https://images.unsplash.com/photo-1519046904884-53103b34b206?w=800", "name": "Ocean Waves", "category": "scene", "tags": ["ocean", "waves", "water", "dramatic"]},
    {"id": "starter_66", "url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=800", "name": "Calm Sea", "category": "scene", "tags": ["sea", "calm", "peaceful", "water"]},
    # Seasons
    {"id": "starter_67", "url": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=800", "name": "Autumn Leaves", "category": "scene", "tags": ["autumn", "leaves", "fall", "colorful"]},
    {"id": "starter_68", "url": "https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=800", "name": "Winter Snow", "category": "scene", "tags": ["winter", "snow", "cold", "peaceful"]},
    {"id": "starter_69", "url": "https://images.unsplash.com/photo-1462275646964-a0e3571f4f67?w=800", "name": "Spring Flowers", "category": "scene", "tags": ["spring", "flowers", "colorful", "nature"]},
    {"id": "starter_70", "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800", "name": "Summer Beach", "category": "scene", "tags": ["summer", "beach", "sunny", "tropical"]},
    # Fantasy Creatures
    {"id": "starter_71", "url": "https://images.unsplash.com/photo-1577493340887-b7bfff550145?w=800", "name": "Dragon Eye", "category": "character", "tags": ["dragon", "eye", "fantasy", "creature"]},
    {"id": "starter_72", "url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800", "name": "Magical Forest", "category": "scene", "tags": ["forest", "magical", "fantasy", "enchanted"]},
    # More Children
    {"id": "starter_73", "url": "https://images.unsplash.com/photo-1503919545889-aef636e10ad4?w=800", "name": "Reading Child", "category": "character", "tags": ["child", "reading", "book", "curious"]},
    {"id": "starter_74", "url": "https://images.unsplash.com/photo-1489710437720-ebb67ec84dd2?w=800", "name": "Happy Girl", "category": "character", "tags": ["girl", "happy", "child", "smiling"]},
    {"id": "starter_75", "url": "https://images.unsplash.com/photo-1445633743309-b60418bedbba?w=800", "name": "Playful Boy", "category": "character", "tags": ["boy", "playful", "child", "outdoor"]},
    # Architecture
    {"id": "starter_76", "url": "https://images.unsplash.com/photo-1431576901776-e539bd916ba2?w=800", "name": "Old Castle", "category": "scene", "tags": ["castle", "old", "medieval", "architecture"]},
    {"id": "starter_77", "url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800", "name": "London Bridge", "category": "scene", "tags": ["bridge", "london", "city", "landmark"]},
    {"id": "starter_78", "url": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=800", "name": "Paris Tower", "category": "scene", "tags": ["paris", "tower", "landmark", "romantic"]},
    # More Animals
    {"id": "starter_79", "url": "https://images.unsplash.com/photo-1425082661705-1834bfd09dca?w=800", "name": "Barn Owl", "category": "character", "tags": ["owl", "bird", "wise", "night"]},
    {"id": "starter_80", "url": "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?w=800", "name": "Swimming Turtle", "category": "character", "tags": ["turtle", "swimming", "ocean", "peaceful"]},
    {"id": "starter_81", "url": "https://images.unsplash.com/photo-1474511320723-9a56873571b7?w=800", "name": "King Lion", "category": "character", "tags": ["lion", "king", "majestic", "wildlife"]},
    # Magical Elements
    {"id": "starter_82", "url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800", "name": "Magic Book", "category": "scene", "tags": ["book", "magic", "fantasy", "mystical"]},
    {"id": "starter_83", "url": "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=800", "name": "Magic Moon", "category": "scene", "tags": ["moon", "magic", "night", "mystical"]},
    # More Landscapes
    {"id": "starter_84", "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800", "name": "Snow Mountain", "category": "scene", "tags": ["mountain", "snow", "winter", "epic"]},
    {"id": "starter_85", "url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800", "name": "Sunset Valley", "category": "scene", "tags": ["valley", "sunset", "golden", "nature"]},
    {"id": "starter_86", "url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800", "name": "Alpine Peaks", "category": "scene", "tags": ["alps", "peaks", "mountain", "dramatic"]},
    # Fantasy Portraits
    {"id": "starter_87", "url": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800", "name": "Elf Princess", "category": "character", "tags": ["elf", "princess", "fantasy", "mystical"]},
    {"id": "starter_88", "url": "https://images.unsplash.com/photo-1552058544-f2b08422138a?w=800", "name": "Old Wizard", "category": "character", "tags": ["wizard", "old", "wise", "magic"]},
    # Indoor Scenes
    {"id": "starter_89", "url": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800", "name": "Magic Library", "category": "scene", "tags": ["library", "books", "magic", "indoor"]},
    {"id": "starter_90", "url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800", "name": "Grand Hall", "category": "scene", "tags": ["hall", "grand", "medieval", "castle"]},
    # More Nature
    {"id": "starter_91", "url": "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=800", "name": "Rainbow Falls", "category": "scene", "tags": ["waterfall", "rainbow", "nature", "magical"]},
    {"id": "starter_92", "url": "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800", "name": "Green Forest", "category": "scene", "tags": ["forest", "green", "nature", "peaceful"]},
    # Diverse Characters
    {"id": "starter_93", "url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=800", "name": "Cool Guy", "category": "character", "tags": ["man", "cool", "portrait", "young"]},
    {"id": "starter_94", "url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=800", "name": "Kind Woman", "category": "character", "tags": ["woman", "kind", "portrait", "warm"]},
    {"id": "starter_95", "url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800", "name": "Brave Girl", "category": "character", "tags": ["girl", "brave", "young", "hero"]},
    # Final Adventures
    {"id": "starter_96", "url": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=800", "name": "Desert Journey", "category": "scene", "tags": ["desert", "journey", "adventure", "sand"]},
    {"id": "starter_97", "url": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800", "name": "Aurora Sky", "category": "scene", "tags": ["aurora", "sky", "night", "magical"]},
    {"id": "starter_98", "url": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800", "name": "Sakura Garden", "category": "scene", "tags": ["sakura", "garden", "japan", "spring"]},
    {"id": "starter_99", "url": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=800", "name": "Hidden Garden", "category": "scene", "tags": ["garden", "hidden", "magical", "flowers"]},
    {"id": "starter_100", "url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800", "name": "Deep Space", "category": "scene", "tags": ["space", "deep", "cosmic", "stars"]},
]

@api_router.get("/starter-library")
async def get_starter_library(category: Optional[str] = None):
    """Get starter library images for new users - no auth required"""
    images = STARTER_LIBRARY_IMAGES
    
    if category:
        images = [img for img in images if img.get("category") == category]
    
    return {"images": images, "total": len(images)}



class SaveAnimationRequest(BaseModel):
    video_url: str
    name: str
    motion_prompt: Optional[str] = ""
    style: Optional[str] = "natural"

@api_router.post("/art-studio/save-animation")
async def save_animation(request: SaveAnimationRequest, current_user: dict = Depends(get_current_user)):
    """Save an animation to user's gallery"""
    user = current_user
    
    try:
        gallery_item = {
            "user_id": user["id"],
            "image_url": request.video_url,  # Store video URL in image_url field for compatibility
            "name": request.name,
            "type": "animation",  # New field to distinguish animations
            "style": request.style,
            "motion_prompt": request.motion_prompt,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = await db.art_studio_gallery.insert_one(gallery_item)
        
        return {
            "success": True,
            "id": str(result.inserted_id)
        }
        
    except Exception as e:
        logging.error(f"Save animation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save animation")



# ============================================================================
# CONTENT MODERATION SYSTEM
# ============================================================================

class ModerationResult(BaseModel):
    flagged: bool
    categories: List[str] = []
    message: str = ""

class PublishRequestModel(BaseModel):
    book_id: str

async def moderate_text_content(text: str) -> ModerationResult:
    """Use AI to moderate text content for inappropriate content"""
    if not text or len(text.strip()) < 5:
        return ModerationResult(flagged=False, categories=[], message="Content too short to moderate")
    
    try:
        llm_key = os.environ.get("EMERGENT_LLM_KEY")
        if not llm_key:
            logging.warning("No EMERGENT_LLM_KEY for moderation")
            return ModerationResult(flagged=False, categories=[], message="Moderation skipped - no API key")
        
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"moderation-{uuid.uuid4()}",
            system_message="""You are a content moderation assistant for a children's book platform. 
Analyze the given text and determine if it contains any inappropriate content for a children's book platform.

Categories to check:
- violence: Graphic violence, gore, or harm to children
- sexual: Sexual content, nudity, or inappropriate relationships
- hate: Hate speech, discrimination, or harmful stereotypes
- profanity: Strong language or profanity
- harmful: Self-harm, drugs, or dangerous activities for children
- disturbing: Scary or disturbing content inappropriate for young readers

Respond ONLY in this exact JSON format:
{"flagged": true/false, "categories": ["category1", "category2"], "reason": "brief explanation"}

If content is safe, respond: {"flagged": false, "categories": [], "reason": "Content is appropriate for children"}"""
        ).with_model("openai", "gpt-4.1-mini")
        
        response = await chat.send_message(UserMessage(text=f"Moderate this children's book content:\n\n{text[:2000]}"))
        
        # Parse the response
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return ModerationResult(
                    flagged=result.get("flagged", False),
                    categories=result.get("categories", []),
                    message=result.get("reason", "")
                )
        except:
            pass
        
        return ModerationResult(flagged=False, categories=[], message="Moderation completed")
    except Exception as e:
        logging.error(f"Moderation error: {e}")
        return ModerationResult(flagged=False, categories=[], message=f"Moderation error: {str(e)}")

@api_router.post("/books/{book_id}/request-publish")
async def request_book_publish(book_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Request to publish a book - sends notification to admin for review"""
    
    # Get the book
    book = await db.books.find_one({"id": book_id, "author_id": current_user["id"]})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found or you don't own it")
    
    # Get all pages content for AI moderation
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    combined_text = f"Title: {book.get('title', '')}\n\nDescription: {book.get('description', '')}\n\n"
    
    for chapter in chapters:
        pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).to_list(100)
        for page in pages:
            if page.get("text_content"):
                combined_text += page["text_content"] + "\n\n"
    
    # Run AI moderation automatically
    moderation_result = await moderate_text_content(combined_text)
    
    # Update book status to pending review with moderation results
    update_data = {
        "publish_status": "pending_review",
        "publish_requested_at": datetime.now(timezone.utc).isoformat(),
        "moderation_flags": moderation_result.categories,
        "moderation_message": moderation_result.message,
        "moderation_flagged": moderation_result.flagged,
        "moderation_run_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.books.update_one({"id": book_id}, {"$set": update_data})
    
    # Send email notification to admin with AI moderation results
    # Note: Until azories.com domain is verified in Resend, emails go to the registered account email
    admin_email = os.environ.get("ADMIN_NOTIFY_EMAIL", "jamesstephenbrooks@outlook.com")
    app_url = os.environ.get("APP_URL", "https://shots-gallery-1.preview.emergentagent.com")
    
    # Different email based on moderation result
    if moderation_result.flagged:
        subject = f"⚠️ FLAGGED: Book '{book['title']}' requires review"
        status_color = "#dc2626"
        status_icon = "⚠️"
        verdict_html = f"""
        <div style="background: #fef2f2; border: 1px solid #dc2626; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h3 style="color: #dc2626; margin: 0 0 10px 0;">⚠️ AI Moderation: FLAGGED</h3>
            <p style="margin: 5px 0;"><strong>Flagged Categories:</strong> {', '.join(moderation_result.categories)}</p>
            <p style="margin: 5px 0;"><strong>AI Assessment:</strong> {moderation_result.message}</p>
        </div>
        """
    else:
        subject = f"✅ New book ready for review: '{book['title']}'"
        status_color = "#16a34a"
        status_icon = "✅"
        verdict_html = f"""
        <div style="background: #f0fdf4; border: 1px solid #16a34a; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h3 style="color: #16a34a; margin: 0 0 10px 0;">✅ AI Moderation: PASSED</h3>
            <p style="margin: 5px 0;">{moderation_result.message}</p>
        </div>
        """
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #7c3aed, #a855f7); padding: 20px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">📚 Azories Book Review</h1>
        </div>
        
        <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
            <h2 style="color: #1f2937; margin-top: 0;">{status_icon} New Book Submission</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Book Title:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{book['title']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Author:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{current_user.get('name', 'Unknown')} ({current_user.get('email', 'Unknown')})</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Genre:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{book.get('genre', 'Unknown')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Age Rating:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{book.get('age_rating', 'All Ages')}</td>
                </tr>
            </table>
            
            {verdict_html}
            
            <p style="color: #6b7280; margin-top: 20px;">Please log in to the Admin Dashboard to review this book and make a final decision.</p>
            
            <div style="text-align: center; margin: 25px 0;">
                <a href="{app_url}/admin" style="background: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">Review Book</a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                Admin Login: Username: <code>Admin</code><br>
                Azories Content Management System
            </p>
        </div>
    </body>
    </html>
    """
    
    # Send email in background
    if email_configured():
        background_tasks.add_task(send_email, admin_email, subject, html_content)
        logging.info(f"Admin notification email sent for book {book_id} (flagged: {moderation_result.flagged})")
    else:
        logging.warning(f"Email not configured - admin notification for book {book_id} skipped")
    
    return {
        "success": True,
        "status": "pending_review",
        "flagged": moderation_result.flagged,
        "moderation_result": moderation_result.message,
        "message": "Your book has been submitted for review. An admin will review it and you will be notified once it's approved."
    }

@api_router.post("/books/{book_id}/unpublish")
async def unpublish_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """User can unpublish their own book (withdraw from publication)"""
    book = await db.books.find_one({"id": book_id, "author_id": current_user["id"]})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found or you don't own it")
    
    await db.books.update_one(
        {"id": book_id},
        {"$set": {
            "is_published": False,
            "publish_status": "draft"
        }}
    )
    
    return {"success": True, "message": "Book unpublished and returned to draft status"}

@api_router.post("/admin/books/{book_id}/approve")
async def admin_approve_book(book_id: str, background_tasks: BackgroundTasks, admin: dict = Depends(get_admin_user)):
    """Admin endpoint to approve a book for publication"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get the author's email
    author = await db.users.find_one({"id": book.get("author_id")}, {"_id": 0})
    author_email = author.get("email") if author else None
    author_name = author.get("name", "Author") if author else "Author"
    
    await db.books.update_one(
        {"id": book_id},
        {"$set": {
            "publish_status": "published",
            "is_published": True,
            "approved_by": admin.get("username", "Admin"),
            "approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send approval email to creator
    if author_email and email_configured():
        app_url = os.environ.get("APP_URL", "https://shots-gallery-1.preview.emergentagent.com")
        subject = f"🎉 Your book '{book['title']}' has been approved!"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #16a34a, #22c55e); padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🎉 Congratulations!</h1>
            </div>
            
            <div style="background: #ffffff; padding: 25px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                <h2 style="color: #16a34a; margin-top: 0;">Your Book Has Been Approved!</h2>
                
                <p>Hi {author_name},</p>
                
                <p>Great news! Your book <strong>"{book['title']}"</strong> has been reviewed and approved for publication on Azories.</p>
                
                <div style="background: #f0fdf4; border: 1px solid #16a34a; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #16a34a; font-weight: bold;">✅ Your book is now live!</p>
                    <p style="margin: 10px 0 0 0; color: #166534;">Readers can now discover and enjoy your story in the Azories library.</p>
                </div>
                
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{app_url}/read/{book_id}" style="background: #16a34a; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">View Your Book</a>
                </div>
                
                <p style="color: #6b7280;">Thank you for sharing your creativity with the Azories community!</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                    The Azories Team<br>
                    <a href="{app_url}" style="color: #7c3aed;">azories.com</a>
                </p>
            </div>
        </body>
        </html>
        """
        background_tasks.add_task(send_email, author_email, subject, html_content)
        logging.info(f"Approval notification sent to {author_email} for book {book_id}")
    
    return {"success": True, "message": "Book approved and published"}

@api_router.post("/admin/books/{book_id}/reject")
async def admin_reject_book(book_id: str, background_tasks: BackgroundTasks, reason: str = "", admin: dict = Depends(get_admin_user)):
    """Admin endpoint to reject a book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get the author's email
    author = await db.users.find_one({"id": book.get("author_id")}, {"_id": 0})
    author_email = author.get("email") if author else None
    author_name = author.get("name", "Author") if author else "Author"
    
    await db.books.update_one(
        {"id": book_id},
        {"$set": {
            "publish_status": "rejected",
            "is_published": False,
            "rejected_by": admin.get("username", "Admin"),
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": reason
        }}
    )
    
    # Send rejection email to creator
    if author_email and email_configured():
        app_url = os.environ.get("APP_URL", "https://shots-gallery-1.preview.emergentagent.com")
        reason_html = f"""
            <div style="background: #fef2f2; border: 1px solid #dc2626; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #dc2626; font-weight: bold;">Reason for rejection:</p>
                <p style="margin: 10px 0 0 0; color: #991b1b;">{reason if reason else "No specific reason provided. Please review our content guidelines."}</p>
            </div>
        """ if reason else ""
        
        subject = f"📚 Update on your book '{book['title']}'"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #7c3aed, #a855f7); padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">📚 Book Review Update</h1>
            </div>
            
            <div style="background: #ffffff; padding: 25px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1f2937; margin-top: 0;">Your Book Needs Some Changes</h2>
                
                <p>Hi {author_name},</p>
                
                <p>Thank you for submitting <strong>"{book['title']}"</strong> to Azories. After careful review, we weren't able to approve your book for publication at this time.</p>
                
                {reason_html}
                
                <p style="color: #4b5563;"><strong>What you can do:</strong></p>
                <ul style="color: #4b5563;">
                    <li>Review and update your book content</li>
                    <li>Make sure it follows our community guidelines</li>
                    <li>Submit it again for review when ready</li>
                </ul>
                
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{app_url}/editor/{book_id}" style="background: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">Edit Your Book</a>
                </div>
                
                <p style="color: #6b7280;">We appreciate your creativity and look forward to seeing your revised submission!</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                    The Azories Team<br>
                    <a href="{app_url}" style="color: #7c3aed;">azories.com</a>
                </p>
            </div>
        </body>
        </html>
        """
        background_tasks.add_task(send_email, author_email, subject, html_content)
        logging.info(f"Rejection notification sent to {author_email} for book {book_id}")
    
    return {"success": True, "message": "Book rejected"}

@api_router.get("/admin/pending-reviews")
async def get_pending_reviews(admin: dict = Depends(get_admin_user)):
    """Get all books pending review (admin only)"""
    # Uses dedicated admin authentication
    
    pending_books = await db.books.find(
        {"publish_status": "pending_review"},
        {"_id": 0}
    ).to_list(100)
    
    return {"books": pending_books, "count": len(pending_books)}

@api_router.post("/admin/books/{book_id}/run-moderation")
async def admin_run_moderation(book_id: str, admin: dict = Depends(get_admin_user)):
    """Admin can manually run content moderation on a book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get all pages content for moderation
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    combined_text = f"Title: {book.get('title', '')}\n\nDescription: {book.get('description', '')}\n\n"
    
    for chapter in chapters:
        pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).to_list(100)
        for page in pages:
            if page.get("text_content"):
                combined_text += page["text_content"] + "\n\n"
    
    # Run moderation
    moderation_result = await moderate_text_content(combined_text)
    
    # Update book with moderation results
    await db.books.update_one(
        {"id": book_id},
        {"$set": {
            "moderation_flags": moderation_result.categories,
            "moderation_message": moderation_result.message,
            "moderation_run_at": datetime.now(timezone.utc).isoformat(),
            "moderation_run_by": admin.get("username", "Admin")
        }}
    )
    
    return {
        "success": True,
        "flagged": moderation_result.flagged,
        "categories": moderation_result.categories,
        "message": moderation_result.message
    }

@api_router.post("/admin/generate-missing-covers")
async def admin_generate_missing_covers(admin: dict = Depends(get_admin_user)):
    """Generate cover images for books that don't have them"""
    import httpx
    
    # Find books without cover images
    books_without_covers = await db.books.find(
        {"$or": [{"cover_image": None}, {"cover_image": ""}, {"cover_image": {"$exists": False}}]},
        {"_id": 0, "id": 1, "title": 1, "genre": 1, "description": 1}
    ).to_list(100)
    
    if not books_without_covers:
        return {"success": True, "message": "All books already have covers", "updated": 0}
    
    updated_count = 0
    errors = []
    
    for book in books_without_covers:
        try:
            # Generate a cover image prompt based on book title and genre
            title = book.get("title", "Untitled")
            genre = book.get("genre", "Fantasy")
            description = book.get("description", "")[:200]
            
            prompt = f"Children's book cover illustration for '{title}', {genre} genre. Vibrant colors, whimsical, professional book cover design. {description}"
            
            # Use fal.ai to generate image
            fal_key = os.environ.get("FAL_KEY")
            if not fal_key:
                errors.append(f"{title}: No FAL_KEY configured")
                continue
                
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://fal.run/fal-ai/flux/schnell",
                    headers={
                        "Authorization": f"Key {fal_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "image_size": "portrait_4_3",
                        "num_images": 1
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("images") and len(result["images"]) > 0:
                        image_url = result["images"][0].get("url")
                        if image_url:
                            # Download and convert to base64
                            img_response = await client.get(image_url)
                            if img_response.status_code == 200:
                                import base64
                                img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                                cover_data = f"data:image/png;base64,{img_base64}"
                                
                                await db.books.update_one(
                                    {"id": book["id"]},
                                    {"$set": {"cover_image": cover_data}}
                                )
                                updated_count += 1
                                logging.info(f"Generated cover for: {title}")
                else:
                    errors.append(f"{title}: API error {response.status_code}")
                    
        except Exception as e:
            errors.append(f"{book.get('title', 'Unknown')}: {str(e)}")
            logging.error(f"Cover generation error for {book.get('id')}: {e}")
    
    return {
        "success": True,
        "message": f"Generated {updated_count} cover images",
        "updated": updated_count,
        "total_without_covers": len(books_without_covers),
        "errors": errors if errors else None
    }


# Workflow Save/Load Endpoints
class WorkflowSaveRequest(BaseModel):
    name: str
    nodes: list
    edges: list
    bookId: Optional[str] = None

@api_router.post("/art-studio/workflow/save")
async def save_workflow(request: WorkflowSaveRequest, current_user: dict = Depends(get_current_user)):
    """Save a node-based workflow"""
    user = current_user
    
    try:
        workflow = {
            "user_id": user["id"],
            "name": request.name,
            "nodes": request.nodes,
            "edges": request.edges,
            "book_id": request.bookId,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Check if workflow with same name exists, update it
        existing = await db.art_studio_workflows.find_one({
            "user_id": user["id"],
            "name": request.name
        })
        
        if existing:
            await db.art_studio_workflows.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "nodes": request.nodes,
                    "edges": request.edges,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            return {"success": True, "id": str(existing["_id"]), "updated": True}
        else:
            result = await db.art_studio_workflows.insert_one(workflow)
            return {"success": True, "id": str(result.inserted_id), "updated": False}
        
    except Exception as e:
        logging.error(f"Workflow save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save workflow")

@api_router.get("/art-studio/workflows")
async def get_workflows(current_user: dict = Depends(get_current_user)):
    """Get user's saved workflows"""
    user = current_user
    
    try:
        workflows = []
        cursor = db.art_studio_workflows.find({"user_id": user["id"]}).sort("updated_at", -1)
        
        async for item in cursor:
            workflows.append({
                "id": str(item["_id"]),
                "name": item["name"],
                "nodes": item.get("nodes", []),
                "edges": item.get("edges", []),
                "created_at": item.get("created_at", "").isoformat() if item.get("created_at") else None,
                "updated_at": item.get("updated_at", "").isoformat() if item.get("updated_at") else None
            })
        
        return {"workflows": workflows}
        
    except Exception as e:
        logging.error(f"Workflow load error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load workflows")

@api_router.delete("/art-studio/workflow/{workflow_id}")
async def delete_workflow(workflow_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a workflow"""
    user = current_user
    
    try:
        from bson import ObjectId
        result = await db.art_studio_workflows.delete_one({
            "_id": ObjectId(workflow_id),
            "user_id": user["id"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {"success": True}
        
    except Exception as e:
        logging.error(f"Workflow delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workflow")

# Prompt History Endpoints
@api_router.get("/art-studio/prompt-history")
async def get_prompt_history(current_user: dict = Depends(get_current_user)):
    """Get user's prompt history"""
    user = current_user
    
    try:
        # Get user's prompt history document
        history_doc = await db.prompt_history.find_one({"user_id": user["id"]})
        
        if history_doc:
            return {"history": history_doc.get("prompts", [])}
        return {"history": []}
        
    except Exception as e:
        logging.error(f"Prompt history fetch error: {e}")
        return {"history": []}

@api_router.post("/art-studio/prompt-history")
async def save_prompt_to_history(data: dict, current_user: dict = Depends(get_current_user)):
    """Save a prompt to user's history"""
    user = current_user
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return {"success": False}
    
    try:
        # Get existing history
        history_doc = await db.prompt_history.find_one({"user_id": user["id"]})
        
        if history_doc:
            prompts = history_doc.get("prompts", [])
            # Remove if already exists (to move to top)
            if prompt in prompts:
                prompts.remove(prompt)
            # Add to beginning
            prompts.insert(0, prompt)
            # Keep only last 20
            prompts = prompts[:20]
            
            await db.prompt_history.update_one(
                {"user_id": user["id"]},
                {"$set": {"prompts": prompts}}
            )
        else:
            await db.prompt_history.insert_one({
                "user_id": user["id"],
                "prompts": [prompt]
            })
        
        return {"success": True}
        
    except Exception as e:
        logging.error(f"Prompt history save error: {e}")
        return {"success": False}

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
