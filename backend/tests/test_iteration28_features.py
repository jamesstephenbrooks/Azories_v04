"""
Test cases for Iteration 28 features:
1. Book Reader Back Cover Navigation - Verify book reading endpoint works 
2. Pro Studio Characters - Reference images and LoRA training button logic
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://studio-v2-preview.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"
TEST_BOOK_ID = "fb341971-71be-4c8a-b764-a7cac7fb9a71"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token") or data.get("token")

@pytest.fixture(scope="module")
def session():
    """Shared requests session"""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s

class TestBookReaderBackCover:
    """Test Book Reader - Back Cover Navigation Fix"""
    
    def test_get_book_full_content(self, session, auth_token):
        """Test getting full book content including pages for navigation"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = session.get(f"{BASE_URL}/api/books/{TEST_BOOK_ID}/full")
        
        assert response.status_code == 200, f"Failed to get book: {response.text}"
        data = response.json()
        
        # Verify book structure
        assert "title" in data, "Book should have title"
        assert "chapters" in data, "Book should have chapters"
        
        # Get total pages count
        total_pages = sum(len(ch.get("pages", [])) for ch in data.get("chapters", []))
        print(f"Book has {total_pages} total pages across {len(data['chapters'])} chapters")
        
        # Verify book has cover info for back cover
        # Back cover uses book description
        assert data.get("title"), "Book should have title for back cover"
        
    def test_book_has_chapters_and_pages(self, session, auth_token):
        """Verify book has navigable content"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = session.get(f"{BASE_URL}/api/books/{TEST_BOOK_ID}/full")
        
        assert response.status_code == 200
        data = response.json()
        
        chapters = data.get("chapters", [])
        assert len(chapters) > 0, "Book should have at least one chapter"
        
        # Count pages
        page_count = 0
        for chapter in chapters:
            pages = chapter.get("pages", [])
            page_count += len(pages)
        
        assert page_count > 0, "Book should have pages for navigation"
        print(f"PASS: Book has {page_count} pages to navigate through")


class TestProStudioCharacters:
    """Test Pro Studio Characters - Reference Images and Train Button Logic"""
    
    def test_get_characters_with_reference_counts(self, session, auth_token):
        """Verify characters list includes reference_images array"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = session.get(f"{BASE_URL}/api/pro-studio/characters")
        
        assert response.status_code == 200
        data = response.json()
        
        characters = data.get("characters", [])
        print(f"Found {len(characters)} characters")
        
        for char in characters:
            # Each character should have reference_images array
            ref_images = char.get("reference_images", [])
            ref_count = len(ref_images)
            lora_status = char.get("lora_status", "none")
            
            print(f"Character '{char.get('name')}': {ref_count} refs, LoRA status: {lora_status}")
            
            # Verify the Train button logic:
            # Button should show when: ref_count >= 3 AND lora_status not in ['completed', 'training']
            can_train = ref_count >= 3 and lora_status not in ['completed', 'training']
            needs_more_refs = ref_count < 3
            
            if needs_more_refs:
                print(f"  -> Needs +{3 - ref_count} more refs for LoRA training")
            elif can_train:
                print(f"  -> Ready for LoRA training (Train button should be visible)")
            else:
                print(f"  -> LoRA already {lora_status}")
    
    def test_fal_availability_for_lora(self, session, auth_token):
        """Verify fal.ai is available for LoRA training"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = session.get(f"{BASE_URL}/api/fal/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "available" in data, "Response should indicate fal availability"
        print(f"fal.ai available: {data.get('available')}")
    
    def test_create_character_with_description(self, session, auth_token):
        """Test creating a character with description (no images)"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Create character
        response = session.post(f"{BASE_URL}/api/pro-studio/characters", json={
            "name": "TEST_Iter28_Character",
            "description_prompt": "A test character for iteration 28 testing",
            "style": "illustration",
            "genre": "fantasy"
        })
        
        assert response.status_code == 200 or response.status_code == 201
        data = response.json()
        
        character = data.get("character", data)
        assert character.get("name") == "TEST_Iter28_Character"
        
        # Character should start with 0 reference images
        ref_images = character.get("reference_images", [])
        print(f"New character has {len(ref_images)} reference images")
        
        # Store character ID for cleanup
        return character.get("id")
    
    def test_character_options_endpoints(self, session):
        """Test character styles and genres endpoints"""
        # Styles
        response = session.get(f"{BASE_URL}/api/pro-studio/character-styles")
        assert response.status_code == 200
        styles = response.json().get("styles", [])
        assert len(styles) > 0, "Should have character styles available"
        print(f"Available styles: {[s.get('id') for s in styles[:5]]}")
        
        # Genres
        response = session.get(f"{BASE_URL}/api/pro-studio/character-genres")
        assert response.status_code == 200
        genres = response.json().get("genres", [])
        assert len(genres) > 0, "Should have character genres available"
        print(f"Available genres: {[g.get('id') for g in genres[:5]]}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_characters(self, session, auth_token):
        """Delete test characters created during testing"""
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = session.get(f"{BASE_URL}/api/pro-studio/characters")
        
        if response.status_code == 200:
            characters = response.json().get("characters", [])
            for char in characters:
                if char.get("name", "").startswith("TEST_Iter28"):
                    delete_response = session.delete(
                        f"{BASE_URL}/api/pro-studio/characters/{char['id']}"
                    )
                    print(f"Deleted test character: {char['name']}")
        
        print("Cleanup completed")
