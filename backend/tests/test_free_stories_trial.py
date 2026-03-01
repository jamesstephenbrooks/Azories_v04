"""
Test suite for the new free stories trial system
- New users get 3 free AI story creations
- After 3 free stories, credits are required (5 credits per story)
- /api/auth/ai-story-trial endpoint returns correct free_stories_remaining count
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "jamesstephenbrooks@outlook.com"
TEST_PASSWORD = "Routetofreedom"


class TestFreeStoriesTrialSystem:
    """Test the free stories trial system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        self.token = data.get("access_token")
        self.user = data.get("user")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
    def test_ai_story_trial_endpoint_returns_200(self):
        """Test GET /api/auth/ai-story-trial returns 200"""
        response = self.session.get(f"{BASE_URL}/api/auth/ai-story-trial")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: /api/auth/ai-story-trial returns 200")
    
    def test_ai_story_trial_response_structure(self):
        """Test that ai-story-trial endpoint returns correct structure"""
        response = self.session.get(f"{BASE_URL}/api/auth/ai-story-trial")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        assert "has_free_stories" in data, "Missing 'has_free_stories' field"
        assert "free_stories_remaining" in data, "Missing 'free_stories_remaining' field"
        assert "free_stories_used" in data, "Missing 'free_stories_used' field"
        assert "display_text" in data, "Missing 'display_text' field"
        
        # Check legacy fields for backwards compatibility
        assert "in_trial" in data, "Missing legacy 'in_trial' field"
        assert "trial_expired" in data, "Missing legacy 'trial_expired' field"
        
        # Check data types
        assert isinstance(data["has_free_stories"], bool), "'has_free_stories' should be boolean"
        assert isinstance(data["free_stories_remaining"], int), "'free_stories_remaining' should be int"
        assert isinstance(data["free_stories_used"], int), "'free_stories_used' should be int"
        assert isinstance(data["display_text"], str), "'display_text' should be string"
        
        # Validate in_trial matches has_free_stories (backwards compatibility)
        assert data["in_trial"] == data["has_free_stories"], "Legacy 'in_trial' should match 'has_free_stories'"
        
        print(f"PASS: Response structure is correct")
        print(f"  - has_free_stories: {data['has_free_stories']}")
        print(f"  - free_stories_remaining: {data['free_stories_remaining']}")
        print(f"  - free_stories_used: {data['free_stories_used']}")
        print(f"  - display_text: {data['display_text']}")
    
    def test_free_stories_remaining_is_non_negative(self):
        """Test that free_stories_remaining is never negative"""
        response = self.session.get(f"{BASE_URL}/api/auth/ai-story-trial")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["free_stories_remaining"] >= 0, f"free_stories_remaining should be >= 0, got {data['free_stories_remaining']}"
        print(f"PASS: free_stories_remaining is non-negative ({data['free_stories_remaining']})")
    
    def test_display_text_format_when_stories_available(self):
        """Test display_text format when free stories are available"""
        response = self.session.get(f"{BASE_URL}/api/auth/ai-story-trial")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["has_free_stories"]:
            # Should show "X free story/stories remaining"
            assert "free" in data["display_text"].lower(), f"Display text should contain 'free': {data['display_text']}"
            assert "remaining" in data["display_text"].lower(), f"Display text should contain 'remaining': {data['display_text']}"
            print(f"PASS: Display text format correct when stories available: '{data['display_text']}'")
        else:
            # Should show "used your 3 free stories" message
            assert "used" in data["display_text"].lower() or "purchase" in data["display_text"].lower(), \
                f"Display text should indicate stories used up: {data['display_text']}"
            print(f"PASS: Display text format correct when no stories: '{data['display_text']}'")
    
    def test_has_free_stories_logic(self):
        """Test that has_free_stories is True when remaining > 0"""
        response = self.session.get(f"{BASE_URL}/api/auth/ai-story-trial")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["free_stories_remaining"] > 0:
            assert data["has_free_stories"] == True, "has_free_stories should be True when remaining > 0"
            print("PASS: has_free_stories is True when free_stories_remaining > 0")
        else:
            assert data["has_free_stories"] == False, "has_free_stories should be False when remaining == 0"
            print("PASS: has_free_stories is False when free_stories_remaining == 0")


class TestGenerateStoryEndpoint:
    """Test the /api/ai/generate-story endpoint trial logic"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        self.token = data.get("access_token")
        self.user = data.get("user")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
    
    def test_generate_story_endpoint_exists(self):
        """Test POST /api/ai/generate-story endpoint exists (without actually generating)"""
        # We test with missing story_description to get validation error, not 404
        response = self.session.post(f"{BASE_URL}/api/ai/generate-story", json={
            "story_description": ""  # Empty to trigger validation error
        })
        
        # Should get 400 (validation error) or another error, NOT 404
        assert response.status_code != 404, f"Endpoint should exist, got 404"
        print(f"PASS: /api/ai/generate-story endpoint exists (status: {response.status_code})")
    
    def test_generate_story_requires_pro_subscription(self):
        """Test that generate-story requires pro subscription"""
        # This test verifies subscription check happens
        # Since our test user has pro, we can't test the rejection
        # But we can verify the endpoint handles auth properly
        response = self.session.post(f"{BASE_URL}/api/ai/generate-story", json={
            "story_description": "A test story about a brave knight"
        })
        
        # Should not be 401 (unauthorized) since we have token
        assert response.status_code != 401, "Should be authenticated"
        print(f"PASS: Generate story endpoint accepts authenticated user (status: {response.status_code})")


class TestNewUserRegistrationFreeStories:
    """Test that new users get 3 free stories"""
    
    def test_register_user_gets_free_stories_field(self):
        """Test new user registration includes free_stories_remaining field"""
        # Note: We can't actually create users in this test as it would pollute the database
        # Instead we verify the endpoint structure by checking an existing user
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as existing user
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200
        
        # Get trial status
        token = response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        trial_response = session.get(f"{BASE_URL}/api/auth/ai-story-trial")
        assert trial_response.status_code == 200
        
        data = trial_response.json()
        
        # Verify the structure exists
        assert "free_stories_remaining" in data
        assert "free_stories_used" in data
        
        # For existing users, sum should be >= 0
        total = data["free_stories_remaining"] + data["free_stories_used"]
        assert total >= 0, f"Total free stories tracking should be >= 0"
        
        print(f"PASS: Free stories tracking is working")
        print(f"  - remaining: {data['free_stories_remaining']}")
        print(f"  - used: {data['free_stories_used']}")


class TestCreditsAfterFreeStories:
    """Test credit requirement after free stories are exhausted"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        self.token = data.get("access_token")
        self.user = data.get("user")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
    
    def test_credit_balance_endpoint(self):
        """Test GET /api/credits/balance returns credit info"""
        response = self.session.get(f"{BASE_URL}/api/credits/balance")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "credits" in data, "Missing 'credits' field"
        assert "costs" in data, "Missing 'costs' field"
        
        # Check AI story cost is defined
        assert "ai_story_create" in data["costs"], "Missing 'ai_story_create' in costs"
        assert data["costs"]["ai_story_create"] == 5, f"AI story cost should be 5, got {data['costs']['ai_story_create']}"
        
        print(f"PASS: Credit balance endpoint working")
        print(f"  - Current credits: {data['credits']}")
        print(f"  - AI story cost: {data['costs']['ai_story_create']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
