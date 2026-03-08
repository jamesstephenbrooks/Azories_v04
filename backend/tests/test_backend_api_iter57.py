"""
Backend API Tests - Iteration 57
Tests for core API endpoints: Auth, Books, Credits, Jobs, Library
"""
import pytest
import requests
import os

# Use the production URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://story-creator-dev.preview.emergentagent.com')
if BASE_URL.endswith('/'):
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
TEST_EMAIL = "test@printtest.com"
TEST_PASSWORD = "printtest"

# Store auth token for authenticated tests
AUTH_TOKEN = None


class TestHealthCheck:
    """Basic health check - run first"""
    
    def test_health_endpoint(self):
        """Health endpoint should return ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        print(f"✅ Health check passed: {data}")


class TestAuthAPIs:
    """Authentication API tests: login, register, me"""
    
    def test_login_success(self):
        """POST /api/auth/login - should return token and user data"""
        global AUTH_TOKEN
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        # Validate response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Validate user data structure
        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
        assert "subscription" in user
        assert "credits" in user
        assert user["email"] == TEST_EMAIL
        
        # Save token for other tests
        AUTH_TOKEN = data["access_token"]
        print(f"✅ Login success: user={user['name']}, credits={user['credits']}")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - should reject invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✅ Invalid login correctly rejected: {data['detail']}")
    
    def test_get_me_authenticated(self):
        """GET /api/auth/me - should return current user with valid token"""
        global AUTH_TOKEN
        if not AUTH_TOKEN:
            # Login first
            login_resp = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            AUTH_TOKEN = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        assert response.status_code == 200, f"Get me failed: {response.text}"
        
        user = response.json()
        assert "id" in user
        assert "email" in user
        assert user["email"] == TEST_EMAIL
        assert "subscription" in user
        assert "credits" in user
        print(f"✅ Get me success: {user['name']}, subscription={user['subscription']}")
    
    def test_get_me_unauthenticated(self):
        """GET /api/auth/me - should reject without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✅ Unauthenticated /me correctly returns 401")
    
    def test_register_duplicate_email(self):
        """POST /api/auth/register - should reject duplicate email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,  # Already exists
                "password": "testpass123",
                "name": "Duplicate User"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data.get("detail", "").lower() or "email" in data.get("detail", "").lower()
        print(f"✅ Duplicate registration rejected: {data['detail']}")


class TestBooksAPIs:
    """Books API tests: GET /api/books, GET /api/books/{id}, GET /api/books/{id}/full"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we have auth token"""
        global AUTH_TOKEN
        if not AUTH_TOKEN:
            login_resp = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            AUTH_TOKEN = login_resp.json()["access_token"]
    
    def test_get_books_list(self):
        """GET /api/books - should return list of published books"""
        response = requests.get(f"{BASE_URL}/api/books")
        assert response.status_code == 200, f"Get books failed: {response.text}"
        
        books = response.json()
        assert isinstance(books, list)
        
        if len(books) > 0:
            # Validate book structure
            book = books[0]
            assert "id" in book
            assert "title" in book
            assert "description" in book
            assert "author_id" in book
            assert "cover_image" in book or "cover_image_url" in book or book.get("cover_image") == ""
            print(f"✅ Get books success: {len(books)} books returned")
            print(f"   First book: {book['title']}")
        else:
            print("✅ Get books success: 0 books (empty library)")
    
    def test_get_book_by_id(self):
        """GET /api/books/{id} - should return specific book"""
        # First get a list of books
        list_resp = requests.get(f"{BASE_URL}/api/books")
        books = list_resp.json()
        
        if len(books) == 0:
            pytest.skip("No books available for testing")
        
        book_id = books[0]["id"]
        response = requests.get(f"{BASE_URL}/api/books/{book_id}")
        assert response.status_code == 200, f"Get book by ID failed: {response.text}"
        
        book = response.json()
        assert book["id"] == book_id
        assert "title" in book
        assert "author_name" in book
        print(f"✅ Get book by ID success: {book['title']}")
    
    def test_get_book_full_with_pages(self):
        """GET /api/books/{id}/full - should return book with pages"""
        # First get a list of books
        list_resp = requests.get(f"{BASE_URL}/api/books")
        books = list_resp.json()
        
        if len(books) == 0:
            pytest.skip("No books available for testing")
        
        book_id = books[0]["id"]
        response = requests.get(f"{BASE_URL}/api/books/{book_id}/full")
        assert response.status_code == 200, f"Get book full failed: {response.text}"
        
        data = response.json()
        # The /full endpoint returns the book directly with pages embedded
        assert "id" in data
        assert "title" in data
        assert data["id"] == book_id
        
        # Check for pages - may be in 'pages' or 'chapters' depending on book structure
        pages = data.get("pages", [])
        assert isinstance(pages, list)
        print(f"✅ Get book full success: {data['title']}, {len(pages)} pages")
        
        # Check page structure if available
        if len(pages) > 0:
            page = pages[0]
            assert "text_content" in page or "content" in page or "image_url" in page
            print(f"   Has {len(pages)} pages with content")
    
    def test_get_book_nonexistent(self):
        """GET /api/books/{id} - should return 404 for non-existent book"""
        response = requests.get(f"{BASE_URL}/api/books/nonexistent-book-id-12345")
        assert response.status_code == 404
        print("✅ Non-existent book correctly returns 404")


