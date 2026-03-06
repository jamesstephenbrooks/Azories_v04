# Azories - AI Story Creator PRD

## Original Problem Statement
Build a "Print on Demand" (POD) book ordering feature using the Gelato API for an AI Story Creator application. The app allows users to create, view, and order printed copies of AI-generated children's books.

## What's Been Implemented

### Core Features (Stable)
- AI Story Creation with text and illustrations
- Book viewing with realistic page-flip animation
- User library and dashboard
- ElevenLabs narration integration
- Stripe payment integration for print orders

### Print on Demand Feature (Completed - March 6, 2026)
- **Print Order Modal** with complete ordering flow:
  - Pure CSS 3D book mockup (softcover/hardcover toggle)
  - Page thumbnails showing Cover, all pages with image+text spreads, and Back Cover
  - Address entry with country selection
  - Shipping estimate from Gelato API
  - Stripe checkout integration
  
- **Product Preview**:
  - 8x11 portrait format book visualization
  - Cover image fills front face directly (no alignment issues)
  - Dynamic spine width based on page count
  - Softcover: thin spine, rounded edges, matte look
  - Hardcover: thicker spine, sharp corners, glossy effect

- **Back Cover Navigation**:
  - Back cover accessible as the last page when reading
  - Displays Azories branding with mascot
  - "Library" and "Read Again" buttons

### Recent Bug Fixes (March 6, 2026)
1. ✅ Replaced AI-generated mockups with pure CSS 3D book (no alignment issues)
2. ✅ Fixed back cover missing from print thumbnails
3. ✅ Fixed back cover navigation in BookReader (now accessible)
4. ✅ Fixed getTotalPages() to return actual flipbook page count

## Code Architecture
```
/app/
├── backend/
│   ├── server.py
│   ├── routes/
│   │   └── print_orders.py      # Print order API endpoints
│   └── services/
│       └── gelato_service.py    # Gelato API integration
└── frontend/
    └── src/
        ├── pages/
        │   ├── BookReader.js    # Book reading with back cover support
        │   └── Dashboard.js     # My Books with print option
        └── components/
            ├── print/
            │   ├── BookPreview3D.jsx   # Pure CSS 3D book mockup
            │   └── BookPageStrip.jsx   # Page thumbnails with back cover
            ├── PrintOrderModal.jsx     # Complete print ordering flow
            └── RealisticPageFlip.jsx   # Flipbook with back cover navigation
```

## Key Technical Details
- **CSS 3D Book**: Uses transform: perspective for 3D effect without image distortion
- **Dynamic Spine**: `spineWidth = Math.max(10, Math.min(35, pageCount * 0.7))`
- **Back Cover Navigation**: Uses flipbook's `goToPage(totalPages - 1)` for direct navigation
- **Page Count**: Flipbook has 22 pages (1 cover + 20 content spreads + 1 back cover)

## API Endpoints
- `POST /api/print/price-estimate` - Get pricing for softcover/hardcover
- `POST /api/print/checkout/create-session` - Create Stripe checkout session
- `GET /api/books/{book_id}/full` - Get book with pages and back_cover_image

## Third-Party Integrations
- **Gelato API**: Print fulfillment (requires GELATO_API_KEY)
- **Stripe**: Payments (requires STRIPE_API_KEY)
- **Cloudinary**: Image storage
- **ElevenLabs**: Narration (requires ELEVENLABS_API_KEY)

## Test Credentials
- Email: hardcover@test.com
- Password: testpass123
- Test Book: fb341971-71be-4c8a-b764-a7cac7fb9a71

## Pending Tasks

### P1 - Full End-to-End POD Testing
- [ ] Complete Stripe payment flow test with test card 4242...
- [ ] Verify order created in database
- [ ] Verify order sent to Gelato API
- [ ] Verify confirmation email sent

### P2 - "My Orders" Section
- [ ] Build order history page
- [ ] Show order status, tracking, ETA

### P2 - Mobile White Screen Fix
- [ ] Fix story creation page half white screen on mobile

### P3 - Production Deployment
- [ ] Pre-deployment verification:
  - [ ] ElevenLabs narration working
  - [ ] AI story creation working end-to-end
  - [ ] Print order modal correct for all books

## Future Tasks (Backlog)
- Gift feature for checkout
- Creative Studio rebuild
- Refactor BookReader.js (2000+ lines)
- Consolidate gallery components

## Known Issues
None critical. Core POD flow is working.
