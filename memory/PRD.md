# Azories - Digital Book Creation and Reading Platform

## Original Problem Statement
Build a digital book creation and reading application named "Azories" with features including:
- Book reader with audio narration (TTS)
- Book editor ("Edit My Books")
- Series manager ("My Series")
- AI librarian ("Azora")
- 3D library environment
- Art Studio for generating assets
- **Pro Studio** for AI-powered character and scene consistency
- **Business Model** with credits, Stripe payments, VIP users, and admin analytics

## What's Been Implemented

### Core Features (Completed)
- Full-stack React/FastAPI/MongoDB application
- Book reading experience with page flip animations (react-pageflip)
- Text-to-Speech using OpenAI TTS (via Emergent LLM Key)
- Audio pre-caching for smoother playback between pages
- Book editor with font/style customization
- Chapter management
- User authentication (JWT-based)
- Reading progress tracking

### Pro Studio Features (Completed - Feb 23, 2026)
1. **Character Consistency System**
   - Create characters with text descriptions AND/OR reference images
   - AI generates thumbnails using fal.ai FLUX
   - Character folder/portfolio system for organizing generated images
   - Reference image collection for LoRA training (need 3+ images)
   - Edit/Delete character functionality

2. **Scene Consistency System**
   - Create consistent scenes/environments for book illustrations
   - Configure: location type, lighting, mood, time of day, weather
   - AI-generated scene thumbnails
   - Scene folder for storing related images

3. **Credits System**
   - Credit costs: FLUX generate (1), FLUX Pro (2), PuLID (3), LoRA training (50), Video (10)
   - Credits display in header with add button
   - Balance tracking per user

4. **Additional Pro Studio Features**
   - Cinema Studio (camera/lens/lighting presets)
   - Shots (9 angles from 1 image)
   - Video generation (Sora 2)
   - Gallery for saving generated images

### Payment & Credits System (Completed - Feb 23, 2026)
**Pricing Model (50% profit margin) - GBP:**
| Package | Credits | Price |
|---------|---------|-------|
| Starter | 100 | £5 |
| Creator | 500 | £18 (Most Popular) |
| Pro | 1,000 | £30 |
| Studio | 5,000 | £120 |

**VIP Users (Unlimited Credits - tracked for costs):**
- arianamillb@icloud.com
- jamesstephenbrooks@outlook.com

### Professional Features (Completed - Feb 23, 2026)
- Cookie Consent popup (GDPR compliant)
- Terms of Service page (/terms)
- Privacy Policy page (/privacy)
- Contact form (/contact) - books@azories.com
- Admin Analytics dashboard (/admin/analytics)
  - User metrics, revenue, book stats
  - Credit usage tracking
  - VIP cost monitoring
- Stripe payment integration for credit purchases

## Sample Books Created (Feb 23, 2026)
6 fully illustrated children's books with AI-generated content:
1. **Luna's Rainbow Adventure** - Sci-Fi (3D render style)
2. **Lila and the Whispering Blossoms** - Fantasy (watercolor style)
3. **The Great Golden Cookie Caper** - Mystery (cartoon style)
4. **Captain Clara and the Kindness Quest** - Adventure (illustration style)
5. **The Midnight Brush** - Fantasy (storybook style)
6. **The Emotion Squad: Power of Unity** - Adventure (comic style)

All books have:
- Professional AI-generated covers
- Page-by-page illustrations
- Age-appropriate engaging stories
- Published and ready to read

## E2E Testing Results (Feb 23, 2026)
- **Backend: 100% (33/33 tests passed)**
- **Frontend: 100% (all tested features working)**
- fal.ai integration confirmed working
- All Pro Studio tabs functional
- Character and scene creation with AI thumbnails working

## Architecture

### Frontend (/app/frontend)
- React with Tailwind CSS
- react-pageflip for book animations
- Shadcn/UI components
- Key files:
  - `/pages/ProStudio.js` - Pro Studio UI (~3300 lines)
  - `/pages/BookReader.js` - Main reader component
  - `/pages/BookEditor.js` - Book editing
  - `/pages/Credits.js` - Credit purchasing UI
  - `/pages/AdminAnalytics.js` - Admin dashboard

