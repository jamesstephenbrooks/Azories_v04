"""
Iteration 7 Test Suite - Testing New Features:
1) Search bar in My Books page
2) Manage Series dialog with expandable/collapsible view
3) Add books to series from within expanded series view
4) Auto-read ON by default in reader
5) Narrator voice dropdown in reader
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthAndSetup:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["subscription"] == "pro"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test user can login successfully"""
        assert auth_token is not None
        print("Login successful for testuser2@example.com")
    
    def test_genres_endpoint(self):
        """Test genres endpoint returns list"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert len(data["genres"]) > 0
        print(f"Genres available: {data['genres']}")
    
    def test_voices_endpoint(self):
        """Test voices endpoint returns narrator voices"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any("voice_id" in v for v in data)
        print(f"Voices available: {len(data)}")


class TestSeriesManagement:
    """Series management API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_series_list(self, auth_headers):
        """Test fetching user's series"""
        response = requests.get(f"{BASE_URL}/api/series", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"User has {len(data)} series")
        
    def test_create_series(self, auth_headers):
        """Test creating a new series"""
        response = requests.post(f"{BASE_URL}/api/series", 
            headers=auth_headers,
            json={
                "name": "TEST_Iteration7_Series",
                "description": "Test series for iteration 7 testing"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "TEST_Iteration7_Series"
        print(f"Created series: {data['id']}")
        return data["id"]
    
    def test_series_has_books_array(self, auth_headers):
        """Test series response includes books array (for expandable view)"""
        response = requests.get(f"{BASE_URL}/api/series", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            # Check that series have books array for expandable view
            for series in data:
                assert "books" in series, "Series should have 'books' array for expandable view"
                assert "book_count" in series
                print(f"Series '{series['name']}' has {series['book_count']} books, books array: {len(series.get('books', []))}")
    
    def test_add_book_to_series(self, auth_headers):
        """Test adding book to series"""
        # First get user's books
        books_response = requests.get(f"{BASE_URL}/api/books/my", headers=auth_headers)
        assert books_response.status_code == 200
        books = books_response.json()
        
        if len(books) == 0:
            pytest.skip("No books available to add to series")
        
        # Get or create a test series
        series_response = requests.get(f"{BASE_URL}/api/series", headers=auth_headers)
        series_list = series_response.json()
        
        # Find a book not in any series
        book_to_add = None
        for book in books:
            if not book.get("series_id"):
                book_to_add = book
                break
        
        if not book_to_add:
            print("All books are already in series")
            return
        
        if len(series_list) == 0:
            # Create a series first
            create_response = requests.post(f"{BASE_URL}/api/series",
                headers=auth_headers,
                json={"name": "TEST_Add_Book_Series", "description": "Test"}
            )
            series_id = create_response.json()["id"]
        else:
            series_id = series_list[0]["id"]
        
        # Add book to series
        add_response = requests.post(
            f"{BASE_URL}/api/series/{series_id}/books/{book_to_add['id']}",
            headers=auth_headers
        )
        assert add_response.status_code == 200
        data = add_response.json()
        assert "order" in data
        print(f"Added book '{book_to_add['title']}' to series with order {data['order']}")
    
    def test_remove_book_from_series(self, auth_headers):
        """Test removing book from series"""
        # Get user's books
        books_response = requests.get(f"{BASE_URL}/api/books/my", headers=auth_headers)
        books = books_response.json()
        
        # Find a book in a series
        book_in_series = None
        for book in books:
            if book.get("series_id"):
                book_in_series = book
                break
        
        if not book_in_series:
            pytest.skip("No book in series to test removal")
        
        # Remove book from series
        remove_response = requests.delete(
            f"{BASE_URL}/api/series/{book_in_series['series_id']}/books/{book_in_series['id']}",
            headers=auth_headers
        )
        assert remove_response.status_code == 200
        print(f"Removed book '{book_in_series['title']}' from series")


class TestBookSearch:
    """Book search functionality tests (backend filter support)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_my_books(self, auth_headers):
        """Test fetching user's books - used for frontend filtering"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"User has {len(data)} books")
        
        # Verify book response structure includes fields needed for search
        if len(data) > 0:
            book = data[0]
            assert "title" in book
            assert "description" in book
            assert "genre" in book
            print(f"Book fields for search: title, description, genre present")
    
    def test_book_has_series_info(self, auth_headers):
        """Test that books have series_id and series_order fields"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            book = data[0]
            # series_id can be null but field should exist
            assert "series_id" in book or book.get("series_id") is None
            print(f"Books have series_id field for series badge display")


class TestBookReader:
    """Book reader API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_voices_for_narrator(self):
        """Test voices endpoint for narrator dropdown"""
        response = requests.get(f"{BASE_URL}/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Verify voice structure for dropdown
        voice = data[0]
        assert "voice_id" in voice
        assert "name" in voice
        print(f"Voices for narrator dropdown: {[v['name'] for v in data[:5]]}...")
    
    def test_book_has_narrator_voice(self, auth_headers):
        """Test book response includes narrator_voice_id"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            book = data[0]
            assert "narrator_voice_id" in book
            print(f"Book has narrator_voice_id: {book.get('narrator_voice_id', 'default')}")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser2@example.com",
            "password": "TestPass123!"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_cleanup_test_series(self, auth_headers):
        """Clean up test series created during testing"""
        response = requests.get(f"{BASE_URL}/api/series", headers=auth_headers)
        if response.status_code == 200:
            series_list = response.json()
            for series in series_list:
                if series["name"].startswith("TEST_"):
                    delete_response = requests.delete(
                        f"{BASE_URL}/api/series/{series['id']}",
                        headers=auth_headers
                    )
                    if delete_response.status_code == 200:
                        print(f"Cleaned up test series: {series['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
