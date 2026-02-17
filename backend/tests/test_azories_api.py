"""
Azories Digital Book Platform - Backend API Tests
Tests for: Library page APIs, voices endpoint, book reader navigation
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Basic health and info endpoints"""
    
    def test_api_root(self):
        """Test API root returns proper message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome to Azories API" in data["message"]
        assert "version" in data
        print(f"✓ API root working - Version: {data['version']}")

    def test_genres_endpoint(self):
        """Test genres endpoint returns list"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert len(data["genres"]) > 0
        assert "Adventure" in data["genres"]
        print(f"✓ Genres endpoint working - {len(data['genres'])} genres available")

    def test_age_ratings_endpoint(self):
        """Test age ratings endpoint"""
        response = requests.get(f"{BASE_URL}/api/age-ratings")
        assert response.status_code == 200
        data = response.json()
        assert "age_ratings" in data
        assert "All Ages" in data["age_ratings"]
        print(f"✓ Age ratings endpoint working - {len(data['age_ratings'])} ratings available")


class TestVoicesAPI:
    """Test narrator voices API - /api/voices"""
    
    def test_voices_returns_list(self):
        """Test voices endpoint returns list of narrator voices"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Voices API returned {len(data)} voices")
    
    def test_voice_has_required_fields(self):
        """Test each voice has required fields"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200
        voices = response.json()
        
        required_fields = ["voice_id", "name"]
        for voice in voices:
            for field in required_fields:
                assert field in voice, f"Voice missing required field: {field}"
        
        # Check first voice structure
        first_voice = voices[0]
        assert first_voice["voice_id"] is not None
        assert first_voice["name"] is not None
        print(f"✓ All voices have required fields (voice_id, name)")
    
    def test_voice_has_optional_fields(self):
        """Test voices include optional category and accent"""
        response = requests.get(f"{BASE_URL}/api/voices")
        voices = response.json()
        
        # Check if category and accent are included
        first_voice = voices[0]
        assert "category" in first_voice or "accent" in first_voice
        print(f"✓ Voices include optional fields (category/accent)")


