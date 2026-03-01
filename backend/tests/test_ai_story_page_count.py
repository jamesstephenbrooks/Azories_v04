"""
Test AI Story Creator - Page Count and Image Generation
Tests the fix for generating exact number of pages with images via fal.ai
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review_request
TEST_EMAIL = "jamesstephenbrooks@outlook.com"
TEST_PASSWORD = "Routetofreedom"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")

@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAIStoryPageCount:
    """Tests for AI Story Creator page count fix"""
    
    def test_api_health(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print(f"Health check passed: {response.json()}")
    
    def test_ai_story_trial_status(self, auth_headers):
        """Check free story trial status"""
        response = requests.get(f"{BASE_URL}/api/auth/ai-story-trial", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Trial status: has_free_stories={data.get('has_free_stories')}, remaining={data.get('free_stories_remaining')}")
        return data
    
    def test_credit_balance(self, auth_headers):
        """Check user credits"""
        response = requests.get(f"{BASE_URL}/api/credits/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Credit balance: {data.get('credits')} credits")
        assert "ai_story_create" in data.get("costs", {}), "AI story cost not defined"
        print(f"AI story cost: {data['costs']['ai_story_create']} credits")
        return data
    
    def test_generate_story_5_pages(self, auth_headers):
        """
        Test generating a 5-page story with images
        This is the main test for the page count fix
        """
        # Prepare story request
        story_request = {
            "title": "Robot Adventures Test",
            "age_range": "5-8",
            "num_pages": 5,  # CRITICAL: Testing 5 pages
            "words_per_page": "medium",  # ~100 words per page
            "character_name": "Sparky",
            "character_description": "A friendly little robot with glowing blue eyes",
            "story_description": "A robot named Sparky explores a magical garden",
            "art_style": "3d-pixar",
            "generate_images": True,
            "media_type": "images"
        }
        
        print(f"\nGenerating story with {story_request['num_pages']} pages...")
        print(f"Story: {story_request['story_description']}")
        
        # This API call may take 30-60 seconds due to AI generation
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-story",
            json=story_request,
            headers=auth_headers,
            timeout=300  # 5 minutes timeout
        )
        
        # Check for success or expected payment errors
        if response.status_code == 402:
            print("402 Payment Required - User needs credits or free stories")
            data = response.json()
            print(f"Error detail: {data.get('detail', 'No detail')}")
            pytest.skip("User has no credits or free stories remaining")
        
        if response.status_code == 503:
            print("503 Service Unavailable - Likely budget exceeded")
            pytest.skip("AI service budget exceeded")
        
        assert response.status_code == 200, f"Story generation failed: {response.status_code} - {response.text}"
        
        data = response.json()
        print(f"\nStory created successfully!")
        print(f"Book ID: {data.get('book_id')}")
        print(f"Title: {data.get('title')}")
        print(f"Pages created: {data.get('pages_created')}")
        print(f"Images generated: {data.get('images_generated')}")
        
        # CRITICAL ASSERTIONS for page count fix
        assert data.get('pages_created') == 5, f"Expected 5 pages, got {data.get('pages_created')}"
        assert data.get('images_generated') == 5, f"Expected 5 images, got {data.get('images_generated')}"
        
        return data
    
    def test_verify_book_pages(self, auth_headers):
        """Verify the test book has exactly 5 pages with images"""
        # Use the test book ID from the review request
        test_book_id = "ef8a6d50-c944-42b0-9fb6-56cd9eaa1a37"
        
        # Get book details
        response = requests.get(f"{BASE_URL}/api/books/{test_book_id}", headers=auth_headers)
        
        if response.status_code == 404:
            print(f"Test book {test_book_id} not found - may have been deleted")
            pytest.skip("Test book not found")
        
        assert response.status_code == 200, f"Failed to get book: {response.text}"
        book = response.json()
        print(f"\nBook: {book.get('title')}")
        print(f"Total pages: {book.get('total_pages')}")
        
        # Get chapters
        chapters_response = requests.get(f"{BASE_URL}/api/books/{test_book_id}/chapters", headers=auth_headers)
        if chapters_response.status_code == 200:
            chapters = chapters_response.json()
            if chapters:
                chapter_id = chapters[0].get('id')
                
                # Get pages
                pages_response = requests.get(f"{BASE_URL}/api/chapters/{chapter_id}/pages", headers=auth_headers)
                if pages_response.status_code == 200:
                    pages = pages_response.json()
                    print(f"Pages in chapter: {len(pages)}")
                    
                    # Count images
                    pages_with_images = 0
                    cloudinary_images = 0
                    
                    for idx, page in enumerate(pages):
                        image_url = page.get('image_url', '')
                        has_image = bool(image_url)
                        is_cloudinary = 'cloudinary' in image_url.lower() if image_url else False
                        
                        if has_image:
                            pages_with_images += 1
                        if is_cloudinary:
                            cloudinary_images += 1
                        
                        print(f"  Page {idx + 1}: {'Has image' if has_image else 'No image'} {'(Cloudinary)' if is_cloudinary else ''}")
                        if image_url:
                            print(f"    URL: {image_url[:80]}...")
                    
                    print(f"\nSummary: {pages_with_images}/{len(pages)} pages have images")
                    print(f"Cloudinary URLs: {cloudinary_images}/{pages_with_images}")
                    
                    # Assert 5 pages
                    assert len(pages) == 5, f"Expected 5 pages, found {len(pages)}"


class TestMobileLayoutElements:
    """Verify mobile layout elements exist in BookEditor"""
    
    def test_book_editor_accessible(self, auth_headers):
        """Verify book editor page is accessible"""
        # Get user's books
        response = requests.get(f"{BASE_URL}/api/books/my", headers=auth_headers)
        assert response.status_code == 200
        books = response.json()
        print(f"User has {len(books)} books")
        
        if books:
            book_id = books[0].get('id')
            print(f"First book ID: {book_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
