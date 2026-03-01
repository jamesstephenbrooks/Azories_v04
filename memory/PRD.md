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
- **Book Reader Experience**: Must be fully optimized for mobile and desktop ✅
- **Art/Pro Studio Mobile**: Core creation tools usable on mobile
- **Character Thumbnail Generation**: Auto-generate when character created
- **Consistent Layout**: Image LEFT, text RIGHT for every page ✅
- **Data Consistency**: Immediate updates, permanent image storage ✅
- **Content Quality**: No text baked into illustrations ✅ (Feb 28)
- **AI Story Creator Free Stories**: New users get 3 free story creations ✅ (Mar 1)

### P1 - High Priority
- Monetization and tier gating (Stripe) ✅
- Generate long-form stories for 17 books with short text
- Update text for 8 books (awaiting .docx files)
- Ingest Batch 3C books (5 new books)
- Production deployment for 24/7 uptime
- **Regenerate covers** for 25 books (to match interior Pixar style)

### P2 - Medium Priority
- Refactor server.py into modular route files
- Refactor large frontend components (ProStudio.js, BookEditor.js)
- Save planning documents to /app/memory/
- Audio caching for faster narration startup

## Current State (March 1, 2026)

### Completed ✅
- **Free Stories Trial System** - 3 free AI story creations for new users (Mar 1, 2026)
- **Credits System** - Full Stripe integration for credit purchases
- **AI Story Creator** - Complete form redesign with fal.ai image generation
- **249 page images regenerated** - Pixar style, portrait, no text (Feb 27-28)
- **25 books now visible** in public library
- **"Opening book..." bug fixed** - Auth issue resolved
- Page turning buttons working
- Text displaying on right page
- 80% viewport height on desktop
- Images fill left page properly
- "Art Studio" renamed to "Creators"
- Back button added to Credits page

### Pending Tasks 🔴
- **Regenerate covers for 25 books** (still old watercolor style)
- **17 books need story text expansion** (short placeholder → full stories)
- **8 books need text from .docx files**
- **5 new books to ingest** (Batch 3C)
- End-to-end test of AI Story Creator with image generation
- Verify mobile back cover display fix

### Books Status
- **44 visible** in library (including all 25 regenerated books)
- **20 hidden** (various issues)

## Free Stories Trial System (Mar 1, 2026)

### Implementation Details
- New users get `free_stories_remaining: 3` and `free_stories_used: 0` on registration
- Existing users without these fields get 3 free stories automatically
- API `/api/auth/ai-story-trial` returns:
  - `has_free_stories`: boolean
  - `free_stories_remaining`: int
  - `free_stories_used`: int
  - `display_text`: string (e.g., "3 free stories remaining")
  - `in_trial`: boolean (legacy compatibility)
- When story is created:
  - If free stories available: decrement `free_stories_remaining`, increment `free_stories_used`
  - If no free stories: deduct 5 credits (402 error if insufficient)

### Test Coverage
- 9/9 backend tests passed
- Frontend correctly shows free stories banner or credit cost
- Test file: `/app/backend/tests/test_free_stories_trial.py`

## Tech Stack
- Frontend: React with react-pageflip library
- Backend: FastAPI (Python)
- Database: MongoDB (test_database)
- Image Storage: Cloudinary
- AI: OpenAI (TTS, thumbnails), fal.ai (image gen)
- Payments: Stripe

## Key Files
- /app/frontend/src/pages/Dashboard.js - AI Story Creator dialog
- /app/frontend/src/pages/BookReader.js
- /app/frontend/src/components/RealisticPageFlip.jsx
- /app/backend/server.py - Main API with free stories logic
- /app/backend/tests/test_free_stories_trial.py

## Test Credentials
- Admin: jamesstephenbrooks@outlook.com / Routetofreedom

## Next Session Tasks (Priority Order)
1. End-to-end test of AI Story Creator (create story, verify images generated)
2. Verify mobile back cover display fix
3. Regenerate covers for 25 books (match Pixar interior style)
4. Generate long-form text for 17 books
5. Update text for 8 books from .docx files
6. Ingest 5 new books (Batch 3C)
7. Audio caching implementation
8. Refactor server.py
