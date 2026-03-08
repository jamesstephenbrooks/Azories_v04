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

### Offline Reading Feature - Phase 1 COMPLETED
**Implemented**:
- `offlineStorage.js` - IndexedDB service for caching books
- `useOffline.js` - React hook for offline state management
- `SaveOfflineButton.jsx` - Save/remove offline button component
- `OfflineBanner.jsx` - Shows when user is offline
- Dashboard & Library integration with offline filter and storage stats
- Service Worker for app shell caching

**Phase 1 Complete**:
- ✅ Cache book images and text when user taps "Save for Offline"
- ✅ Show offline indicator on saved books
- ✅ Offline filter to show only saved books

**Pending Phases**:
- Phase 2: None (integrated into Phase 1)
- Phase 3: Cache narration audio files

## Pending Verification (by User)
- **P1**: iPad button responsiveness (expand menu, play button) - `touch-manipulation` fix applied
- **P2**: Checkbox size on iPad - `md:scale-[0.6]` fix applied

## Known Issues - Deferred
- **P1**: Pro Studio mobile bugs (image deletion, video download) - User requested deferral
- **P2**: Slow thumbnail loading in Library - Needs investigation

## Future/Backlog
- P1: Complete Offline Reading Phase 3 (audio caching)
- P1: Pro Studio mobile bugs (image deletion, video download)
- P2: Build "My Orders" page for order history
- P2: Slow thumbnail loading optimization
- P3: Order tracking notifications (email/SMS)
- P3: Gift feature for checkout
- P3: Decompose BookReader.js (>2000 lines)

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

## Latest Updates (March 8, 2026)

### Service Worker & Offline App Shell - COMPLETED
- Service Worker registered in `/app/frontend/src/index.js`
- Smart caching strategy in `/app/frontend/public/service-worker.js`:
  - Network-first for navigation (HTML pages)
  - Cache-first for app shell assets (JS, CSS, images)
  - Bypasses API requests for fresh data
- Offline fallback page (`/app/frontend/public/offline.html`)
- Console shows `[Azories SW] Service worker registered` on load

### Offline Reading Phase 1 - COMPLETED
- ✅ Save books for offline via "Save for Offline" button on book cards
- ✅ IndexedDB stores book metadata, cover, and page images
- ✅ Offline indicator badge on saved books in Library
- ✅ "Offline" filter button to show only saved books
- ✅ Storage stats display (MB used)
- **Note**: Narration audio caching deferred to Phase 3

### BookEditor Page Switching Bug - FIXED
**Root Cause**: Stale closure in auto-save timeout captured old `selectedPage` state
**Fix Applied**:
- Added `pendingAutoSaveRef` to capture page data at edit time, not timeout fire time
- `handlePageSelect` now saves current page to backend before switching
- `selectedPageRef` keeps page state always up-to-date for callbacks
- Tested: Text preserved after 4+ page switches (verified by testing agent)

### Print on Demand E2E - VERIFIED WORKING
Full flow tested and passing:
1. Login → Open book → "Order Printed Copy" button visible
2. 4-step wizard modal with 3D book preview
3. Product selection (Softcover £14.99 / Hardcover £19.99)
4. Shipping address form with country selection
5. Shipping method selection (Standard/Express/Overnight)
6. Order review with coupon validation (LAUNCH10 = 10% off)
7. Stripe checkout redirect working

**API Endpoints Verified**:
- `GET /api/print/product-info` - Returns products, gelato_configured: true
- `POST /api/print/checkout/create-session` - Creates Stripe checkout
- `POST /api/print/validate-coupon` - Validates discount codes

## Previous Updates (March 7, 2026)

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
