"""
Iteration 29 Tests: UI/UX Changes
Testing:
1. Starter Library API endpoint returns images - GET /api/starter-library
2. Login flow with VIP account
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://studio-mobile-2.preview.emergentagent.com')

# VIP Test credentials
VIP_EMAIL = "jamesstephenbrooks@outlook.com"
VIP_PASSWORD = "test123"


class TestStarterLibraryAPI:
    """Starter Library endpoint tests"""
    
    def test_starter_library_returns_images(self):
        """Test that starter library returns images without auth"""
        response = requests.get(f"{BASE_URL}/api/starter-library")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "images" in data, "Response should have 'images' key"
        assert "total" in data, "Response should have 'total' key"
        assert len(data["images"]) >= 29, f"Expected at least 29 images, got {len(data['images'])}"
    
    def test_starter_library_image_structure(self):
        """Test that each starter image has correct structure"""
        response = requests.get(f"{BASE_URL}/api/starter-library")
        assert response.status_code == 200
        
        data = response.json()
        images = data["images"]
        
        # Check first image structure
        first_image = images[0]
        assert "id" in first_image, "Image should have 'id'"
        assert "url" in first_image, "Image should have 'url'"
        assert "name" in first_image, "Image should have 'name'"
        assert "category" in first_image, "Image should have 'category'"
        assert "tags" in first_image, "Image should have 'tags'"
        
        # Verify URL is valid
        assert first_image["url"].startswith("http"), "URL should be HTTP/HTTPS"
    
    def test_starter_library_category_filter(self):
        """Test filtering starter library by category"""
        # Test character category
        response = requests.get(f"{BASE_URL}/api/starter-library?category=character")
        assert response.status_code == 200
        
        data = response.json()
        for image in data["images"]:
            assert image["category"] == "character", f"All images should be characters, got {image['category']}"
        
        # Test scene category
        response = requests.get(f"{BASE_URL}/api/starter-library?category=scene")
        assert response.status_code == 200
        
        data = response.json()
        for image in data["images"]:
            assert image["category"] == "scene", f"All images should be scenes, got {image['category']}"


class TestVIPLogin:
    """VIP user login tests"""
    
    def test_vip_login_success(self):
        """Test VIP user can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "access_token" in data, "Response should have access_token"
        assert "user" in data, "Response should have user object"
        assert data["user"]["email"] == VIP_EMAIL, "Email should match"
        assert data["user"]["subscription"] == "pro", "VIP user should have pro subscription"
    
    def test_vip_user_is_admin(self):
        """Test VIP user has admin role"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "admin", "VIP user should have admin role"
    
    def test_vip_can_access_authenticated_endpoints(self):
        """Test VIP user can access protected endpoints"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Test /auth/me endpoint
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["email"] == VIP_EMAIL


class TestArtStudioGallery:
    """Art Studio Gallery tests (requires auth)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for VIP user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Login failed")
    
    def test_art_studio_gallery_loads(self, auth_token):
        """Test Art Studio gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/art-studio/gallery", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "images" in data, "Response should have 'images' key"


class TestBooksAPI:
    """Books API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for VIP user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Login failed")
    
    def test_get_my_books(self, auth_token):
        """Test getting user's books"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list of books"
