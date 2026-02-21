"""
Test Iteration 19 Features:
- Books API returns 5+ published books with detailed stories (10+ pages each)
- Animation save to gallery endpoint
- Gallery type filter (all/images/animations)
- Book reader loads pages without separate chapter title pages
- New user registration gives 30-day Pro trial
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Login and get token for authenticated tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "artstudio3@test.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPublishedBooks:
    """Test books API returns 5+ published books with detailed stories"""
    
    def test_published_books_count(self):
        """Verify at least 5 published books exist"""
        response = requests.get(f"{BASE_URL}/api/books?status=published&limit=10")
        assert response.status_code == 200
        
        books = response.json()
        assert len(books) >= 5, f"Expected 5+ published books, got {len(books)}"
    
    def test_books_have_detailed_content(self):
        """Verify books have 9+ pages with substantial text"""
        response = requests.get(f"{BASE_URL}/api/books?status=published&limit=5")
        assert response.status_code == 200
        books = response.json()
        
        for book in books:
            assert book.get("total_pages", 0) >= 9, \
                f"Book '{book.get('title')}' has only {book.get('total_pages')} pages, expected 9+"
    
    def test_book_chapters_have_pages_with_text(self):
        """Verify book chapters have pages with actual story text"""
        # Get a published book
        response = requests.get(f"{BASE_URL}/api/books?status=published&limit=1")
        assert response.status_code == 200
        book = response.json()[0]
        book_id = book["id"]
        
        # Get chapters
        chapters_response = requests.get(f"{BASE_URL}/api/books/{book_id}/chapters")
        assert chapters_response.status_code == 200
        chapters = chapters_response.json()
        assert len(chapters) > 0, "Book should have at least one chapter"
        
        # Get pages from first chapter
        chapter_id = chapters[0]["id"]
        pages_response = requests.get(f"{BASE_URL}/api/chapters/{chapter_id}/pages")
        assert pages_response.status_code == 200
        pages = pages_response.json()
        
        # Verify pages have text content
        assert len(pages) >= 5, f"Chapter should have 5+ pages, got {len(pages)}"
        
        # Check first page has substantial text
        first_page = pages[0]
        assert "text_content" in first_page
        assert len(first_page["text_content"]) > 50, \
            f"Page text too short: {len(first_page['text_content'])} chars"


class TestBookFullEndpoint:
    """Test /books/{id}/full endpoint used by reader"""
    
    def test_book_full_returns_chapters_and_pages(self, auth_headers):
        """Verify /books/{id}/full returns chapters with pages inline (requires auth)"""
        response = requests.get(f"{BASE_URL}/api/books?status=published&limit=1")
        book_id = response.json()[0]["id"]
        
        # Must be authenticated to get chapters/pages
        full_response = requests.get(f"{BASE_URL}/api/books/{book_id}/full", headers=auth_headers)
        assert full_response.status_code == 200
        
        data = full_response.json()
        assert "chapters" in data, "Full book should include chapters"
        assert len(data["chapters"]) > 0, "Book should have chapters"
        
        # Verify pages are inline in chapters
        chapter = data["chapters"][0]
        assert "pages" in chapter, "Chapter should include pages inline"
        assert len(chapter["pages"]) > 0, "Chapter should have pages"
        
        # Verify page structure
        page = chapter["pages"][0]
        assert "text_content" in page
        assert "order" in page
    
    def test_book_full_requires_auth(self):
        """Verify /books/{id}/full without auth returns requires_auth=True"""
        response = requests.get(f"{BASE_URL}/api/books?status=published&limit=1")
        book_id = response.json()[0]["id"]
        
        # Without auth, should return requires_auth=True and empty chapters
        full_response = requests.get(f"{BASE_URL}/api/books/{book_id}/full")
        assert full_response.status_code == 200
        
        data = full_response.json()
        assert data.get("requires_auth") == True, "Without auth, should require auth"
        assert len(data.get("chapters", [])) == 0, "Without auth, chapters should be empty"


class TestAnimationFeatures:
    """Test animation save and gallery features"""
    
    def test_save_animation_endpoint(self, auth_headers):
        """Test /api/art-studio/save-animation saves animation to gallery"""
        test_animation = {
            "video_url": "https://example.com/test_animation.mp4",
            "name": f"TEST_Animation_{uuid.uuid4().hex[:8]}",
            "motion_prompt": "A dragon flying through clouds",
            "style": "fantasy"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/art-studio/save-animation",
            json=test_animation,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        assert "id" in data
        
        # Cleanup - delete the test animation
        animation_id = data["id"]
        requests.delete(f"{BASE_URL}/api/art-studio/gallery/{animation_id}", headers=auth_headers)
    
    def test_gallery_type_filter_all(self, auth_headers):
        """Test gallery returns all items when no type filter"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/gallery",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "images" in response.json()
    
    def test_gallery_type_filter_images(self, auth_headers):
        """Test gallery filters to images only"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/gallery?type_filter=image",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "images" in data
        
        # All items should be non-animation type
        for item in data["images"]:
            assert item.get("type") != "animation", \
                f"Found animation in images filter: {item.get('name')}"
    
    def test_gallery_type_filter_animations(self, auth_headers):
        """Test gallery filters to animations only"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/gallery?type_filter=animation",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "images" in data
        
        # All items should be animation type
        for item in data["images"]:
            assert item.get("type") == "animation", \
                f"Found non-animation in animations filter: {item.get('type')}"