class TestBooksAPI:
    """Test books listing API - /api/books"""
    
    def test_books_returns_list(self):
        """Test books endpoint returns list of published books"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Books API returned {len(data)} published books")
    
    def test_book_has_required_fields(self):
        """Test each book has required display fields"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        books = response.json()
        
        if len(books) == 0:
            pytest.skip("No published books available for testing")
        
        required_fields = ["id", "title", "author_name", "genre", "is_published"]
        for book in books:
            for field in required_fields:
                assert field in book, f"Book missing required field: {field}"
        
        print(f"✓ All books have required fields")
    
    def test_books_filter_by_genre(self):
        """Test books can be filtered by genre"""
        response = requests.get(f"{BASE_URL}/api/books?genre=Fantasy&published_only=true")
        assert response.status_code == 200
        books = response.json()
        # Just ensure endpoint works with filter
        print(f"✓ Genre filter works - {len(books)} Fantasy books found")
    
    def test_books_search(self):
        """Test books search functionality"""
        response = requests.get(f"{BASE_URL}/api/books?search=story&published_only=true")
        assert response.status_code == 200
        books = response.json()
        print(f"✓ Search functionality works - {len(books)} books matching 'story'")
    
    def test_featured_books_endpoint(self):
        """Test featured books endpoint"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        assert response.status_code == 200
        books = response.json()
        assert isinstance(books, list)
        print(f"✓ Featured books endpoint works - {len(books)} featured books")


class TestBookReaderAPIs:
    """Test book reader related APIs"""
    
    @pytest.fixture(autouse=True)
    def get_test_book(self):
        """Get a test book ID"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        books = response.json()
        if books:
            self.book_id = books[0]["id"]
        else:
            self.book_id = None
    
    def test_get_single_book(self):
        """Test fetching a single book by ID"""
        if not self.book_id:
            pytest.skip("No books available for testing")
        
        response = requests.get(f"{BASE_URL}/api/books/{self.book_id}")
        assert response.status_code == 200
        book = response.json()
        assert book["id"] == self.book_id
        assert "title" in book
        assert "author_name" in book
        print(f"✓ Single book fetch works - '{book['title']}'")
    
    def test_get_book_chapters(self):
        """Test fetching chapters for a book"""
        if not self.book_id:
            pytest.skip("No books available for testing")
        
        response = requests.get(f"{BASE_URL}/api/books/{self.book_id}/chapters")
        assert response.status_code == 200
        chapters = response.json()
        assert isinstance(chapters, list)
        print(f"✓ Book chapters fetch works - {len(chapters)} chapters found")
        
        return chapters
    
    def test_get_chapter_pages(self):
        """Test fetching pages for a chapter - for book reader navigation"""
        if not self.book_id:
            pytest.skip("No books available for testing")
        
        # First get chapters
        chapters_response = requests.get(f"{BASE_URL}/api/books/{self.book_id}/chapters")
        chapters = chapters_response.json()
        
        if not chapters:
            pytest.skip("No chapters available for testing")
        
        chapter_id = chapters[0]["id"]
        response = requests.get(f"{BASE_URL}/api/chapters/{chapter_id}/pages")
        assert response.status_code == 200
        pages = response.json()
        assert isinstance(pages, list)
        print(f"✓ Chapter pages fetch works - {len(pages)} pages found")
    
    def test_book_full_content_endpoint(self):
        """Test full book content endpoint (for reading)"""
        if not self.book_id:
            pytest.skip("No books available for testing")
        
        response = requests.get(f"{BASE_URL}/api/books/{self.book_id}/full")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        # Without auth, requires_auth should be True or chapters empty
        print(f"✓ Full book endpoint works")
    
    def test_book_preview_endpoint(self):
        """Test book preview endpoint (cover + summary)"""
        if not self.book_id:
            pytest.skip("No books available for testing")
        
        response = requests.get(f"{BASE_URL}/api/books/{self.book_id}/preview")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "cover_image" in data
        assert "author_name" in data
        print(f"✓ Book preview endpoint works")
    
    def test_nonexistent_book_returns_404(self):
        """Test that requesting a non-existent book returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/books/{fake_id}")
        assert response.status_code == 404
        print(f"✓ Non-existent book returns 404 as expected")


class TestAuthenticationFlow:
    """Test authentication endpoints"""
    
    def test_register_and_login(self):
        """Test user registration and login flow"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "TestPass123!"
        test_name = "Test User"
        
        # Register
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "name": test_name
        })
        assert register_response.status_code == 200
        register_data = register_response.json()
        assert "access_token" in register_data
        assert "user" in register_data
        print(f"✓ Registration successful for {test_email}")
        
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        print(f"✓ Login successful for {test_email}")
        
        return login_data["access_token"]
    
    def test_invalid_login(self):
        """Test invalid login credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print(f"✓ Invalid login correctly rejected with 401")


class TestLibraryPageData:
    """Test data requirements for Library page grid and 3D views"""
    
    def test_books_have_cover_info_for_grid(self):
        """Test books have cover image info for grid display"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        books = response.json()
        
        if not books:
            pytest.skip("No books available")
        
        # Check grid-related fields
        grid_fields = ["title", "description", "cover_image", "author_name", "genre"]
        for book in books:
            for field in grid_fields:
                assert field in book, f"Missing field for grid view: {field}"
        
        print(f"✓ Books have all fields needed for grid view")
    
    def test_books_have_3d_bookshelf_info(self):
        """Test books have info needed for 3D bookshelf"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true")
        books = response.json()
        
        if not books:
            pytest.skip("No books available")
        
        # Check 3D bookshelf needs: title, genre (for color), id (for selection)
        bookshelf_fields = ["id", "title", "genre"]
        for book in books:
            for field in bookshelf_fields:
                assert field in book, f"Missing field for 3D bookshelf: {field}"
        
        print(f"✓ Books have all fields needed for 3D bookshelf view")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
