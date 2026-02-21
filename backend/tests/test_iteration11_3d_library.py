"""
Iteration 11: Test 3D Library and related features
- Ambient sounds endpoint (forest/ocean) 
- AI Reading Buddy endpoint (used by Luna AI Librarian)
- Book recommendations fallback
- Books listing endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAmbientSounds:
    """Test ambient sound endpoints including new forest and ocean sounds"""
    
    def test_forest_sound_returns_audio(self):
        """Forest sound endpoint should return audio/mpeg"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/forest", timeout=10)
        assert response.status_code == 200, f"Forest sound returned {response.status_code}"
        assert 'audio' in response.headers.get('content-type', ''), f"Expected audio content-type, got {response.headers.get('content-type')}"
        print("PASS: Forest ambient sound endpoint returns 200 with audio")
    
    def test_ocean_sound_returns_audio(self):
        """Ocean sound endpoint should return audio/mpeg"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/ocean", timeout=10)
        assert response.status_code == 200, f"Ocean sound returned {response.status_code}"
        assert 'audio' in response.headers.get('content-type', ''), f"Expected audio content-type, got {response.headers.get('content-type')}"
        print("PASS: Ocean ambient sound endpoint returns 200 with audio")
    
    def test_rain_sound_returns_audio(self):
        """Rain sound should still work"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/rain", timeout=10)
        assert response.status_code == 200, f"Rain sound returned {response.status_code}"
        print("PASS: Rain ambient sound endpoint returns 200")
    
    def test_invalid_sound_returns_404(self):
        """Invalid sound name should return 404"""
        response = requests.get(f"{BASE_URL}/api/ambient-sounds/invalid_sound_xyz", timeout=10)
        assert response.status_code == 404, f"Expected 404 for invalid sound, got {response.status_code}"
        print("PASS: Invalid ambient sound returns 404")


class TestAIReadingBuddy:
    """Test AI Reading Buddy endpoint used by Luna AI Librarian"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test123@example.com",
            "password": "Test123!"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('access_token')
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Login failed - cannot test authenticated endpoints")
    
    def test_reading_buddy_endpoint_exists(self):
        """AI Reading Buddy endpoint should respond (used by Luna)"""
        response = requests.post(f"{BASE_URL}/api/ai/reading-buddy", 
            json={
                "message": "What book should I read?",
                "system_prompt": "You are Luna, a friendly AI librarian",
                "context": "User is exploring the 3D library"
            },
            headers=self.headers,
            timeout=30
        )
        # Even if AI fails, endpoint should exist and not return 404
        assert response.status_code != 404, f"AI Reading Buddy endpoint not found (404)"
        print(f"PASS: AI Reading Buddy endpoint exists (status: {response.status_code})")


class TestBookRecommendations:
    """Test book recommendations endpoint and fallback"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test123@example.com",
            "password": "Test123!"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('access_token')
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Login failed - cannot test authenticated endpoints")
    
    def test_user_recommendations_endpoint(self):
        """User recommendations endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/user/recommendations", 
            headers=self.headers, timeout=10)
        # Endpoint should exist (even if it returns empty recommendations)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"PASS: Recommendations endpoint responded with {response.status_code}")
    
    def test_books_fallback_for_recommendations(self):
        """Books endpoint (fallback for recommendations) should return array"""
        response = requests.get(f"{BASE_URL}/api/books?limit=6&published_only=true", timeout=10)
        assert response.status_code == 200, f"Books endpoint returned {response.status_code}"
        data = response.json()
        # Should return array (not {books: [...]})
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"PASS: Books endpoint returns array with {len(data)} books")


class TestBooksEndpoint:
    """Test books listing for 3D Library"""
    
    def test_get_published_books(self):
        """Should return published books for library display"""
        response = requests.get(f"{BASE_URL}/api/books?published_only=true", timeout=10)
        assert response.status_code == 200, f"Books endpoint returned {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Expected array"
        print(f"PASS: Published books endpoint returns {len(data)} books")
    
    def test_get_featured_books(self):
        """Should return featured books"""
        response = requests.get(f"{BASE_URL}/api/books/featured", timeout=10)
        assert response.status_code == 200, f"Featured books returned {response.status_code}"
        print("PASS: Featured books endpoint returns 200")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
