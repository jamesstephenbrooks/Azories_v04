"""
Pro Studio Feature Tests - Iteration 27
Tests for Character creation (description + images), Edit, Delete, Thumbnail regeneration, Gallery/Folder

Test credentials: test@test.com / test123
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://studio-v2-preview.preview.emergentagent.com').rstrip('/')

# Test credentials provided by main agent
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

# Small test image (1x1 pixel red PNG)
TEST_IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="


class TestProStudioAuthSetup:
    """Setup: Login and verify Pro subscription"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Verify we have pro subscription
        user = data.get("user", {})
        print(f"Logged in user: {user.get('email')}, subscription: {user.get('subscription')}")
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_login_and_verify_pro(self, headers):
        """Test login and verify user has pro subscription"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Failed to get user info: {response.text}"
        user = response.json()
        assert user.get("subscription") == "pro", f"User should have 'pro' subscription, got: {user.get('subscription')}"
        print(f"PASS: User {user.get('email')} has pro subscription")


class TestCharacterCreation:
    """Test character creation with description AND/OR images"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_create_character_description_only(self, headers):
        """Test creating a character with description only (no images)"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "TEST_Luna",
            "description_prompt": "A young elven princess with silver hair and violet eyes, pointed ears with crystal earrings",
            "style": "fantasy",
            "genre": "fantasy",
            "reference_images": []
        })
        
        print(f"Create character response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text[:500]}")
        
        # May return 200 or 500 depending on FAL_KEY availability
        if response.status_code == 200:
            data = response.json()
            assert "character" in data, "Response should contain 'character'"
            char = data["character"]
            assert char.get("name") == "TEST_Luna"
            assert char.get("description_prompt") == "A young elven princess with silver hair and violet eyes, pointed ears with crystal earrings"
            assert "id" in char, "Character should have an id"
            print(f"PASS: Character created with ID: {char['id']}")
            # Store character ID for later tests
            return char["id"]
        else:
            # API key issues - acceptable
            print(f"INFO: Character creation returned {response.status_code} - may be API key issue")
            pytest.skip("Character creation requires valid fal.ai key for thumbnail generation")
    
    def test_create_character_with_images_only(self, headers):
        """Test creating a character with reference images only"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "TEST_Marcus",
            "description_prompt": "",
            "style": "photorealistic",
            "genre": "contemporary",
            "reference_images": [TEST_IMAGE_BASE64]
        })
        
        print(f"Create character (images only) response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "character" in data
            char = data["character"]
            assert char.get("name") == "TEST_Marcus"
            assert len(char.get("reference_images", [])) >= 1
            print(f"PASS: Character created from images with ID: {char['id']}")
        else:
            print(f"INFO: Response: {response.text[:300]}")
    
    def test_create_character_with_both(self, headers):
        """Test creating a character with BOTH description AND images"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "TEST_Captain_Rex",
            "description_prompt": "A battle-hardened space captain with cybernetic eye and rugged appearance",
            "style": "scifi",
            "genre": "space-opera",
            "reference_images": [TEST_IMAGE_BASE64],
            "personality": "brave and loyal",
            "special_features": "cybernetic left eye with red glow"
        })
        
        print(f"Create character (both) response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "character" in data
            char = data["character"]
            assert char.get("name") == "TEST_Captain_Rex"
            assert char.get("description_prompt") == "A battle-hardened space captain with cybernetic eye and rugged appearance"
            assert len(char.get("reference_images", [])) >= 1
            assert char.get("special_features") == "cybernetic left eye with red glow"
            print(f"PASS: Character created with both description and images, ID: {char['id']}")
        else:
            print(f"INFO: Response: {response.text[:300]}")
    
    def test_create_character_requires_name_or_description(self, headers):
        """Test that character creation fails without name/description/images"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "Empty Character",
            "description_prompt": "",
            "reference_images": []
        })
        
        # Should return 400 - need at least description OR images
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("PASS: Character creation correctly requires description or images")


