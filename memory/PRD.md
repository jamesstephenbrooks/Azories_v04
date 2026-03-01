# Azories - Digital Book Platform PRD

## Original Problem Statement
User wants to enhance their "Azories" digital book application with:
- Finalized "Pro Studio" for AI content generation
- Credits-based business model with Stripe
- Professional site elements
- Library of sample books
- Bug fixes and codebase refactoring

## Core Requirements - ALL COMPLETE ✅

### P0 - Critical
- **Book Reader Experience**: Fully optimized for mobile and desktop ✅
- **AI Story Creator Page Count**: Creates exact number of pages ✅
- **AI Story Creator Images**: Portrait orientation (768x1024) ✅
- **Free Stories Trial**: New users get 3 free story creations ✅
- **BookEditor Mobile Layout**: Responsive design ✅
- **Audio Caching**: Narration cached to Cloudinary (70.5% complete) ✅
- **Newly Added Section**: Horizontal scroll row with NEW badges ✅
- **Coming Soon Section**: Blurred teasers with countdown labels ✅
- **Admin Email Notifications**: ✅ VERIFIED (March 1, 2026)
  - New user signup notifications via Resend
  - Credit purchase notifications via Resend  
  - Book submission notifications via Resend
- **Admin Panel Fixed**: ✅ (March 1, 2026)
  - `/api/admin/login` endpoint created
  - `/api/admin/verify` endpoint created
  - Admin authentication works independently from user auth
  - Admin can access panel at /admin without user login

### P1 - High Priority
- Monetization and tier gating (Stripe) ✅
- Production deployment ✅ READY

### P2 - Medium Priority
- Regenerate covers for 25 books
- Generate long-form stories for 17 books
- Refactor server.py into modular route files

## Latest Session Updates (March 1, 2026)

### P0 Fixes Completed ✅
1. **AI Book Back Cover** - Verified: AI-created books get Azories branded back cover URL
2. **Loading Screen Image** - Changed from 'waving' to 'running' pose Azora mascot
3. **Library Purple Flash Fix** - Removed motion animation from header to prevent flash

### New Features Added ✅
1. **Share Book Button** - Users can copy direct link to any book
   - Uses Web Share API on mobile, clipboard fallback on desktop
   - Toast notification: "Link copied! Share this story with friends 📚"
2. **Book Completion Celebration** - Confetti animation when child finishes a book
   - Fires when reaching back cover page
   - Uses canvas-confetti library
   - Shows "The End! Amazing job finishing this story!" message
3. **Autoplay Narration** - (Already existed) Pages auto-advance when audio ends

### Dependencies Added
- `canvas-confetti@1.9.3` - For book completion celebration

## Previous Updates (March 1, 2026)

### Site Analytics System ✅ NEW
- **Automatic page view tracking** on every route change
- **Book read tracking** when users open books
- **Signup/login event tracking**
- **Admin dashboard** shows:
  - Total users, new users (30 days)
  - Total page views, unique visitors
  - Popular books (most read)
  - AI stories created
  - Recent users list
- **API Endpoints:**
  - `POST /api/analytics/track` - Track events
  - `GET /api/admin/site-analytics` - Get analytics summary
  - `GET /api/admin/users` - Search/list all users
  - `GET /api/admin/user/{user_id}` - Get user details

### Printable PDF Feature ✅ NEW
- **Landscape A4** format (297mm x 210mm)
- Each page split into two A5 halves (left=illustration, right=text)
- Includes cover, all story pages, and branded back cover
- **5 credits** per download
- Left-aligned text, 14pt font

### Bug Fixes ✅
- **Image upload fixed** - Added Authorization header
- **Profile update fixed** - Added Authorization header  
- **Book review emails fixed** - Changed from background_tasks to await
- **Admin panel access fixed** - Removed ProtectedRoute wrapper
- **Gallery "Add to Page" fixed** - Closes modal automatically after selection

## New Features Implemented (Earlier)

### 1. Audio Caching System
- TTS audio uploads to Cloudinary CDN
- Audio URL saved to page document
- Frontend checks cached URL before calling TTS
- Background batch generation for all library books
- Admin endpoints: `/api/admin/narration-status`, `/api/admin/generate-narration-batch`
- **Status: 70.5% of library pages cached**

### 2. "Newly Added" Library Section
- Horizontal scroll row showing books from last 30 days
- "NEW" badge on books less than 7 days old
- Section hidden if no recent books
- Ordered by most recently published first
- API: `GET /api/books/newly-added`

