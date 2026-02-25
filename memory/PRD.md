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
- **Gallery**: Unified view of all generated content with expand/fullscreen

### Content Moderation
- AI moderation before publishing
- Admin review workflow
- Email notifications to admin (books@azories.com) and author

### Integrations
- **fal.ai**: PuLID, LoRA, Kling video generation
- **OpenAI**: GPT for content, Whisper for speech-to-text
- **Resend**: Transactional emails (primary)
- **Brevo**: SMTP email (configured but needs correct login)
- **Stripe**: Payments and credits

## Technical Architecture

### Frontend (React)
- `/app/frontend/src/pages/`
  - BookEditor.js - Book creation/editing
  - ProStudio.js - AI generation tools
  - AdminDashboard.js - Content moderation
  - Dashboard.js - User dashboard

### Backend (FastAPI)
- `/app/backend/server.py` - Main API routes
- `/app/backend/services/`
  - email_service.py - Email handling (Resend + Brevo)
  - brevo_email_service.py - Brevo SMTP integration

### Database (MongoDB)
- Collections: users, books, chapters, pages, pro_studio_characters, pro_studio_scenes, character_gallery, art_studio_gallery

## Recent Updates (Feb 2026)

### Session Completed:
- FAL_KEY restored for PuLID/image generation
- Author confirmation email added to publish flow
- Videos tab added to Pro Studio Gallery
- Expand/fullscreen viewer for gallery items
- Cover Editor now has all gallery tabs
- Admin preview navigation with page thumbnails
- Video thumbnail fallback UI

### Known Issues:
- Brevo SMTP needs correct login credentials (SMTP Login email from dashboard)
- Some videos stored as base64 don't show thumbnails properly

### Pending Tasks:
1. Verify book publish email flow
2. Test Videos tab count in Pro Studio
3. Test expand functionality
4. Backend refactoring (split server.py)
5. Frontend refactoring (break down large components)
6. Crop option for Scenes
7. Mobile UI improvements

## Environment Variables

### Backend (.env)
```
MONGO_URL, DB_NAME, JWT_SECRET
FAL_KEY=story-creator-86:1acb251c84bd25d64197c8996d28b1da
RESEND_API_KEY, SENDER_EMAIL
BREVO_API_KEY, BREVO_SENDER_EMAIL, BREVO_ACCOUNT_EMAIL
EMERGENT_LLM_KEY, OPENAI_API_KEY
APP_URL, ADMIN_NOTIFY_EMAIL
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL
```

## Test Credentials
- Admin: Username: Admin / Password: Routetofreedom
- VIP User: jamesstephenbrooks@outlook.com / test123
