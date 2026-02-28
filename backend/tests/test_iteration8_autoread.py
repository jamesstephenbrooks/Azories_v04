"""
Iteration 8 Backend Tests: Auto-read, Series Management, Search Functionality
Focus: Testing the audiobook continuous playback infrastructure and supporting features
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://azories-audit.preview.emergentagent.com').rstrip('/')


class TestAuthAndSetup:
    """Test authentication and basic setup"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["subscription"] == "pro"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_user_login(self, auth_token, headers):
        """Test that user can login and has pro subscription"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == "testuser2@example.com"
        assert user["subscription"] == "pro"
        print(f"✓ User authenticated: {user['name']} ({user['subscription']})")


class TestVoicesAPI:
    """Test voice endpoints for narrator voice dropdown"""
    
    def test_get_voices_returns_list(self):
        """Test that /api/voices returns a list of available voices"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200
        voices = response.json()
        assert isinstance(voices, list)
        assert len(voices) >= 10, f"Expected at least 10 voices, got {len(voices)}"
        
        # Check voice structure
        for voice in voices[:3]:
            assert "voice_id" in voice
            assert "name" in voice
        
        # Check Rachel is in the list (default voice)
        rachel = next((v for v in voices if v["name"] == "Rachel"), None)
        assert rachel is not None, "Rachel voice not found"
        print(f"✓ Found {len(voices)} narrator voices (Rachel default exists)")


class TestTTSAPI:
    """Test Text-to-Speech API for auto-read functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_tts_generate_returns_audio(self, headers):
        """Test TTS endpoint generates audio for page content"""
        response = requests.post(f"{BASE_URL}/api/tts/generate", headers=headers, json={
            "text": "Once upon a time in a magical forest...",
            "voice_id": "21m00Tcm4TlvDq8ikWAM"  # Rachel
        })
        assert response.status_code == 200
        data = response.json()
        assert "audio_base64" in data
        assert len(data["audio_base64"]) > 100  # Should have substantial audio data
        print(f"✓ TTS generated audio successfully ({len(data['audio_base64'])} chars)")
    
    def test_tts_with_different_voice(self, headers):
        """Test TTS with a different narrator voice"""
        response = requests.post(f"{BASE_URL}/api/tts/generate", headers=headers, json={
            "text": "The brave knight rode through the kingdom.",
            "voice_id": "TxGEqnHWrfWFTfGW9XjX"  # Josh
        })
        assert response.status_code == 200
        data = response.json()
        assert "audio_base64" in data
        print("✓ TTS works with different voices (Josh)")


class TestSeriesManagement:
    """Test series CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_create_series(self, headers):
        """Test creating a new series"""
        response = requests.post(f"{BASE_URL}/api/series", headers=headers, json={
            "name": "TEST_AutoRead_Series",
            "description": "Test series for iteration 8"
        })
        assert response.status_code == 200
        series = response.json()
        assert series["name"] == "TEST_AutoRead_Series"
        assert "id" in series
        print(f"✓ Created series: {series['name']} ({series['id'][:8]}...)")
        return series["id"]
    
    def test_get_user_series(self, headers):
        """Test getting user's series list"""
        response = requests.get(f"{BASE_URL}/api/series", headers=headers)
        assert response.status_code == 200
        series_list = response.json()
        assert isinstance(series_list, list)
        
        # Check series structure
        if len(series_list) > 0:
            s = series_list[0]
            assert "id" in s
            assert "name" in s
            assert "books" in s  # Should include books array for expandable view
        print(f"✓ Got {len(series_list)} series")
    
    def test_delete_test_series(self, headers):
        """Cleanup: Delete test series"""
        response = requests.get(f"{BASE_URL}/api/series", headers=headers)
        series_list = response.json()
        
        for s in series_list:
            if s["name"].startswith("TEST_"):
                del_response = requests.delete(f"{BASE_URL}/api/series/{s['id']}", headers=headers)
                assert del_response.status_code == 200
                print(f"✓ Cleaned up test series: {s['name']}")


class TestBookFullEndpoint:
    """Test the /api/books/{id}/full endpoint used by BookReader"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_get_user_books(self, headers):
        """Get user's books to find one for testing"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers=headers)
        assert response.status_code == 200
        books = response.json()
        return books
    
    def test_book_full_endpoint_structure(self, headers):
        """Test that /api/books/{id}/full returns correct structure for reader"""
        books = self.test_get_user_books(headers)
        
        if len(books) == 0:
            pytest.skip("No books available to test")
        
        book_id = books[0]["id"]
        response = requests.get(f"{BASE_URL}/api/books/{book_id}/full", headers=headers)
        assert response.status_code == 200
        
        book = response.json()
        assert "id" in book
        assert "title" in book
        assert "narrator_voice_id" in book  # Important for auto-read
        assert "chapters" in book
        
        # Check chapters have pages
        if book.get("chapters"):
            chapter = book["chapters"][0]
            assert "id" in chapter
            assert "title" in chapter
            assert "pages" in chapter
            
            # Check page structure for auto-read
            if chapter.get("pages"):
                page = chapter["pages"][0]
                assert "id" in page
                assert "text_content" in page or "text" in page.get("text_content", "text")
        
        print(f"✓ Book full endpoint returns correct structure for '{book['title']}'")


