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
│   ├── routes/
│   │   └── print_orders.py   # POD ordering endpoints
│   └── services/
│       ├── print_pdf_generator.py  # PDF generation for print
│       ├── gelato_service.py       # Gelato API integration
│       └── fal_service.py          # AI image generation
└── frontend/
    └── src/
        ├── pages/
        │   ├── BookReader.js       # Book reading experience
        │   ├── StoryCreator.js     # AI story creation
        │   └── Landing.js          # Homepage
        └── components/
            ├── print/
            │   ├── BookPreview3D.jsx   # CSS 3D book mockup
            │   ├── BookPageStrip.jsx   # Page thumbnails (fixed navigation)
            │   └── BonusPagesPreview.jsx # Bonus pages modal (fixed)
            ├── AIReadingBuddy.jsx      # Azora AI helper
            └── PrintOrderModal.jsx     # POD ordering flow
```

## 3rd Party Integrations
- **fal.ai**: AI image generation (FLUX.1-schnell, Ideogram V3)
- **Gelato API**: Print on Demand fulfillment
- **Stripe**: Payment processing
- **Cloudinary**: Image/PDF storage (using chunked upload for large files)
- **ElevenLabs**: Text-to-speech narration (primary, with OpenAI TTS fallback)

## POD E2E Test Results (March 7, 2026)

| Step | Status | Notes |
|------|--------|-------|
| 1. Open book in preview | ✅ PASSED | Book opened correctly |
| 2. Click Order Printed Copy | ✅ PASSED | Modal opened |
| 3. 3D mockup shows correctly | ✅ PASSED | CSS 3D book with cover image |
| 4. Page thumbnails show correct images | ✅ PASSED | All pages visible with text |
| 5. Back cover shows as last thumbnail | ✅ PASSED | Dark purple Azora design |
| 6. Select softcover £14.99 | ✅ PASSED | Product selection working |
| 7. Enter test address | ✅ PASSED | Form validation working |
| 8. Shipping estimate appears | ✅ PASSED | Standard/Express/Next Day options |
| 9. Stripe checkout redirect | ✅ PASSED | Redirected to checkout.stripe.com |
| 10-13. Payment & Order Creation | ⏳ PENDING | Requires live payment |

## Critical Fixes Applied (March 7, 2026)
- ✅ Fixed PDF upload with chunked upload for large files (>10MB)
- ✅ Reduced JPEG quality from 95 to 75 for smaller file sizes
- ✅ Fixed navigation arrows closing the modal (stopPropagation)
- ✅ Fixed bonus page text overflow - Welcome page title now wraps properly
- ✅ Made all bonus pages responsive with proper text containment
- ✅ Updated landing page book cover to "The Wizard's Apprentice"
- ✅ Fixed "0 ch 0 pg" display bug for AI books - now correctly counts pages from embedded pages array
- ✅ Fixed mobile white bottom on StoryCreator and BookReader pages using min-h-[100dvh]
- ✅ Added lazy loading to book cover thumbnails in Dashboard for faster loading
- ✅ Fixed bonus preview modal closing when navigating (pointer-events-none when preview open)
- ✅ Implemented BookActionsDropdown component for cleaner "My Books" card actions
- ✅ Switched TTS to ElevenLabs with OpenAI fallback for high-quality narration
- ✅ Added mobile-friendly Prev/Next buttons to BonusPagesPreview
- ✅ Photorealistic style now routes to Ideogram V3 (realistic mode) for true photorealistic results
- ✅ Added fal.ai balance alert system - emails books@azories.com when balance is exhausted

## Pending Verification
- **P1**: Verify ElevenLabs narration integration
- **P1**: Verify AI story creation end-to-end
- **P1**: Test Ideogram Character style for consistency
- **P2**: Full E2E POD test (payment through to Gelato order creation)

## Future/Backlog
- P2: Build "My Orders" page for order history
- Order tracking notifications (email/SMS)
- Gift feature for checkout
- Decompose BookReader.js (>2000 lines)

## Test Credentials
- Email: test@printtest.com
- Password: printtest

## Key API Endpoints
- `POST /api/ai/story` - Generate AI story
- `GET /api/pricing` - Get art style pricing
- `POST /api/print/prepare/{book_id}` - Prepare book PDF
- `POST /api/print/checkout/create-session` - Create Stripe checkout
- `POST /api/print/create-order` - Submit order to Gelato

