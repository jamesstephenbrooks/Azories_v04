"""
Books routes for Azories API
Handles book CRUD, collaborators, and book images
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/books", tags=["Books"])

# Get database from main app
db = None

def set_db(database):
    global db
    db = database

# Models
class BookCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    genre: Optional[str] = "fantasy"
    age_group: Optional[str] = "7-12"
    target_age: Optional[str] = "All Ages"
    cover_image: Optional[str] = None
    back_cover_image: Optional[str] = None
    cover_title: Optional[str] = None
    cover_subtitle: Optional[str] = None
    back_cover_text: Optional[str] = None
    narrator_voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"
    narrator_voice_locked: Optional[bool] = False
    layout_mode: Optional[str] = "standard"

class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    age_group: Optional[str] = None
    target_age: Optional[str] = None
    cover_image: Optional[str] = None
    back_cover_image: Optional[str] = None
    cover_title: Optional[str] = None
    cover_subtitle: Optional[str] = None
    back_cover_text: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    narrator_voice_id: Optional[str] = None
    narrator_voice_locked: Optional[bool] = None
    layout_mode: Optional[str] = None

class BookResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    author_id: str
    author_name: Optional[str] = ""
    genre: Optional[str] = "fantasy"
    age_group: Optional[str] = "7-12"
    target_age: Optional[str] = "All Ages"
    cover_image: Optional[str] = None
    back_cover_image: Optional[str] = None
    cover_title: Optional[str] = None
    cover_subtitle: Optional[str] = None
    back_cover_text: Optional[str] = None
    is_published: bool = False
    is_featured: bool = False
    created_at: str
    updated_at: Optional[str] = None
    views: int = 0
    reads: int = 0
    likes: int = 0
    chapter_count: int = 0
    page_count: int = 0
    narrator_voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"
    narrator_voice_locked: Optional[bool] = False
    layout_mode: Optional[str] = "standard"
    collaborators: Optional[list] = []

class CollaboratorInvite(BaseModel):
    email: str
    role: str = "editor"

class CollaboratorRoleUpdate(BaseModel):
    role: str

def set_book_defaults(book: dict) -> dict:
    """Ensure all book fields have defaults"""
    defaults = {
        "description": "",
        "genre": "fantasy",
        "age_group": "7-12",
        "target_age": "All Ages",
        "cover_image": None,
        "back_cover_image": None,
        "cover_title": None,
        "cover_subtitle": None,
        "back_cover_text": None,
        "is_published": False,
        "is_featured": False,
        "views": 0,
        "reads": 0,
        "likes": 0,
        "narrator_voice_id": "21m00Tcm4TlvDq8ikWAM",
        "narrator_voice_locked": False,
        "layout_mode": "standard",
        "collaborators": []
    }
    for key, value in defaults.items():
        if key not in book:
            book[key] = value
    return book

async def get_book_with_counts(book: dict) -> dict:
    """Get book with chapter and page counts"""
    book = set_book_defaults(book)
    chapters = await db.chapters.find({"book_id": book["id"]}).to_list(100)
    book["chapter_count"] = len(chapters)
    
    total_pages = 0
    for chapter in chapters:
        pages = await db.pages.count_documents({"chapter_id": chapter["id"]})
        total_pages += pages
    book["page_count"] = total_pages
    
    # Get author name
    author = await db.users.find_one({"id": book["author_id"]}, {"_id": 0, "name": 1})
    book["author_name"] = author.get("name", "Unknown") if author else "Unknown"
    
    return book

# This file contains the route structure for books.
# Full implementation would move all book-related routes from server.py here.
# For now, this serves as a template showing the target structure.

# Example routes (to be migrated from server.py):
# @router.post("/", response_model=BookResponse)
# async def create_book(...)
# 
# @router.get("/", response_model=List[BookResponse])
# async def get_books(...)
#
# @router.get("/featured", response_model=List[BookResponse])
# async def get_featured_books(...)
#
# @router.get("/my", response_model=List[BookResponse])
# async def get_my_books(...)
#
# @router.get("/{book_id}", response_model=BookResponse)
# async def get_book(...)
#
# @router.put("/{book_id}", response_model=BookResponse)
# async def update_book(...)
#
# @router.delete("/{book_id}")
# async def delete_book(...)
#
# @router.post("/{book_id}/collaborators/invite")
# async def invite_collaborator(...)
#
# @router.get("/{book_id}/collaborators")
# async def get_collaborators(...)
#
# @router.put("/{book_id}/collaborators/{user_id}")
# async def update_collaborator_role(...)
#
# @router.delete("/{book_id}/collaborators/{user_id}")
# async def remove_collaborator(...)
#
# @router.post("/{book_id}/images")
# async def save_image_to_book(...)
#
# @router.get("/{book_id}/images")
# async def get_book_images(...)
#
# @router.delete("/{book_id}/images/{image_id}")
# async def delete_book_image(...)
#
# @router.get("/{book_id}/download")
# async def download_book_pdf(...)
