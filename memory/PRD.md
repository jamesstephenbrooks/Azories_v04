# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations, Three.js for 3D
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented

### Latest Updates (Feb 21, 2026) - Debug Mode & Physics Improvements
- **Coordinate Debug Mode**: Toggle in 3D library to click and get exact (x, y, z) coordinates
- **Debug Panel**: Shows last click coords, mesh name, camera position, copy button
- **Enhanced Stair Physics**: Multi-ray foot sensor (center, forward, forward-left, forward-right)
- **Increased Step Height**: 1.0m for stairs (was 0.7m) to handle spiral stairs
- **Removed Simple 3D View**: Library now only has Grid and Immersive views
- **Click-to-explore**: Canvas now uses onCanvasClick for both debug mode and book selection

### Previous Session: Core 3D Library Fixes
- Camera starting angle: Tilted down (-0.2 rad) to see floor, bookcases, and room
- Camera position: Set at (0, floorY+1.1, 2) looking toward bookcases
- Gravity simplified: Fixed to floor level to prevent floating/jumping
- Touch panning sensitivity: Increased 3x for faster look-around
- Mobile UI cleanup: Hidden Azora button and Books panel on mobile
- Mobile joystick: Visual joystick at bottom-left for touch movement

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
- [x] Camera starting angle
- [x] Coordinate debug mode for positioning

### P1 (High Priority) - IN PROGRESS
- [ ] Use debug mode to get correct banner positions
- [ ] Fix genre banner placement with real coordinates
- [ ] Test spiral staircase climbing with new physics
- [ ] Fix mobile joystick UI obstruction

### P2 (Medium Priority)
- [ ] Re-enable interactive books on shelves
- [ ] Re-enable Azora AI librarian with correct position
- [ ] Art Studio node-based UI (React Flow)
- [ ] Stripe payment integration

### P3 (Nice to Have)
- [ ] "Call Azora Over" walking feature
- [ ] Multiplayer library exploration
- [ ] Animate still images
- [ ] Comic book layout support

## Key Files
- `/app/frontend/src/components/ImmersiveLibrary3D.jsx` - 3D library logic with debug mode
- `/app/frontend/src/pages/Library.js` - Library page (grid + immersive views only)
- `/app/backend/server.py` - All backend routes

## Technical Notes - 3D Library
- Library bounds: X: -9.5 to 9.5, Z: -9.5 to 9.5
- Floor level: Y = 4.722
- Player height: 1.1m (eye level Y: 5.82)
- Camera start: (0, 5.82, 2) facing negative Z
- Camera tilt: -0.2 radians (looking down)
- Touch sensitivity: 0.008 (panning), threshold 15px (joystick)
- Mobile UI: Joystick visible, Books panel and Azora button hidden
- **Debug Mode**: Click anywhere in 3D scene to get exact coordinates

## Stair Climbing Physics
- Multi-ray foot sensor: center, forward, forward-left, forward-right
- Max step up: 1.0m for stairs, 0.7m for regular surfaces
- Max step down: 3.0m
- Interpolation speed: 0.25 (climbing) / 0.2 (descending)

## Currently Disabled (Need Calibration via Debug Mode)
1. Genre banners - need correct bookcase positions from debug clicks
2. Azora 3D model - position needs calibration
3. Interactive book markers - need shelf position mapping
