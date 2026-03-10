# Azories AI Story Creator - Product Requirements Document

## Original Problem Statement
Build a full-featured AI Story Creator application named "Azories" with:
- AI-powered story and image generation
- Comprehensive book editor
- Print-on-demand (POD) integration via Gelato
- Offline reading capabilities (especially iOS Safari)
- User authentication and credit system

## Tech Stack
- **Frontend:** React (with Shadcn UI components)
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **AI Services:** fal.ai (image generation), OpenAI/Emergent LLM (text), ElevenLabs (TTS)
- **Payments:** Stripe
- **Storage:** Cloudinary (images/PDFs)
- **Email:** Resend

## Core Features Implemented
- [x] User authentication (register, login, password reset)
- [x] Book library and management
- [x] Book editor with chapters and pages
- [x] AI story generation (Azora AI Author)
- [x] AI image generation (FLUX, Ideogram, PuLID)
- [x] Pro Studio for character consistency
- [x] Text-to-speech narration
- [x] Offline book storage (IndexedDB)
- [x] Stripe payment integration
- [x] Print-on-demand via Gelato
- [x] Admin dashboard
- [x] Contact form with email notifications

## Recent Fixes (December 2026)

### Session v1.0.18 (March 2026)
- [x] **iPad Layout Fix** - Expanded tablet book dimensions (portrait: 72% width/80% height, landscape: 46% width/88% height), reduced container padding
- [x] **Fullscreen Button Fix** - Raised header z-index to z-[210] above tap zones z-[200], enlarged fullscreen button touch target, added spacing
- [x] **Narration Auto-Scroll Fix** - Fixed auto-scroll to work in both portrait AND landscape mobile views (was only scrolling portrait ref)
- [x] **Fullscreen Dimensions** - Increased fullscreen book size (landscape: 42%/90%, portrait: 50%/80%)

### Session v1.0.9 (March 2026)
- [x] **CRITICAL: Fixed AI Story Editing** - AI-generated books now load chapters and pages correctly in the editor
  - Root cause: AI books store pages EMBEDDED in the book document, not in the `pages` collection
  - Fix: Modified `/api/books/{book_id}/chapters` to detect embedded pages and migrate them to the `pages` collection
  - Ran data migration script to fix 282 existing pages (book_id and page_number fields)
  - Verified: "The Dragon's Secret Garden" and all other AI books now load with all pages editable
- [x] **Removed Editor Tour on Mobile** - Tour was causing alignment issues; now auto-skipped on mobile devices

### Session v1.0.8 (March 2026)
- [x] **Hide PDF button on mobile** - Added `hidden md:flex` to Download PDF button with fallback message directing users to "Order Physical Copy"
- [x] **Narration play button states** - Added loading spinner (`FiLoader`), pause icon states, and haptic feedback (`navigator.vibrate`) to floating listen buttons
- [x] **Editor onboarding tour centering** - Enhanced EditorTourGuide.jsx to properly center on mobile in both portrait and landscape orientations with orientation change listener
- [x] **Book summary text selection** - Fixed summary text in Library.js dialog to be selectable with `select-text` class and `userSelect: 'text'` styles
- [x] **Info (i) icon button fix** - Improved info button with larger touch target (w-10 h-10), higher z-index (z-30), explicit pointer-events, and accessibility attributes
- [x] **Firefox mobile compatibility** - Added comprehensive CSS fallbacks:
  - dvh viewport unit fallbacks
  - Firefox scrollbar styling (scrollbar-width: thin)
  - backdrop-filter fallbacks for Firefox
  - line-clamp fallbacks using overflow/max-height
  - Touch action improvements for Firefox
  - Modal/overlay touch fixes

### Previous Session v1.0.7
- [x] Fixed `/api/pro-studio/characters/{id}/generate-consistent` 500 error
  - Root cause: `physical_traits` stored as `None` causing `.get()` to fail
  - Fix: `character.get('physical_traits') or {}` handles explicit `None`
  - Also fixed HTTPException being swallowed by generic exception handler
- [x] Fixed `get_admin_user` NoneType credentials error
- [x] Merged duplicate Stripe webhook handlers
- [x] Fixed author_id/user_id mismatch for book display
- [x] Added admin endpoint for updating user credits
- [x] Added Book Editor tooltip tour for new users
- [x] Fixed AI book editing by adding fallback to find orphaned pages by book_id

## Known Issues

### P0 - Critical
- [ ] **Production Environment Instability** - Intermittent 502/520 errors after deployments (infrastructure issue, not code)
- [x] **AI Story Editing** - FIXED in v1.0.9. AI books now load chapters/pages correctly.

### P1 - High Priority
- [ ] **Data Discrepancy** - Preview and production databases are separate; changes in preview don't affect production
- [ ] **Slow thumbnail loading** - Library/dashboard pages load thumbnails slowly
- [ ] **Root cause of blank PDF downloads** - Currently hidden on mobile as temporary fix; needs proper debugging

### P2 - Medium Priority
- [ ] **Mobile UI bugs** - Pro Studio image deletion, video download issues, oversized checkbox on iPad
- [ ] **Offline functionality** - Needs verification on production after stable deployment

## Pending Tasks

### Upcoming
1. Run production DB migration: `db.books.updateMany({}, {$set: {requires_auth: false, is_published: true}})`
2. Create "My Orders" page for print order tracking
3. Revert image generation model back to `flux-dev`

### Future/Backlog
- Download All Books button
- Order tracking notifications
- Gift feature for print orders
- Add Ideogram as separate art style option
- Decompose large components (server.py 14.6k lines, ProStudio.js 6.8k lines)

## Architecture

### Backend (`/app/backend/`)
- `server.py` - Main API server (14,610 lines - needs decomposition)
- `fal_service.py` - fal.ai integration
- `cloudinary_service.py` - Image/PDF storage
- `services/email_service.py` - Email handling
- `services/print_pdf_generator.py` - PDF generation for print

### Frontend (`/app/frontend/src/`)
- `pages/` - Main application pages
  - `BookEditor.js` (3.5k lines)
  - `BookReader.js` (3.1k lines)
  - `ProStudio.js` (6.8k lines)
  - `Library.js`
  - `StoryCreator.js`
- `components/ui/` - Shadcn UI components
- `services/` - API and offline storage

## Test Accounts
- `test@printtest.com` / `printtest` (Pro subscription, 100 credits)
- `karapoole@yahoo.co.uk` / `TempPass123!` (Preview DB only)

## 3rd Party Integrations
- fal.ai (FAL_KEY) - AI image generation
- Stripe - Payments
- Gelato API - Print on demand
- Cloudinary - Image/PDF storage
- ElevenLabs - Text-to-speech
- Resend - Email service
- Emergent LLM Key - AI text generation

## Environment Variables Required
- `JWT_SECRET` - Authentication
- `ADMIN_USERNAME`, `ADMIN_PASSWORD` - Admin access
- `MONGO_URL`, `DB_NAME` - Database
- `FAL_KEY` - fal.ai API
- `STRIPE_SECRET_KEY` - Payments
- `CLOUDINARY_*` - Storage
- `ELEVENLABS_API_KEY` - TTS
- `RESEND_API_KEY` - Email
- `EMERGENT_LLM_KEY` - AI text
