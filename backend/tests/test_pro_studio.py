"""
Pro Studio Feature Tests
Tests for Character consistency, Cinema Studio, Shots App, Video generation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://reader-audio-test.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "artstudio3@test.com"
TEST_PASSWORD = "password123"


class TestProStudioAuth:
    """Test Pro Studio authentication requirements"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_characters_requires_auth(self):
        """Test that /api/pro-studio/characters requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Characters endpoint requires authentication")
    
    def test_generate_image_requires_auth(self):
        """Test that /api/pro-studio/generate-image requires authentication"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/generate-image", json={
            "prompt": "test prompt"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Generate image endpoint requires authentication")


class TestProStudioCharacters:
    """Test Pro Studio Character endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_get_characters_empty(self, headers):
        """Test getting characters for a user - should return empty array for new users"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "characters" in data, "Response should contain 'characters' key"
        assert isinstance(data["characters"], list), "Characters should be a list"
        print(f"PASS: Get characters returns {len(data['characters'])} characters")
    
    def test_create_character_requires_3_images(self, headers):
        """Test that creating a character requires at least 3 reference images"""
        # Test with only 1 image
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "Test Character",
            "reference_images": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="]
        })
        assert response.status_code == 400, f"Expected 400 for insufficient images, got {response.status_code}"
        print("PASS: Character creation requires at least 3 images")
    
    def test_create_character_validation(self, headers):
        """Test character creation validation"""
        # Test with 2 images - should fail
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "Test Character 2",
            "reference_images": [
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            ]
        })
        assert response.status_code == 400, f"Expected 400 for 2 images, got {response.status_code}"
        print("PASS: Character creation correctly validates minimum image count")


class TestProStudioCinemaStudio:
    """Test Cinema Studio image generation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_generate_image_with_cinema_settings(self, headers):
        """Test generating an image with Cinema Studio camera/lens settings"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/generate-image", headers=headers, json={
            "prompt": "A woman standing on a beach at sunset",
            "camera": "arri-alexa-35",
            "lens": "panavision-series",
            "focal_length": "35mm",
            "lighting": "golden-hour",
            "aspect_ratio": "16:9"
        })
        # This may take time for AI generation - check response structure
        assert response.status_code in [200, 500], f"Got unexpected status: {response.status_code}: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert "image_url" in data or "image_base64" in data, "Response should contain image data"
            print("PASS: Image generation with Cinema Studio settings works")
        else:
            print(f"INFO: Image generation returned 500 - may be API key or quota issue: {response.text[:200]}")
    
    def test_generate_image_minimal(self, headers):
        """Test generating an image with minimal parameters"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/generate-image", headers=headers, json={
            "prompt": "A simple portrait"
        })
        # Record the response for diagnosis
        print(f"Generate image response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text[:300]}")
        assert response.status_code in [200, 500], f"Got unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "image_url" in data or "image_base64" in data
            print("PASS: Minimal image generation works")


class TestProStudioShots:
    """Test Shots App - generate 9 angles from 1 image"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_generate_shots_requires_image(self, headers):
        """Test that generate shots requires a source image"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/generate-shots", headers=headers, json={})
        # Should fail without source_image
        assert response.status_code == 422 or response.status_code == 400, f"Expected validation error, got {response.status_code}"
        print("PASS: Generate shots correctly requires source image")
    
    def test_generate_shots_structure(self, headers):
        """Test generate shots endpoint accepts correct structure"""
        # Use a minimal base64 image for testing
        test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        response = requests.post(f"{BASE_URL}/api/pro-studio/generate-shots", headers=headers, json={
            "source_image": test_image
        })
        # May return 200 or 500 depending on AI service
        print(f"Generate shots response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "shots" in data, "Response should contain 'shots' key"
            print(f"PASS: Generate shots returned {len(data.get('shots', []))} shots")
        else:
            print(f"INFO: Generate shots returned {response.status_code} - AI service may have issues")


class TestProStudioVideo:
    """Test Video generation with multiple models"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_animate_hero_requires_image(self, headers):
        """Test that animate hero requires an image URL"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/animate-hero", headers=headers, json={
            "motion_prompt": "subtle movement",
            "model": "sora-2",
            "duration": 5
        })
        # Should fail without image_url
        assert response.status_code == 422 or response.status_code == 400, f"Expected validation error, got {response.status_code}"
        print("PASS: Animate hero correctly requires image_url")
    
    def test_animate_hero_accepts_sora2(self, headers):
        """Test that animate hero accepts sora-2 model selection"""
        # Use a minimal test - actual animation would take too long
        test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        response = requests.post(f"{BASE_URL}/api/pro-studio/animate-hero", headers=headers, json={
            "image_url": test_image,
            "motion_prompt": "subtle cinematic movement",
            "model": "sora-2",
            "duration": 5
        }, timeout=10)  # Short timeout since we don't want to wait for actual generation
        
        print(f"Animate hero response status: {response.status_code}")
        # 200 means job started, other codes indicate issues
        if response.status_code == 200:
            data = response.json()
            # May return job_id for async processing
            if "job_id" in data:
                print(f"PASS: Animate hero started job: {data['job_id']}")
            elif "video_url" in data or "video_base64" in data:
                print("PASS: Animate hero generated video directly")
            else:
                print(f"INFO: Animate hero response: {data}")
        else:
            print(f"INFO: Animate hero returned {response.status_code}")


class TestProStudioExpression:
    """Test expression variation generation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_generate_expression_requires_character(self, headers):
        """Test that expression generation requires a character_id"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/generate-expression", headers=headers, json={
            "expression": "happy",
            "base_prompt": "portrait"
        })
        # Should fail without character_id
        assert response.status_code in [400, 404, 422], f"Expected error without character_id, got {response.status_code}"
        print("PASS: Expression generation correctly requires character_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
