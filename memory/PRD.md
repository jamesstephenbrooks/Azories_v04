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
- **AI Integrations**: OpenAI GPT Image 1, Sora 2 Video, ElevenLabs TTS
- **Auth**: JWT-based authentication

## Core Requirements (Static)
- [x] User authentication (register/login)
- [x] Free vs Pro subscription model
- [x] Book CRUD operations
- [x] Chapter and page management
- [x] AI image generation
- [x] AI video generation (Sora 2)
- [x] Text-to-speech with multiple voices
- [x] Library with search/filter
- [x] Featured/Best of Week sections
- [x] Cover editor (front/back)
- [x] Comic book mode (multiple panels)
- [x] Video upload
- [x] Dark/Light theme toggle

## What's Been Implemented (January 2026)

### Backend (100% Working)
- JWT Authentication with subscription levels
- Books, Chapters, Pages CRUD
- AI Image Generation endpoint (OpenAI GPT Image 1)
- AI Video Generation endpoint (Sora 2)
- TTS with ElevenLabs (9 fallback voices)
- File upload (image/video)
- Admin CMS (featured, best of week toggles)
- Genres API

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
  - Scrollable visual panel
- Library with tabs (All, Featured, Best of Week)
- Book Reader with page turning

## Known Issues
- AI Image/Video generation requires valid OpenAI API key with billing
- ElevenLabs API key needs `voices_read` permission for live voice list (fallback voices work)

## Prioritized Backlog

### P0 (Critical)
- [x] Core reading experience
- [x] Core creation experience
- [x] Authentication

### P1 (High Priority)
- [ ] Payment integration (Stripe) for Pro subscription
- [ ] 3D animated book library visualization
- [ ] Page turning animation in reader
- [ ] AI story continuation/enhancement

### P2 (Medium Priority)
- [ ] Template system for quick book creation
- [ ] Collaborative book editing
- [ ] Book sharing/embedding
- [ ] Audio book player controls
- [ ] Vector logo download

### P3 (Nice to Have)
- [ ] User profiles and following
- [ ] Book reviews/ratings
- [ ] Reading statistics
- [ ] Gamification (badges)

## Next Action Items
1. Add payment integration for Pro subscriptions
2. Implement 3D book visualization in library
3. Enhance page turning animation in reader
4. Add AI story continuation feature
5. Create downloadable vector logo
6. Improve audiobook player experience
