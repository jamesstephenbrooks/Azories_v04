"""
Admin routes for Azories API
Handles admin authentication, CMS, analytics, and moderation
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import jwt
import os
import logging

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBearer()

# Database reference - set by main app
db = None

def set_db(database):
    global db
    db = database

# JWT settings
JWT_SECRET = os.environ.get("JWT_SECRET", "azories-secret-key-2024")
JWT_ALGORITHM = "HS256"

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Routetofreedom")

# VIP users list
VIP_USERS = ["arianamillb@icloud.com", "jamesstephenbrooks@outlook.com"]

# Age ratings
AGE_RATINGS = ["All Ages", "7+", "10+", "13+", "16+"]


# ============ MODELS ============

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    access_token: str
    admin_name: str

class BookModerationUpdate(BaseModel):
    status: str  # 'approved', 'rejected', 'pending'
    rejection_reason: Optional[str] = None


# ============ AUTH HELPERS ============

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if not payload.get("admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid admin token")

async def get_admin_or_vip(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Allow admin token OR VIP user token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Admin token
        if payload.get("admin"):
            return {"is_admin": True, "username": payload.get("username")}
        
        # Regular user token - check if VIP
        user_id = payload.get("sub")
        if user_id and db:
            user = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "role": 1})
            if user:
                is_admin = user.get("role") == "admin"
                is_vip = user.get("email", "").lower() in [v.lower() for v in VIP_USERS]
                if is_admin or is_vip:
                    return {"is_admin": is_admin, "is_vip": is_vip, "email": user.get("email")}
        
        raise HTTPException(status_code=403, detail="Admin or VIP access required")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============ AUTH ROUTES ============

@router.post("/login", response_model=AdminResponse)
async def admin_login(login_data: AdminLogin):
    """Admin login endpoint"""
    if login_data.username != ADMIN_USERNAME or login_data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    expiration = datetime.now(timezone.utc) + timedelta(hours=8)
    token_data = {
        "admin": True,
        "username": login_data.username,
        "exp": expiration
    }
    token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return AdminResponse(access_token=token, admin_name=login_data.username)

@router.get("/verify")
async def verify_admin(admin: dict = Depends(get_admin_user)):
    """Verify admin token is valid"""
    return {"valid": True, "username": admin.get("username")}


# ============ CMS ROUTES ============

@router.get("/books")
async def admin_get_all_books(admin: dict = Depends(get_admin_user)):
    """Get all books for admin CMS"""
    books = await db.books.find({}, {"_id": 0}).to_list(200)
    result = []
    for book in books:
        # Get counts
        chapters = await db.chapters.find({"book_id": book["id"]}).to_list(100)
        book["chapter_count"] = len(chapters)
        
        total_pages = 0
        for chapter in chapters:
            pages = await db.pages.count_documents({"chapter_id": chapter["id"]})
            total_pages += pages
        book["page_count"] = total_pages
        
        # Get author name
        author = await db.users.find_one({"id": book.get("author_id")}, {"_id": 0, "name": 1})
        book["author_name"] = author.get("name", "Unknown") if author else "Unknown"
        
        result.append(book)
    return result

@router.get("/books/{book_id}/full")
async def admin_get_full_book(book_id: str, admin: dict = Depends(get_admin_user)):
    """Get full book content for admin preview"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get all chapters
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).sort("order", 1).to_list(100)
    
    # Get pages for each chapter
    for chapter in chapters:
        pages = await db.pages.find({"chapter_id": chapter["id"]}, {"_id": 0}).sort("order", 1).to_list(100)
        chapter["pages"] = pages
    
    book["chapters"] = chapters
    
    # Get author info
    author = await db.users.find_one({"id": book.get("author_id")}, {"_id": 0, "name": 1, "email": 1})
    book["author_name"] = author.get("name", "Unknown") if author else "Unknown"
    book["author_email"] = author.get("email", "") if author else ""
    
    return book

