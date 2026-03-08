from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request, Response, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from enum import Enum
import os
import logging
import secrets
import hashlib
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
load_dotenv(ROOT_DIR / '.env', override=False)

# Import email service
from services.email_service import (
    send_email, is_configured as email_configured,
    get_welcome_email_html, get_password_reset_email_html, 
    get_password_changed_email_html, generate_reset_token, get_token_expiry
)

# Import routes package
from routes import setup_routes

# Import fal.ai service AFTER dotenv loads
try:
    from fal_service import (
        generate_image_flux,
        generate_image_ideogram,
        generate_with_face_id,
        train_character_lora,
        check_training_status,
        generate_with_lora,
        upload_image_to_fal,
        upload_video_to_fal,
        generate_video_from_image,
        generate_thumbnails,
        upload_image_with_thumbnails,
        get_available_models as get_fal_models,
        is_fal_configured,
        validate_fal_key_on_startup,
        get_fal_key_status
    )
    FAL_AVAILABLE = is_fal_configured()
    if FAL_AVAILABLE:
        fal_key = os.environ.get('FAL_KEY', '')
        masked_key = f"{fal_key[:10]}...{fal_key[-4:]}" if len(fal_key) > 20 else "***"
        logging.info(f"fal.ai service initialized with key: {masked_key}")
    else:
        logging.warning("fal.ai service available but FAL_KEY not configured")
except ImportError as e:
    logging.warning(f"fal.ai service not available: {e}")
    FAL_AVAILABLE = False
    is_fal_configured = lambda: False
    validate_fal_key_on_startup = None
    get_fal_key_status = lambda: {"valid": None, "error_message": "fal_service not loaded"}

# Import Cloudinary service for permanent video storage
try:
    from cloudinary_service import (
        upload_video_to_cloudinary,
        migrate_video_from_fal_to_cloudinary,
        is_cloudinary_configured
    )
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = is_cloudinary_configured()
    if CLOUDINARY_AVAILABLE:
        logging.info("Cloudinary service initialized for permanent video storage")
    else:
        logging.warning("Cloudinary service available but not configured")
except ImportError as e:
    logging.warning(f"Cloudinary service not available: {e}")
    CLOUDINARY_AVAILABLE = False
    is_cloudinary_configured = lambda: False
    cloudinary = None

# Google Veo 3 video generation service
VEO3_AVAILABLE = False
veo3_client = None
try:
    from google import genai
    from google.genai import types
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or os.environ.get('EMERGENT_LLM_KEY')
    if GOOGLE_API_KEY:
        veo3_client = genai.Client(api_key=GOOGLE_API_KEY)
        VEO3_AVAILABLE = True
        logging.info("Google Veo 3 video service initialized")
    else:
        logging.warning("Google Veo 3 not available - no API key configured")
except ImportError as e:
    logging.warning(f"Google Veo 3 service not available: {e}")

async def generate_video_with_veo3(prompt: str, duration_seconds: int = 8, aspect_ratio: str = "16:9") -> dict:
    """
    Generate video using Google Veo 3.1 model.
    Returns dict with video_url or error.
    """
    if not VEO3_AVAILABLE or not veo3_client:
        return {"success": False, "error": "Veo 3 service not available"}
    
    try:
        # Map aspect ratio to Veo format
        veo_aspect = aspect_ratio.replace(":", ":")  # Already in correct format
        
        # Configure generation parameters
        config = types.GenerateVideosConfig(
            duration_seconds=min(duration_seconds, 8),  # Veo 3.1 max is 8 seconds
            aspect_ratio=veo_aspect,
            enhance_prompt=True,
            number_of_videos=1
        )
        
        # Submit video generation request
        logging.info(f"Starting Veo 3.1 video generation: {prompt[:50]}...")
        operation = veo3_client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            config=config
        )
        
        # Poll for completion (Veo is async)
        import time
        max_wait = 300  # 5 minutes max
        poll_interval = 10  # Check every 10 seconds
        waited = 0
        
        while waited < max_wait:
            try:
                # Check operation status
                op_result = veo3_client.operations.get(operation.name)
                
                if op_result.done:
                    if op_result.response and op_result.response.generated_videos:
                        video = op_result.response.generated_videos[0]
                        
                        # Get video URL or save video bytes
                        video_url = None
                        if hasattr(video.video, 'uri') and video.video.uri:
                            video_url = video.video.uri
                        elif hasattr(video.video, 'video_bytes'):
                            # Save video bytes to Cloudinary
                            import base64
                            video_bytes = video.video.video_bytes
                            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
                            if CLOUDINARY_AVAILABLE:
                                upload_result = cloudinary.uploader.upload(
                                    f"data:video/mp4;base64,{video_base64}",
                                    resource_type="video",
                                    folder="azories/veo3_videos"
                                )
                                video_url = upload_result.get("secure_url")
                        
                        if video_url:
                            logging.info(f"Veo 3.1 video generated: {video_url[:60]}...")
                            return {"success": True, "video_url": video_url, "model": "veo-3.1"}
                        else:
                            return {"success": False, "error": "No video URL in response"}
                    else:
                        return {"success": False, "error": "No video generated"}
                
                # Still processing - wait and poll again
                await asyncio.sleep(poll_interval)
                waited += poll_interval
                logging.info(f"Veo 3.1 still processing... ({waited}s)")
                
            except Exception as poll_error:
                logging.warning(f"Veo 3 polling error: {poll_error}")
                await asyncio.sleep(poll_interval)
                waited += poll_interval
        
        return {"success": False, "error": "Video generation timed out"}
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Veo 3.1 generation error: {error_msg}")
        return {"success": False, "error": error_msg}

# MongoDB connection - uses Emergent's managed database
# In production, MONGO_URL is set by Emergent's deployment pipeline
import asyncio

def get_mongo_connection():
    """Get MongoDB connection from environment with timeouts for K8s deployment."""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'azories')
    
    # Add connection timeouts for faster failure detection in K8s
    # This prevents long hangs during health checks
    client = AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=5000,  # 5s to select server
        connectTimeoutMS=5000,           # 5s to connect
        socketTimeoutMS=0,               # 0 = no timeout (unlimited) for long AI operations
        maxPoolSize=50,                  # Connection pool size
        retryWrites=True
    )
    
    return client, db_name

# Initialize MongoDB connection
client, db_name = get_mongo_connection()
db = client[db_name]

# ElevenLabs client
eleven_client = None
try:
    eleven_client = ElevenLabs(api_key=os.environ.get('ELEVENLABS_API_KEY'))
except Exception as e:
    logging.warning(f"ElevenLabs client initialization failed: {e}")

# Emergent LLM Key for AI features
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Resend API Key for email notifications
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')

# JWT settings - REQUIRED, no defaults for security
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Default session: 24 hours
JWT_REMEMBER_ME_DAYS = 30  # Remember me: 30 days

# Admin credentials - REQUIRED, no defaults for security
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required")

# VIP users - loaded from environment variable for security
VIP_USERS = [e.strip() for e in os.environ.get("VIP_USERS", "").split(",") if e.strip()]

# Configure logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# In-memory task stores
TASK_STORE: Dict[str, dict] = {}


async def convert_base64_to_cdn(image_data: str) -> str:
    """
    Convert a base64 image to a CDN URL.
    If already a URL or empty, returns as-is.
    """
    if not image_data:
        return image_data
    
    if image_data.startswith('data:image'):
        if FAL_AVAILABLE:
            try:
                cdn_url = await upload_image_to_fal(image_data)
                logger.info(f"Converted base64 to CDN: {cdn_url[:60]}...")
                return cdn_url
            except Exception as e:
                logger.warning(f"Failed to upload to CDN, keeping base64: {e}")
                return image_data
        else:
            logger.warning("FAL_KEY not available, cannot convert base64 to CDN")
            return image_data
    
    return image_data

# Cleanup task reference
_cleanup_task = None

async def cleanup_old_tasks():
    """Remove tasks older than 1 hour from both TASK_STORE and animation_jobs"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    
    # Clean TASK_STORE
    expired = [tid for tid, task in TASK_STORE.items() 
               if task.get("created_at", datetime.now(timezone.utc)) < cutoff]
    for tid in expired:
        TASK_STORE.pop(tid, None)
    
    # Clean animation_jobs (defined later in file, but accessible globally)
    try:
        global animation_jobs
        if 'animation_jobs' in globals():
            expired_jobs = [jid for jid, job in animation_jobs.items() 
                          if job.get("created_at", datetime.now(timezone.utc)) < cutoff]
            for jid in expired_jobs:
                animation_jobs.pop(jid, None)
    except Exception:
        pass  # animation_jobs may not be defined yet at startup
    
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired tasks")

async def periodic_cleanup():
    """Run cleanup every 30 minutes to prevent memory buildup"""
    while True:
        await asyncio.sleep(1800)  # 30 minutes
        await cleanup_old_tasks()
        # Also force garbage collection
        import gc
        gc.collect()
        logger.info("Periodic cleanup and GC completed")

# ============================================================
# AUTO-SEEDING: Automatically seed database on first deployment
# ============================================================

# Auto-seed configuration (loaded from environment for flexibility)
PREVIEW_URL = os.environ.get('SEED_PREVIEW_URL', 'https://blank-screen-debug-3.preview.emergentagent.com')
SEED_IMPORT_KEY = os.environ.get('SEED_IMPORT_KEY', 'azories-import-2026')
LOCAL_EXPORTS_PATH = "/app/exports/collections"

async def seed_from_local_exports():
    """
    Seed database from local export files (for preview environment).
    """
    from bson import json_util
    import glob
    
    essential_collections = ['users', 'books', 'chapters', 'pages', 'book_images', 'system_settings']
    results = {"imported": [], "failed": [], "skipped": []}
    
    logger.info("=" * 60)
    logger.info("🌱 SEEDING DATABASE FROM LOCAL EXPORT FILES")
    logger.info("=" * 60)
    
    for collection_name in essential_collections:
        json_file = f"{LOCAL_EXPORTS_PATH}/{collection_name}.json"
        
        if not os.path.exists(json_file):
            logger.warning(f"   ⚠️ {collection_name}: export file not found")
            results["skipped"].append({"collection": collection_name, "reason": "file not found"})
            continue
        
        try:
            logger.info(f"📥 Loading {collection_name} from {json_file}...")
            
            with open(json_file, 'r') as f:
                documents = json_util.loads(f.read())
            
            if not documents or (isinstance(documents, list) and len(documents) == 0):
                logger.info(f"   ⏭️ {collection_name}: empty, skipping")
                results["skipped"].append({"collection": collection_name, "reason": "empty"})
                continue
            
            # Get collection and drop existing data
            coll = db[collection_name]
            await coll.drop()
            
            # Batch insert for efficiency
            if isinstance(documents, list) and len(documents) > 0:
                batch_size = 500
                total = 0
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    result = await coll.insert_many(batch)
                    total += len(result.inserted_ids)
                
                logger.info(f"   ✅ {collection_name}: {total} documents imported")
                results["imported"].append({"collection": collection_name, "documents": total})
                
        except Exception as e:
            logger.error(f"   ❌ {collection_name}: {str(e)[:100]}")
            results["failed"].append({"collection": collection_name, "error": str(e)[:100]})
    
    logger.info("=" * 60)
    logger.info(f"🌱 LOCAL SEED COMPLETE: {len(results['imported'])} collections imported")
    logger.info("=" * 60)
    
    return results


async def seed_from_preview():
    """
    Fetch essential data from preview environment and insert into local database.
    This is used by production to fetch data from preview.
    """
    from bson import json_util
    
    essential_collections = ['users', 'books', 'chapters', 'pages', 'book_images', 'system_settings']
    results = {"imported": [], "failed": [], "skipped": []}
    
    logger.info("=" * 60)
    logger.info("🌱 SEEDING DATABASE FROM PREVIEW ENVIRONMENT")
    logger.info(f"   Source: {PREVIEW_URL}")
    logger.info("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for collection_name in essential_collections:
            remote_url = f"{PREVIEW_URL}/api/admin/export-collection/{collection_name}?import_key={SEED_IMPORT_KEY}"
            
            try:
                logger.info(f"📥 Fetching {collection_name} from preview...")
                
                async with session.get(remote_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 404:
                        logger.warning(f"   ⚠️ {collection_name}: not found in preview")
                        results["skipped"].append({"collection": collection_name, "reason": "not found"})
                        continue
                    elif response.status != 200:
                        logger.error(f"   ❌ {collection_name}: HTTP {response.status}")
                        results["failed"].append({"collection": collection_name, "error": f"HTTP {response.status}"})
                        continue
                    
                    data_text = await response.text()
                
                # Parse BSON-aware JSON
                documents = json_util.loads(data_text)
                
                if not documents or (isinstance(documents, list) and len(documents) == 0):
                    logger.info(f"   ⏭️ {collection_name}: empty, skipping")
                    results["skipped"].append({"collection": collection_name, "reason": "empty"})
                    continue
                
                # Get collection and drop existing data
                coll = db[collection_name]
                await coll.drop()
                
                # Batch insert for efficiency
                if isinstance(documents, list) and len(documents) > 0:
                    batch_size = 500
                    total = 0
                    for i in range(0, len(documents), batch_size):
                        batch = documents[i:i + batch_size]
                        result = await coll.insert_many(batch)
                        total += len(result.inserted_ids)
                    
                    logger.info(f"   ✅ {collection_name}: {total} documents imported")
                    results["imported"].append({"collection": collection_name, "documents": total})
                
            except asyncio.TimeoutError:
                logger.error(f"   ⏱️ {collection_name}: timeout fetching data")
                results["failed"].append({"collection": collection_name, "error": "timeout"})
            except Exception as e:
                logger.error(f"   ❌ {collection_name}: {str(e)[:100]}")
                results["failed"].append({"collection": collection_name, "error": str(e)[:100]})
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"🌱 REMOTE SEED COMPLETE: {len(results['imported'])} collections imported")
    if results["failed"]:
        logger.warning(f"   ⚠️ {len(results['failed'])} collections failed")
    logger.info("=" * 60)
    
    return results


async def seed_if_empty():
    """
    Check if the database is empty and seed if needed.
    - If local export files exist, use them (preview environment)
    - Otherwise, fetch from preview URL (production environment)
    """
    try:
        # Check if we have any books (primary content)
        book_count = await db.books.count_documents({})
        user_count = await db.users.count_documents({})
        
        logger.info(f"📊 Database check: {book_count} books, {user_count} users")
        
        if book_count == 0:
            logger.info("📭 Database is empty - starting auto-seed...")
            
            # Check if local export files exist
            if os.path.exists(LOCAL_EXPORTS_PATH) and os.path.exists(f"{LOCAL_EXPORTS_PATH}/books.json"):
                logger.info("📁 Local export files found - using local seed")
                await seed_from_local_exports()
            else:
                logger.info("🌐 No local exports - fetching from preview")
                await seed_from_preview()
        else:
            logger.info("✅ Database already has data - skipping seed")
            
    except Exception as e:
        logger.error(f"❌ Auto-seed check failed: {str(e)}")
        # Don't crash the app if seeding fails - it can be done manually


async def background_seed():
    """
    Run seed in background so it doesn't block app startup.
    Waits a few seconds for the app to fully initialize first.
    """
    try:
        await asyncio.sleep(5)  # Wait for app to be ready
        await seed_if_empty()
    except Exception as e:
        logger.error(f"Background seed error (non-fatal): {str(e)[:200]}")


# Lifespan context manager (modern FastAPI approach)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events - optimized for K8s deployment."""
    global _cleanup_task
    
    try:
        # Startup: start periodic cleanup (non-blocking)
        _cleanup_task = asyncio.create_task(periodic_cleanup())
        logger.info("Started periodic task cleanup")
        
        # Load FAL_KEY from database - run in background to not block startup
        asyncio.create_task(_safe_load_fal_key())
        
        # AUTO-SEED: Run in background so app starts immediately
        # This prevents startup timeouts when fetching from preview
        asyncio.create_task(background_seed())
        logger.info("🌱 Background seed task scheduled")
        
        # Create indexes in background - don't block startup
        asyncio.create_task(_create_indexes_background())
        
        # App is ready to serve requests
        logger.info("✅ Application startup complete - ready for health checks")
    except Exception as e:
        logger.error(f"Startup error (non-fatal): {e}")
    
    yield
    
    # Shutdown
    try:
        if _cleanup_task:
            _cleanup_task.cancel()
            try:
                await _cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


async def _safe_load_fal_key():
    """Load FAL key in background with error handling."""
    try:
        await _load_fal_key_from_db()
        # Validate FAL_KEY after loading
        if validate_fal_key_on_startup:
            try:
                fal_status = await validate_fal_key_on_startup()
                if fal_status.get("valid") == False:
                    logger.warning(f"⚠️ FAL_KEY invalid: {fal_status.get('error_message', 'Unknown')}")
                elif fal_status.get("valid") == True:
                    logger.info("✅ FAL_KEY validated - fal.ai features ready")
            except Exception as e:
                logger.warning(f"⚠️ FAL_KEY validation error: {str(e)[:100]}")
    except Exception as e:
        logger.warning(f"FAL key loading error (non-fatal): {e}")


async def _create_indexes_background():
    """Create database indexes in background."""
    try:
        await asyncio.sleep(2)  # Wait a bit for DB connection to stabilize
        await db.audio_cache.create_index("cache_key", unique=True)
        await db.audio_cache.create_index("expires_at", expireAfterSeconds=0)
        logger.info("✅ Audio cache indexes created")
    except Exception as e:
        logger.warning(f"Audio cache index creation: {e}")


async def _load_fal_key_from_db():
    """
    Load FAL_KEY from database if .env key is missing or invalid.
    This ensures the key persists across deployments.
    """
    try:
        # Check if we have a key in the database
        db_setting = await db.system_settings.find_one({"key": "fal_api_key"})
        
        if db_setting and db_setting.get("value"):
            db_key = db_setting["value"]
            env_key = os.environ.get("FAL_KEY", "")
            
            # If .env key is missing or different, use DB key
            if not env_key or env_key != db_key:
                logger.info("Loading FAL_KEY from database (persisted key)")
                os.environ["FAL_KEY"] = db_key
                
                # Also update .env file so it persists locally
                try:
                    env_path = '/app/backend/.env'
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                    
                    updated = False
                    new_lines = []
                    for line in lines:
                        if line.startswith('FAL_KEY='):
                            new_lines.append(f'FAL_KEY={db_key}\n')
                            updated = True
                        else:
                            new_lines.append(line)
                    
                    if not updated:
                        new_lines.append(f'FAL_KEY={db_key}\n')
                    
                    with open(env_path, 'w') as f:
                        f.writelines(new_lines)
                    
                    logger.info("✅ FAL_KEY synced from database to .env file")
                except Exception as e:
                    logger.warning(f"Could not sync FAL_KEY to .env: {e}")
        else:
            # No key in DB, save current .env key to DB for persistence
            env_key = os.environ.get("FAL_KEY", "")
            if env_key and ":" in env_key:
                await db.system_settings.update_one(
                    {"key": "fal_api_key"},
                    {"$set": {
                        "key": "fal_api_key",
                        "value": env_key,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "updated_by": "system_startup"
                    }},
                    upsert=True
                )
                logger.info("✅ FAL_KEY saved to database for persistence")
                
    except Exception as e:
        logger.warning(f"Could not load/save FAL_KEY from database: {e}")

# Create the main app with lifespan
app = FastAPI(
    title="Azories API", 
    description="Digital Book Creation Platform",
    lifespan=lifespan
)

# CORS Configuration - MUST be added immediately after app creation
# Using allow_origins=["*"] for maximum compatibility across all deployments
cors_env = os.environ.get('CORS_ORIGINS', '*')

if cors_env == '*':
    # Allow all origins - works with all deployment environments
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when using wildcard origins
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    # Explicit origins list
    cors_allowed_origins = [o.strip() for o in cors_env.split(',') if o.strip()]
    cors_allowed_origins.extend([
        "https://azories.com",
        "https://www.azories.com",
        "http://localhost:3000",
    ])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

# Global exception handler to prevent server crashes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions to prevent server crash"""
    import traceback
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"[ERROR-{error_id}] Unhandled exception on {request.url.path}: {str(exc)[:200]}")
    logger.error(f"[ERROR-{error_id}] Traceback: {traceback.format_exc()[:500]}")
    
    # Return a proper error response instead of crashing
    return Response(
        content=json.dumps({
            "detail": "An internal error occurred. Please try again.",
            "error_id": error_id
        }),
        status_code=500,
        media_type="application/json"
    )

# Memory management - force garbage collection periodically
import gc
_gc_counter = 0

@app.middleware("http")
async def memory_management_middleware(request: Request, call_next):
    """Middleware to manage memory and prevent leaks"""
    global _gc_counter
    response = await call_next(request)
    
    # Run garbage collection every 100 requests
    _gc_counter += 1
    if _gc_counter >= 100:
        gc.collect()
        _gc_counter = 0
    
    return response

# Setup modular routes (admin, etc.) with email functions
email_funcs = {
    'email_configured': email_configured,
    'send_email': send_email,
    'get_welcome_email_html': get_welcome_email_html,
    'get_password_reset_email_html': get_password_reset_email_html,
    'get_password_changed_email_html': get_password_changed_email_html
}
setup_routes(app, db, email_funcs)

# Create a router with the /api prefix (for remaining routes)
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Health check endpoint for monitoring services (UptimeRobot, etc.)
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint - MUST respond quickly for K8s liveness/readiness probes.
    
    Returns immediately with basic status. Deep checks are optional via ?deep=true.
    """
    from datetime import datetime
    
    # Basic response - always return quickly
    result = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return result


@api_router.get("/health/fal")
async def health_check_fal():
    """
    Dedicated fal.ai key health check endpoint.
    Returns 503 if key is invalid - useful for UptimeRobot alerts.
    """
    from fastapi import Response
    
    if not FAL_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="fal.ai service not configured"
        )
    
    fal_status = get_fal_key_status()
    
    if fal_status.get("valid") is False:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "FAL_KEY_EXPIRED",
                "message": fal_status.get("error_message", "fal.ai API key is invalid or expired"),
                "action": "Update key via Admin Dashboard > Settings or POST /api/admin/update-fal-key",
                "last_checked": fal_status.get("last_checked")
            }
        )
    
    return {
        "status": "ok",
        "fal_ai_key_valid": True,
        "last_checked": fal_status.get("last_checked")
    }

# Admin authentication helper (used by remaining admin endpoints)
async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        # Check for admin role in the payload
        if payload.get("role") != "admin" and not payload.get("admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid admin token")

# ============ ADMIN LOGIN ============
# Separate admin login endpoint for the admin dashboard
# ADMIN_USERNAME and ADMIN_PASSWORD are defined at module level (lines ~148-151)

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@api_router.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """
    Admin login endpoint for the admin dashboard.
    Uses a separate username/password from regular user accounts.
    Returns a JWT token with admin role.
    """
    # Check credentials
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    # Create admin token
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {
        "sub": "admin",
        "email": "admin@azories.com",
        "role": "admin",
        "admin": True,
        "username": request.username,
        "exp": expire
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin_name": request.username,
        "expires_in": 7 * 24 * 60 * 60  # 7 days in seconds
    }


@api_router.get("/admin/verify")
async def verify_admin_token(admin: dict = Depends(get_admin_user)):
    """Verify admin token is valid"""
    return {
        "valid": True,
        "username": admin.get("username", "Admin"),
        "role": "admin"
    }


@api_router.post("/admin/fix-books-auth")
async def fix_books_auth(admin: dict = Depends(get_admin_user)):
    """
    EMERGENCY FIX: Set requires_auth=false on all books so they can be viewed.
    This fixes the issue where AI-created books show 'No illustration' and '1/0' pages.
    """
    try:
        result = await db.books.update_many(
            {},
            {"$set": {"requires_auth": False, "is_published": True}}
        )
        
        return {
            "success": True,
            "message": f"Fixed {result.modified_count} books",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fix books: {str(e)}")



@api_router.post("/admin/fix-ai-books")
async def fix_ai_books(admin: dict = Depends(get_admin_user)):
    """
    Fix AI-generated books to have proper author_id and cover_image fields.
    This ensures AI books appear in 'My Books' and have covers displayed correctly.
    """
    try:
        # Find all AI-generated books (those with generation_job_id but missing author_id)
        ai_books = await db.books.find({
            "generation_job_id": {"$exists": True}
        }).to_list(1000)
        
        fixed_count = 0
        for book in ai_books:
            updates = {}
            
            # Fix author_id if missing
            if not book.get("author_id") and book.get("user_id"):
                updates["author_id"] = book["user_id"]
            
            # Fix cover_image if missing but cover_image_url exists
            if not book.get("cover_image") and book.get("cover_image_url"):
                updates["cover_image"] = book["cover_image_url"]
            
            # Apply updates if any
            if updates:
                await db.books.update_one(
                    {"id": book["id"]},
                    {"$set": updates}
                )
                fixed_count += 1
        
        return {
            "success": True,
            "message": f"Fixed {fixed_count} AI-generated books",
            "total_ai_books": len(ai_books),
            "fixed_count": fixed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fix AI books: {str(e)}")

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
    remember_me: bool = False  # Extended session (30 days) if True

class UserResponse(BaseModel):
    """User data response model - includes is_admin flag"""
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
    trial_hours_remaining: Optional[int] = None  # For 48-hour trial timer
    is_admin: Optional[bool] = False
    
# Credit costs for Pro Studio features
CREDIT_COSTS = {
    "flux_generate": 1,        # Basic FLUX generation
    "flux_pro_generate": 2,    # FLUX Pro generation
    "pulid_generate": 3,       # Face ID preservation
    "lora_training": 50,       # Train LoRA model
    "lora_generate": 2,        # Generate with trained LoRA
    "video_generate": 10,      # Video generation
    "shots_generate": 5,       # 6 angle shots generation
    "expression_generate": 2,  # Expression generation
    "ai_story_create": 5,      # AI Story Creator (covers all page images)
}

# Actual costs to us (for tracking VIP usage)
ACTUAL_COSTS = {
    "flux_generate": 0.025,    # $0.025 per image
    "flux_pro_generate": 0.05, # $0.05 per image
    "pulid_generate": 0.08,    # $0.08 per image
    "lora_training": 2.00,     # $2.00 per training
    "lora_generate": 0.05,     # $0.05 per image
    "video_generate": 0.50,    # $0.50 per video (5 second)
    "shots_generate": 0.25,    # $0.25 for 6 shots
    "expression_generate": 0.05, # $0.05 per expression
    "ai_story_create": 0.50,   # $0.50 for story with images
}

# Note: VIP_USERS is now defined at the top of the file from environment variable

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
    "mini": {
        "credits": 40,
        "price": 2.50,
        "currency": "gbp",
        "description": "~4 AI images",
        "popular": False
    },
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
    hidden: Optional[bool] = None  # Admin can hide books from public library
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
    narrator_voice_locked: Optional[bool] = False
    age_rating: str
    publish_status: str = "draft"
    moderation_flags: Optional[List[str]] = []
    created_at: str
    updated_at: str
    published_at: Optional[str] = None
    chapter_count: int = 0
    total_pages: int = 0
    view_count: int = 0
    read_count: int = 0
    coming_soon: Optional[bool] = False
    coming_soon_label: Optional[str] = None

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
    # Story Details
    title: str = ""  # Optional - AI will generate if empty
    age_range: str = "5-8"  # 3-5, 5-8, 8-12
    num_pages: int = 8
    words_per_page: str = "medium"  # short (50), medium (100), long (150), long_adult (200)
    
    # Main Character
    character_name: str = ""
    character_description: str = ""
    
    # Story
    story_description: str = ""  # Main story idea/description
    
    # Advanced Story Options (Story Studio mode)
    genre: str = "Adventure"  # Adventure, Fantasy, Mystery, Romance, Sci-Fi, Horror, Drama, Comedy
    tone: str = ""  # Optional: dark, light, humorous, serious, emotional
    plot_summary: str = ""  # Optional: detailed plot for advanced users
    chapter_structure: bool = False  # For longer books (30+ pages)
    
    # Style
    art_style: str = "3d-pixar"  # Expanded art styles
    
    # Mode
    creator_mode: str = "kids"  # 'kids' or 'studio' (Story Studio for older readers)
    
    # Legacy fields for backwards compatibility
    idea: str = ""  # Will be derived from story_description if not provided
    age_rating: str = "All Ages"
    generate_images: bool = True
    media_type: str = "images"
    image_style: str = "3d-pixar"

# Credit costs based on page count
AI_STORY_PAGE_CREDITS = {
    5: 5,    # 5 pages = 5 credits
    10: 8,   # 10 pages = 8 credits
    15: 12,  # 15 pages = 12 credits
    20: 15,  # 20 pages = 15 credits
    30: 20,  # 30 pages = 20 credits
    50: 30,  # 50 pages = 30 credits (novel length)
}

# Story Generation Job Status
class StoryJobStatus(str, Enum):
    PENDING = "pending"
    GENERATING_STORY = "generating_story"
    GENERATING_IMAGES = "generating_images"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some images failed but story is saved

class StoryJobProgress(BaseModel):
    job_id: str
    status: StoryJobStatus
    user_id: str
    book_id: Optional[str] = None  # Set when book is created
    progress_percent: int = 0
    current_step: str = "Starting..."
    total_pages: int = 0
    pages_completed: int = 0
    story_text_done: bool = False
    images_status: dict = {}  # {page_num: "pending"|"generating"|"done"|"failed"}
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    completed_at: Optional[datetime] = None
    request_data: dict = {}  # Store original request for retry

# In-memory job store for active jobs (also persisted to MongoDB)
STORY_JOBS = {}

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
    art_style: Optional[str] = "cinematic"  # Art style for generation

class GenerateShotsRequest(BaseModel):
    source_image: str  # Base64 encoded image
    character_id: Optional[str] = None
    style: Optional[str] = "realistic"  # Art style for generation
    character_style: Optional[str] = None  # Character's specific style if available

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

# Note: ADMIN_USERNAME and ADMIN_PASSWORD are defined at the top of the file

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str, remember_me: bool = False) -> str:
    """Create JWT token with configurable expiration"""
    if remember_me:
        expiration = datetime.now(timezone.utc) + timedelta(days=JWT_REMEMBER_ME_DAYS)
    else:
        expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expiration
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
    # 48-hour (2-day) free Pro trial for all new users
    trial_expires = (now + timedelta(hours=48)).isoformat()
    
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": "user",
        "subscription": "pro",  # Start with Pro
        "pro_trial": True,  # Mark as trial user
        "pro_trial_expires_at": trial_expires,  # Trial expiration
        "free_stories_remaining": 3,  # 3 free AI story creations
        "free_stories_used": 0,  # Track usage
        "credits": 0,  # Initialize credits to 0 (users must purchase)
        "created_at": now_iso
    }
    await db.users.insert_one(user)
    
    # Send welcome email in background
    if email_configured():
        welcome_html = get_welcome_email_html(user_data.name)
        background_tasks.add_task(send_email, user_data.email, "Welcome to Azories — your 3 free stories are waiting! 🐉", welcome_html)
        
        # Send admin notification for new user signup
        admin_email = os.environ.get("ADMIN_NOTIFY_EMAIL", "books@azories.com")
        admin_subject = f"🆕 New User Signup: {user_data.name}"
        admin_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🎉 New User Registered!</h1>
            </div>
            <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Name:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{user_data.name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{user_data.email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Registered:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{now_iso}</td>
                    </tr>
                </table>
                <p style="color: #6b7280; margin-top: 20px;">User has a 48-hour Pro trial active.</p>
            </div>
        </body>
        </html>
        """
        background_tasks.add_task(send_email, admin_email, admin_subject, admin_html)
        
        # Also send to backup admin
        backup_admin = os.environ.get("BACKUP_ADMIN_EMAIL")
        if backup_admin and backup_admin != admin_email:
            background_tasks.add_task(send_email, backup_admin, admin_subject, admin_html)
    
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
            trial_days_remaining=3
        )
    )

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if trial has expired
    subscription = user.get("subscription", "free")
    pro_trial = user.get("pro_trial", False)
    trial_expires = user.get("pro_trial_expires_at")
    trial_days_remaining = None
    trial_hours_remaining = None
    
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
            # Calculate time remaining
            time_remaining = expiry_date - now
            total_hours = int(time_remaining.total_seconds() / 3600)
            if total_hours >= 24:
                trial_days_remaining = time_remaining.days
            else:
                trial_hours_remaining = max(1, total_hours)  # At least 1 hour
    
    token = create_token(user["id"], user["email"], user["role"], user_data.remember_me)
    logger.info(f"Login: remember_me={user_data.remember_me} for user {user['email']}")
    is_admin_value = user.get("is_admin", False) or user.get("role") == "admin"
    logger.info(f"Login: is_admin computed as {is_admin_value} for user {user['email']}")
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
            trial_days_remaining=trial_days_remaining,
            trial_hours_remaining=trial_hours_remaining,
            is_admin=is_admin_value
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    # Check trial status
    subscription = current_user.get("subscription", "free")
    pro_trial = current_user.get("pro_trial", False)
    trial_expires = current_user.get("pro_trial_expires_at")
    trial_days_remaining = None
    trial_hours_remaining = None
    
    if pro_trial and trial_expires:
        expiry_date = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        if now > expiry_date:
            subscription = "free"
            pro_trial = False
        else:
            # Calculate time remaining
            time_remaining = expiry_date - now
            total_hours = int(time_remaining.total_seconds() / 3600)
            if total_hours >= 24:
                trial_days_remaining = time_remaining.days
            else:
                trial_hours_remaining = max(1, total_hours)  # At least 1 hour
    
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
        trial_days_remaining=trial_days_remaining,
        trial_hours_remaining=trial_hours_remaining,
        is_admin=current_user.get("is_admin", False) or current_user.get("role") == "admin"
    )


