# Azories - Digital Book Platform PRD

## Original Problem Statement
User wants to enhance their "Azories" digital book application with:
- Finalized "Pro Studio" for AI content generation
- Credits-based business model with Stripe
- Professional site elements
- Library of sample books
- Bug fixes and codebase refactoring

## Core Requirements

### P0 - Critical
- **Book Reader Experience**: Must be fully optimized for mobile and desktop
- **Art/Pro Studio Mobile**: Core creation tools usable on mobile
- **Character Thumbnail Generation**: Auto-generate when character created
- **Consistent Layout**: Image LEFT, text RIGHT for every page
- **Data Consistency**: Immediate updates, permanent image storage

### P1 - High Priority
- Monetization and tier gating (Stripe)
- Generate long-form stories for 18 books with short text
- Update text for 8 books (awaiting .docx files)
- Ingest Batch 3C books (5 new books)
- Production deployment for 24/7 uptime

### P2 - Medium Priority
- Refactor server.py into modular route files
- Refactor large frontend components (ProStudio.js, BookEditor.js)
- Save planning documents to /app/memory/

## What's Been Implemented

### Feb 27, 2026 - Page-Turning Bug Fix
- **Fixed**: Bottom navigation buttons now properly flip pages using goToPage()
- **Fixed**: Image aspect ratio changed to object-fit:contain to prevent bleeding
- **Fixed**: BookReader pages extraction handles both direct pages and chapters
- **Status**: Verified by testing agent - Page 1, 2, 3 show different content

### Previous Session
- Cloudinary Migration: All images migrated from fal.ai and local storage
- Performance: On-the-fly Cloudinary transformations for ~97% bandwidth reduction
- fal.ai key persistence in database with UI warning banner
- OpenAI fallback for character thumbnail generation
- Duplicate title overlays removed from book covers
- Desktop reader correctly fills 80% viewport height
- Book hiding feature via API

## Tech Stack
- Frontend: React with react-pageflip library
- Backend: FastAPI (Python)
- Database: MongoDB (production)
- Image Storage: Cloudinary
- AI: OpenAI (TTS, thumbnails), fal.ai (image gen)
- Payments: Stripe

## Key Files
- /app/frontend/src/pages/BookReader.js - Book reader with page flip
- /app/frontend/src/components/RealisticPageFlip.jsx - Flipbook component
- /app/backend/server.py - Main backend API
- /app/backend/config.py - Environment configuration

## Known Issues
1. ~~Page-turning buttons not working~~ FIXED
2. Slow narration startup (TTS latency) - PENDING
3. Some book images have text baked in - DATA ISSUE

## Test Credentials
- Admin: jamesstephenbrooks@outlook.com / test123