### Backend (/app/backend)
- FastAPI
- MongoDB via MONGO_URL
- fal.ai integration for image generation
- OpenAI TTS integration
- Key files:
  - `server.py` - Main API (~6500 lines, monolithic)
  - `fal_service.py` - fal.ai integration

### Environment Variables
- Frontend: REACT_APP_BACKEND_URL
- Backend: MONGO_URL, DB_NAME, EMERGENT_LLM_KEY, FAL_KEY, STRIPE_API_KEY

## Known Issues / Pending

### P1 (High Priority)
- iPad "Read Aloud" fix needs real-device testing
- End-to-end LoRA training test (create character with 3+ images, click Train)

### P2 (Medium Priority)
- Scene list may need refresh to show newly created scenes

### Resolved (Feb 23, 2026)
- ✅ Back cover visibility at end of book - Fixed by changing Next button disabled condition
- ✅ LoRA training workflow UI - Validated Train button logic works correctly
- ✅ Credits security - Regular users must now purchase via Stripe, can't add credits directly
- ✅ PuLID/LoRA style consistency - Now includes character's style/genre in generation prompts
- ✅ fal.ai API key updated - New key working for all fal.ai features
- ✅ Scene Templates - Now shows landscape thumbnails in Scene Creator tab
- ✅ Animation API fix - Removed unsupported image_path parameter from Sora 2 calls

### Feature Requests - Completed (Feb 23, 2026)
- ✅ Node Editor: Continue Workflow button on output nodes
- ✅ Node Editor: Node copy/duplication functionality on all node types
- ✅ Node Editor: Save to Book functionality for book-specific image libraries
- ✅ Node Editor: Image node type for workflow continuation
- ✅ Voice Narration: Speech-to-text for book writing (OpenAI Whisper)
- ✅ LoRA Training: Fixed with new fal.ai API key - training now starts successfully

### P3 (Low Priority)
- Grand Library stair navigation/camera issues
- iPad/iPhone UI layout optimizations
- Code refactoring (split server.py and ProStudio.js into modules) - STARTED

## Next Tasks
1. Code refactoring continuation (migrate routes from server.py to modules)
2. Mobile UI/UX testing on real iPad
3. Animation save/download full verification

## Future/Backlog
- Export Book as PDF feature (already exists)
- Book Editor collaboration features
- Additional mobile optimizations
- Frontend refactoring (ProStudio.js split into components)

## 3rd Party Integrations
- **OpenAI GPT-4o & Sora 2** (via Emergent LLM Key) - Text generation, video
- **fal.ai** (fal-client) - Image generation (FLUX), PuLID, LoRA
- **Stripe** - Payment processing
- **react-pageflip** - Book animations
- **React Three Fiber / Drei** - 3D library view

## Test Credentials
- Email: test@test.com
- Password: test123

## Key API Endpoints
- `POST /api/auth/login` - User login
- `GET/POST /api/pro-studio/characters` - Character CRUD
- `GET/POST /api/pro-studio/scenes` - Scene CRUD
- `GET/POST /api/pro-studio/characters/{id}/gallery` - Character folder
- `GET/POST /api/pro-studio/scenes/{id}/gallery` - Scene folder
- `POST /api/art-studio/gallery` - Save to main gallery
- `GET/POST /api/books/{book_id}/images` - Book image library
- `DELETE /api/books/{book_id}/images/{image_id}` - Delete book image
- `POST /api/speech-to-text` - Voice narration transcription (NEW)
- `GET /api/credits/balance` - Get credits
- `POST /api/credits/add` - Add credits
- `POST /api/create-checkout-session` - Stripe checkout
- `GET /api/admin/analytics` - Admin dashboard data
- `POST /api/contact` - Contact form submission

## Code Refactoring Status
Backend route modules created (templates):
- `/app/backend/routes/auth.py` - Authentication
- `/app/backend/routes/credits.py` - Credits management
- `/app/backend/routes/books.py` - Book CRUD
- `/app/backend/routes/pro_studio.py` - Pro Studio features

See `/app/memory/REFACTORING_PLAN.md` for full details.