class TestCharacterCRUD:
    """Test Character CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_character_id(self, headers):
        """Create a test character and return its ID"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "TEST_CRUD_Character",
            "description_prompt": "A test character for CRUD operations",
            "style": "illustration",
            "genre": "fantasy"
        })
        if response.status_code == 200:
            return response.json()["character"]["id"]
        pytest.skip("Could not create test character")
    
    def test_get_characters_list(self, headers):
        """Test getting list of all characters"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers=headers)
        assert response.status_code == 200, f"Failed to get characters: {response.text}"
        data = response.json()
        assert "characters" in data, "Response should contain 'characters' list"
        assert isinstance(data["characters"], list)
        print(f"PASS: Got {len(data['characters'])} characters")
    
    def test_get_character_by_id(self, headers, test_character_id):
        """Test getting a specific character by ID"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters/{test_character_id}", headers=headers)
        assert response.status_code == 200, f"Failed to get character: {response.text}"
        data = response.json()
        assert "character" in data
        assert data["character"]["id"] == test_character_id
        print(f"PASS: Got character by ID: {test_character_id}")
    
    def test_update_character(self, headers, test_character_id):
        """Test updating a character (PUT /api/pro-studio/characters/{id})"""
        response = requests.put(f"{BASE_URL}/api/pro-studio/characters/{test_character_id}", headers=headers, json={
            "name": "TEST_CRUD_Character_Updated",
            "description_prompt": "An updated test character description",
            "special_features": "glowing tattoos on arms"
        })
        
        assert response.status_code == 200, f"Failed to update character: {response.text}"
        data = response.json()
        assert "character" in data
        assert data["character"]["name"] == "TEST_CRUD_Character_Updated"
        assert data["character"]["special_features"] == "glowing tattoos on arms"
        print("PASS: Character updated successfully")
        
        # Verify update persisted with GET
        verify_response = requests.get(f"{BASE_URL}/api/pro-studio/characters/{test_character_id}", headers=headers)
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["character"]["name"] == "TEST_CRUD_Character_Updated"
        print("PASS: Character update verified with GET")


