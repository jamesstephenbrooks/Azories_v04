"""
Credits routes for Azories API
Handles credit balance, purchases, and deductions
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/credits", tags=["Credits"])

# Get database from main app
db = None

def set_db(database):
    global db
    db = database

# VIP email addresses (exempt from credit charges)
VIP_EMAILS = ["arianamillb@icloud.com", "jamesstephenbrooks@outlook.com"]

# Credit costs for different operations
CREDIT_COSTS = {
    "flux_generate": 1,
    "flux_pro": 2,
    "pulid_generate": 3,
    "lora_training": 50,
    "lora_generate": 2,
    "video_generate": 10,
    "shots_generate": 5,
    "expression_generate": 2,
    "cinema_generate": 3,
    "sora_animation": 15,
}

# Actual costs (for VIP tracking)
ACTUAL_COSTS = {
    "flux_generate": 0.03,
    "flux_pro": 0.05,
    "pulid_generate": 0.08,
    "lora_training": 2.00,
    "lora_generate": 0.05,
    "video_generate": 0.50,
    "shots_generate": 0.25,
    "expression_generate": 0.06,
    "cinema_generate": 0.10,
    "sora_animation": 0.75,
}

async def deduct_credits(user_id: str, operation: str, db_instance=None) -> bool:
    """
    Deduct credits for an operation.
    VIP users are not charged but usage is tracked.
    Returns True if operation can proceed, False if insufficient credits.
    """
    database = db_instance or db
    cost = CREDIT_COSTS.get(operation, 1)
    actual_cost = ACTUAL_COSTS.get(operation, 0.05)
    
    user = await database.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return False
    
    is_vip = user.get("is_vip", False) or user.get("email", "").lower() in [e.lower() for e in VIP_EMAILS]
    
    if is_vip:
        # Track VIP usage for analytics but don't charge
        await database.analytics_events.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": "vip_credit_usage",
            "user_id": user_id,
            "operation": operation,
            "credits_would_cost": cost,
            "actual_cost": actual_cost,
            "timestamp": datetime.utcnow().isoformat()
        })
        return True
    
    # Check if user has enough credits
    current_credits = user.get("credits", 0)
    if current_credits < cost:
        return False
    
    # Deduct credits
    await database.users.update_one(
        {"id": user_id},
        {"$inc": {"credits": -cost}}
    )
    
    # Track usage
    await database.analytics_events.insert_one({
        "id": str(uuid.uuid4()),
        "event_type": "credit_usage",
        "user_id": user_id,
        "operation": operation,
        "credits_deducted": cost,
        "actual_cost": actual_cost,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return True

async def get_current_user_dependency():
    """Import get_current_user from auth module"""
    from routes.auth import get_current_user
    return get_current_user

@router.get("/balance")
async def get_credit_balance(current_user: dict = Depends(get_current_user_dependency)):
    return {
        "credits": current_user.get("credits", 0),
        "is_vip": current_user.get("is_vip", False),
        "costs": CREDIT_COSTS
    }

@router.post("/add")
async def add_credits(amount: int = 100, current_user: dict = Depends(get_current_user_dependency)):
    """
    Add credits to user account.
    Only VIP users can add credits directly (for testing).
    Regular users must purchase through Stripe.
    """
    is_vip = current_user.get("is_vip", False) or current_user.get("email", "").lower() in [e.lower() for e in VIP_EMAILS]
    
    if not is_vip:
        raise HTTPException(
            status_code=403, 
            detail="Credits must be purchased through the Credits page. Direct credit addition is only available for VIP users."
        )
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$inc": {"credits": amount}}
    )
    
    # Track VIP credit addition
    await db.analytics_events.insert_one({
        "id": str(uuid.uuid4()),
        "event_type": "vip_credit_addition",
        "user_id": current_user["id"],
        "amount": amount,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    updated_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    return {"credits": updated_user.get("credits", 0), "added": amount}
