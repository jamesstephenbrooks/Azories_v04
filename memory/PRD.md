# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations, Three.js for 3D
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented

### Latest Updates (Feb 21, 2026) - 3D Library Fixes
- **Fixed Large Geometry Issue**: Removed ornate_book.glb that was causing large floating purple geometry
- **Interactive Books**: Replaced with simple small box markers (0.08x0.25x0.15) positioned on back wall bookcases
- **Genre Banners**: Repositioned above actual bookcases (Fantasy/Mystery/Adventure at z=-4)
- **Azora Position**: Moved to floor near right bookcase (x=3.5, y=floorLevel, z=-2)
- **Player Height**: Adjusted from 1.2 to 1.6 for more grounded camera feel
- **Movement Physics**: Simplified to prevent vertical jumping issues

### Previous Session: 3D Library Major Rewrite
- **Camera-relative controls**: WASD/Arrow keys move in direction facing
- **Click-and-drag mouse look**: Replaced buggy pointer lock system
- **Genre teleport sections**: "Jump to Section" with Fantasy, Adventure, Mystery, Sci-Fi zones
- **AI Librarian "Azora"**: 3D GLB model, clickable for chat
- **New GLB model**: gothic_library_16_cycles-compressed.glb

### Core Features Implemented
- Full-stack book creation platform
- AI image/video generation (10 image styles, 8 video styles)
- AI story generation with media options
- Text-to-Speech (ElevenLabs, 22+ voices)
- Auto-save (2-second debounce)
- Book series management
- Reading streaks & badges
- User profiles with social features
- Ambient sounds system
- Offline reading support
- Admin CMS at /admin

## Test Credentials
- **Admin**: azories_admin / AzoriesAdmin2024!
- **Test Author**: testauthor@azories.com / TestAuthor123! (Pro)
- **Test User**: testuser@example.com / password123 (Pro)

## Prioritized Backlog

### P0 (Critical) - IN PROGRESS
- [x] Core reading/creation experience
- [x] Authentication
- [x] AI generation (image + video)
- [x] Admin CMS
- [x] 3D Library with GLB model
- [ ] **3D Library fine-tuning** - Banner positions, Azora placement, book marker alignment

### P1 (High Priority)
- [ ] Stripe payment integration
- [ ] Voice narration UI improvements (mic access prompt)
- [ ] Jump to Section teleport fixes
- [ ] Realistic page-turning animation

### P2 (Medium Priority)
- [ ] Art Studio node-based UI (React Flow)
- [ ] AI Librarian knowledge enhancement
- [ ] "Call Azora Over" feature
- [ ] Personalized book recommendations

### P3 (Nice to Have)
- [ ] Multiplayer library exploration
- [ ] Animate still images
- [ ] Comic book advanced layouts
- [ ] Vector logo creation

## API Endpoints
- `/api/auth/*` - Authentication
- `/api/books/*` - Book CRUD
- `/api/ai/*` - AI generation endpoints
- `/api/admin/*` - Admin CMS
- `/api/proxy/glb` - GLB model proxy (CORS bypass)
- `/api/ambient-sounds/*` - Ambient sound proxy
- `/api/users/*` - User profiles and social
- `/api/art-studio/*` - Art Studio (new, placeholder)

## Key Files
- `/app/frontend/src/components/ImmersiveLibrary3D.jsx` - 3D library logic (~1050 lines)
- `/app/frontend/src/pages/Library.js` - Library page with view modes
- `/app/frontend/src/pages/ArtStudio.jsx` - Art Studio placeholder
- `/app/backend/server.py` - All backend routes (monolithic)

## Known Issues
1. Genre banners may need coordinate adjustment based on actual bookcase positions
2. Azora position may need fine-tuning to be visible
3. Interactive book markers need alignment with visible shelf space
4. Jump to Section teleport coordinates need updating to match new genre positions