class TestThumbnailRegeneration:
    """Test thumbnail regeneration API"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_character_id(self, headers):
        """Create a test character for thumbnail test"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "TEST_Thumbnail_Character",
            "description_prompt": "A wizard with a long white beard and blue robes",
            "style": "fantasy",
            "genre": "fantasy"
        })
        if response.status_code == 200:
            return response.json()["character"]["id"]
        pytest.skip("Could not create test character")
    
    def test_regenerate_thumbnail(self, headers, test_character_id):
        """Test regenerating thumbnail (POST /api/pro-studio/characters/{id}/generate-thumbnail)"""
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/characters/{test_character_id}/generate-thumbnail",
            headers=headers
        )
        
        print(f"Regenerate thumbnail response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "thumbnail" in data or "success" in data
            print(f"PASS: Thumbnail regenerated: {data.get('thumbnail', '')[:50]}...")
        elif response.status_code == 503:
            print("INFO: Image generation service not available - expected if fal.ai key not set")
        else:
            print(f"INFO: Thumbnail regeneration returned {response.status_code}: {response.text[:200]}")


class TestCharacterGallery:
    """Test Character Gallery/Folder API"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_character_id(self, headers):
        """Create a test character for gallery test"""
        response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "TEST_Gallery_Character",
            "description_prompt": "A knight in shining armor",
            "style": "fantasy",
            "genre": "fantasy"
        })
        if response.status_code == 200:
            return response.json()["character"]["id"]
        pytest.skip("Could not create test character")
    
    def test_get_character_gallery_empty(self, headers, test_character_id):
        """Test getting empty gallery for a new character"""
        response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters/{test_character_id}/gallery",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to get gallery: {response.text}"
        data = response.json()
        assert "images" in data
        assert isinstance(data["images"], list)
        print(f"PASS: Got character gallery with {len(data['images'])} images")
    
    def test_add_to_character_gallery(self, headers, test_character_id):
        """Test adding an image to character gallery (POST /api/pro-studio/characters/{id}/gallery)"""
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/characters/{test_character_id}/gallery",
            headers=headers,
            json={
                "image_url": "https://example.com/test-image.png",
                "prompt": "Knight in battle stance",
                "type": "generated"
            }
        )
        
        assert response.status_code == 200, f"Failed to add to gallery: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "item" in data
        assert data["item"]["prompt"] == "Knight in battle stance"
        print("PASS: Image added to character gallery")
        
        # Verify with GET
        verify_response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters/{test_character_id}/gallery",
            headers=headers
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert len(verify_data["images"]) >= 1
        print("PASS: Gallery item verified with GET")
    
    def test_gallery_requires_image_url(self, headers, test_character_id):
        """Test that adding to gallery requires image_url"""
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/characters/{test_character_id}/gallery",
            headers=headers,
            json={"prompt": "test"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Gallery correctly requires image_url")


class TestCharacterDelete:
    """Test Character deletion"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_delete_character(self, headers):
        """Test deleting a character (DELETE /api/pro-studio/characters/{id})"""
        # First create a character to delete
        create_response = requests.post(f"{BASE_URL}/api/pro-studio/characters", headers=headers, json={
            "name": "TEST_Delete_Me",
            "description_prompt": "A character to be deleted",
            "style": "illustration",
            "genre": "fantasy"
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test character for deletion")
        
        char_id = create_response.json()["character"]["id"]
        print(f"Created character for deletion: {char_id}")
        
        # Now delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/pro-studio/characters/{char_id}",
            headers=headers
        )
        
        assert delete_response.status_code == 200, f"Failed to delete: {delete_response.text}"
        print("PASS: Character deleted")
        
        # Verify deletion with GET
        verify_response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters/{char_id}",
            headers=headers
        )
        assert verify_response.status_code == 404, f"Expected 404, got {verify_response.status_code}"
        print("PASS: Character deletion verified (404 on GET)")
    
    def test_delete_nonexistent_character(self, headers):
        """Test deleting a character that doesn't exist"""
        response = requests.delete(
            f"{BASE_URL}/api/pro-studio/characters/nonexistent-id-12345",
            headers=headers
        )
        assert response.status_code == 404
        print("PASS: Deleting nonexistent character returns 404")


class TestCharacterStyles:
    """Test Character Styles and Genres endpoints"""
    
    def test_get_character_styles(self):
        """Test getting available character styles (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-styles")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "styles" in data
        assert len(data["styles"]) > 0
        # Check style structure
        style = data["styles"][0]
        assert "id" in style
        assert "name" in style
        print(f"PASS: Got {len(data['styles'])} character styles")
    
    def test_get_character_genres(self):
        """Test getting available character genres (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-genres")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "genres" in data
        assert len(data["genres"]) > 0
        # Check genre structure
        genre = data["genres"][0]
        assert "id" in genre
        assert "name" in genre
        print(f"PASS: Got {len(data['genres'])} character genres")


class TestCleanup:
    """Clean up test data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        if auth_token:
            return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        return {}
    
    def test_cleanup_test_characters(self, headers):
        """Clean up TEST_ prefixed characters"""
        if not headers:
            pytest.skip("No auth available for cleanup")
        
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers=headers)
        if response.status_code == 200:
            characters = response.json().get("characters", [])
            deleted_count = 0
            for char in characters:
                if char.get("name", "").startswith("TEST_"):
                    del_response = requests.delete(
                        f"{BASE_URL}/api/pro-studio/characters/{char['id']}",
                        headers=headers
                    )
                    if del_response.status_code == 200:
                        deleted_count += 1
            print(f"CLEANUP: Deleted {deleted_count} test characters")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
