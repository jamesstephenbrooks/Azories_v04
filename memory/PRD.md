# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented (February 2026)

### Latest Updates (Feb 17, 2026) - Session 2
- **Book Series Management**: Create and manage book series in My Books
  - Manage Series button in header
  - Create series with name and description
  - Expandable series view showing books with order numbers and thumbnails
  - Add books to series from within expanded series view
  - Remove books from series
  - Series badge displays on book cards
- **My Books Search Bar**: Filter books by title, description, or genre
- **Enhanced Book Reader**:
  - Auto-Read ON by default
  - Narrator voice dropdown in bottom controls (22+ voices)
  - Larger book display in fullscreen mode (95vw × 85vh)
  - Exit fullscreen button always visible
  - Auto-advances through chapter title pages (2.5s)
- **AI Story Creator Enhanced**:
  - Visual Media options (Images, Videos, Cinemagraphs, None)
  - 10 image styles (Illustration, Comic, Realistic, Sci-Fi, Sketch, Watercolor, Anime, Fantasy, Pixar, Storybook)
  - 8 video styles for Sora AI

### Session 1 Updates (Feb 17, 2026)
- **Summary Preview Popup**: Info icon on book cards in Library
- **Admin CMS Button Removed**: From Dashboard (still at /admin)
- **Video Generation Fix**: Size parameter fixed

### Previous Updates
- Play Button Fix: Continues through all chapters
- Single-Page Front Cover with hover overlay
- Generate All AI Images: Batch generation
- Auto-Save: 2-second debounce
- Harry Potter Style Library (3D immersive)
- Enhanced Fullscreen mode
- Multiple AI styles (Sci-Fi, etc.)

### Admin CMS
- **URL**: /admin
- **Credentials**: azories_admin / AzoriesAdmin2024!
- Features: Dashboard stats, book management, user list, analytics

### Backend Features
- JWT Authentication (Free/Pro tiers)
- Books, Chapters, Pages CRUD
- **Book Series CRUD** (create, list, add/remove books)
- Book Download (JSON export)
- AI Image Generation (10 styles)
- AI Video Generation (8 styles) - Valid sizes: 1280x720, 1792x1024, 1024x1792, 1024x1024
- Batch Image Generation
- AI Story Generation with media options
- AI Summary Generation
- Text-to-Speech (ElevenLabs, 22+ voices)
- File uploads (image/video)
- Admin CMS with separate auth

### Frontend Features
- Landing page
- Auth (login/register)
- Dashboard with subscription management
- **My Books with Search Bar**
- **Series Management Dialog** (expandable view)
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
  - **Summary Preview Popup** on book cards (hover for info icon, click to view summary)
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
- **Test User**: testuser2@example.com / TestPass123! (Pro)

## Prioritized Backlog

### P0 (Critical) - COMPLETED
- [x] Core reading/creation experience
- [x] Authentication
- [x] AI generation (image + video)
- [x] Admin CMS
- [x] 3D Library
- [x] Auto-save
- [x] Summary preview popup on book cards
- [x] Auto-read continuous playback through chapters (fixed Feb 18, 2026)

### P1 (High Priority)
- [ ] Stripe payment integration
- [ ] Realistic page-turning animation (BookReaderV2)
- [x] Interactive PDF download (working)
- [x] Loading bars for image/video uploads (working)

### P2 (Medium Priority)
- [ ] Book analytics dashboard for creators
- [ ] Playback speed control for audiobook
- [ ] Animated image options during AI book creation
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
