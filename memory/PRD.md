# Azories - Digital Book Platform PRD

## Original Problem Statement
User wants to enhance their "Azories" digital book application with:
- Finalized "Pro Studio" for AI content generation
- Credits-based business model with Stripe
- Professional site elements
- Library of sample books
- Bug fixes and codebase refactoring

## Core Requirements

### P0 - Critical (All Complete ✅)
- **Book Reader Experience**: Fully optimized for mobile and desktop ✅
- **AI Story Creator Page Count**: Creates exact number of pages requested ✅
- **AI Story Creator Images**: Each page gets fal.ai generated image ✅
- **Free Stories Trial**: New users get 3 free story creations ✅
- **BookEditor Mobile Layout**: Responsive design matching ProStudio ✅
- **Audio Caching**: Narration cached to Cloudinary for instant playback ✅ (Mar 1)

### P1 - High Priority
- Monetization and tier gating (Stripe) ✅
- Generate long-form stories for 17 books with short text
- Update text for 8 books (awaiting .docx files)
- Ingest Batch 3C books (5 new books)
- Production deployment for 24/7 uptime ✅ READY
- Regenerate covers for 25 books (to match interior Pixar style)

### P2 - Medium Priority
- Refactor server.py into modular route files
- Refactor large frontend components

## Audio Caching Implementation (Mar 1, 2026)

### How It Works
1. **First-time narration**: TTS generates audio → uploads to Cloudinary → saves URL to page document
2. **Subsequent plays**: Serves cached Cloudinary URL directly (no TTS call)
3. **Pre-generation**: Admin can batch-generate narration for all library books

### API Endpoints
- `POST /api/tts/generate` - Returns `audio_url` (Cloudinary) or `audio_base64` fallback
- `POST /api/tts/generate-for-page/{page_id}` - Generate and cache for specific page
- `POST /api/admin/generate-narration-batch` - Batch generate for books
- `GET /api/admin/narration-status` - Check cache status

### Frontend Changes
- `BookReader.js` - Checks `page.audio_url` first, falls back to TTS generation
- `audioCache` now stores `{ type: 'url'|'base64', url/data }` objects

### Benefits
- **Instant playback** for cached pages (CDN delivery)
- **Reduced API costs** (no repeated TTS calls)
- **Better UX** - Pre-generated library books start immediately

## Current State (March 1, 2026)

### Completed ✅
- **Audio Caching System** - Cloudinary-based narration caching (Mar 1)
- **AI Story Creator Page Count Fix** - Creates exact number of pages (Mar 1)
- **BookEditor Mobile Layout** - Responsive with Visual/Text tabs (Mar 1)
- **Free Stories Trial** - 3 free AI stories for new users (Mar 1)
- **Credits System** - Full Stripe integration
- **249 page images regenerated** - Pixar style, portrait, no text

### In Progress 🔄
- **Batch narration generation** - 41 books queued, generating in background

### Pending Tasks 🔴
- Regenerate covers for 25 books
- 17 books need story text expansion
- 8 books need text from .docx files
- 5 new books to ingest (Batch 3C)

## Tech Stack
- Frontend: React with react-pageflip library
- Backend: FastAPI (Python)
- Database: MongoDB (azories)
- Image Storage: Cloudinary
- Audio Storage: Cloudinary (new!)
- AI: fal.ai (images), OpenAI TTS (narration)
- Payments: Stripe

## Key Files
- `/app/backend/server.py`: TTS caching endpoints (lines 5652-5820, 8910-9080)
- `/app/frontend/src/pages/BookReader.js`: Audio playback with URL support

## Test Credentials
- Admin: jamesstephenbrooks@outlook.com / Routetofreedom
- Admin Panel: Username: Admin / Password: Routetofreedom

## Next Session Tasks
1. Monitor narration batch generation progress
2. Regenerate covers for 25 books
3. Generate text for 17 books
4. Deploy to production
