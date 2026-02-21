"""
Test Art Studio API endpoints
- /api/art-studio/generate - Generate AI images for characters/scenes
- /api/art-studio/gallery - Get user's gallery
- /api/art-studio/save - Save image to gallery
- /api/art-studio/gallery/{image_id} - Delete from gallery
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials provided
TEST_USER = {
    "email": "artstudio3@test.com",
    "password": "password123",
    "subscription": "pro"
}


class TestArtStudioAPI:
    """Art Studio API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        token_data = login_response.json()
        self.token = token_data["access_token"]
        self.user = token_data["user"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Verify user has pro subscription
        assert self.user["subscription"] == "pro", f"User should have pro subscription, got: {self.user['subscription']}"
        print(f"✓ Logged in as {self.user['email']} with {self.user['subscription']} subscription")
    
    def test_auth_me_endpoint(self):
        """Test /api/auth/me returns user info"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["email"] == TEST_USER["email"]
        assert data["subscription"] == "pro"
        print(f"✓ Auth me endpoint working - user: {data['email']}, subscription: {data['subscription']}")
    
    def test_art_studio_gallery_get(self):
        """Test /api/art-studio/gallery endpoint returns user's gallery"""
        response = self.session.get(f"{BASE_URL}/api/art-studio/gallery")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data, "Response should have 'images' key"
        assert isinstance(data["images"], list), "images should be a list"
        print(f"✓ Gallery endpoint working - {len(data['images'])} images in gallery")
    
    def test_art_studio_generate_character(self):
        """Test /api/art-studio/generate endpoint for character generation"""
        payload = {
            "prompt": "Female character, young adult age, average body type, medium skin tone, brown long hair, brown eyes, fantasy clothing style, confident expression",
            "style": "fantasy",
            "type": "character",
            "characterData": {
                "name": "Test Character",
                "gender": "Female",
                "ageGroup": "Young Adult",
                "bodyType": "Average",
                "skinTone": "Medium",
                "hairColor": "Brown",
                "hairStyle": "Long",
                "eyeColor": "Brown",
                "clothing": "Fantasy",
                "expression": "Confident"
            },
            "sceneData": None
        }
        
        print("Generating AI character image (this may take 30-60 seconds)...")
        response = self.session.post(f"{BASE_URL}/api/art-studio/generate", json=payload, timeout=120)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "image_url" in data, "Response should have 'image_url' key"
        assert data["image_url"].startswith("data:image/png;base64,"), "image_url should be base64 PNG"
        assert "prompt_used" in data, "Response should have 'prompt_used' key"
        print(f"✓ Character image generated successfully!")
        print(f"  Prompt used: {data['prompt_used'][:100]}...")
        
        # Store for cleanup
        self.generated_image_url = data["image_url"]
    
    def test_art_studio_generate_scene(self):
        """Test /api/art-studio/generate endpoint for scene generation"""
        payload = {
            "prompt": "magical forest with glowing flowers and mystical lighting, day time, clear weather, peaceful atmosphere",
            "style": "watercolor",
            "type": "scene",
            "characterData": None,
            "sceneData": {
                "preset": "forest",
                "customPrompt": "magical forest with glowing flowers",
                "timeOfDay": "day",
                "weather": "clear",
                "mood": "peaceful"
            }
        }
        
        print("Generating AI scene image (this may take 30-60 seconds)...")
        response = self.session.post(f"{BASE_URL}/api/art-studio/generate", json=payload, timeout=120)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "image_url" in data, "Response should have 'image_url' key"
        assert data["image_url"].startswith("data:image/png;base64,"), "image_url should be base64 PNG"
        print(f"✓ Scene image generated successfully!")
    
    def test_art_studio_generate_without_auth(self):
        """Test /api/art-studio/generate fails without auth"""
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        payload = {
            "prompt": "test character",
            "style": "fantasy",
            "type": "character"
        }
        
        response = no_auth_session.post(f"{BASE_URL}/api/art-studio/generate", json=payload)
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✓ Generate endpoint correctly requires authentication")
    
    def test_art_studio_gallery_without_auth(self):
        """Test /api/art-studio/gallery fails without auth"""
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/art-studio/gallery")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✓ Gallery endpoint correctly requires authentication")


class TestArtStudioSaveAndDelete:
    """Test save and delete operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        token_data = login_response.json()
        self.token = token_data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_art_studio_save_and_verify(self):
        """Test saving an image to gallery and verifying it appears"""
        # Sample base64 image (small test image)
        test_image_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        save_payload = {
            "image_url": test_image_url,
            "name": "TEST_ArtStudio_Save",
            "type": "character",
            "style": "fantasy",
            "characterData": {"name": "Test"},
            "sceneData": None
        }
        
        # Save to gallery
        response = self.session.post(f"{BASE_URL}/api/art-studio/save", json=save_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "id" in data
        saved_id = data["id"]
        print(f"✓ Image saved to gallery with ID: {saved_id}")
        
        # Verify it appears in gallery
        gallery_response = self.session.get(f"{BASE_URL}/api/art-studio/gallery")
        assert gallery_response.status_code == 200
        gallery_data = gallery_response.json()
        
        # Find the saved image
        saved_images = [img for img in gallery_data["images"] if img.get("name") == "TEST_ArtStudio_Save"]
        assert len(saved_images) > 0, "Saved image should appear in gallery"
        print(f"✓ Saved image verified in gallery")
        
        # Store for cleanup
        self.saved_image_id = saved_id
        
        # Delete the test image
        delete_response = self.session.delete(f"{BASE_URL}/api/art-studio/gallery/{saved_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"✓ Test image deleted from gallery")
        
        # Verify deletion
        gallery_response2 = self.session.get(f"{BASE_URL}/api/art-studio/gallery")
        gallery_data2 = gallery_response2.json()
        remaining = [img for img in gallery_data2["images"] if img.get("_id") == saved_id]
        assert len(remaining) == 0, "Deleted image should not appear in gallery"
        print(f"✓ Deletion verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
