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

## Core Requirements
1. ✅ Art Studio - Free AI image generation
2. ✅ Pro Studio - Advanced workflows with credits
3. ✅ Stripe payments integration
4. ✅ Book Editor with voice narration
5. ✅ Email notifications (welcome, password reset)
6. ✅ Starter Library - 100 free images for users
7. ⏳ Backend refactoring (in progress)

## What's Been Implemented

### Session: Feb 23, 2026 (Latest)
- **Art Studio Header Redesign**:
  - Node Workflow moved to tab navigation (next to Character Builder) - both FREE
  - Pro Studio button kept in header with "PRO" badge
  - Gallery button now has prominent green gradient styling with count
- **Starter Library (100 images)**:
  - Added `/api/starter-library` endpoint with 100 diverse free images
  - Categories: characters, scenes, animals, fantasy, nature, space
  - Available in Art Studio Gallery (collapsible amber section)
  - Available in Book Editor Gallery Picker (new "⭐ Starter Library" tab)
- **Unsaved Changes Warning**:
  - Book Editor now tracks content changes
  - Shows "Unsaved changes" indicator in header
  - Browser warns before leaving page with unsaved changes
  - Save button highlights (amber) when changes are pending

### Previous Session: Feb 23, 2026
- **Fixed Node Editor errors**: Resolved infinite loop, updateNodeData reference, canvasRef issues
- **Animation Enhancement**: 
  - Auto-populate motion prompt from gallery image
  - Camera movement options (Static, Slow Zoom, Slow Pan, Orbit)
  - Shows selected image info (name, style, prompt)
- **Node Workflow Improvements**:
  - Lightning bolt run button in top-left
  - Copy selected nodes with all data preserved
  - Drag selection enabled
  - Combine node: 4 input handles
  - Output node lock/unlock (auto-lock after generation)
  - Image node: Upload + Gallery picker (Art/Pro Studio tabs)
- **Save to Book**: Modal with book dropdown selector

### Previous Sessions
- LoRA Training feature fixed & verified
- Voice Narration (Whisper integration)
- Email system (Resend integration) 
- Book cover thumbnails on dashboard
- Video support in book pages
- Gallery picker integration in Book Editor
- Node editor copy & continue workflow buttons
- Backend route refactoring initiated

## Tech Stack
- **Frontend**: React, Shadcn UI, ReactFlow
- **Backend**: FastAPI, Pydantic
- **Database**: MongoDB
- **AI**: fal.ai (PuLID, LoRA, Kling), emergentintegrations (Sora 2), OpenAI (Whisper)
- **Email**: Resend
- **Payments**: Stripe

## Prioritized Backlog

### P0 - Critical
- [x] Starter Library (100 images) - DONE
- [x] Art Studio header reorganization - DONE
- [x] Unsaved changes warning in Book Editor - DONE
- [ ] Test animation save bug fix
- [ ] Test email notifications

### P1 - High Priority
- [ ] Complete backend refactoring (server.py → routes/)
- [ ] Test Book Editor UX features (video, galleries)
- [ ] Book-specific media library in Book Editor

### P2 - Medium Priority
- [ ] Frontend refactoring (ProStudio.js)
- [ ] Mobile UI/UX improvements (iPad)

### P3 - Future
- [ ] Real-time collaboration
- [ ] Sample book generation
- [ ] Cookie consent banner
- [ ] Legal pages (Terms, Privacy)
- [ ] Contact form
