# Code Refactoring Plan for Azories

## Overview
The codebase has grown organically and needs refactoring for maintainability:
- `server.py`: 6,713 lines → Should be split into ~15 modules
- `ProStudio.js`: 3,500 lines → Should be split into ~8 components

## Backend Refactoring Plan (`/app/backend/`)

### Current Structure
```
/app/backend/
├── server.py          # 6,713 lines (MONOLITHIC - needs splitting)
├── fal_service.py     # 17,385 bytes (OK - focused on fal.ai)
├── config.py          # Configuration (OK)
├── models/
│   └── schemas.py     # Pydantic schemas (partial)
├── routes/            # Route handlers (mostly empty)
└── services/          # Business logic (empty)
```

### Target Structure
```
/app/backend/
├── main.py            # FastAPI app initialization (minimal)
├── config.py          # Configuration & settings
├── database.py        # MongoDB connection
├── fal_service.py     # fal.ai integration (existing)
├── models/
│   ├── __init__.py
│   ├── user.py        # User schemas
│   ├── book.py        # Book schemas
│   ├── chapter.py     # Chapter/Page schemas
│   ├── series.py      # Series schemas
│   ├── character.py   # Pro Studio character schemas
│   ├── scene.py       # Pro Studio scene schemas
│   └── analytics.py   # Analytics schemas
├── routes/
│   ├── __init__.py    # Router aggregation
│   ├── auth.py        # Authentication (✅ CREATED)
│   ├── credits.py     # Credits management (✅ CREATED)
│   ├── books.py       # Book CRUD (~34 endpoints)
│   ├── chapters.py    # Chapter/Page CRUD (~9 endpoints)
│   ├── series.py      # Series CRUD (~8 endpoints)
│   ├── pro_studio.py  # Pro Studio (~65 endpoints)
│   ├── art_studio.py  # Art Studio (~21 endpoints)
│   ├── admin.py       # Admin endpoints (~14 endpoints)
│   ├── tts.py         # Text-to-speech
│   └── fal.py         # fal.ai proxy endpoints (~6 endpoints)
├── services/
│   ├── __init__.py
│   ├── auth_service.py    # Password hashing, JWT
│   ├── credit_service.py  # Credit operations
│   ├── book_service.py    # Book operations
│   ├── ai_service.py      # AI generation (OpenAI, fal.ai)
│   └── analytics_service.py # Analytics tracking
└── utils/
    ├── __init__.py
    └── helpers.py         # Common utilities
```

### Migration Steps
1. ✅ Create route stubs for auth.py, credits.py
2. Extract Pydantic models to models/ directory
3. Create service layer for business logic
4. Move routes one module at a time (test after each)
5. Update imports in server.py to use new modules
6. Gradually deprecate server.py endpoints

## Frontend Refactoring Plan (`/app/frontend/src/pages/`)

### Current ProStudio.js (3,500 lines)
Contains:
- Character management (~800 lines)
- Scene management (~500 lines)
- Cinema Studio (~400 lines)
- Shots generation (~300 lines)
- Video generation (~400 lines)
- Gallery management (~300 lines)
- UI state & handlers (~800 lines)

### Target Structure
```
/app/frontend/src/pages/ProStudio/
├── index.js               # Main component, tab routing
├── ProStudioContext.js    # Shared state context
├── CharacterTab.jsx       # Character creation & management
├── SceneTab.jsx           # Scene creation & management
├── CinemaStudioTab.jsx    # Cinema presets
├── ShotsTab.jsx           # 9-shot generation
├── VideoTab.jsx           # Video generation
├── GalleryTab.jsx         # Gallery view
└── components/
    ├── CharacterCard.jsx
    ├── SceneCard.jsx
    ├── GenerationSettings.jsx
    ├── ImageGrid.jsx
    └── VideoPlayer.jsx
```

## Progress Tracking

### Completed
- [x] Created `/app/backend/routes/auth.py` (authentication routes)
- [x] Created `/app/backend/routes/credits.py` (credits management)
- [x] Created `/app/backend/routes/__init__.py` (router aggregation)
- [x] Created `/app/backend/routes/books.py` (books route template)
- [x] Created `/app/backend/routes/pro_studio.py` (pro studio route template)

### In Progress
- [ ] Migrate actual route implementations from server.py to modules
- [ ] Create service layer for business logic
- [ ] Frontend ProStudio.js refactoring

### Not Started
- [ ] Frontend ProStudio.js refactoring
- [ ] Service layer creation
- [ ] Full migration testing

## Notes
- Refactoring should be done incrementally to avoid breaking changes
- Each module should be tested independently before integration
- The existing server.py can remain as fallback during migration
- Priority: Backend first (more critical), then frontend

## Why This Matters
1. **Maintainability**: Smaller files are easier to understand and modify
2. **Testing**: Isolated modules can be unit tested
3. **Collaboration**: Multiple developers can work on different modules
4. **Performance**: Lazy loading possible for frontend components
5. **Debugging**: Easier to locate and fix issues