@api_router.get("/auth/ai-story-trial")
async def get_ai_story_trial_status(current_user: dict = Depends(get_current_user)):
    """Check AI Story Creator free stories status"""
    
    # Get free stories remaining (default to 3 for existing users without this field)
    free_stories_remaining = current_user.get("free_stories_remaining")
    free_stories_used = current_user.get("free_stories_used", 0)
    
    # For existing users who don't have this field, give them 3 free stories
    if free_stories_remaining is None:
        free_stories_remaining = 3 - free_stories_used
        # Update the user record
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"free_stories_remaining": free_stories_remaining, "free_stories_used": free_stories_used}}
        )
    
    has_free_stories = free_stories_remaining > 0
    
    if has_free_stories:
        return {
            "has_free_stories": True,
            "free_stories_remaining": free_stories_remaining,
            "free_stories_used": free_stories_used,
            "display_text": f"{free_stories_remaining} free stor{'y' if free_stories_remaining == 1 else 'ies'} remaining",
            # Legacy fields for backwards compatibility
            "in_trial": True,
            "trial_expired": False
        }
    else:
        return {
            "has_free_stories": False,
            "free_stories_remaining": 0,
            "free_stories_used": free_stories_used,
            "display_text": "You've used your 3 free stories! Purchase credits to keep creating — from just £5",
            # Legacy fields for backwards compatibility
            "in_trial": False,
            "trial_expired": True
        }


@api_router.get("/ai/story-pricing")
async def get_story_pricing():
    """Get credit costs for different page counts"""
    return {
        "page_credits": AI_STORY_PAGE_CREDITS,
        "free_story_pages": 5,  # Only 5-page stories are free
        "free_story_mode": "kids",  # Only Kids Mode stories are free
        "art_styles": {
            "kids": [
                {"id": "3d-pixar", "name": "3D Pixar Animation", "emoji": "🎬"},
                {"id": "watercolour", "name": "Watercolour Illustration", "emoji": "🎨"},
                {"id": "comic-book", "name": "Comic Book", "emoji": "💥"},
                {"id": "hand-drawn", "name": "Hand Drawn / Sketch", "emoji": "✏️"},
                {"id": "ideogram-storybook", "name": "Ideogram Storybook", "emoji": "📚", "badge": "NEW"},
                {"id": "ideogram-character", "name": "Ideogram Character (Consistent)", "emoji": "👤", "badge": "NEW"}
            ],
            "studio": [
                {"id": "3d-pixar", "name": "3D Pixar Animation", "emoji": "🎬"},
                {"id": "watercolour", "name": "Watercolour Illustration", "emoji": "🎨"},
                {"id": "pencil-sketch", "name": "Pencil Sketch / Hand Drawn", "emoji": "✏️"},
                {"id": "comic-book", "name": "Comic Book / Graphic Novel", "emoji": "💥"},
                {"id": "realistic", "name": "Realistic Digital Art", "emoji": "🖼️"},
                {"id": "anime", "name": "Anime / Manga", "emoji": "🎌"},
                {"id": "oil-painting", "name": "Oil Painting", "emoji": "🖌️"},
                {"id": "vintage-storybook", "name": "Vintage Storybook", "emoji": "📜"},
                {"id": "dark-fantasy", "name": "Dark Fantasy Art", "emoji": "🌙"},
                {"id": "photorealistic", "name": "Photorealistic", "emoji": "📷"},
                {"id": "ideogram-realistic", "name": "Ideogram Realistic", "emoji": "📸", "badge": "NEW"},
                {"id": "ideogram-storybook", "name": "Ideogram Storybook", "emoji": "📚", "badge": "NEW"},
                {"id": "ideogram-character", "name": "Ideogram Character (Consistent)", "emoji": "👤", "badge": "NEW"}
            ]
        },
        "age_ranges": {
            "kids": [
                {"id": "0-2", "name": "0-2 (Baby/Toddler)", "emoji": "👶"},
                {"id": "3-5", "name": "3-5 (Early Years)", "emoji": "🧒"},
                {"id": "6-8", "name": "6-8 (Early Readers)", "emoji": "📖"},
                {"id": "9-12", "name": "9-12 (Middle Grade)", "emoji": "📚"}
            ],
            "studio": [
                {"id": "13-16", "name": "13-16 (Young Adult)", "emoji": "🎭"},
                {"id": "17+", "name": "17+ (Adult Fiction)", "emoji": "📕"}
            ]
        },
        "page_options": {
            "kids": [5, 10, 15],
            "studio": [5, 10, 15, 20, 30, 50]
        },
        "genres": [
            "Adventure", "Fantasy", "Mystery", "Romance", "Sci-Fi", 
            "Horror", "Drama", "Comedy", "Thriller", "Historical"
        ]
    }


# ============ PASSWORD RESET ============

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Request a password reset email"""
    import hashlib
    
    user = await db.users.find_one({"email": request.email.lower()}, {"_id": 0})
    
    # Always return success to prevent email enumeration attacks
    if not user:
        return {"message": "If this email exists, a reset link has been sent."}
    
    # Generate reset token
    reset_token = generate_reset_token()
    expiry = get_token_expiry()
    
    # Hash token before storing (security: if DB is compromised, tokens can't be used)
    token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    
    # Store hashed reset token in database
    await db.password_resets.delete_many({"user_id": user["id"]})  # Remove old tokens
    await db.password_resets.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token_hash": token_hash,  # Store hash, not plaintext
        "expires_at": expiry.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Get app URL for reset link
    app_url = os.environ.get("APP_URL", "https://azories.com")
    reset_url = f"{app_url}/reset-password?token={reset_token}"
    
    # Send reset email (with unhashed token)
    if email_configured():
        reset_html = get_password_reset_email_html(user["name"], reset_token, reset_url)
        # Send email directly (not in background) to ensure delivery
        try:
            result = await send_email(request.email, "Reset Your Azories Password", reset_html)
            if result.get("success"):
                logger.info(f"Password reset email sent to {request.email}, email_id: {result.get('email_id')}")
            else:
                logger.error(f"Password reset email failed for {request.email}: {result.get('error')}")
        except Exception as e:
            logger.error(f"Password reset email error for {request.email}: {str(e)}")
    else:
        logger.warning(f"Email not configured - reset token for {request.email}: {reset_token}")
    
    return {"message": "If this email exists, a reset link has been sent."}

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, background_tasks: BackgroundTasks):
    """Reset password using a valid token"""
    import hashlib
    
    # Hash the incoming token to compare with stored hash
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    
    # Find the reset token by hash
    reset_record = await db.password_resets.find_one({"token_hash": token_hash}, {"_id": 0})
    
    # Fallback: check for old plaintext tokens (migration compatibility)
    if not reset_record:
        reset_record = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token has expired
    expiry = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(timezone.utc) > expiry:
        # Delete by either hash or plaintext token
        await db.password_resets.delete_one({"$or": [{"token_hash": token_hash}, {"token": request.token}]})
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
    
    # Delete used token (by hash or plaintext)
    await db.password_resets.delete_one({"$or": [{"token_hash": token_hash}, {"token": request.token}]})
    
    # Send confirmation email
    if email_configured():
        changed_html = get_password_changed_email_html(user["name"])
        background_tasks.add_task(send_email, user["email"], "Your Azories Password Has Been Changed", changed_html)
    
    logger.info(f"Password reset completed for user {user['id']}")
    return {"message": "Password has been reset successfully. You can now log in."}

@api_router.get("/auth/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verify if a password reset token is valid"""
    import hashlib
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Check hashed token first, then fallback to plaintext
    reset_record = await db.password_resets.find_one({"token_hash": token_hash}, {"_id": 0})
    if not reset_record:
        reset_record = await db.password_resets.find_one({"token": token}, {"_id": 0})
    
    if not reset_record:
        return {"valid": False, "message": "Invalid token"}
    
    expiry = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(timezone.utc) > expiry:
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

# SECURITY: /auth/make-admin endpoint removed - was a privilege escalation vulnerability

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