class TestMyBooksAPI:
    """User Books API test: GET /api/books/my"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we have auth token"""
        global AUTH_TOKEN
        if not AUTH_TOKEN:
            login_resp = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            AUTH_TOKEN = login_resp.json()["access_token"]
    
    def test_get_my_books_authenticated(self):
        """GET /api/books/my - should return user's books"""
        global AUTH_TOKEN
        response = requests.get(
            f"{BASE_URL}/api/books/my",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        assert response.status_code == 200, f"Get my books failed: {response.text}"
        
        books = response.json()
        assert isinstance(books, list)
        print(f"✅ Get my books success: {len(books)} books for user")
        
        if len(books) > 0:
            book = books[0]
            assert "id" in book
            assert "title" in book
            print(f"   First book: {book['title']}")
    
    def test_get_my_books_unauthenticated(self):
        """GET /api/books/my - should reject without auth"""
        response = requests.get(f"{BASE_URL}/api/books/my")
        assert response.status_code == 401
        print("✅ Unauthenticated /books/my correctly returns 401")


class TestCreditsAPIs:
    """Credits API tests: GET /api/credits/balance, GET /api/ai/story-pricing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we have auth token"""
        global AUTH_TOKEN
        if not AUTH_TOKEN:
            login_resp = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            AUTH_TOKEN = login_resp.json()["access_token"]
    
    def test_get_credits_balance(self):
        """GET /api/credits/balance - should return user's credit balance"""
        global AUTH_TOKEN
        response = requests.get(
            f"{BASE_URL}/api/credits/balance",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        assert response.status_code == 200, f"Get credits balance failed: {response.text}"
        
        data = response.json()
        assert "credits" in data or "balance" in data
        credits = data.get("credits") or data.get("balance", 0)
        assert isinstance(credits, int)
        print(f"✅ Get credits balance success: {credits} credits")
    
    def test_get_credits_balance_unauthenticated(self):
        """GET /api/credits/balance - should reject without auth"""
        response = requests.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 401
        print("✅ Unauthenticated /credits/balance correctly returns 401")
    
    def test_get_story_pricing(self):
        """GET /api/ai/story-pricing - should return pricing tiers"""
        response = requests.get(f"{BASE_URL}/api/ai/story-pricing")
        assert response.status_code == 200, f"Get story pricing failed: {response.text}"
        
        data = response.json()
        # Should contain pricing info for different page counts
        assert isinstance(data, dict)
        print(f"✅ Get story pricing success: {data}")


class TestJobsAPI:
    """Jobs API test: GET /api/jobs/active"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we have auth token"""
        global AUTH_TOKEN
        if not AUTH_TOKEN:
            login_resp = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            AUTH_TOKEN = login_resp.json()["access_token"]
    
    def test_get_active_jobs(self):
        """GET /api/jobs/active - should return active generation jobs"""
        global AUTH_TOKEN
        response = requests.get(
            f"{BASE_URL}/api/jobs/active",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        assert response.status_code == 200, f"Get active jobs failed: {response.text}"
        
        data = response.json()
        # Should return a list of active jobs (may be empty)
        if isinstance(data, list):
            print(f"✅ Get active jobs success: {len(data)} active jobs")
        elif isinstance(data, dict) and "jobs" in data:
            print(f"✅ Get active jobs success: {len(data['jobs'])} active jobs")
        else:
            print(f"✅ Get active jobs success: response={data}")
    
    def test_get_active_jobs_unauthenticated(self):
        """GET /api/jobs/active - should reject without auth"""
        response = requests.get(f"{BASE_URL}/api/jobs/active")
        assert response.status_code == 401
        print("✅ Unauthenticated /jobs/active correctly returns 401")


class TestLibraryAPIs:
    """Library-related API tests"""
    
    def test_get_featured_books(self):
        """GET /api/books/featured - should return featured books"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        assert response.status_code == 200, f"Get featured books failed: {response.text}"
        
        books = response.json()
        assert isinstance(books, list)
        print(f"✅ Get featured books success: {len(books)} featured books")
        
        if len(books) > 0:
            # All books should be featured
            for book in books[:3]:
                print(f"   Featured: {book.get('title', 'Unknown')}")
    
    def test_get_newly_added_books(self):
        """GET /api/books/newly-added - should return recently added books"""
        response = requests.get(f"{BASE_URL}/api/books/newly-added")
        assert response.status_code == 200, f"Get newly added failed: {response.text}"
        
        data = response.json()
        # May return books list or object with books
        if isinstance(data, list):
            books = data
        elif isinstance(data, dict) and "books" in data:
            books = data["books"]
        else:
            books = []
        
        print(f"✅ Get newly added books success: {len(books)} new releases")
    
    def test_get_coming_soon_books(self):
        """GET /api/books/coming-soon - should return coming soon books"""
        response = requests.get(f"{BASE_URL}/api/books/coming-soon")
        assert response.status_code == 200, f"Get coming soon failed: {response.text}"
        
        books = response.json()
        assert isinstance(books, list)
        print(f"✅ Get coming soon books success: {len(books)} books")


class TestAdditionalEndpoints:
    """Additional useful API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we have auth token"""
        global AUTH_TOKEN
        if not AUTH_TOKEN:
            login_resp = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            AUTH_TOKEN = login_resp.json()["access_token"]
    
    def test_get_ai_story_trial_info(self):
        """GET /api/auth/ai-story-trial - should return trial info"""
        global AUTH_TOKEN
        response = requests.get(
            f"{BASE_URL}/api/auth/ai-story-trial",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        assert response.status_code == 200, f"Get AI story trial failed: {response.text}"
        
        data = response.json()
        # Should contain free stories remaining info
        print(f"✅ Get AI story trial info: {data}")
    
    def test_get_reading_stats(self):
        """GET /api/reading-stats - should return user reading stats"""
        global AUTH_TOKEN
        response = requests.get(
            f"{BASE_URL}/api/reading-stats",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        assert response.status_code == 200, f"Get reading stats failed: {response.text}"
        
        data = response.json()
        print(f"✅ Get reading stats success: {data}")
    
    def test_get_starter_library(self):
        """GET /api/starter-library - should return starter library content"""
        response = requests.get(f"{BASE_URL}/api/starter-library")
        # Note: May return 200 with data or 404 if not configured
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get starter library success: {len(data) if isinstance(data, list) else data}")
        elif response.status_code == 404:
            print("✅ Starter library not configured (404) - expected in some environments")
        else:
            assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
