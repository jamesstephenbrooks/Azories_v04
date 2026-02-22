"""
Test iteration 26 bug fixes:
1. TTS endpoint with ElevenLabs
2. Create chapter API
3. Create page API
4. Save covers API (should work with valid token)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestIteration26BugFixes:
    """Test bug fixes for iteration 26 - Azories Book Editor"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data and login"""
        self.book_id = "341ebcad-2712-43e8-a956-b0edf6958149"
        self.chapter_id = "2be893f9-3374-4fc8-beaa-fea22bd6e950"
        self.test_email = "testpdf@test.com"
        self.test_password = "password123"
        
        # Login to get token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get('access_token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_tts_generate_with_elevenlabs(self):
        """TTS endpoint should work with ElevenLabs"""
        response = requests.post(f"{BASE_URL}/api/tts/generate", json={
            "text": "Hello, this is a test of the text-to-speech system.",
            "voice_id": "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        })
        
        assert response.status_code == 200, f"TTS failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "audio_base64" in data, "Response should contain audio_base64"
        assert "success" in data, "Response should contain success flag"
        assert data["success"] == True, "TTS should succeed"
        assert len(data["audio_base64"]) > 100, "Audio data should not be empty"
        print(f"✓ TTS with ElevenLabs working - Audio length: {len(data['audio_base64'])}")
    
    def test_create_chapter_with_valid_token(self):
        """Create chapter should work when user is logged in"""
        response = requests.post(
            f"{BASE_URL}/api/books/{self.book_id}/chapters",
            json={"title": "TEST_Chapter_Iteration26"},
            headers=self.headers
        )
        
        assert response.status_code in [200, 201], f"Create chapter failed: {response.text}"
        data = response.json()
        
        # Verify chapter was created
        assert "id" in data, "Response should contain chapter id"
        assert data["title"] == "TEST_Chapter_Iteration26"
        
        # Store chapter id for cleanup
        self.created_chapter_id = data["id"]
        print(f"✓ Chapter created with id: {self.created_chapter_id}")
        
        # Verify by fetching
        verify = requests.get(
            f"{BASE_URL}/api/books/{self.book_id}/chapters",
            headers=self.headers
        )
        chapters = verify.json()
        chapter_titles = [c.get("title") for c in chapters]
        assert "TEST_Chapter_Iteration26" in chapter_titles, "Created chapter should be in list"
    
    def test_create_page_with_valid_token(self):
        """Create page should work when user is logged in"""
        response = requests.post(
            f"{BASE_URL}/api/chapters/{self.chapter_id}/pages",
            json={"text_content": "TEST_Page_Iteration26 content"},
            headers=self.headers
        )
        
        assert response.status_code in [200, 201], f"Create page failed: {response.text}"
        data = response.json()
        
        # Verify page was created
        assert "id" in data, "Response should contain page id"
        
        self.created_page_id = data["id"]
        print(f"✓ Page created with id: {self.created_page_id}")
    
    def test_save_cover_with_valid_token(self):
        """Save cover via PUT /api/books/{book_id} should work when logged in"""
        # The bug was that the frontend was using wrong localStorage key 'token' 
        # instead of 'azories-token'. This API test verifies the backend endpoint works.
        # Covers are saved via PUT /api/books/{book_id} with cover fields
        
        response = requests.put(
            f"{BASE_URL}/api/books/{self.book_id}",
            json={
                "cover_title": "Test PDF Book Updated",
                "cover_subtitle": "Test Subtitle",
                "back_cover_text": "Test description for back cover"
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Save cover failed: {response.text}"
        data = response.json()
        
        # Verify cover was saved
        assert "id" in data, "Should return book data with id"
        print(f"✓ Cover saved successfully via PUT /api/books/{self.book_id}")
    
    def test_save_cover_without_token_fails(self):
        """Save cover should fail without auth token"""
        response = requests.put(
            f"{BASE_URL}/api/books/{self.book_id}",
            json={
                "cover_title": "Test",
                "cover_subtitle": "Test"
            }
            # No headers - no auth
        )
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Should fail without token, got {response.status_code}"
        print(f"✓ Cover save correctly requires authentication")
    
    def test_book_chapters_list(self):
        """Get chapters list should work"""
        response = requests.get(
            f"{BASE_URL}/api/books/{self.book_id}/chapters",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Get chapters failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return list of chapters"
        print(f"✓ Found {len(data)} chapters")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpdf@test.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json().get('access_token')
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_cleanup_test_chapters(self):
        """Clean up TEST_ prefixed chapters"""
        book_id = "341ebcad-2712-43e8-a956-b0edf6958149"
        response = requests.get(f"{BASE_URL}/api/books/{book_id}/chapters", headers=self.headers)
        if response.status_code == 200:
            chapters = response.json()
            for chapter in chapters:
                if chapter.get("title", "").startswith("TEST_"):
                    requests.delete(
                        f"{BASE_URL}/api/chapters/{chapter['id']}",
                        headers=self.headers
                    )
                    print(f"Cleaned up test chapter: {chapter['title']}")
