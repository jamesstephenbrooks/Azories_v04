"""
Authentication utilities
"""
import jwt
import bcrypt
import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import db, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION, VIP_USERS, CREDIT_COSTS, ACTUAL_COSTS

logger = logging.getLogger(__name__)
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user_id: str) -> str:
    """Create a JWT token for a user"""
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get the current authenticated user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def deduct_credits(user_id: str, operation: str) -> bool:
    """
    Deduct credits for an operation. 
    VIP users get unlimited credits but usage is tracked.
    Returns True if successful.
    """
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


def is_vip_user(email: str) -> bool:
    """Check if email belongs to a VIP user"""
    return email.lower() in [v.lower() for v in VIP_USERS]
