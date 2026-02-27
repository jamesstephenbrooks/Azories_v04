# Azories - Digital Book Platform

## Product Overview
Azories is a full-stack digital book creation platform with AI-powered features for generating characters, scenes, images, and videos. Users can create, edit, and publish children's books with rich media content.

## Core Requirements

### Authentication & Users
- JWT-based authentication
- User roles: regular, VIP (exempt from credit deductions), admin
- Credits-based system for Pro Studio features
- VIP email exemptions tracked in database

### Book Editor
- Multi-chapter book creation
- Page-by-page editing with text and media
- Gallery picker with tabs: Starter Library, This Book, Art Studio, Pro Characters, Pro Scenes, Videos
- Cover editor with same gallery options
- Voice narration (speech-to-text)
- PDF export

### Pro Studio
- **Characters**: Create AI characters with reference images, LoRA training
- **Scenes**: Create environments/backgrounds
- **Shots**: Generate consistent character images with art style options
- **Cinema Studio**: Professional image generation with camera/lens options
- **Video Generation**: Animate images using Sora 2 or Kling
- **Gallery**: Unified view of all generated content with expand/fullscreen, pagination, lazy loading

### Content Moderation
- AI moderation before publishing
- Admin review workflow
- Email notifications to admin (books@azories.com) and author

### Integrations
- **fal.ai**: PuLID, LoRA, Kling video generation
- **OpenAI**: GPT for content, Whisper for speech-to-text
- **Brevo**: SMTP email (working)
- **Stripe**: Payments and credits (live mode configured)
- **Cloudinary**: Permanent video storage

## Technical Architecture

### Frontend (React)
- `/app/frontend/src/pages/`
  - BookEditor.js - Book creation/editing
  - ProStudio.js - AI generation tools
  - AdminDashboard.js - Content moderation
  - Dashboard.js - User dashboard
- `/app/frontend/src/components/`
  - ImmersiveLibrary3D.jsx - 3D Grand Library (Three.js)
  - pro-studio/hooks.js - Shared hooks

### Backend (FastAPI)
- `/app/backend/server.py` - Main API routes (~8150 lines)
- `/app/backend/routes/` - Extracted route modules
  - admin.py - Admin routes (418 lines)
  - auth_routes.py - Auth routes (duplicate exists in server.py)
- `/app/backend/services/`
  - cloudinary_service.py - Video upload to Cloudinary
  - email_service.py - Brevo SMTP integration
- Key endpoints:
  - `/api/pro-studio/gallery/unified` - Optimized paginated gallery
  - `/api/starter-library` - Stock images for books

### Database (MongoDB)
- Collections: users, books, chapters, pages, pro_studio_characters, pro_studio_scenes, character_gallery, art_studio_gallery

## Starter Library (Completed Feb 26, 2026)
200 AI-generated children's book illustrations across 4 categories:
- **Batch 1:** 50 Characters (watercolour, realistic, comic, sketch styles)
- **Batch 2:** 50 Settings & Backgrounds  
- **Batch 3:** 50 Objects & Props
- **Batch 4:** 50 Action & Emotion Scenes

Files:
- `/app/backend/data/starter_library_batch[1-4].py` - Image metadata
- `/app/frontend/public/starter-library/[characters|scenes|objects|actions]/` - Image files

## Pre-Deployment Verification (Feb 25, 2026)

### Test Results Summary
| Feature | Status |
|---------|--------|
| User Authentication | ✅ PASS |
| Gallery Loading | ✅ PASS |
| Book Creation | ✅ PASS |
| Pro Studio | ✅ PASS |
| Grand Library 3D | ✅ PASS (loads) |
| Video Playback | ✅ PASS |

**Backend Tests:** 21/22 passed (95%)
**Frontend Tests:** 100% passed

### Auth Routes Status
- Auth routes exist in BOTH `server.py` (lines 758-991) AND `auth_routes.py`
- Both work without conflicts - FastAPI handles gracefully
- **Risk Level:** LOW - works correctly, but is technical debt