@router.get("/users")
async def admin_get_all_users(admin: dict = Depends(get_admin_user)):
    """Get all users for admin"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@router.post("/books/{book_id}/feature")
async def toggle_featured(book_id: str, admin: dict = Depends(get_admin_user)):
    """Toggle book featured status"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_featured", False)
    await db.books.update_one({"id": book_id}, {"$set": {"is_featured": new_status}})
    return {"is_featured": new_status}

@router.post("/books/{book_id}/best-of-week")
async def toggle_best_of_week(book_id: str, admin: dict = Depends(get_admin_user)):
    """Toggle book best-of-week status"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_status = not book.get("is_best_of_week", False)
    await db.books.update_one({"id": book_id}, {"$set": {"is_best_of_week": new_status}})
    return {"is_best_of_week": new_status}

@router.post("/books/{book_id}/age-rating")
async def set_age_rating(book_id: str, age_rating: str, admin: dict = Depends(get_admin_user)):
    """Set book age rating"""
    if age_rating not in AGE_RATINGS:
        raise HTTPException(status_code=400, detail=f"Invalid age rating. Must be one of: {AGE_RATINGS}")
    
    await db.books.update_one({"id": book_id}, {"$set": {"age_rating": age_rating}})
    return {"age_rating": age_rating}

@router.post("/books/{book_id}/publish")
async def admin_publish_book(book_id: str, admin: dict = Depends(get_admin_user)):
    """Admin publish/unpublish book directly"""
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

@router.delete("/books/{book_id}")
async def admin_delete_book(book_id: str, admin: dict = Depends(get_admin_user)):
    """Admin delete any book"""
    chapters = await db.chapters.find({"book_id": book_id}, {"_id": 0}).to_list(100)
    for chapter in chapters:
        await db.pages.delete_many({"chapter_id": chapter["id"]})
    await db.chapters.delete_many({"book_id": book_id})
    await db.books.delete_one({"id": book_id})
    return {"message": "Book deleted by admin"}


# ============ MODERATION ROUTES ============

@router.get("/moderation/pending")
async def get_pending_books(admin: dict = Depends(get_admin_user)):
    """Get books pending moderation review"""
    pending_books = await db.books.find(
        {"publish_status": "pending_review"},
        {"_id": 0}
    ).to_list(100)
    
    for book in pending_books:
        author = await db.users.find_one({"id": book.get("author_id")}, {"_id": 0, "name": 1, "email": 1})
        book["author_name"] = author.get("name", "Unknown") if author else "Unknown"
        book["author_email"] = author.get("email", "") if author else ""
    
    return pending_books

@router.post("/moderation/books/{book_id}")
async def moderate_book(book_id: str, update: BookModerationUpdate, admin: dict = Depends(get_admin_user)):
    """Approve or reject a book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    update_data = {
        "publish_status": update.status,
        "moderation_date": datetime.now(timezone.utc).isoformat(),
        "moderated_by": admin.get("username", "admin")
    }
    
    if update.status == "approved":
        update_data["is_published"] = True
    elif update.status == "rejected":
        update_data["is_published"] = False
        update_data["rejection_reason"] = update.rejection_reason
    
    await db.books.update_one({"id": book_id}, {"$set": update_data})
    return {"status": update.status, "book_id": book_id}


# ============ ANALYTICS ROUTES ============

@router.get("/analytics")
async def get_admin_analytics(admin_info: dict = Depends(get_admin_or_vip)):
    """Get admin analytics dashboard data"""
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
    
    # Credit usage by operation
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
    
    for user_stat in active_users:
        user = await db.users.find_one({"id": user_stat["_id"]}, {"_id": 0, "email": 1, "name": 1})
        if user:
            user_stat["email"] = user.get("email", "")
            user_stat["name"] = user.get("name", "")
    
    # Engagement stats
    total_reads = await db.reading_progress.count_documents({})
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

@router.get("/vip-usage")
async def get_vip_usage(admin_info: dict = Depends(get_admin_or_vip)):
    """Get VIP user usage statistics"""
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