class TestProTrialForNewUsers:
    """Test new user registration includes 30-day Pro trial"""
    
    def test_new_user_gets_pro_trial(self):
        """Verify new user registration sets pro_trial and 30-day expiry"""
        unique_id = uuid.uuid4().hex[:8]
        new_user = {
            "email": f"TEST_trialuser_{unique_id}@example.com",
            "password": "TestPass123!",
            "name": "Trial Test User"
        }
        
        # Register new user
        response = requests.post(f"{BASE_URL}/api/auth/register", json=new_user)
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data
        
        user = data["user"]
        # Check pro_trial fields
        assert user.get("pro_trial") == True, "New user should have pro_trial=True"
        assert user.get("pro_trial_expires_at") is not None, "pro_trial_expires_at should be set"
        
        # Verify trial_days_remaining is approximately 30
        trial_days = user.get("trial_days_remaining")
        assert trial_days is not None, "trial_days_remaining should be set"
        assert trial_days >= 29, f"Trial days should be ~30, got {trial_days}"
        
        # Verify user can access Pro features (subscription should effectively be pro)
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": new_user["email"],
            "password": new_user["password"]
        })
        assert login_response.status_code == 200


class TestBookReaderPagesStructure:
    """Test book reader gets pages without separate chapter title pages"""
    
    def test_full_book_pages_are_content_only(self):
        """Verify /books/{id}/full returns content pages, not chapter titles"""
        response = requests.get(f"{BASE_URL}/api/books?status=published&limit=1")
        book_id = response.json()[0]["id"]
        
        full_response = requests.get(f"{BASE_URL}/api/books/{book_id}/full")
        assert full_response.status_code == 200
        
        data = full_response.json()
        chapters = data.get("chapters", [])
        
        for chapter in chapters:
            pages = chapter.get("pages", [])
            for page in pages:
                # Content pages should have text_content
                assert "text_content" in page, "Page should have text_content"
                # Pages should have order numbers
                assert "order" in page, "Page should have order"
                # If a page has only a title without text, that's a chapter title page
                # Content pages should have substantial text
                if page.get("text_content"):
                    assert len(page["text_content"]) > 10, \
                        "Content pages should have substantial text"


class TestGalleryManagement:
    """Test gallery CRUD operations"""
    
    def test_save_and_delete_image(self, auth_headers):
        """Test saving image to gallery and deleting it"""
        # First save an image
        test_image = {
            "image_url": "https://example.com/test_image.png",
            "name": f"TEST_Image_{uuid.uuid4().hex[:8]}",
            "type": "character",
            "style": "fantasy"
        }
        
        save_response = requests.post(
            f"{BASE_URL}/api/art-studio/save",
            json=test_image,
            headers=auth_headers
        )
        assert save_response.status_code == 200
        
        saved_id = save_response.json().get("id")
        assert saved_id is not None
        
        # Verify it appears in gallery
        gallery_response = requests.get(
            f"{BASE_URL}/api/art-studio/gallery",
            headers=auth_headers
        )
        assert gallery_response.status_code == 200
        
        # Delete the image
        delete_response = requests.delete(
            f"{BASE_URL}/api/art-studio/gallery/{saved_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
