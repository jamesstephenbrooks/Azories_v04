"""
Batch 2 Book Editor Tests
Tests for: PDF download with auth, Edit Cover in sidebar, Narration button removed

Features tested:
1. PDF download endpoint with proper auth header
2. Book editor page load
3. Cover data management
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestBatch2PDFDownload:
    """Test PDF download endpoint - requires auth header"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpdf@test.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def book_id(self):
        return "341ebcad-2712-43e8-a956-b0edf6958149"
    
    def test_pdf_download_without_auth_fails(self, book_id):
        """PDF download should fail without authorization header"""
        response = requests.get(f"{BASE_URL}/api/books/{book_id}/download")
        # Should return 401 Unauthorized
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("PASS: PDF download without auth returns 401")
    
    def test_pdf_download_with_auth_succeeds(self, auth_token, book_id):
        """PDF download should work with proper auth header"""
        response = requests.get(
            f"{BASE_URL}/api/books/{book_id}/download",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"PDF download failed: {response.status_code} - {response.text}"
        
        # Verify content type is PDF
        assert "application/pdf" in response.headers.get("content-type", ""), \
            f"Expected PDF content type, got {response.headers.get('content-type')}"
        
        # Verify content disposition header
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, f"Expected attachment disposition, got {content_disp}"
        assert ".pdf" in content_disp, f"Expected .pdf in filename, got {content_disp}"
        
        # Verify we got actual PDF content (PDF files start with %PDF)
        content = response.content
        assert len(content) > 100, f"PDF content too small: {len(content)} bytes"
        assert content[:4] == b'%PDF', f"Content doesn't start with PDF magic number"
        
        print(f"PASS: PDF download with auth works - received {len(content)} bytes")
    
    def test_pdf_download_wrong_book_owner(self, book_id):
        """PDF download should fail for non-owner"""
        # Create a different user
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"testother_{os.urandom(4).hex()}@test.com",
            "password": "password123",
            "name": "Other User"
        })
        
        if register_response.status_code == 200:
            other_token = register_response.json()["access_token"]
            
            response = requests.get(
                f"{BASE_URL}/api/books/{book_id}/download",
                headers={"Authorization": f"Bearer {other_token}"}
            )
            # Should return 403 Forbidden for non-owner
            assert response.status_code == 403, f"Expected 403 for non-owner, got {response.status_code}"
            print("PASS: PDF download blocked for non-owner")
        else:
            pytest.skip("Could not create test user")


class TestBookEditorAPI:
    """Test Book Editor related APIs"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testpdf@test.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def book_id(self):
        return "341ebcad-2712-43e8-a956-b0edf6958149"
    
    def test_get_book_loads(self, book_id):
        """Book data loads correctly"""
        response = requests.get(f"{BASE_URL}/api/books/{book_id}")
        assert response.status_code == 200, f"Failed to load book: {response.status_code}"
        
        data = response.json()
        assert data["id"] == book_id
        assert "title" in data
        assert "cover_image" in data
        assert "back_cover_image" in data
        print(f"PASS: Book loads correctly - title: {data['title']}")
    
    def test_update_book_cover(self, auth_token, book_id):
        """Cover data can be updated"""
        # Update cover data
        update_data = {
            "cover_title": "Test PDF Book",
            "cover_subtitle": "Test Subtitle",
            "back_cover_text": "Test description for back cover"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/books/{book_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to update book: {response.status_code}"
        
        data = response.json()
        assert data["cover_title"] == "Test PDF Book"
        print("PASS: Book cover data can be updated")
    
    def test_get_book_chapters(self, book_id):
        """Book chapters endpoint works"""
        response = requests.get(f"{BASE_URL}/api/books/{book_id}/chapters")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Got {len(data)} chapters for book")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
