# Azories - AI Story Creator PRD

## Original Problem Statement
Build a "Print on Demand" (POD) book ordering feature using the Gelato API for an AI Story Creator platform. The platform allows users to create AI-powered personalized children's stories with illustrations.

## Core Features Implemented
- **AI Story Creation**: Create personalized stories with AI-generated illustrations using fal.ai (FLUX.1-schnell and Ideogram V3 models)
- **Book Reader**: Interactive flipbook reader with audio narration (ElevenLabs)
- **Print on Demand**: Full POD integration with Gelato API, Stripe payments, CSS 3D book preview
- **User Library**: Personal book collection management
- **Art Styles**: Multiple AI art styles including Storybook, Character (Consistent), Realistic
- **Offline Reading**: Phase 1 implemented - save books for offline reading via IndexedDB

## Architecture
```
/app/
├── backend/
│   ├── server.py             # Main FastAPI server
│   ├── routes/
│   │   ├── auth_routes.py    # Authentication (with remember_me fix)
│   │   └── print_orders.py   # POD ordering endpoints
│   └── services/
│       ├── print_pdf_generator.py  # PDF generation for print
│       ├── gelato_service.py       # Gelato API integration
│       └── fal_service.py          # AI image generation
└── frontend/
    └── src/
        ├── pages/
        │   ├── Dashboard.js        # My Books (offline support added)
        │   ├── BookReader.js       # Book reading experience
        │   ├── StoryCreator.js     # AI story creation
        │   └── Landing.js          # Homepage
        ├── components/
        │   ├── SaveOfflineButton.jsx   # Offline save button
        │   ├── OfflineBanner.jsx       # Offline status banner
        │   └── print/
        │       ├── BookPreview3D.jsx   # CSS 3D book mockup
        │       └── PrintOrderModal.jsx # POD ordering flow
        ├── services/
        │   └── offlineStorage.js   # IndexedDB offline storage
        └── hooks/
            └── useOffline.js       # Offline state management
```

## 3rd Party Integrations
- **fal.ai**: AI image generation (FLUX.1-schnell, Ideogram V3)
- **Gelato API**: Print on Demand fulfillment
- **Stripe**: Payment processing
- **Cloudinary**: Image/PDF storage (using chunked upload for large files)
- **ElevenLabs**: Text-to-speech narration (primary, with OpenAI TTS fallback)

## Latest Fixes (March 7, 2026)

### "Keep me signed in" Bug - FIXED
**Root Cause**: The login endpoint in `/app/backend/routes/auth_routes.py` was:
1. Using `JWT_EXPIRATION_HOURS = 720` (30 days) as default instead of 24 hours
2. Not passing `remember_me` parameter to `create_token()` function

**Fix Applied**:
- Changed `JWT_EXPIRATION_HOURS` default from 720 to 24 hours
- Added `JWT_REMEMBER_ME_DAYS = 30` constant  
- Updated `create_token()` to accept `remember_me` parameter
- Updated `UserLogin` model to include `remember_me: bool = False`
- Login endpoint now passes `user_data.remember_me` to `create_token()`

**Verification**: Tested via curl - token now expires in 24h without checkbox, 30 days with checkbox ✅

### Free Book/Story Creation - FIXED
**Issue**: New users saw "Upgrade to Pro" when trying to create books

**Fix Applied**:
- Removed Pro subscription check from `create_book()` in `server.py`
- Removed Pro subscription check from `create_series()` in `server.py`
- Updated Dashboard.js to show "AI Stories" and "New Book" buttons to all users
- Removed "Upgrade to Pro" button from dashboard header
- Updated empty state to show create options for all users

**Note**: New users automatically get 3-day Pro trial with `subscription: "pro"`. AI story generation has its own free tier (3 free stories in Kids Mode, 5 pages).

### Offline Reading Feature - Phase 1 IN PROGRESS
**Implemented**:
- `offlineStorage.js` - IndexedDB service for caching books
- `useOffline.js` - React hook for offline state management
- `SaveOfflineButton.jsx` - Save/remove offline button component
- `OfflineBanner.jsx` - Shows when user is offline
- Dashboard integration with offline filter and storage stats

**Pending**:
- Phase 2: Offline indicators on book cards, offline-only filter in library
- Phase 3: Cache narration audio files

## Pending Verification (by User)
- **P1**: iPad button responsiveness (expand menu, play button) - `touch-manipulation` fix applied
- **P1**: Pro Studio mobile fixes (lightbox, delete, download) - refactored gallery
- **P1**: Photorealistic art style fix - now prioritizes selected_style over detected_style
- **P2**: Checkbox size on iPad - `md:scale-[0.6]` fix applied

## Future/Backlog
- P1: Complete Offline Reading Phase 2 & 3
- P2: Full E2E POD test (payment through to Gelato order creation)
- P2: Build "My Orders" page for order history
- Order tracking notifications (email/SMS)
- Gift feature for checkout
- Decompose BookReader.js (>2000 lines)

## Test Credentials
- Email: test@printtest.com
- Password: printtest

## Key API Endpoints
- `POST /api/auth/login` - Login (with remember_me support)
- `POST /api/auth/register` - Register (3-day Pro trial)
- `POST /api/books` - Create book (free for all users)
- `POST /api/ai/generate-story-async` - Generate AI story
- `GET /api/pricing` - Get art style pricing
- `POST /api/print/prepare/{book_id}` - Prepare book PDF
- `POST /api/print/checkout/create-session` - Create Stripe checkout

## Latest Updates (March 7, 2026 - Session 2)

### Image Generation Model Change
- **Switched from FLUX Dev to FLUX Pro** for AI story image generation
- Settings remain: 2400x3000px (print quality), 28 inference steps, 3.5 guidance scale
- FLUX Pro provides higher quality images suitable for print

### AI Image Generation in Book Editor - NEW FEATURE
- Added "AI Image" button next to "Upload Image" in the Book Editor
- Uses page text content as the prompt basis
- Generates images using FLUX Pro at print quality (2400x3000px)
- Works for both AI-generated and manually created stories
- Images automatically uploaded to Cloudinary for permanent storage

**Backend endpoint**: `POST /api/ai/generate-page-image`
- Parameters: `page_id`, `prompt` (optional), `art_style`, `use_page_text`
- Uses book's art style for consistent imagery
- Returns Cloudinary URL for the generated image

### Words per Page Option - NEW FEATURE  
- Added "Words per Page" dropdown to AI Story Creator
- Options: Short (~50), Medium (~100), Long (~150), Extended (~200 - Studio only)
- Allows users to control story text density

### AI Stories Now Fully Editable
- AI-generated stories now create a default chapter for editor compatibility
- Auto-migration creates chapters for legacy AI books without them
- Pages properly linked to chapters for full editing support
