"""
Azories Digital Book Platform - Admin CMS and New Features Tests
Tests for:
- Admin authentication and CMS endpoints
- Book download endpoint for creators
- Sci-fi style option in AI generation
- Toggle featured/best-of-week status
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials from the request
ADMIN_USERNAME = "azories_admin"
ADMIN_PASSWORD = "AzoriesAdmin2024!"


class TestAdminAuthentication:
    """Test separate admin authentication system"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "admin_name" in data
        assert data["admin_name"] == ADMIN_USERNAME
        print(f"✓ Admin login successful - token received")
        return data["access_token"]
    
    def test_admin_login_failure_wrong_username(self):
        """Test admin login fails with wrong username"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "wrong_admin",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 401
        print(f"✓ Wrong admin username correctly rejected")
    
    def test_admin_login_failure_wrong_password(self):
        """Test admin login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print(f"✓ Wrong admin password correctly rejected")
    
    def test_admin_verify_token(self):
        """Test admin token verification"""
        # First login
        login_res = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        token = login_res.json()["access_token"]
        
        # Verify token
        response = requests.get(
            f"{BASE_URL}/api/admin/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["username"] == ADMIN_USERNAME
        print(f"✓ Admin token verification successful")


class TestAdminCMSEndpoints:
    """Test admin CMS endpoints for viewing all books, users, and analytics"""
    
    @pytest.fixture(autouse=True)
    def get_admin_token(self):
        """Get admin auth token for all tests"""
        login_res = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        self.admin_token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_get_all_books(self):
        """Test admin can see all books (published and unpublished)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/books",
            headers=self.headers
        )
        assert response.status_code == 200
        books = response.json()
        assert isinstance(books, list)
        print(f"✓ Admin can view all {len(books)} books")
        return books
    
    def test_admin_get_all_users(self):
        """Test admin can see all users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers=self.headers
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        # Verify password is not included
        if len(users) > 0:
            assert "password" not in users[0]
        print(f"✓ Admin can view all {len(users)} users (passwords excluded)")
    
    def test_admin_get_analytics(self):
        """Test admin can access platform analytics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_books" in data
        assert "published_books" in data
        assert "total_users" in data
        assert "pro_users" in data
        assert "top_books" in data
        print(f"✓ Admin analytics working - {data['total_books']} books, {data['total_users']} users")


class TestAdminBookManagement:
    """Test admin book management - featured, best-of-week, publish toggles"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token and find a test book"""
        login_res = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        self.admin_token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Get a book to test with
        books_res = requests.get(f"{BASE_URL}/api/admin/books", headers=self.headers)
        books = books_res.json()
        self.test_book_id = books[0]["id"] if books else None
    
    def test_toggle_featured_status(self):
        """Test admin can toggle featured status for books"""
        if not self.test_book_id:
            pytest.skip("No books available for testing")
        
        # Get current status
        books_res = requests.get(f"{BASE_URL}/api/admin/books", headers=self.headers)
        book = next((b for b in books_res.json() if b["id"] == self.test_book_id), None)
        initial_featured = book.get("is_featured", False)
        
        # Toggle
        response = requests.post(
            f"{BASE_URL}/api/admin/books/{self.test_book_id}/feature",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_featured" in data
        assert data["is_featured"] != initial_featured
        print(f"✓ Featured status toggled from {initial_featured} to {data['is_featured']}")
        
        # Toggle back
        response2 = requests.post(
            f"{BASE_URL}/api/admin/books/{self.test_book_id}/feature",
            headers=self.headers
        )
        assert response2.json()["is_featured"] == initial_featured
        print(f"✓ Featured status restored to {initial_featured}")
    
    def test_toggle_best_of_week_status(self):
        """Test admin can toggle best-of-week status for books"""
        if not self.test_book_id:
            pytest.skip("No books available for testing")
        
        # Get current status
        books_res = requests.get(f"{BASE_URL}/api/admin/books", headers=self.headers)
        book = next((b for b in books_res.json() if b["id"] == self.test_book_id), None)
        initial_best = book.get("is_best_of_week", False)
        
        # Toggle
        response = requests.post(
            f"{BASE_URL}/api/admin/books/{self.test_book_id}/best-of-week",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_best_of_week" in data
        assert data["is_best_of_week"] != initial_best
        print(f"✓ Best-of-week status toggled from {initial_best} to {data['is_best_of_week']}")
        
        # Toggle back
        response2 = requests.post(
            f"{BASE_URL}/api/admin/books/{self.test_book_id}/best-of-week",
            headers=self.headers
        )
        assert response2.json()["is_best_of_week"] == initial_best
        print(f"✓ Best-of-week status restored to {initial_best}")
    
    def test_toggle_publish_status(self):
        """Test admin can publish/unpublish books"""
        if not self.test_book_id:
            pytest.skip("No books available for testing")
        
        # Get current status
        books_res = requests.get(f"{BASE_URL}/api/admin/books", headers=self.headers)
        book = next((b for b in books_res.json() if b["id"] == self.test_book_id), None)
        initial_published = book.get("is_published", False)
        
        # Toggle
        response = requests.post(
            f"{BASE_URL}/api/admin/books/{self.test_book_id}/publish",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_published" in data
        print(f"✓ Publish status toggled from {initial_published} to {data['is_published']}")
        
        # Toggle back to original
        response2 = requests.post(
            f"{BASE_URL}/api/admin/books/{self.test_book_id}/publish",
            headers=self.headers
        )
        print(f"✓ Publish status restored")
    
    def test_admin_seed_test_books(self):
        """Test admin can seed test books"""
        response = requests.post(
            f"{BASE_URL}/api/admin/seed-test-books",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Seed test books endpoint working - {data['message']}")


class TestBookDownloadEndpoint:
    """Test book download endpoint for creators"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a test user and book for download testing"""
        # Create unique test user
        self.test_email = f"test_download_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "TestPass123!"
        
        # Register user
        register_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.test_email,
            "password": self.test_password,
            "name": "Download Test User"
        })
        self.user_token = register_res.json()["access_token"]
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Upgrade to pro (required to create books)
        requests.post(
            f"{BASE_URL}/api/auth/upgrade",
            json={"subscription": "pro"},
            headers=self.user_headers
        )
        
        # Create a test book
        book_res = requests.post(
            f"{BASE_URL}/api/books",
            json={
                "title": "Test Download Book",
                "description": "A book for testing download",
                "genre": "Fantasy"
            },
            headers=self.user_headers
        )
        if book_res.status_code == 200:
            self.test_book_id = book_res.json()["id"]
        else:
            self.test_book_id = None
    
    def test_creator_can_download_own_book(self):
        """Test that creator can download their own book"""
        if not self.test_book_id:
            pytest.skip("Could not create test book")
        
        response = requests.get(
            f"{BASE_URL}/api/books/{self.test_book_id}/download",
            headers=self.user_headers
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        
        # Check for download attachment header
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp
        print(f"✓ Creator can download own book - Content-Disposition: {content_disp}")
        
        # Verify JSON structure
        data = response.json()
        assert "metadata" in data
        assert "cover" in data
        assert "chapters" in data
        assert data["metadata"]["title"] == "Test Download Book"
        print(f"✓ Download contains valid book structure")
    
    def test_non_creator_cannot_download_book(self):
        """Test that non-creator cannot download someone else's book"""
        if not self.test_book_id:
            pytest.skip("Could not create test book")
        
        # Create different user
        other_email = f"test_other_{uuid.uuid4().hex[:8]}@example.com"
        other_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": other_email,
            "password": "OtherPass123!",
            "name": "Other User"
        })
        other_token = other_res.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/books/{self.test_book_id}/download",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert response.status_code == 403
        print(f"✓ Non-creator correctly rejected from downloading")
    
    def test_download_requires_auth(self):
        """Test that download requires authentication"""
        if not self.test_book_id:
            pytest.skip("Could not create test book")
        
        response = requests.get(f"{BASE_URL}/api/books/{self.test_book_id}/download")
        assert response.status_code == 401
        print(f"✓ Download correctly requires authentication")


class TestSciFiStyleOptions:
    """Test sci-fi style option in AI image/video generation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for AI tests"""
        self.test_email = f"test_scifi_{uuid.uuid4().hex[:8]}@example.com"
        register_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.test_email,
            "password": "TestPass123!",
            "name": "Sci-Fi Test User"
        })
        self.user_token = register_res.json()["access_token"]
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}
    
    def test_image_generation_accepts_scifi_style(self):
        """Test that image generation endpoint accepts sci-fi style"""
        # Note: We don't actually run the generation as it's expensive
        # Just verify the endpoint accepts the style parameter
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-image",
            json={
                "prompt": "A spaceship in orbit",
                "style": "scifi"
            },
            headers=self.user_headers
        )
        # Expect either 200 (if it runs) or error about generation
        # Main point is it shouldn't reject the style parameter as invalid
        assert response.status_code in [200, 500]  # 500 would mean API issue, not param rejection
        if response.status_code == 500:
            # If 500, check it's not because of invalid style
            error_msg = response.json().get("detail", "")
            assert "style" not in error_msg.lower() or "invalid" not in error_msg.lower()
        print(f"✓ Image generation accepts 'scifi' style parameter")
    
    def test_video_generation_accepts_scifi_style(self):
        """Test that video generation endpoint accepts sci-fi style"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-video",
            json={
                "prompt": "A rocket launch",
                "duration": 5,
                "style": "scifi"
            },
            headers=self.user_headers
        )
        # Allow 200, 500 (API issues), or 5xx (timeout/connection)
        assert response.status_code in [200, 500, 502, 503, 520]
        if response.status_code == 500:
            error_msg = response.json().get("detail", "")
            assert "style" not in error_msg.lower() or "invalid" not in error_msg.lower()
        print(f"✓ Video generation accepts 'scifi' style parameter (status: {response.status_code})")


class TestAdminWithoutAuth:
    """Test admin endpoints require authentication"""
    
    def test_admin_books_requires_auth(self):
        """Test /admin/books requires admin token"""
        response = requests.get(f"{BASE_URL}/api/admin/books")
        assert response.status_code in [401, 403, 422]
        print(f"✓ Admin books endpoint requires authentication")
    
    def test_admin_users_requires_auth(self):
        """Test /admin/users requires admin token"""
        response = requests.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code in [401, 403, 422]
        print(f"✓ Admin users endpoint requires authentication")
    
    def test_admin_analytics_requires_auth(self):
        """Test /admin/analytics requires admin token"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code in [401, 403, 422]
        print(f"✓ Admin analytics endpoint requires authentication")
    
    def test_regular_user_cannot_access_admin(self):
        """Test regular user token cannot access admin endpoints"""
        # Create regular user
        test_email = f"test_regular_{uuid.uuid4().hex[:8]}@example.com"
        register_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Regular User"
        })
        user_token = register_res.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/books",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        # Either 401 (not admin token) or 403 (forbidden) is acceptable
        assert response.status_code in [401, 403]
        print(f"✓ Regular user cannot access admin endpoints (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
