# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations, Three.js for 3D
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented

### Latest Updates (Feb 21, 2026) - 3D Library Mobile & Gravity Fixes
- **Floor-following gravity**: Camera now properly follows terrain with raycast detection
- **Mobile joystick**: Added visual joystick (bottom-left) for touch movement controls
- **Responsive welcome screen**: Shows joystick instructions on mobile, keyboard on desktop
- **Disabled Azora**: Removed until positioning can be calibrated
- **Disabled book markers**: Removed floating boxes until shelf positions determined
- **Disabled genre banners**: Removed until correct bookcase positions identified
- **Camera height**: Set to 1.1m for proper library scale

### Previous Session: 3D Library Rendering Fixes
- Fixed "purple screen" issue
- Camera positioned correctly facing bookcases
- Scene background updated to warm brown
- Removed large floating geometry from ornate_book.glb

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

### P0 (Critical) - COMPLETED
- [x] Core reading/creation experience
- [x] Authentication
- [x] AI generation (image + video)
- [x] Admin CMS
- [x] 3D Library with GLB model
- [x] Floor-following gravity
- [x] Mobile joystick controls

### P1 (High Priority) - IN PROGRESS
- [ ] Re-enable genre banners with correct positions
- [ ] Re-enable Azora with proper calibration
- [ ] Re-enable interactive books on shelves
- [ ] Stripe payment integration
- [ ] Voice narration UI improvements

### P2 (Medium Priority)
- [ ] Art Studio node-based UI (React Flow)
- [ ] Personalized book recommendations
- [ ] "Call Azora Over" feature

### P3 (Nice to Have)
- [ ] Multiplayer library exploration
- [ ] Animate still images
- [ ] Comic book advanced layouts

## Key Files
- `/app/frontend/src/components/ImmersiveLibrary3D.jsx` - 3D library logic
- `/app/frontend/src/pages/Library.js` - Library page with view modes
- `/app/backend/server.py` - All backend routes

## Known Issues (Currently Disabled)
1. Genre banners need position calibration to appear above bookcases
2. Interactive book markers need shelf position calibration
3. Azora 3D model needs proper floor positioning

## Technical Notes - 3D Library
- Floor level detected at Y: 4.72
- Player height: 1.1m (eye level Y: 5.82)
- Camera start position: (0, 5.82, 3)
- GLB model: gothic_library_16_cycles-compressed.glb
- Mobile uses touch joystick, desktop uses WASD + mouse drag
