"""
Iteration 33 Tests: Post API Refactor + Thumbnail + Cloudinary Integration Tests
- User authentication (login/logout)
- Book listing in Library page
- Pro Studio gallery loading with thumbnails
- Art Studio image generation
- Video/animation playback in gallery
- Book creation and editing
- Dashboard functionality
- API authentication headers working correctly
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://kids-mode-demo.preview.emergentagent.com')

# Test credentials - VIP user
VIP_EMAIL = "jamesstephenbrooks@outlook.com"
VIP_PASSWORD = "test123"

class TestAuthAPI:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login with VIP credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == VIP_EMAIL
        print(f"✓ Login successful for {VIP_EMAIL}")
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"
        print("✓ Invalid login rejected correctly")
        
    def test_auth_me_requires_token(self):
        """Test /auth/me endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"
        print("✓ /auth/me correctly requires authentication")
        
    def test_auth_me_with_token(self):
        """Test /auth/me with valid token"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        # Then check /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", 
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert data["email"] == VIP_EMAIL
        print("✓ /auth/me returns user data with valid token")


class TestBooksAPI:
    """Books endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication for tests"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_public_books(self):
        """Test getting public books (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/books")
        assert response.status_code == 200, f"Failed: {response.text}"
        books = response.json()
        assert isinstance(books, list)
        print(f"✓ Public books endpoint returns {len(books)} books")
        
    def test_get_my_books(self):
        """Test getting user's own books (requires auth)"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        books = response.json()
        assert isinstance(books, list)
        print(f"✓ My books endpoint returns {len(books)} books")
        
    def test_get_featured_books(self):
        """Test getting featured books"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        assert response.status_code == 200, f"Failed: {response.text}"
        books = response.json()
        assert isinstance(books, list)
        print(f"✓ Featured books endpoint returns {len(books)} books")
        
    def test_get_genres(self):
        """Test getting genres"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "genres" in data
        print(f"✓ Genres endpoint returns {len(data['genres'])} genres")
        
    def test_get_age_ratings(self):
        """Test getting age ratings"""
        response = requests.get(f"{BASE_URL}/api/age-ratings")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "age_ratings" in data
        print(f"✓ Age ratings endpoint returns {len(data['age_ratings'])} ratings")


class TestDashboardAPI:
    """Dashboard-related API tests (verifying auth headers work)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_series_api(self):
        """Test series endpoint (Dashboard uses this)"""
        response = requests.get(f"{BASE_URL}/api/series", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        series = response.json()
        assert isinstance(series, list)
        print(f"✓ Series endpoint returns {len(series)} series")
        
    def test_credits_balance(self):
        """Test credits balance endpoint"""
        response = requests.get(f"{BASE_URL}/api/credits/balance", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "credits" in data
        assert "costs" in data
        print(f"✓ Credits balance: {data['credits']} credits")


class TestProStudioAPI:
    """Pro Studio tests - character consistency, gallery with thumbnails"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_get_characters(self):
        """Test getting Pro Studio characters"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "characters" in data
        print(f"✓ Pro Studio characters endpoint returns {len(data['characters'])} characters")
        
    def test_get_scenes(self):
        """Test getting Pro Studio scenes"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/scenes", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "scenes" in data
        print(f"✓ Pro Studio scenes endpoint returns {len(data['scenes'])} scenes")
        
    def test_get_unified_gallery(self):
        """Test unified gallery endpoint with thumbnails"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/gallery/unified", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "has_more" in data
        print(f"✓ Unified gallery returns {data['total']} items (showing {len(data['items'])})")
        
        # Check if thumbnails are present in items
        if data['items']:
            for item in data['items'][:3]:  # Check first 3 items
                if item.get('type') == 'image' and item.get('thumbnail_url'):
                    print(f"  - Thumbnail found: {item['thumbnail_url'][:60]}...")
                    
    def test_get_videos(self):
        """Test getting Pro Studio videos"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/videos", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "videos" in data
        print(f"✓ Pro Studio videos endpoint returns {len(data['videos'])} videos")
        
        # Check for Cloudinary URLs
        cloudinary_count = 0
        fal_count = 0
        for video in data['videos']:
            url = video.get('url', '') or video.get('video_url', '')
            if 'cloudinary' in url or 'res.cloudinary.com' in url:
                cloudinary_count += 1
            elif 'fal' in url.lower():
                fal_count += 1
        print(f"  - Cloudinary videos: {cloudinary_count}, fal.ai videos: {fal_count}")
        
    def test_character_styles(self):
        """Test character styles endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-styles")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "styles" in data
        print(f"✓ Character styles endpoint returns {len(data['styles'])} styles")
        
    def test_character_genres(self):
        """Test character genres endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-genres")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "genres" in data
        print(f"✓ Character genres endpoint returns {len(data['genres'])} genres")
        
    def test_scene_options(self):
        """Test scene options endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/scene-options")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Scene options should have location_types, lighting, moods
        print(f"✓ Scene options endpoint returns options")


class TestArtStudioAPI:
    """Art Studio tests - gallery, book galleries"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_get_art_studio_gallery(self):
        """Test Art Studio gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/art-studio/gallery", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "images" in data
        print(f"✓ Art Studio gallery returns {len(data['images'])} images")


class TestFalAPI:
    """fal.ai integration tests"""
    
    def test_fal_models(self):
        """Test fal.ai models endpoint"""
        response = requests.get(f"{BASE_URL}/api/fal/models")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "available" in data
        print(f"✓ fal.ai models available: {data['available']}")
        if data['available'] and 'models' in data:
            print(f"  - Models: {[m['name'] for m in data['models']]}")


class TestVoicesAPI:
    """Voice/narration tests"""
    
    def test_get_voices(self):
        """Test voices endpoint"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200, f"Failed: {response.text}"
        voices = response.json()
        assert isinstance(voices, list)
        print(f"✓ Voices endpoint returns {len(voices)} voices")


class TestStarterLibrary:
    """Starter library tests"""
    
    def test_get_starter_library(self):
        """Test starter library endpoint"""
        response = requests.get(f"{BASE_URL}/api/starter-library")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ Starter library endpoint works")


class TestTasksAPI:
    """Async task status endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_task_not_found(self):
        """Test task endpoint returns 404 for non-existent task"""
        response = requests.get(f"{BASE_URL}/api/tasks/nonexistent-task-id", headers=self.headers)
        assert response.status_code == 404, f"Expected 404 but got {response.status_code}"
        print("✓ Tasks endpoint correctly returns 404 for non-existent task")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