async def run_shots_generation_task(task_id: str, user_id: str, source_image: str, character_id: Optional[str], style: str = "realistic", character_style: Optional[str] = None):
    """Background task to generate 6 shots with specified art style"""
    try:
        from emergentintegrations.llm.openai import LlmChat, UserMessage, ImageContent
        
        TASK_STORE[task_id]["status"] = "processing"
        TASK_STORE[task_id]["progress"] = 5
        
        # Build style prompt based on selection
        style_prompts = {
            "realistic": "photorealistic, professional photography, natural lighting, high detail",
            "cinematic": "cinematic, movie still, dramatic lighting, film grain, professional color grading",
            "cartoon": "cartoon style, animated, bold colors, clean lines, expressive",
            "anime": "anime style, manga, Japanese animation, vibrant colors, detailed eyes",
            "pixar": "Pixar style, 3D animated, smooth render, family-friendly, expressive features",
            "watercolor": "watercolor painting, soft edges, artistic, painterly style, delicate colors",
            "comic": "comic book style, bold outlines, dynamic shading, graphic novel",
            "fantasy": "fantasy art style, magical, ethereal, detailed, imaginative",
            "storybook": "children's book illustration, soft colors, whimsical, gentle, friendly"
        }
        
        # Use character style if "character" is selected and available
        if style == "character" and character_style:
            selected_style = f"{character_style} style, consistent with character art style"
        else:
            selected_style = style_prompts.get(style, style_prompts["realistic"])
        
        logger.info(f"Task {task_id}: Using style: {selected_style[:50]}...")
        
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
        
        # Generate 6 shots
        shots = []
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        for i, shot_prompt in enumerate(SHOT_TYPE_PROMPTS):
            # Include the selected style in the prompt
            full_prompt = f"{base_description}, {shot_prompt}, {selected_style}, consistent lighting, high quality"
            logger.info(f"Task {task_id}: Generating shot {i+1}/9 with style...")
            
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
                        "type": f"shot_{i+1}",
                        "style": style
                    })
            except Exception as shot_error:
                logger.error(f"Task {task_id}: Error generating shot {i+1}: {str(shot_error)}")
                # Check for budget error
                if check_budget_error(str(shot_error)):
                    TASK_STORE[task_id]["status"] = "failed"
                    TASK_STORE[task_id]["error"] = "AI service budget limit reached. Please add balance to your Universal Key."
                    return
                continue
            
            TASK_STORE[task_id]["progress"] = 20 + int((i + 1) * 80 / 6)
        
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
    
    # Ensure author_name exists (AI-generated books may only have user_id)
    if not book.get("author_name"):
        book["author_name"] = ""
    
    # Ensure author_id exists
    if not book.get("author_id") and book.get("user_id"):
        book["author_id"] = book["user_id"]
    
    # Convert datetime objects to ISO strings for Pydantic
    if isinstance(book.get("created_at"), datetime):
        book["created_at"] = book["created_at"].isoformat()
    if isinstance(book.get("updated_at"), datetime):
        book["updated_at"] = book["updated_at"].isoformat()
    
    # Ensure created_at and updated_at exist
    if not book.get("created_at"):
        book["created_at"] = datetime.now(timezone.utc).isoformat()
    if not book.get("updated_at"):
        book["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    return book

async def get_book_with_counts(book: dict) -> dict:
    """Add chapter and page counts to book"""
    book = set_book_defaults(book)
    
    # First check if book has embedded pages array (AI-generated books)
    embedded_pages = book.get("pages", [])
    if embedded_pages and len(embedded_pages) > 0:
        # AI-generated book with embedded pages - count from the array
        book["chapter_count"] = 1  # AI books typically have 1 chapter
        book["total_pages"] = len(embedded_pages)
        return book
    
    # Fallback to chapters/pages collections (traditional books)
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
    # Book creation is free for all users
    
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Convert base64 images to CDN URLs for better performance
    cover_image = await convert_base64_to_cdn(book_data.cover_image or "")
    back_cover_image = await convert_base64_to_cdn(book_data.back_cover_image or "")
    
    book = {
        "id": book_id,
        "title": book_data.title,
        "description": book_data.description or "",
        "genre": book_data.genre or "General",
        "cover_image": cover_image,
        "back_cover_image": back_cover_image,
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
    # Always exclude hidden books from public library
    query["hidden"] = {"$ne": True}
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
    query = {"is_published": True, "hidden": {"$ne": True}, "$or": [{"is_featured": True}, {"is_best_of_week": True}]}
    books = await db.books.find(query, {"_id": 0}).to_list(20)
    result = []
    for book in books:
        book = await get_book_with_counts(book)
        result.append(BookResponse(**book))
    return result


@api_router.get("/books/newly-added")
async def get_newly_added_books():
    """Get books published in the last 30 days, ordered by most recent first"""
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    query = {
        "is_published": True, 
        "hidden": {"$ne": True},
        "coming_soon": {"$ne": True},
        "$or": [
            {"published_at": {"$gte": thirty_days_ago.isoformat()}},
            {"created_at": {"$gte": thirty_days_ago.isoformat()}}
        ]
    }
    
    books = await db.books.find(query, {"_id": 0}).sort("published_at", -1).to_list(20)
    
    # If no published_at, fall back to sorting by created_at
    if not books:
        query_fallback = {
            "is_published": True, 
            "hidden": {"$ne": True},
            "coming_soon": {"$ne": True},
            "created_at": {"$gte": thirty_days_ago.isoformat()}
        }
        books = await db.books.find(query_fallback, {"_id": 0}).sort("created_at", -1).to_list(20)
    
    result = []
    for book in books:
        book = await get_book_with_counts(book)
        result.append(book)
    return result


@api_router.get("/books/coming-soon")
async def get_coming_soon_books():
    """Get books marked as coming soon OR books with pending_regeneration/draft status"""
    # Include explicitly marked coming_soon books AND books being worked on
    # EXCLUDE books that are already published
    query = {
        "$or": [
            {"coming_soon": True},
            {"status": {"$in": ["pending_regeneration", "draft"]}}
        ],
        "hidden": {"$ne": True},
        "is_published": {"$ne": True}  # Exclude published books
    }
    
    books = await db.books.find(query, {"_id": 0}).sort([("coming_soon_order", 1), ("created_at", -1)]).to_list(20)
    result = []
    for book in books:
        # Add a default coming_soon_label if not set
        if not book.get("coming_soon_label"):
            if book.get("status") == "pending_regeneration":
                book["coming_soon_label"] = "Being Updated"
            elif book.get("status") == "draft":
                book["coming_soon_label"] = "In Progress"
            else:
                book["coming_soon_label"] = "Coming Soon"
        book["coming_soon"] = True  # Mark as coming soon for frontend
        book = await get_book_with_counts(book)
        result.append(book)
    return result


@api_router.put("/books/{book_id}/coming-soon")
async def set_book_coming_soon(
    book_id: str,
    coming_soon: bool = True,
    coming_soon_label: str = "Coming Soon",
    current_user: dict = Depends(get_current_user)
):
    """Mark a book as coming soon (admin only)"""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin" or user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.books.update_one(
        {"id": book_id},
        {"$set": {
            "coming_soon": coming_soon,
            "coming_soon_label": coming_soon_label,
            "is_published": False if coming_soon else True
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"success": True, "coming_soon": coming_soon}


@api_router.get("/books/my", response_model=List[BookResponse])
async def get_my_books(current_user: dict = Depends(get_current_user)):
    # Query books by author_id OR user_id (AI-generated books use user_id)
    books = await db.books.find({
        "$or": [
            {"author_id": current_user["id"]},
            {"user_id": current_user["id"]}
        ]
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    result = []
    for book in books:
        # Normalize cover_image field (AI books use cover_image_url)
        if not book.get("cover_image") and book.get("cover_image_url"):
            book["cover_image"] = book["cover_image_url"]
        # Set author_id if missing (for AI books)
        if not book.get("author_id") and book.get("user_id"):
            book["author_id"] = book["user_id"]
        # Set author_name if missing
        if not book.get("author_name"):
            book["author_name"] = current_user.get("name", "")
        # Convert datetime to ISO string if needed
        if isinstance(book.get("created_at"), datetime):
            book["created_at"] = book["created_at"].isoformat()
        if isinstance(book.get("updated_at"), datetime):
            book["updated_at"] = book["updated_at"].isoformat()
        book = await get_book_with_counts(book)
        result.append(BookResponse(**book))
    return result

@api_router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Increment view count
    await db.books.update_one({"id": book_id}, {"$inc": {"view_count": 1}})
    book["view_count"] = book.get("view_count", 0) + 1
    
    book = await get_book_with_counts(book)
    return BookResponse(**book)


@api_router.get("/books/{book_id}/full")
async def get_book_full(book_id: str):
    """Get complete book data with all pages - used for offline saving"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if book has embedded pages (AI-generated books)
    pages = book.get("pages", [])
    
    # If no embedded pages, fetch from chapters/pages collections
    if not pages or len(pages) == 0:
        chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
        for chapter in chapters:
            chapter_pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).sort("page_number", 1).to_list(100)
            pages.extend(chapter_pages)
    
    book["pages"] = pages
    book = await get_book_with_counts(book)
    
    return {
        **book,
        "pages": pages
    }


@api_router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: str, book_data: BookUpdate, current_user: dict = Depends(get_current_user)):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in book_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Convert base64 images to CDN URLs for better performance
    if "cover_image" in update_data:
        update_data["cover_image"] = await convert_base64_to_cdn(update_data["cover_image"])
    if "back_cover_image" in update_data:
        update_data["back_cover_image"] = await convert_base64_to_cdn(update_data["back_cover_image"])
    
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
    base_url = os.environ.get('FRONTEND_URL', 'https://azories.com')
    invite_link = f"{base_url}/invite/{invite_token}"
    
    return {"invite_link": invite_link, "token": invite_token}


@api_router.post("/invites/{token}/accept")
async def accept_invite(token: str, current_user: dict = Depends(get_current_user)):
    """Accept a book collaboration invite"""
    # Find the invite
    invite = await db.invites.find_one({"id": token}, {"_id": 0})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite link")
    
    if invite.get("used"):
        raise HTTPException(status_code=400, detail="This invite has already been used")
    
    # Get the book
    book = await db.books.find_one({"id": invite["book_id"]}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if user is already a collaborator or owner
    if book["author_id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="You are already the owner of this book")
    
    existing_collaborators = book.get("collaborators", [])
    if any(c["user_id"] == current_user["id"] for c in existing_collaborators):
        raise HTTPException(status_code=400, detail="You are already a collaborator on this book")
    
    # Add user as collaborator
    new_collaborator = {
        "user_id": current_user["id"],
        "email": current_user.get("email", ""),
        "name": current_user.get("name", ""),
        "role": invite.get("role", "editor"),
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.books.update_one(
        {"id": invite["book_id"]},
        {"$push": {"collaborators": new_collaborator}}
    )
    
    # Mark invite as used
    await db.invites.update_one(
        {"id": token},
        {"$set": {
            "used": True,
            "used_by": current_user["id"],
            "used_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": "Successfully joined as collaborator",
        "book_id": invite["book_id"],
        "book_title": book.get("title", "Untitled"),
        "role": invite.get("role", "editor")
    }


@api_router.get("/invites/{token}")
async def get_invite_details(token: str):
    """Get invite details (public - no auth required)"""
    invite = await db.invites.find_one({"id": token}, {"_id": 0})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite link")
    
    if invite.get("used"):
        raise HTTPException(status_code=400, detail="This invite has already been used")
    
    # Get book details
    book = await db.books.find_one({"id": invite["book_id"]}, {"_id": 0, "title": 1, "author_name": 1, "cover_image": 1})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {
        "book_title": book.get("title", "Untitled"),
        "author_name": book.get("author_name", "Unknown"),
        "cover_image": book.get("cover_image", ""),
        "role": invite.get("role", "editor")
    }


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
        "created_at": datetime.now(timezone.utc).isoformat()
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

@api_router.get("/user/image-library")
async def get_user_image_library(
    page: int = 1,
    limit: int = 50,
    book_id: Optional[str] = None,
    image_type: Optional[str] = None,  # 'character', 'scene', 'cover', etc.
    current_user: dict = Depends(get_current_user)
):
    """
    Get all images from the user's book library.
    
    This is a unified view of all images across ALL of a user's books,
    allowing easy re-use of assets in new projects.
    
    Parameters:
    - page: Page number for pagination
    - limit: Items per page (max 100)
    - book_id: Optional filter by specific book
    - image_type: Optional filter by image type (character, scene, cover, etc.)
    """
    skip = (page - 1) * limit
    limit = min(limit, 100)  # Cap at 100
    
    # Build query
    query = {"user_id": current_user["id"]}
    if book_id:
        query["book_id"] = book_id
    if image_type:
        query["type"] = image_type
    
    try:
        # Get total count
        total = await db.book_images.count_documents(query)
        
        # Get paginated images with book info
        images_cursor = db.book_images.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        images = await images_cursor.to_list(limit)
        
        # Get unique book IDs to fetch book titles
        book_ids = list(set(img.get("book_id") for img in images if img.get("book_id")))
        books = await db.books.find(
            {"id": {"$in": book_ids}},
            {"_id": 0, "id": 1, "title": 1}
        ).to_list(len(book_ids))
        book_map = {b["id"]: b["title"] for b in books}
        
        # Enrich images with book title
        for img in images:
            img["book_title"] = book_map.get(img.get("book_id"), "Unknown Book")
        
        # Get available image types for filtering
        types = await db.book_images.distinct("type", {"user_id": current_user["id"]})
        
        return {
            "images": images,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "available_types": types
        }
        
    except Exception as e:
        logger.error(f"Error fetching user image library: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch image library")


@api_router.post("/user/image-library/copy-to-book")
async def copy_image_to_book(
    source_image_id: str = Body(...),
    target_book_id: str = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Copy an image from the user's library to a specific book.
    
    Allows re-using images across different books without re-uploading.
    """
    # Verify source image belongs to user
    source_image = await db.book_images.find_one({
        "id": source_image_id,
        "user_id": current_user["id"]
    })
    
    if not source_image:
        raise HTTPException(status_code=404, detail="Source image not found")
    
    # Verify target book belongs to user or user is collaborator
    target_book = await db.books.find_one({"id": target_book_id})
    if not target_book:
        raise HTTPException(status_code=404, detail="Target book not found")
    
    is_author = target_book["author_id"] == current_user["id"]
    collaborators = target_book.get("collaborators", [])
    is_collaborator = any(c.get("user_id") == current_user["id"] for c in collaborators)
    
    if not is_author and not is_collaborator:
        raise HTTPException(status_code=403, detail="Not authorized to add images to this book")
    
    # Create new image entry for target book
    new_image = {
        "id": str(uuid.uuid4()),
        "book_id": target_book_id,
        "user_id": current_user["id"],
        "image_url": source_image["image_url"],
        "name": source_image.get("name", "Copied Image"),
        "type": source_image.get("type", "scene"),
        "style": source_image.get("style", ""),
        "metadata": {
            **source_image.get("metadata", {}),
            "copied_from": source_image_id,
            "original_book_id": source_image.get("book_id")
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.book_images.insert_one(new_image)
    new_image.pop("_id", None)
    
    return {"success": True, "image": new_image}


@api_router.post("/user/image-library/sync")
async def sync_image_library(current_user: dict = Depends(get_current_user)):
    """
    Scan ALL of the user's books and extract all images into the book_images collection.
    
    This populates the "My Library" with all images from:
    - Book pages (image_url, image_url_2, image_url_3, image_url_4)
    - Book covers (cover_image)
    - Character images from pages
    
    Skips images that are already in the library to avoid duplicates.
    """
    results = {
        "books_scanned": 0,
        "chapters_scanned": 0,
        "pages_scanned": 0,
        "images_found": 0,
        "images_added": 0,
        "images_skipped": 0,  # Already in library
        "errors": []
    }
    
    try:
        user_id = current_user["id"]
        
        # Get all user's books
        books = await db.books.find({"author_id": user_id}, {"_id": 0}).to_list(500)
        results["books_scanned"] = len(books)
        
        # Get existing image URLs to avoid duplicates
        existing_images = await db.book_images.find(
            {"user_id": user_id},
            {"image_url": 1, "_id": 0}
        ).to_list(10000)
        existing_urls = set(img.get("image_url", "") for img in existing_images)
        
        images_to_insert = []
        
        for book in books:
            book_id = book.get("id")
            book_title = book.get("title", "Unknown Book")
            
            # Extract cover image
            cover_image = book.get("cover_image", "")
            if cover_image and cover_image.startswith("http") and cover_image not in existing_urls:
                images_to_insert.append({
                    "id": str(uuid.uuid4()),
                    "book_id": book_id,
                    "user_id": user_id,
                    "image_url": cover_image,
                    "name": f"{book_title} - Cover",
                    "type": "cover",
                    "book_title": book_title,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                existing_urls.add(cover_image)
                results["images_found"] += 1
            
            # Get all chapters for this book
            chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
            results["chapters_scanned"] += len(chapters)
            
            for chapter in chapters:
                chapter_id = chapter.get("id")
                
                # Get all pages for this chapter
                pages = await db.pages.find({"chapter_id": chapter_id}, {"_id": 0}).to_list(500)
                results["pages_scanned"] += len(pages)
                
                for page in pages:
                    page_num = page.get("page_number", page.get("order", 0))
                    
                    # Extract all image URLs from the page
                    image_fields = ["image_url", "image_url_2", "image_url_3", "image_url_4"]
                    for i, field in enumerate(image_fields):
                        img_url = page.get(field, "")
                        
                        # Skip empty, base64, or already-added images
                        if not img_url or not img_url.startswith("http") or img_url in existing_urls:
                            if img_url and img_url.startswith("http") and img_url in existing_urls:
                                results["images_skipped"] += 1
                            continue
                        
                        # Determine image type based on content
                        image_type = "scene"
                        image_name = f"{book_title} - Page {page_num}"
                        if i > 0:
                            image_name += f" (Image {i+1})"
                        
                        # Check if it looks like a character image
                        if "character" in img_url.lower() or page.get("is_character_page"):
                            image_type = "character"
                        
                        images_to_insert.append({
                            "id": str(uuid.uuid4()),
                            "book_id": book_id,
                            "user_id": user_id,
                            "image_url": img_url,
                            "name": image_name,
                            "type": image_type,
                            "book_title": book_title,
                            "page_number": page_num,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                        existing_urls.add(img_url)
                        results["images_found"] += 1
        
        # Bulk insert all new images
        if images_to_insert:
            await db.book_images.insert_many(images_to_insert)
            results["images_added"] = len(images_to_insert)
        
        logger.info(f"Image library sync complete for user {user_id}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error syncing image library: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync image library: {str(e)}")


@api_router.get("/books/{book_id}/download")
async def download_book_pdf(book_id: str, current_user: dict = Depends(get_current_user)):
    """Download a book as interactive PDF (for the creator only)"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["author_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the book creator can download")


@api_router.get("/books/{book_id}/print-pdf")
async def download_printable_pdf(book_id: str, current_user: dict = Depends(get_current_user)):
    """
    Download a printable A5 booklet PDF in LANDSCAPE orientation.
    
    Layout: Each A4 LANDSCAPE page (297mm x 210mm) is split into two A5 portrait halves:
    - Left half (148.5mm x 210mm): Full illustration (fills entire half, cropped to fit)
    - Right half (148.5mm x 210mm): Story text (left-aligned, 14pt font)
    
    When printed on A4 landscape and folded in half, creates a proper A5 portrait picture book.
    
    Cost: 5 credits per download.
    """
    from reportlab.lib.pagesizes import landscape
    from reportlab.lib.units import mm
    import aiohttp
    import io
    import base64
    
    # Check credits first
    user_email = current_user.get("email", "").lower()
    is_vip = user_email in [v.lower() for v in VIP_USERS]
    is_admin = current_user.get("role") == "admin"
    
    # Credit cost for printable PDF
    PRINT_PDF_COST = 5
    
    if not is_vip and not is_admin:
        user_credits = current_user.get("credits", 0)
        if user_credits < PRINT_PDF_COST:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. You need {PRINT_PDF_COST} credits to download a printable PDF. You have {user_credits} credits."
            )
    
    # Get book
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get all pages - try direct pages first (AI books), then chapters
    pages = []
    direct_pages = book.get("pages", [])
    
    if direct_pages and len(direct_pages) > 0:
        # AI-generated books store pages directly
        for idx, p in enumerate(direct_pages):
            if not p.get("isBackCover", False):  # Skip back cover, we handle it separately
                pages.append(p)
    else:
        # Traditional books with chapters
        chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
        for chapter in chapters:
            chapter_pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).sort("order", 1).to_list(100)
            pages.extend(chapter_pages)
    
    if not pages:
        raise HTTPException(status_code=400, detail="Book has no pages to print")
    
    # Deduct credits AFTER validation but BEFORE generating PDF
    if not is_vip and not is_admin:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"credits": -PRINT_PDF_COST}}
        )
        # Log the purchase
        await db.credit_usage.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "operation": "print_pdf",
            "book_id": book_id,
            "book_title": book.get("title", "Unknown"),
            "credits_spent": PRINT_PDF_COST,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"User {current_user['id']} spent {PRINT_PDF_COST} credits for printable PDF of book {book_id}")
    
    # Helper to download image from URL
    async def fetch_image(url: str) -> PILImage.Image:
        """Fetch image from URL or base64 and return PIL Image."""
        if not url:
            return None
        
        try:
            if url.startswith("data:image"):
                # Base64 image
                img_data = url.split(",")[1]
                img_bytes = base64.b64decode(img_data)
                return PILImage.open(io.BytesIO(img_bytes))
            elif url.startswith("http"):
                # URL image
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status == 200:
                            img_bytes = await resp.read()
                            return PILImage.open(io.BytesIO(img_bytes))
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch image {url[:50]}...: {e}")
            return None
    
    # Create PDF buffer
    pdf_buffer = io.BytesIO()
    
    # A4 LANDSCAPE dimensions (297mm x 210mm)
    # When rotated to landscape: width=841.89, height=595.28
    PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)  # 841.89 x 595.28 points
    
    # Each half is 148.5mm x 210mm (A5 portrait when folded)
    HALF_WIDTH = PAGE_WIDTH / 2  # 420.94 points = 148.5mm
    HALF_HEIGHT = PAGE_HEIGHT    # 595.28 points = 210mm
    
    # Create canvas with LANDSCAPE A4
    c = canvas.Canvas(pdf_buffer, pagesize=landscape(A4))
    
    # Page margin and padding - increased for better readability
    MARGIN = 12 * mm
    TEXT_PADDING = 6 * mm
    
    # Helper to draw text with word wrap - LEFT ALIGNED, larger font
    def draw_wrapped_text_left(canvas_obj, text, x, y, max_width, max_height, font_name="Helvetica", font_size=14):
        """Draw text with word wrapping, LEFT-ALIGNED, vertically centered."""
        if not text:
            return
        
        canvas_obj.setFont(font_name, font_size)
        line_height = font_size * 1.5  # More line spacing for readability
        
        # Word wrap
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_width = canvas_obj.stringWidth(test_line, font_name, font_size)
            if text_width < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # Calculate total text height and center vertically
        total_text_height = len(lines) * line_height
        start_y = y - (max_height - total_text_height) / 2
        
        # Ensure we don't overflow
        available_lines = int(max_height / line_height)
        lines = lines[:available_lines]
        
        # Draw lines - LEFT ALIGNED
        for i, line in enumerate(lines):
            text_y = start_y - (i * line_height)
            canvas_obj.drawString(x, text_y, line)  # Left aligned at x position
    
    # Helper to draw an image FILLING the entire space with crop
    def draw_image_cover(canvas_obj, pil_img, x, y, width, height):
        """Draw image filling the entire specified area by cropping to fit (like CSS object-fit: cover)."""
        if pil_img is None:
            # Draw placeholder - purple branded background
            canvas_obj.setFillColorRGB(0.25, 0.1, 0.35)  # Dark purple
            canvas_obj.rect(x, y, width, height, fill=1, stroke=0)
            canvas_obj.setFillColorRGB(0.7, 0.6, 0.8)
            canvas_obj.setFont("Helvetica", 12)
            canvas_obj.drawCentredString(x + width/2, y + height/2, "No illustration")
            return
        
        # Convert to RGB if needed
        if pil_img.mode in ('RGBA', 'LA', 'P'):
            background = PILImage.new('RGB', pil_img.size, (255, 255, 255))
            if pil_img.mode == 'P':
                pil_img = pil_img.convert('RGBA')
            if pil_img.mode == 'RGBA':
                background.paste(pil_img, mask=pil_img.split()[-1])
            else:
                background.paste(pil_img)
            pil_img = background
        
        # Calculate crop to fill the target area (object-fit: cover)
        img_width, img_height = pil_img.size
        target_ratio = width / height  # Target aspect ratio (A5 portrait)
        img_ratio = img_width / img_height  # Source image aspect ratio
        
        if img_ratio > target_ratio:
            # Image is wider than target - crop sides
            new_width = int(img_height * target_ratio)
            left = (img_width - new_width) // 2
            pil_img = pil_img.crop((left, 0, left + new_width, img_height))
        else:
            # Image is taller than target - crop top/bottom (favor top)
            new_height = int(img_width / target_ratio)
            top = 0  # Keep the top of the image (faces are usually at top)
            pil_img = pil_img.crop((0, top, img_width, top + new_height))
        
        # Save to buffer
        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format='JPEG', quality=92)
        img_buffer.seek(0)
        
        # Draw the cropped image filling the entire area
        canvas_obj.drawImage(
            ImageReader(img_buffer), 
            x, y, 
            width=width, 
            height=height,
            preserveAspectRatio=False  # We've already cropped, so stretch to fill
        )
    
    # ======== FRONT COVER ========
    # Cover takes full A4 LANDSCAPE page, illustration on left half, title/author on right half
    cover_img = await fetch_image(book.get("cover_image", ""))
    
    # Left half: Cover illustration - FILLS ENTIRE LEFT HALF
    draw_image_cover(c, cover_img, 0, 0, HALF_WIDTH, HALF_HEIGHT)
    
    # Right half: Title and author (styled)
    c.setFillColorRGB(0.98, 0.97, 0.95)  # Cream background
    c.rect(HALF_WIDTH, 0, HALF_WIDTH, HALF_HEIGHT, fill=1, stroke=0)
    
    # Title
    c.setFillColorRGB(0.2, 0.1, 0.3)
    title = book.get("cover_title", book.get("title", "Untitled"))
    c.setFont("Helvetica-Bold", 24)
    
    # Word wrap title
    title_words = title.split()
    title_lines = []
    current_line = ""
    for word in title_words:
        test_line = current_line + (" " if current_line else "") + word
        if c.stringWidth(test_line, "Helvetica-Bold", 24) < HALF_WIDTH - 40:
            current_line = test_line
        else:
            if current_line:
                title_lines.append(current_line)
            current_line = word
    if current_line:
        title_lines.append(current_line)
    
    title_y = HALF_HEIGHT * 0.6
    for i, line in enumerate(title_lines):
        c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, title_y - i*30, line)
    
    # Subtitle if exists
    if book.get("cover_subtitle"):
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0.4, 0.3, 0.5)
        c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, title_y - len(title_lines)*30 - 15, book["cover_subtitle"])
    
    # Author
    c.setFont("Helvetica-Oblique", 14)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, HALF_HEIGHT * 0.3, f"By {book.get('author_name', 'Unknown')}")
    
    # Small Azories branding
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, 25, "Created with Azories")
    
    c.showPage()
    
    # ======== CONTENT PAGES ========
    # Each A4 LANDSCAPE page: Left half = Illustration, Right half = Text (left-aligned)
    for page_num, page in enumerate(pages):
        image_url = page.get("image_url", "")
        text_content = page.get("text_content", "") or page.get("text", "") or page.get("content", "")
        
        # Fetch image
        page_img = await fetch_image(image_url)
        
        # Left half: Illustration - FILLS ENTIRE LEFT HALF (no white space)
        draw_image_cover(c, page_img, 0, 0, HALF_WIDTH, HALF_HEIGHT)
        
        # Right half: Text content
        c.setFillColorRGB(0.99, 0.98, 0.96)  # Off-white
        c.rect(HALF_WIDTH, 0, HALF_WIDTH, HALF_HEIGHT, fill=1, stroke=0)
        
        # Text area with padding
        text_x = HALF_WIDTH + MARGIN
        text_y = HALF_HEIGHT - MARGIN - 20
        text_width = HALF_WIDTH - (2 * MARGIN)
        text_height = HALF_HEIGHT - (2 * MARGIN) - 50  # Reserve space for page number
        
        # Draw the story text - LEFT ALIGNED, 14pt font
        c.setFillColorRGB(0.15, 0.1, 0.2)
        draw_wrapped_text_left(c, text_content, text_x, text_y, text_width, text_height, "Helvetica", 14)
        
        # Page number
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, 20, f"— {page_num + 1} —")
        
        # Decorative element
        c.setStrokeColorRGB(0.8, 0.75, 0.7)
        c.setLineWidth(0.5)
        c.line(HALF_WIDTH + 40, 40, HALF_WIDTH + HALF_WIDTH - 40, 40)
        
        c.showPage()
    
    # ======== BACK COVER ========
    # Back cover: LEFT = Branded Azories purple page, RIGHT = The End + details
    
    # LEFT HALF: Branded Azories back cover (purple with branding)
    c.setFillColorRGB(0.25, 0.08, 0.38)  # Rich purple (#3F1461)
    c.rect(0, 0, HALF_WIDTH, HALF_HEIGHT, fill=1, stroke=0)
    
    # Try to load back cover image if available
    back_cover_url = book.get("back_cover_image", "")
    back_cover_img = await fetch_image(back_cover_url)
    
    if back_cover_img:
        # Draw the branded back cover image filling the space
        draw_image_cover(c, back_cover_img, 0, 0, HALF_WIDTH, HALF_HEIGHT)
    else:
        # Create a branded Azories back cover with text
        # Purple background already drawn above
        
        # "Azories" title at top
        c.setFillColorRGB(1, 1, 1)  # White
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(HALF_WIDTH/2, HALF_HEIGHT - 60, "Azories")
        
        # Tagline
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0.85, 0.8, 0.95)
        c.drawCentredString(HALF_WIDTH/2, HALF_HEIGHT - 85, "Where Stories Come to Life")
        
        # Decorative line
        c.setStrokeColorRGB(0.6, 0.4, 0.8)
        c.setLineWidth(1)
        c.line(40, HALF_HEIGHT/2 + 100, HALF_WIDTH - 40, HALF_HEIGHT/2 + 100)
        
        # Book title
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 16)
        book_title = book.get("title", "Untitled")
        c.drawCentredString(HALF_WIDTH/2, HALF_HEIGHT/2 + 70, book_title)
        
        # Author
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColorRGB(0.85, 0.8, 0.95)
        c.drawCentredString(HALF_WIDTH/2, HALF_HEIGHT/2 + 50, f"by {book.get('author_name', 'Unknown')}")
        
        # Description/summary if available
        desc = book.get("back_cover_text") or book.get("description", "")
        if desc:
            c.setFillColorRGB(0.9, 0.88, 0.95)
            c.setFont("Helvetica", 10)
            # Simple word wrap for description
            words = desc.split()
            lines = []
            current_line = ""
            for word in words:
                test = current_line + (" " if current_line else "") + word
                if c.stringWidth(test, "Helvetica", 10) < HALF_WIDTH - 50:
                    current_line = test
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            # Draw description lines
            desc_y = HALF_HEIGHT/2 + 15
            for i, line in enumerate(lines[:5]):  # Max 5 lines
                c.drawCentredString(HALF_WIDTH/2, desc_y - i*14, line)
        
        # Decorative line at bottom
        c.setStrokeColorRGB(0.6, 0.4, 0.8)
        c.line(40, 70, HALF_WIDTH - 40, 70)
        
        # Website URL at bottom
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(HALF_WIDTH/2, 45, "www.azories.com")
        
        # Small copyright
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.7, 0.65, 0.8)
        c.drawCentredString(HALF_WIDTH/2, 28, "© Azories - Digital Stories for Young Readers")
    
    # RIGHT HALF: "The End" page with details
    c.setFillColorRGB(0.98, 0.97, 0.95)  # Cream background
    c.rect(HALF_WIDTH, 0, HALF_WIDTH, HALF_HEIGHT, fill=1, stroke=0)
    
    # "The End" text - larger and more prominent
    c.setFillColorRGB(0.25, 0.15, 0.35)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, HALF_HEIGHT * 0.65, "The End")
    
    # Decorative flourish
    c.setStrokeColorRGB(0.6, 0.5, 0.7)
    c.setLineWidth(1)
    flourish_y = HALF_HEIGHT * 0.58
    c.line(HALF_WIDTH + 60, flourish_y, HALF_WIDTH + HALF_WIDTH - 60, flourish_y)
    
    # Thank you message
    c.setFont("Helvetica-Oblique", 12)
    c.setFillColorRGB(0.4, 0.35, 0.5)
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, HALF_HEIGHT * 0.48, "Thank you for reading!")
    
    # Book info
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, HALF_HEIGHT * 0.33, f'"{book.get("title", "Untitled")}"')
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, HALF_HEIGHT * 0.27, f"by {book.get('author_name', 'Unknown')}")
    
    # Azories branding at bottom
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.5, 0.4, 0.6)
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, 55, "Created with Azories")
    
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(HALF_WIDTH + HALF_WIDTH/2, 38, "www.azories.com")
    
    c.showPage()
    c.save()
    
    pdf_buffer.seek(0)
    
    # Generate filename
    safe_title = "".join(ch if ch.isalnum() or ch in " -_" else "" for ch in book.get("title", "book"))
    safe_title = safe_title.strip().replace(" ", "_")[:50]
    filename = f"{safe_title}_printable_a5_book.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
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

@api_router.get("/continue-reading")
async def get_continue_reading(current_user: dict = Depends(get_current_user)):
    """Get books the user is currently reading (in-progress, not completed)
    
    Returns book details with reading progress for "Continue Reading" section.
    Each book appears only once with the most recent reading progress.
    """
    # Use aggregation to get the most recent progress entry per book
    pipeline = [
        {
            "$match": {
                "user_id": current_user["id"],
                "completed": {"$ne": True},
                "current_page": {"$gt": 0}  # Must have started reading
            }
        },
        {
            "$sort": {"last_read": -1}  # Most recent first
        },
        {
            "$group": {
                "_id": "$book_id",  # Group by book_id to deduplicate
                "book_id": {"$first": "$book_id"},
                "current_page": {"$first": "$current_page"},
                "total_pages": {"$first": "$total_pages"},
                "progress_percent": {"$first": "$progress_percent"},
                "last_read": {"$first": "$last_read"},
                "completed": {"$first": "$completed"}
            }
        },
        {
            "$sort": {"last_read": -1}  # Sort again after grouping
        },
        {
            "$limit": 10
        }
    ]
    
    progress_list = await db.reading_progress.aggregate(pipeline).to_list(10)
    
    if not progress_list:
        return {"books": [], "total": 0}
    
    # Get book details for each in-progress book
    book_ids = [p["book_id"] for p in progress_list]
    books = await db.books.find(
        {"id": {"$in": book_ids}},
        {"_id": 0, "id": 1, "title": 1, "cover_image": 1, "author_name": 1, "genre": 1}
    ).to_list(10)
    
    # Create a lookup map
    books_map = {b["id"]: b for b in books}
    
    # Combine book details with progress
    result = []
    for progress in progress_list:
        book = books_map.get(progress["book_id"])
        if book:
            result.append({
                "book_id": book["id"],
                "title": book["title"],
                "cover_image": book.get("cover_image", ""),
                "author_name": book.get("author_name", ""),
                "genre": book.get("genre", ""),
                "current_page": progress["current_page"],
                "total_pages": progress["total_pages"],
                "progress_percent": progress.get("progress_percent", 0),
                "last_read": progress.get("last_read", "")
            })
    
    return {"books": result, "total": len(result)}

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
    """Create a new book series - free for all users"""
    
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
    series.pop("_id", None)
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

# ============ CHAPTER ROUTES ============
# Note: Admin CMS routes moved to /app/backend/routes/admin.py

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
async def get_chapters(book_id: str, response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
    
    # If no chapters exist but book has pages (AI-generated book), create a default chapter
    if not chapters:
        # Check if book has pages in the pages collection
        existing_pages = await db.pages.find({"book_id": book_id}, {"_id": 0}).to_list(1)
        if existing_pages:
            # Create default chapter for legacy AI books
            now = datetime.now(timezone.utc)
            chapter_id = str(uuid.uuid4())
            default_chapter = {
                "id": chapter_id,
                "book_id": book_id,
                "title": "Story",
                "order": 0,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            await db.chapters.insert_one({k: v for k, v in default_chapter.items() if k != "_id"})
            
            # Update all orphan pages to belong to this chapter
            await db.pages.update_many(
                {"book_id": book_id, "chapter_id": {"$exists": False}},
                {"$set": {"chapter_id": chapter_id}}
            )
            await db.pages.update_many(
                {"book_id": book_id, "chapter_id": None},
                {"$set": {"chapter_id": chapter_id}}
            )
            
            chapters = [default_chapter]
    
    return [ChapterResponse(**c) for c in chapters]

@api_router.delete("/chapters/{chapter_id}")
async def delete_chapter(chapter_id: str, current_user: dict = Depends(get_current_user)):
    chapter = await db.chapters.find_one({"id": chapter_id}, {"_id": 0})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    book = await db.books.find_one({"id": chapter["book_id"]}, {"_id": 0})
    if book["author_id"] != current_user["id"] and book.get("user_id") != current_user["id"]:
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
    if book["author_id"] != current_user["id"] and book.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    page_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    if page_data.order == 0:
        max_order = await db.pages.find_one({"chapter_id": chapter_id}, sort=[("order", -1)])
        page_data.order = (max_order["order"] + 1) if max_order else 1
    
    # Convert base64 images to CDN URLs for better performance
    image_url = await convert_base64_to_cdn(page_data.image_url or "")
    image_url_2 = await convert_base64_to_cdn(page_data.image_url_2 or "")
    image_url_3 = await convert_base64_to_cdn(page_data.image_url_3 or "")
    image_url_4 = await convert_base64_to_cdn(page_data.image_url_4 or "")
    
    page = {
        "id": page_id,
        "chapter_id": chapter_id,
        "text_content": page_data.text_content,
        "image_url": image_url,
        "image_url_2": image_url_2,
        "image_url_3": image_url_3,
        "image_url_4": image_url_4,
        "video_url": page_data.video_url or "",
        "audio_url": page_data.audio_url or "",
        "order": page_data.order,
        "layout_type": page_data.layout_type or "single",
        "created_at": now
    }
    await db.pages.insert_one(page)
    return PageResponse(**page)

@api_router.get("/chapters/{chapter_id}/pages", response_model=List[PageResponse])
async def get_pages(chapter_id: str, response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # First try to find pages by chapter_id
    pages = await db.pages.find({"chapter_id": chapter_id}, {"_id": 0}).to_list(100)
    
    # Sort by order if available, otherwise by page_number (for AI-generated books)
    pages.sort(key=lambda p: (p.get("order", 0), p.get("page_number", 0)))
    
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
        # Ensure order is set for editor compatibility
        if "order" not in page:
            page["order"] = page.get("page_number", 0)
    return [PageResponse(**p) for p in pages]

@api_router.put("/pages/{page_id}", response_model=PageResponse)
async def update_page(page_id: str, page_data: PageUpdate, current_user: dict = Depends(get_current_user)):
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    chapter = await db.chapters.find_one({"id": page["chapter_id"]}, {"_id": 0})
    book = await db.books.find_one({"id": chapter["book_id"]}, {"_id": 0})
    
    # Check authorization - allow if user is author_id OR user_id (for AI-generated books)
    if book.get("author_id") != current_user["id"] and book.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in page_data.model_dump().items() if v is not None}
    
    # Convert base64 images to CDN URLs for better performance
    image_fields = ["image_url", "image_url_2", "image_url_3", "image_url_4"]
    for field in image_fields:
        if field in update_data:
            update_data[field] = await convert_base64_to_cdn(update_data[field])
    
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
    if book["author_id"] != current_user["id"] and book.get("user_id") != current_user["id"]:
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


class PageImageGenerateRequest(BaseModel):
    """Request model for generating AI image for a specific page"""
    page_id: str
    prompt: Optional[str] = None  # If not provided, uses page text
    art_style: Optional[str] = "3d-pixar"  # Art style to use
    use_page_text: bool = True  # Whether to use page text as prompt base

@api_router.post("/ai/generate-page-image")
async def generate_page_image(request: PageImageGenerateRequest, current_user: dict = Depends(get_current_user)):
    """Generate an AI image for a specific page using FLUX Pro.
    Uses the page's text content as the prompt basis.
    """
    try:
        # Get the page
        page = await db.pages.find_one({"id": request.page_id}, {"_id": 0})
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        # Get the book - pages may have book_id directly or through chapter_id
        book = None
        book_id = page.get("book_id")
        
        if book_id:
            book = await db.books.find_one({"id": book_id}, {"_id": 0})
        
        # If no book_id, try to get it through chapter
        if not book and page.get("chapter_id"):
            chapter = await db.chapters.find_one({"id": page["chapter_id"]}, {"_id": 0})
            if chapter:
                book_id = chapter.get("book_id")
                book = await db.books.find_one({"id": book_id}, {"_id": 0})
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found for this page")
        
        if book.get("author_id") != current_user["id"] and book.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to edit this book")
        
        # Determine the prompt - enhance with better prompt engineering for accuracy
        if request.use_page_text and page.get("text_content"):
            base_text = page.get("text_content", "").strip()
            
            # Extract key visual elements from the text for better image accuracy
            # Create a structured prompt that focuses on the scene described
            if request.prompt:
                # User provided custom prompt, use it with scene context
                image_prompt = f"{request.prompt}. Scene from story: {base_text[:300]}"
            else:
                # Generate prompt from page text - be specific about visual elements
                image_prompt = f"""Create an illustration depicting this exact scene: "{base_text[:400]}"

Key requirements:
- Show the specific characters, objects, and setting described in the text
- Capture the mood and action of the scene
- Include all visual details mentioned in the text
- Make the illustration match the story moment precisely"""
        else:
            image_prompt = request.prompt or "A beautiful illustration"
        
        # Get the art style description
        art_style = request.art_style or book.get("art_style", "3d-pixar")
        style_prompts = get_style_prompts()
        style_desc = style_prompts.get(art_style, style_prompts.get("3d-pixar", ""))
        
        # Deduct credits for AI image generation (2 credits per image)
        CREDITS_PER_PAGE_IMAGE = 2
        user_credits = current_user.get("credits", 0)
        if user_credits < CREDITS_PER_PAGE_IMAGE:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. You need {CREDITS_PER_PAGE_IMAGE} credits, but have {user_credits}. Please top up your credits."
            )
        
        # Deduct credits before generation
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"credits": -CREDITS_PER_PAGE_IMAGE}}
        )
        
        # Generate the image using FLUX Pro
        if not FAL_AVAILABLE:
            # Refund credits if service not available
            await db.users.update_one(
                {"id": current_user["id"]},
                {"$inc": {"credits": CREDITS_PER_PAGE_IMAGE}}
            )
            raise HTTPException(status_code=500, detail="Image generation service not available")
        
        # Build prompt based on style - photorealistic styles need different handling
        if art_style in ["photorealistic", "realistic", "ideogram-realistic"]:
            # For photorealistic, don't add children's book language
            full_prompt = f"{image_prompt}. {style_desc}. Ultra realistic, no cartoon elements, no anime, no stylization, real photograph quality, DSLR camera, professional lighting."
        else:
            full_prompt = f"{image_prompt}. {style_desc}. High quality, detailed illustration suitable for a children's book."
        
        # Use Ideogram for styles that need better prompt adherence, FLUX Pro for others
        use_ideogram = art_style in ["ideogram-storybook", "ideogram-character", "ideogram-realistic", "storybook", "realistic", "photorealistic"]
        
        if use_ideogram:
            # Ideogram is better at following prompts accurately
            result = await generate_image_ideogram(
                prompt=full_prompt,
                model="ideogram-v3",
                aspect_ratio="4:5",  # Portrait for book pages
                style="realistic" if art_style in ["photorealistic", "realistic", "ideogram-realistic"] else "general",
                magic_prompt=True,  # Let Ideogram enhance the prompt
                print_quality=True
            )
        else:
            result = await generate_image_flux(
                prompt=full_prompt,
                model="flux-schnell",  # Use standard FLUX for cost efficiency
                image_size="portrait_4_3",
                num_images=1,
                guidance_scale=5.0,  # Increased for better prompt adherence
                num_inference_steps=4,  # Good quality
                print_quality=True  # Generate at print quality (2400x3000)
            )
        
        if not result.get("success") or not result.get("images"):
            raise HTTPException(status_code=500, detail="Image generation failed")
        
        image_data = result["images"][0]
        image_url = image_data.get("url")
        
        if not image_url:
            raise HTTPException(status_code=500, detail="No image URL in response")
        
        # Upload to Cloudinary for permanent storage
        if CLOUDINARY_AVAILABLE:
            upload_result = cloudinary.uploader.upload(
                image_url,
                folder="azories/story_pages"
            )
            final_url = upload_result.get("secure_url")
        else:
            final_url = image_url
        
        # Update the page with the new image
        await db.pages.update_one(
            {"id": request.page_id},
            {"$set": {
                "image_url": final_url,
                "image_prompt": image_prompt,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        return {
            "success": True,
            "image_url": final_url,
            "prompt_used": full_prompt[:200]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating page image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")


# Credit cost for AI text enhancement
CREDITS_PER_TEXT_ENHANCE = 2

class TextEnhanceRequest(BaseModel):
    """Request model for AI text enhancement"""
    text: str
    style: Optional[str] = "children"  # "children", "young_adult", "adult"
    preserve_names: bool = True  # Keep character names unchanged

@api_router.post("/ai/enhance-text")
async def enhance_text(request: TextEnhanceRequest, current_user: dict = Depends(get_current_user)):
    """Enhance user's text with AI to make it more polished and author-quality.
    
    Takes raw user text and improves grammar, flow, vocabulary while preserving
    the original meaning and story events.
    
    Cost: 1 credit per enhancement
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="No text provided to enhance")
        
        # Check user has enough credits
        user_credits = current_user.get("credits", 0)
        if user_credits < CREDITS_PER_TEXT_ENHANCE:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. Need {CREDITS_PER_TEXT_ENHANCE} credit(s), have {user_credits}"
            )
        
        # Deduct credits first
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"credits": -CREDITS_PER_TEXT_ENHANCE}}
        )
        
        # Determine writing style based on audience
        style_instructions = {
            "children": "Write for children aged 4-8. Use simple, clear language. Short sentences. Vivid but simple descriptions. Keep it warm, friendly, and magical.",
            "young_adult": "Write for young adults aged 12-18. More sophisticated vocabulary. Can include mild tension or drama. Engaging prose with good pacing.",
            "adult": "Write for adults. Rich, literary prose. Sophisticated vocabulary and sentence structure. Can be more nuanced and complex."
        }
        
        style_guide = style_instructions.get(request.style, style_instructions["children"])
        
        # Create the enhancement prompt
        system_prompt = f"""You are a professional children's book author and editor. Your task is to take the user's draft text and polish it into professional, publication-ready prose.

STYLE GUIDE:
{style_guide}

RULES:
1. PRESERVE the original story events, characters, and meaning exactly
2. IMPROVE grammar, sentence flow, and word choice
3. ADD vivid sensory details where appropriate
4. MAINTAIN the author's voice - enhance, don't replace
5. Keep the same approximate length (within 20%)
6. {"Keep all character names exactly as written" if request.preserve_names else "You may suggest better character names"}
7. Make it sound like a professionally published book

Return ONLY the enhanced text, nothing else. No explanations or commentary."""

        user_prompt = f"Please enhance this text:\n\n{request.text}"
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            chat = LlmChat(
                api_key=os.environ.get("EMERGENT_LLM_KEY"),
                session_id=f"enhance-{current_user['id']}-{str(uuid.uuid4())[:8]}",
                system_message=system_prompt
            ).with_model("openai", "gpt-4o-mini")  # Fast and cost-effective
            
            response = await chat.send_message(UserMessage(text=user_prompt))
            
            enhanced_text = response.strip() if response else ""
            
            if not enhanced_text:
                # Refund credits if enhancement failed
                await db.users.update_one(
                    {"id": current_user["id"]},
                    {"$inc": {"credits": CREDITS_PER_TEXT_ENHANCE}}
                )
                raise HTTPException(status_code=500, detail="AI enhancement returned empty result")
            
            return {
                "success": True,
                "original_text": request.text,
                "enhanced_text": enhanced_text,
                "credits_used": CREDITS_PER_TEXT_ENHANCE,
                "style": request.style
            }
            
        except ImportError:
            # Refund credits
            await db.users.update_one(
                {"id": current_user["id"]},
                {"$inc": {"credits": CREDITS_PER_TEXT_ENHANCE}}
            )
            raise HTTPException(status_code=500, detail="AI text enhancement not available")
            
    except HTTPException:
        raise
    except Exception as e:
        # Refund credits on error
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"credits": CREDITS_PER_TEXT_ENHANCE}}
        )
        logger.error(f"Error enhancing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enhancing text: {str(e)}")



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
    "looking upward, low angle perspective",
    "over the shoulder view, back partially visible"
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
        if not thumbnail and has_description:
            gen_prompt = f"{request.description_prompt}, {style_info.get('name', '')} style, character portrait, detailed face"
            
            # Try fal.ai first
            if FAL_AVAILABLE:
                try:
                    result = await generate_image_flux(
                        prompt=gen_prompt,
                        model="flux-schnell",
                        image_size="square_hd",
                        num_images=1
                    )
                    if result.get("images"):
                        thumbnail = result["images"][0].get("url")
                        logger.info("Generated thumbnail via fal.ai for character")
                except Exception as e:
                    logger.warning(f"fal.ai thumbnail generation failed: {e}")
            
            # Fallback to OpenAI if fal.ai failed or unavailable
            if not thumbnail and EMERGENT_LLM_KEY:
                try:
                    logger.info("Attempting thumbnail generation via OpenAI fallback")
                    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
                    images = await image_gen.generate_images(
                        prompt=gen_prompt,
                        model="gpt-image-1",
                        number_of_images=1
                    )
                    if images and len(images) > 0:
                        image_base64 = base64.b64encode(images[0]).decode('utf-8')
                        thumbnail = f"data:image/png;base64,{image_base64}"
                        logger.info("Generated thumbnail via OpenAI fallback for character")
                except Exception as e:
                    logger.warning(f"OpenAI thumbnail generation also failed: {e}")
        
        # Create character record
        char_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Convert any base64 reference images to CDN URLs for better performance
        converted_reference_images = []
        for img in (request.reference_images[:20] if request.reference_images else []):
            converted_url = await convert_base64_to_cdn(img)
            converted_reference_images.append(converted_url)
        
        # Also convert thumbnail if it's base64
        converted_thumbnail = await convert_base64_to_cdn(thumbnail) if thumbnail else None
        
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
            "reference_images": converted_reference_images,
            "thumbnail": converted_thumbnail,
            "created_at": now,
            "updated_at": now
        }
        
        # If we generated a thumbnail but have no reference images, 
        # add the thumbnail as the first reference image (enables PuLID later)
        if converted_thumbnail and not character.get("reference_images"):
            character["reference_images"] = [converted_thumbnail]
        
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
            model="flux-schnell",
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
        "reference_images": ref_images,
        "reference_images_count": len(ref_images),
        "can_train_lora": can_train_lora,
        "message": f"Reference image added. {len(ref_images)}/3 images for LoRA training." if len(ref_images) < 3 else "You can now train a LoRA model for this character!"
    }

@api_router.post("/pro-studio/characters/{character_id}/remove-reference")
async def remove_reference_image(character_id: str, request: dict, current_user: dict = Depends(get_current_user)):
    """Remove an image from a character's reference images
    
    This allows users to remove unwanted reference images from their collection.
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
    
    # Remove from reference images
    ref_images = character.get("reference_images", [])
    if image_url in ref_images:
        ref_images.remove(image_url)
        
        await db.pro_studio_characters.update_one(
            {"id": character_id},
            {"$set": {
                "reference_images": ref_images,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    return {
        "success": True,
        "reference_images": ref_images,
        "reference_images_count": len(ref_images),
        "can_train_lora": len(ref_images) >= 3
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
                model="flux-schnell",
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
                    model="flux-schnell",
                    image_size="landscape_16_9",
                    num_images=1
                )
                if result.get("images"):
                    thumbnail = result["images"][0].get("url")
            except Exception as thumb_err:
                logger.warning(f"Could not generate scene thumbnail: {thumb_err}")
        
        scene_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Convert any base64 reference images to CDN URLs
        converted_reference_images = []
        for img in (request.reference_images[:10] if request.reference_images else []):
            converted_url = await convert_base64_to_cdn(img)
            converted_reference_images.append(converted_url)
        
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
            "reference_images": converted_reference_images,
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
    
    update_data = {k: v for k, v in request.model_dump().items() if v is not None and k != 'add_reference_images'}
    
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
                model="flux-schnell",
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
    """Generate a hero frame with Cinema Studio settings - uses PuLID for character consistency"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=500, detail="fal.ai service not configured")
    
    # Deduct credits
    if not await deduct_credits(current_user["id"], "pulid_generate"):
        credits_needed = CREDIT_COSTS.get("pulid_generate", 3)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Image generation requires {credits_needed} credits.")
    
    # Art style mapping
    ART_STYLE_PROMPTS = {
        "realistic": "photorealistic, professional photography, natural lighting, high detail",
        "cinematic": "cinematic, movie still, dramatic lighting, film grain, professional color grading",
        "cartoon": "cartoon style, animated, bold colors, clean lines, expressive",
        "anime": "anime style, manga, Japanese animation, vibrant colors, detailed eyes",
        "pixar": "Pixar style, 3D animated, smooth render, family-friendly, expressive features",
        "watercolor": "watercolor painting, soft edges, artistic, painterly style, delicate colors",
        "comic": "comic book style, bold outlines, dynamic shading, graphic novel",
        "fantasy": "fantasy art style, magical, ethereal, detailed, imaginative",
        "storybook": "children's book illustration, soft colors, whimsical, gentle, friendly"
    }
    
    try:
        # Build full prompt with cinema settings
        prompt_parts = [request.prompt]
        
        # Check if character has reference image for PuLID
        reference_image = None
        character = None
        if request.character_id:
            character = await db.pro_studio_characters.find_one(
                {"id": request.character_id, "user_id": current_user["id"]},
                {"_id": 0}
            )
            if character:
                if character.get("description"):
                    prompt_parts.insert(0, character["description"])
                # Get reference image for PuLID
                reference_image = character.get("thumbnail_url") or (character.get("reference_images", [None])[0] if character.get("reference_images") else None)
        
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
        
        # Add art style
        art_style_prompt = ART_STYLE_PROMPTS.get(request.art_style, ART_STYLE_PROMPTS["cinematic"])
        prompt_parts.append(art_style_prompt)
        
        # Add quality enhancers
        prompt_parts.append("professional photography, 8K resolution, masterfully composed")
        
        full_prompt = ", ".join(prompt_parts)
        
        # Determine size based on aspect ratio
        aspect_to_fal_size = {
            "1:1": "square",
            "16:9": "landscape_16_9",
            "9:16": "portrait_9_16",
            "4:3": "landscape_4_3",
            "3:4": "portrait_4_3",
            "21:9": "landscape_16_9",  # closest match
            "2:3": "portrait_4_3"  # closest match
        }
        image_size = aspect_to_fal_size.get(request.aspect_ratio, "landscape_16_9")
        
        # Use PuLID if character has reference image, otherwise use FLUX
        if reference_image:
            # PuLID for character consistency
            result = await generate_with_face_id(
                prompt=full_prompt,
                reference_image_url=reference_image,
                id_weight=1.0,
                image_size=image_size,
                mode="fidelity",
                character_appearance=character.get("appearance", "") if character else "",
                art_style=request.art_style
            )
            
            if result.get("success") and result.get("images"):
                image_url = result["images"][0].get("url")
                
                # Upload to Cloudinary
                if image_url and CLOUDINARY_AVAILABLE:
                    upload_result = cloudinary.uploader.upload(
                        image_url,
                        folder=f"azories/pro_studio/{current_user['id']}/images"
                    )
                    image_url = upload_result.get("secure_url", image_url)
                
                return {"image_url": image_url, "success": True, "method": "pulid"}
        else:
            # Use FLUX-dev for better quality (Pro Studio is paid)
            result = await generate_image_flux(
                prompt=full_prompt,
                model="flux-dev",  # Use better quality model for paid Pro Studio
                image_size=image_size,
                num_images=1,
                guidance_scale=4.0,
                num_inference_steps=25
            )
            
            if result.get("success") and result.get("images"):
                image_url = result["images"][0].get("url")
                
                # Upload to Cloudinary
                if image_url and CLOUDINARY_AVAILABLE:
                    upload_result = cloudinary.uploader.upload(
                        image_url,
                        folder=f"azories/pro_studio/{current_user['id']}/images"
                    )
                    image_url = upload_result.get("secure_url", image_url)
                
                return {"image_url": image_url, "success": True, "method": "flux-dev"}
        
        raise HTTPException(status_code=500, detail="No image was generated")
            
    except HTTPException:
        raise
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
    art_style: Optional[str] = "cinematic"  # Art style for generation

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
        
        # Art style mapping
        ART_STYLE_PROMPTS = {
            "realistic": "photorealistic, professional photography, natural lighting, high detail",
            "cinematic": "cinematic, movie still, dramatic lighting, film grain, professional color grading",
            "cartoon": "cartoon style, animated, bold colors, clean lines, expressive",
            "anime": "anime style, manga, Japanese animation, vibrant colors, detailed eyes",
            "pixar": "Pixar style, 3D animated, smooth render, family-friendly, expressive features",
            "watercolor": "watercolor painting, soft edges, artistic, painterly style, delicate colors",
            "comic": "comic book style, bold outlines, dynamic shading, graphic novel",
            "fantasy": "fantasy art style, magical, ethereal, detailed, imaginative",
            "storybook": "children's book illustration, soft colors, whimsical, gentle, friendly"
        }
        
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
        
        # Add art style
        art_style_prompt = ART_STYLE_PROMPTS.get(request.art_style, ART_STYLE_PROMPTS["cinematic"])
        prompt_parts.append(art_style_prompt)
        
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
        request.character_id,
        request.style or "realistic",
        request.character_style
    )
    
    # Return task ID immediately (HTTP 202 Accepted)
    return {"task_id": task_id, "status": "pending", "message": "Shots generation started. Poll /api/tasks/{task_id} for status."}