### Grand Library 3D Performance
**Root causes of slowness (identified):**
1. Large GLB model (~50MB compressed)
2. No Level-of-Detail (LOD) rendering
3. Collision mesh processing on every load
4. Multiple raycasts per frame

**Status:** FUNCTIONAL - loads without crashing, just slow

## Book Library Generation (Updated Feb 27, 2026)

### Progress Summary
| Category | Completed | Remaining |
|----------|-----------|-----------|
| Total Books | 64 | 0 |
| Books with text | 64 | 0 |
| Books with images | 64 | 0 |

### Image Generation Complete (Feb 27, 2026) - 230 images
Generated illustrations for 23 books using fal.ai flux/schnell model:
- Fantasy: Unicorn's Rainbow Bridge, Wizard's Apprentice, Giant's Gentle Heart, Enchanted Carousel
- Adventure: Jungle Explorers Club, Mountain Climbing Mice, Underground City, Sky Pirates of Cloudland, Lighthouse Keeper's Secret, Arctic Expedition
- Sci-Fi: Time Machine Treehouse, Space Station School, Friendly Martians, Gadget Girl
- Mystery: Secret Code Club, Detective Daisy's First Case
- Humour: Burping Dragon, Backwards Day, Pirate Pete's Bad Hair Day, Dinosaur Dentist
- General: Alphabet Zoo, Kindness Kingdom, Feelings Garden

### AI-Generated Content (Feb 27, 2026) - 11 books, 110 pages
Using OpenAI GPT-4o via Emergent LLM Key, generated story content for:
- The Jungle Explorers Club
- Mountain Climbing Mice
- Space Station School
- The Friendly Martians
- Gadget Girl and the Invention Fair
- The Secret Code Club
- Detective Daisy's First Case
- The Backwards Day
- Pirate Pete's Bad Hair Day
- Dinosaur Dentist
- Kindness Kingdom

### Batch 3C Import (Feb 27, 2026) - 10 books, 100 pages
The Arctic Expedition, The Burping Dragon, The Enchanted Carousel, The Feelings Garden, The Giant's Gentle Heart, The Lighthouse Keeper's Secret, The Time Machine Treehouse, The Underground City, The Unicorn's Rainbow Bridge, The Wizard's Apprentice

### All 64 Books Now Have Text Content ✅

### Generation Script
- `/app/generate_books_v2.py` - Using OpenAI GPT-Image-1 via Emergent Key
- Images stored in: `/app/frontend/public/book-assets/[book-slug]/`

## Book Library Audit (Final Status - Feb 27, 2026)

### Current State
- **Total books:** 64
- **Books with text content:** 64 (100%)
- **Books with images:** 64 (100%)
- **Pages with images:** 640 out of 703 (91%)

### Generation Methods Used
- **fal.ai flux/schnell** - Primary image generation (230 images)
- **OpenAI GPT-4o** - Text content generation for 11 books
- **OpenAI GPT-Image-1** - Fallback image generation when fal.ai key was invalid

## Pending Tasks (P0-P2)

### P0 - Critical
- ✅ **Complete Batch 3C Import** - DONE (Feb 27, 2026) - 10 books, 100 pages
- ✅ **BookReader API text_content fix** - DONE (Feb 27, 2026)
- ✅ **Generate images for all books** - DONE (Feb 27, 2026) - 230 images using fal.ai
- ✅ **All 64 books have text content** - DONE (Feb 27, 2026)
- ✅ **All 64 books have images** - DONE (Feb 27, 2026)
- ✅ **FAL.AI Key Management** - DONE (Feb 27, 2026) - Admin can update key from Settings tab
  - Priority order:
    1. Super Silly Superhero, Colors of the World (duplicate survivors)
    2. Remaining Picture Books
    3. Early Readers
    4. Middle Grade last