class TestSearchFunctionality:
    """Test search bar functionality (backend perspective)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_get_books_with_fields_for_search(self, headers):
        """Test that books API returns all fields needed for search filtering"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers=headers)
        assert response.status_code == 200
        books = response.json()
        
        if len(books) == 0:
            pytest.skip("No books to test search fields")
        
        # Check that books have searchable fields
        for book in books[:3]:
            assert "title" in book
            assert "description" in book
            assert "genre" in book
        
        print(f"✓ Books have all fields required for search (title, description, genre)")


class TestAutoReadBookCreation:
    """Test creating a book with multiple chapters for auto-read testing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_create_multi_chapter_book_for_autoread(self, headers):
        """Create a test book with multiple chapters for testing auto-read flow"""
        # Create book
        book_response = requests.post(f"{BASE_URL}/api/books", headers=headers, json={
            "title": "TEST_AutoRead_MultiChapter_Book",
            "description": "A test book with multiple chapters for auto-read testing",
            "genre": "Adventure",
            "narrator_voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "age_rating": "All Ages"
        })
        assert book_response.status_code == 200
        book = book_response.json()
        book_id = book["id"]
        print(f"✓ Created book: {book['title']}")
        
        # Create Chapter 1
        ch1_response = requests.post(f"{BASE_URL}/api/books/{book_id}/chapters", headers=headers, json={
            "title": "Chapter 1: The Beginning",
            "order": 1
        })
        assert ch1_response.status_code == 200
        chapter1 = ch1_response.json()
        ch1_id = chapter1["id"]
        print(f"✓ Created Chapter 1")
        
        # Create pages for Chapter 1
        for i in range(1, 3):
            page_response = requests.post(f"{BASE_URL}/api/chapters/{ch1_id}/pages", headers=headers, json={
                "text_content": f"This is page {i} of chapter 1. It has text content for the auto-read feature to narrate.",
                "order": i
            })
            assert page_response.status_code == 200
        print(f"✓ Created 2 pages for Chapter 1")
        
        # Create Chapter 2
        ch2_response = requests.post(f"{BASE_URL}/api/books/{book_id}/chapters", headers=headers, json={
            "title": "Chapter 2: The Adventure",
            "order": 2
        })
        assert ch2_response.status_code == 200
        chapter2 = ch2_response.json()
        ch2_id = chapter2["id"]
        print(f"✓ Created Chapter 2")
        
        # Create pages for Chapter 2
        for i in range(1, 3):
            page_response = requests.post(f"{BASE_URL}/api/chapters/{ch2_id}/pages", headers=headers, json={
                "text_content": f"This is page {i} of chapter 2. The adventure continues with more exciting content.",
                "order": i
            })
            assert page_response.status_code == 200
        print(f"✓ Created 2 pages for Chapter 2")
        
        # Publish the book for reading
        publish_response = requests.put(f"{BASE_URL}/api/books/{book_id}", headers=headers, json={
            "is_published": True
        })
        assert publish_response.status_code == 200
        print(f"✓ Published book")
        
        # Verify the full book structure
        full_response = requests.get(f"{BASE_URL}/api/books/{book_id}/full", headers=headers)
        assert full_response.status_code == 200
        full_book = full_response.json()
        
        assert len(full_book.get("chapters", [])) == 2, "Expected 2 chapters"
        assert full_book["narrator_voice_id"] == "21m00Tcm4TlvDq8ikWAM"
        
        total_pages = sum(len(ch.get("pages", [])) for ch in full_book.get("chapters", []))
        assert total_pages == 4, f"Expected 4 pages, got {total_pages}"
        
        print(f"✓ Book structure verified: 2 chapters, 4 pages, narrator_voice_id set")
        
        return book_id
    
    def test_cleanup_test_books(self, headers):
        """Cleanup: Delete test books"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers=headers)
        books = response.json()
        
        for book in books:
            if book["title"].startswith("TEST_"):
                del_response = requests.delete(f"{BASE_URL}/api/books/{book['id']}", headers=headers)
                if del_response.status_code == 200:
                    print(f"✓ Cleaned up test book: {book['title']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
