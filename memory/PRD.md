# Azories - Digital Book Platform PRD

## Original Problem Statement
User wants to enhance their "Azories" digital book application with:
- Finalized "Pro Studio" for AI content generation
- Credits-based business model with Stripe
- Professional site elements
- Library of sample books
- Bug fixes and codebase refactoring

## Core Requirements

### P0 - Critical
- **Book Reader Experience**: Must be fully optimized for mobile and desktop ✅
- **Art/Pro Studio Mobile**: Core creation tools usable on mobile
- **Character Thumbnail Generation**: Auto-generate when character created
- **Consistent Layout**: Image LEFT, text RIGHT for every page ✅
- **Data Consistency**: Immediate updates, permanent image storage ✅
- **Content Quality**: No text baked into illustrations ✅ (Feb 28)

### P1 - High Priority
- Monetization and tier gating (Stripe)
- Generate long-form stories for 17 books with short text
- Update text for 8 books (awaiting .docx files)
- Ingest Batch 3C books (5 new books)
- Production deployment for 24/7 uptime
- **Regenerate covers** for 25 books (to match interior Pixar style)

### P2 - Medium Priority
- Refactor server.py into modular route files
- Refactor large frontend components (ProStudio.js, BookEditor.js)
- Save planning documents to /app/memory/
- Audio caching for faster narration startup

## Current State (Feb 28, 2026)

### Completed ✅
- **249 page images regenerated** - Pixar style, portrait, no text (Feb 27-28)
- **25 books now visible** in public library
- **"Opening book..." bug fixed** - Auth issue resolved
- Page turning buttons working
- Text displaying on right page
- 80% viewport height on desktop
- Images fill left page properly

### Pending Tasks 🔴
- **Regenerate covers for 25 books** (still old watercolor style)
- **17 books need story text expansion** (short placeholder → full stories)
- **8 books need text from .docx files**
- **5 new books to ingest** (Batch 3C)

### Books Status
- **44 visible** in library (including all 25 regenerated books)
- **20 hidden** (various issues)

## Image Regeneration - SUCCESS (Feb 28, 2026)

### What Was Done
- Generated 249 Pixar-style portrait images using fal.ai
- Uploaded to Cloudinary with `_clean` suffix (unique filenames)
- Updated database with new URLs
- Zero failures

### Image Specifications
- Model: fal-ai/flux-pro/v1.1
- Size: 768x1024 (portrait)
- Style: Pixar/Disney 3D animation
- Constraint: No text/words in images

### URL Pattern
- Old: `azories/books/{slug}/page_XX.jpg`
- New: `azories/books/{slug}/page_XX_clean.jpg`

## The 25 Regenerated Books
1. The Unicorn's Rainbow Bridge
2. The Wizard's Apprentice
3. The Giant's Gentle Heart
4. Pixie Dust Adventures
5. The Enchanted Carousel
6. Captain Compass and the Treasure Map
7. The Jungle Explorers Club
8. Mountain Climbing Mice
9. The Underground City
10. Sky Pirates of Cloudland
11. The Lighthouse Keeper's Secret
12. The Arctic Expedition
13. The Time Machine Treehouse
14. Space Station School
15. The Friendly Martians
16. Gadget Girl and the Invention Fair
17. The Secret Code Club
18. Detective Daisy's First Case
19. The Burping Dragon
20. The Backwards Day
21. Pirate Pete's Bad Hair Day
22. Dinosaur Dentist
23. The Alphabet Zoo
24. Kindness Kingdom
25. The Feelings Garden

## Tech Stack
- Frontend: React with react-pageflip library
- Backend: FastAPI (Python)
- Database: MongoDB (test_database)
- Image Storage: Cloudinary
- AI: OpenAI (TTS, thumbnails), fal.ai (image gen)
- Payments: Stripe

## Key Files
- /app/frontend/src/pages/BookReader.js
- /app/frontend/src/components/RealisticPageFlip.jsx
- /app/backend/server.py
- /app/backend/scripts/batch_regenerate_all.py
- /app/memory/SESSION_STATE_20260228.md

## Test Credentials
- Admin: jamesstephenbrooks@outlook.com / Routetofreedom

## Next Session Tasks (Priority Order)
1. Regenerate covers for 25 books (match Pixar interior style)
2. Generate long-form text for 17 books
3. Update text for 8 books from .docx files
4. Ingest 5 new books (Batch 3C)
5. Audio caching implementation
6. Refactor server.py
