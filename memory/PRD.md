# Azories - AI Story Creator PRD

## Original Problem Statement
Build a "Print on Demand" (POD) book ordering feature using the Gelato API for an AI Story Creator platform. The platform allows users to create AI-powered personalized children's stories with illustrations.

## Core Features Implemented
- **AI Story Creation**: Create personalized stories with AI-generated illustrations using fal.ai (FLUX.1-schnell and Ideogram V3 models)
- **Book Reader**: Interactive flipbook reader with audio narration (ElevenLabs)
- **Print on Demand**: Full POD integration with Gelato API, Stripe payments, CSS 3D book preview
- **User Library**: Personal book collection management
- **Art Styles**: Multiple AI art styles including Storybook, Character (Consistent), Realistic

## Architecture
```
/app/
├── backend/
│   ├── server.py             # Main FastAPI server
│   └── services/
│       ├── pdf_service.py    # PDF generation for print
│       └── fal_service.py    # AI image generation
└── frontend/
    └── src/
        ├── pages/
        │   ├── BookReader.js       # Book reading experience
        │   ├── StoryCreator.js     # AI story creation
        │   └── Landing.js          # Homepage
        └── components/
            ├── print/
            │   ├── BookPreview3D.jsx   # CSS 3D book mockup
            │   ├── BookPageStrip.jsx   # Page thumbnails
            │   └── BonusPagesPreview.jsx # Bonus pages modal
            ├── AIReadingBuddy.jsx      # Azora AI helper
            └── PrintOrderModal.jsx     # POD ordering flow
```

## 3rd Party Integrations
- **fal.ai**: AI image generation (FLUX.1-schnell, Ideogram V3)
- **Gelato API**: Print on Demand fulfillment
- **Stripe**: Payment processing
- **Cloudinary**: Image storage
- **ElevenLabs**: Text-to-speech narration

## What's Been Implemented (March 7, 2026)
- ✅ Fixed navigation arrows in BookPageStrip closing modal
- ✅ Fixed bonus page text overflow in preview
- ✅ Updated landing page book cover from "Robot Best Friend" to "The Wizard's Apprentice"
- ✅ Made all bonus pages responsive for mobile preview
- ✅ Pure CSS 3D book mockup with dynamic spine width
- ✅ Softcover/hardcover selection functionality
- ✅ Print quality image generation (8:10 aspect ratio)
- ✅ Ideogram art styles for character consistency

## Pending Tasks (P0-P2)
- **P0**: Full End-to-End POD test (modal, address, shipping, Stripe checkout)
- **P1**: Verify ElevenLabs narration integration
- **P1**: Verify AI story creation end-to-end
- **P1**: Test Ideogram Character style for consistency
- **P2**: Fix AI story creation page half white screen on mobile
- **P2**: Build "My Orders" page for print order history

## Future/Backlog
- Gift feature for checkout
- Creative Studio rebuild
- Refactor gallery components
- Decompose BookReader.js (>2000 lines)
- Deploy to production

## Test Credentials
- Email: test@printtest.com
- Password: printtest

## Key API Endpoints
- `POST /api/ai/story` - Generate AI story
- `GET /api/pricing` - Get art style pricing
- `POST /api/stripe/create-checkout-session` - Create Stripe session
- `POST /api/print/prepare/{book_id}` - Prepare book for printing
