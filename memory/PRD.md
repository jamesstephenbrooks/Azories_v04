# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" for children, by children.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion, Three.js for 3D, React Flow
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented

### Latest Session (Feb 21, 2026) - Art Studio Phase 2 Fixes & Character Consistency
- **Expert Mode Style Node Dropdown**
  - Changed from tabbed interface to searchable dropdown
  - Categories: Realistic, Illustration, Traditional, Digital, 3D, Fantasy, Children, Retro, Cultural, Stylized
  - 62 art styles with search functionality
  - Grouped display by category
  
- **Expert Mode Image Node Resizing Fix**
  - Fixed Reference and Output nodes - images now properly scale with node resize
  - Changed from `object-cover` to `object-contain` for proper image display
  - Added `absolute inset-0` positioning for full container coverage
  - NodeResizer component properly integrated with flex layout

- **Easy Mode Prompt History**
  - New backend endpoints: GET/POST /api/art-studio/prompt-history
  - History stored per user with deduplication (max 20 prompts)
  - "History" button appears in Additional Details for Character Builder
  - "History" button appears in Custom Scene Description for Scene Creator
  - Clicking history shows dropdown of recent prompts for quick reuse
  - Prompts auto-save on successful generation

- **ResizeObserver Error Fix**
  - Added global error handler in index.js to suppress benign ResizeObserver loop warnings

- **Art Studio Navigation**
  - Added "Art Studio" link to navbar (desktop + mobile + user dropdown)
  - Purple droplet icon for visual distinction

- **Character Consistency System (NEW)**
  - Character Profile endpoints: POST/GET /api/art-studio/character-profiles
  - Save character with name, description, traits, reference images
  - Auto-generated seed for consistency
  - "Use Profile" button to generate with saved character
  - "Save Profile" button to create new profile from current settings
  - Enhanced prompts with consistency anchors
  - Generation counter per profile

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
- [ ] **Character Consistency** - Research and implement solution for consistent character generation (Higgsfield, IP-Adapter, LoRA)
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
