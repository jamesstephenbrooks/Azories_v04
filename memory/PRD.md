# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented (December 2026)

### Latest Updates
- **Play Button Fix**: Starts from cover page, continues through all chapters
- **Single-Page Front Cover**: With hover overlay showing "Click to Start Reading"
- **Generate All AI Images**: Batch generate images for entire book
- **Generate Images from Text**: AI creates images based on page content
- **Auto-Save**: 2-second debounce in book editor (silent save)
- **Harry Potter Style Library**: Immersive dark library room with:
  - Auto-rotating camera view
  - Wooden bookshelves on all sides
  - Candlelight ambient effects
  - Ornate pillars and decorations
  - Book selection with hover effects
- **Enhanced Fullscreen**: Dark background, scaled-up book view
- **Sci-Fi Style**: Added for AI image/video generation

### Admin CMS
- **URL**: /admin
- **Credentials**: azories_admin / AzoriesAdmin2024!
- Features: Dashboard stats, book management, user list, analytics

### Backend Features
- JWT Authentication (Free/Pro tiers)
- Books, Chapters, Pages CRUD
- Book Download (JSON export for creators)
- AI Image Generation (4 styles: illustration, comic, realistic, sci-fi)
- AI Video Generation (Sora 2, 4 styles)
- Batch Image Generation (generate-all-images, generate-images-from-text)
- AI Story Generation from idea
- AI Summary Generation
- Text-to-Speech (ElevenLabs, 20+ voices)
- File uploads (image/video)
- Admin CMS with separate auth
- Test book seeding

### Frontend Features
- Landing page
- Auth (login/register)
- Dashboard with subscription management
- Book Editor:
  - Auto-save (2-second debounce)
  - Download button
  - AI Images dropdown (batch generation)
  - Cover editor
  - Comic book mode
  - Narrator voice selection
- Library:
  - Grid view
  - 3D Harry Potter style library (auto-rotate, candlelight)
  - Search/filter
- Book Reader:
  - Single-page front cover with play overlay
  - Enhanced page turning animation
  - Chapter title pages
  - Auto-read with page turning
  - Improved fullscreen mode (dark bg, scaled book)
  - Volume and speed controls

## Test Credentials
- **Admin**: azories_admin / AzoriesAdmin2024!
- **Test Author**: testauthor@azories.com / TestAuthor123! (Pro)

## Prioritized Backlog

### P0 (Critical) - COMPLETED
- [x] Core reading/creation experience
- [x] Authentication
- [x] AI generation
- [x] Admin CMS
- [x] 3D Library
- [x] Auto-save

### P1 (High Priority)
- [ ] Stripe payment integration
- [ ] AI story generator from single idea (full implementation)

### P2 (Medium Priority)
- [ ] Book analytics dashboard for creators
- [ ] Public book preview (cover only)
- [ ] Azories vector logo

### P3 (Nice to Have)
- [ ] Animate still images
- [ ] Comic book advanced layouts
- [ ] User profiles and following
- [ ] Book reviews/ratings

## API Endpoints
- `/api/auth/*` - Authentication
- `/api/books/*` - Book CRUD
- `/api/books/{id}/download` - Download book as JSON
- `/api/ai/generate-image` - Single image generation
- `/api/ai/generate-video` - Video generation
- `/api/ai/generate-all-images` - Batch generate images
- `/api/ai/generate-images-from-text` - Generate from text content
- `/api/ai/generate-story` - Generate full story
- `/api/ai/generate-summary` - Generate back cover summary
- `/api/admin/*` - Admin CMS (separate auth)
