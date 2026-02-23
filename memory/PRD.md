# Azories - Digital Book Platform

## Original Problem Statement
Build a full-featured digital book platform ("Azories") with:
- Free "Art Studio" for basic AI image generation
- Credit-based "Pro Studio" with advanced AI capabilities (PuLID, LoRA, Kling, Sora 2)
- Stripe integration for payments (GBP currency: £5, £18, £30, £120)
- VIP user management (exempt from credit deductions)
- Admin analytics dashboard
- Book creation and reading experience
- Voice narration (speech-to-text via Whisper)
- Email notifications (Resend integration)

## User Personas
- **Authors**: Create illustrated digital books with AI-generated imagery
- **Readers**: Discover and read books in immersive page-flip experience
- **VIP Users**: arianamillb@icloud.com, jamesstephenbrooks@outlook.com (exempt from credit deductions)
- **Admin**: Dedicated login (Admin/Routetofreedom) for content moderation and approval

## Core Requirements
1. ✅ Art Studio - Free AI image generation
2. ✅ Pro Studio - Advanced workflows with credits
3. ✅ Stripe payments integration
4. ✅ Book Editor with voice narration
5. ✅ Email notifications (welcome, password reset, admin publish notification)
6. ✅ Starter Library - 100 free images for users
7. ✅ Admin Dashboard with dedicated login
8. ✅ Content moderation system
9. ⏳ Backend refactoring (in progress)

## What's Been Implemented

### Session: Dec 23, 2026 (Current)
- **Dedicated Admin Login Implemented**:
  - Username: `Admin`, Password: `Routetofreedom`
  - Separate JWT token with `admin: true` claim
  - All admin endpoints now use `get_admin_user` dependency
  - Admin token stored in `azories-admin-token` localStorage
  
- **Publishing Workflow FULLY FIXED**:
  - **BLOCKED direct publish**: Removed `is_published` and `publish_status` from `BookUpdate` model
  - User clicks "Submit for Review" → status changes to `pending_review` (book stays unpublished)
  - Added `/api/books/{id}/unpublish` endpoint for users to withdraw published books
  - Email notification sent to `book@azories.com` when book submitted
  - Dashboard shows status badges: Published (green), Pending Review (amber), Rejected (red), Draft (gray)
  - Admin manually runs AI moderation via "Scan" button
  - **Only admin can publish**: via `/api/admin/books/{id}/approve`
  - Fixed all direct publish code in Dashboard.js and MySeries.js
  
- **COMBINED Admin Dashboard** (at `/admin`):
  - **Stats Bar**: Pending Review, Flagged, Total Books, Published, Total Users
  - **Search & Filters**: Search by title/author, filter by Genre, filter by Age Rating
  - **Generate Missing Covers**: AI-powered cover generation for books without images
  - **Tabs**:
    - Pending Reviews: View books awaiting approval, run AI moderation, approve/reject
    - All Books: Full CMS - publish/unpublish, feature, best-of-week, delete
    - Users: User management with search - name, email, subscription, credits, join date
    - Analytics: Total books, published, users, pro users, views, reads
  - "Seed Test Books" button for testing
  
- **Library Thumbnail Fix**:
  - Fixed book cover positioning in ImmersiveLibrary3D component
  - Cover now positioned with `left: -140px` instead of `translateX(-85%)`

- **Route Updates**:
  - `/admin` → Combined AdminDashboard (CMS + Content Moderation + Users + Analytics)
  - `/admin/cms` → Legacy AdminCMS (kept for backwards compatibility)
  - Onboarding modal skipped on admin pages

### Previous Sessions
- **UI/UX Overhaul**: Art Studio reorganization, Media tab combined, unsaved changes warning
- **Starter Library**: 100 images, accessible in Art Studio and Book Editor
- **Node Editor Fixes**: 2nd Output node working, copy nodes, drag selection
- **Voice Narration**: Whisper integration
- **Email System**: Resend integration
- **Backend Refactoring**: Started migrating to routes/

## Tech Stack
- **Frontend**: React, Shadcn UI, ReactFlow, Tailwind CSS
- **Backend**: FastAPI, Pydantic
- **Database**: MongoDB
- **AI**: fal.ai (PuLID, LoRA, Kling), emergentintegrations (Sora 2, OpenAI Moderation), OpenAI (Whisper)
- **Email**: Resend (to `book@azories.com`)
- **Payments**: Stripe

## Key API Endpoints

### Admin Endpoints (require admin JWT)
- `POST /api/admin/login` - Admin login (Admin/Routetofreedom)
- `GET /api/admin/verify` - Verify admin token
- `GET /api/admin/pending-reviews` - Get books pending review
- `POST /api/admin/books/{id}/run-moderation` - Run AI moderation
- `POST /api/admin/books/{id}/approve` - Approve and publish book
- `POST /api/admin/books/{id}/reject?reason=...` - Reject book

### Publishing Flow
- `POST /api/books/{id}/request-publish` - Submit book for review (sends email)

## Prioritized Backlog

### P0 - Critical (DONE THIS SESSION)
- [x] Dedicated Admin Login (Admin/Routetofreedom)
- [x] Publishing workflow with Pending Review status
- [x] Admin triggers moderation from dashboard
- [x] Email notification to book@azories.com
- [x] Library thumbnail fix

### P1 - High Priority
- [ ] Test PuLID with new fal.ai API key
- [ ] Complete backend refactoring (server.py → routes/)
- [ ] Character consistency improvements

### P2 - Medium Priority
- [ ] Frontend refactoring (ProStudio.js, BookEditor.js)
- [ ] Mobile UI/UX improvements (iPad)

### P3 - Future
- [ ] Real-time collaboration
- [ ] Sample book generation
- [ ] readkids.com competitor analysis

## Admin Credentials
- **Username**: Admin
- **Password**: Routetofreedom
- **Route**: /admin

## Test Credentials
- **VIP User**: jamesstephenbrooks@outlook.com / test123
