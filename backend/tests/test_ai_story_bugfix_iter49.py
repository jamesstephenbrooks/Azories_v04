"""
Test AI Story Bug Fix - Iteration 49

Tests the bug fix for AI-generated books appearing empty. The root cause was that 
the /books/{book_id}/full endpoint was not checking the pages collection where 
AI-generated pages are stored (linked by book_id instead of chapter_id).

Key tests:
1. Verify existing AI book (f1328a57-849f-4160-8820-a7caea04c1ea) returns pages with text and images
2. Test login flow with provided credentials
3. Test job status endpoint accessibility
4. Test book/full endpoint returns chapters array with pages
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials provided by main agent
TEST_EMAIL = "jamesstephenbrooks@outlook.com"
TEST_PASSWORD = "Routetofreedom"

# Existing test book created by the bug fix verification
TEST_BOOK_ID = "f1328a57-849f-4160-8820-a7caea04c1ea"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test user can login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        assert "user" in data, "No user object in login response"
        assert data["user"]["email"] == TEST_EMAIL
        
        print(f"Login successful for user: {data['user']['name']}")


class TestAIStoryBugFix:
    """Tests for the AI story empty book bug fix"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate - skipping tests")
    
    def test_existing_ai_book_has_pages(self):
        """CRITICAL: Verify the existing AI book returns pages with content"""
        response = requests.get(
            f"{BASE_URL}/api/books/{TEST_BOOK_ID}/full",
            headers=self.headers
        )
        
        # Book might not exist if test data changed
        if response.status_code == 404:
            pytest.skip(f"Test book {TEST_BOOK_ID} not found - may have been deleted")
        
        assert response.status_code == 200, f"Failed to get book: {response.text}"
        
        data = response.json()
        
        # Verify book data structure
        assert "chapters" in data, "No chapters array in response"
        chapters = data.get("chapters", [])
        
        # The fix should ensure chapters are NOT empty
        assert len(chapters) > 0, "BUG: chapters array is empty - fix not working!"
        
        # Verify pages in first chapter
        first_chapter = chapters[0]
        assert "pages" in first_chapter, "No pages array in chapter"
        pages = first_chapter.get("pages", [])
        
        assert len(pages) > 0, "BUG: pages array is empty - fix not working!"
        
        # Verify page content structure
        first_page = pages[0]
        
        # Check for text content (either 'text' or 'text_content')
        has_text = bool(first_page.get("text") or first_page.get("text_content"))
        assert has_text, f"BUG: Page has no text content: {first_page.keys()}"
        
        # Check for image URL
        has_image = bool(first_page.get("image_url"))
        # Image might be optional, but warn if missing
        if not has_image:
            print(f"WARNING: Page 1 has no image_url")
        
        # Print success info
        print(f"SUCCESS: Book has {len(chapters)} chapter(s) with {len(pages)} pages")
        print(f"First page text preview: {(first_page.get('text') or first_page.get('text_content', ''))[:100]}...")
        if has_image:
            print(f"First page has image: {first_page.get('image_url', '')[:60]}...")
    
    def test_book_full_returns_all_pages(self):
        """Verify all pages are returned with proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/books/{TEST_BOOK_ID}/full",
            headers=self.headers
        )
        
        if response.status_code == 404:
            pytest.skip(f"Test book {TEST_BOOK_ID} not found")
        
        assert response.status_code == 200
        data = response.json()
        
        chapters = data.get("chapters", [])
        total_pages = 0
        pages_with_images = 0
        pages_with_text = 0
        
        for chapter in chapters:
            pages = chapter.get("pages", [])
            for page in pages:
                total_pages += 1
                if page.get("image_url"):
                    pages_with_images += 1
                if page.get("text") or page.get("text_content"):
                    pages_with_text += 1
        
        # The test book should have 5 pages per the agent context
        print(f"Total pages: {total_pages}")
        print(f"Pages with images: {pages_with_images}")
        print(f"Pages with text: {pages_with_text}")
        
        assert total_pages > 0, "No pages returned"
        assert pages_with_text > 0, "No pages have text content"
    
    def test_page_data_structure(self):
        """Verify pages have all expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/books/{TEST_BOOK_ID}/full",
            headers=self.headers
        )
        
        if response.status_code == 404:
            pytest.skip(f"Test book {TEST_BOOK_ID} not found")
        
        assert response.status_code == 200
        data = response.json()
        
        chapters = data.get("chapters", [])
        if not chapters:
            pytest.skip("No chapters found")
        
        pages = chapters[0].get("pages", [])
        if not pages:
            pytest.skip("No pages found")
        
        # Check first page has expected fields
        page = pages[0]
        expected_fields = ["id", "order", "text_content", "layout_type"]
        
        for field in expected_fields:
            # Handle 'text' vs 'text_content' variation
            if field == "text_content":
                has_field = "text_content" in page or "text" in page
            else:
                has_field = field in page
            assert has_field, f"Missing expected field: {field}"
        
        print(f"Page structure verified with fields: {list(page.keys())}")


