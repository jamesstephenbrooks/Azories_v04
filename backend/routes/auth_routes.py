"""
Authentication Routes for Azories API
Extracted from server.py for better code organization.

Handles:
- User registration and login
- Token management
- Password reset flow
- Subscription upgrade
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
import uuid
import os
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# Database reference - set by setup_routes()
db = None

# Email functions - set by setup_routes()
email_configured = None
send_email = None
get_welcome_email_html = None
get_password_reset_email_html = None
get_password_changed_email_html = None

def setup(database, email_funcs: dict):
    """Initialize the auth router with database and email functions."""
    global db, email_configured, send_email
    global get_welcome_email_html, get_password_reset_email_html, get_password_changed_email_html
    
    db = database
    email_configured = email_funcs.get('email_configured', lambda: False)
    send_email = email_funcs.get('send_email')
    get_welcome_email_html = email_funcs.get('get_welcome_email_html')
    get_password_reset_email_html = email_funcs.get('get_password_reset_email_html')
    get_password_changed_email_html = email_funcs.get('get_password_changed_email_html')
    
    logger.info(f"Auth routes setup - email_configured: {email_configured is not None}, send_email: {send_email is not None}")


# ============ CONFIGURATION ============

JWT_SECRET = os.environ.get("JWT_SECRET", "azories-jwt-secret-key-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", 24))  # Default session: 24 hours
JWT_REMEMBER_ME_DAYS = int(os.environ.get("JWT_REMEMBER_ME_DAYS", 30))  # Remember me: 30 days

VIP_USERS = os.environ.get("VIP_USERS", "").split(",")


# ============ MODELS ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: bool = False  # Extended session (30 days) if True

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    subscription: str
    credits: int = 0
    created_at: str
    pro_trial: bool = False
    pro_trial_expires_at: Optional[str] = None
    trial_days_remaining: Optional[int] = None
    is_admin: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ============ HELPERS ============

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str, remember_me: bool = False) -> str:
    """Create a JWT token for a user.
    
    Args:
        user_id: The user's unique ID
        email: The user's email
        role: The user's role
        remember_me: If True, token expires in 30 days; if False, expires in 24 hours
    """
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

def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)

def get_token_expiry() -> datetime:
    """Get expiry time for password reset tokens (1 hour)."""
    return datetime.now(timezone.utc) + timedelta(hours=1)

def is_vip_user(email: str) -> bool:
    """Check if email is a VIP user."""
    return email.lower() in [e.lower().strip() for e in VIP_USERS if e.strip()]


# ============ DEPENDENCIES ============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get the current authenticated user from JWT token."""
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
    """Get the current user if authenticated, None otherwise."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        return user
    except Exception:
        return None


def calculate_trial_status(user: dict) -> tuple:
    """Calculate trial status for a user. Returns (subscription, pro_trial, trial_days_remaining)."""
    subscription = user.get("subscription", "free")
    pro_trial = user.get("pro_trial", False)
    trial_expires = user.get("pro_trial_expires_at")
    trial_days_remaining = None
    
    if pro_trial and trial_expires:
        try:
            expiry_date = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            if now > expiry_date:
                # Trial expired
                subscription = "free"
                pro_trial = False
            else:
                trial_days_remaining = (expiry_date - now).days
        except:
            pass
    
    return subscription, pro_trial, trial_days_remaining


# ============ ROUTES ============

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, background_tasks: BackgroundTasks):
    """Register a new user account."""
    existing = await db.users.find_one({"email": user_data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    
    # 3-day free Pro trial for all new users
    trial_expires = (now + timedelta(days=3)).isoformat()
    
    # VIP users get credits
    is_vip = is_vip_user(user_data.email)
    
    user = {
        "id": user_id,
        "email": user_data.email.lower(),
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": "user",
        "subscription": "pro",  # Start with Pro trial
        "credits": 200 if is_vip else 0,
        "is_vip": is_vip,
        "pro_trial": True,
        "pro_trial_expires_at": trial_expires,
        "created_at": now_iso
    }
    await db.users.insert_one(user)
    
    # Send welcome email
    if email_configured and email_configured():
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
            credits=user["credits"],
            created_at=now_iso,
            pro_trial=True,
            pro_trial_expires_at=trial_expires,
            trial_days_remaining=3
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login with email and password."""
    user = await db.users.find_one({"email": user_data.email.lower()}, {"_id": 0})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check trial status and update if expired
    subscription, pro_trial, trial_days_remaining = calculate_trial_status(user)
    
    if subscription != user.get("subscription") or pro_trial != user.get("pro_trial"):
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"subscription": subscription, "pro_trial": pro_trial}}
        )
    
    # Pass remember_me to create_token for extended session duration
    token = create_token(user["id"], user["email"], user["role"], user_data.remember_me)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            subscription=subscription,
            credits=user.get("credits", 0),
            created_at=user["created_at"],
            pro_trial=pro_trial,
            pro_trial_expires_at=user.get("pro_trial_expires_at"),
            trial_days_remaining=trial_days_remaining,
            is_admin=user.get("is_admin", False) or user.get("role") == "admin"
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user's profile."""
    subscription, pro_trial, trial_days_remaining = calculate_trial_status(current_user)
    
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        subscription=subscription,
        credits=current_user.get("credits", 0),
        created_at=current_user["created_at"],
        pro_trial=pro_trial,
        pro_trial_expires_at=current_user.get("pro_trial_expires_at"),
        trial_days_remaining=trial_days_remaining,
        is_admin=current_user.get("is_admin", False) or current_user.get("role") == "admin"
    )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Request a password reset email."""
    print(f"[FORGOT-PASSWORD] Request received for: {request.email}")
    
    user = await db.users.find_one({"email": request.email.lower()}, {"_id": 0})
    
    # Always return success to prevent email enumeration attacks
    if not user:
        print(f"[FORGOT-PASSWORD] User not found: {request.email}")
        return {"message": "If this email exists, a reset link has been sent."}
    
    print(f"[FORGOT-PASSWORD] User found: {user.get('name')}")
    
    # Generate reset token
    reset_token = generate_reset_token()
    expiry = get_token_expiry()
    
    # Hash token before storing
    token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    
    # Store reset token
    await db.password_resets.delete_many({"user_id": user["id"]})
    await db.password_resets.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token_hash": token_hash,
        "expires_at": expiry.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    print(f"[FORGOT-PASSWORD] Reset token stored for user {user['id']}")
    
    # Get app URL for reset link
    app_url = os.environ.get("APP_URL", "https://azories.com")
    reset_url = f"{app_url}/reset-password?token={reset_token}"
    
    # Debug email configuration
    print(f"[FORGOT-PASSWORD] Email check - email_configured: {email_configured is not None}, send_email: {send_email is not None}")
    if email_configured:
        config_result = email_configured() if callable(email_configured) else bool(email_configured)
        print(f"[FORGOT-PASSWORD] Email configured result: {config_result}")
    
    # Send reset email (with unhashed token)
    if email_configured and email_configured() and send_email:
        print(f"[FORGOT-PASSWORD] Generating email HTML...")
        reset_html = get_password_reset_email_html(user["name"], reset_token, reset_url)
        # Send email directly (not in background) to ensure delivery
        try:
            print(f"[FORGOT-PASSWORD] Calling send_email for {request.email}...")
            result = await send_email(request.email, "Reset Your Azories Password", reset_html)
            print(f"[FORGOT-PASSWORD] send_email result: {result}")
            if result and result.get("success"):
                print(f"[FORGOT-PASSWORD] ✅ Email SENT to {request.email}, email_id: {result.get('email_id')}")
            else:
                print(f"[FORGOT-PASSWORD] ❌ Email FAILED for {request.email}: {result}")
        except Exception as e:
            print(f"[FORGOT-PASSWORD] ❌ Email ERROR for {request.email}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    else:
        print(f"[FORGOT-PASSWORD] ⚠️ Email not configured - token for {request.email}: {reset_token[:10]}...")
    
    return {"message": "If this email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, background_tasks: BackgroundTasks):
    """Reset password using a valid token."""
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    
    # Find the reset token
    reset_record = await db.password_resets.find_one({"token_hash": token_hash}, {"_id": 0})
    if not reset_record:
        # Fallback to plaintext tokens for migration
        reset_record = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token has expired
    expiry = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(timezone.utc) > expiry:
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
    await db.users.update_one({"id": user["id"]}, {"$set": {"password": new_hash}})
    
    # Delete used token
    await db.password_resets.delete_one({"$or": [{"token_hash": token_hash}, {"token": request.token}]})
    
    # Send confirmation email
    if email_configured and email_configured():
        changed_html = get_password_changed_email_html(user["name"])
        background_tasks.add_task(send_email, user["email"], "Your Azories Password Has Been Changed", changed_html)
    
    logger.info(f"Password reset completed for user {user['id']}")
    return {"message": "Password has been reset successfully. You can now log in."}


@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verify if a password reset token is valid."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    reset_record = await db.password_resets.find_one({"token_hash": token_hash}, {"_id": 0})
    if not reset_record:
        reset_record = await db.password_resets.find_one({"token": token}, {"_id": 0})
    
    if not reset_record:
        return {"valid": False, "message": "Invalid token"}
    
    expiry = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(timezone.utc) > expiry:
        return {"valid": False, "message": "Token has expired"}
    
    return {"valid": True, "message": "Token is valid"}
