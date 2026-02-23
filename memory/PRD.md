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

### E2E Testing Results (Feb 23, 2026)
- **Backend: 100% (33/33 tests passed)**
- **Frontend: 100% (all tested features working)**
- fal.ai integration confirmed working with updated API key
- All Pro Studio tabs functional
- Character and scene creation with AI thumbnails working

### Payment & Credits System (Feb 23, 2026)
**Pricing Model (50% profit margin):**
- Starter: 100 credits for $5 (~10 images)
- Creator: 500 credits for $20 (~50 images) - MOST POPULAR
- Pro: 1,000 credits for $35 (~100 images or 1 LoRA)
- Studio: 5,000 credits for $150 (~500 images)

**VIP Users (Unlimited Credits - tracked for costs):**
- arianamillb@icloud.com
- jamesstephenbrooks@outlook.com

### Professional Features Added (Feb 23, 2026)
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

## Architecture

### Frontend (/app/frontend)
- React with Tailwind CSS
- react-pageflip for book animations
- Shadcn/UI components
- Key files:
  - `/pages/ProStudio.js` - Pro Studio UI (~3000+ lines)
  - `/pages/BookReader.js` - Main reader component
  - `/pages/BookEditor.js` - Book editing

### Backend (/app/backend)
- FastAPI
- MongoDB via MONGO_URL
- fal.ai integration for image generation
- OpenAI TTS integration
- Key files:
  - `server.py` - Main API (monolithic)
  - `fal_service.py` - fal.ai integration

### Environment
- Frontend: REACT_APP_BACKEND_URL
- Backend: MONGO_URL, DB_NAME, EMERGENT_LLM_KEY, FAL_KEY

## Known Issues / Pending

### P0 (Critical)
- None currently blocking

### P1 (High)
- ~~Re-enable credits system~~ ✅ DONE (Feb 23, 2026) - Credits now deducted for all Pro Studio operations
- LoRA training full workflow validation
- ~~Video generation UX~~ ✅ IMPROVED (Feb 23, 2026) - Added progress bar display

### P2 (Medium)
- Back cover visibility at end of book
- "Read Aloud" button error on iPad
- Scene list may need refresh to show newly created scenes

### P3 (Low)
- Grand Library stair navigation/camera issues
- iPad/iPhone UI layout fixes
- Code refactoring (split server.py and ProStudio.js)

## Upcoming Tasks
1. **Deploy to azories.com** - User's next requested step
2. Re-enable credits system before deployment
3. Full LoRA training implementation and testing

## 3rd Party Integrations
- **OpenAI GPT-4o & Sora 2** (via Emergent LLM Key) - Text generation, video
- **fal.ai** (fal-client) - Image generation (FLUX), PuLID, LoRA
- **react-pageflip** - Book animations
- **React Three Fiber / Drei** - 3D library view

## Test Credentials
- Email: test@test.com
- Password: test123
- OR Email: test / Password: test (alternate)

## API Endpoints (Key)
- `POST /api/auth/login` - User login
- `GET/POST /api/pro-studio/characters` - Character CRUD
- `GET/POST /api/pro-studio/scenes` - Scene CRUD
- `GET/POST /api/pro-studio/characters/{id}/gallery` - Character folder
- `GET/POST /api/pro-studio/scenes/{id}/gallery` - Scene folder
- `POST /api/art-studio/gallery` - Save to main gallery
- `GET /api/credits/balance` - Get credits
- `POST /api/credits/add` - Add credits
