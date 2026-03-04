"""
Test Reading Streaks and Badge Features
Tests for:
- /api/user/reading-stats endpoint - returns streak and best_streak
- /api/user/record-reading endpoint - updates streak, returns best_streak
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from problem statement
TEST_EMAIL = "jamesstephenbrooks@outlook.com"
TEST_PASSWORD = "Routetofreedom"

class TestReadingStreaksFeature:
    """Tests for Reading Streaks and Badge Feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json().get("access_token")
        assert token, "No token returned from login"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def sample_book_id(self, auth_headers):
        """Get a sample book ID for testing"""
        # Try to get a book from library
        response = requests.get(
            f"{BASE_URL}/api/library",
            headers=auth_headers
        )
        if response.status_code == 200:
            books = response.json().get("books", [])
            if books:
                return books[0].get("id")
        # Fallback to a static ID
        return "test-book-id"
    
    # Test 1: Get reading stats endpoint returns streak and best_streak
    def test_get_reading_stats_returns_streak_and_best_streak(self, auth_headers):
        """Test /api/user/reading-stats returns streak and best_streak"""
        response = requests.get(
            f"{BASE_URL}/api/user/reading-stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Reading stats failed: {response.text}"
        data = response.json()
        
        # Check required fields exist
        assert "streak" in data, "streak field missing from response"
        assert "best_streak" in data, "best_streak field missing from response"
        assert "badges" in data, "badges field missing from response"
        assert "total_books_read" in data, "total_books_read field missing"
        
        # Validate types
        assert isinstance(data["streak"], int), "streak should be int"
        assert isinstance(data["best_streak"], int), "best_streak should be int"
        assert isinstance(data["badges"], list), "badges should be list"
        
        print(f"✓ Reading stats - streak: {data['streak']}, best_streak: {data['best_streak']}, badges: {data['badges']}")
    
    # Test 2: Record reading endpoint updates streak
    def test_record_reading_updates_streak(self, auth_headers, sample_book_id):
        """Test /api/user/record-reading updates streak and returns best_streak"""
        response = requests.post(
            f"{BASE_URL}/api/user/record-reading",
            headers=auth_headers,
            json={
                "book_id": sample_book_id,
                "time_spent": 60,
                "completed": False
            }
        )
        
        assert response.status_code == 200, f"Record reading failed: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "streak" in data, "streak field missing from record-reading response"
        assert "best_streak" in data, "best_streak field missing from record-reading response"
        
        # best_streak should be >= streak
        assert data["best_streak"] >= data["streak"], "best_streak should be >= streak"
        
        print(f"✓ Record reading - streak: {data['streak']}, best_streak: {data['best_streak']}")
    
    # Test 3: Record reading can return new_badge
    def test_record_reading_returns_badge_fields(self, auth_headers, sample_book_id):
        """Test /api/user/record-reading returns new_badge and all_badges fields"""
        response = requests.post(
            f"{BASE_URL}/api/user/record-reading",
            headers=auth_headers,
            json={
                "book_id": sample_book_id,
                "time_spent": 120,
                "completed": False
            }
        )
        
        assert response.status_code == 200, f"Record reading failed: {response.text}"
        data = response.json()
        
        # Check badge-related fields exist
        assert "new_badge" in data, "new_badge field missing"
        assert "all_badges" in data, "all_badges field missing"
        
        print(f"✓ Record reading badges - new_badge: {data['new_badge']}, all_badges: {data['all_badges']}")
    
    # Test 4: Reading stats endpoint authentication required
    def test_reading_stats_requires_auth(self):
        """Test /api/user/reading-stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/user/reading-stats")
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Reading stats correctly requires authentication")
    
    # Test 5: Record reading endpoint authentication required
    def test_record_reading_requires_auth(self):
        """Test /api/user/record-reading requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/user/record-reading",
            json={"book_id": "test-book", "time_spent": 60}
        )
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Record reading correctly requires authentication")
    
    # Test 6: Verify badge names match expected values
    def test_badge_definitions_in_response(self, auth_headers):
        """Verify the reading stats returns correct badge IDs"""
        response = requests.get(
            f"{BASE_URL}/api/user/reading-stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Expected badge IDs that can be earned
        expected_badge_ids = [
            'streak_3',    # On Fire!
            'streak_7',    # Star Reader!
            'streak_14',   # Champion Reader!
            'streak_30',   # Dragon Reader!
            'first_book',
            'bookworm',
            'night_owl',
            'early_bird',
            'genre_explorer',
            'supporter',
            'creator'
        ]
        
        # Badges in response should be valid badge IDs
        for badge in data.get("badges", []):
            assert badge in expected_badge_ids, f"Unknown badge ID: {badge}"
        
        print(f"✓ All badges in response are valid: {data.get('badges', [])}")


class TestBookShareFeature:
    """Tests for Share Book URL feature - no specific backend endpoint needed"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # Test 1: Verify public book access (shared link)
    def test_public_book_access_no_auth_required(self, auth_headers):
        """Test that books can be accessed without authentication (for sharing)"""
        # First get a book ID from library
        response = requests.get(
            f"{BASE_URL}/api/library",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            books = response.json().get("books", [])
            if books:
                book_id = books[0].get("id")
                
                # Try to access book without auth
                public_response = requests.get(f"{BASE_URL}/api/books/{book_id}")
                
                # Should be accessible (200) or at least not require auth (not 401)
                assert public_response.status_code in [200, 404], \
                    f"Book should be publicly accessible, got {public_response.status_code}"
                
                if public_response.status_code == 200:
                    print(f"✓ Book {book_id} is publicly accessible (for sharing)")
                else:
                    print(f"⚠ Book {book_id} returned 404 - may be draft/private")
                return
        
        pytest.skip("No books available to test public access")
    
    # Test 2: Verify book by ID endpoint exists
    def test_book_by_id_endpoint_exists(self, auth_headers):
        """Test /api/books/{id} endpoint exists"""
        # Get a published book from library
        response = requests.get(
            f"{BASE_URL}/api/library",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            books = response.json().get("books", [])
            if books:
                book_id = books[0].get("id")
                
                # Access with auth to verify endpoint works
                book_response = requests.get(
                    f"{BASE_URL}/api/books/{book_id}",
                    headers=auth_headers
                )
                
                assert book_response.status_code in [200, 404], \
                    f"Unexpected status: {book_response.status_code}"
                
                if book_response.status_code == 200:
                    book_data = book_response.json()
                    assert "id" in book_data or "_id" in book_data, "Book should have id"
                    assert "title" in book_data, "Book should have title"
                    print(f"✓ Book endpoint works for ID: {book_id}")
                return
        
        pytest.skip("No books available to test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
