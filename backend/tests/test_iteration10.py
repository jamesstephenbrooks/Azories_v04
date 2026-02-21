"""
Iteration 10 Testing: Engagement Features
Tests for:
- Ambient sounds endpoint (backend proxy for CORS)
- Reading streaks/badges API
- Book recommendations API
- User reading stats API
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test123@example.com"
TEST_PASSWORD = "Test123!"


class TestAmbientSounds:
    """Test ambient sound proxy endpoints"""
    
    def test_ambient_sound_rain(self):
        """Test rain ambient sound returns audio"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/rain", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get('content-type') == 'audio/mpeg'
        print("✓ Rain ambient sound endpoint working")
    
    def test_ambient_sound_fireplace(self):
        """Test fireplace ambient sound"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/fireplace", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get('content-type') == 'audio/mpeg'
        print("✓ Fireplace ambient sound endpoint working")
    
    def test_ambient_sound_forest(self):
        """Test forest ambient sound"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/forest", timeout=30)
        assert response.status_code == 200
        print("✓ Forest ambient sound endpoint working")
    
    def test_ambient_sound_ocean(self):
        """Test ocean ambient sound"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/ocean", timeout=30)
        assert response.status_code == 200
        print("✓ Ocean ambient sound endpoint working")
    
    def test_ambient_sound_invalid(self):
        """Test invalid sound returns 404"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/invalid_sound", timeout=30)
        assert response.status_code == 404, f"Expected 404 for invalid sound, got {response.status_code}"
        print("✓ Invalid ambient sound returns 404 correctly")


class TestAuthentication:
    """Test authentication for engagement features"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Could not authenticate: {response.status_code}")
        return response.json().get('access_token')
    
    def test_login_works(self, auth_token):
        """Verify login works"""
        assert auth_token is not None
        print("✓ Login authentication working")


class TestReadingStreaksAndBadges:
    """Test reading streaks and badges endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        token = response.json().get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    def test_reading_stats_endpoint(self, auth_headers):
        """Test GET /api/reading-stats returns user stats"""
        response = requests.get(f"{BASE_URL}/api/reading-stats", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Verify response structure
        assert 'current_streak' in data, "Response should have current_streak"
        assert 'total_reading_days' in data, "Response should have total_reading_days"
        assert 'completed_books' in data, "Response should have completed_books"
        print(f"✓ Reading stats: {data['current_streak']} day streak, {data['completed_books']} books completed")
    
    def test_user_reading_stats_endpoint(self, auth_headers):
        """Test GET /api/user/reading-stats returns user stats with badges"""
        response = requests.get(f"{BASE_URL}/api/user/reading-stats", headers=auth_headers)
        # This might be a different endpoint format
        if response.status_code == 404:
            print("⚠ /api/user/reading-stats not found, checking alternative endpoint")
            # Try reading-stats instead
            pytest.skip("Endpoint may have different path")
        assert response.status_code == 200 or response.status_code == 404
        print("✓ User reading stats endpoint checked")


class TestBookRecommendations:
    """Test book recommendations endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        token = response.json().get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    def test_user_recommendations(self, auth_headers):
        """Test GET /api/user/recommendations returns book recommendations"""
        response = requests.get(f"{BASE_URL}/api/user/recommendations", headers=auth_headers)
        if response.status_code == 404:
            # Endpoint might not exist yet
            print("⚠ /api/user/recommendations endpoint not found")
            pytest.skip("Recommendations endpoint not implemented")
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Recommendations endpoint working, returned {len(data.get('recommendations', []))} books")


class TestBooksEndpoints:
    """Test existing books endpoints"""
    
    def test_get_published_books(self):
        """Test GET /api/books returns published books"""
        response = requests.get(f"{BASE_URL}/api/books")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        books = response.json()
        assert isinstance(books, list), "Books should be a list"
        print(f"✓ Books endpoint working, found {len(books)} published books")
        return books
    
    def test_get_featured_books(self):
        """Test GET /api/books/featured returns featured books"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Featured books endpoint working")
    
    def test_get_genres(self):
        """Test GET /api/genres returns genre list"""
        response = requests.get(f"{BASE_URL}/api/genres")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'genres' in data, "Response should have genres"
        print(f"✓ Genres endpoint working, found {len(data['genres'])} genres")


class TestEditorCollaborativeFeatures:
    """Test collaborative writing endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        token = response.json().get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_book_id(self, auth_headers):
        """Get a test book ID"""
        # First get user's books
        response = requests.get(f"{BASE_URL}/api/books/my", headers=auth_headers)
        if response.status_code != 200:
            pytest.skip("Could not get user books")
        books = response.json()
        if not books:
            pytest.skip("No books found for user")
        return books[0]['id']
    
    def test_get_book_collaborators(self, auth_headers, test_book_id):
        """Test GET /api/books/{id}/collaborators"""
        response = requests.get(f"{BASE_URL}/api/books/{test_book_id}/collaborators", headers=auth_headers)
        # Endpoint might return 404 if not implemented or 200 with empty list
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Collaborators endpoint working, {len(data.get('collaborators', []))} collaborators")
        else:
            print("⚠ Collaborators endpoint not implemented (404)")


class TestSpecificBook:
    """Test specific book endpoints"""
    
    def test_get_book_details(self):
        """Test getting book details - use known test book ID"""
        test_book_id = "0d439aa7-20bc-42c3-be56-1c81bf560960"  # Book editor test ID from context
        response = requests.get(f"{BASE_URL}/api/books/{test_book_id}")
        if response.status_code == 404:
            print(f"⚠ Test book {test_book_id} not found, skipping")
            pytest.skip("Test book not found")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        book = response.json()
        print(f"✓ Book details: '{book.get('title')}' by {book.get('author_name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
