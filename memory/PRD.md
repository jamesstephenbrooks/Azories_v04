# Azories - Digital Book Creation Platform PRD

## Original Problem Statement
Create a digital book creating and reading web application called "Azories" (azories.com). This is for children, by children to start with.

## Architecture
- **Frontend**: React with Tailwind CSS, Framer Motion animations
- **Backend**: FastAPI with MongoDB
- **AI Integrations**: Emergent Universal Key (OpenAI GPT Image 1, Sora 2 Video, GPT-4o)
- **Auth**: JWT-based + Separate Admin Auth

## What's Been Implemented (February 2026)

### Latest Updates (Feb 20, 2026) - Session 7: User Experience Improvements
- **Onboarding Tutorial**: 4-step guided tutorial for new users
  - Welcome to Azories (features overview)
  - Explore the Library (browse/search/3D view)
  - Immersive Reading (auto-read, ambient sounds)
  - Create Your Stories (Pro features, AI tools)
  - Progress dots, skip option, animated transitions
- **Reading Streaks & Badges System**: Gamification to encourage reading
  - Daily reading streak tracking (3, 7, 30 day badges)
  - Achievement badges: First Book, Bookworm, Night Owl, Early Bird, Genre Explorer, Creator, Supporter
  - New badge popup with confetti animation
  - Backend endpoints: `/api/user/reading-stats`, `/api/user/record-reading`
- **Book Recommendations**: Personalized suggestions
  - Based on genres user has read
  - Fallback to popular books
  - Backend endpoint: `/api/user/recommendations`
- **Animated Book Cards**: Hover effects, shimmer, floating particles
- **Improved Theme Toggle**: Animated sun/moon toggle with smooth transitions
- **Ambient Sounds Fixed**: Changed to Pixabay audio sources (more reliable CORS support)

### Previous: Session 6 (Feb 20, 2026) - 3D GLB Library Integration
- **3D Gothic Library with User's GLB Model**: Successfully integrated the user's purchased 50MB GLB model
  - Fixed CORS issues by implementing backend proxy endpoint `/api/proxy/glb`
  - Added proper Content-Length header for accurate loading progress display
  - Loading progress now shows correctly (0% → 100%)
  - Gothic library renders with wooden floors, stone pillars, and decorative elements
  - OrbitControls for drag to rotate, scroll to zoom, right-click to pan
  - Library collection panel shows books at the bottom
  - Fullscreen mode supported
  - Ambient fireplace audio plays on user interaction
- **Verified Ambient Sound Popup Fix**: Confirmed the popup now displays correctly on-screen

### Latest Updates (Feb 18, 2026) - Session 5: Immersive Library
- **Fixed Ambient Sound Dropdown**: Changed popup to open downward (top-full) instead of upward to prevent off-screen rendering
- **Immersive 3D Library (CSS Fallback)**: Created CSS 3D library experience as fallback with:
  - Starry night sky background with animated stars
  - Chandelier with glowing candles
  - 8 bookshelves arranged in a circular pattern
  - Colorful books that can be clicked to read
  - Gothic pillars in the corners
  - Floating magic orbs with glow effects
  - Drag to rotate, arrow buttons for navigation
  - Ambient fireplace audio
  - Book preview modal when clicking books

### Latest Updates (Feb 18, 2026) - Session 4: Best Reading App Vision
- **Analytics Dashboard**: Added tabbed view in Dashboard with "My Books" and "Analytics" tabs
  - Total Views, Total Reads, Published Books, Avg Reads/Book stats cards
  - Book Performance table with Status, Views, Reads, Actions
  - Per-book detailed analytics modal with daily reads chart
- **User Profile System**: Full social profiles at `/profile` and `/profile/:userId`
  - Avatar (initials-based), display name, bio, location, website, twitter
  - Stats: Followers, Following, Books, Total Reads
  - Achievement badges (Pro Creator, Prolific Author, Rising Star)
  - Published books gallery with empty state
  - Edit Profile dialog with all profile fields
- **Ambient Sound System**: Immersive reading with background sounds
  - 8 ambient sounds: Rain, Fireplace, Forest, Ocean, Café, Night, Wind, Library
  - Genre-based recommendations (Fantasy → Fireplace/Forest, Mystery → Rain/Night)
  - Volume control and play/stop functionality
- **Social Features Backend**:
  - User profiles API (GET /api/users/{id}/profile, PUT /api/users/profile)
  - Follow/Unfollow system (/api/users/{id}/follow)
  - Followers/Following lists
  - Book reviews with ratings (1-5 stars) and average rating calculation
- **Navigation**: Profile link added to Navbar user dropdown

### Latest Updates (Feb 18, 2026) - Session 3
- **Auto-Read Continuous Playback Fix**: Fixed critical bug where audiobook would stop at chapter title pages
  - Added refs (autoReadRef, currentPageRef) to avoid stale closure issues in setTimeout callbacks
  - Chapter title pages now properly auto-advance after 2.5 seconds
  - Audio playback correctly advances to next page on completion
  - Fixed race condition with auth token on direct URL navigation
- **Code Quality**: Improved BookReader.js with proper ref usage for async callbacks

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
- [x] 3D Library (CSS fallback + GLB model integration Feb 20, 2026)
- [x] Auto-save
- [x] Summary preview popup on book cards
- [x] Auto-read continuous playback through chapters (fixed Feb 18, 2026)
- [x] Analytics Dashboard for creators (Feb 18, 2026)
- [x] User Profile system with social features (Feb 18, 2026)
- [x] Ambient reading sounds (Feb 18, 2026)
- [x] Immersive 3D Gothic Library with GLB model (Feb 20, 2026)

### P1 (High Priority)
- [ ] Stripe payment integration
- [ ] Realistic page-turning animation (BookReaderV2)
- [x] Interactive PDF download (working)
- [x] Loading bars for image/video uploads (working)
- [x] Social features - follow/unfollow, reviews (Feb 18, 2026)

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
- `/api/proxy/glb` - Proxy for CORS-bypassing GLB 3D model files
- `/api/users/{id}/profile` - User profile (GET/PUT)
- `/api/users/{id}/follow` - Follow/unfollow user
