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
| Total Books | 47 | 26 |
| Books with text | 47 | 17 |
| Books with images | ~37 | ~28 |

### Batch 3C Import (Feb 27, 2026) - 10 books, 100 pages
The Arctic Expedition, The Burping Dragon, The Enchanted Carousel, The Feelings Garden, The Giant's Gentle Heart, The Lighthouse Keeper's Secret, The Time Machine Treehouse, The Underground City, The Unicorn's Rainbow Bridge, The Wizard's Apprentice

### Previously Completed Books (37 total)
Fantasy: Dragon's Secret Garden, Unicorn's Rainbow Bridge, Princess Penny's Pet Dragon, Wizard's Apprentice, Fairies of Moonlight Meadow, Mermaid's Lost Pearl, Elves & Magic Tree, Giant's Gentle Heart, Pixie Dust Adventures, Enchanted Carousel

Adventure: Captain Compass, Jungle Explorers Club, Mountain Climbing Mice, Underground City, Sky Pirates of Cloudland, Safari Sam's Big Day, River Rafting Raccoons, Arctic Expedition

Sci-Fi: Aliens at My School, Space Station School, Friendly Martians, Gadget Girl, Astronaut Alex's Moon Mission

Mystery: Secret Code Club, Detective Daisy's First Case

Humour: Burping Dragon, Backwards Day, Pirate Pete's Bad Hair Day, Monster Who Was Scared of Kids, Dinosaur Dentist

General: Alphabet Zoo, Seasons of Magic Forest, Kindness Kingdom, Feelings Garden, Robot Best Friend, Superhero School, Case of Missing Cookies

### Books Still Empty (26)
Bedtime in the Animal World, Colors of the World, Cooking Adventures with Chef Cat, Desert Treasure Hunt, Flame's Courageous Journey, Friendship Island, Galaxy Racers, Guardians of Tomorrow (x2), Lila and the Whispering Blossoms, Luna's Rainbow Adventure, Mystery at the Zoo, Numbers Come Alive, Ocean Wonders, Princess and the Enchanted Forest, Puzzle Palace Adventures, Shapes in the City, The Dinosaur Time Machine, The Emotion Squad, The Haunted Library Book, The Haunted Treehouse, The Journey to Merlden, The Lighthouse Keeper's Secret, The Midnight Brush, The Missing Birthday Present, The Robot Who Wanted Friends, The Time Machine Treehouse

### Generation Script
- `/app/generate_books_v2.py` - Using OpenAI GPT-Image-1 via Emergent Key
- Images stored in: `/app/frontend/public/book-assets/[book-slug]/`

## Book Library Audit (Final Status)

### Original State → Current State
- **Started with:** 80 empty book shells (titles only, no content)
- **After cleanup:** 65 books (15 deleted)
- **Now completed:** 37 books with full content
- **Still empty:** 28 books

### Deletions (15 books removed)
**Test books (4):** PDF Test Book, Font Size Test Book, Node Test Book, Jamie The City Hero

**Overlapping titles (11):** Grandma's Wacky Inventions, The Great Golden Cookie Caper, The Mystery of the Missing Cookies, The Dragon's Secret, Journey to Planet Sparkle, Space Explorers: Mission to Mars, Captain Clara and the Kindness Quest

### Duplicates Handled
One copy of each duplicate pair was kept and completed:
- Robot Best Friend (completed)
- The Case of the Missing Cookies (completed)  
- Super Silly Superhero (still empty - priority for next session)
- Colors of the World (still empty - priority for next session)
- Guardians of Tomorrow (1 duplicate deleted, 1 remains empty)

### Starter Library Usage
- **3 images** from the 200-image starter library used (only in "The Unicorn's Rainbow Bridge")
- **371 images** freshly generated using GPT-Image-1 and fal.ai
- Note: Starter library is designed for the Book Editor gallery picker, not for pre-populating library books

## Pending Tasks (P0-P2)

### P0 - Critical
- **Complete remaining 27 books** (was 28, deleted 1 duplicate)
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

## Test Reports
- /app/test_reports/iteration_34.json (Latest - Feb 25, 2026)
- /app/backend/tests/test_pre_deployment_iter34.py
