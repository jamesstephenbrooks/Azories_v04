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
- Generate long-form stories for 17 books with short text
- Update text for 8 books (awaiting .docx files)
- Ingest Batch 3C books (5 new books)
- Production deployment for 24/7 uptime
- **Regenerate page images** for 23 books (text baked into old images)

### P2 - Medium Priority
- Refactor server.py into modular route files
- Refactor large frontend components (ProStudio.js, BookEditor.js)
- Save planning documents to /app/memory/
- Regenerate covers to match interior Pixar style

## Current State (Feb 27, 2026 EOD)

### Working ✅
- Page turning buttons
- Text displaying on right page (reads from pages array)
- 80% viewport height on desktop
- Image fills left page (object-fit: cover)
- Images loading (rolled back to original Cloudinary URLs)

### Not Working / Pending 🔴
- 23 books have OLD images with AI text baked in
- 17 books need story text expansion (5-10 words → 100+ words per page)
- Cover style mismatch (old watercolor vs new Pixar style)

### Books Status
- **44 visible** in library
- **16 hidden** (wrong covers or other issues)

## IMPORTANT: Image Regeneration Notes
The batch regeneration on Feb 27 FAILED because:
1. Script connected to local MongoDB instead of production
2. Database URLs were updated to non-existent files
3. Had to rollback to original URLs

**For next attempt:**
- Use API endpoints only (not direct MongoDB)
- Verify each Cloudinary upload before updating DB
- Test one book completely before running batch

## Tech Stack
- Frontend: React with react-pageflip library
- Backend: FastAPI (Python)
- Database: MongoDB (production - NOT localhost)
- Image Storage: Cloudinary
- AI: OpenAI (TTS, thumbnails), fal.ai (image gen)
- Payments: Stripe

## Key Files
- /app/frontend/src/pages/BookReader.js
- /app/frontend/src/components/RealisticPageFlip.jsx
- /app/backend/server.py
- /app/memory/SESSION_STATE_20260227.md - Detailed session state

## Test Credentials
- Admin: jamesstephenbrooks@outlook.com / test123
