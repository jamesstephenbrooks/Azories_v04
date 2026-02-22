# Azories - Digital Book Creation and Reading Platform

## Original Problem Statement
Build a digital book creation and reading application named "Azories" with features including:
- Book reader with audio narration (TTS)
- Book editor ("Edit My Books")
- Series manager ("My Series")
- AI librarian ("Azora")
- 3D library environment
- Art Studio for generating assets

## What's Been Implemented

### Core Features (Completed)
- Full-stack React/FastAPI/MongoDB application
- Book reading experience with page flip animations (react-pageflip)
- Text-to-Speech using OpenAI TTS (via Emergent LLM Key)
- Audio pre-caching for smoother playback between pages
- Book editor with font/style customization
- Chapter management
- User authentication
- Reading progress tracking

### Recent Fixes (Feb 22, 2025)
1. **Listen Button on Cover** - Added "Start Listening" button outside the book cover that reliably starts audio narration (internal Listen button had event capture issues with react-pageflip)
2. **Auto-Read Flow** - Fixed state synchronization issues between `autoReadRef` and `autoRead` state that prevented audio from playing
3. **Audio Caching** - Implemented `audioCache` Map to pre-load audio for upcoming pages and avoid regenerating TTS
4. **Faster Transitions** - Reduced delays between pages (500ms -> 200ms) for smoother auto-read experience
5. **Collaboration API** - Fixed URL mismatch for collaboration endpoints

### Recent Fixes (Feb 24, 2025)
1. **Font Size Bug Fixed** - Font size selected in Book Editor was not applying in the Book Reader. Root cause: The `get_full_book` API endpoint was missing `setdefault()` calls for `font_size`, `font_family`, and `text_align` fields. When pages in MongoDB didn't have these fields, the frontend received `undefined` values. Fixed by adding defaults in three places in server.py:
   - `get_full_book()` endpoint (line ~2815)
   - `get_pages()` endpoint (line ~1499)
   - `update_page()` endpoint (line ~1522)

2. **fal.ai Integration for Character Consistency (Pro Studio)** - Integrated fal.ai API for true face/character consistency:
   - **FLUX.1 Dev** - Fast, high-quality text-to-image generation
   - **FLUX Pro** - Premium quality generation
   - **FLUX PuLID** - Face/identity preservation using reference images
   - **FLUX LoRA** - Generate with trained character models
   - **Portrait LoRA Trainer** - Train custom LoRA for 100% consistent characters
   
   New API endpoints:
   - `GET /api/fal/models` - List available fal.ai models
   - `POST /api/fal/generate` - Generate images with FLUX
   - `POST /api/fal/generate-with-face` - Generate with face ID preservation (PuLID)
   - `POST /api/fal/train-lora` - Start LoRA training for a character
   - `GET /api/fal/training-status/{job_id}` - Check LoRA training progress
   - `POST /api/fal/generate-with-lora` - Generate with trained LoRA
   - `POST /api/pro-studio/characters/train-consistency` - Train LoRA for existing character
   - `POST /api/pro-studio/characters/{id}/generate-consistent` - Smart generation using best available method

3. **Credits System** - Added credits for Pro Studio features:
   - Credit costs: FLUX generate (1), FLUX Pro (2), PuLID (3), LoRA training (50), LoRA generate (2), Video (10)
   - Endpoints: `GET /api/credits/balance`, `POST /api/credits/add`
   - UI: Credits display in Pro Studio header with add button

4. **Bug Fixes:**
   - Fixed duplicate images when uploading to character creator
   - Fixed character creation with URL images (now downloads and analyzes)
   - Fixed token key mismatch in Pro Studio (`token` -> `azories-token`)
   - Fixed gallery integration (now loads from Art Studio gallery)

### Latest Updates (Feb 22, 2026)

1. **fal.ai API Key Updated** - Fixed invalid API key that was blocking image generation

2. **Unified Character Creation Form** - Replaced tabbed interface with unified form:
   - Description AND reference images can be provided together (not either/or)
   - More intuitive workflow for creating characters

3. **Character Folder/Portfolio System** - Each character now has a dedicated folder:
   - New endpoints: `GET/POST /api/pro-studio/characters/{id}/gallery`
   - Generated images auto-save to character's folder
   - View all images for a character in one place
   - Click to preview images in full-size modal

4. **Larger Image Preview Modal** - Click any image for full-size view with:
   - Download button
   - Save to gallery option
   - Character/prompt info display

5. **Genre Options Added** - Added "Futuristic" and "Sci-Fi" genres as requested

6. **Character View Modal** - Click character thumbnail or folder icon to see:
   - Full character description
   - Reference images gallery
   - Generated images folder
   - "Use for Generation" quick action

## Architecture

### Frontend (/app/frontend)
- React with Tailwind CSS
- react-pageflip for book animations
- Axios for API calls
- Key files:
  - `/pages/BookReader.js` - Main reader component
  - `/components/RealisticPageFlip.jsx` - Page flip component
  - `/pages/BookEditor.js` - Book editing
  - `/components/CollaborativeWriting.jsx` - Collaboration features

### Backend (/app/backend)
- FastAPI
- MongoDB via MONGO_URL
- OpenAI TTS integration
- Key file: `server.py`

### Environment
- Frontend: REACT_APP_BACKEND_URL
- Backend: MONGO_URL, DB_NAME, EMERGENT_LLM_KEY

## Known Issues / Pending

### P0 (Critical)
- ~~Font size selection in Book Editor doesn't apply in reader~~ - **FIXED Feb 24, 2025**
- ~~fal.ai API key invalid~~ - **FIXED Feb 22, 2026**

### P1 (High)
- Re-enable credits system (currently disabled for testing)
- LoRA training endpoint (stubbed, needs full implementation)
- Character Portfolio persistence across sessions
- Back cover visibility at end of book

### P2 (Medium)
- Grand Library stair navigation/camera issues
- Full collaboration workflow (backend stubs need implementation)
- iPad/iPhone UI layout fixes
- "Read Aloud" button error on iPad

## Upcoming Tasks
1. Grand Library - Fix camera/stair collision
2. Collaborators popup positioning
3. Full collaboration workflow implementation
4. Azora AI testing
5. Art Studio features
6. iPad/iPhone UI fixes

## Backlog
- Art Studio "dramatic" mode
- Scene thumbnails
- Character consistency system (Pro Studio)
- iPad read-only mode

## 3rd Party Integrations
- OpenAI TTS (via Emergent LLM Key)
- OpenAI GPT-4o (via Emergent LLM Key)
- react-pageflip (book animations)
- reactflow (Art Studio)
