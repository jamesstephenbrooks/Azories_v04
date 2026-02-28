"""
Shared database and configuration module
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Database connection
# In production, MONGO_URL is set by Emergent's deployment pipeline
# For local development, defaults to localhost
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'azories')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# JWT Configuration - no fallback for secret
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 7  # 7 days

# VIP Users - loaded from environment variable
VIP_USERS = [e.strip() for e in os.environ.get('VIP_USERS', '').split(',') if e.strip()]

# Credit costs for Pro Studio features
CREDIT_COSTS = {
    "flux_generate": 1,
    "flux_pro_generate": 2,
    "pulid_generate": 3,
    "lora_training": 50,
    "lora_generate": 2,
    "video_generate": 10,
}

# Actual costs to us (for tracking VIP usage)
ACTUAL_COSTS = {
    "flux_generate": 0.025,
    "flux_pro_generate": 0.05,
    "pulid_generate": 0.08,
    "lora_training": 2.00,
    "lora_generate": 0.05,
    "video_generate": 0.50,
}

# Credit packages for purchase
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

# Stripe configuration - no fallback, must be set
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# Emergent LLM Key (optional - used for fallback image generation)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# fal.ai configuration (optional - primary image generation)
FAL_KEY = os.environ.get('FAL_KEY', '')
