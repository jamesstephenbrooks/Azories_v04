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
- **Character consistency system** for book series

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
9. ✅ Unified Pro Studio Gallery
10. ✅ Async task polling for long-running AI operations
11. ✅ Character-specific gallery in Shots panel
12. ⏳ Character consistency improvements (in progress)

## What's Been Implemented

### Session: Feb 24, 2026 (Current Fork)

**Async Task Polling Architecture (MAJOR FIX):**
1. **Fixed 520 timeout errors** for Shots and Video generation
   - Backend now returns `task_id` immediately (HTTP 202 Accepted)
   - New `GET /api/tasks/{task_id}` endpoint for polling status
   - Frontend polls every 3 seconds with progress updates
   - Shows progress percentage during generation (0-100%)
   - In-memory `TASK_STORE` tracks task state

2. **Character Gallery in Shots Panel:**
   - Clicking a character shows their dedicated gallery
   - Gallery includes: Master image, Reference images, Generated images
   - Users can select any image as source for 9-shot generation
   - "Master" badge on primary character image
   - Close button (X) to dismiss gallery

3. **Bug Fix:** Fixed `/api/my-books` -> `/api/books/my` endpoint mismatch

**Previous Session (Feb 24, 2026):**

1. **Shots Generation Fix**:
   - Fixed base64/URL handling for source images
   - Added proper error messages for budget exceeded
   - Added credit deduction (5 credits per generation)

2. **Video Generation Fix**:
   - Updated fal.ai API key
   - Images now uploaded to fal.ai CDN before processing
   - Kling video generation working

3. **Email System Fixed**:
   - Domain `azories.com` verified in Resend
   - Sender: `notifications@azories.com`

4. **Character Consistency Improvements**:
   - PuLID now receives character appearance traits automatically
   - Art style enforcement in generation prompts
   - Increased id_weight values for better face preservation

5. **UI Visibility Fixes**:
   - Changed dark buttons to colored outlines (purple, blue, amber)
   - Better hover states on action buttons

6. **Unified Gallery System**:
   - Gallery aggregates ALL Pro Studio content
   - Filter by: All, Images, Videos, Characters

**Credit Costs:**
- flux_generate: 1 credit
- flux_pro_generate: 2 credits
- pulid_generate: 3 credits
- shots_generate: 5 credits
- expression_generate: 2 credits
- video_generate: 10 credits
- lora_training: 50 credits
- lora_generate: 2 credits

## Prioritized Backlog

### P0 - Critical
- [x] Fix 520 timeout errors for Shots/Video generation (DONE - async polling)
- [x] Add character gallery in Shots panel (DONE)
- [ ] Test full Shots generation flow with actual image output

### P1 - High Priority
- [ ] Verify character consistency with Ariza after PuLID improvements
- [ ] Scene-character linking for book consistency
- [ ] Character expansion system (more poses, expressions)
- [ ] Art style lock per character

### P2 - Medium Priority
- [ ] Backend refactoring (server.py -> routes/)
- [ ] Frontend component breakdown (ProStudio.js is large)
- [ ] Investigate LoRA training getting stuck root cause

### P3 - Future
- [ ] Series consistency (same characters across multiple books)
- [ ] Style transfer between characters
- [ ] Batch generation for storyboards

## Technical Notes

### Async Task Polling Architecture
- `TASK_STORE`: In-memory dict storing task state
- Task fields: `status` (pending/processing/completed/failed), `progress`, `result`, `error`, `user_id`
- Cleanup: Tasks older than 1 hour are removed
- Endpoints: `POST /api/pro-studio/generate-shots`, `POST /api/pro-studio/animate-hero`, `GET /api/tasks/{task_id}`

### fal.ai Configuration
- Models: PuLID (face ID), Kling (video), FLUX (images)
- Images must be uploaded to fal.ai CDN for reliability

### Emergent LLM Key
- Used for: Shots, Expressions, Cover generation
- Budget tracking enabled
- Shows error with "Add Balance" link when exceeded

### Database
- Collection: `test_database`
- Characters: `pro_studio_characters`
- Gallery: `character_gallery`
