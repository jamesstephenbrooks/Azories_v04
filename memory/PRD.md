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

## Pending Tasks (P0-P2)

### P0 - Critical
- None (pre-deployment checks passed)

### P1 - High Priority
1. **Complete server.py refactoring** - Remove duplicate auth routes from server.py
2. **Grand Library performance optimization** - Implement LOD, asset compression

### P2 - Medium Priority
1. Debug Book Editor Pro Characters/Scenes tabs with real data
2. Implement Crop Option in Scenes
3. Analyze readkids.com competitor
4. Continue frontend refactoring (ProStudio.js, BookEditor.js)

### Future Tasks
- Frontend component decomposition
- N+1 query optimization in get_books(), get_user_followers()
- Mobile-specific performance tuning

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
