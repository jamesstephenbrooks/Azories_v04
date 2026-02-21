# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations, Three.js for 3D
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented

### Latest Updates (Feb 21, 2026) - 3D Library Mobile & Camera Fixes
- **Camera starting angle**: Now tilted down (-0.2 rad) to see floor, bookcases, and room
- **Camera position**: Set at (0, floorY+1.1, 2) looking toward bookcases
- **Gravity simplified**: Fixed to floor level (4.72) to prevent floating/jumping
- **Touch panning sensitivity**: Increased 3x (0.003 → 0.008) for faster look-around
- **Mobile UI cleanup**: Hidden Azora button and Books panel on mobile for clear joystick
- **Mobile joystick**: Visual joystick at bottom-left for touch movement

### Previous Session: Core Fixes
- Fixed floor-following gravity
- Added mobile joystick controls
- Responsive welcome screen (touch vs keyboard instructions)
- Disabled Azora, banners, and book markers (need calibration)

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
- [x] Camera starting angle (see floor + bookcases)

### P1 (High Priority) - IN PROGRESS
- [ ] Test mobile joystick on device
- [ ] Verify walking works properly
- [ ] Re-enable Azora with correct floor position
- [ ] Re-enable genre banners above bookcases
- [ ] Stripe payment integration

### P2 (Medium Priority)
- [ ] Interactive books on shelves
- [ ] Art Studio node-based UI (React Flow)
- [ ] Personalized book recommendations

### P3 (Nice to Have)
- [ ] "Call Azora Over" walking feature
- [ ] Multiplayer library exploration
- [ ] Animate still images

## Key Files
- `/app/frontend/src/components/ImmersiveLibrary3D.jsx` - 3D library logic
- `/app/frontend/src/pages/Library.js` - Library page with view modes
- `/app/backend/server.py` - All backend routes

## Technical Notes - 3D Library
- Library bounds: X: -9.5 to 9.5, Z: -9.5 to 9.5
- Floor level: Y = 4.722
- Player height: 1.1m (eye level Y: 5.82)
- Camera start: (0, 5.82, 2) facing negative Z
- Camera tilt: -0.2 radians (looking down)
- Touch sensitivity: 0.008 (panning), threshold 15px (joystick)
- Mobile UI: Joystick visible, Books panel and Azora button hidden

## Currently Disabled (Need Calibration)
1. Azora 3D model - position needs calibration
2. Genre banners - need correct bookcase positions
3. Interactive book markers - need shelf position mapping
