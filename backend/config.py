"""
Shared database and configuration module
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Database connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'azories')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 7  # 7 days

# VIP Users - loaded from environment variable in server.py
# VIP_USERS = os.environ.get('VIP_USERS', '').split(',')

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

# Stripe configuration
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# fal.ai configuration
FAL_KEY = os.environ.get('FAL_KEY', '')