@api_router.post("/pro-studio/generate-expression")
async def generate_expression(request: GenerateExpressionRequest, current_user: dict = Depends(get_current_user)):
    """Generate character with a specific expression using PuLID for consistency"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=500, detail="fal.ai service not configured")
    
    # Deduct credits
    if not await deduct_credits(current_user["id"], "expression_generate"):
        credits_needed = CREDIT_COSTS.get("expression_generate", 2)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Expression generation requires {credits_needed} credits.")
    
    try:
        # Get character
        character = await db.pro_studio_characters.find_one(
            {"id": request.character_id, "user_id": current_user["id"]},
            {"_id": 0}
        )
        
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Get reference image for PuLID (use thumbnail or first reference)
        reference_image = character.get("thumbnail_url") or (character.get("reference_images", [None])[0] if character.get("reference_images") else None)
        
        if not reference_image:
            raise HTTPException(status_code=400, detail="Character needs a reference image for expression generation")
        
        # Build prompt with expression
        expression_desc = EXPRESSION_PROMPTS.get(request.expression, "neutral expression")
        
        prompt_parts = [
            character.get("description", f"Portrait of {character['name']}"),
            expression_desc,
            request.base_prompt if request.base_prompt else "",
            "professional portrait photography, high quality, consistent appearance, same person"
        ]
        
        full_prompt = ", ".join(filter(None, prompt_parts))
        
        # Use PuLID for face consistency
        result = await generate_with_face_id(
            prompt=full_prompt,
            reference_image_url=reference_image,
            id_weight=1.0,  # High weight for strong consistency
            image_size="square",  # Good for portraits
            mode="fidelity",
            character_appearance=character.get("appearance", ""),
            art_style=character.get("art_style", "realistic")
        )
        
        if result.get("success") and result.get("images"):
            image_url = result["images"][0].get("url")
            
            # Upload to Cloudinary for permanent storage
            if image_url and CLOUDINARY_AVAILABLE:
                upload_result = cloudinary.uploader.upload(
                    image_url,
                    folder=f"azories/pro_studio/{current_user['id']}/expressions"
                )
                image_url = upload_result.get("secure_url", image_url)
            
            return {"image_url": image_url, "success": True, "expression": request.expression, "method": "pulid"}
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating expression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating expression: {str(e)}")

@api_router.post("/pro-studio/animate-hero")
async def animate_hero_frame(request: AnimateHeroRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Animate a hero frame to video using multiple models - returns task_id for polling"""
    if current_user.get("subscription", "free") != "pro" and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    # Credits check for video generation
    if not await deduct_credits(current_user["id"], "video_generate"):
        credits_needed = CREDIT_COSTS.get("video_generate", 10)
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Video generation requires {credits_needed} credits.")
    
    # Check which video generation service is available for the requested model
    model = request.model.lower()
    
    # Veo 3.1 uses Google's API
    if model in ("veo-3.1", "veo-3", "veo3"):
        if not VEO3_AVAILABLE:
            raise HTTPException(status_code=503, detail="Veo 3.1 video service not available (Google API key not configured)")
    else:
        # Other models (sora-2, kling) use fal.ai
        if not FAL_AVAILABLE:
            raise HTTPException(status_code=503, detail="Video generation service not available (fal.ai not configured)")
    
    # Create task and return immediately
    task_id = str(uuid.uuid4())
    TASK_STORE[task_id] = {
        "status": "pending",
        "user_id": current_user["id"],
        "type": "video",
        "model": model,
        "created_at": datetime.now(timezone.utc),
        "progress": 0,
        "result": None,
        "error": None
    }
    
    logger.info(f"Video generation task {task_id} created for user {current_user['id']} with model {model}")
    
    # Start background task
    background_tasks.add_task(
        run_video_generation_task,
        task_id,
        current_user["id"],
        request.image_url,
        request.motion_prompt,
        request.duration,
        model
    )
    
    return {"task_id": task_id, "status": "pending", "message": f"Video generation started with {model}. Poll /api/tasks/{task_id} for status."}

async def run_video_generation_task(task_id: str, user_id: str, image_url: str, motion_prompt: str, duration: int, model: str = "kling"):
    """Background task to generate video with multiple model support"""
    try:
        TASK_STORE[task_id]["status"] = "processing"
        TASK_STORE[task_id]["progress"] = 10
        
        result = None
        
        # Route to correct video generation service based on model
        if model in ("veo-3.1", "veo-3", "veo3"):
            # Use Google Veo 3.1
            logger.info(f"Task {task_id}: Starting Veo 3.1 video generation")
            TASK_STORE[task_id]["progress"] = 20
            
            # Veo 3.1 is text-to-video, so we need to describe the scene
            # Combine the motion prompt with scene description
            full_prompt = motion_prompt or "cinematic shot with subtle natural movement"
            if "movement" not in full_prompt.lower() and "motion" not in full_prompt.lower():
                full_prompt = f"{full_prompt}, smooth cinematic movement"
            
            result = await generate_video_with_veo3(
                prompt=full_prompt,
                duration_seconds=min(duration, 8),  # Veo 3.1 max is 8 seconds
                aspect_ratio="16:9"
            )
        else:
            # Use fal.ai (Kling or other models)
            logger.info(f"Task {task_id}: Starting {model} video generation via fal.ai")
            
            result = await generate_video_from_image(
                image_url=image_url,
                prompt=motion_prompt or "gentle breathing, subtle natural movement, soft hair motion",
                duration=min(duration, 10),
                aspect_ratio="16:9",
                model=model if model != "sora-2" else "kling"  # Map sora-2 to kling for now
            )
        
        TASK_STORE[task_id]["progress"] = 90
        
        if result and result.get("success") and result.get("video_url"):
            TASK_STORE[task_id]["status"] = "completed"
            TASK_STORE[task_id]["result"] = {
                "video_url": result["video_url"],
                "model": result.get("model", model)
            }
            TASK_STORE[task_id]["progress"] = 100
            logger.info(f"Task {task_id}: Video generation completed with {model}")
        else:
            error_msg = result.get("error", "No video URL returned") if result else "No result from video service"
            TASK_STORE[task_id]["status"] = "failed"
            TASK_STORE[task_id]["error"] = error_msg
            logger.error(f"Task {task_id}: {error_msg}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task {task_id}: Video generation failed: {error_msg}")
        TASK_STORE[task_id]["status"] = "failed"
        TASK_STORE[task_id]["error"] = f"Video generation failed: {error_msg}"

# ==================== FAL.AI CHARACTER CONSISTENCY ENDPOINTS ====================

@api_router.get("/fal/models")
async def get_fal_available_models():
    """Get list of available fal.ai models and key status"""
    if not FAL_AVAILABLE:
        return {"models": [], "available": False, "message": "fal.ai not configured"}
    
    # Include key validity status
    fal_status = get_fal_key_status() if get_fal_key_status else {}
    key_valid = fal_status.get("valid", None)
    
    return {
        "models": get_fal_models(), 
        "available": True,
        "key_valid": key_valid,
        "key_error": fal_status.get("error_message") if key_valid is False else None
    }

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
            
            # If reference image is base64, convert to CDN URL for PuLID
            if ref_image.startswith('data:image'):
                logger.info("Converting base64 reference image to CDN URL for PuLID...")
                ref_image = await convert_base64_to_cdn(ref_image)
                # Update character with CDN URL to avoid future conversions
                await db.pro_studio_characters.update_one(
                    {"id": character_id},
                    {"$set": {"reference_images.0": ref_image}}
                )
            
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


# ==================== ASYNC STORY GENERATION SYSTEM ====================

async def update_job_status(job_id: str, updates: dict):
    """Update job status in both memory and database"""
    updates["updated_at"] = datetime.now(timezone.utc)
    
    if job_id in STORY_JOBS:
        STORY_JOBS[job_id].update(updates)
    
    await db.story_jobs.update_one(
        {"job_id": job_id},
        {"$set": updates}
    )

async def send_story_ready_email(user_email: str, user_name: str, book_title: str, book_id: str):
    """Send email notification when story is ready"""
    try:
        if not RESEND_API_KEY:
            logger.warning("Resend API key not configured, skipping email notification")
            return
        
        import resend
        resend.api_key = RESEND_API_KEY
        
        book_url = f"https://azories.com/read/{book_id}"
        
        html_content = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #7c3aed; margin: 0;">Your Story is Ready! 🐉</h1>
            </div>
            
            <p style="font-size: 16px; color: #333;">Hi {user_name or 'there'},</p>
            
            <p style="font-size: 16px; color: #333;">
                Great news! Azora has finished creating your story <strong>"{book_title}"</strong>!
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{book_url}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #ec4899); color: white; padding: 15px 30px; text-decoration: none; border-radius: 30px; font-weight: bold; font-size: 16px;">
                    📚 Read Your Story Now
                </a>
            </div>
            
            <p style="font-size: 14px; color: #666;">
                Your book is waiting in your library, complete with beautiful illustrations!
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="font-size: 12px; color: #999; text-align: center;">
                Happy reading! 📖<br>
                The Azories Team
            </p>
        </div>
        """
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: resend.Emails.send({
                "from": "Azories <stories@azories.com>",
                "to": user_email,
                "subject": f"🐉 Your story \"{book_title}\" is ready!",
                "html": html_content
            })
        )
        logger.info(f"Story ready email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send story ready email: {e}")

async def run_story_generation_job(job_id: str, request_data: dict, user_data: dict):
    """Background worker for story generation"""
    try:
        logger.info(f"Starting story generation job {job_id}")
        
        # Update status to generating story
        await update_job_status(job_id, {
            "status": StoryJobStatus.GENERATING_STORY.value,
            "current_step": "Azora is writing your story...",
            "progress_percent": 5
        })
        
        # Reconstruct request from data
        request = AIStoryRequest(**request_data)
        num_pages = request.num_pages
        
        # Initialize images status
        images_status = {str(i): "pending" for i in range(1, num_pages + 1)}
        await update_job_status(job_id, {"images_status": images_status, "total_pages": num_pages})
        
        # ============ STEP 1: Generate Story Text ============
        try:
            story_data = await generate_story_text(request, user_data)
            
            await update_job_status(job_id, {
                "story_text_done": True,
                "current_step": "Story written! Now creating illustrations...",
                "progress_percent": 20
            })
            logger.info(f"Job {job_id}: Story text generated successfully")
        except Exception as e:
            logger.error(f"Job {job_id}: Story text generation failed: {e}")
            await update_job_status(job_id, {
                "status": StoryJobStatus.FAILED.value,
                "error_message": f"Failed to generate story: {str(e)}",
                "current_step": "Story generation failed"
            })
            # Refund credits
            await refund_story_credits(user_data["id"], num_pages)
            return
        
        # ============ STEP 2: Create Book in Database ============
        book_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Use the selected art style
        selected_style = request.art_style or request.image_style or "3d-pixar"
        style_prompts = get_style_prompts()
        style_desc = style_prompts.get(selected_style, style_prompts["3d-pixar"])
        
        # Create default chapter for AI story (required for BookEditor compatibility)
        chapter_id = str(uuid.uuid4())
        default_chapter = {
            "id": chapter_id,
            "book_id": book_id,
            "title": "Story",
            "order": 0,
            "created_at": now,
            "updated_at": now
        }
        await db.chapters.insert_one({k: v for k, v in default_chapter.items() if k != "_id"})
        
        # Create book document with all required fields for compatibility
        book = {
            "id": book_id,
            "user_id": user_data["id"],
            "author_id": user_data["id"],  # Also set author_id for My Books compatibility
            "author_name": user_data.get("name", ""),
            "title": story_data.get("title", "Untitled Story"),
            "cover_title": story_data.get("title", "Untitled Story"),  # Store title for cover display
            "description": story_data.get("description", ""),
            "back_cover_text": story_data.get("back_cover_text", ""),
            "main_character_description": story_data.get("main_character_description", ""),
            "genre": request.genre,
            "age_rating": request.age_range,
            "art_style": selected_style,
            "is_published": False,
            "status": "generating",  # Mark as generating until images done
            "created_at": now,
            "updated_at": now,
            "generation_job_id": job_id,
            "cover_image": "",  # Will be populated after cover generation
            "back_cover_image": "",
            "ai_generated": True,  # Flag to identify AI-generated stories
            "default_chapter_id": chapter_id,  # Reference to the default chapter
        }
        
        await db.books.insert_one({k: v for k, v in book.items() if k != "_id"})
        
        await update_job_status(job_id, {
            "book_id": book_id,
            "current_step": "Book created, generating cover...",
            "progress_percent": 25
        })
        
        # ============ STEP 3: Generate Cover Image ============
        try:
            book_title = story_data.get('title', 'Story')
            cover_prompt = f"Children's book cover design with the title '{book_title}' prominently displayed. {story_data.get('main_character_description', '')}. {style_desc}. Professional book cover layout with title text at the top, eye-catching illustration, appealing to readers, centered composition."
            
            cover_url = await generate_single_image(cover_prompt, style_desc)
            
            # Store in both fields for compatibility (cover_image for BookResponse, cover_image_url for legacy)
            await db.books.update_one(
                {"id": book_id},
                {"$set": {
                    "cover_image_url": cover_url,
                    "cover_image": cover_url,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            await update_job_status(job_id, {
                "current_step": "Cover done! Creating page illustrations...",
                "progress_percent": 30
            })
        except Exception as e:
            logger.warning(f"Job {job_id}: Cover generation failed: {e}")
            # Continue without cover
        
        # ============ STEP 4: Generate Page Images ============
        pages = story_data.get("pages", [])
        total_pages = len(pages)
        images_completed = 0
        failed_pages = []
        
        # Calculate progress per page (from 30% to 95%)
        progress_per_page = 65 / total_pages if total_pages > 0 else 0
        
        for page in pages:
            page_num = page.get("page_number", 0)
            
            # Update status for this page
            images_status[str(page_num)] = "generating"
            await update_job_status(job_id, {
                "images_status": images_status,
                "current_step": f"Creating illustration for page {page_num} of {total_pages}..."
            })
            
            try:
                # Generate image for this page
                image_prompt = page.get("image_prompt", "")
                if not image_prompt:
                    image_prompt = f"Illustration for: {page.get('text', '')[:100]}"
                
                # Add character and style to prompt
                char_desc = story_data.get("main_character_description", "")
                full_prompt = f"{image_prompt}. {char_desc}. {style_desc}"
                
                image_url = await generate_single_image(full_prompt, style_desc)
                
                # Create page document
                page_doc = {
                    "id": str(uuid.uuid4()),
                    "book_id": book_id,
                    "chapter_id": chapter_id,  # Link to the default chapter for editor compatibility
                    "page_number": page_num,
                    "text_content": page.get("text", ""),
                    "image_url": image_url,
                    "image_prompt": image_prompt,
                    "chapter_title": page.get("chapter_title"),
                    "created_at": now,
                    "updated_at": now
                }
                
                await db.pages.insert_one({k: v for k, v in page_doc.items() if k != "_id"})
                
                images_status[str(page_num)] = "done"
                images_completed += 1
                
                # Update progress
                current_progress = 30 + (images_completed * progress_per_page)
                await update_job_status(job_id, {
                    "images_status": images_status,
                    "pages_completed": images_completed,
                    "progress_percent": int(current_progress)
                })
                
                logger.info(f"Job {job_id}: Page {page_num}/{total_pages} completed")
                
            except Exception as e:
                logger.error(f"Job {job_id}: Page {page_num} image failed: {e}")
                images_status[str(page_num)] = "failed"
                failed_pages.append(page_num)
                
                # Still create page with placeholder
                page_doc = {
                    "id": str(uuid.uuid4()),
                    "book_id": book_id,
                    "chapter_id": chapter_id,  # Link to the default chapter for editor compatibility
                    "page_number": page_num,
                    "text_content": page.get("text", ""),
                    "image_url": None,  # No image
                    "image_prompt": page.get("image_prompt", ""),
                    "image_failed": True,
                    "created_at": now,
                    "updated_at": now
                }
                await db.pages.insert_one({k: v for k, v in page_doc.items() if k != "_id"})
                
                images_completed += 1
                current_progress = 30 + (images_completed * progress_per_page)
                await update_job_status(job_id, {
                    "images_status": images_status,
                    "pages_completed": images_completed,
                    "progress_percent": int(current_progress)
                })
        
        # ============ STEP 5: Finalize ============
        # Update book status
        final_status = "draft" if failed_pages else "draft"  # Book is ready
        await db.books.update_one(
            {"id": book_id},
            {"$set": {"status": final_status, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Handle partial completion
        if failed_pages:
            # Refund credits for failed pages
            failed_count = len(failed_pages)
            credits_per_page = AI_STORY_PAGE_CREDITS.get(num_pages, 5) / num_pages
            refund_amount = int(failed_count * credits_per_page)
            
            if refund_amount > 0:
                await db.users.update_one(
                    {"id": user_data["id"]},
                    {"$inc": {"credits": refund_amount}}
                )
                logger.info(f"Job {job_id}: Refunded {refund_amount} credits for {failed_count} failed pages")
            
            await update_job_status(job_id, {
                "status": StoryJobStatus.PARTIAL.value,
                "current_step": f"Story complete! {len(failed_pages)} images failed.",
                "progress_percent": 100,
                "completed_at": datetime.now(timezone.utc),
                "error_message": f"Some illustrations couldn't be generated. Refunded {refund_amount} credits."
            })
        else:
            await update_job_status(job_id, {
                "status": StoryJobStatus.COMPLETED.value,
                "current_step": "Your story is ready! 🎉",
                "progress_percent": 100,
                "completed_at": datetime.now(timezone.utc)
            })
        
        # Send email notification
        await send_story_ready_email(
            user_data.get("email", ""),
            user_data.get("name", ""),
            story_data.get("title", "Your Story"),
            book_id
        )
        
        logger.info(f"Job {job_id}: Story generation completed. Book ID: {book_id}")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Unexpected error: {e}")
        await update_job_status(job_id, {
            "status": StoryJobStatus.FAILED.value,
            "error_message": f"Unexpected error: {str(e)}",
            "current_step": "Generation failed"
        })
        # Refund all credits
        await refund_story_credits(user_data["id"], request_data.get("num_pages", 5))

async def refund_story_credits(user_id: str, num_pages: int):
    """Refund credits for a failed story generation"""
    credits_to_refund = AI_STORY_PAGE_CREDITS.get(num_pages, 5)
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"credits": credits_to_refund}}
    )
    logger.info(f"Refunded {credits_to_refund} credits to user {user_id}")

def get_style_prompts():
    """Get style prompt mappings"""
    return {
        "3d-pixar": "Pixar 3D animation style, Disney quality, vibrant colors, expressive characters, magical lighting, cinematic composition",
        "pixar": "Pixar 3D animation style, Disney quality, vibrant colors, expressive characters, magical lighting, cinematic composition",
        "watercolour": "Soft watercolor illustration, gentle colors, dreamy atmosphere, hand-painted feel, children's book quality",
        "watercolor": "Soft watercolor illustration, gentle colors, dreamy atmosphere, hand-painted feel",
        "pencil-sketch": "Pencil sketch illustration, hand-drawn feel, artistic linework, detailed textures, warm and inviting",
        "hand-drawn": "Hand-drawn illustration, artistic linework, warm colors, whimsical style",
        "comic-book": "Comic book style, bold outlines, dynamic poses, vibrant colors, graphic novel aesthetic",
        "storybook": "Classic storybook illustration, warm colors, nostalgic, timeless, whimsical, vintage children's book",
        "realistic": "Ultra photorealistic, hyperdetailed, professional DSLR photography, real life, no stylization, no cartoon, natural lighting, sharp focus",
        "photorealistic": "Ultra photorealistic style, hyperdetailed like a real photograph, professional photography quality, DSLR camera, natural lighting, NO cartoon, NO anime, NO illustration, real life quality",
        "anime": "Anime/manga style illustration, big expressive eyes, colorful, dynamic, Japanese animation quality",
        "manga": "Manga style, detailed linework, dramatic shading, Japanese comic aesthetic",
        "oil-painting": "Classical oil painting style, rich colors, dramatic brushwork, museum quality, fine art aesthetic",
        "vintage-storybook": "Vintage storybook illustration, aged paper texture, classic fairy tale style, ornate details",
        "dark-fantasy": "Dark fantasy art, moody atmosphere, dramatic lighting, gothic elements, epic fantasy style",
        "illustration": "Professional children's book illustration, colorful, friendly, whimsical, hand-drawn feel",
        "comic": "Comic book panel style, bold outlines, dynamic poses, vibrant colors",
        "sketch": "Pencil sketch illustration, hand-drawn, artistic, detailed linework",
        "fantasy": "Fantasy art style, magical, ethereal, detailed environments",
        "scifi": "Futuristic sci-fi style, neon colors, advanced technology, space themes"
    }

async def generate_single_image(prompt: str, style_desc: str) -> str:
    """Generate a single image and return its URL using fal.ai FLUX"""
    
    # Use fal.ai FLUX for high-quality image generation
    if FAL_AVAILABLE:
        try:
            # Combine prompt with style description for better results
            full_prompt = f"{prompt}. {style_desc}. High quality, detailed illustration."
            
            # Use print_quality for correct 8x10 ratio (2400x3000px at 300 DPI)
            result = await generate_image_flux(
                prompt=full_prompt,
                model="flux-schnell",  # Use standard FLUX for cost efficiency
                image_size="portrait_4_3",  # Fallback
                num_images=1,
                guidance_scale=3.5,
                num_inference_steps=4,
                print_quality=True  # Generate at correct 8x10 ratio for printing
            )
            
            if result.get("success") and result.get("images"):
                image_data = result["images"][0]
                image_url = image_data.get("url")
                
                if image_url:
                    # Upload to Cloudinary for permanent storage
                    if CLOUDINARY_AVAILABLE:
                        upload_result = cloudinary.uploader.upload(
                            image_url,
                            folder="azories/story_pages"
                        )
                        return upload_result.get("secure_url")
                    return image_url
                    
            raise Exception("No image URL in fal.ai response")
            
        except Exception as e:
            logger.warning(f"fal.ai generation failed, falling back to OpenAI: {e}")
            # Fall through to OpenAI fallback
    
    # Fallback to fal.ai standard model if Pro fails
    if FAL_AVAILABLE:
        try:
            logger.info("Attempting fallback to fal.ai FLUX standard model")
            full_prompt = f"{prompt}. {style_desc}. High quality illustration."
            
            result = await generate_image_flux(
                prompt=full_prompt,
                model="flux-schnell",  # Standard FLUX model as fallback
                image_size="portrait_4_3",
                num_images=1,
                guidance_scale=3.5,
                num_inference_steps=4,
                print_quality=True
            )
            
            if result.get("success") and result.get("images"):
                image_data = result["images"][0]
                image_url = image_data.get("url")
                
                if image_url:
                    if CLOUDINARY_AVAILABLE:
                        upload_result = cloudinary.uploader.upload(
                            image_url,
                            folder="azories/story_pages"
                        )
                        return upload_result.get("secure_url")
                    return image_url
                    
        except Exception as e2:
            logger.error(f"fal.ai standard fallback also failed: {e2}")
    
    # Final fallback to OpenAI only if fal.ai completely unavailable
    if not EMERGENT_LLM_KEY:
        raise Exception("Image generation not available")
    
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
    images = await image_gen.generate_images(
        prompt=prompt,
        model="gpt-image-1",
        number_of_images=1,
        size="1024x1536",
        quality="high"
    )
    
    if images and len(images) > 0:
        if CLOUDINARY_AVAILABLE:
            image_bytes = images[0]
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            upload_result = cloudinary.uploader.upload(
                f"data:image/png;base64,{image_base64}",
                folder="azories/story_pages"
            )
            return upload_result.get("secure_url")
        else:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
    
    raise Exception("No image generated")

async def generate_story_text(request: AIStoryRequest, user_data: dict) -> dict:
    """Generate just the story text (no images)"""
    # Build the story idea
    story_idea = request.story_description or request.plot_summary or request.idea
    if not story_idea.strip():
        raise Exception("Please provide a story description")
    
    # Build character context
    character_context = ""
    if request.character_name and request.character_description:
        character_context = f"The main character is {request.character_name}: {request.character_description}."
    elif request.character_name:
        character_context = f"The main character is named {request.character_name}."
    
    # Age-appropriate context
    age_mapping = {
        "0-2": "babies and toddlers (ages 0-2) - extremely simple words, very short sentences",
        "3-5": "preschoolers (ages 3-5) - simple words and short sentences, playful tone",
        "6-8": "early readers (ages 6-8) - engaging vocabulary, adventurous plots",
        "9-12": "middle grade readers (ages 9-12) - more complex narrative and vocabulary",
        "13-16": "young adult readers (ages 13-16) - complex vocabulary, deeper themes",
        "17+": "adult fiction readers (17+) - full literary fiction quality"
    }
    age_context = age_mapping.get(request.age_range, age_mapping["6-8"])
    
    # Word count
    word_counts = {"short": 50, "medium": 100, "long": 150, "long_adult": 200}
    target_words = word_counts.get(request.words_per_page, 100)
    
    is_story_studio = request.creator_mode == "studio" or request.age_range in ["13-16", "17+"]
    if is_story_studio and request.words_per_page == "long":
        target_words = 200
    
    # Title instruction
    title_instruction = f'Use the title: "{request.title}"' if request.title.strip() else 'Create an engaging, memorable title'
    
    # System message based on mode
    if is_story_studio and request.age_range == "17+":
        system_message = "You are a literary fiction author. Create engaging, sophisticated stories."
    elif is_story_studio:
        system_message = "You are a young adult fiction author. Create engaging stories with emotional depth."
    else:
        system_message = "You are a children's book author. Create engaging, safe, age-appropriate stories."
    
    # Generate story
    story_prompt = f"""Create a story with EXACTLY {request.num_pages} pages.

STORY IDEA: {story_idea}
{character_context}

REQUIREMENTS:
- Title: {title_instruction}
- Target audience: {age_context}
- MUST have exactly {request.num_pages} pages
- Each page should have approximately {target_words} words

Return a JSON object:
{{
    "title": "Story Title",
    "description": "Brief description",
    "back_cover_text": "Back cover summary",
    "main_character_description": "Visual description of main character",
    "pages": [
        {{"page_number": 1, "text": "Page text", "image_prompt": "Scene description"}},
        ... (exactly {request.num_pages} pages)
    ]
}}

