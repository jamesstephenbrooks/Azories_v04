"""
Iteration 6 - Testing New Features:
1. Summary popup on Library book cards (backend data support)
2. Admin CMS button removal (Dashboard - frontend only)
3. Video generation size parameter (1280x720 instead of 1920x1080)
4. Core API endpoints verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBookSummaryData:
    """Test book data includes fields needed for summary popup"""
    
    def test_books_list_has_summary_fields(self):
        """Verify books endpoint returns summary-related fields"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "No books found"
        
        book = data[0]
        # Check summary-related fields exist
        assert "description" in book
        assert "back_cover_text" in book
        assert "genre" in book
        assert "author_name" in book
        assert "age_rating" in book
        print(f"✓ Books list includes summary fields - {len(data)} books available")

    def test_single_book_has_summary_data(self):
        """Verify single book endpoint returns summary data"""
        # First get a book ID
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        assert response.status_code == 200
        books = response.json()
        assert len(books) > 0
        
        book_id = books[0]["id"]
        
        # Get single book
        response = requests.get(f"{BASE_URL}/api/books/{book_id}")
        assert response.status_code == 200
        book = response.json()
        
        # Verify summary fields
        assert "description" in book
        assert "back_cover_text" in book
        assert "back_cover_image" in book
        print(f"✓ Single book API returns summary data: '{book['title']}'")

    def test_featured_books_have_summary(self):
        """Verify featured books endpoint also returns summary fields"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            book = data[0]
            assert "description" in book
            assert "back_cover_text" in book
            print(f"✓ Featured books have summary fields - {len(data)} featured books")
        else:
            print("✓ Featured books endpoint works (no featured books currently)")


class TestCoreAPIEndpoints:
    """Test core API endpoints are working"""
    
    def test_api_health(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✓ API health check passed")

    def test_genres_endpoint(self):
        """Test genres endpoint"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert len(data["genres"]) > 0
        print(f"✓ Genres endpoint working - {len(data['genres'])} genres")

    def test_age_ratings_endpoint(self):
        """Test age ratings endpoint"""
        response = requests.get(f"{BASE_URL}/api/age-ratings")
        assert response.status_code == 200
        data = response.json()
        assert "age_ratings" in data
        print(f"✓ Age ratings endpoint working - {len(data['age_ratings'])} ratings")

    def test_voices_endpoint(self):
        """Test narrator voices endpoint"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "voice_id" in data[0]
        assert "name" in data[0]
        print(f"✓ Voices endpoint working - {len(data)} voices available")


class TestAuthenticationFlow:
    """Test user authentication"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login successful - User: {data['user']['name']}")
        return data["access_token"]

    def test_login_fail_invalid_password(self):
        """Test login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 401
        print("✓ Login correctly rejects wrong password")

    def test_protected_endpoint_requires_auth(self):
        """Test that protected endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/books/my")
        assert response.status_code == 401
        print("✓ Protected endpoints require authentication")


class TestAdminCMS:
    """Test Admin CMS endpoints"""
    
    def test_admin_login(self):
        """Test admin login endpoint"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "azories_admin",
            "password": "AzoriesAdmin2024!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✓ Admin login successful")
        return data["access_token"]

    def test_admin_login_fail_wrong_credentials(self):
        """Test admin login fails with wrong credentials"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "wrong_admin",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Admin login correctly rejects wrong credentials")

    def test_admin_verify_with_valid_token(self):
        """Test admin token verification"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "azories_admin",
            "password": "AzoriesAdmin2024!"
        })
        token = login_response.json()["access_token"]
        
        # Verify token
        response = requests.get(
            f"{BASE_URL}/api/admin/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        print("✓ Admin token verification working")


class TestVideoGenerationEndpoint:
    """Test video generation endpoint parameters"""
    
    def test_video_generation_endpoint_exists(self):
        """Test AI video generation endpoint requires auth"""
        response = requests.post(f"{BASE_URL}/api/ai/generate-video", json={
            "prompt": "test prompt"
        })
        # Should return 401 (not authenticated) not 404
        assert response.status_code == 401
        print("✓ Video generation endpoint exists and requires auth")

    def test_image_generation_endpoint_exists(self):
        """Test AI image generation endpoint requires auth"""
        response = requests.post(f"{BASE_URL}/api/ai/generate-image", json={
            "prompt": "test prompt"
        })
        assert response.status_code == 401
        print("✓ Image generation endpoint exists and requires auth")


class TestLibraryFeatures:
    """Test Library page related features"""
    
    def test_books_search(self):
        """Test search functionality"""
        response = requests.get(f"{BASE_URL}/api/books?search=story&published_only=true")
        assert response.status_code == 200
        print("✓ Book search working")

    def test_books_filter_by_genre(self):
        """Test genre filter"""
        response = requests.get(f"{BASE_URL}/api/books?genre=Fantasy&published_only=true")
        assert response.status_code == 200
        print("✓ Book genre filter working")

    def test_books_featured_filter(self):
        """Test featured filter"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        assert response.status_code == 200
        data = response.json()
        # All returned books should be featured or best of week
        for book in data:
            assert book.get("is_featured") or book.get("is_best_of_week")
        print(f"✓ Featured books filter working - {len(data)} featured books")


# Module-level fixtures
@pytest.fixture(scope="module")
def auth_token():
    """Get user auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "testuser2@example.com",
        "password": "TestPass123!"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/admin/login", json={
        "username": "azories_admin",
        "password": "AzoriesAdmin2024!"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
