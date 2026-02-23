"""
Pydantic models for the Azories API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# ============ AUTH MODELS ============
class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    subscription: str
    credits: Optional[int] = 0
    role: str = "user"
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[dict] = None

# ============ BOOK MODELS ============
class BookCreate(BaseModel):
    title: str
    description: str = ""
    genre: str = "Fantasy"
    age_rating: str = "All Ages"
    is_published: bool = False
    series_id: Optional[str] = None
    series_order: Optional[int] = None
    cover_image: Optional[str] = None

class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    age_rating: Optional[str] = None
    is_published: Optional[bool] = None
    cover_image: Optional[str] = None
    back_cover_image: Optional[str] = None

class BookResponse(BaseModel):
    id: str
    title: str
    description: str
    author_id: str
    author_name: str
    genre: str
    age_rating: str
    is_published: bool
    cover_image: Optional[str] = None
    created_at: str
    updated_at: str

# ============ CHAPTER MODELS ============
class ChapterCreate(BaseModel):
    title: str = "Chapter"
    order: int = 1

class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    order: Optional[int] = None

class ChapterResponse(BaseModel):
    id: str
    book_id: str
    title: str
    order: int
    created_at: str

# ============ PAGE MODELS ============
class PageCreate(BaseModel):
    text_content: str = ""
    image_url: Optional[str] = None
    order: int = 1
    layout_type: str = "text-left"
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_color: Optional[str] = None
    text_alignment: Optional[str] = None
    background_color: Optional[str] = None

class PageUpdate(BaseModel):
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    order: Optional[int] = None
    layout_type: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_color: Optional[str] = None
    text_alignment: Optional[str] = None
    background_color: Optional[str] = None
    image_prompt: Optional[str] = None
    narrator_voice: Optional[str] = None
    narrator_voice_locked: Optional[bool] = None

class PageResponse(BaseModel):
    id: str
    chapter_id: str
    text_content: str
    image_url: Optional[str]
    order: int
    layout_type: str
    created_at: str

# ============ PRO STUDIO MODELS ============
class CharacterCreate(BaseModel):
    name: str
    description_prompt: str
    style: str = "illustration"
    genre: str = "fantasy"
    reference_images: Optional[List[str]] = None
    add_reference_images: Optional[List[str]] = None

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    description_prompt: Optional[str] = None
    style: Optional[str] = None
    genre: Optional[str] = None
    add_reference_images: Optional[List[str]] = None

class SceneCreate(BaseModel):
    name: str
    description: str
    style: str = "illustration"
    genre: str = "fantasy"
    location_type: Optional[str] = None
    lighting: Optional[str] = None
    mood: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None

class SceneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    style: Optional[str] = None
    genre: Optional[str] = None
    location_type: Optional[str] = None
    lighting: Optional[str] = None
    mood: Optional[str] = None

# ============ PAYMENT MODELS ============
class CreateCheckoutRequest(BaseModel):
    package_id: str
    origin_url: str

# ============ AI GENERATION MODELS ============
class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str = "flux-dev"
    image_size: str = "landscape_16_9"
    num_images: int = 1
    seed: Optional[int] = None

class VideoGenerationRequest(BaseModel):
    image_url: str
    motion_prompt: str = "subtle cinematic movement"
    model: str = "sora-2"
    duration: float = 5.0

class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"

class AIStoryRequest(BaseModel):
    idea: str
    genre: str = "Fantasy"
    age_rating: str = "All Ages"
    num_pages: int = 10
    generate_images: bool = False
    media_type: str = "none"
    image_style: str = "illustration"

# ============ REVIEW MODELS ============
class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

# ============ SERIES MODELS ============
class SeriesCreate(BaseModel):
    name: str
    description: str = ""

class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
