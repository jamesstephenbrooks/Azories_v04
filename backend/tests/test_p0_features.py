"""
P0 Features Backend API Tests
Tests for:
1. Veo 3.1 API Integration - video generation model availability
2. Pro Studio endpoints - animate-hero with model parameter
3. Character gallery endpoints
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://character-studio-dev.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "jamesstephenbrooks@outlook.com"
TEST_PASSWORD = "Routetofreedom"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers for API requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealthEndpoints:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test basic health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ Health endpoint working")


class TestAuthFlow:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print("✅ Login successful")
    
    def test_get_current_user(self, auth_headers):
        """Test getting current user info"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print("✅ Get current user working")


class TestProStudioEndpoints:
    """Pro Studio feature tests"""
    
    def test_character_styles(self):
        """Test character styles endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-styles")
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        print(f"✅ Character styles: {len(data['styles'])} styles available")
    
    def test_character_genres(self):
        """Test character genres endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-genres")
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        print(f"✅ Character genres: {len(data['genres'])} genres available")
    
    def test_scene_options(self):
        """Test scene options endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/scene-options")
        assert response.status_code == 200
        data = response.json()
        assert "location_types" in data or "lighting" in data or "moods" in data
        print("✅ Scene options endpoint working")
    
    def test_get_characters(self, auth_headers):
        """Test getting user's characters"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        print(f"✅ Characters endpoint: {len(data['characters'])} characters found")
        return data["characters"]
    
    def test_get_scenes(self, auth_headers):
        """Test getting user's scenes"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/scenes",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "scenes" in data
        print(f"✅ Scenes endpoint: {len(data['scenes'])} scenes found")


class TestVideoModels:
    """Video model configuration tests"""
    
    def test_fal_models_endpoint(self):
        """Test fal.ai models endpoint - checks video model availability"""
        response = requests.get(f"{BASE_URL}/api/fal/models")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ fal.ai available: {data.get('available', False)}")
        print(f"   Models: {data.get('models', [])}")


class TestVeo31Integration:
    """Tests for Veo 3.1 video model integration"""
    
    def test_animate_hero_endpoint_accepts_veo31(self, auth_headers):
        """
        Test that animate-hero endpoint accepts 'veo-3.1' model parameter
        Note: We test the endpoint accepts the request, not the actual generation
        (which requires credits and takes time)
        """
        # This test verifies the endpoint accepts the veo-3.1 model
        # We expect either:
        # - 200/202 if VEO3 is configured
        # - 503 if VEO3 is not configured (but the model is recognized)
        # - 400 if model is not recognized (this would be a failure)
        
        # Use a test image URL (small placeholder)
        test_data = {
            "image_url": "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
            "motion_prompt": "subtle movement test",
            "model": "veo-3.1",
            "duration": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/animate-hero",
            headers=auth_headers,
            json=test_data
        )
        
        # The endpoint should recognize veo-3.1 as a valid model
        # 402 = Insufficient credits (valid endpoint, needs credits)
        # 503 = Service not available (Veo 3 not configured, but model recognized)
        # 200/202 = Success (task started)
        # 400/422 = Bad request (model not recognized - this would be a failure)
        
        assert response.status_code in [200, 202, 402, 503], \
            f"Unexpected status {response.status_code}: {response.text}"
        
        if response.status_code == 402:
            print("✅ Veo 3.1 model recognized - needs credits")
        elif response.status_code == 503:
            data = response.json()
            if "Veo" in str(data.get("detail", "")):
                print("✅ Veo 3.1 model recognized - service not configured")
            else:
                print(f"⚠️ Service unavailable: {data.get('detail')}")
        elif response.status_code in [200, 202]:
            print("✅ Veo 3.1 video generation started successfully")
            data = response.json()
            print(f"   Task ID: {data.get('task_id')}")
        
        return response.status_code


class TestCharacterGallery:
    """Tests for character folder/gallery with video thumbnails"""
    
    def test_unified_gallery_endpoint(self, auth_headers):
        """Test the unified gallery endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/gallery/unified?page=1&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✅ Unified gallery: {len(data['items'])} items, total: {data.get('total', 0)}")
        
        # Check for video items
        videos = [item for item in data["items"] if item.get("type") == "video"]
        print(f"   Videos in gallery: {len(videos)}")
        
        return data
    
    def test_character_gallery_with_videos(self, auth_headers):
        """Test getting character gallery which may contain videos"""
        # First get characters
        char_response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters",
            headers=auth_headers
        )
        assert char_response.status_code == 200
        characters = char_response.json().get("characters", [])
        
        if not characters:
            print("⚠️ No characters found to test gallery")
            return
        
        # Test gallery for first character
        char_id = characters[0]["id"]
        gallery_response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters/{char_id}/gallery",
            headers=auth_headers
        )
        assert gallery_response.status_code == 200
        data = gallery_response.json()
        print(f"✅ Character gallery for '{characters[0]['name']}': {len(data.get('images', []))} items")
        
        # Check for video items with thumbnails
        for item in data.get("images", []):
            if item.get("type") == "video":
                has_thumbnail = bool(item.get("thumbnail_url"))
                print(f"   Video item: thumbnail_url present = {has_thumbnail}")


class TestExpressionGeneration:
    """Tests for expression generation endpoint"""
    
    def test_expression_endpoint_exists(self, auth_headers):
        """Test that expression generation endpoint is available"""
        # Get a character first
        char_response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters",
            headers=auth_headers
        )
        characters = char_response.json().get("characters", [])
        
        if not characters:
            pytest.skip("No characters available for expression test")
        
        char_id = characters[0]["id"]
        
        # Test the endpoint with minimal data
        # We expect 402 (no credits) or 200 (success) - both mean endpoint works
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/generate-expression",
            headers=auth_headers,
            json={
                "character_id": char_id,
                "expression": "happy",
                "base_prompt": "portrait test"
            }
        )
        
        # 402 = needs credits but endpoint works
        # 200 = success
        # 400/404 = endpoint issue
        assert response.status_code in [200, 402], \
            f"Expression endpoint issue: {response.status_code} - {response.text}"
        
        if response.status_code == 402:
            print("✅ Expression endpoint works - needs credits")
        else:
            print("✅ Expression generation successful")
            data = response.json()
            # Verify auto-save happened
            if data.get("auto_saved") or "image_url" in data:
                print("   Image generated and auto-saved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