Return ONLY valid JSON."""

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"story-{user_data['id']}-{str(uuid.uuid4())[:8]}",
        system_message=system_message
    ).with_model("openai", "gpt-4o")
    
    response = await chat.send_message(UserMessage(text=story_prompt))
    
    # Parse JSON
    response_text = response.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    try:
        story_data = json.loads(response_text.strip())
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            story_data = json.loads(json_match.group())
        else:
            raise Exception("Failed to parse story data")
    
    # If user specified a title, use it instead of AI-generated one
    if request.title and request.title.strip():
        story_data["title"] = request.title.strip()
    
    return story_data


@api_router.post("/ai/generate-story-async")
async def generate_story_async(request: AIStoryRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Start async story generation - returns job_id immediately
    
    The story will be generated in the background. Poll /api/jobs/{job_id}/status for progress.
    """
    # Calculate credits needed
    page_count = request.num_pages
    credits_needed = AI_STORY_PAGE_CREDITS.get(page_count, 5)
    
    # Check free stories (only for Kids Mode, 5 pages)
    free_stories_remaining = current_user.get("free_stories_remaining")
    free_stories_used = current_user.get("free_stories_used", 0)
    
    if free_stories_remaining is None:
        free_stories_remaining = max(0, 3 - free_stories_used)
    
    is_kids_mode = request.creator_mode == "kids"
    is_free_eligible = is_kids_mode and page_count <= 5
    has_free_stories = free_stories_remaining > 0 and is_free_eligible
    
    if has_free_stories:
        # Use free story
        new_remaining = free_stories_remaining - 1
        new_used = free_stories_used + 1
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"free_stories_remaining": new_remaining, "free_stories_used": new_used}}
        )
        logger.info(f"User {current_user['id']} using free story ({new_remaining} remaining)")
    else:
        # Check and deduct credits
        current_credits = current_user.get("credits", 0)
        if current_credits < credits_needed:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Need {credits_needed} credits for {page_count} pages, have {current_credits}."
            )
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"credits": -credits_needed}}
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    job_data = {
        "job_id": job_id,
        "status": StoryJobStatus.PENDING.value,
        "user_id": current_user["id"],
        "book_id": None,
        "progress_percent": 0,
        "current_step": "Starting your story...",
        "total_pages": page_count,
        "pages_completed": 0,
        "story_text_done": False,
        "images_status": {},
        "error_message": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "request_data": request.dict(),
        "credits_charged": credits_needed if not has_free_stories else 0,
        "used_free_story": has_free_stories
    }
    
    # Store in memory and database
    STORY_JOBS[job_id] = job_data
    await db.story_jobs.insert_one({k: v for k, v in job_data.items() if k != "_id"})
    
    # Start background task
    background_tasks.add_task(
        run_story_generation_job,
        job_id,
        request.dict(),
        {
            "id": current_user["id"],
            "email": current_user.get("email"),
            "name": current_user.get("name")
        }
    )
    
    logger.info(f"Story generation job {job_id} created for user {current_user['id']}")
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Story generation started. Poll /api/jobs/{job_id}/status for progress.",
        "estimated_time_minutes": max(2, page_count // 3)  # Rough estimate
    }


@api_router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Get the current status of a story generation job"""
    
    # Check memory first
    if job_id in STORY_JOBS:
        job = STORY_JOBS[job_id]
    else:
        # Check database
        job = await db.story_jobs.find_one({"job_id": job_id}, {"_id": 0})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify user owns this job
    if job.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "progress_percent": job.get("progress_percent", 0),
        "current_step": job.get("current_step", ""),
        "book_id": job.get("book_id"),
        "total_pages": job.get("total_pages", 0),
        "pages_completed": job.get("pages_completed", 0),
        "story_text_done": job.get("story_text_done", False),
        "images_status": job.get("images_status", {}),
        "error_message": job.get("error_message"),
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at")
    }


@api_router.get("/jobs/active")
async def get_active_jobs(current_user: dict = Depends(get_current_user)):
    """Get all active/pending jobs for the current user"""
    
    active_statuses = [StoryJobStatus.PENDING.value, StoryJobStatus.GENERATING_STORY.value, StoryJobStatus.GENERATING_IMAGES.value]
    
    jobs = await db.story_jobs.find(
        {"user_id": current_user["id"], "status": {"$in": active_statuses}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    return {"jobs": jobs}


@api_router.get("/jobs/history")
async def get_job_history(current_user: dict = Depends(get_current_user)):
    """Get recent job history for the current user"""
    
    jobs = await db.story_jobs.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "request_data": 0}  # Don't return full request data
    ).sort("created_at", -1).to_list(20)
    
    return {"jobs": jobs}

# ==================== END ASYNC STORY GENERATION ====================


@api_router.post("/ai/generate-story")
async def generate_story(request: AIStoryRequest, current_user: dict = Depends(get_current_user)):
    """Generate a complete story from an idea using AI, with images
    
    Business Logic:
    - First 3 stories are FREE for all users (Kids Mode only, max 5 pages)
    - After free stories, credits scale with page count
    - Story Studio mode always requires credits
    """
    # Calculate credits needed based on page count
    page_count = request.num_pages
    credits_needed = AI_STORY_PAGE_CREDITS.get(page_count, 5)
    
    # Check if user has free stories remaining (3 free stories for new users)
    # Free stories only available for Kids Mode and 5 pages
    free_stories_remaining = current_user.get("free_stories_remaining")
    free_stories_used = current_user.get("free_stories_used", 0)
    
    # For existing users without the field, give them 3 free stories
    if free_stories_remaining is None:
        free_stories_remaining = max(0, 3 - free_stories_used)
    
    # Free stories only for Kids Mode with 5 pages
    is_kids_mode = request.creator_mode == "kids"
    is_free_eligible = is_kids_mode and page_count <= 5
    has_free_stories = free_stories_remaining > 0 and is_free_eligible
    
    if has_free_stories:
        # Use a free story - decrement remaining and increment used
        new_remaining = free_stories_remaining - 1
        new_used = free_stories_used + 1
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"free_stories_remaining": new_remaining, "free_stories_used": new_used}}
        )
        logger.info(f"User {current_user['id']} using free story ({new_remaining} remaining)")
    else:
        # Deduct credits based on page count
        current_credits = current_user.get("credits", 0)
        if current_credits < credits_needed:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. You have {current_credits} credits but need {credits_needed} for {page_count} pages. Please purchase more credits to continue."
            )
        
        # Deduct credits manually (not using standard deduct_credits since cost varies)
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"credits": -credits_needed}}
        )
        logger.info(f"User {current_user['id']} charged {credits_needed} credits for {page_count}-page story")
    
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
        
        # Build the story idea from new fields
        story_idea = request.story_description or request.plot_summary or request.idea
        if not story_idea.strip():
            raise HTTPException(status_code=400, detail="Please provide a story description")
        
        # Build character context
        character_context = ""
        if request.character_name and request.character_description:
            character_context = f"The main character is {request.character_name}: {request.character_description}."
        elif request.character_name:
            character_context = f"The main character is named {request.character_name}."
        
        # Expanded age-appropriate context with tone guidance
        age_mapping = {
            # Kids Mode ages
            "0-2": "babies and toddlers (ages 0-2) - extremely simple words, very short sentences (3-5 words), repetitive patterns, sensory descriptions, gentle and soothing tone",
            "3-5": "preschoolers (ages 3-5) - simple words and short sentences, playful tone, clear morals, happy endings",
            "6-8": "early readers (ages 6-8) - engaging vocabulary appropriate for the age, adventurous plots, relatable characters",
            "9-12": "middle grade readers (ages 9-12) - more complex narrative and vocabulary, character growth, exciting adventures",
            # Story Studio ages
            "13-16": "young adult readers (ages 13-16) - complex vocabulary, deeper themes and character development, can include mild peril, romance, complex emotions, less simplified sentence structure",
            "17+": "adult fiction readers (17+) - full literary fiction quality, complex plots and subplots, mature themes (not explicit), sophisticated prose, novel-style chapter structure for longer books"
        }
        age_context = age_mapping.get(request.age_range, age_mapping["6-8"])
        
        # Determine if this is Story Studio mode (for teens/adults)
        is_story_studio = request.creator_mode == "studio" or request.age_range in ["13-16", "17+"]
        
        # Word count mapping - expanded
        word_counts = {
            "short": 50,
            "medium": 100,
            "long": 150,
            "long_adult": 200  # For adult fiction
        }
        target_words = word_counts.get(request.words_per_page, 100)
        
        # Adjust for Story Studio mode
        if is_story_studio and request.words_per_page == "long":
            target_words = 200  # Adult fiction gets more words per page
        
        # Expanded image style mapping for prompts
        style_prompts = {
            # Kids Mode styles
            "3d-pixar": "Pixar 3D animation style, Disney quality, vibrant colors, expressive characters, magical lighting, cinematic composition",
            "pixar": "Pixar 3D animation style, Disney quality, vibrant colors, expressive characters, magical lighting, cinematic composition",
            "watercolour": "Soft watercolor illustration, gentle colors, dreamy atmosphere, hand-painted feel, children's book quality",
            "watercolor": "Soft watercolor illustration, gentle colors, dreamy atmosphere, hand-painted feel",
            "pencil-sketch": "Pencil sketch illustration, hand-drawn feel, artistic linework, detailed textures, warm and inviting",
            "hand-drawn": "Hand-drawn illustration, artistic linework, warm colors, whimsical style",
            "comic-book": "Comic book style, bold outlines, dynamic poses, vibrant colors, graphic novel aesthetic",
            "storybook": "Classic storybook illustration, warm colors, nostalgic, timeless, whimsical, vintage children's book",
            
            # Story Studio styles (for older readers)
            "realistic": "Ultra photorealistic, hyperdetailed, professional DSLR photography, real life, no stylization, no cartoon, natural lighting, sharp focus",
            "photorealistic": "Ultra photorealistic style, hyperdetailed like a real photograph, professional photography quality, DSLR camera, natural lighting, NO cartoon, NO anime, NO illustration, real life quality",
            "anime": "Anime/manga style illustration, big expressive eyes, colorful, dynamic, Japanese animation quality",
            "manga": "Manga style, detailed linework, dramatic shading, Japanese comic aesthetic",
            "oil-painting": "Classical oil painting style, rich colors, dramatic brushwork, museum quality, fine art aesthetic",
            "vintage-storybook": "Vintage storybook illustration, aged paper texture, classic fairy tale style, ornate details",
            "dark-fantasy": "Dark fantasy art, moody atmosphere, dramatic lighting, gothic elements, epic fantasy style",
            
            # Ideogram styles (NEW - Character consistency)
            "ideogram-realistic": "Ultra photorealistic style, hyperdetailed like a real photograph, professional DSLR photography, natural lighting, NO cartoon, NO anime, real life quality",
            "ideogram-storybook": "Charming children's book illustration style, soft pastel colors, warm lighting, whimsical and friendly",
            "ideogram-character": "Illustrated character style, consistent character appearance, expressive features, warm colors, storybook quality",
            
            # Legacy fallbacks
            "illustration": "Professional children's book illustration, colorful, friendly, whimsical, hand-drawn feel",
            "comic": "Comic book panel style, bold outlines, dynamic poses, vibrant colors",
            "sketch": "Pencil sketch illustration, hand-drawn, artistic, detailed linework",
            "fantasy": "Fantasy art style, magical, ethereal, detailed environments",
            "scifi": "Futuristic sci-fi style, neon colors, advanced technology, space themes"
        }
        
        # Use the art_style from request, fallback to image_style for backwards compatibility
        selected_style = request.art_style or request.image_style or "3d-pixar"
        
        # Detect style from the story description ONLY if user didn't explicitly select a style
        story_lower = story_idea.lower()
        detected_style = None
        
        # Only auto-detect style if user is using the default style
        if selected_style == "3d-pixar":
            style_keywords = {
                "pixar": ["pixar", "disney", "animated movie"],
                "anime": ["anime", "manga", "japanese", "studio ghibli"],
                "comic": ["comic", "superhero", "marvel", "dc"],
                "watercolour": ["watercolor", "watercolour", "painted", "painterly"],
                "photorealistic": ["photorealistic", "photograph", "photo realistic", "photo-realistic"],
                "realistic": ["realistic", "real life", "lifelike"],
                "scifi": ["sci-fi", "scifi", "space", "futuristic", "robot"],
                "sketch": ["sketch", "pencil", "drawn", "line art"],
                "fantasy": ["fantasy", "magical", "enchanted", "fairy"],
                "storybook": ["classic", "storybook", "traditional", "vintage"]
            }
            
            for style, keywords in style_keywords.items():
                if any(kw in story_lower for kw in keywords):
                    detected_style = style
                    logger.info(f"Auto-detected style '{style}' from story description")
                    break
        
        # Use selected style (user's explicit choice takes priority), fall back to detected
        final_style = selected_style if selected_style != "3d-pixar" else (detected_style or selected_style)
        style_desc = style_prompts.get(final_style, style_prompts["3d-pixar"])
        
        logger.info(f"Using style: {final_style} (selected: {selected_style}, detected: {detected_style})")
        
        # Build the title instruction
        title_instruction = f'Use the title: "{request.title}"' if request.title.strip() else 'Create an engaging, memorable title'
        
        # Build genre and tone context for Story Studio mode
        genre_context = ""
        tone_context = ""
        chapter_instruction = ""
        
        if is_story_studio:
            if request.genre:
                genre_context = f"\n- Genre: {request.genre}"
            if request.tone:
                tone_context = f"\n- Tone: {request.tone}"
            if request.chapter_structure and request.num_pages >= 20:
                chapter_instruction = f"""
CHAPTER STRUCTURE (for {request.num_pages} pages):
- Organize the story into chapters
- Include chapter titles in the JSON
- Each chapter should have 3-8 pages
- Use "chapter_title" field for pages that start a new chapter"""
        
        # Different system messages based on mode
        if is_story_studio and request.age_range == "17+":
            system_message = "You are a literary fiction author. Create engaging, sophisticated stories with complex characters and themes. Write at a professional novel quality level. Always respond with valid JSON only."
        elif is_story_studio and request.age_range == "13-16":
            system_message = "You are a young adult fiction author. Create engaging stories with relatable characters, emotional depth, and appropriate themes for teenagers. Always respond with valid JSON only."
        else:
            system_message = "You are a children's book author. Create engaging, safe, age-appropriate stories. Always respond with valid JSON only. Pay careful attention to word count requirements."
        
        # Generate story structure using Emergent LLM Chat
        story_prompt = f"""Create a {'literary' if is_story_studio else "children's"} story with EXACTLY {request.num_pages} pages.

STORY IDEA: {story_idea}
{character_context}

REQUIREMENTS:
- Title: {title_instruction}
- Target audience: {age_context}{genre_context}{tone_context}
- MUST have exactly {request.num_pages} pages - no more, no less
- Each page MUST have approximately {target_words} words (±15 tolerance)
{chapter_instruction}

CRITICAL: You MUST generate exactly {request.num_pages} pages. The story should have a beginning, middle, and end spread across all {request.num_pages} pages.

Return a JSON object with this EXACT structure:
{{
    "title": "Story Title",
    "description": "Brief description for the book",
    "back_cover_text": "Engaging back cover summary (2-3 sentences)",
    "main_character_description": "Detailed visual description of the main character",
    "pages": [
        {{"page_number": 1, "text": "First page text (~{target_words} words)", "image_prompt": "Scene description"{', "chapter_title": "Chapter 1 Title"' if request.chapter_structure else ''}}},
        {{"page_number": 2, "text": "Second page text (~{target_words} words)", "image_prompt": "Scene description"}},
        ... (continue for all {request.num_pages} pages)
    ]
}}

Story pacing guidelines for {request.num_pages} pages:
{f'''- This is a longer form story - use proper story arc with rising action, climax, and resolution
- Pages 1-3: Opening hook and character establishment  
- Pages 4-{request.num_pages // 2}: Rising action and conflict development
- Pages {request.num_pages // 2 + 1}-{request.num_pages - 2}: Climax and turning point
- Final pages: Resolution and conclusion''' if request.num_pages >= 20 else '''- Pages 1-2: Introduction of character and setting
- Middle pages: Main adventure/conflict
- Final page(s): Resolution and happy ending'''}

IMPORTANT: 
1. Generate EXACTLY {request.num_pages} pages in the pages array
2. Each page text should be approximately {target_words} words
3. Image prompts should be detailed for {final_style} style illustrations
4. {'Content can include mild peril, romance, and complex emotions appropriate for the age group' if is_story_studio else 'Keep content age-appropriate and positive'}

Return ONLY the JSON object, no other text."""
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"story-gen-{current_user['id']}-{str(uuid.uuid4())[:8]}",
            system_message=system_message
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
        
        # CRITICAL: Validate page count and retry if wrong
        actual_pages = len(story_data.get("pages", []))
        expected_pages = request.num_pages
        
        logger.info(f"AI returned {actual_pages} pages, expected {expected_pages}")
        
        if actual_pages < expected_pages:
            logger.warning(f"AI only generated {actual_pages} pages instead of {expected_pages}. Requesting additional pages...")
            
            # Request remaining pages
            remaining_pages = expected_pages - actual_pages
            existing_text = "\n".join([f"Page {p['page_number']}: {p['text']}" for p in story_data["pages"]])
            
            continuation_prompt = f"""Continue this children's story with {remaining_pages} more pages.

EXISTING STORY:
Title: {story_data.get('title', 'Story')}
{existing_text}

REQUIREMENTS:
- Add exactly {remaining_pages} more pages
- Continue from page {actual_pages + 1}
- Words per page: EXACTLY {target_words} words (±10 words tolerance)
- Maintain the same characters, style, and tone
- Build toward a satisfying conclusion

Return ONLY a JSON array of the new pages:
[
    {{
        "page_number": {actual_pages + 1},
        "text": "Page text with EXACTLY {target_words} words",
        "image_prompt": "Detailed scene description for illustration"
    }}
]

Return ONLY the JSON array, no other text."""

            continuation_response = await chat.send_message(UserMessage(text=continuation_prompt))
            
            try:
                cont_text = continuation_response.strip()
                if cont_text.startswith("```json"):
                    cont_text = cont_text[7:]
                if cont_text.startswith("```"):
                    cont_text = cont_text[3:]
                if cont_text.endswith("```"):
                    cont_text = cont_text[:-3]
                
                additional_pages = json.loads(cont_text.strip())
                
                # Handle if it returned an object with pages array
                if isinstance(additional_pages, dict) and "pages" in additional_pages:
                    additional_pages = additional_pages["pages"]
                
                if isinstance(additional_pages, list):
                    story_data["pages"].extend(additional_pages)
                    logger.info(f"Added {len(additional_pages)} continuation pages. Total: {len(story_data['pages'])}")
            except Exception as cont_error:
                logger.error(f"Failed to parse continuation pages: {cont_error}")
                # Continue with what we have
        
        # Final count logging
        final_page_count = len(story_data.get("pages", []))
        logger.info(f"Final page count: {final_page_count} (requested: {expected_pages})")
        
        # Create the book
        book_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Azories branded back cover for all AI-created books
        azories_back_cover_url = "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772281331/azories/back_covers/the_dragons_secret_garden_back.png"
        
        book = {
            "id": book_id,
            "title": story_data["title"],
            "description": story_data["description"],
            "genre": request.genre,
            "cover_image": "",
            "back_cover_image": azories_back_cover_url,
            "cover_title": story_data["title"],
            "cover_subtitle": "",
            "back_cover_text": story_data["back_cover_text"],
            "user_id": current_user["id"],  # Owner ID for access control
            "author_id": current_user["id"],
            "author_name": current_user["name"],
            "is_published": False,
            "requires_auth": False,  # Always allow owner to read their books
            "is_featured": False,
            "is_best_of_week": False,
            "layout_mode": "standard",
            "narrator_voice_id": "21m00Tcm4TlvDq8ikWAM",
            "narrator_voice_locked": False,  # Added - was missing
            "age_rating": request.age_rating,
            "publish_status": "draft",  # Added - was missing
            "moderation_flags": [],  # Added - was missing
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
        
        # Get main character description for consistent images
        main_char_desc = story_data.get("main_character_description", "")
        
        # Create pages and generate images if requested
        pages_created = []
        images_generated = 0
        
        for idx, page_data in enumerate(story_data["pages"]):
            page_id = str(uuid.uuid4())
            image_url = ""
            
            # Generate image for this page if requested
            if request.generate_images and request.media_type == "images":
                try:
                    # Build comprehensive image prompt
                    base_prompt = page_data.get("image_prompt", page_data["text"])
                    full_prompt = f"{style_desc}. {base_prompt}"
                    if main_char_desc:
                        full_prompt = f"{style_desc}. Main character: {main_char_desc}. Scene: {base_prompt}"
                    
                    logger.info(f"Generating image for page {idx + 1}: {full_prompt[:100]}...")
                    
                    # Check if using Ideogram style OR photorealistic (which works better with Ideogram)
                    if final_style.startswith("ideogram-") or final_style == "photorealistic":
                        # Use Ideogram for character consistency and photorealistic styles
                        from fal_service import generate_image_ideogram
                        
                        ideogram_style = "design"  # Default
                        if final_style == "ideogram-realistic" or final_style == "photorealistic":
                            ideogram_style = "realistic"
                        elif final_style == "ideogram-storybook":
                            ideogram_style = "design"
                        elif final_style == "ideogram-character":
                            ideogram_style = "design"  # Best for consistent characters
                        
                        result = await generate_image_ideogram(
                            prompt=full_prompt,
                            model="ideogram-v3",
                            aspect_ratio="4:5",  # Portrait for book pages
                            style=ideogram_style,
                            magic_prompt=True,
                            print_quality=True
                        )
                    else:
                        # Use fal.ai FLUX for image generation
                        # print_quality=True generates at 2400x3000 (8x10 at 300 DPI)
                        result = await generate_image_flux(
                            prompt=full_prompt,
                            model="flux-schnell",
                            image_size="portrait_4_3",  # Fallback if print_quality doesn't work
                            num_images=1,
                            print_quality=True  # Generate at correct 8x10 ratio for printing
                        )
                    
                    if result and result.get("images") and len(result["images"]) > 0:
                        image_url_raw = result["images"][0].get("url", "")
                        
                        if image_url_raw:
                            # Upload to Cloudinary for permanent storage if available
                            if CLOUDINARY_AVAILABLE and cloudinary:
                                try:
                                    cloudinary_result = cloudinary.uploader.upload(
                                        image_url_raw,
                                        folder=f"azories/books/{book_id}/pages",
                                        public_id=f"page_{idx + 1}",
                                        resource_type="image"
                                    )
                                    image_url = cloudinary_result.get("secure_url", "")
                                except Exception as cloud_err:
                                    logger.warning(f"Cloudinary upload failed, using direct URL: {cloud_err}")
                                    image_url = image_url_raw
                            else:
                                image_url = image_url_raw
                            images_generated += 1
                            logger.info(f"Generated and uploaded image for page {idx + 1}")
                    
                except Exception as img_error:
                    logger.error(f"Failed to generate image for page {idx + 1}: {str(img_error)}")
                    # Continue without image - user can generate later
            
            page = {
                "id": page_id,
                "chapter_id": chapter_id,
                "text_content": page_data["text"],
                "image_url": image_url,
                "image_url_2": "",
                "image_url_3": "",
                "image_url_4": "",
                "video_url": "",
                "audio_url": "",
                "order": idx + 1,
                "layout_type": "single",
                "created_at": now,
                "image_prompt": page_data.get("image_prompt", "")
            }
            await db.pages.insert_one(page)
            pages_created.append({
                "page_id": page_id,
                "order": idx + 1,
                "text": page_data["text"],
                "image_prompt": page_data.get("image_prompt", ""),
                "image_url": image_url
            })
        
        # Generate cover image if images were requested
        cover_image_url = ""
        if request.generate_images and request.media_type == "images" and images_generated > 0:
            try:
                cover_prompt = f"{style_desc}. Book cover for '{story_data['title']}'. {story_data['description']}. {main_char_desc if main_char_desc else ''}"
                
                # Use fal.ai FLUX for cover image generation
                # print_quality=True generates at 2400x3000 (8x10 at 300 DPI)
                cover_result = await generate_image_flux(
                    prompt=cover_prompt,
                    model="flux-schnell",
                    image_size="portrait_4_3",  # Fallback if print_quality doesn't work
                    num_images=1,
                    print_quality=True  # Generate at correct 8x10 ratio for printing
                )
                
                if cover_result and cover_result.get("images") and len(cover_result["images"]) > 0:
                    cover_url_raw = cover_result["images"][0].get("url", "")
                    
                    if cover_url_raw:
                        if CLOUDINARY_AVAILABLE and cloudinary:
                            try:
                                cloudinary_cover = cloudinary.uploader.upload(
                                    cover_url_raw,
                                    folder=f"azories/books/{book_id}",
                                    public_id="cover",
                                    resource_type="image"
                                )
                                cover_image_url = cloudinary_cover.get("secure_url", "")
                            except Exception as cloud_err:
                                logger.warning(f"Cloudinary upload failed for cover, using direct URL: {cloud_err}")
                                cover_image_url = cover_url_raw
                        else:
                            cover_image_url = cover_url_raw
                        
                        # Update book with cover
                        await db.books.update_one(
                            {"id": book_id},
                            {"$set": {"cover_image": cover_image_url}}
                        )
                        logger.info("Generated cover image for book")
                    
            except Exception as cover_error:
                logger.error(f"Failed to generate cover: {str(cover_error)}")
        
        # Add Azories branded back cover to every AI-created book
        # Use a working Azories back cover template
        azories_back_cover_url = "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772281331/azories/back_covers/the_dragons_secret_garden_back.png"
        back_cover_text = story_data.get("description", request.story_description)[:200]
        
        await db.books.update_one(
            {"id": book_id},
            {"$set": {
                "back_cover_image": azories_back_cover_url,
                "back_cover_text": back_cover_text
            }}
        )
        logger.info("Added Azories branded back cover to AI-created book")
        
        return {
            "success": True,
            "book_id": book_id,
            "title": story_data["title"],
            "pages_created": len(pages_created),
            "images_generated": images_generated,
            "cover_image": cover_image_url,
            "back_cover_image": azories_back_cover_url,
            "pages": pages_created,
            "message": f"Story created with {images_generated} images!" if images_generated > 0 else "Story created! Navigate to editor to generate images."
        }
        
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating story: {str(e)}")

# Endpoint to add Azories back cover to existing books that don't have one
@api_router.post("/admin/add-back-covers")
async def add_back_covers_to_books(current_user: dict = Depends(get_admin_user)):
    """Add Azories branded back cover to all books that don't have one"""
    azories_back_cover_url = "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772281331/azories/back_covers/the_dragons_secret_garden_back.png"
    
    # Find all books without back cover image
    books_without_back_cover = await db.books.find(
        {"$or": [{"back_cover_image": ""}, {"back_cover_image": None}, {"back_cover_image": {"$exists": False}}]},
        {"_id": 0, "id": 1, "title": 1, "description": 1}
    ).to_list(1000)
    
    updated_count = 0
    for book in books_without_back_cover:
        back_cover_text = (book.get("description") or "")[:200]
        await db.books.update_one(
            {"id": book["id"]},
            {"$set": {
                "back_cover_image": azories_back_cover_url,
                "back_cover_text": back_cover_text
            }}
        )
        updated_count += 1
        logger.info(f"Added back cover to book: {book['title']}")
    
    # Also fix any books with the broken azories_standard_back URL
    broken_url = "azories_standard_back"
    books_with_broken_url = await db.books.find(
        {"back_cover_image": {"$regex": broken_url}},
        {"_id": 0, "id": 1, "title": 1, "description": 1}
    ).to_list(1000)
    
    for book in books_with_broken_url:
        back_cover_text = (book.get("description") or "")[:200]
        await db.books.update_one(
            {"id": book["id"]},
            {"$set": {
                "back_cover_image": azories_back_cover_url,
                "back_cover_text": back_cover_text
            }}
        )
        updated_count += 1
        logger.info(f"Fixed broken back cover URL for book: {book['title']}")
    
    return {
        "success": True,
        "books_updated": updated_count,
        "message": f"Added/Fixed Azories back cover for {updated_count} books"
    }

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
    """Generate TTS audio using ElevenLabs with OpenAI fallback, with Cloudinary caching"""
    import hashlib
    import base64
    
    try:
        # Use the voice_id directly (it's already an ElevenLabs voice ID)
        voice_id = request.voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default to Rachel
        
        # Create a cache key based on text content and voice
        cache_key = hashlib.sha256(f"{request.text}:{voice_id}:tts".encode()).hexdigest()
        
        # Check if we have a Cloudinary URL cached
        cached_audio = await db.audio_cache.find_one({"cache_key": cache_key})
        if cached_audio and cached_audio.get("cloudinary_url"):
            logger.info(f"TTS Cloudinary cache hit for key: {cache_key[:16]}...")
            return {
                "audio_url": cached_audio["cloudinary_url"],
                "audio_base64": None,
                "success": True, 
                "cached": True
            }
        
        # Not in cache - generate new audio
        logger.info(f"TTS cache miss, generating for key: {cache_key[:16]}...")
        
        audio_bytes = None
        provider = "unknown"
        
        # Try ElevenLabs first
        if eleven_client:
            try:
                audio_generator = eleven_client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=request.text,
                    model_id="eleven_multilingual_v2",
                    voice_settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.0,
                        use_speaker_boost=True
                    )
                )
                audio_bytes = b"".join(audio_generator)
                provider = "elevenlabs"
                logger.info("Generated audio with ElevenLabs")
            except Exception as eleven_err:
                error_msg = str(eleven_err)
                if "missing_permissions" in error_msg or "401" in error_msg:
                    logger.error(f"ElevenLabs API key missing text_to_speech permission. Please regenerate the key with proper permissions.")
                else:
                    logger.warning(f"ElevenLabs failed: {error_msg[:150]}")
                # Fall through to OpenAI fallback
        
        # Fallback to OpenAI TTS if ElevenLabs failed
        if audio_bytes is None:
            emergent_key = os.environ.get("EMERGENT_LLM_KEY")
            if not emergent_key:
                raise HTTPException(status_code=500, detail="TTS service not configured")
            
            # Map ElevenLabs voice IDs to OpenAI voices
            voice_mapping = {
                "21m00Tcm4TlvDq8ikWAM": "nova",
                "AZnzlk1XvdvUeBnXmlld": "shimmer",
                "EXAVITQu4vr4xnSDxMaL": "alloy",
                "ErXwobaYiN019PkySvjV": "onyx",
                "MF3mGyEYCl7XYWbV9V6O": "coral",
                "TxGEqnHWrfWFTfGW9XjX": "echo",
                "VR6AewLTigWG4xSOukaG": "fable",
                "pNInz6obpgDQGcFmaJgB": "sage",
                "yoZ06aMxZJJ28mfd3POQ": "ash",
            }
            openai_voice = voice_mapping.get(voice_id, "nova")
            
            tts = OpenAITextToSpeech(api_key=emergent_key)
            audio_base64 = await tts.generate_speech_base64(
                text=request.text,
                model="tts-1",
                voice=openai_voice,
                response_format="mp3"
            )
            audio_bytes = base64.b64decode(audio_base64)
            provider = "openai"
            logger.info("Generated audio with OpenAI TTS (fallback)")
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Upload to Cloudinary
        cloudinary_url = None
        try:
            upload_result = cloudinary.uploader.upload(
                audio_bytes,
                resource_type="video",
                folder="azories/audio/narration",
                public_id=f"tts_{cache_key[:16]}",
                format="mp3"
            )
            cloudinary_url = upload_result.get("secure_url")
            logger.info(f"Audio uploaded to Cloudinary: {cloudinary_url}")
        except Exception as upload_error:
            logger.warning(f"Failed to upload audio to Cloudinary: {upload_error}")
        
        # Store in cache with Cloudinary URL
        await db.audio_cache.update_one(
            {"cache_key": cache_key},
            {
                "$set": {
                    "cache_key": cache_key,
                    "cloudinary_url": cloudinary_url,
                    "audio_base64": audio_base64 if not cloudinary_url else None,
                    "voice": voice_id,
                    "provider": provider,
                    "text_preview": request.text[:100],
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": datetime.now(timezone.utc) + timedelta(days=365)
                }
            },
            upsert=True
        )
        
        return {
            "audio_url": cloudinary_url,
            "audio_base64": audio_base64 if not cloudinary_url else None,
            "success": True, 
            "cached": False
        }
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

class BatchTTSRequest(BaseModel):
    book_id: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"

