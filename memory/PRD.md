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
10. ⏳ Character consistency improvements (in progress)

## What's Been Implemented

### Session: Feb 24, 2026 (Current)

**Pro Studio Fixes & Enhancements:**

1. **Shots Generation Fix**:
   - Fixed base64/URL handling for source images
   - Added proper error messages for budget exceeded
   - Added credit deduction (5 credits per generation)

2. **Video Generation Fix**:
   - Updated fal.ai API key: `9cc164f3-9355-4cc7-...`
   - Images now uploaded to fal.ai CDN before processing (fixes download errors)
   - Kling video generation working with new key

3. **Email System Fixed**:
   - Domain `azories.com` verified in Resend
   - Sender: `notifications@azories.com`
   - Admin emails to `books@azories.com` now working

4. **LoRA Training Reset**:
   - Reset Ariza's stuck LoRA training status

5. **Character Consistency Improvements**:
   - PuLID now receives character appearance traits automatically
   - Art style enforcement in generation prompts
   - Increased id_weight values for better face preservation
   - Added `character_appearance` and `art_style` parameters to `generate_with_face_id`

6. **UI Visibility Fixes**:
   - Changed dark buttons to colored outlines (purple, blue, amber)
   - Better hover states on action buttons
   - Improved contrast throughout Pro Studio

7. **Unified Gallery System**:
   - Gallery aggregates ALL Pro Studio content (characters, images, videos)
   - Filter by: All, Images, Videos, Characters
   - Can select from gallery for Video and Shots features
   - "Browse from Gallery" button in Upload mode

**Credit Costs:**
- flux_generate: 1 credit
- flux_pro_generate: 2 credits
- pulid_generate: 3 credits
- shots_generate: 5 credits
- expression_generate: 2 credits
- video_generate: 10 credits
- lora_training: 50 credits
- lora_generate: 2 credits

### Previous Sessions
- Admin Dashboard with search/filter for books and users
- Publishing workflow with AI moderation
- Email notifications on approve/reject
- Mobile/landscape responsive improvements
- Book reader page flip with audio narration

## Prioritized Backlog

### P0 - Critical
- [ ] Test Shots and Video generation with real images
- [ ] Verify character consistency with Ariza after PuLID improvements

### P1 - High Priority
- [ ] Scene-character linking for book consistency
- [ ] Character expansion system (more poses, expressions for same character)
- [ ] Art style lock per character (enforce across all generations)

### P2 - Medium Priority
- [ ] Backend refactoring (server.py → routes/)
- [ ] Frontend component breakdown (ProStudio.js is large)
- [ ] Similarity scoring after generation

### P3 - Future
- [ ] Series consistency (same characters across multiple books)
- [ ] Style transfer between characters
- [ ] Batch generation for storyboards

## Technical Notes

### fal.ai Configuration
- Key: `9cc164f3-9355-4cc7-8286-9f0943b64d94:f9dbbe1ab5957fc43fedf5b9c59fa04f`
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
