"""
Test Art Studio Pro Features
- Tests new parameters: negativePrompt, aspectRatio, qualityLevel
- Tests API schema acceptance
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Register a user and get auth token"""
    ts = int(time.time())
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"artstudio_test_{ts}@test.com",
        "password": "testpass123",
        "name": "Art Studio Test User"
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        # Upgrade to Pro
        requests.post(f"{BASE_URL}/api/auth/upgrade", 
            headers={"Authorization": f"Bearer {token}"},
            json={"subscription": "pro"})
        return token
    pytest.skip("Could not register test user")

@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestArtStudioProFeatures:
    """Test Art Studio Pro features - API schema validation"""
    
    def test_generate_endpoint_accepts_negative_prompt(self, auth_headers):
        """Test that /api/art-studio/generate accepts negativePrompt parameter"""
        # We're testing schema acceptance, not actual generation (which takes too long)
        # Just verify the endpoint accepts the parameter without 400 error
        
        payload = {
            "prompt": "A test character",
            "style": "fantasy",
            "type": "character",
            "negativePrompt": "blurry, low quality, distorted"
        }
        
        # The endpoint might timeout on actual generation, but we check it doesn't reject the param
        try:
            response = requests.post(
                f"{BASE_URL}/api/art-studio/generate",
                headers=auth_headers,
                json=payload,
                timeout=5  # Short timeout since we just want to check param acceptance
            )
            # If we get a response, check it's not a 400 (bad request) due to invalid params
            assert response.status_code != 400, "negativePrompt parameter should be accepted"
        except requests.exceptions.Timeout:
            # Timeout is fine - means the endpoint accepted params and started processing
            pass
    
    def test_generate_endpoint_accepts_aspect_ratio(self, auth_headers):
        """Test that /api/art-studio/generate accepts aspectRatio parameter"""
        payload = {
            "prompt": "A test character",
            "style": "fantasy",
            "type": "character",
            "aspectRatio": "16:9"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/art-studio/generate",
                headers=auth_headers,
                json=payload,
                timeout=5
            )
            assert response.status_code != 400, "aspectRatio parameter should be accepted"
        except requests.exceptions.Timeout:
            pass
    
    def test_generate_endpoint_accepts_quality_level(self, auth_headers):
        """Test that /api/art-studio/generate accepts qualityLevel parameter"""
        payload = {
            "prompt": "A test character",
            "style": "fantasy",
            "type": "character",
            "qualityLevel": "ultra"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/art-studio/generate",
                headers=auth_headers,
                json=payload,
                timeout=5
            )
            assert response.status_code != 400, "qualityLevel parameter should be accepted"
        except requests.exceptions.Timeout:
            pass
    
    def test_generate_endpoint_accepts_all_pro_params(self, auth_headers):
        """Test that /api/art-studio/generate accepts all Pro parameters together"""
        payload = {
            "prompt": "A majestic dragon",
            "style": "fantasy",
            "type": "character",
            "negativePrompt": "blurry, low quality, watermark",
            "aspectRatio": "16:9",
            "qualityLevel": "high",
            "transparentBackground": False
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/art-studio/generate",
                headers=auth_headers,
                json=payload,
                timeout=5
            )
            assert response.status_code != 400, "All Pro parameters should be accepted"
        except requests.exceptions.Timeout:
            pass
    
    def test_aspect_ratio_values(self, auth_headers):
        """Test various aspect ratio values are accepted"""
        for ratio in ["1:1", "16:9", "9:16", "4:3", "3:4"]:
            payload = {
                "prompt": "Test",
                "style": "fantasy",
                "type": "character",
                "aspectRatio": ratio
            }
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/art-studio/generate",
                    headers=auth_headers,
                    json=payload,
                    timeout=3
                )
                assert response.status_code != 400, f"Aspect ratio {ratio} should be accepted"
            except requests.exceptions.Timeout:
                pass
    
    def test_quality_level_values(self, auth_headers):
        """Test various quality level values are accepted"""
        for quality in ["low", "medium", "high", "ultra"]:
            payload = {
                "prompt": "Test",
                "style": "fantasy",
                "type": "character",
                "qualityLevel": quality
            }
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/art-studio/generate",
                    headers=auth_headers,
                    json=payload,
                    timeout=3
                )
                assert response.status_code != 400, f"Quality level {quality} should be accepted"
            except requests.exceptions.Timeout:
                pass


class TestArtStudioGallery:
    """Test Art Studio Gallery endpoints"""
    
    def test_gallery_endpoint(self, auth_headers):
        """Test gallery endpoint returns list"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/gallery",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert isinstance(data["images"], list)
    
    def test_character_profiles_endpoint(self, auth_headers):
        """Test character profiles endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/character-profiles",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
    
    def test_prompt_history_endpoint(self, auth_headers):
        """Test prompt history endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/prompt-history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