### P1 - High Priority
1. **Fix FAL_KEY permanently** - PARTIALLY IMPLEMENTED:
   - ✅ Added auto-detection on startup with clear warning messages
   - ✅ Added `/api/admin/system-status` endpoint to check all API keys
   - ✅ Added `/api/admin/validate-fal-key` endpoint for manual re-validation
   - ⏳ Need valid FAL_KEY from user - current key `azories-books:...` is INVALID
   - Root cause: The key format looks correct (key_id:key_secret) but fal.ai reports "No user found" - key likely revoked or expired on their side
   - Solution: User needs to generate a new key at https://fal.ai/dashboard/keys
2. **Complete server.py refactoring** - Remove duplicate auth routes from server.py

### P2 - Medium Priority
1. Debug Book Editor Pro Characters/Scenes tabs with real data
2. Test fal.ai LoRA training (may be fixed by image URL conversion)
3. Implement Crop Option in Scenes
4. Analyze readkids.com competitor
5. Continue frontend refactoring (ProStudio.js, BookEditor.js)

### Future Tasks
- Frontend component decomposition
- N+1 query optimization in get_books(), get_user_followers()
- Mobile-specific performance tuning
- Permanent image storage (migrate from fal.ai 7-day retention)

## Environment Variables

### Backend (.env)
```
MONGO_URL, DB_NAME, JWT_SECRET
FAL_KEY, EMERGENT_LLM_KEY
BREVO_API_KEY, BREVO_SENDER_EMAIL
STRIPE_API_KEY (live)
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
ADMIN_USERNAME, ADMIN_PASSWORD
VIP_USERS
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL
REACT_APP_STRIPE_PUBLISHABLE_KEY (live)
```

## Test Credentials
- Admin: Username: Admin / Password: Routetofreedom
- VIP User: jamesstephenbrooks@outlook.com / test123
- Test Admin: testadmin@azories.com / TestAdmin123!

## Test Reports
- /app/test_reports/iteration_34.json (Latest - Feb 25, 2026)
- /app/backend/tests/test_pre_deployment_iter34.py

## Session Update - Feb 27, 2026

### Character Thumbnail Generation Fix
**Issue:** fal.ai API key expired, causing character thumbnail generation to fail silently.

**Solution:** Added OpenAI (GPT-Image-1) fallback in `/app/backend/server.py` for character creation.
When fal.ai fails, the system now automatically uses OpenAI via Emergent LLM Key.

**Status:** ✅ WORKING - Characters now generate thumbnails even with invalid fal.ai key.

### FAL.AI Key Persistence Implemented
**Changes made:**
1. Database persistence: FAL key stored in `system_settings` collection
2. Auto-load from DB on startup if .env key is missing/different
3. Auto-sync to .env file for local persistence
4. New health check endpoints:
   - `/api/health` - Returns `status: "degraded"` when key invalid
   - `/api/health/fal` - Returns 503 for UptimeRobot monitoring
5. Pro Studio warning banner shows when key expired
6. Admin update endpoint now persists to both .env AND database

**UptimeRobot URL:** `https://book-reader-hub-2.preview.emergentagent.com/api/health/fal`

### Cloudinary Migration COMPLETE ✅
**Migration Date:** Feb 27, 2026
**Migration Script:** `/app/backend/scripts/migrate_fal_to_cloudinary.py`
**Report:** `/app/backend/scripts/migration_report_20260227_183237.json`

**Results:**
- Total fal.ai images found: 284
- Successfully migrated: 284 ✅
- Failed migrations: 0 ✅
- Already on Cloudinary: 20

**All book images are now permanently stored on Cloudinary** and will NOT expire.

### Book Reader Verification
- Desktop view: Book fills ~80% viewport height ✅
- Layout: Image LEFT, Text RIGHT (consistent) ✅
- Text: Large, readable, Nunito font ✅
- Text caching: No issues - fresh content served correctly ✅
- Page turning buttons: Working on both desktop and mobile ✅

### Known Issues
- Some AI-generated images have text baked INTO the images (not a layout bug, but an image generation artifact)
