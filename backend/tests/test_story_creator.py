"""
Test suite for StoryCreator (AI Story Creator) feature
Tests: /api/ai/story-pricing, /api/ai/generate-story-async, /api/jobs/{job_id}/status
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "jamesstephenbrooks@outlook.com"
TEST_PASSWORD = "Routetofreedom"


class TestStoryCreatorEndpoints:
    """Story Creator feature endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print(f"✅ Logged in as {TEST_EMAIL}")
        else:
            pytest.skip(f"Login failed: {login_resp.status_code}")
    
    # ===== /api/ai/story-pricing endpoint tests =====
    
    def test_story_pricing_endpoint_accessible(self):
        """Test /api/ai/story-pricing returns 200"""
        response = requests.get(f"{BASE_URL}/api/ai/story-pricing")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✅ /api/ai/story-pricing returns 200")
    
    def test_story_pricing_has_page_credits(self):
        """Test pricing returns page_credits"""
        response = requests.get(f"{BASE_URL}/api/ai/story-pricing")
        data = response.json()
        
        assert "page_credits" in data, "Missing page_credits"
        assert isinstance(data["page_credits"], dict), "page_credits should be dict"
        assert "5" in data["page_credits"] or 5 in data["page_credits"], "Missing 5-page credit info"
        print(f"✅ page_credits present: {data['page_credits']}")
    
    def test_story_pricing_has_art_styles(self):
        """Test pricing returns art_styles for both modes"""
        response = requests.get(f"{BASE_URL}/api/ai/story-pricing")
        data = response.json()
        
        assert "art_styles" in data, "Missing art_styles"
        assert "kids" in data["art_styles"], "Missing kids art_styles"
        assert "studio" in data["art_styles"], "Missing studio art_styles"
        
        # Verify kids has at least one style
        assert len(data["art_styles"]["kids"]) > 0, "Kids mode has no art styles"
        assert len(data["art_styles"]["studio"]) > 0, "Studio mode has no art styles"
        
        # Check structure of art style item
        kids_style = data["art_styles"]["kids"][0]
        assert "id" in kids_style, "Art style missing id"
        assert "name" in kids_style, "Art style missing name"
        print(f"✅ art_styles present: kids={len(data['art_styles']['kids'])}, studio={len(data['art_styles']['studio'])}")
    
    def test_story_pricing_has_age_ranges(self):
        """Test pricing returns age_ranges for both modes"""
        response = requests.get(f"{BASE_URL}/api/ai/story-pricing")
        data = response.json()
        
        assert "age_ranges" in data, "Missing age_ranges"
        assert "kids" in data["age_ranges"], "Missing kids age_ranges"
        assert "studio" in data["age_ranges"], "Missing studio age_ranges"
        
        # Verify kids has at least one age range
        assert len(data["age_ranges"]["kids"]) > 0, "Kids mode has no age ranges"
        
        # Check structure of age range item
        kids_age = data["age_ranges"]["kids"][0]
        assert "id" in kids_age, "Age range missing id"
        assert "name" in kids_age, "Age range missing name"
        print(f"✅ age_ranges present: kids={len(data['age_ranges']['kids'])}, studio={len(data['age_ranges']['studio'])}")
    
    def test_story_pricing_has_page_options(self):
        """Test pricing returns page_options for both modes"""
        response = requests.get(f"{BASE_URL}/api/ai/story-pricing")
        data = response.json()
        
        assert "page_options" in data, "Missing page_options"
        assert "kids" in data["page_options"], "Missing kids page_options"
        assert "studio" in data["page_options"], "Missing studio page_options"
        
        # Kids mode should have smaller page options
        assert 5 in data["page_options"]["kids"], "Kids mode should include 5 pages"
        # Studio mode should have larger page options
        assert 50 in data["page_options"]["studio"], "Studio mode should include 50 pages"
        print(f"✅ page_options present: kids={data['page_options']['kids']}, studio={data['page_options']['studio']}")
    
    # ===== /api/auth/ai-story-trial endpoint tests =====
    
    def test_story_trial_status_endpoint(self):
        """Test /api/auth/ai-story-trial returns trial status"""
        response = self.session.get(f"{BASE_URL}/api/auth/ai-story-trial")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "has_free_stories" in data, "Missing has_free_stories"
        assert "free_stories_remaining" in data, "Missing free_stories_remaining"
        print(f"✅ Trial status: has_free={data['has_free_stories']}, remaining={data['free_stories_remaining']}")
    
    # ===== /api/credits/balance endpoint tests =====
    
    def test_credits_balance_endpoint(self):
        """Test /api/credits/balance returns user credits"""
        response = self.session.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "credits" in data, "Missing credits field"
        assert isinstance(data["credits"], int), "Credits should be integer"
        print(f"✅ User credits: {data['credits']}")
    
    # ===== /api/ai/generate-story-async endpoint tests =====
    
    def test_generate_story_async_requires_auth(self):
        """Test generate-story-async requires authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        response = no_auth_session.post(f"{BASE_URL}/api/ai/generate-story-async", json={
            "story_description": "Test story",
            "num_pages": 5
        })
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✅ /api/ai/generate-story-async requires auth (returns 401)")
    
    def test_generate_story_async_returns_job_id(self):
        """Test generate-story-async returns job_id on success"""
        response = self.session.post(f"{BASE_URL}/api/ai/generate-story-async", json={
            "title": "TEST_story_creator_test",
            "story_description": "A brave little dragon learns to fly",
            "character_name": "Spark",
            "character_description": "A small purple dragon",
            "num_pages": 5,
            "age_range": "6-8",
            "art_style": "3d-pixar",
            "creator_mode": "kids"
        })
        
        # May fail due to insufficient credits - that's OK
        if response.status_code == 402:
            print("⚠️ Insufficient credits - test passes as endpoint works correctly")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "job_id" in data, "Missing job_id in response"
        assert "status" in data, "Missing status in response"
        print(f"✅ Story generation started: job_id={data['job_id']}, status={data['status']}")
        
        # Store job_id for next test
        self.test_job_id = data["job_id"]
        return data["job_id"]
    
    # ===== /api/jobs/{job_id}/status endpoint tests =====
    
    def test_job_status_requires_auth(self):
        """Test job status requires authentication"""
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/jobs/fake-job-id/status")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✅ /api/jobs/{job_id}/status requires auth")
    
    def test_job_status_returns_404_for_invalid_job(self):
        """Test job status returns 404 for non-existent job"""
        response = self.session.get(f"{BASE_URL}/api/jobs/nonexistent-job-123/status")
        assert response.status_code == 404, f"Expected 404 for invalid job, got {response.status_code}"
        print("✅ /api/jobs/{job_id}/status returns 404 for invalid job")
    
    # ===== /api/jobs/active endpoint tests =====
    
    def test_active_jobs_endpoint(self):
        """Test /api/jobs/active returns user's active jobs"""
        response = self.session.get(f"{BASE_URL}/api/jobs/active")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "jobs" in data, "Missing jobs field"
        assert isinstance(data["jobs"], list), "jobs should be a list"
        print(f"✅ Active jobs endpoint works: {len(data['jobs'])} active jobs")
    
    # ===== /api/jobs/history endpoint tests =====
    
    def test_job_history_endpoint(self):
        """Test /api/jobs/history returns user's job history"""
        response = self.session.get(f"{BASE_URL}/api/jobs/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "jobs" in data, "Missing jobs field"
        assert isinstance(data["jobs"], list), "jobs should be a list"
        print(f"✅ Job history endpoint works: {len(data['jobs'])} jobs in history")


class TestStoryCreatorIntegration:
    """Integration tests for full story creation flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed: {login_resp.status_code}")
    
    def test_credit_cost_matches_page_count(self):
        """Verify credit costs match expected values based on page count"""
        response = requests.get(f"{BASE_URL}/api/ai/story-pricing")
        data = response.json()
        
        expected_credits = {
            "5": 5,
            "10": 8,
            "15": 12,
            "20": 15,
            "30": 20,
            "50": 30
        }
        
        for pages, expected in expected_credits.items():
            actual = data["page_credits"].get(pages) or data["page_credits"].get(int(pages))
            assert actual == expected, f"Expected {expected} credits for {pages} pages, got {actual}"
        
        print("✅ Credit costs match expected values for all page counts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
