# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with. Features include:
- Reader side: 3D library with floating books, search, read or listen (audiobook), full-screen book view with page turning animation
- Creator side: AI-powered creation tool with text/image/video generation, multiple narrator voices
- Free vs Pro subscription model
- Comic book mode for multiple images per page
- Cover editor for front and back covers

## User Personas
1. **Reader (Free User)**: Children who want to read/listen to stories
2. **Creator (Pro User)**: Young authors who create their own books with AI tools
3. **Admin (Az)**: Platform owner managing featured books

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key for OpenAI GPT Image 1, Sora 2 Video, GPT-4o (text), ElevenLabs TTS
- **Auth**: JWT-based authentication

## Core Requirements (Static)
- [x] User authentication (register/login)
- [x] Free vs Pro subscription model
- [x] Book CRUD operations
- [x] Chapter and page management
- [x] AI image generation (Emergent LLM Key)
- [x] AI video generation (Sora 2 via Emergent LLM Key)
- [x] AI text generation for stories/summaries (GPT-4o via Emergent LLM Key)
- [x] Text-to-speech with multiple voices (ElevenLabs)
- [x] Library with search/filter
- [x] Featured/Best of Week sections
- [x] Cover editor (front/back)
- [x] Comic book mode (multiple panels)
- [x] Video upload
- [x] Dark/Light theme toggle

## What's Been Implemented

### December 2026 Updates
- **Switched to Emergent Universal Key** - Resolved OpenAI billing limit issues
- **3D CSS Bookshelf** - Interactive library view with drag-to-rotate bookcase
- **Chapter Title Pages** - Dedicated chapter intro pages in book reader
- **View Mode Toggle** - Grid/3D view switch in library

### Backend (100% Working)
- JWT Authentication with subscription levels
- Books, Chapters, Pages CRUD
- AI Image Generation (GPT Image 1 via Emergent Key)
- AI Video Generation (Sora 2 via Emergent Key)
- AI Story Generation (GPT-4o via Emergent Key)
- AI Summary Generation (GPT-4o-mini via Emergent Key)
- TTS with ElevenLabs (20 narrator voices)
- File upload (image/video)
- Admin CMS (featured, best of week toggles)
- Book analytics (views, reads)

### Frontend
- Landing page with Azories branding
- Auth page (login/register)
- Dashboard with subscription management
- Book Editor with:
  - Cover editor (front/back)
  - Chapter/page management
  - AI image generation (3 styles)
  - AI video generation
  - Video upload
  - Comic book mode (2, 3, 4 panels)
  - Narrator voice selection
  - AI summary generation
- Library with tabs (All, Featured, Best of Week)
  - Grid view with hover effects
  - 3D Bookshelf view (CSS-based)
  - Search and genre filtering
- Book Reader with:
  - Dual-page layout
  - Chapter title pages
  - Auto-read with auto-page-turn
  - Playback speed control
  - Volume control

## Known Working Integrations
- **Emergent Universal Key**: All AI features (text, image, video)
- **ElevenLabs**: Text-to-speech (20 voices available)

## Prioritized Backlog

### P0 (Critical) - COMPLETED
- [x] Core reading experience
- [x] Core creation experience
- [x] Authentication
- [x] AI generation with working key

### P1 (High Priority)
- [ ] Payment integration (Stripe) for Pro subscription
- [x] 3D animated book library visualization
- [ ] Page turning animation enhancement
- [ ] AI story generator from idea

### P2 (Medium Priority)
- [ ] Admin CMS full UI
- [ ] Book analytics dashboard for creators
- [ ] Public book view (cover/summary only for non-auth)
- [ ] Vector logo creation for Azories branding
- [ ] More narrator voice options

### P3 (Nice to Have)
- [ ] Animate still images feature
- [ ] Comic book multi-layout options
- [ ] User profiles and following
- [ ] Book reviews/ratings

## Next Action Items
1. Complete Admin CMS panel UI
2. Add book analytics display on creator dashboard
3. Implement Stripe for Pro subscriptions
4. Create Azories vector logo
5. Add public book preview mode