@api_router.post("/tts/batch-prepare")
async def batch_prepare_tts(request: BatchTTSRequest, background_tasks: BackgroundTasks):
    """Pre-generate TTS audio for all pages in a book - runs in background for speed"""
    import hashlib
    import base64
    
    book = await db.books.find_one({"id": request.book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get all pages with text content
    pages = book.get("pages", [])
    pages_to_process = [p for p in pages if p.get("text_content") and not p.get("audio_url")]
    
    if not pages_to_process:
        return {"success": True, "message": "All pages already have audio", "pages_processed": 0}
    
    # Use ElevenLabs voice_id directly
    voice_id = request.voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default to Rachel
    
    # Voice mapping for OpenAI fallback
    voice_mapping = {
        "21m00Tcm4TlvDq8ikWAM": "nova",
        "AZnzlk1XvdvUeBnXmlld": "shimmer",
        "EXAVITQu4vr4xnSDxMaL": "alloy",
        "ErXwobaYiN019PkySvjV": "onyx",
        "MF3mGyEYCl7XYWbV9V6O": "coral",
        "TxGEqnHWrfWFTfGW9XjX": "echo",
        "VR6AewLTigWG4xSOukaG": "fable",
        "pNInz6obpgDQGcFmaJgB": "sage",
        "yoZ06aMxZJJ28mfd3POQ": "ash",
    }
    openai_voice = voice_mapping.get(voice_id, "nova")
    
    async def process_pages():
        emergent_key = os.environ.get("EMERGENT_LLM_KEY")
        
        try:
            processed = 0
            max_pages = 10  # Limit concurrent processing to prevent memory issues
            
            for page in pages_to_process[:max_pages]:  # Process max 10 pages per batch
                try:
                    text = page.get("text_content", "")
                    if not text:
                        continue
                        
                    cache_key = hashlib.sha256(f"{text}:{voice_id}:tts".encode()).hexdigest()
                    
                    # Check cache first
                    cached = await db.audio_cache.find_one({"cache_key": cache_key})
                    if cached and cached.get("cloudinary_url"):
                        # Update page with cached URL
                        await db.books.update_one(
                            {"id": request.book_id, "pages.page_number": page.get("page_number")},
                            {"$set": {"pages.$.audio_url": cached["cloudinary_url"]}}
                        )
                        processed += 1
                        continue
                    
                    audio_bytes = None
                    provider = "unknown"
                    
                    # Try ElevenLabs first
                    if eleven_client:
                        try:
                            audio_generator = eleven_client.text_to_speech.convert(
                                voice_id=voice_id,
                                text=text,
                                model_id="eleven_multilingual_v2",
                                voice_settings=VoiceSettings(
                                    stability=0.5,
                                    similarity_boost=0.75,
                                    style=0.0,
                                    use_speaker_boost=True
                                )
                            )
                            audio_bytes = b"".join(audio_generator)
                            provider = "elevenlabs"
                        except Exception as eleven_err:
                            logger.warning(f"ElevenLabs batch failed, falling back to OpenAI: {str(eleven_err)[:50]}")
                    
                    # Fallback to OpenAI
                    if audio_bytes is None and emergent_key:
                        tts = OpenAITextToSpeech(api_key=emergent_key)
                        audio_base64 = await tts.generate_speech_base64(
                            text=text,
                            model="tts-1",
                            voice=openai_voice,
                            response_format="mp3"
                        )
                        audio_bytes = base64.b64decode(audio_base64)
                        provider = "openai"
                    
                    if audio_bytes is None:
                        logger.error("No TTS provider available")
                        continue
                    
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        audio_bytes,
                        resource_type="video",
                        folder="azories/audio/narration",
                        public_id=f"tts_{cache_key[:16]}",
                        format="mp3"
                    )
                    del audio_bytes  # Free memory immediately
                    
                    cloudinary_url = upload_result.get("secure_url")
                    
                    # Cache and update page
                    await db.audio_cache.update_one(
                        {"cache_key": cache_key},
                        {"$set": {
                            "cache_key": cache_key,
                            "cloudinary_url": cloudinary_url,
                            "voice": voice_id,
                            "provider": provider,
                            "created_at": datetime.now(timezone.utc)
                        }},
                        upsert=True
                    )
                    
                    await db.books.update_one(
                        {"id": request.book_id, "pages.page_number": page.get("page_number")},
                        {"$set": {"pages.$.audio_url": cloudinary_url}}
                    )
                    processed += 1
                    logger.info(f"Batch TTS ({provider}): Processed page {page.get('page_number')} for book {request.book_id}")
                    
                except Exception as e:
                    logger.error(f"Batch TTS error for page {page.get('page_number')}: {e}")
                    continue
            
            logger.info(f"Batch TTS complete: {processed}/{len(pages_to_process)} pages for book {request.book_id}")
        except Exception as e:
            logger.error(f"Batch TTS fatal error: {e}")
    
    # Run in background for instant response
    background_tasks.add_task(process_pages)
    
    return {
        "success": True,
        "message": f"Started preparing audio for {len(pages_to_process)} pages",
        "pages_to_process": len(pages_to_process)
    }


@api_router.post("/tts/generate-for-page/{page_id}")
async def generate_tts_for_page(
    page_id: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    current_user: dict = Depends(get_current_user)
):
    """Generate and cache TTS audio for a specific page using ElevenLabs with OpenAI fallback"""
    import hashlib
    import base64
    
    try:
        # Find the page
        page = await db.pages.find_one({"id": page_id})
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        # Check if page already has cached audio
        if page.get("audio_url") and page["audio_url"].startswith("https://"):
            logger.info(f"Page {page_id} already has cached audio: {page['audio_url']}")
            return {"audio_url": page["audio_url"], "cached": True, "success": True}
        
        text = page.get("text_content", "")
        if not text.strip():
            return {"audio_url": None, "cached": False, "success": True, "message": "No text to narrate"}
        
        audio_bytes = None
        provider = "unknown"
        
        # Try ElevenLabs first
        if eleven_client:
            try:
                audio_generator = eleven_client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id="eleven_multilingual_v2",
                    voice_settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.0,
                        use_speaker_boost=True
                    )
                )
                audio_bytes = b"".join(audio_generator)
                provider = "elevenlabs"
            except Exception as eleven_err:
                logger.warning(f"ElevenLabs failed for page TTS, falling back to OpenAI: {str(eleven_err)[:50]}")
        
        # Fallback to OpenAI
        if audio_bytes is None:
            emergent_key = os.environ.get("EMERGENT_LLM_KEY")
            if not emergent_key:
                raise HTTPException(status_code=500, detail="TTS service not configured")
            
            voice_mapping = {
                "21m00Tcm4TlvDq8ikWAM": "nova",
                "AZnzlk1XvdvUeBnXmlld": "shimmer",
                "EXAVITQu4vr4xnSDxMaL": "alloy",
                "ErXwobaYiN019PkySvjV": "onyx",
                "MF3mGyEYCl7XYWbV9V6O": "coral",
                "TxGEqnHWrfWFTfGW9XjX": "echo",
                "VR6AewLTigWG4xSOukaG": "fable",
                "pNInz6obpgDQGcFmaJgB": "sage",
                "yoZ06aMxZJJ28mfd3POQ": "ash",
            }
            openai_voice = voice_mapping.get(voice_id, "nova")
            
            tts = OpenAITextToSpeech(api_key=emergent_key)
            audio_base64 = await tts.generate_speech_base64(
                text=text,
                model="tts-1",
                voice=openai_voice,
                response_format="mp3"
            )
            audio_bytes = base64.b64decode(audio_base64)
            provider = "openai"
        
        # Get book info for folder organization
        chapter = await db.chapters.find_one({"id": page.get("chapter_id")})
        book_id = chapter.get("book_id", "unknown") if chapter else "unknown"
        
        upload_result = cloudinary.uploader.upload(
            audio_bytes,
            resource_type="video",
            folder=f"azories/audio/books/{book_id}",
            public_id=f"page_{page_id}",
            format="mp3"
        )
        cloudinary_url = upload_result.get("secure_url")
        
        # Save audio URL to page document
        await db.pages.update_one(
            {"id": page_id},
            {"$set": {"audio_url": cloudinary_url}}
        )
        
        logger.info(f"Generated and cached {provider} audio for page {page_id}: {cloudinary_url}")
        return {"audio_url": cloudinary_url, "cached": False, "success": True}
        
    except Exception as e:
        logger.error(f"Error generating TTS for page: {str(e)}")
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
async def get_full_book(book_id: str, response: Response, current_user: dict = Depends(get_optional_user)):
    """Get complete book - always returns pages to the book owner"""
    # Prevent caching so text updates appear immediately
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = set_book_defaults(book)
    
    # ALWAYS return full book content if:
    # 1. User is logged in AND is the book owner
    # 2. Book is published/public
    # 3. Book doesn't require auth
    is_published = book.get("is_published", False)
    is_owner = current_user and (
        book.get("user_id") == current_user.get("id") or 
        book.get("owner_id") == current_user.get("id") or
        book.get("author_id") == current_user.get("id")
    )
    requires_auth = book.get("requires_auth", False)
    
    # Allow access if: owner, published, or doesn't require auth
    allow_full_access = is_owner or is_published or not requires_auth
    
    # If not allowed and not logged in, return 401
    if not allow_full_access and not current_user:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required to read this book"
        )
    
    full_chapters = []
    
    # Check ALL THREE sources and pick the one with actual images
    
    # Source 1: Chapters from separate collection (BookEditor-created books)
    chapters_from_db = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
    chapters_have_images = False
    
    if chapters_from_db and len(chapters_from_db) > 0:
        for chapter in chapters_from_db:
            pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).sort("order", 1).to_list(100)
            # Check if any page has an image
            for page in pages:
                if page.get("image_url") and len(page.get("image_url", "")) > 0:
                    chapters_have_images = True
                    break
            if chapters_have_images:
                break
    
    # Source 2: Embedded pages array (generated library books)
    embedded_pages = book.get("pages", [])
    embedded_have_images = False
    
    if embedded_pages and len(embedded_pages) > 0:
        for page in embedded_pages:
            if page.get("image_url") and len(page.get("image_url", "")) > 0:
                embedded_have_images = True
                break
    
    # Source 3: Pages collection linked by book_id (AI-generated stories)
    ai_generated_pages = await db.pages.find({"book_id": book_id}, {"_id": 0}).sort("page_number", 1).to_list(100)
    ai_pages_have_images = False
    
    if ai_generated_pages and len(ai_generated_pages) > 0:
        for page in ai_generated_pages:
            if page.get("image_url") and len(page.get("image_url", "")) > 0:
                ai_pages_have_images = True
                break
    
    # Decision: Prioritize data sources with actual content
    # 1. AI-generated pages (book_id linked) - these are newest format
    # 2. Embedded pages in book document
    # 3. Chapter-based pages
    
    if ai_pages_have_images or (ai_generated_pages and len(ai_generated_pages) > 0):
        # Use AI-generated pages from pages collection (linked by book_id)
        normalized_pages = []
        for page in ai_generated_pages:
            normalized_page = {
                "id": page.get("id", f"page-{page.get('page_number', 0)}"),
                "chapter_id": "ai-generated-chapter",
                "order": page.get("page_number", 0),
                "page_number": page.get("page_number", 0),
                "text": page.get("text_content", page.get("text", "")),
                "text_content": page.get("text_content", page.get("text", "")),
                "image_url": page.get("image_url", ""),
                "image_url_2": page.get("image_url_2", ""),
                "image_url_3": page.get("image_url_3", ""),
                "image_url_4": page.get("image_url_4", ""),
                "video_url": page.get("video_url", ""),
                "use_video": page.get("use_video", False),
                "layout_type": page.get("layout_type", page.get("layout", "single")),
                "image_position_x": page.get("image_position_x", 50),
                "image_position_y": page.get("image_position_y", 50),
                "image_fit": page.get("image_fit", "cover"),
                "font_family": page.get("font_family", "default"),
                "font_size": page.get("font_size", "medium"),
                "text_align": page.get("text_align", "left"),
                "image_prompt": page.get("image_prompt", ""),
            }
            normalized_pages.append(normalized_page)
        
        full_chapters.append({
            "id": "ai-generated-chapter",
            "book_id": book_id,
            "title": book.get("title", "Story"),
            "order": 0,
            "pages": normalized_pages
        })
    
    elif embedded_have_images:
        # Use embedded pages - convert to chapter format
        normalized_pages = []
        for page in embedded_pages:
            normalized_page = {
                "id": page.get("id", f"page-{page.get('page_number', 0)}"),
                "chapter_id": "embedded-chapter",
                "order": page.get("page_number", 0),
                "text": page.get("text_content", page.get("text", "")),
                "text_content": page.get("text_content", page.get("text", "")),
                "image_url": page.get("image_url", ""),
                "image_url_2": page.get("image_url_2", ""),
                "image_url_3": page.get("image_url_3", ""),
                "image_url_4": page.get("image_url_4", ""),
                "video_url": page.get("video_url", ""),
                "use_video": page.get("use_video", False),
                "layout_type": page.get("layout", "single"),
                "image_position_x": page.get("image_position_x", 50),
                "image_position_y": page.get("image_position_y", 50),
                "image_fit": page.get("image_fit", "cover"),
                "font_family": page.get("font_family", "default"),
                "font_size": page.get("font_size", "medium"),
                "text_align": page.get("text_align", "left"),
            }
            normalized_pages.append(normalized_page)
        
        full_chapters.append({
            "id": "embedded-chapter",
            "book_id": book_id,
            "title": book.get("title", "Story"),
            "order": 0,
            "pages": normalized_pages
        })
    
    elif chapters_have_images or (chapters_from_db and len(chapters_from_db) > 0):
        # Use chapters from separate collection
        for chapter in chapters_from_db:
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
    
    elif embedded_pages and len(embedded_pages) > 0:
        # Fallback: use embedded pages even without images (better than nothing)
        normalized_pages = []
        for page in embedded_pages:
            normalized_page = {
                "id": page.get("id", f"page-{page.get('page_number', 0)}"),
                "chapter_id": "embedded-chapter",
                "order": page.get("page_number", 0),
                "text": page.get("text_content", page.get("text", "")),
                "text_content": page.get("text_content", page.get("text", "")),
                "image_url": page.get("image_url", ""),
                "image_url_2": "",
                "image_url_3": "",
                "image_url_4": "",
                "video_url": "",
                "use_video": False,
                "layout_type": page.get("layout", "single"),
                "image_position_x": 50,
                "image_position_y": 50,
                "image_fit": "cover",
                "font_family": "default",
                "font_size": "medium",
                "text_align": "left",
            }
            normalized_pages.append(normalized_page)
        
        full_chapters.append({
            "id": "embedded-chapter",
            "book_id": book_id,
            "title": book.get("title", "Story"),
            "order": 0,
            "pages": normalized_pages
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
    'streak_14': {'type': 'streak', 'count': 14},
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
            "best_streak": 0,
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
        "best_streak": stats.get("best_streak", 0),
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
            "best_streak": 0,
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
    
    # Update best streak if current streak is higher
    if stats["streak"] > stats.get("best_streak", 0):
        stats["best_streak"] = stats["streak"]
    
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
    if streak >= 14 and 'streak_14' not in current_badges:
        new_badges.append('streak_14')
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
        "best_streak": stats.get("best_streak", stats["streak"]),
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
                amount = metadata.get("amount", "unknown")
                
                # Add credits
                user = await db.users.find_one({"id": user_id})
                if user:
                    current_credits = user.get("credits", 0)
                    await db.users.update_one(
                        {"id": user_id},
                        {"$set": {"credits": current_credits + credits}}
                    )
                    
                    # Send admin notification for credit purchase
                    if email_configured():
                        admin_email = os.environ.get("ADMIN_NOTIFY_EMAIL", "books@azories.com")
                        user_email = user.get("email", "unknown")
                        user_name = user.get("name", "Unknown")
                        admin_subject = f"💰 Credit Purchase: {credits} credits by {user_name}"
                        admin_html = f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
                            <div style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 20px; border-radius: 12px 12px 0 0;">
                                <h1 style="color: white; margin: 0; font-size: 24px;">💰 New Credit Purchase!</h1>
                            </div>
                            <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                                <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                                    <tr>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>User:</strong></td>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{user_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{user_email}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Credits:</strong></td>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{credits} credits</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Amount:</strong></td>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">${amount}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>New Balance:</strong></td>
                                        <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{current_credits + credits} credits</td>
                                    </tr>
                                </table>
                                <p style="color: #16a34a; font-weight: bold; margin-top: 20px;">✅ Payment processed successfully via Stripe</p>
                            </div>
                        </body>
                        </html>
                        """
                        # Send in background (can't use background_tasks in webhook, use asyncio.create_task)
                        asyncio.create_task(send_email(admin_email, admin_subject, admin_html))
                
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

# Note: Admin Analytics routes moved to /app/backend/routes/admin.py

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

# Note: Contact form endpoint is defined later in the file with Pydantic model (better version)

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
                "thumbnail_url": item.get("thumbnail_url"),  # For video thumbnails
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
    """Save an image to the Art Studio gallery with thumbnails"""
    user = current_user
    
    image_url = request.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    try:
        now = datetime.now(timezone.utc)
        
        # Initialize URLs
        final_url = image_url
        thumbnail_url = request.get("thumbnail_url")  # Accept thumbnail from request (for videos)
        medium_url = None
        
        # For videos, use the provided thumbnail_url (source image)
        item_type = request.get("type", "image")
        if item_type == "animation" and thumbnail_url:
            # Keep the provided thumbnail for videos
            logging.info(f"Using provided thumbnail for video: {thumbnail_url[:50]}...")
        # If image is base64, upload it to fal.ai CDN with thumbnails
        elif image_url.startswith('data:image') and FAL_AVAILABLE:
            try:
                logging.info("Uploading base64 image to fal.ai CDN with thumbnails...")
                result = await upload_image_with_thumbnails(image_url)
                final_url = result['image_url']
                thumbnail_url = result['thumbnail_url']
                medium_url = result['medium_url']
                logging.info(f"Image uploaded with thumbnails: {final_url[:50]}...")
            except Exception as upload_error:
                logging.warning(f"Failed to upload with thumbnails: {upload_error}")
                # Fallback: try simple upload
                try:
                    final_url = await upload_image_to_fal(image_url)
                except:
                    final_url = image_url
        # If already a CDN URL, generate thumbnails
        elif image_url.startswith('https://') and FAL_AVAILABLE:
            try:
                logging.info("Generating thumbnails for existing CDN image...")
                thumbs = await generate_thumbnails(image_url)
                thumbnail_url = thumbs['thumbnail_url']
                medium_url = thumbs['medium_url']
            except Exception as thumb_error:
                logging.warning(f"Failed to generate thumbnails: {thumb_error}")
        
        gallery_item = {
            "user_id": user["id"],
            "image_url": final_url,
            "thumbnail_url": thumbnail_url,
            "medium_url": medium_url,
            "name": request.get("name", request.get("prompt", "Untitled")),
            "prompt": request.get("prompt", ""),
            "type": request.get("type", "image"),
            "style": request.get("style", ""),
            "model": request.get("model", ""),
            "book_id": request.get("book_id"),
            "source": request.get("source", "art_studio"),
            "created_at": now
        }
        
        result = await db.art_studio_gallery.insert_one(gallery_item)
        
        return {
            "success": True,
            "id": str(result.inserted_id),
            "message": "Image saved to gallery",
            "image_url": final_url,
            "thumbnail_url": thumbnail_url,
            "medium_url": medium_url
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

# Starter Library Images - AI-Illustrated images for children's books
# Batch 1: 50 Character images (Watercolour, Realistic, Comic, Sketch styles)
# Batch 2: 50 Settings & Backgrounds images
# Batch 3: 50 Objects & Props images
# Batch 4: 50 Action & Emotion Scenes
# Stock photos archived - Feb 25, 2026
from data.starter_library_batch1 import BATCH_1_CHARACTERS
from data.starter_library_batch2 import BATCH_2_SETTINGS
from data.starter_library_batch3 import BATCH_3_OBJECTS
from data.starter_library_batch4 import BATCH_4_ACTIONS
from data.starter_library_new import STARTER_LIBRARY_PROMPTS

# Complete library contains 200 images total (old format)
STARTER_LIBRARY_IMAGES_OLD = BATCH_1_CHARACTERS + BATCH_2_SETTINGS + BATCH_3_OBJECTS + BATCH_4_ACTIONS

# New starter library - stored in database after generation
async def get_starter_library_from_db():
    """Get generated starter library images from database"""
    images = await db.starter_library.find({}, {"_id": 0}).to_list(100)
    return images

@api_router.get("/starter-library")
async def get_starter_library(category: Optional[str] = None):
    """Get starter library images for new users - no auth required"""
    # Try to get from database first (generated images)
    db_images = await get_starter_library_from_db()
    
    if db_images and len(db_images) > 0:
        images = db_images
    else:
        # Fallback to old placeholder data with proper placeholder URLs
        # OLD data has relative URLs that won't work - generate working Cloudinary placeholders
        images = []
        for img in STARTER_LIBRARY_IMAGES_OLD:
            img_copy = img.copy()
            if not img_copy.get("url", "").startswith("http"):
                # Use Cloudinary's text overlay feature to create a branded placeholder
                # This creates a purple square with category name - works without uploading any image
                category = img_copy.get("category", "image")[:15]  # Limit text length
                name = img_copy.get("name", "")[:20]  # Limit text length
                placeholder_url = f"https://res.cloudinary.com/dlbmjqmoy/image/upload/w_400,h_400,c_fill/co_white,l_text:Arial_16_bold:{category}/fl_layer_apply,g_center,y_-20/co_white,l_text:Arial_12:{name.replace(' ', '%20')}/fl_layer_apply,g_center,y_20/c_fill,w_400,h_400,b_rgb:7c3aed/sample.jpg"
                img_copy["url"] = placeholder_url
                img_copy["thumbnail_url"] = placeholder_url
            images.append(img_copy)
    
    if category:
        images = [img for img in images if img.get("category") == category]
    
    return {"images": images, "total": len(images)}

@api_router.post("/admin/generate-starter-library")
async def generate_starter_library_images(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    batch_size: int = 5,
    start_index: int = 0
):
    """
    Admin endpoint to generate starter library images using fal.ai
    Generates images in batches and uploads to Cloudinary
    """
    # Admin only
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not FAL_AVAILABLE:
        raise HTTPException(status_code=500, detail="fal.ai service not available")
    
    # Get prompts to generate
    prompts_to_generate = STARTER_LIBRARY_PROMPTS[start_index:start_index + batch_size]
    
    if not prompts_to_generate:
        return {"message": "No more images to generate", "total_prompts": len(STARTER_LIBRARY_PROMPTS)}
    
    results = []
    errors = []
    
    for item in prompts_to_generate:
        try:
            logger.info(f"Generating starter library image: {item['id']} - {item['name']}")
            
            # Generate image using fal.ai flux-dev
            image_result = await generate_image_flux(
                prompt=item['prompt'],
                model="flux-schnell",
                image_size="square_hd",
                num_images=1
            )
            
            if image_result and image_result.get('images'):
                image_url = image_result['images'][0].get('url')
                
                # Upload to Cloudinary for permanent storage
                cloudinary_url = None
                if image_url and CLOUDINARY_AVAILABLE:
                    try:
                        # Download image and upload to Cloudinary
                        async with aiohttp.ClientSession() as session:
                            async with session.get(image_url) as resp:
                                if resp.status == 200:
                                    image_data = await resp.read()
                                    upload_result = cloudinary.uploader.upload(
                                        image_data,
                                        folder=f"azories/starter_library/{item['category']}",
                                        public_id=item['id'],
                                        resource_type="image"
                                    )
                                    cloudinary_url = upload_result.get("secure_url")
                                    logger.info(f"Uploaded to Cloudinary: {cloudinary_url}")
                    except Exception as upload_error:
                        logger.warning(f"Cloudinary upload failed: {upload_error}")
                        cloudinary_url = image_url  # Use fal.ai URL as fallback
                
                final_url = cloudinary_url or image_url
                
                # Store in database
                library_item = {
                    "id": item['id'],
                    "name": item['name'],
                    "category": item['category'],
                    "art_style": item['art_style'],
                    "url": final_url,
                    "thumbnail_url": final_url,
                    "tags": [item['category'], item['art_style']],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.starter_library.update_one(
                    {"id": item['id']},
                    {"$set": library_item},
                    upsert=True
                )
                
                results.append({
                    "id": item['id'],
                    "name": item['name'],
                    "url": final_url,
                    "status": "success"
                })
            else:
                errors.append({"id": item['id'], "error": "No image generated"})
                
        except Exception as e:
            logger.error(f"Error generating {item['id']}: {str(e)}")
            errors.append({"id": item['id'], "error": str(e)})
    
    return {
        "message": f"Generated {len(results)} images",
        "batch_start": start_index,
        "batch_size": batch_size,
        "next_index": start_index + batch_size,
        "total_prompts": len(STARTER_LIBRARY_PROMPTS),
        "remaining": len(STARTER_LIBRARY_PROMPTS) - (start_index + batch_size),
        "results": results,
        "errors": errors
    }

@api_router.get("/admin/starter-library-status")
async def get_starter_library_status(current_user: dict = Depends(get_current_user)):
    """Check status of starter library generation"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    generated = await db.starter_library.count_documents({})
    total = len(STARTER_LIBRARY_PROMPTS)
    
    return {
        "generated": generated,
        "total": total,
        "remaining": total - generated,
        "percent_complete": round((generated / total) * 100, 1) if total > 0 else 0
    }


class StarterLibraryImportItem(BaseModel):
    id: str
    name: str
    category: str
    art_style: Optional[str] = None
    tags: Optional[List[str]] = []
    url: str
    thumbnail_url: Optional[str] = None
    created_at: Optional[str] = None

class StarterLibraryImportRequest(BaseModel):
    images: List[StarterLibraryImportItem]

@api_router.post("/admin/import-starter-library")
async def import_starter_library(request: StarterLibraryImportRequest, current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint to bulk import starter library images.
    Use this to copy starter library data from preview to production.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    imported = 0
    skipped = 0
    errors = []
    
    for item in request.images:
        try:
            # Check if already exists
            existing = await db.starter_library.find_one({"id": item.id})
            if existing:
                skipped += 1
                continue
            
            # Insert new item
            doc = {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "art_style": item.art_style,
                "tags": item.tags or [],
                "url": item.url,
                "thumbnail_url": item.thumbnail_url or item.url,
                "created_at": datetime.now(timezone.utc)
            }
            await db.starter_library.insert_one(doc)
            imported += 1
            
        except Exception as e:
            errors.append(f"{item.id}: {str(e)[:50]}")
    
    return {
        "message": "Import complete",
        "imported": imported,
        "skipped": skipped,
        "total_in_db": await db.starter_library.count_documents({}),
        "errors": errors[:10] if errors else []
    }


class SaveAnimationRequest(BaseModel):
    video_url: str
    name: str
    motion_prompt: Optional[str] = ""
    style: Optional[str] = "natural"
    thumbnail_url: Optional[str] = None  # Source image used for animation

@api_router.post("/art-studio/save-animation")
async def save_animation(request: SaveAnimationRequest, current_user: dict = Depends(get_current_user)):
    """
    Save an animation to user's gallery.
    
    Videos are uploaded to Cloudinary for PERMANENT storage.
    Falls back to fal.ai if Cloudinary is not available (⚠️ 7-day retention only).
    """
    user = current_user
    
    try:
        video_url = request.video_url
        storage_provider = "original"  # Track where video is stored
        
        # Priority 1: Upload to Cloudinary for permanent storage
        if video_url.startswith('data:video') and CLOUDINARY_AVAILABLE:
            try:
                logging.info("Uploading video to Cloudinary (permanent storage)...")
                result = await upload_video_to_cloudinary(video_url, folder="azories/animations")
                video_url = result['url']
                storage_provider = "cloudinary"
                logging.info(f"Video uploaded to Cloudinary: {video_url[:60]}...")
            except Exception as cloudinary_error:
                logging.warning(f"Cloudinary upload failed: {cloudinary_error}")
                # Fall through to fal.ai fallback
        
        # Priority 2: Fallback to fal.ai (⚠️ 7-day retention only)
        if video_url.startswith('data:video') and FAL_AVAILABLE:
            try:
                logging.warning("⚠️ Using fal.ai for video storage (7-day retention only)")
                video_url = await upload_video_to_fal(video_url)
                storage_provider = "fal"
                logging.info(f"Video uploaded to fal.ai: {video_url[:60]}...")
            except Exception as fal_error:
                logging.warning(f"fal.ai upload failed: {fal_error}")
                # Keep original base64 as last resort
        
        gallery_item = {
            "user_id": user["id"],
            "image_url": video_url,  # Store video URL in image_url field for compatibility
            "thumbnail_url": request.thumbnail_url,  # Source image as thumbnail
            "name": request.name,
            "type": "animation",
            "style": request.style,
            "motion_prompt": request.motion_prompt,
            "storage_provider": storage_provider,  # Track storage location
            "created_at": datetime.now(timezone.utc)
        }
        
        result = await db.art_studio_gallery.insert_one(gallery_item)
        
        return {
            "success": True,
            "id": str(result.inserted_id),
            "video_url": video_url,
            "storage_provider": storage_provider
        }
        
    except Exception as e:
        logging.error(f"Save animation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save animation")



@api_router.get("/pro-studio/videos")
async def get_all_user_videos(current_user: dict = Depends(get_current_user)):
    """Get all videos/animations created by the user from all sources"""
    user = current_user
    all_videos = []
    
    try:
        # Get videos from art_studio_gallery (type: animation)
        art_studio_videos = await db.art_studio_gallery.find({
            "user_id": user["id"],
            "type": "animation"
        }).sort("created_at", -1).to_list(100)
        
        for video in art_studio_videos:
            all_videos.append({
                "id": str(video["_id"]),
                "video_url": video.get("image_url", ""),
                "thumbnail_url": video.get("thumbnail_url"),  # Video thumbnail
                "name": video.get("name", "Animation"),
                "source": "art_studio",
                "style": video.get("style", ""),
                "created_at": video.get("created_at", datetime.now(timezone.utc)).isoformat() if video.get("created_at") else None
            })
        
        # Get videos from character galleries (type: video or containing video data)
        characters = await db.pro_studio_characters.find({"user_id": user["id"]}).to_list(100)
        for char in characters:
            char_videos = await db.character_gallery.find({
                "character_id": str(char["_id"]),
                "user_id": user["id"],
                "$or": [
                    {"type": "video"},
                    {"image_url": {"$regex": "video|mp4", "$options": "i"}}
                ]
            }).sort("created_at", -1).to_list(50)
            
            for video in char_videos:
                all_videos.append({
                    "id": str(video["_id"]),
                    "video_url": video.get("image_url", ""),
                    "thumbnail_url": video.get("thumbnail_url"),  # Video thumbnail
                    "name": f"{char.get('name', 'Character')} - Video",
                    "source": "character",
                    "character_name": char.get("name", ""),
                    "character_id": str(char["_id"]),
                    "created_at": video.get("created_at", datetime.now(timezone.utc)).isoformat() if video.get("created_at") else None
                })
        
        return {"videos": all_videos}
    
    except Exception as e:
        logging.error(f"Error fetching user videos: {e}")
        return {"videos": []}


@api_router.post("/admin/backfill-video-thumbnails")
async def backfill_video_thumbnails(admin: dict = Depends(get_admin_user)):
    """
    Admin endpoint to generate thumbnails for existing videos/animations.
    
    For fal.media and other external videos, downloads first frame using ffmpeg
    and uploads to Cloudinary. For Cloudinary videos, uses video transformation.
    """
    import tempfile
    import subprocess
    import os
    
    results = {
        "total_videos": 0,
        "missing_thumbnails": 0,
        "updated": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    try:
        # Find all animation items
        videos = await db.art_studio_gallery.find({
            "type": "animation"
        }).to_list(500)
        
        results["total_videos"] = len(videos)
        
        for video in videos:
            try:
                video_url = video.get("image_url", "")
                video_id = video.get("_id")
                existing_thumb = video.get("thumbnail_url", "")
                
                # Skip if no video URL
                if not video_url:
                    results["skipped"] += 1
                    continue
                
                # Check if existing thumbnail is valid (not a placeholder that 404s)
                if existing_thumb and "placeholders/" not in existing_thumb and existing_thumb.startswith("https://res.cloudinary.com"):
                    # Verify it's not a placeholder
                    results["skipped"] += 1
                    continue
                
                results["missing_thumbnails"] += 1
                thumbnail_url = None
                
                # Option 1: If it's a Cloudinary video, generate thumbnail via transformation
                if "cloudinary.com" in video_url and "/video/" in video_url:
                    thumbnail_url = video_url.replace("/upload/", "/upload/so_0,w_400,h_400,c_fill/")
                    if ".mp4" in thumbnail_url:
                        thumbnail_url = thumbnail_url.replace(".mp4", ".jpg")
                    elif ".webm" in thumbnail_url:
                        thumbnail_url = thumbnail_url.replace(".webm", ".jpg")
                
                # Option 2: For external videos, use ffmpeg to extract frame and upload to Cloudinary
                elif video_url.startswith("http"):
                    try:
                        with tempfile.TemporaryDirectory() as tmpdir:
                            output_path = os.path.join(tmpdir, "thumbnail.jpg")
                            
                            # Use ffmpeg to extract first frame
                            cmd = [
                                "ffmpeg", "-y",
                                "-i", video_url,
                                "-vframes", "1",
                                "-ss", "0",
                                "-vf", "scale=400:400:force_original_aspect_ratio=decrease,pad=400:400:(ow-iw)/2:(oh-ih)/2",
                                "-q:v", "2",
                                output_path
                            ]
                            
                            result = subprocess.run(cmd, capture_output=True, timeout=30)
                            
                            if result.returncode == 0 and os.path.exists(output_path):
                                # Upload to Cloudinary
                                upload_result = cloudinary.uploader.upload(
                                    output_path,
                                    folder="azories/video_thumbnails",
                                    public_id=f"thumb_{str(video_id)}",
                                    overwrite=True
                                )
                                thumbnail_url = upload_result.get("secure_url")
                                logger.info(f"Uploaded thumbnail for video {video_id}: {thumbnail_url}")
                            else:
                                logger.warning(f"FFmpeg failed for video {video_id}: {result.stderr[:200] if result.stderr else 'unknown'}")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"FFmpeg timeout for video {video_id}")
                    except Exception as ffmpeg_error:
                        logger.warning(f"FFmpeg error for video {video_id}: {ffmpeg_error}")
                
                # Update the document if we have a thumbnail
                if thumbnail_url:
                    await db.art_studio_gallery.update_one(
                        {"_id": video_id},
                        {"$set": {"thumbnail_url": thumbnail_url}}
                    )
                    results["updated"] += 1
                    logger.info(f"Updated thumbnail for video {video_id}")
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Could not generate thumbnail for {str(video_id)}")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Video {video_id}: {str(e)[:100]}")
                logger.error(f"Error backfilling thumbnail for video {video_id}: {e}")
        
        logger.info(f"Backfill complete: {results['updated']} updated, {results['failed']} failed, {results['skipped']} skipped")
        return results
        
    except Exception as e:
        logger.error(f"Backfill video thumbnails error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SetVideoThumbnailRequest(BaseModel):
    video_id: str
    thumbnail_url: str

@api_router.post("/admin/set-video-thumbnail")
async def set_video_thumbnail(request: SetVideoThumbnailRequest, current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint to manually set a video thumbnail URL.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from bson import ObjectId
        video_id = ObjectId(request.video_id)
        
        result = await db.art_studio_gallery.update_one(
            {"_id": video_id},
            {"$set": {"thumbnail_url": request.thumbnail_url}}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": f"Thumbnail updated for video {request.video_id}"}
        else:
            return {"success": False, "message": "Video not found or thumbnail already set"}
            
    except Exception as e:
        logger.error(f"Error setting video thumbnail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SetVideoThumbnailsBulkRequest(BaseModel):
    thumbnails: dict  # {video_id: thumbnail_url}

@api_router.post("/admin/set-video-thumbnails-bulk")
async def set_video_thumbnails_bulk(request: SetVideoThumbnailsBulkRequest, current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint to bulk set video thumbnail URLs.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    updated = 0
    failed = 0
    
    try:
        from bson import ObjectId
        
        for video_id, thumbnail_url in request.thumbnails.items():
            try:
                result = await db.art_studio_gallery.update_one(
                    {"_id": ObjectId(video_id)},
                    {"$set": {"thumbnail_url": thumbnail_url}}
                )
                if result.modified_count > 0:
                    updated += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error updating thumbnail for {video_id}: {e}")
                failed += 1
        
        return {"success": True, "updated": updated, "failed": failed}
        
    except Exception as e:
        logger.error(f"Error bulk setting video thumbnails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/pro-studio/gallery/unified")
async def get_unified_gallery(
    page: int = 1,
    limit: int = 50,
    filter_type: Optional[str] = None,  # 'images', 'videos', 'characters'
    current_user: dict = Depends(get_current_user)
):
    """
    Get all Pro Studio gallery items in a single optimized call.
    Combines art_studio_gallery, character galleries, and videos.
    Returns paginated results with minimal data for thumbnails.
    """
    user = current_user
    all_items = []
    skip = (page - 1) * limit
    
    def safe_isoformat(val):
        """Safely convert datetime to ISO string, handling already-string values."""
        if val is None:
            return None
        if isinstance(val, str):
            return val
        if hasattr(val, 'isoformat'):
            return val.isoformat()
        return str(val)
    
    try:
        # 1. Get art studio gallery items
        if filter_type in (None, 'images', 'videos'):
            art_query = {"user_id": user["id"]}
            if filter_type == 'videos':
                art_query["type"] = "animation"
            elif filter_type == 'images':
                art_query["type"] = {"$ne": "animation"}
            
            art_items = await db.art_studio_gallery.find(art_query).sort("created_at", -1).to_list(200)
            
            for item in art_items:
                is_video = item.get("type") == "animation"
                prompt_text = item.get("prompt", item.get("name", ""))
                # Preserve original source field, default to 'art-studio' if not set
                item_source = item.get("source", "art-studio")
                all_items.append({
                    "id": str(item["_id"]),
                    "image_url": item.get("image_url", ""),
                    "thumbnail_url": item.get("thumbnail_url"),
                    "medium_url": item.get("medium_url"),
                    "prompt": prompt_text[:100] if prompt_text else "",
                    "name": item.get("name", ""),
                    "source": item_source,
                    "type": "video" if is_video else "image",
                    "is_animation": is_video,
                    "created_at": safe_isoformat(item.get("created_at"))
                })
        
        # 2. Get characters and their galleries in one batch
        if filter_type in (None, 'images', 'characters'):
            characters = await db.pro_studio_characters.find({"user_id": user["id"]}).to_list(100)
            char_ids = [str(char["_id"]) for char in characters]
            char_map = {str(char["_id"]): char.get("name", "Character") for char in characters}
            
            # Add character master images
            for char in characters:
                if char.get("thumbnail"):
                    desc_text = char.get("description", char.get("appearance_traits", ""))
                    all_items.append({
                        "id": f"char-{char['_id']}",
                        "image_url": char.get("thumbnail", ""),
                        "prompt": desc_text[:100] if desc_text else "",
                        "name": char.get("name", ""),
                        "source": "character",
                        "type": "image",
                        "is_master": True,
                        "character_id": str(char["_id"]),
                        "character_name": char.get("name", ""),
                        "created_at": safe_isoformat(char.get("created_at"))
                    })
            
            # Batch fetch all character gallery images
            if char_ids:
                char_gallery_items = await db.character_gallery.find({
                    "character_id": {"$in": char_ids},
                    "user_id": user["id"]
                }).sort("created_at", -1).to_list(500)
                
                for img in char_gallery_items:
                    is_video = img.get("type") == "video" or "video" in str(img.get("image_url", "")).lower()
                    if filter_type == 'videos' and not is_video:
                        continue
                    if filter_type == 'images' and is_video:
                        continue
                    
                    char_id = img.get("character_id", "")
                    prompt_text = img.get("prompt", "")
                    all_items.append({
                        "id": str(img["_id"]),
                        "image_url": img.get("image_url", ""),
                        "thumbnail_url": img.get("thumbnail_url"),
                        "medium_url": img.get("medium_url"),
                        "prompt": prompt_text[:100] if prompt_text else "",
                        "name": img.get("name", ""),
                        "source": "character-gallery",
                        "type": "video" if is_video else "image",
                        "is_animation": is_video,
                        "character_id": char_id,
                        "character_name": char_map.get(char_id, ""),
                        "created_at": safe_isoformat(img.get("created_at"))
                    })
        
        # Sort all items by created_at (newest first)
        all_items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        
        # Get total count and paginate
        total = len(all_items)
        paginated_items = all_items[skip:skip + limit]
        
        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": skip + limit < total
        }
    
    except Exception as e:
        logging.error(f"Unified gallery error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load gallery")


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
    app_url = os.environ.get("APP_URL", "https://azories.com")
    
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
    
    # Send emails directly (await instead of background_tasks for async functions)
    if email_configured():
        try:
            # Send to admin email
            await send_email(admin_email, subject, html_content)
            logging.info(f"Admin notification email sent for book {book_id} to {admin_email}")
            
            # Also send to backup admin if configured
            backup_admin = os.environ.get("BACKUP_ADMIN_EMAIL")
            if backup_admin and backup_admin != admin_email:
                await send_email(backup_admin, subject, html_content)
                logging.info(f"Backup admin notification sent for book {book_id} to {backup_admin}")
        except Exception as e:
            logging.error(f"Failed to send admin email for book {book_id}: {e}")
        
        # Also send confirmation email to the author
        author_email = current_user.get("email")
        if author_email:
            author_subject = f"📚 Your book '{book['title']}' has been submitted for review"
            author_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #7c3aed, #a855f7); padding: 20px; border-radius: 12px 12px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">📚 Book Submitted!</h1>
                </div>
                
                <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                    <h2 style="color: #1f2937; margin-top: 0;">Hi {current_user.get('name', 'Author')}! 👋</h2>
                    
                    <p style="color: #4b5563; line-height: 1.6;">
                        Great news! Your book <strong>"{book['title']}"</strong> has been successfully submitted for review.
                    </p>
                    
                    <div style="background: #f3f4f6; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <h3 style="color: #374151; margin: 0 0 10px 0;">What happens next?</h3>
                        <ol style="color: #4b5563; margin: 0; padding-left: 20px; line-height: 1.8;">
                            <li>Our team will review your book for content quality</li>
                            <li>You'll receive an email once the review is complete</li>
                            <li>If approved, your book will be published to the library!</li>
                        </ol>
                    </div>
                    
                    <p style="color: #4b5563; line-height: 1.6;">
                        Review typically takes <strong>1-2 business days</strong>. We'll notify you as soon as there's an update.
                    </p>
                    
                    <div style="text-align: center; margin: 25px 0;">
                        <a href="{app_url}/dashboard" style="background: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">View Your Books</a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                    <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                        Questions? Reply to this email or contact us at books@azories.com<br>
                        © 2026 Azories. Happy storytelling! ✨
                    </p>
                </div>
            </body>
            </html>
            """
            try:
                await send_email(author_email, author_subject, author_html)
                logging.info(f"Author confirmation email sent for book {book_id} to {author_email}")
            except Exception as e:
                logging.error(f"Failed to send author email for book {book_id}: {e}")
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


@api_router.get("/admin/books")
async def admin_get_all_books(
    limit: int = 100,
    skip: int = 0,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """Get all books for admin (with optional status filter)"""
    query = {}
    if status:
        if status == "published":
            query["is_published"] = True
        elif status == "draft":
            query["publish_status"] = "draft"
        elif status == "pending":
            query["publish_status"] = "pending_review"
    
    total = await db.books.count_documents(query)
    books = await db.books.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "books": books,
        "total": total,
        "limit": limit,
        "skip": skip
    }


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
            "coming_soon": False,  # Clear coming_soon flag when published
            "status": "published",  # Update status to published
            "published_at": datetime.now(timezone.utc).isoformat(),  # Track when published
            "approved_by": admin.get("username", "Admin"),
            "approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send approval email to creator
    if author_email and email_configured():
        app_url = os.environ.get("APP_URL", "https://azories.com")
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
        app_url = os.environ.get("APP_URL", "https://azories.com")
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


class BulkHideBooksRequest(BaseModel):
    book_ids: List[str]
    hidden: bool = True


@api_router.put("/admin/books/bulk-hide")
async def admin_bulk_hide_books(request: BulkHideBooksRequest, current_user: dict = Depends(get_current_user)):
    """Admin endpoint to hide/unhide multiple books from the public library.
    Hidden books remain in the database but are not shown in the public library.
    Requires admin role or VIP user."""
    
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin" or user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    updated_count = 0
    not_found = []
    
    for book_id in request.book_ids:
        result = await db.books.update_one(
            {"id": book_id},
            {"$set": {"hidden": request.hidden, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count > 0:
            updated_count += 1
        else:
            not_found.append(book_id)
    
    return {
        "success": True,
        "updated_count": updated_count,
        "not_found": not_found,
        "message": f"Successfully {'hid' if request.hidden else 'unhid'} {updated_count} books"
    }


@api_router.get("/admin/hidden-books")
async def admin_get_hidden_books(current_user: dict = Depends(get_current_user)):
    """Get all hidden books (admin/VIP only)"""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin" or user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    hidden_books = await db.books.find(
        {"hidden": True},
        {"_id": 0}
    ).to_list(100)
    
    return {"books": hidden_books, "count": len(hidden_books)}


# ============ SITE-WIDE ANALYTICS ============

class AnalyticsEvent(BaseModel):
    event_type: str  # page_view, book_read, ai_story_create, signup, login, etc.
    page: Optional[str] = None
    book_id: Optional[str] = None
    metadata: Optional[dict] = None

@api_router.post("/analytics/track")
async def track_analytics_event(event: AnalyticsEvent, request: Request):
    """Track an analytics event (anonymous or authenticated)"""
    # Get user info if authenticated
    user_id = None
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
    except:
        pass
    
    # Create analytics record
    analytics_record = {
        "id": str(uuid.uuid4()),
        "event_type": event.event_type,
        "page": event.page,
        "book_id": event.book_id,
        "user_id": user_id,
        "metadata": event.metadata or {},
        "ip_hash": hashlib.sha256(request.client.host.encode()).hexdigest()[:16] if request.client else None,
        "user_agent": request.headers.get("User-Agent", "")[:200],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }
    
    await db.site_analytics.insert_one(analytics_record)
    return {"success": True}


@api_router.get("/admin/site-analytics")
async def get_site_analytics(
    days: int = 30,
    admin: dict = Depends(get_admin_user)
):
    """Get comprehensive site analytics (admin only)"""
    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Get total users
    total_users = await db.users.count_documents({})
    
    # Get users created in period
    new_users = await db.users.count_documents({
        "created_at": {"$gte": from_date}
    })
    
    # Get total books
    total_books = await db.books.count_documents({})
    published_books = await db.books.count_documents({"is_published": True})
    
    # Get page views by day
    pipeline = [
        {"$match": {"date": {"$gte": from_date}, "event_type": "page_view"}},
        {"$group": {"_id": "$date", "views": {"$sum": 1}, "unique_visitors": {"$addToSet": "$ip_hash"}}},
        {"$project": {"date": "$_id", "views": 1, "unique_visitors": {"$size": "$unique_visitors"}}},
        {"$sort": {"date": 1}}
    ]
    daily_views = await db.site_analytics.aggregate(pipeline).to_list(100)
    
    # Get unique visitors total
    unique_visitors_pipeline = [
        {"$match": {"date": {"$gte": from_date}}},
        {"$group": {"_id": "$ip_hash"}},
        {"$count": "total"}
    ]
    unique_result = await db.site_analytics.aggregate(unique_visitors_pipeline).to_list(1)
    unique_visitors = unique_result[0]["total"] if unique_result else 0
    
    # Get popular pages
    popular_pages_pipeline = [
        {"$match": {"date": {"$gte": from_date}, "event_type": "page_view"}},
        {"$group": {"_id": "$page", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$limit": 10}
    ]
    popular_pages = await db.site_analytics.aggregate(popular_pages_pipeline).to_list(10)
    
    # Get popular books (by reads)
    popular_books_pipeline = [
        {"$match": {"date": {"$gte": from_date}, "event_type": "book_read"}},
        {"$group": {"_id": "$book_id", "reads": {"$sum": 1}}},
        {"$sort": {"reads": -1}},
        {"$limit": 10}
    ]
    popular_books_data = await db.site_analytics.aggregate(popular_books_pipeline).to_list(10)
    
    # Enrich with book titles
    popular_books = []
    for pb in popular_books_data:
        if pb["_id"]:
            book = await db.books.find_one({"id": pb["_id"]}, {"_id": 0, "title": 1, "cover_image": 1})
            if book:
                popular_books.append({
                    "book_id": pb["_id"],
                    "title": book.get("title", "Unknown"),
                    "cover_image": book.get("cover_image"),
                    "reads": pb["reads"]
                })
    
    # Get event counts
    event_counts_pipeline = [
        {"$match": {"date": {"$gte": from_date}}},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    event_counts = await db.site_analytics.aggregate(event_counts_pipeline).to_list(50)
    
    # Get AI stories created
    ai_stories_created = await db.site_analytics.count_documents({
        "date": {"$gte": from_date},
        "event_type": "ai_story_create"
    })
    
    # Get signups
    signups = await db.site_analytics.count_documents({
        "date": {"$gte": from_date},
        "event_type": "signup"
    })
    
    # Get total page views
    total_page_views = await db.site_analytics.count_documents({
        "date": {"$gte": from_date},
        "event_type": "page_view"
    })
    
    # Get recent users (last 20)
    recent_users = await db.users.find(
        {},
        {"_id": 0, "id": 1, "email": 1, "name": 1, "created_at": 1, "credits": 1, "role": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {
        "period_days": days,
        "from_date": from_date,
        "summary": {
            "total_users": total_users,
            "new_users": new_users,
            "unique_visitors": unique_visitors,
            "total_page_views": total_page_views,
            "total_books": total_books,
            "published_books": published_books,
            "ai_stories_created": ai_stories_created,
            "signups": signups
        },
        "daily_views": daily_views,
        "popular_pages": [{"page": p["_id"], "views": p["views"]} for p in popular_pages],
        "popular_books": popular_books,
        "event_counts": [{"event": e["_id"], "count": e["count"]} for e in event_counts],
        "recent_users": recent_users
    }


@api_router.get("/admin/analytics-timeseries")
async def get_analytics_timeseries(
    period: str = "daily",  # daily, weekly, monthly
    days: int = 30,
    admin: dict = Depends(get_admin_user)
):
    """
    Get time-series analytics data for line graphs (admin only)
    Returns data grouped by day/week/month for various metrics
    """
    from_date = datetime.now(timezone.utc) - timedelta(days=days)
    from_date_str = from_date.strftime("%Y-%m-%d")
    
    # Helper to generate date range
    def generate_date_range(start_date, num_days):
        dates = []
        for i in range(num_days):
            d = start_date + timedelta(days=i)
            dates.append(d.strftime("%Y-%m-%d"))
        return dates
    
    date_range = generate_date_range(from_date, days)
    
    # Initialize data structure with all dates (to fill gaps)
    daily_data = {d: {
        "date": d,
        "page_views": 0,
        "unique_visitors": 0,
        "signups": 0,
        "book_reads": 0,
        "ai_stories": 0,
        "books_created": 0
    } for d in date_range}
    
    # Get page views by day
    page_views_pipeline = [
        {"$match": {"date": {"$gte": from_date_str}, "event_type": "page_view"}},
        {"$group": {
            "_id": "$date",
            "count": {"$sum": 1},
            "unique_ips": {"$addToSet": "$ip_hash"}
        }}
    ]
    page_views = await db.site_analytics.aggregate(page_views_pipeline).to_list(100)
    for pv in page_views:
        if pv["_id"] in daily_data:
            daily_data[pv["_id"]]["page_views"] = pv["count"]
            daily_data[pv["_id"]]["unique_visitors"] = len(pv.get("unique_ips", []))
    
    # Get signups by day
    signups_pipeline = [
        {"$match": {"date": {"$gte": from_date_str}, "event_type": "signup"}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}}
    ]
    signups = await db.site_analytics.aggregate(signups_pipeline).to_list(100)
    for s in signups:
        if s["_id"] in daily_data:
            daily_data[s["_id"]]["signups"] = s["count"]
    
    # Get book reads by day
    reads_pipeline = [
        {"$match": {"date": {"$gte": from_date_str}, "event_type": "book_read"}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}}
    ]
    reads = await db.site_analytics.aggregate(reads_pipeline).to_list(100)
    for r in reads:
        if r["_id"] in daily_data:
            daily_data[r["_id"]]["book_reads"] = r["count"]
    
    # Get AI stories created by day
    ai_pipeline = [
        {"$match": {"date": {"$gte": from_date_str}, "event_type": "ai_story_create"}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}}
    ]
    ai_stories = await db.site_analytics.aggregate(ai_pipeline).to_list(100)
    for a in ai_stories:
        if a["_id"] in daily_data:
            daily_data[a["_id"]]["ai_stories"] = a["count"]
    
    # Get books created by day (from books collection)
    books_pipeline = [
        {"$match": {"created_at": {"$gte": from_date_str}}},
        {"$project": {"date": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}}
    ]
    books_created = await db.books.aggregate(books_pipeline).to_list(100)
    for b in books_created:
        if b["_id"] in daily_data:
            daily_data[b["_id"]]["books_created"] = b["count"]
    
    # Convert to sorted list
    daily_list = sorted(daily_data.values(), key=lambda x: x["date"])
    
    # Aggregate by week if requested
    if period == "weekly":
        weekly_data = {}
        for d in daily_list:
            week_start = datetime.strptime(d["date"], "%Y-%m-%d")
            week_start = week_start - timedelta(days=week_start.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "date": week_key,
                    "week_label": f"Week of {week_start.strftime('%b %d')}",
                    "page_views": 0,
                    "unique_visitors": 0,
                    "signups": 0,
                    "book_reads": 0,
                    "ai_stories": 0,
                    "books_created": 0
                }
            
            weekly_data[week_key]["page_views"] += d["page_views"]
            weekly_data[week_key]["unique_visitors"] += d["unique_visitors"]
            weekly_data[week_key]["signups"] += d["signups"]
            weekly_data[week_key]["book_reads"] += d["book_reads"]
            weekly_data[week_key]["ai_stories"] += d["ai_stories"]
            weekly_data[week_key]["books_created"] += d["books_created"]
        
        return {
            "period": "weekly",
            "days": days,
            "data": sorted(weekly_data.values(), key=lambda x: x["date"])
        }
    
    # Aggregate by month if requested
    elif period == "monthly":
        monthly_data = {}
        for d in daily_list:
            month_key = d["date"][:7]  # YYYY-MM
            month_label = datetime.strptime(d["date"], "%Y-%m-%d").strftime("%B %Y")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "date": month_key,
                    "month_label": month_label,
                    "page_views": 0,
                    "unique_visitors": 0,
                    "signups": 0,
                    "book_reads": 0,
                    "ai_stories": 0,
                    "books_created": 0
                }
            
            monthly_data[month_key]["page_views"] += d["page_views"]
            monthly_data[month_key]["unique_visitors"] += d["unique_visitors"]
            monthly_data[month_key]["signups"] += d["signups"]
            monthly_data[month_key]["book_reads"] += d["book_reads"]
            monthly_data[month_key]["ai_stories"] += d["ai_stories"]
            monthly_data[month_key]["books_created"] += d["books_created"]
        
        return {
            "period": "monthly",
            "days": days,
            "data": sorted(monthly_data.values(), key=lambda x: x["date"])
        }
    
    # Default: daily
    return {
        "period": "daily",
        "days": days,
        "data": daily_list
    }


@api_router.get("/admin/users")
async def get_all_users(
    search: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    admin: dict = Depends(get_admin_user)
):
    """Get all users with search capability (admin only)"""
    query = {}
    if search:
        query = {
            "$or": [
                {"email": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}}
            ]
        }
    
    total = await db.users.count_documents(query)
    users = await db.users.find(
        query,
        {"_id": 0, "password": 0, "password_reset_token": 0}  # Exclude sensitive fields
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "users": users,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@api_router.get("/admin/user/{user_id}")
async def get_user_details(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get detailed user information (admin only)"""
    user = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "password": 0, "password_reset_token": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's books
    user_books = await db.books.find(
        {"author_id": user_id},
        {"_id": 0, "id": 1, "title": 1, "is_published": 1, "publish_status": 1, "created_at": 1}
    ).to_list(100)
    
    # Get user's activity
    user_activity = await db.site_analytics.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    # Get credit history
    credit_history = await db.credit_usage.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    return {
        "user": user,
        "books": user_books,
        "recent_activity": user_activity,
        "credit_history": credit_history
    }


# ============ AUDIO CACHING / PRE-GENERATION ============

@api_router.post("/admin/generate-narration-batch")
async def admin_generate_narration_batch(
    background_tasks: BackgroundTasks,
    book_ids: Optional[List[str]] = None,
    all_published: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Pre-generate and cache narration for books (admin only).
    - If book_ids provided: generate for those specific books
    - If all_published=True: generate for all published books
    """
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin" or user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get books to process
    if book_ids:
        books = await db.books.find({"id": {"$in": book_ids}}, {"_id": 0}).to_list(100)
    elif all_published:
        books = await db.books.find(
            {"is_published": True, "hidden": {"$ne": True}},
            {"_id": 0}
        ).to_list(100)
    else:
        raise HTTPException(status_code=400, detail="Provide book_ids or set all_published=True")
    
    # Schedule background task for narration generation
    background_tasks.add_task(generate_narration_for_books, [b["id"] for b in books])
    
    return {
        "success": True,
        "message": f"Started narration generation for {len(books)} books",
        "books_queued": len(books)
    }


async def generate_narration_for_books(book_ids: List[str]):
    """Background task to generate narration for multiple books"""
    import base64
    
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        logger.error("EMERGENT_LLM_KEY not set, cannot generate narration")
        return
    
    voice_mapping = {
        "21m00Tcm4TlvDq8ikWAM": "nova",
        "AZnzlk1XvdvUeBnXmlld": "shimmer",
        "EXAVITQu4vr4xnSDxMaL": "alloy",
        "ErXwobaYiN019PkySvjV": "onyx",
        "MF3mGyEYCl7XYWbV9V6O": "coral",
        "TxGEqnHWrfWFTfGW9XjX": "echo",
        "VR6AewLTigWG4xSOukaG": "fable",
        "pNInz6obpgDQGcFmaJgB": "sage",
        "yoZ06aMxZJJ28mfd3POQ": "ash",
    }
    
    total_pages = 0
    cached_pages = 0
    generated_pages = 0
    errors = 0
    
    for book_id in book_ids:
        try:
            book = await db.books.find_one({"id": book_id})
            if not book:
                continue
            
            voice_id = book.get("narrator_voice_id", "21m00Tcm4TlvDq8ikWAM")
            openai_voice = voice_mapping.get(voice_id, "nova")
            
            # Get all chapters for this book
            chapters = await db.chapters.find({"book_id": book_id}).to_list(50)
            
            for chapter in chapters:
                pages = await db.pages.find({"chapter_id": chapter["id"]}).to_list(100)
                
                for page in pages:
                    total_pages += 1
                    
                    # Skip if already has audio
                    if page.get("audio_url") and page["audio_url"].startswith("https://"):
                        cached_pages += 1
                        continue
                    
                    text = page.get("text_content", "").strip()
                    if not text:
                        continue
                    
                    try:
                        # Generate TTS
                        tts = OpenAITextToSpeech(api_key=emergent_key)
                        audio_base64 = await tts.generate_speech_base64(
                            text=text,
                            model="tts-1",
                            voice=openai_voice,
                            response_format="mp3"
                        )
                        
                        # Upload to Cloudinary
                        audio_bytes = base64.b64decode(audio_base64)
                        upload_result = cloudinary.uploader.upload(
                            audio_bytes,
                            resource_type="video",
                            folder=f"azories/audio/books/{book_id}",
                            public_id=f"page_{page['id']}",
                            format="mp3"
                        )
                        cloudinary_url = upload_result.get("secure_url")
                        
                        # Update page with audio URL
                        await db.pages.update_one(
                            {"id": page["id"]},
                            {"$set": {"audio_url": cloudinary_url}}
                        )
                        
                        generated_pages += 1
                        logger.info(f"Generated narration for page {page['id']} in book {book_id}")
                        
                        # Small delay to avoid rate limits
                        await asyncio.sleep(0.5)
                        
                    except Exception as page_error:
                        errors += 1
                        logger.error(f"Error generating narration for page {page['id']}: {page_error}")
                        
        except Exception as book_error:
            logger.error(f"Error processing book {book_id}: {book_error}")
    
    logger.info(f"Narration batch complete: {total_pages} total, {cached_pages} already cached, {generated_pages} generated, {errors} errors")


@api_router.get("/admin/narration-status")
async def admin_get_narration_status(current_user: dict = Depends(get_current_user)):
    """Get narration caching status for all published books (admin only)"""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin" or user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all published books
    books = await db.books.find(
        {"is_published": True, "hidden": {"$ne": True}},
        {"_id": 0, "id": 1, "title": 1}
    ).to_list(100)
    
    book_status = []
    total_pages = 0
    total_cached = 0
    
    for book in books:
        chapters = await db.chapters.find({"book_id": book["id"]}).to_list(50)
        book_pages = 0
        book_cached = 0
        
        for chapter in chapters:
            pages = await db.pages.find({"chapter_id": chapter["id"]}).to_list(100)
            for page in pages:
                if page.get("text_content", "").strip():
                    book_pages += 1
                    total_pages += 1
                    if page.get("audio_url") and page["audio_url"].startswith("https://"):
                        book_cached += 1
                        total_cached += 1
        
        book_status.append({
            "id": book["id"],
            "title": book["title"],
            "total_pages": book_pages,
            "cached_pages": book_cached,
            "percent_cached": round(book_cached / book_pages * 100, 1) if book_pages > 0 else 0
        })
    
    return {
        "total_books": len(books),
        "total_pages": total_pages,
        "total_cached": total_cached,
        "percent_cached": round(total_cached / total_pages * 100, 1) if total_pages > 0 else 0,
        "books": book_status
    }




class UpdatePageImageRequest(BaseModel):
    page_index: int
    image_url: str
    chapter_index: int = 0
    source: str = "chapters"  # "chapters" or "pages"


@api_router.put("/admin/books/{book_id}/page-image")
async def admin_update_page_image(book_id: str, request: UpdatePageImageRequest, current_user: dict = Depends(get_current_user)):
    """Admin endpoint to update embedded page image URL directly"""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin" or user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if request.source == "chapters":
        chapters = book.get("chapters", [])
        if request.chapter_index >= len(chapters):
            raise HTTPException(status_code=400, detail="Chapter index out of range")
        chapter = chapters[request.chapter_index]
        pages = chapter.get("pages", [])
        if request.page_index >= len(pages):
            raise HTTPException(status_code=400, detail="Page index out of range")
        
        # Update the page image URL
        chapters[request.chapter_index]["pages"][request.page_index]["image_url"] = request.image_url
        await db.books.update_one(
            {"id": book_id},
            {"$set": {"chapters": chapters, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        pages = book.get("pages", [])
        if request.page_index >= len(pages):
            raise HTTPException(status_code=400, detail="Page index out of range")
        
        pages[request.page_index]["image_url"] = request.image_url
        await db.books.update_one(
            {"id": book_id},
            {"$set": {"pages": pages, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"success": True, "message": f"Updated page {request.page_index + 1} image"}


@api_router.put("/admin/books/{book_id}/bulk-page-images")
async def admin_bulk_update_page_images(book_id: str, updates: List[UpdatePageImageRequest], current_user: dict = Depends(get_current_user)):
    """Admin endpoint to bulk update multiple page images for a book"""
    user_email = current_user.get("email", "").lower()
    is_admin = current_user.get("role") == "admin" or user_email in [v.lower() for v in VIP_USERS]
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    chapters = book.get("chapters", [])
    pages = book.get("pages", [])
    updated_count = 0
    
    logger.info(f"Bulk update for {book_id}: chapters={len(chapters)}, pages={len(pages)}, updates={len(updates)}")
    
    for update in updates:
        try:
            if update.source == "chapters" and chapters:
                logger.info(f"  Updating chapters[{update.chapter_index}].pages[{update.page_index}]")
                if update.chapter_index < len(chapters):
                    ch_pages = chapters[update.chapter_index].get("pages", [])
                    logger.info(f"    ch_pages length: {len(ch_pages)}")
                    if update.page_index < len(ch_pages):
                        chapters[update.chapter_index]["pages"][update.page_index]["image_url"] = update.image_url
                        updated_count += 1
                        logger.info("    Updated!")
            elif update.source == "pages" and pages:
                if update.page_index < len(pages):
                    pages[update.page_index]["image_url"] = update.image_url
                    updated_count += 1
        except Exception as e:
            logger.error(f"Error updating page {update.page_index}: {e}")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if chapters:
        update_data["chapters"] = chapters
    if pages:
        update_data["pages"] = pages
    
    await db.books.update_one({"id": book_id}, {"$set": update_data})
    
    return {"success": True, "updated_count": updated_count, "message": f"Updated {updated_count} page images"}

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

@api_router.get("/admin/books/{book_id}/full")
async def admin_get_full_book(book_id: str, admin: dict = Depends(get_admin_user)):
    """Admin endpoint to get complete book with all pages - no user auth required"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = set_book_defaults(book)
    
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
        "chapters": full_chapters
    }


# ==========================================================================================
# SYSTEM STATUS ENDPOINTS
# ==========================================================================================

@api_router.get("/admin/system-status")
async def get_system_status(admin: dict = Depends(get_admin_user)):
    """Get system status including API key validation (admin only)"""
    
    # Get FAL_KEY status
    fal_status = get_fal_key_status() if get_fal_key_status else {"valid": None, "error_message": "Not available"}
    
    # Check Emergent Key
    emergent_key = os.environ.get('EMERGENT_LLM_KEY', '')
    emergent_status = {
        "configured": bool(emergent_key and len(emergent_key) > 10),
        "masked_key": f"{emergent_key[:15]}..." if emergent_key else None
    }
    
    # Get FAL_KEY masked
    fal_key = os.environ.get('FAL_KEY', '')
    fal_masked = f"{fal_key[:15]}...{fal_key[-6:]}" if len(fal_key) > 21 else "Not set"
    
    return {
        "fal_ai": {
            **fal_status,
            "masked_key": fal_masked,
            "help_url": "https://fal.ai/dashboard/keys"
        },
        "emergent_key": emergent_status,
        "stripe": {
            "configured": bool(os.environ.get('STRIPE_API_KEY')),
            "mode": "live" if os.environ.get('STRIPE_API_KEY', '').startswith('sk_live') else "test"
        },
        "brevo_email": {
            "configured": bool(os.environ.get('BREVO_API_KEY'))
        },
        "cloudinary": {
            "configured": bool(os.environ.get('CLOUDINARY_API_KEY'))
        },
        "database": {
            "connected": True,  # If we got here, DB is connected
            "name": os.environ.get('DB_NAME', 'unknown')
        }
    }


@api_router.post("/admin/validate-fal-key")
async def admin_validate_fal_key(admin: dict = Depends(get_admin_user)):
    """Force re-validation of FAL_KEY (admin only)"""
    if not validate_fal_key_on_startup:
        return {"success": False, "error": "FAL validation not available"}
    
    try:
        status = await validate_fal_key_on_startup()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

class UpdateFalKeyRequest(BaseModel):
    fal_key: str

@api_router.post("/admin/update-fal-key")
async def admin_update_fal_key(request: UpdateFalKeyRequest, admin: dict = Depends(get_admin_user)):
    """Update FAL_KEY at runtime and persist to .env file (admin only)"""
    import fal_client
    
    new_key = request.fal_key.strip()
    if not new_key or ':' not in new_key:
        return {"success": False, "error": "Invalid key format. Expected format: key_id:key_secret"}
    
    try:
        # Test the new key first
        os.environ['FAL_KEY'] = new_key
        
        handler = await fal_client.submit_async(
            "fal-ai/flux/schnell",
            arguments={"prompt": "test", "image_size": "square", "num_images": 1}
        )
        result = await handler.get()
        
        if not result or not result.get('images'):
            return {"success": False, "error": "Key test failed - no images returned"}
        
        # Key works! Update the .env file
        env_path = '/app/backend/.env'
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith('FAL_KEY='):
                new_lines.append(f'FAL_KEY={new_key}\n')
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            new_lines.append(f'FAL_KEY={new_key}\n')
        
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        # ALSO persist to database for cross-deployment persistence
        await db.system_settings.update_one(
            {"key": "fal_api_key"},
            {"$set": {
                "key": "fal_api_key",
                "value": new_key,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": admin.get("username", "admin")
            }},
            upsert=True
        )
        
        # Re-validate and update cached status
        if validate_fal_key_on_startup:
            await validate_fal_key_on_startup()
        
        logger.info("FAL_KEY updated successfully by admin and persisted to database")
        
        return {
            "success": True,
            "message": "FAL_KEY updated, validated, and persisted to database successfully",
            "key_preview": f"{new_key[:15]}...{new_key[-10:]}",
            "persisted": True
        }
        
    except Exception as e:
        return {"success": False, "error": f"Key validation failed: {str(e)}"}


# ==========================================================================================
# CONTACT FORM
# ==========================================================================================

class ContactRequest(BaseModel):
    name: str
    email: str
    subject: Optional[str] = ""
    category: str = "general"
    message: str

@api_router.post("/contact")
async def submit_contact_form(request: ContactRequest, background_tasks: BackgroundTasks):
    """Handle contact form submissions - sends email to admin"""
    
    category_labels = {
        "general": "General Inquiry",
        "support": "Technical Support",
        "publishing": "Book Publishing",
        "business": "Business & Partnerships"
    }
    
    category_label = category_labels.get(request.category, "General Inquiry")
    subject_line = request.subject or f"{category_label} from {request.name}"
    
    # Email to admin
    admin_email = os.environ.get("ADMIN_NOTIFY_EMAIL", "books@azories.com")
    backup_email = os.environ.get("BACKUP_ADMIN_EMAIL")
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #7c3aed, #a855f7); padding: 20px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">📬 New Contact Message</h1>
        </div>
        
        <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; width: 120px;"><strong>From:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{request.name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">
                        <a href="mailto:{request.email}" style="color: #7c3aed;">{request.email}</a>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Category:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{category_label}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Subject:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{request.subject or 'No subject'}</td>
                </tr>
            </table>
            
            <div style="background: #f9fafb; border-radius: 8px; padding: 15px; margin: 20px 0;">
                <h3 style="color: #374151; margin: 0 0 10px 0;">Message:</h3>
                <p style="color: #4b5563; line-height: 1.6; white-space: pre-wrap; margin: 0;">{request.message}</p>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <a href="mailto:{request.email}?subject=Re: {subject_line}" 
                   style="background: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                    Reply to {request.name}
                </a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                This message was sent from the Azories contact form.
            </p>
        </div>
    </body>
    </html>
    """
    
    if email_configured():
        # Send to primary admin
        background_tasks.add_task(send_email, admin_email, f"[Azories Contact] {subject_line}", html_content)
        logging.info(f"Contact form email sent to {admin_email} from {request.email}")
        
        # Send to backup admin if configured
        if backup_email and backup_email != admin_email:
            background_tasks.add_task(send_email, backup_email, f"[BACKUP] [Azories Contact] {subject_line}", html_content)
        
        # Send confirmation to user
        confirmation_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #7c3aed, #a855f7); padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">📬 Message Received!</h1>
            </div>
            
            <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1f2937; margin-top: 0;">Hi {request.name}! 👋</h2>
                
                <p style="color: #4b5563; line-height: 1.6;">
                    Thank you for reaching out to Azories! We've received your message and will get back to you as soon as possible.
                </p>
                
                <div style="background: #f3f4f6; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <p style="color: #6b7280; margin: 0;"><strong>Your message:</strong></p>
                    <p style="color: #4b5563; margin: 10px 0 0 0; font-style: italic;">"{request.message[:200]}{'...' if len(request.message) > 200 else ''}"</p>
                </div>
                
                <p style="color: #4b5563; line-height: 1.6;">
                    We typically respond within <strong>1-2 business days</strong>.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                    © 2026 Azories. Happy storytelling! ✨
                </p>
            </div>
        </body>
        </html>
        """
        background_tasks.add_task(send_email, request.email, "We received your message - Azories", confirmation_html)
    
    # Also save to database for records
    contact_record = {
        "name": request.name,
        "email": request.email,
        "subject": request.subject,
        "category": request.category,
        "message": request.message,
        "created_at": datetime.now(timezone.utc),
        "status": "new"
    }
    await db.contact_messages.insert_one(contact_record)
    
    return {"success": True, "message": "Message sent successfully"}



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

# Export endpoints for downloading book data
@api_router.get("/admin/exports")
async def list_exports(admin: dict = Depends(get_admin_user)):
    """List available export files"""
    export_dir = Path("/app/exports")
    if not export_dir.exists():
        return {"files": []}
    
    files = []
    for f in export_dir.glob("*.json"):
        files.append({
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "download_url": f"/api/admin/exports/{f.name}"
        })
    
    return {"files": sorted(files, key=lambda x: x["filename"])}

@api_router.get("/admin/exports/{filename}")
async def download_export(filename: str, admin: dict = Depends(get_admin_user)):
    """Download an export file"""
    from fastapi.responses import FileResponse
    
    export_path = Path(f"/app/exports/{filename}")
    if not export_path.exists() or not filename.endswith('.json'):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    return FileResponse(
        path=export_path,
        filename=filename,
        media_type="application/json"
    )

@api_router.post("/admin/imports/books")
async def import_books(admin: dict = Depends(get_admin_user)):
    """Import books from JSON data. Accepts file upload."""
    from fastapi import File, UploadFile
    # This endpoint handles the actual import - see import_books_file below
    return {"error": "Use POST with file upload"}

@api_router.post("/admin/imports/books/upload")
async def import_books_file(
    file: UploadFile = File(...),
    admin: dict = Depends(get_admin_user)
):
    """Import books from uploaded JSON file"""
    import uuid
    from datetime import datetime
    
    try:
        # Read and parse the uploaded JSON
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Handle different JSON formats
        books_to_import = []
        
        # Format 1: {"books": [...]} (our export format)
        if isinstance(data, dict) and 'books' in data:
            books_to_import = data['books']
        # Format 2: [{"book": "title", "pages": [...]}] (text import format)
        elif isinstance(data, list) and len(data) > 0 and 'pages' in data[0]:
            books_to_import = data
        # Format 3: Direct array of books
        elif isinstance(data, list):
            books_to_import = data
        else:
            return {"success": False, "error": "Unrecognized JSON format"}
        
        imported_count = 0
        skipped_count = 0
        errors = []
        imported_titles = []
        
        for book_data in books_to_import:
            try:
                title = book_data.get('title', book_data.get('book', 'Unknown'))
                
                # Check if book already exists
                existing = await db.books.find_one({"title": title})
                if existing:
                    skipped_count += 1
                    continue
                
                # Generate new ID if not present
                if not book_data.get('id'):
                    book_data['id'] = str(uuid.uuid4())
                
                # Ensure required fields
                book_data.setdefault('title', title)
                book_data.setdefault('description', '')
                book_data.setdefault('genre', 'General')
                book_data.setdefault('is_published', True)
                book_data.setdefault('hidden', False)
                book_data.setdefault('author_id', admin.get('sub', 'admin'))
                book_data.setdefault('author_name', 'Azories')
                book_data.setdefault('created_at', datetime.utcnow().isoformat())
                book_data.setdefault('updated_at', datetime.utcnow().isoformat())
                book_data.setdefault('view_count', 0)
                book_data.setdefault('read_count', 0)
                
                # Handle pages - normalize text_content field
                pages = book_data.get('pages', [])
                normalized_pages = []
                for i, page in enumerate(pages):
                    normalized_page = {
                        'page_number': page.get('page_number', page.get('page', i + 1)),
                        'text_content': page.get('text_content', page.get('text', page.get('content', ''))),
                        'image_url': page.get('image_url', ''),
                        'layout': page.get('layout', 'standard')
                    }
                    normalized_pages.append(normalized_page)
                
                book_data['pages'] = normalized_pages
                
                # Insert into database
                await db.books.insert_one(book_data)
                imported_count += 1
                imported_titles.append(title)
                
            except Exception as e:
                errors.append(f"{title}: {str(e)}")
        
        return {
            "success": True,
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": len(errors),
            "error_details": errors[:10] if errors else [],
            "imported_titles": imported_titles[:20],
            "message": f"Successfully imported {imported_count} books, skipped {skipped_count} duplicates"
        }
        
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.post("/admin/imports/books/json")
async def import_books_json(
    request: Request,
    admin: dict = Depends(get_admin_user)
):
    """Import books from JSON body (for smaller imports)"""
    import uuid
    from datetime import datetime
    
    try:
        data = await request.json()
        
        # Handle different formats
        books_to_import = []
        if isinstance(data, dict) and 'books' in data:
            books_to_import = data['books']
        elif isinstance(data, list):
            books_to_import = data
        else:
            return {"success": False, "error": "Expected {books: [...]} or [...]"}
        
        imported_count = 0
        skipped_count = 0
        
        for book_data in books_to_import:
            title = book_data.get('title', 'Unknown')
            
            existing = await db.books.find_one({"title": title})
            if existing:
                skipped_count += 1
                continue
            
            if not book_data.get('id'):
                book_data['id'] = str(uuid.uuid4())
            
            book_data.setdefault('is_published', True)
            book_data.setdefault('hidden', False)
            book_data.setdefault('created_at', datetime.utcnow().isoformat())
            
            await db.books.insert_one(book_data)
            imported_count += 1
        
        return {
            "success": True,
            "imported": imported_count,
            "skipped": skipped_count,
            "message": f"Imported {imported_count} books"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# ADMIN DATABASE IMPORT ENDPOINT
# Import all collections from exported JSON files
# ============================================================

@api_router.get("/admin/import-collections")
async def list_import_collections(
    import_key: str = Query(..., description="Admin import key for security")
):
    """
    List all available collections for import with their sizes.
    Use this to see what can be imported, then import one at a time.
    """
    import glob
    
    IMPORT_KEY = os.environ.get('DB_IMPORT_KEY', 'azories-import-2026')
    if import_key != IMPORT_KEY:
        raise HTTPException(status_code=403, detail="Invalid import key")
    
    exports_path = "/app/exports/collections"
    
    if not os.path.exists(exports_path):
        return {"error": "Exports directory not found", "collections": []}
    
    json_files = glob.glob(os.path.join(exports_path, "*.json"))
    
    collections = []
    # Priority order - essential collections first, large caches last
    priority_order = ['users', 'books', 'chapters', 'pages', 'system_settings', 
                      'character_profiles', 'character_gallery', 'book_images',
                      'analytics', 'reading_history', 'favorites', 'follows', 'invites',
                      'credit_usage', 'vip_usage', 'password_resets', 'contact_messages',
                      'art_studio_animations', 'art_studio_workflows', 
                      'art_studio_generations', 'art_studio_gallery', 'audio_cache']
    
    for json_file in json_files:
        name = os.path.basename(json_file).replace('.json', '')
        size_mb = os.path.getsize(json_file) / (1024 * 1024)
        priority = priority_order.index(name) if name in priority_order else 99
        collections.append({
            "name": name,
            "file": json_file,
            "size_mb": round(size_mb, 2),
            "priority": priority,
            "recommended": size_mb < 10  # Recommend importing smaller files
        })
    
    # Sort by priority
    collections.sort(key=lambda x: x["priority"])
    
    return {
        "total_collections": len(collections),
        "collections": collections,
        "instructions": "Import collections one at a time using POST /api/admin/import-collection?collection=NAME&import_key=KEY"
    }


@api_router.post("/admin/import-collection")
async def import_single_collection(
    collection: str = Query(..., description="Collection name to import"),
    import_key: str = Query(..., description="Admin import key for security")
):
    """
    Import a SINGLE collection from exports. Use this to import one at a time
    to avoid timeout issues with large databases.
    """
    from bson import json_util
    
    IMPORT_KEY = os.environ.get('DB_IMPORT_KEY', 'azories-import-2026')
    if import_key != IMPORT_KEY:
        raise HTTPException(status_code=403, detail="Invalid import key")
    
    json_file = f"/app/exports/collections/{collection}.json"
    
    if not os.path.exists(json_file):
        raise HTTPException(status_code=404, detail=f"Collection '{collection}' not found")
    
    try:
        file_size = os.path.getsize(json_file) / (1024 * 1024)
        logger.info(f"Importing collection '{collection}' ({file_size:.2f} MB)...")
        
        with open(json_file, 'r') as f:
            documents = json_util.loads(f.read())
        
        if not documents:
            return {"collection": collection, "status": "skipped", "reason": "empty file", "documents": 0}
        
        # Get the collection and drop existing data
        coll = db[collection]
        await coll.drop()
        
        # Insert documents in batches to avoid memory issues
        if isinstance(documents, list) and len(documents) > 0:
            batch_size = 500
            total_inserted = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                result = await coll.insert_many(batch)
                total_inserted += len(result.inserted_ids)
            
            return {
                "collection": collection,
                "status": "success",
                "documents": total_inserted,
                "size_mb": round(file_size, 2)
            }
        else:
            return {"collection": collection, "status": "skipped", "reason": "no documents", "documents": 0}
            
    except Exception as e:
        logger.error(f"Error importing {collection}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@api_router.post("/admin/import-essential")
async def import_essential_collections(
    import_key: str = Query(..., description="Admin import key for security")
):
    """
    Import only the essential collections needed for the app to function.
    This is faster and avoids timeout issues. Skips large cache collections.
    """
    from bson import json_util
    
    IMPORT_KEY = os.environ.get('DB_IMPORT_KEY', 'azories-import-2026')
    if import_key != IMPORT_KEY:
        raise HTTPException(status_code=403, detail="Invalid import key")
    
    # Essential collections only - skip large caches
    essential = ['users', 'books', 'chapters', 'pages', 'system_settings',
                 'character_profiles', 'favorites', 'follows', 'invites',
                 'reading_history', 'analytics']
    
    results = {"imported": [], "skipped": [], "errors": []}
    
    for name in essential:
        json_file = f"/app/exports/collections/{name}.json"
        
        if not os.path.exists(json_file):
            results["skipped"].append({"collection": name, "reason": "file not found"})
            continue
        
        try:
            file_size = os.path.getsize(json_file) / (1024 * 1024)
            
            with open(json_file, 'r') as f:
                documents = json_util.loads(f.read())
            
            if not documents:
                results["skipped"].append({"collection": name, "reason": "empty"})
                continue
            
            coll = db[name]
            await coll.drop()
            
            if isinstance(documents, list) and len(documents) > 0:
                # Batch insert
                batch_size = 500
                total = 0
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    result = await coll.insert_many(batch)
                    total += len(result.inserted_ids)
                
                results["imported"].append({
                    "collection": name,
                    "documents": total,
                    "size_mb": round(file_size, 2)
                })
            
        except Exception as e:
            results["errors"].append({"collection": name, "error": str(e)})
    
    results["success"] = len(results["errors"]) == 0
    results["total_imported"] = len(results["imported"])
    
    return results


@api_router.post("/admin/import-database")
async def import_database_from_exports(
    import_key: str = Query(..., description="Admin import key for security")
):
    """
    Import all collections from /app/exports/collections/ into MongoDB.
    WARNING: This may timeout for large databases. Use /import-essential or /import-collection instead.
    """
    from bson import json_util
    import glob
    
    IMPORT_KEY = os.environ.get('DB_IMPORT_KEY', 'azories-import-2026')
    
    if import_key != IMPORT_KEY:
        raise HTTPException(status_code=403, detail="Invalid import key")
    
    exports_path = "/app/exports/collections"
    
    if not os.path.exists(exports_path):
        return {
            "success": False,
            "error": f"Exports directory not found at {exports_path}",
            "hint": "Use /api/admin/import-essential for faster import"
        }
    
    json_files = glob.glob(os.path.join(exports_path, "*.json"))
    
    if not json_files:
        return {"success": False, "error": "No JSON files found"}
    
    results = {
        "success": True,
        "collections_imported": 0,
        "total_documents": 0,
        "details": [],
        "errors": []
    }
    
    for json_file in json_files:
        collection_name = os.path.basename(json_file).replace('.json', '')
        
        try:
            with open(json_file, 'r') as f:
                documents = json_util.loads(f.read())
            
            if not documents:
                results["details"].append({"collection": collection_name, "status": "skipped", "reason": "empty"})
                continue
            
            collection = db[collection_name]
            await collection.drop()
            
            if isinstance(documents, list) and len(documents) > 0:
                # Batch insert for large collections
                batch_size = 500
                total = 0
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    result = await collection.insert_many(batch)
                    total += len(result.inserted_ids)
                count = total
            else:
                count = 0
            
            results["collections_imported"] += 1
            results["total_documents"] += count
            results["details"].append({"collection": collection_name, "status": "success", "documents": count})
            
        except Exception as e:
            results["errors"].append({"collection": collection_name, "error": str(e)})
    
    if results["errors"]:
        results["success"] = len(results["errors"]) < len(json_files)
    
    return results


@api_router.get("/admin/export-collection/{collection_name}")
async def export_collection_data(
    collection_name: str,
    import_key: str = Query(..., description="Admin import key for security")
):
    """
    Serve collection data from local export files via API.
    This allows production to fetch data from preview environment.
    """
    from bson import json_util
    
    IMPORT_KEY = os.environ.get('DB_IMPORT_KEY', 'azories-import-2026')
    if import_key != IMPORT_KEY:
        raise HTTPException(status_code=403, detail="Invalid import key")
    
    json_file = f"/app/exports/collections/{collection_name}.json"
    
    if not os.path.exists(json_file):
        raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' export not found")
    
    try:
        with open(json_file, 'r') as f:
            # Return raw JSON string to preserve BSON types
            return Response(content=f.read(), media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading export: {str(e)}")


@api_router.post("/admin/import-from-remote")
async def import_from_remote_url(
    collection: str = Query(..., description="Collection name to import"),
    source_url: str = Query(..., description="URL of the preview/source environment"),
    import_key: str = Query(..., description="Admin import key for security")
):
    """
    Fetch collection data from a remote URL and import it into the local database.
    Use this to import data from preview environment into production.
    
    Example:
    POST /api/admin/import-from-remote?collection=books&source_url=https://preview.example.com&import_key=KEY
    """
    from bson import json_util
    
    IMPORT_KEY = os.environ.get('DB_IMPORT_KEY', 'azories-import-2026')
    if import_key != IMPORT_KEY:
        raise HTTPException(status_code=403, detail="Invalid import key")
    
    # Construct the remote export URL
    remote_url = f"{source_url.rstrip('/')}/api/admin/export-collection/{collection}?import_key={import_key}"
    
    try:
        logger.info(f"Fetching {collection} from {source_url}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(remote_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Remote fetch failed: {error_text}")
                
                data_text = await response.text()
        
        # Parse the BSON-aware JSON
        documents = json_util.loads(data_text)
        
        if not documents:
            return {"collection": collection, "status": "skipped", "reason": "no documents", "documents": 0}
        
        # Drop and reimport
        coll = db[collection]
        await coll.drop()
        
        if isinstance(documents, list) and len(documents) > 0:
            # Batch insert
            batch_size = 500
            total = 0
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                result = await coll.insert_many(batch)
                total += len(result.inserted_ids)
            
            logger.info(f"Imported {total} documents into {collection}")
            return {"collection": collection, "status": "success", "documents": total}
        else:
            return {"collection": collection, "status": "skipped", "reason": "invalid data format", "documents": 0}
            
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching {collection}: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error importing {collection}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@api_router.delete("/admin/delete-test-accounts")
async def delete_test_accounts(admin: dict = Depends(get_admin_user)):
    """
    Delete all test accounts from the database.
    
    Test accounts are identified by:
    - Email containing "test" (case-insensitive)
    - Email ending with "@example.com"
    - Name containing "Test User" or "Test Author" etc.
    
    Protected accounts (will NOT be deleted):
    - jamesstephenbrooks@outlook.com
    - stories@azories.com
    - arianamillyb@icloud.com
    - palmbeach@hotmail.co.uk
    - dales.preloved.shop@gmail.com
    - mandybrooks151@hotmail.co.uk
    """
    protected_emails = [
        "jamesstephenbrooks@outlook.com",
        "stories@azories.com",
        "arianamillyb@icloud.com",
        "palmbeach@hotmail.co.uk",
        "dales.preloved.shop@gmail.com",
        "mandybrooks151@hotmail.co.uk"
    ]
    
    results = {
        "deleted_count": 0,
        "deleted_users": [],
        "protected_count": 0,
        "errors": []
    }
    
    try:
        # Find all test accounts
        test_query = {
            "$and": [
                {"email": {"$nin": protected_emails}},  # Not in protected list
                {"$or": [
                    {"email": {"$regex": "test", "$options": "i"}},  # Email contains "test"
                    {"email": {"$regex": "@example\\.com$", "$options": "i"}},  # @example.com emails
                    {"name": {"$regex": "^test", "$options": "i"}},  # Name starts with "test"
                    {"name": {"$regex": "test user", "$options": "i"}},  # Name contains "test user"
                ]}
            ]
        }
        
        # Get list of test users first
        test_users = await db.users.find(test_query, {"_id": 0, "id": 1, "email": 1, "name": 1}).to_list(500)
        
        if not test_users:
            return {"message": "No test accounts found", **results}
        
        # Delete each test user and their associated data
        for user in test_users:
            user_id = user.get("id")
            user_email = user.get("email", "Unknown")
            
            try:
                # Delete user's books
                await db.books.delete_many({"author_id": user_id})
                # Delete user's chapters (via book_id relationship would need more complex query)
                # Delete user's reading progress
                await db.reading_progress.delete_many({"user_id": user_id})
                # Delete user's book images
                await db.book_images.delete_many({"user_id": user_id})
                # Delete user's art studio gallery
                await db.art_studio_gallery.delete_many({"user_id": user_id})
                # Delete the user
                await db.users.delete_one({"id": user_id})
                
                results["deleted_users"].append({"email": user_email, "name": user.get("name", "")})
                results["deleted_count"] += 1
                
            except Exception as e:
                results["errors"].append(f"Error deleting {user_email}: {str(e)}")
        
        logger.info(f"Deleted {results['deleted_count']} test accounts")
        return results
        
    except Exception as e:
        logger.error(f"Error in delete_test_accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/seed-from-preview")
async def seed_from_preview(
    import_key: str = Query(..., description="Admin import key for security"),
    preview_url: str = Query(default="https://blank-screen-debug-3.preview.emergentagent.com", description="Preview environment URL")
):
    """
    Seed the production database with essential collections from the preview environment.
    This is a one-command solution to populate production after deployment.
    
    Essential collections: users, books, chapters, pages, book_images
    """
    from bson import json_util
    
    IMPORT_KEY = os.environ.get('DB_IMPORT_KEY', 'azories-import-2026')
    if import_key != IMPORT_KEY:
        raise HTTPException(status_code=403, detail="Invalid import key")
    
    # Essential collections in order of dependency
    essential_collections = ['users', 'books', 'chapters', 'pages', 'book_images', 'system_settings']
    
    results = {"imported": [], "failed": [], "skipped": []}
    
    async with aiohttp.ClientSession() as session:
        for collection in essential_collections:
            remote_url = f"{preview_url.rstrip('/')}/api/admin/export-collection/{collection}?import_key={import_key}"
            
            try:
                logger.info(f"Fetching {collection} from preview...")
                
                async with session.get(remote_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 404:
                        results["skipped"].append({"collection": collection, "reason": "not found in preview"})
                        continue
                    elif response.status != 200:
                        results["failed"].append({"collection": collection, "error": f"HTTP {response.status}"})
                        continue
                    
                    data_text = await response.text()
                
                documents = json_util.loads(data_text)
                
                if not documents or (isinstance(documents, list) and len(documents) == 0):
                    results["skipped"].append({"collection": collection, "reason": "empty"})
                    continue
                
                # Drop and reimport
                coll = db[collection]
                await coll.drop()
                
                if isinstance(documents, list):
                    batch_size = 500
                    total = 0
                    for i in range(0, len(documents), batch_size):
                        batch = documents[i:i + batch_size]
                        result = await coll.insert_many(batch)
                        total += len(result.inserted_ids)
                    
                    results["imported"].append({"collection": collection, "documents": total})
                    logger.info(f"✅ Imported {total} documents into {collection}")
                
            except Exception as e:
                logger.error(f"Error with {collection}: {str(e)}")
                results["failed"].append({"collection": collection, "error": str(e)})
    
    results["success"] = len(results["failed"]) == 0
    results["total_imported"] = len(results["imported"])
    
    return results


# Include the router
# Import print PDF generator
from services.print_pdf_generator import pdf_generator, generate_test_pdf

@api_router.get("/print/preview-bonus-pages/{book_id}")
async def download_bonus_pages_preview(book_id: str):
    """Download a preview PDF of all bonus pages for a specific book."""
    try:
        result = await generate_test_pdf(book_id, db)
        preview_path = result["path"]
        
        def iter_file():
            with open(preview_path, 'rb') as f:
                yield from f
        
        return StreamingResponse(
            iter_file(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=azories_print_preview_{book_id}.pdf"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


# ==================== STRIPE WEBHOOK ====================
@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for payment confirmations"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
    
    try:
        # Get raw body
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        # Initialize Stripe checkout (webhook URL not needed for handling)
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        
        # Handle the webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook received: {webhook_response.event_type}")
        
        # Process payment confirmation
        if webhook_response.event_type == "checkout.session.completed":
            session_id = webhook_response.session_id
            
            # Update transaction status
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "payment_status": webhook_response.payment_status,
                    "event_id": webhook_response.event_id,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # If paid, check if print order needs to be created
            if webhook_response.payment_status == "paid":
                transaction = await db.payment_transactions.find_one({"session_id": session_id})
                if transaction:
                    # Check if print order already exists
                    existing_order = await db.print_orders.find_one({
                        "payment_session_id": session_id
                    })
                    
                    if not existing_order:
                        order_id = str(uuid.uuid4())
                        await db.print_orders.insert_one({
                            "id": order_id,
                            "order_reference": transaction.get("order_reference"),
                            "book_id": transaction.get("book_id"),
                            "book_title": transaction.get("book_title"),
                            "user_id": transaction.get("user_id"),
                            "product_type": transaction.get("product_type"),
                            "status": "paid",
                            "payment_session_id": session_id,
                            "amount_paid": transaction.get("amount"),
                            "currency": transaction.get("currency"),
                            "shipping_country": transaction.get("shipping_country"),
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        })
                        logger.info(f"Print order created via webhook: {order_id}")
        
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        # Return 200 to acknowledge receipt (Stripe will retry on non-200)
        return {"received": True, "error": str(e)}


app.include_router(api_router)

# Note: CORS middleware is configured at the top of the file, right after app creation
# This ensures OPTIONS preflight requests are handled correctly
