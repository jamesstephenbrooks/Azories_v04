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
- [x] Fixed `/api/pro-studio/characters/{id}/generate-consistent` 500 error
  - Root cause: `physical_traits` stored as `None` causing `.get()` to fail
  - Fix: `character.get('physical_traits') or {}` handles explicit `None`
  - Also fixed HTTPException being swallowed by generic exception handler
- [x] Fixed `get_admin_user` NoneType credentials error
- [x] Merged duplicate Stripe webhook handlers
- [x] Fixed author_id/user_id mismatch for book display
- [x] Added admin endpoint for updating user credits
- [x] Added Book Editor tooltip tour for new users

## Known Issues

### P0 - Critical
- [ ] **Production Environment Instability** - Intermittent 502/520 errors after deployments (infrastructure issue, not code)

### P1 - High Priority
- [ ] **Data Discrepancy** - Preview and production databases are separate; changes in preview don't affect production
- [ ] **Slow thumbnail loading** - Library/dashboard pages load thumbnails slowly

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
