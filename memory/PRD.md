# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with. Features include:
- Reader side: 3D library with floating books, search, read or listen (audiobook), full-screen book view with page turning animation
- Creator side: AI-powered creation tool with text/image/video generation, multiple narrator voices
- Free vs Pro subscription model
- Comic book mode for multiple images per page
- Cover editor for front and back covers
- Admin CMS for content management

## User Personas
1. **Reader (Free User)**: Children who want to read/listen to stories
2. **Creator (Pro User)**: Young authors who create their own books with AI tools
3. **Admin**: Platform owner managing featured books, users, content moderation

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key for OpenAI GPT Image 1, Sora 2 Video, GPT-4o (text), ElevenLabs TTS
- **Auth**: JWT-based authentication (separate admin auth)

## What's Been Implemented

### December 2026 - Latest Updates
- **Book Download Feature**: Creators can download their books as JSON files
- **Sci-Fi Style**: Added to AI image and video generation options
- **Separate Admin CMS**: Full admin panel at /admin with its own authentication
- **Test Books Seeded**: 12 sample books across various genres
- **Improved 3D Bookshelf**: CSS-based with realistic wooden bookcase, drag-to-rotate
- **Enhanced Page Turning**: More realistic 3D page flip animation

### Admin CMS (at /admin)
- Separate admin login (username: azories_admin, password: AzoriesAdmin2024!)
- Dashboard with platform statistics
- Book management (publish, feature, best-of-week, delete)
- User list with subscription status
- Platform analytics with top books

### Backend (100% Working)
- JWT Authentication with subscription levels
- Books, Chapters, Pages CRUD
- Book Download endpoint (/api/books/{id}/download)
- AI Image Generation with 4 styles (illustration, comic, realistic, sci-fi)
- AI Video Generation with 4 styles (animation, comic, realistic, sci-fi)
- AI Story Generation (GPT-4o via Emergent Key)
- AI Summary Generation (GPT-4o-mini via Emergent Key)
- TTS with ElevenLabs (20 narrator voices)
- File upload (image/video)
- Separate Admin Auth System
- Admin CMS endpoints (books, users, analytics, toggles)
- Test data seeding endpoint

### Frontend
- Landing page with Azories branding
- Auth page (login/register)
- Dashboard with subscription management
- Book Editor with:
  - Download button for creators
  - Cover editor (front/back)
  - Chapter/page management
  - AI image generation (4 styles including Sci-Fi)
  - AI video generation (4 styles including Sci-Fi)
  - Video upload
  - Comic book mode (2, 3, 4 panels)
  - Narrator voice selection
  - AI summary generation
- Library with tabs (All, Featured, Best of Week)
  - Grid view with hover effects
  - 3D Bookshelf view (CSS-based with wooden bookcase)
  - Search and genre filtering
- Book Reader with:
  - Dual-page layout
  - Chapter title pages
  - Enhanced 3D page turning animation
  - Auto-read with auto-page-turn
  - Playback speed control
  - Volume control
- Admin CMS (/admin):
  - Separate admin login
  - Stats dashboard
  - Book management table
  - User list
  - Analytics view

## Test Credentials
- **Admin**: username=azories_admin, password=AzoriesAdmin2024!
- **Test Author**: email=testauthor@azories.com, password=TestAuthor123! (Pro user)

## Prioritized Backlog

### P0 (Critical) - COMPLETED
- [x] Core reading experience
- [x] Core creation experience  
- [x] Authentication
- [x] AI generation with working key
- [x] Admin CMS with separate auth

### P1 (High Priority)
- [ ] Payment integration (Stripe) for Pro subscription
- [x] 3D animated book library visualization
- [x] Book download for creators
- [ ] AI story generator from single idea

### P2 (Medium Priority)
- [x] Sci-fi style for AI generation
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
1. Implement Stripe for Pro subscriptions
2. Add book analytics display on creator dashboard
3. Create AI story generator from single idea
4. Create Azories vector logo
5. Add public book preview mode