### 3. "Coming Soon" Library Section
- Horizontal scroll row with blurred/locked thumbnails
- "Coming Soon" overlay badge with custom labels
- Clicking shows friendly message: "This story is almost ready — check back soon! 🐉"
- Section hidden if no coming soon books
- Admin can mark books via `PUT /api/books/{book_id}/coming-soon`
- API: `GET /api/books/coming-soon`

### 4. AI Story Creator Portrait Images
- fal.ai configured for portrait orientation
- Aspect ratio: 3:4 (768x1024)
- Default `image_size` changed to `portrait_4_3`

## API Endpoints Added

```
# Audio Caching
POST /api/tts/generate - Returns audio_url (Cloudinary) or audio_base64 fallback
POST /api/tts/generate-for-page/{page_id} - Generate and cache for specific page
POST /api/admin/generate-narration-batch - Batch generate narration
GET /api/admin/narration-status - Check cache status

# Library Sections
GET /api/books/newly-added - Books from last 30 days
GET /api/books/coming-soon - Books marked as coming soon
PUT /api/books/{book_id}/coming-soon - Mark book as coming soon (admin)
```

## Database Schema Updates

### books collection
- `coming_soon: boolean` - Mark book as coming soon
- `coming_soon_label: string` - Custom label (e.g., "This Week!")
- `published_at: datetime` - Publication date for newly added sorting

### pages collection
- `audio_url: string` - Cloudinary URL for cached narration

### audio_cache collection
- `cloudinary_url: string` - CDN URL for cached audio
- `cache_key: string` - Hash of text+voice
- `expires_at: datetime` - Cache expiry (365 days)

## Tech Stack
- Frontend: React with react-pageflip library
- Backend: FastAPI (Python)
- Database: MongoDB (azories)
- Image Storage: Cloudinary
- Audio Storage: Cloudinary (NEW)
- AI: fal.ai (images), OpenAI TTS (narration)
- Payments: Stripe

## Test Credentials
- Admin App: jamesstephenbrooks@outlook.com / Routetofreedom
- Admin Panel: Username: Admin / Password: Routetofreedom

## Deployment Checklist ✅
- [x] AI Story Creator page count working
- [x] Portrait image orientation configured
- [x] Audio caching implemented (70.5%+ cached)
- [x] Newly Added section showing 20 books
- [x] Coming Soon section with blurred teasers
- [x] All API endpoints tested
- [x] Frontend lint passed
- [x] Backend running without errors
- [x] Admin email notifications tested (March 1, 2026)
  - User signup: ✅ Verified (Resend email ID received)
  - Credit purchase: ✅ Verified (Resend email ID received)
  - Book submission: ✅ Verified (Resend email ID received)

## Ready for Production Deployment ✅

## Printable Book PDF Feature (March 1, 2026) ✅

### Overview
Users can download a printable A5 booklet PDF of their books for **5 credits**.

### Layout Design
- **A4 page split into two A5 halves**:
  - Left half: Full illustration
  - Right half: Story text (centered, word-wrapped)
- When printed double-sided and folded = real A5 picture book

### Pages Included
1. **Front Cover**: Cover illustration (left), Title/Author/Branding (right)
2. **Content Pages**: Each page has illustration (left) and text (right)
3. **Back Cover**: Branded back cover image (left), "The End" with description (right)

### API Endpoint
```
GET /api/books/{book_id}/print-pdf
- Requires authentication
- Returns PDF with Content-Disposition: attachment
- Cost: 5 credits (VIP/Admin exempt)
- Returns 402 if insufficient credits
```

### Frontend UI
- **Print Button**: FiPrinter icon in BookReader header (visible when logged in)
- **Print Dialog Modal**: Shows cost (5 credits), features list, Cancel/Download buttons
- **Data test IDs**: `print-book-btn`, `confirm-print-btn`

### Credit Usage
- Regular users: 5 credits deducted per download
- VIP users: Free (usage tracked in `vip_usage` collection)
- Admin users: Free

## Email Notification System
- **Provider**: Resend (primary), Brevo (fallback)
- **Admin Notification Email**: books@azories.com (configurable via ADMIN_NOTIFY_EMAIL)
- **Events Covered**:
  1. New user registration → admin notified with user details
  2. Successful Stripe credit purchase → admin notified with purchase details
  3. Book submission for review → admin notified with moderation results
- **Rate Limit**: Resend allows 2 requests/second (sufficient for production usage)
