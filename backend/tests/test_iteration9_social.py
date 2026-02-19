"""
Iteration 9: Testing new features:
1. User Profile API endpoints (/api/users/{id}/profile, /api/users/profile PUT)
2. Social features (follow/unfollow)
3. Reviews API (/api/reviews POST, /api/books/{id}/reviews GET)
4. Analytics Dashboard backend
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser2@example.com"
TEST_PASSWORD = "TestPass123!"


class TestUserProfileAndSocial:
    """Test user profile and social features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token")
            self.user = data.get("user", {})
            self.user_id = self.user.get("id")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_01_get_user_profile(self):
        """Test GET /api/users/{id}/profile - get user profile"""
        response = self.session.get(f"{BASE_URL}/api/users/{self.user_id}/profile")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Profile should have id"
        assert "name" in data, "Profile should have name"
        assert "display_name" in data, "Profile should have display_name"
        assert "followers_count" in data, "Profile should have followers_count"
        assert "following_count" in data, "Profile should have following_count"
        assert "books_count" in data, "Profile should have books_count"
        assert "total_reads" in data, "Profile should have total_reads"
        assert "created_at" in data or data.get("created_at") is not None, "Profile should have created_at"
        
        print(f"✓ User profile retrieved: {data['name']}, books: {data['books_count']}")
    
    def test_02_update_user_profile(self):
        """Test PUT /api/users/profile - update own profile"""
        unique_suffix = str(uuid.uuid4())[:8]
        update_data = {
            "display_name": f"TEST_Display_{unique_suffix}",
            "bio": f"TEST_Bio: I love creating stories! {unique_suffix}",
            "location": "TEST_San Francisco, CA",
            "website": "https://test-example.com",
            "twitter": "test_author"
        }
        
        response = self.session.put(f"{BASE_URL}/api/users/profile", json=update_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify update was persisted by fetching profile
        get_response = self.session.get(f"{BASE_URL}/api/users/{self.user_id}/profile")
        assert get_response.status_code == 200
        
        profile = get_response.json()
        assert profile["display_name"] == update_data["display_name"], "Display name should be updated"
        assert profile["bio"] == update_data["bio"], "Bio should be updated"
        assert profile["location"] == update_data["location"], "Location should be updated"
        
        print(f"✓ Profile updated: {profile['display_name']}")
    
    def test_03_get_user_books(self):
        """Test GET /api/users/{id}/books - get user's published books"""
        response = self.session.get(f"{BASE_URL}/api/users/{self.user_id}/books")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        books = response.json()
        assert isinstance(books, list), "Should return a list of books"
        
        # All returned books should be published
        for book in books:
            if "is_published" in book:
                assert book["is_published"] == True, "Only published books should be returned"
        
        print(f"✓ User books retrieved: {len(books)} published books")
    
    def test_04_get_nonexistent_user_profile(self):
        """Test GET /api/users/{id}/profile - nonexistent user returns 404"""
        fake_id = "nonexistent-user-id-12345"
        response = self.session.get(f"{BASE_URL}/api/users/{fake_id}/profile")
        
        assert response.status_code == 404, f"Expected 404 for nonexistent user, got {response.status_code}"
        
        print("✓ Nonexistent user profile returns 404")


class TestFollowFeatures:
    """Test follow/unfollow functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - create a second test user to follow"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as main test user
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        data = login_response.json()
        self.token = data.get("token")
        self.user = data.get("user", {})
        self.user_id = self.user.get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Create or find a second user to test following
        unique_id = str(uuid.uuid4())[:8]
        register_response = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_followtest_{unique_id}@example.com",
            "password": "TestPass123!",
            "name": f"TEST_FollowUser_{unique_id}"
        })
        
        if register_response.status_code == 200:
            self.target_user_id = register_response.json().get("user", {}).get("id")
        else:
            # If registration fails, skip follow tests
            pytest.skip("Could not create test user for follow tests")
    
    def test_01_cannot_follow_self(self):
        """Test that user cannot follow themselves"""
        response = self.session.post(f"{BASE_URL}/api/users/{self.user_id}/follow")
        
        assert response.status_code == 400, f"Expected 400 when following self, got {response.status_code}"
        
        print("✓ Cannot follow self - returns 400")
    
    def test_02_follow_user(self):
        """Test POST /api/users/{id}/follow - follow a user"""
        response = self.session.post(f"{BASE_URL}/api/users/{self.target_user_id}/follow")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Should return a message"
        
        print(f"✓ Successfully followed user {self.target_user_id}")
    
    def test_03_get_followers(self):
        """Test GET /api/users/{id}/followers - get user's followers"""
        response = self.session.get(f"{BASE_URL}/api/users/{self.target_user_id}/followers")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        followers = response.json()
        assert isinstance(followers, list), "Should return a list"
        
        print(f"✓ Followers list retrieved: {len(followers)} followers")
    
    def test_04_get_following(self):
        """Test GET /api/users/{id}/following - get users being followed"""
        response = self.session.get(f"{BASE_URL}/api/users/{self.user_id}/following")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        following = response.json()
        assert isinstance(following, list), "Should return a list"
        
        print(f"✓ Following list retrieved: {len(following)} users")
    
    def test_05_unfollow_user(self):
        """Test DELETE /api/users/{id}/follow - unfollow a user"""
        # First ensure we're following
        self.session.post(f"{BASE_URL}/api/users/{self.target_user_id}/follow")
        
        # Then unfollow
        response = self.session.delete(f"{BASE_URL}/api/users/{self.target_user_id}/follow")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        print(f"✓ Successfully unfollowed user {self.target_user_id}")


class TestReviewsAPI:
    """Test reviews functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and find a book to review"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        data = login_response.json()
        self.token = data.get("token")
        self.user_id = data.get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Find a published book to review
        books_response = self.session.get(f"{BASE_URL}/api/books?is_published=true")
        if books_response.status_code == 200:
            books = books_response.json()
            if books:
                self.book_id = books[0].get("id")
            else:
                pytest.skip("No published books to review")
        else:
            pytest.skip("Could not fetch books")
        
        self.review_id = None
    
    def test_01_create_review(self):
        """Test POST /api/reviews - create a book review"""
        review_data = {
            "book_id": self.book_id,
            "rating": 5,
            "content": f"TEST_Review: Great book! {uuid.uuid4()}"
        }
        
        response = self.session.post(f"{BASE_URL}/api/reviews", json=review_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data or "message" in data, "Should return review id or message"
        
        if "id" in data:
            self.review_id = data["id"]
        
        print(f"✓ Review created for book {self.book_id}")
    
    def test_02_get_book_reviews(self):
        """Test GET /api/books/{id}/reviews - get reviews for a book"""
        response = self.session.get(f"{BASE_URL}/api/books/{self.book_id}/reviews")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "reviews" in data, "Should have reviews array"
        assert "average_rating" in data, "Should have average_rating"
        assert "total_reviews" in data, "Should have total_reviews"
        
        assert isinstance(data["reviews"], list), "Reviews should be a list"
        
        print(f"✓ Book reviews retrieved: {data['total_reviews']} reviews, avg rating: {data['average_rating']}")
    
    def test_03_review_rating_validation(self):
        """Test that review rating must be 1-5"""
        # Test rating below 1
        response = self.session.post(f"{BASE_URL}/api/reviews", json={
            "book_id": self.book_id,
            "rating": 0,
            "content": "TEST_Invalid rating"
        })
        
        assert response.status_code == 422, f"Expected 422 for rating 0, got {response.status_code}"
        
        # Test rating above 5
        response = self.session.post(f"{BASE_URL}/api/reviews", json={
            "book_id": self.book_id,
            "rating": 6,
            "content": "TEST_Invalid rating"
        })
        
        assert response.status_code == 422, f"Expected 422 for rating 6, got {response.status_code}"
        
        print("✓ Review rating validation works (1-5 only)")


class TestAnalyticsAPI:
    """Test analytics endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get user's books"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        data = login_response.json()
        self.token = data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get user's books
        books_response = self.session.get(f"{BASE_URL}/api/books/my")
        if books_response.status_code == 200:
            books = books_response.json()
            if books:
                self.book_id = books[0].get("id")
            else:
                pytest.skip("No books to test analytics")
        else:
            pytest.skip("Could not fetch user books")
    
    def test_01_get_book_analytics(self):
        """Test GET /api/books/{id}/analytics - get book analytics"""
        response = self.session.get(f"{BASE_URL}/api/books/{self.book_id}/analytics")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify analytics data structure
        assert "view_count" in data, "Should have view_count"
        assert "read_count" in data, "Should have read_count"
        assert "unique_readers" in data, "Should have unique_readers"
        
        print(f"✓ Book analytics retrieved: {data.get('view_count', 0)} views, {data.get('read_count', 0)} reads")
    
    def test_02_my_books_have_analytics_fields(self):
        """Test that /api/books/my returns books with view/read counts"""
        response = self.session.get(f"{BASE_URL}/api/books/my")
        
        assert response.status_code == 200
        
        books = response.json()
        assert len(books) > 0, "Should have at least one book"
        
        # Check that books have analytics fields
        for book in books[:3]:  # Check first 3 books
            assert "view_count" in book or book.get("view_count") is not None, f"Book {book.get('id')} should have view_count"
            # read_count might be optional, just check it doesn't error
        
        print(f"✓ My books have analytics fields (view_count, read_count)")


class TestAmbientSoundPrerequisites:
    """Test that ambient sound component has access to book genre"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_01_book_full_includes_genre(self):
        """Test that /api/books/{id}/full returns genre for ambient sound"""
        # Get a published book
        response = self.session.get(f"{BASE_URL}/api/books?is_published=true")
        
        if response.status_code != 200:
            pytest.skip("Could not fetch books")
        
        books = response.json()
        if not books:
            pytest.skip("No published books")
        
        book_id = books[0].get("id")
        
        # Get full book
        full_response = self.session.get(f"{BASE_URL}/api/books/{book_id}/full")
        
        assert full_response.status_code == 200, f"Expected 200, got {full_response.status_code}"
        
        book = full_response.json()
        assert "genre" in book, "Book should have genre field for ambient sound selection"
        
        print(f"✓ Book full endpoint includes genre: {book.get('genre', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
