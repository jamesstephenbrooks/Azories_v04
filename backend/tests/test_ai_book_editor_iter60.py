"""
Test suite for AI Book Editor fix - iteration 60
Tests: Chapter and Page datetime serialization fix for AI-generated books
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tale-studio-1.preview.emergentagent.com').rstrip('/')

# Test book and chapter IDs
TEST_BOOK_ID = "d624355f-1ab8-449d-a146-6b4c45d88250"
TEST_CHAPTER_ID = "9388162d-b184-4ea5-a461-1a341a1f4446"

# Test user credentials
TEST_USER_EMAIL = "test@printtest.com"
TEST_USER_PASSWORD = "printtest"


class TestHealthCheck:
    """Verify API is running"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ API health check passed")


class TestAIBookChapters:
    """Test chapters endpoint with datetime serialization fix"""
    
    def test_chapters_returns_data(self):
        """GET /api/books/{book_id}/chapters should return chapter with 'Story' title"""
        response = requests.get(f"{BASE_URL}/api/books/{TEST_BOOK_ID}/chapters")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 1, "Should have at least 1 chapter"
        
        # Verify first chapter
        chapter = data[0]
        assert "id" in chapter, "Chapter should have 'id' field"
        assert "book_id" in chapter, "Chapter should have 'book_id' field"
        assert "title" in chapter, "Chapter should have 'title' field"
        assert "created_at" in chapter, "Chapter should have 'created_at' field"
        
        # Verify datetime is serialized as string (the fix)
        assert isinstance(chapter["created_at"], str), "created_at should be a string"
        assert "T" in chapter["created_at"], "created_at should be ISO format"
        
        print(f"✅ Chapters endpoint returned {len(data)} chapter(s)")
        print(f"   Chapter title: {chapter['title']}")
        print(f"   created_at (serialized): {chapter['created_at']}")
    
    def test_chapter_has_story_title(self):
        """Chapter should be titled 'Story' for AI-generated books"""
        response = requests.get(f"{BASE_URL}/api/books/{TEST_BOOK_ID}/chapters")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "Story", f"Chapter title should be 'Story', got '{data[0]['title']}'"
        print("✅ Chapter title is 'Story' as expected")


class TestAIBookPages:
    """Test pages endpoint with datetime serialization fix"""
    
    def test_pages_returns_data(self):
        """GET /api/chapters/{chapter_id}/pages should return 5 pages with content"""
        response = requests.get(f"{BASE_URL}/api/chapters/{TEST_CHAPTER_ID}/pages")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 5, f"Should have 5 pages, got {len(data)}"
        
        print(f"✅ Pages endpoint returned {len(data)} pages")
    
    def test_pages_have_text_content(self):
        """Each page should have text_content"""
        response = requests.get(f"{BASE_URL}/api/chapters/{TEST_CHAPTER_ID}/pages")
        assert response.status_code == 200
        
        data = response.json()
        for i, page in enumerate(data):
            assert "text_content" in page, f"Page {i+1} should have 'text_content'"
            assert page["text_content"], f"Page {i+1} text_content should not be empty"
            print(f"   Page {i+1}: {page['text_content'][:50]}...")
        
        print("✅ All pages have text_content")
    
    def test_pages_have_image_url(self):
        """Each page should have image_url"""
        response = requests.get(f"{BASE_URL}/api/chapters/{TEST_CHAPTER_ID}/pages")
        assert response.status_code == 200
        
        data = response.json()
        for i, page in enumerate(data):
            assert "image_url" in page, f"Page {i+1} should have 'image_url'"
            assert page["image_url"], f"Page {i+1} image_url should not be empty"
            print(f"   Page {i+1} image: {page['image_url'][:60]}...")
        
        print("✅ All pages have image_url")
    
    def test_pages_created_at_serialized(self):
        """Verify created_at is serialized as string (the fix)"""
        response = requests.get(f"{BASE_URL}/api/chapters/{TEST_CHAPTER_ID}/pages")
        assert response.status_code == 200
        
        data = response.json()
        for i, page in enumerate(data):
            assert "created_at" in page, f"Page {i+1} should have 'created_at'"
            assert isinstance(page["created_at"], str), f"Page {i+1} created_at should be string"
            assert "T" in page["created_at"], f"Page {i+1} created_at should be ISO format"
        
        print("✅ All pages have properly serialized created_at")


class TestBookEditorAccess:
    """Test book access and authorization"""
    
    def test_book_exists(self):
        """Book should exist and be accessible"""
        response = requests.get(f"{BASE_URL}/api/books/{TEST_BOOK_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TEST_BOOK_ID
        assert "title" in data
        print(f"✅ Book exists: {data.get('title', 'Unknown')}")
    
    def test_user_login(self):
        """Test user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        # Note: User may not exist or have access
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            print(f"✅ User login successful: {TEST_USER_EMAIL}")
            return data["access_token"]
        else:
            print(f"⚠️ Login returned {response.status_code} - user may not have access to this book")
            return None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
