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
- **Art/Pro Studio Mobile**: Core creation tools usable on mobile ✅
- **AI Story Creator Page Count**: Must create exact number of pages requested ✅ (Mar 1)
- **AI Story Creator Images**: Each page must have fal.ai generated image ✅ (Mar 1)
- **Free Stories Trial**: New users get 3 free story creations ✅ (Mar 1)
- **BookEditor Mobile Layout**: Responsive design matching ProStudio/Creators ✅ (Mar 1)

### P1 - High Priority
- Monetization and tier gating (Stripe) ✅
- Generate long-form stories for 17 books with short text
- Update text for 8 books (awaiting .docx files)
- Ingest Batch 3C books (5 new books)
- Production deployment for 24/7 uptime ✅ READY
- **Regenerate covers** for 25 books (to match interior Pixar style)

### P2 - Medium Priority
- Refactor server.py into modular route files
- Refactor large frontend components (ProStudio.js, BookEditor.js)
- Audio caching for faster narration startup

## Current State (March 1, 2026)

### Completed ✅
- **AI Story Creator Page Count Fix** - Now creates exact number of requested pages (Mar 1)
- **AI Story Creator Images** - All pages get fal.ai images uploaded to Cloudinary (Mar 1)
- **BookEditor Mobile Layout** - Responsive design with Visual/Text tabs, floating bottom bar (Mar 1)
- **Free Stories Trial System** - 3 free AI story creations for new users (Mar 1)
- **Credits System** - Full Stripe integration for credit purchases
- **249 page images regenerated** - Pixar style, portrait, no text (Feb 27-28)
- **25 books now visible** in public library
- Page turning buttons working
- Text displaying on right page
- 80% viewport height on desktop
- Images fill left page properly
- "Art Studio" renamed to "Creators"

### Production Ready ✅
Deployment agent verified:
- All environment variables properly configured
- CORS allows all origins
- MongoDB connection reads from environment
- Supervisor configuration valid
- No hardcoded secrets

### Pending Tasks 🔴
- **Regenerate covers for 25 books** (still old watercolor style)
- **17 books need story text expansion** (short placeholder → full stories)
- **8 books need text from .docx files**
- **5 new books to ingest** (Batch 3C)

## AI Story Creator Technical Details

### Page Count Fix Implementation
```python
# After AI generates story, validate page count
actual_pages = len(story_data.get("pages", []))
expected_pages = request.num_pages

if actual_pages < expected_pages:
    # Send continuation prompt for remaining pages
    remaining_pages = expected_pages - actual_pages
    continuation_prompt = f"Continue with {remaining_pages} more pages..."
    additional_pages = await chat.send_message(continuation_prompt)
    story_data["pages"].extend(additional_pages)
```

### Image Generation Flow
1. Story text generated via Emergent LLM Chat (GPT)
2. For each page, image prompt sent to fal.ai
3. Generated image uploaded to Cloudinary
4. Cloudinary URL stored in page document

## BookEditor Mobile Responsive Pattern

### State Management
```javascript
const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
const [mobileActivePanel, setMobileActivePanel] = useState('visual');
```

### Layout Breakpoints
- **Mobile (<1024px)**: Visual/Text toggle tabs, stacked panels, floating bottom bar
- **Desktop (≥1024px)**: Side-by-side panels, fixed sidebar

### Key CSS Classes
- `lg:hidden` - Mobile-only elements
- `hidden lg:flex` - Desktop-only elements  
- `flex-col lg:flex-row` - Stacking on mobile, row on desktop
- `safe-area-bottom` - iPhone notch compatibility

## Tech Stack
- Frontend: React with react-pageflip library
- Backend: FastAPI (Python)
- Database: MongoDB (azories)
- Image Storage: Cloudinary
- AI: fal.ai (images), OpenAI (TTS)
- Payments: Stripe

## Key Files
- `/app/backend/server.py`: Core API logic
- `/app/frontend/src/pages/Dashboard.js`: AI Story Creator dialog
- `/app/frontend/src/pages/BookEditor.js`: Mobile-responsive book editor
- `/app/frontend/src/pages/BookReader.js`: Reading experience

## Test Reports
- `/app/test_reports/iteration_42.json` - Free stories trial tests
- `/app/test_reports/iteration_43.json` - Page count and mobile layout tests
- `/app/backend/tests/test_free_stories_trial.py`
- `/app/backend/tests/test_ai_story_page_count.py`

## Test Credentials
- Admin: jamesstephenbrooks@outlook.com / Routetofreedom

## Next Session Tasks (Priority Order)
1. ~~AI Story Creator page count fix~~ ✅
2. ~~End-to-end test with 5 pages~~ ✅
3. ~~BookEditor mobile layout~~ ✅
4. ~~Deploy to production~~ READY
5. Regenerate covers for 25 books (match Pixar interior style)
6. Generate long-form text for 17 books
7. Update text for 8 books from .docx files
8. Ingest 5 new books (Batch 3C)
9. Audio caching implementation
10. Refactor server.py
