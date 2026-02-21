# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" for children, by children.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion, Three.js for 3D, React Flow
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented

### Latest Session (Feb 21, 2026) - Art Studio Enhancements & Fixes

**Part 1: Art Studio Fixes**
- **Expert Mode Style Node Dropdown** - Changed from tabs to searchable dropdown
- **Expert Mode Image Node Resizing** - Fixed CSS for proper image scaling
- **Easy Mode Prompt History** - Added history endpoints and UI
- **ResizeObserver Error Fix** - Comprehensive error suppression in index.js
- **Art Studio Navigation** - Added to navbar (desktop, mobile, dropdown)

**Part 2: Character Consistency System**
- Character Profile endpoints: POST/GET `/api/art-studio/character-profiles`
- Save characters with traits, reference images, and auto-generated seed
- "Use Profile" and "Save Profile" buttons in Character Builder

**Part 3: 3D Library Improvements**
- Removed "Books" panel from bottom-right corner
- Moved book popup to **center of screen** with backdrop
- Enhanced spiral staircase climbing physics

**Part 4: Additional Enhancements**
- **More Scene Presets** (24 total): Added Dreamscape, Sunset Cliffs, Aurora, Cherry Blossom, Ruins, Throne Room, Tavern, Garden, Desert, Crystal Cave, Floating Islands, Moonlit Lake, Battlefield, Village, Ship Deck, Magic Academy
- **New Art Styles**: Added "Ethereal Fantasy" and "Surreal Dreamscape" styles (matching user's reference image)
- **Prompt History Scroll** - Moved under Reference Image section with custom scrollbar
- **Copy to Expert Mode** - Button to transfer character data from Easy Mode to Node Editor
- **Expert Mode Fixes** - Added better error handling and logging

### Previous Session (Feb 21, 2026) - Art Studio Enhancement
- **Phase 1: Easy Mode Art Studio Enhancements**
  - Art style example images with preview thumbnails (62 styles total)
  - Book assignment dropdown (assign images to specific books or General Library)
  - Reference image upload option
  - "Use from Gallery" to reuse previously generated images as references
  - Download button for generated images
  - "Use as Reference" button after generation
  - Gallery picker modal

- **Phase 2: Expert Node-Based Studio**
  - New route: `/art-studio/expert`
  - React Flow-based visual workflow editor
  - Node types: Character, Scene, Style, Reference, Prompt, Combine, Output
  - Visual node connections with animated edges
  - Save/Load workflow functionality
  - Run workflow to generate images
  - Minimap and zoom controls
  - Resizable nodes for Character, Scene, Reference, Output
  - PRO feature badge

### Previous Session - 3D Grand Library
- **Coordinate Debug Mode**: Click in 3D to get exact (x, y, z) positions
- **Genre Banners**: Fiction, Adventure, Fantasy, Comic, Science Fiction with calibrated positions
- **"Click to browse" hints**: Below each banner pointing up
- **Interactive Book Selection**: 
  - Click banner → genre book list panel appears on left
  - Select book → animated GLB book appears in front of camera
  - Book info panel on right with cover, title, summary, Read button
  - Genre panel stays open for quick book switching
  - Selected book highlighted in list
- **3D Grand Library Button**: Fancy gradient text, marked for Pro feature
- **Removed simple 3D view**: Only grid + immersive views
- **Removed book rotation feature**: Was causing purple screen issues
- **Camera controls**: 80° left rotation on start, drag to look

### Core Features (Previous Sessions)
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
- **Art Studio Test**: artstudio3@test.com / password123 (Pro)

## Prioritized Backlog

### P0 (Critical) - COMPLETED
- [x] Core reading/creation experience
- [x] Authentication
- [x] AI generation (image + video)
- [x] Admin CMS
- [x] 3D Library with GLB model
- [x] Genre banners with book selection
- [x] Interactive 3D book display

### P1 (High Priority) - NEXT
- [x] ~~**Character Consistency**~~ - Implemented Character Profile system with seeds and enhanced prompts
- [ ] **Spiral Staircase Navigation** - Fix 3D library so player can climb stairs
- [ ] Creation history view for each book (show how images were generated)
- [ ] Improve book/image creation experience
- [ ] AI image generation quality/speed
- [ ] Story editor enhancements
- [ ] Cover creation tools

### P2 (Medium Priority) - LATER
- [ ] Mobile joystick UI fix verification
- [ ] Add more genre banners (Mystery, Humour)
- [ ] Make 3D Library Pro-only feature
- [x] ~~Art Studio node-based UI~~ (COMPLETED)
- [ ] Expert Mode as separate paid tier

### P3 (Nice to Have)
- [ ] Re-integrate Azora AI librarian
- [ ] Multiplayer library exploration
- [ ] Animate still images
- [ ] Comic book layout support

## Key Files
- `/app/frontend/src/components/ImmersiveLibrary3D.jsx` - 3D library with debug mode, genre banners, book selection
- `/app/frontend/src/pages/Library.js` - Library page (grid + immersive views)
- `/app/frontend/public/animated_book.glb` - Animated book model
- `/app/backend/server.py` - All backend routes

## Technical Notes - 3D Library
- Library bounds: X: -9.5 to 9.5, Z: -9.5 to 9.5
- Floor level: Y = 4.722
- Player height: 1.1m
- Camera start: Rotated 80° left
- Book display: 0.8 units in front of camera, Y-0.35 from eye level, scale 0.08
- Genre banners: Calibrated positions with shelfPos for each

## Genre Sections (Calibrated)
- Fiction: X:-4.79, Y:6.5, Z:-1.35
- Adventure: X:-5.0, Y:6.5, Z:0.42
- Fantasy: X:-1.01, Y:5.7, Z:-7.5
- Comic: X:-2.5, Y:5.7, Z:-6.5
- Science Fiction: X:-5.5, Y:6.5, Z:-1.29
- Mystery: Uncalibrated
- Humour: Uncalibrated

## Currently Disabled
- Azora AI librarian - needs position calibration
- Book rotation feature - was causing issues
- Auto-loading featured books - simplified