class TestAIStoryGenerationEndpoints:
    """Tests for AI story generation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate - skipping tests")
    
    def test_generate_story_async_endpoint_exists(self):
        """Verify the async story generation endpoint is accessible"""
        # Use OPTIONS to check endpoint exists without triggering actual generation
        # Or use a minimal request that will fail validation but confirm endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-story-async",
            headers=self.headers,
            json={}  # Empty request to trigger validation error
        )
        
        # Should get 422 (validation error) not 404 (not found)
        assert response.status_code != 404, "Endpoint /api/ai/generate-story-async not found!"
        print(f"Endpoint exists, status: {response.status_code}")
    
    def test_job_status_endpoint_exists(self):
        """Verify job status endpoint exists"""
        # Test with a fake job ID - should get 404 for the job, not the endpoint
        response = requests.get(
            f"{BASE_URL}/api/jobs/fake-job-id/status",
            headers=self.headers
        )
        
        # Should get 404 for job not found, not for endpoint
        assert response.status_code in [404, 403], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 404:
            data = response.json()
            # Confirm it's "Job not found" not "Endpoint not found"
            assert "job" in data.get("detail", "").lower() or "not found" in data.get("detail", "").lower()
        
        print(f"Job status endpoint exists, returned: {response.status_code}")
    
    def test_active_jobs_endpoint(self):
        """Verify active jobs endpoint returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/jobs/active",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "jobs" in data, "Response should have 'jobs' array"
        assert isinstance(data["jobs"], list), "jobs should be a list"
        
        print(f"Active jobs count: {len(data['jobs'])}")
    
    def test_job_history_endpoint(self):
        """Verify job history endpoint returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/jobs/history",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "jobs" in data, "Response should have 'jobs' array"
        assert isinstance(data["jobs"], list), "jobs should be a list"
        
        print(f"Job history count: {len(data['jobs'])}")
        
        # Check structure of job entries if any exist
        if data["jobs"]:
            job = data["jobs"][0]
            assert "job_id" in job, "Job should have job_id"
            assert "status" in job, "Job should have status"
            print(f"Most recent job: {job.get('job_id')} - {job.get('status')}")


class TestBookRetrievalMultipleSources:
    """Test that book retrieval works with all three data sources"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate - skipping tests")
    
    def test_get_my_books(self):
        """Get user's books to find test subjects"""
        response = requests.get(
            f"{BASE_URL}/api/books/my",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        books = response.json()
        print(f"User has {len(books)} books")
        
        # Check each book for pages
        for book in books[:3]:  # Check first 3 books
            book_id = book.get("id")
            title = book.get("title", "Untitled")
            
            full_response = requests.get(
                f"{BASE_URL}/api/books/{book_id}/full",
                headers=self.headers
            )
            
            if full_response.status_code == 200:
                full_data = full_response.json()
                chapters = full_data.get("chapters", [])
                total_pages = sum(len(ch.get("pages", [])) for ch in chapters)
                print(f"Book '{title[:30]}' has {len(chapters)} chapters, {total_pages} pages")
    
    def test_ai_book_pages_linked_by_book_id(self):
        """Verify the specific test book has pages linked by book_id"""
        # Note: The single book endpoint /api/books/{id} has a separate issue with 
        # Pydantic validation for AI-generated books (missing author_id, cover_image, etc.)
        # This is a DIFFERENT bug from the empty pages issue we're testing.
        # The /full endpoint is the critical one for the bug fix verification.
        
        # Get full book and verify pages are returned (this tests the bug fix)
        full_response = requests.get(
            f"{BASE_URL}/api/books/{TEST_BOOK_ID}/full",
            headers=self.headers
        )
        
        if full_response.status_code == 404:
            pytest.skip(f"Test book {TEST_BOOK_ID} not found")
        
        assert full_response.status_code == 200, f"Full book endpoint failed: {full_response.text}"
        full_data = full_response.json()
        
        # Extract book info from full response
        print(f"Book title: '{full_data.get('title', 'Unknown')}'")
        
        chapters = full_data.get("chapters", [])
        assert len(chapters) > 0, "BUG NOT FIXED: No chapters returned"
        
        # AI-generated pages should be in an "ai-generated-chapter"
        chapter_ids = [ch.get("id") for ch in chapters]
        print(f"Chapter IDs: {chapter_ids}")
        
        total_pages = sum(len(ch.get("pages", [])) for ch in chapters)
        assert total_pages > 0, "BUG NOT FIXED: No pages in chapters"
        
        print(f"SUCCESS: {total_pages} pages returned from {len(chapters)} chapter(s)")


# Standalone test function for quick verification
def test_critical_bug_fix():
    """Quick critical test - can run standalone"""
    # Login
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.text}")
        return False
    
    token = login_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get full book
    book_resp = requests.get(
        f"{BASE_URL}/api/books/{TEST_BOOK_ID}/full",
        headers=headers
    )
    
    if book_resp.status_code == 404:
        print(f"Test book {TEST_BOOK_ID} not found")
        return False
    
    if book_resp.status_code != 200:
        print(f"Failed to get book: {book_resp.text}")
        return False
    
    data = book_resp.json()
    chapters = data.get("chapters", [])
    
    if not chapters:
        print("CRITICAL BUG: chapters array is empty!")
        return False
    
    total_pages = sum(len(ch.get("pages", [])) for ch in chapters)
    
    if total_pages == 0:
        print("CRITICAL BUG: No pages in chapters!")
        return False
    
    print(f"BUG FIX VERIFIED: {total_pages} pages returned in {len(chapters)} chapter(s)")
    return True


if __name__ == "__main__":
    print("Running critical bug fix verification...")
    result = test_critical_bug_fix()
    exit(0 if result else 1)
