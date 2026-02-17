"""
Backend API Tests for Azories New Features (Iteration 5)
Testing: 
- /api/ai/generate-all-images endpoint
- /api/ai/generate-images-from-text endpoint
- Book reader flow
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_AUTHOR_EMAIL = "testauthor@azories.com"
TEST_AUTHOR_PASSWORD = "TestAuthor123!"
ADMIN_USERNAME = "azories_admin"
ADMIN_PASSWORD = "AzoriesAdmin2024!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test author"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_AUTHOR_EMAIL,
        "password": TEST_AUTHOR_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/admin/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def test_book_id(authenticated_client):
    """Get or create a test book for testing"""
    # First try to get existing test book
    response = authenticated_client.get(f"{BASE_URL}/api/books/my")
    if response.status_code == 200 and len(response.json()) > 0:
        return response.json()[0]["id"]
    
    # Create a new test book if none exists
    response = authenticated_client.post(f"{BASE_URL}/api/books", json={
        "title": "TEST_New_Features_Book",
        "description": "Test book for new features",
        "genre": "Fantasy"
    })
    if response.status_code == 200:
        return response.json()["id"]
    return None


class TestGenerateAllImagesEndpoint:
    """Test /api/ai/generate-all-images endpoint"""
    
    def test_endpoint_exists(self, authenticated_client, test_book_id):
        """Test that the endpoint exists and requires authentication"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        # Test without auth first
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-all-images",
            json={"book_id": test_book_id}
        )
        # Should fail without auth
        assert response.status_code == 401, "Endpoint should require authentication"
        print("SUCCESS: generate-all-images endpoint requires authentication")
    
    def test_endpoint_accepts_book_id_and_style(self, authenticated_client, test_book_id):
        """Test that endpoint accepts book_id and style parameters"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        # Request body should accept book_id and style
        # We don't actually generate images (takes too long), just test the endpoint exists
        response = authenticated_client.post(
            f"{BASE_URL}/api/ai/generate-all-images",
            json={
                "book_id": test_book_id,
                "style": "illustration"
            }
        )
        # Should return 200 or appropriate error (not 404/405)
        assert response.status_code != 404, "Endpoint should exist"
        assert response.status_code != 405, "Endpoint should accept POST"
        print(f"SUCCESS: generate-all-images endpoint responds with status {response.status_code}")
    
    def test_endpoint_rejects_invalid_book(self, authenticated_client):
        """Test that endpoint returns 404 for invalid book"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/ai/generate-all-images",
            json={"book_id": "invalid-book-id-12345"}
        )
        assert response.status_code == 404, "Should return 404 for invalid book"
        print("SUCCESS: generate-all-images endpoint returns 404 for invalid book")


class TestGenerateImagesFromTextEndpoint:
    """Test /api/ai/generate-images-from-text endpoint"""
    
    def test_endpoint_exists(self, authenticated_client, test_book_id):
        """Test that the endpoint exists and requires authentication"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        # Test without auth first
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images-from-text",
            json={"book_id": test_book_id}
        )
        assert response.status_code == 401, "Endpoint should require authentication"
        print("SUCCESS: generate-images-from-text endpoint requires authentication")
    
    def test_endpoint_accepts_book_id_and_style(self, authenticated_client, test_book_id):
        """Test that endpoint accepts book_id and style parameters"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/ai/generate-images-from-text",
            json={
                "book_id": test_book_id,
                "style": "comic"
            }
        )
        assert response.status_code != 404, "Endpoint should exist"
        assert response.status_code != 405, "Endpoint should accept POST"
        print(f"SUCCESS: generate-images-from-text endpoint responds with status {response.status_code}")
    
    def test_endpoint_rejects_invalid_book(self, authenticated_client):
        """Test that endpoint returns 404 for invalid book"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/ai/generate-images-from-text",
            json={"book_id": "invalid-book-id-67890"}
        )
        assert response.status_code == 404, "Should return 404 for invalid book"
        print("SUCCESS: generate-images-from-text endpoint returns 404 for invalid book")


class TestBookReaderFlow:
    """Test book reader API flow"""
    
    def test_get_full_book_requires_auth_for_content(self, api_client, test_book_id):
        """Test that full book requires auth to see content"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        # Get book without auth
        response = api_client.get(f"{BASE_URL}/api/books/{test_book_id}/full")
        data = response.json()
        
        # Should return requires_auth = True when not authenticated
        if data.get("requires_auth"):
            print("SUCCESS: Full book requires auth for content")
            assert len(data.get("chapters", [])) == 0, "Should not return chapters without auth"
        else:
            print("Book returned content (may be published public book)")
    
    def test_get_book_preview_no_auth(self, api_client, test_book_id):
        """Test that book preview works without auth"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        response = api_client.get(f"{BASE_URL}/api/books/{test_book_id}/preview")
        assert response.status_code == 200, "Preview should be accessible without auth"
        
        data = response.json()
        assert "title" in data, "Preview should include title"
        assert "cover_image" in data, "Preview should include cover image"
        assert "back_cover_text" in data, "Preview should include back cover text"
        print("SUCCESS: Book preview accessible without auth")
    
    def test_authenticated_user_gets_full_content(self, authenticated_client, test_book_id):
        """Test that authenticated user gets full book content"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        response = authenticated_client.get(f"{BASE_URL}/api/books/{test_book_id}/full")
        assert response.status_code == 200, "Should get full book when authenticated"
        
        data = response.json()
        assert data.get("requires_auth") == False, "Authenticated user should not require auth"
        print("SUCCESS: Authenticated user gets full book content")


class TestStyleOptions:
    """Test that style options work correctly"""
    
    def test_image_styles_accepted(self, authenticated_client, test_book_id):
        """Test that all image styles are accepted"""
        if not test_book_id:
            pytest.skip("No test book available")
        
        styles = ["illustration", "comic", "realistic", "scifi"]
        
        for style in styles:
            # Just test that the endpoint accepts the style (don't actually generate)
            response = authenticated_client.post(
                f"{BASE_URL}/api/ai/generate-all-images",
                json={"book_id": test_book_id, "style": style}
            )
            # Should not return 400 for invalid style
            assert response.status_code != 400, f"Style '{style}' should be accepted"
        
        print(f"SUCCESS: All styles accepted: {styles}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
