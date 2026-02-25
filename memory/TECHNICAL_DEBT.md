# Azories - Technical Debt & Pending Items

## Code Review Items NOT YET Addressed

### Performance (Lower Priority)

**1. N+1 Query Pattern in `get_books()`**
- **Location:** `/app/backend/server.py` - `get_books()` function
- **Issue:** For every book returned, `get_book_with_counts()` fires additional MongoDB queries (one for chapters, then one per chapter for page counts). Fetching 100 books triggers 200+ queries.
- **Fix:** Replace with MongoDB aggregation pipeline using `$lookup` and `$size` to get all counts in a single query.
- **Impact:** Medium - affects book listing performance

**2. Duplicate `get_reading_stats` Function**
- **Location:** Lines ~1883 and ~5555 in server.py
- **Issue:** Function defined twice, second one shadows the first
- **Fix:** Remove the duplicate definition
- **Impact:** Low - code cleanliness

**3. Large Base64 Images in MongoDB**
- **Issue:** Some book covers, page images, and AI-generated content may still be stored as base64 strings (1-5MB each)
- **Fix:** Run migration to upload all remaining base64 images to CDN and store URLs instead
- **Impact:** Medium - affects query performance and risks 16MB document limit

### Code Quality (Lower Priority)

**4. Unused Variables in server.py**
- Lines with `F841` lint errors:
  - Line 3503: `size` unused
  - Line 3632: `size` unused  
  - Line 3925: `char_id` unused
  - Line 6407: `COMPOSITION_TAGS` unused
  - Line 7492: `status_color` unused
- **Fix:** Remove or use these variables
- **Impact:** Very Low - code cleanliness

**5. Bare `except` Clauses**
- Lines 6933, 7431: Using `except:` instead of `except Exception:`
- **Fix:** Change to specific exception types
- **Impact:** Very Low - code quality

### Architecture (Future)

**6. Backend Refactoring - Incomplete**
- **Status:** Started - admin routes extracted to `/app/backend/routes/admin.py`
- **Remaining:**
  - Extract auth routes
  - Extract books routes  
  - Extract pro_studio routes
  - Extract payments routes
  - Extract AI routes
- **Target:** Reduce server.py from ~8200 lines to <2000 lines
- **Impact:** Development velocity, maintainability

**7. Frontend Refactoring - Incomplete**
- **Status:** Started - hooks created at `/app/frontend/src/components/pro-studio/hooks.js`
- **Remaining:**
  - Extract ProStudio.js tabs into separate components (~5700 lines)
  - Extract BookEditor.js into components (~2600 lines)
- **Target:** Each component <500 lines
- **Impact:** Development velocity, bundle size

---

## Completed Code Review Items (Feb 25, 2026)

### Critical Bugs Fixed ✅
1. Removed duplicate ADMIN_USERNAME/ADMIN_PASSWORD definitions
2. Removed duplicate /api/contact route
3. Fixed `del series['_id']` → `series.pop("_id", None)`
4. Fixed `request.dict()` → `request.model_dump()` (Pydantic v2)

### Security Issues Fixed ✅
5. **REMOVED `/auth/make-admin` endpoint** - Critical privilege escalation
6. Moved VIP_USERS from hardcoded to environment variable
7. Added warning if ADMIN credentials not set in env
8. Updated all APP_URL/FRONTEND_URL defaults to https://azories.com
9. Password reset tokens now hashed (SHA-256) before storage

### Performance Fixed ✅
10. Periodic cleanup for TASK_STORE and animation_jobs (hourly)
11. Modern lifespan approach replaces deprecated on_event

### Code Quality Fixed ✅
12. All `datetime.utcnow()` → `datetime.now(timezone.utc)`
13. BookResponse includes narrator_voice_locked
14. AI-generated books have all required fields
15. Added invite accept endpoint (`/api/invites/{token}/accept`)

---

## Environment Variables Checklist

**Required in Production (.env):**
```
MONGO_URL=<mongodb connection string>
DB_NAME=<database name>
JWT_SECRET=<strong random string>
STRIPE_API_KEY=<sk_live_...>
EMERGENT_LLM_KEY=<key>
FAL_KEY=<key>
ELEVENLABS_API_KEY=<key>
ADMIN_USERNAME=<username>
ADMIN_PASSWORD=<strong password>
APP_URL=https://azories.com
FRONTEND_URL=https://azories.com
VIP_USERS=email1@example.com,email2@example.com
CORS_ORIGINS=https://azories.com
BREVO_SMTP_LOGIN=<brevo smtp login>
BREVO_API_KEY=<brevo api key>
BREVO_SENDER_EMAIL=books@azories.com
```

---

Last Updated: February 25, 2026
