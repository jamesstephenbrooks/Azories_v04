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
- Internal Listen button on book cover doesn't work (react-pageflip captures events) - WORKAROUND: Added external "Start Listening" button
- ~~Font size selection in Book Editor doesn't apply in reader~~ - **FIXED Feb 24, 2025**
- Collaborator system backend infrastructure - **ON HOLD per user request**

### P1 (High)
- Blank page next to front/back cover (react-pageflip showCover behavior)
- Book centering issues on cover view
- Back cover visibility at end of book

### P2 (Medium)
- Grand Library stair navigation/camera issues
- Collaborator button opens upward (UI positioning)
- Full collaboration workflow (backend stubs need implementation)

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
