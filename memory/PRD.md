# Azories - Digital Book Platform

## Product Overview
Azories is a full-stack digital book creation platform with AI-powered features for generating characters, scenes, images, and videos. Users can create, edit, and publish children's books with rich media content.

## Core Requirements

### Authentication & Users
- JWT-based authentication
- User roles: regular, VIP (exempt from credit deductions), admin
- Credits-based system for Pro Studio features
- VIP email exemptions tracked in database

### Book Editor
- Multi-chapter book creation
- Page-by-page editing with text and media
- Gallery picker with tabs: Starter Library, This Book, Art Studio, Pro Characters, Pro Scenes, Videos
- Cover editor with same gallery options
- Voice narration (speech-to-text)
- PDF export

### Pro Studio
- **Characters**: Create AI characters with reference images, LoRA training
- **Scenes**: Create environments/backgrounds
- **Shots**: Generate consistent character images with art style options
- **Cinema Studio**: Professional image generation with camera/lens options
- **Video Generation**: Animate images using Sora 2 or Kling
- **Gallery**: Unified view of all generated content with expand/fullscreen, pagination, lazy loading

### Content Moderation
- AI moderation before publishing
- Admin review workflow
- Email notifications to admin (books@azories.com) and author

### Integrations
- **fal.ai**: PuLID, LoRA, Kling video generation
- **OpenAI**: GPT for content, Whisper for speech-to-text
- **Brevo**: SMTP email (working)
- **Stripe**: Payments and credits (live mode configured)

## Technical Architecture

### Frontend (React)
- `/app/frontend/src/pages/`
  - BookEditor.js - Book creation/editing
  - ProStudio.js - AI generation tools (5700+ lines)
  - AdminDashboard.js - Content moderation
  - Dashboard.js - User dashboard

### Backend (FastAPI)
- `/app/backend/server.py` - Main API routes (8000+ lines)
- Key endpoints:
  - `/api/pro-studio/gallery/unified` - Optimized paginated gallery endpoint

### Database (MongoDB)
- Collections: users, books, chapters, pages, pro_studio_characters, pro_studio_scenes, character_gallery, art_studio_gallery

## Recent Updates (Feb 25, 2026)

### Session Completed:
- **Mobile Gallery Optimization (P0)**: 
  - Created new `/api/pro-studio/gallery/unified` endpoint for single API call with pagination
  - Implemented lazy loading for gallery images with skeleton placeholders
  - Added `decoding="async"` and `loading="lazy"` to images
  - Optimized video elements to not preload on mobile (`preload="none"`)
  - Added "Load More" pagination (30 items per page)
  - Filter buttons now show current count only when active
- **Video Playback Improvements**:
  - Added `playsInline` attribute for mobile compatibility
  - Added error handling for base64 videos with incorrect MIME types
  - Videos show thumbnail placeholder on mobile until tapped
- **Credit Check Redirects**: Implemented and ready for testing

### Previous Session Work:
- FAL_KEY restored for PuLID/image generation
- Email system migrated to Brevo (working)
- Videos tab added to Pro Studio Gallery
- Expand/fullscreen viewer for gallery items
- Admin preview navigation with page thumbnails
- Stripe configured with live keys

### Known Issues:
- Book Editor "Pro Characters" and "Pro Scenes" tabs may be empty (need user data to test)
- fal.ai Pulid generation errors reported (need error details)
- LoRA character training gets stuck (need monitoring)

### Pending Tasks:
1. **P1**: Test credit check redirect functionality
2. **P1**: Debug Book Editor Pro Characters/Scenes tabs with real data
3. **P2**: Implement Crop Option in Scenes
4. **P2**: Backend refactoring (split server.py into routers)
5. **P2**: Frontend refactoring (break down ProStudio.js, BookEditor.js)
6. **P2**: Analyze readkids.com competitor

## Environment Variables

### Backend (.env)
```
MONGO_URL, DB_NAME, JWT_SECRET
FAL_KEY=story-creator-86:1acb251c84bd25d64197c8996d28b1da
BREVO_SMTP_KEY, BREVO_SENDER_EMAIL
EMERGENT_LLM_KEY, OPENAI_API_KEY
APP_URL, ADMIN_NOTIFY_EMAIL
STRIPE_API_KEY (live), STRIPE_WEBHOOK_SECRET
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL
REACT_APP_STRIPE_PUBLISHABLE_KEY (live)
```

## Test Credentials
- Admin: Username: Admin / Password: Routetofreedom
- VIP User: jamesstephenbrooks@outlook.com / test123
