"""
Pre-Deployment Testing - Iteration 34
Comprehensive API verification for Azories platform.

Tests cover:
- User authentication (login, register, /me)
- Gallery loading (unified endpoint)
- Book creation flow
- Pro Studio (characters, scenes)
- Credits balance
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# VIP Test Credentials
VIP_EMAIL = "jamesstephenbrooks@outlook.com"
VIP_PASSWORD = "test123"


class TestAuthAPI:
    """Authentication endpoint tests"""
    
    def test_login_vip_user(self):
        """Test VIP user login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": VIP_EMAIL, "password": VIP_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == VIP_EMAIL
        assert data["user"]["role"] in ["user", "admin"]
        print(f"✓ VIP login successful - User: {data['user']['name']}, Role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
        print("✓ Invalid login correctly returns 401")
    
    def test_auth_me_requires_token(self):
        """Test /auth/me requires valid token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401 or response.status_code == 422
        print("✓ /auth/me correctly requires authentication")
    
    def test_auth_me_with_valid_token(self, auth_token):
        """Test /auth/me returns user info with valid token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "subscription" in data
        print(f"✓ /auth/me returns user: {data['name']}, subscription: {data['subscription']}")


class TestRegistrationAPI:
    """User registration tests"""
    
    def test_register_duplicate_email_fails(self):
        """Test registration with existing email fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": VIP_EMAIL,  # Existing user
                "password": "testpass123",
                "name": "Test User"
            },
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
        print("✓ Duplicate email registration correctly rejected")


class TestGalleryAPI:
    """Gallery loading tests - unified endpoint"""
    
    def test_unified_gallery_endpoint(self, auth_token):
        """Test Pro Studio unified gallery endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/gallery/unified",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "has_more" in data
        
        print(f"✓ Unified gallery loaded: {len(data['items'])} items, total: {data['total']}")
        
        # Check item structure if items exist
        if data['items']:
            item = data['items'][0]
            assert "id" in item
            assert "type" in item  # 'image', 'video', 'character'
            print(f"  Sample item type: {item['type']}")
    
    def test_unified_gallery_with_filter(self, auth_token):
        """Test gallery with filter type"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/gallery/unified?filter_type=images",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Filtered gallery (images): {len(data.get('items', []))} items")
    
    def test_unified_gallery_pagination(self, auth_token):
        """Test gallery pagination"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/gallery/unified?page=1&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get('items', [])) <= 10
        print(f"✓ Gallery pagination works: {len(data.get('items', []))} items (limit 10)")


class TestBooksAPI:
    """Book CRUD tests"""
    
    def test_get_books_public(self):
        """Test getting published books (public)"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public books endpoint: {len(data)} published books")
    
    def test_get_my_books(self, auth_token):
        """Test getting user's books (authenticated)"""
        response = requests.get(
            f"{BASE_URL}/api/books/my",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ My books: {len(data)} books for current user")
    
    def test_create_book(self, auth_token):
        """Test book creation flow"""
        response = requests.post(
            f"{BASE_URL}/api/books",
            json={
                "title": "TEST_Pre_Deployment_Book",
                "description": "Test book for pre-deployment verification",
                "genre": "Fantasy"
            },
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200, f"Book creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["title"] == "TEST_Pre_Deployment_Book"
        
        book_id = data["id"]
        print(f"✓ Book created successfully: {book_id}")
        
        # Verify book exists via GET
        get_response = requests.get(f"{BASE_URL}/api/books/{book_id}")
        assert get_response.status_code == 200
        print(f"✓ Book verified via GET")
        
        # Cleanup - delete test book
        delete_response = requests.delete(
            f"{BASE_URL}/api/books/{book_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200
        print(f"✓ Test book cleaned up")
    
    def test_get_featured_books(self):
        """Test featured books endpoint"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Featured books: {len(data)} books")


class TestProStudioAPI:
    """Pro Studio endpoints tests"""
    
    def test_get_characters(self, auth_token):
        """Test getting user's characters"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "characters" in data
        print(f"✓ Pro Studio characters: {len(data['characters'])} characters")
    
    def test_get_scenes(self, auth_token):
        """Test getting user's scenes"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/scenes",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "scenes" in data
        print(f"✓ Pro Studio scenes: {len(data['scenes'])} scenes")
    
    def test_get_character_styles(self):
        """Test getting character style options"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-styles")
        assert response.status_code == 200
        
        data = response.json()
        assert "styles" in data
        assert len(data["styles"]) > 0
        print(f"✓ Character styles: {len(data['styles'])} styles available")
    
    def test_get_character_genres(self):
        """Test getting character genre options"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-genres")
        assert response.status_code == 200
        
        data = response.json()
        assert "genres" in data
        assert len(data["genres"]) > 0
        print(f"✓ Character genres: {len(data['genres'])} genres available")
    
    def test_get_scene_options(self):
        """Test getting scene options"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/scene-options")
        assert response.status_code == 200
        
        data = response.json()
        # Check for expected keys
        assert any(key in data for key in ["location_types", "lighting", "moods"])
        print(f"✓ Scene options loaded successfully")


class TestCreditsAPI:
    """Credits balance and costs tests"""
    
    def test_get_credits_balance(self, auth_token):
        """Test getting user's credit balance"""
        response = requests.get(
            f"{BASE_URL}/api/credits/balance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "credits" in data
        assert "costs" in data
        
        print(f"✓ Credits balance: {data['credits']} credits")
        print(f"  Cost definitions: {len(data.get('costs', {}))} operation types")


class TestVoicesAndModels:
    """Test voices and model endpoints"""
    
    def test_get_voices(self):
        """Test getting available TTS voices"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check voice structure
        voice = data[0]
        assert "voice_id" in voice
        assert "name" in voice
        print(f"✓ Voices endpoint: {len(data)} voices available")
    
    def test_get_fal_models(self):
        """Test getting fal.ai model info"""
        response = requests.get(f"{BASE_URL}/api/fal/models")
        assert response.status_code == 200
        
        data = response.json()
        assert "available" in data
        print(f"✓ fal.ai availability: {data.get('available')}")


class TestStarterLibrary:
    """Test starter library endpoint"""
    
    def test_get_starter_library(self):
        """Test getting starter library books"""
        response = requests.get(f"{BASE_URL}/api/books/starter-library")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Starter library: {len(data)} books")


class TestVideosAPI:
    """Test video-related endpoints"""
    
    def test_get_videos(self, auth_token):
        """Test getting user's videos from Pro Studio"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/videos",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "videos" in data
        print(f"✓ Pro Studio videos: {len(data['videos'])} videos")


# Fixtures
@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for VIP user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": VIP_EMAIL, "password": VIP_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code != 200:
        pytest.skip(f"VIP login failed: {response.text}")
    
    return response.json().get("access_token")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
