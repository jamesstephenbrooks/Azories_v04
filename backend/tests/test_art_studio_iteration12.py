"""
Test Art Studio features - Iteration 12
Tests:
1. Prompt History API - GET /api/art-studio/prompt-history
2. Prompt History API - POST /api/art-studio/prompt-history
3. Expert Mode StyleNode dropdown functionality (UI test)
4. Expert Mode Image Node resize (UI test)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER = {
    "email": "testuser3@example.com",
    "password": "password123"
}

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    if response.status_code == 200:
        return response.json().get("access_token")
    # Try registering if login fails
    register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "name": "Test User 3"
    })
    if register_response.status_code == 200:
        return register_response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture
def auth_headers(auth_token):
    """Get headers with authentication"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPromptHistoryAPI:
    """Test Prompt History endpoints"""
    
    def test_get_prompt_history_empty(self, auth_headers):
        """Test GET /api/art-studio/prompt-history returns empty history initially or existing history"""
        response = requests.get(f"{BASE_URL}/api/art-studio/prompt-history", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "history" in data, "Response should contain 'history' key"
        assert isinstance(data["history"], list), "History should be a list"
        print(f"GET prompt-history returned {len(data['history'])} prompts")
    
    def test_save_prompt_to_history(self, auth_headers):
        """Test POST /api/art-studio/prompt-history saves a prompt"""
        test_prompt = "TEST_A magical dragon flying over mountains"
        
        response = requests.post(
            f"{BASE_URL}/api/art-studio/prompt-history",
            headers=auth_headers,
            json={"prompt": test_prompt}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Should return success=True"
        print(f"POST prompt-history succeeded: {data}")
        
    def test_verify_prompt_saved(self, auth_headers):
        """Verify the saved prompt appears in GET response"""
        # Save a unique prompt
        test_prompt = "TEST_Unique test prompt for verification"
        
        # Save first
        save_response = requests.post(
            f"{BASE_URL}/api/art-studio/prompt-history",
            headers=auth_headers,
            json={"prompt": test_prompt}
        )
        assert save_response.status_code == 200
        
        # Then verify it's in the list
        get_response = requests.get(f"{BASE_URL}/api/art-studio/prompt-history", headers=auth_headers)
        assert get_response.status_code == 200
        
        history = get_response.json().get("history", [])
        assert test_prompt in history, f"Saved prompt should be in history. History: {history}"
        # Should be at the top (most recent)
        assert history[0] == test_prompt, "Most recently saved prompt should be first"
        print(f"Prompt verified at top of history: {history[0]}")
    
    def test_empty_prompt_not_saved(self, auth_headers):
        """Test that empty prompts are not saved"""
        response = requests.post(
            f"{BASE_URL}/api/art-studio/prompt-history",
            headers=auth_headers,
            json={"prompt": ""}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, "Empty prompt should return success=False"
        print("Empty prompt correctly rejected")
    
    def test_duplicate_prompt_moves_to_top(self, auth_headers):
        """Test that adding a duplicate prompt moves it to the top"""
        # Save two prompts
        prompt1 = "TEST_First prompt in list"
        prompt2 = "TEST_Second prompt in list"
        
        requests.post(f"{BASE_URL}/api/art-studio/prompt-history", headers=auth_headers, json={"prompt": prompt1})
        requests.post(f"{BASE_URL}/api/art-studio/prompt-history", headers=auth_headers, json={"prompt": prompt2})
        
        # Now save prompt1 again - it should move to top
        requests.post(f"{BASE_URL}/api/art-studio/prompt-history", headers=auth_headers, json={"prompt": prompt1})
        
        # Verify order
        get_response = requests.get(f"{BASE_URL}/api/art-studio/prompt-history", headers=auth_headers)
        history = get_response.json().get("history", [])
        
        # prompt1 should now be at the top
        assert history[0] == prompt1, f"Duplicate prompt should be moved to top. Got: {history[:3]}"
        print(f"Duplicate prompt correctly moved to top: {history[0]}")
    
    def test_prompt_history_requires_auth(self):
        """Test that endpoints require authentication"""
        # GET without auth
        response = requests.get(f"{BASE_URL}/api/art-studio/prompt-history")
        assert response.status_code == 401, "GET should require authentication"
        
        # POST without auth
        response = requests.post(
            f"{BASE_URL}/api/art-studio/prompt-history",
            json={"prompt": "test"}
        )
        assert response.status_code == 401, "POST should require authentication"
        print("Authentication correctly required for both endpoints")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
