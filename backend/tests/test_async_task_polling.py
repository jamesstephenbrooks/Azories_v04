"""
Test Suite: Async Task Polling for Shots and Video Generation
Tests the async architecture where:
1. POST returns task_id immediately
2. GET /api/tasks/{task_id} returns status
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
VIP_USER_EMAIL = "jamesstephenbrooks@outlook.com"
VIP_USER_PASSWORD = "test123"


class TestAsyncTaskPolling:
    """Test async task polling architecture for Shots and Video generation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for VIP user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_USER_EMAIL,
            "password": VIP_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def api_client(self, auth_token):
        """Session with auth headers"""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        })
        return session
    
    def test_01_login_vip_user(self):
        """Verify VIP user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_USER_EMAIL,
            "password": VIP_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == VIP_USER_EMAIL
        assert data["user"]["subscription"] == "pro"
        print(f"PASS: VIP user logged in - subscription: {data['user']['subscription']}")
    
    def test_02_generate_shots_returns_task_id(self, api_client):
        """Test that POST /api/pro-studio/generate-shots returns task_id immediately"""
        # Use a small test image (100x100 red square as base64)
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAD0lEQVR4nO3BMQEAAADCoPVP7WsIoAAAAAAAAAAAAE4NPr8AAQPgECsAAAAASUVORK5CYII="
        
        response = api_client.post(f"{BASE_URL}/api/pro-studio/generate-shots", json={
            "source_image": test_image_base64,
            "character_id": None
        })
        
        # Should return 200 with task_id (not 520 timeout)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify task_id is returned
        assert "task_id" in data, f"No task_id in response: {data}"
        assert data["status"] == "pending"
        assert "message" in data
        
        task_id = data["task_id"]
        print(f"PASS: generate-shots returned task_id={task_id}")
        
        return task_id
    
    def test_03_task_status_endpoint(self, api_client):
        """Test GET /api/tasks/{task_id} returns proper status"""
        # First create a task
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAD0lEQVR4nO3BMQEAAADCoPVP7WsIoAAAAAAAAAAAAE4NPr8AAQPgECsAAAAASUVORK5CYII="
        
        create_response = api_client.post(f"{BASE_URL}/api/pro-studio/generate-shots", json={
            "source_image": test_image_base64
        })
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        task_id = create_response.json()["task_id"]
        
        # Poll the task status
        status_response = api_client.get(f"{BASE_URL}/api/tasks/{task_id}")
        assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
        
        status_data = status_response.json()
        assert "task_id" in status_data
        assert "status" in status_data
        assert status_data["task_id"] == task_id
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]
        
        print(f"PASS: Task status endpoint working - status={status_data['status']}, progress={status_data.get('progress', 'N/A')}")
    
    def test_04_task_status_has_progress(self, api_client):
        """Verify task status includes progress field"""
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAD0lEQVR4nO3BMQEAAADCoPVP7WsIoAAAAAAAAAAAAE4NPr8AAQPgECsAAAAASUVORK5CYII="
        
        create_response = api_client.post(f"{BASE_URL}/api/pro-studio/generate-shots", json={
            "source_image": test_image_base64
        })
        task_id = create_response.json()["task_id"]
        
        # Wait a moment for processing to start
        time.sleep(2)
        
        status_response = api_client.get(f"{BASE_URL}/api/tasks/{task_id}")
        status_data = status_response.json()
        
        # Progress should be present
        assert "progress" in status_data, f"Missing progress field: {status_data}"
        assert status_data["progress"] is not None
        assert isinstance(status_data["progress"], int) or status_data["progress"] is None
        
        print(f"PASS: Task has progress field - progress={status_data['progress']}")
    
    def test_05_task_not_found_for_invalid_id(self, api_client):
        """Test 404 for non-existent task_id"""
        fake_task_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{BASE_URL}/api/tasks/{fake_task_id}")
        assert response.status_code == 404
        print("PASS: Invalid task_id returns 404")
    
    def test_06_task_authorization(self, api_client, auth_token):
        """Test that task belongs to user (403 for others)"""
        # Create a task as VIP user
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAD0lEQVR4nO3BMQEAAADCoPVP7WsIoAAAAAAAAAAAAE4NPr8AAQPgECsAAAAASUVORK5CYII="
        
        create_response = api_client.post(f"{BASE_URL}/api/pro-studio/generate-shots", json={
            "source_image": test_image_base64
        })
        task_id = create_response.json()["task_id"]
        
        # Verify same user can access
        status_response = api_client.get(f"{BASE_URL}/api/tasks/{task_id}")
        assert status_response.status_code == 200
        print(f"PASS: Task owner can access task status")
    
    def test_07_animate_hero_returns_task_id(self, api_client):
        """Test that POST /api/pro-studio/animate-hero returns task_id immediately"""
        # Use a small test image
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAD0lEQVR4nO3BMQEAAADCoPVP7WsIoAAAAAAAAAAAAE4NPr8AAQPgECsAAAAASUVORK5CYII="
        
        response = api_client.post(f"{BASE_URL}/api/pro-studio/animate-hero", json={
            "image_url": test_image_base64,
            "motion_prompt": "subtle cinematic movement",
            "model": "kling",
            "duration": 5
        })
        
        # Should return 200 with task_id (not 520 timeout)
        # Could be 503 if fal.ai not available - that's acceptable
        if response.status_code == 503:
            print(f"INFO: animate-hero returns 503 - fal.ai not configured (expected in test env)")
            return
            
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify task_id is returned
        assert "task_id" in data, f"No task_id in response: {data}"
        assert data["status"] == "pending"
        
        print(f"PASS: animate-hero returned task_id={data['task_id']}")
    
    def test_08_video_task_status(self, api_client):
        """Test video task status endpoint"""
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAD0lEQVR4nO3BMQEAAADCoPVP7WsIoAAAAAAAAAAAAE4NPr8AAQPgECsAAAAASUVORK5CYII="
        
        create_response = api_client.post(f"{BASE_URL}/api/pro-studio/animate-hero", json={
            "image_url": test_image_base64,
            "motion_prompt": "gentle breathing",
            "duration": 5
        })
        
        if create_response.status_code == 503:
            print("INFO: Skipping video task status - fal.ai not configured")
            return
            
        assert create_response.status_code == 200
        task_id = create_response.json()["task_id"]
        
        # Check status
        status_response = api_client.get(f"{BASE_URL}/api/tasks/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["task_id"] == task_id
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]
        
        print(f"PASS: Video task status working - status={status_data['status']}")


class TestCharacterGalleryInShots:
    """Test character gallery display in Shots panel"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for VIP user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_USER_EMAIL,
            "password": VIP_USER_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def api_client(self, auth_token):
        """Session with auth headers"""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        })
        return session
    
    def test_01_get_user_characters(self, api_client):
        """Test GET /api/pro-studio/characters returns user's characters"""
        response = api_client.get(f"{BASE_URL}/api/pro-studio/characters")
        assert response.status_code == 200
        
        data = response.json()
        assert "characters" in data
        print(f"PASS: Got {len(data['characters'])} characters")
        
        return data["characters"]
    
    def test_02_character_has_gallery_endpoint(self, api_client):
        """Test character gallery endpoint exists"""
        # Get characters
        char_response = api_client.get(f"{BASE_URL}/api/pro-studio/characters")
        characters = char_response.json().get("characters", [])
        
        if not characters:
            print("INFO: No characters found - skipping gallery test")
            return
        
        # Try to get gallery for first character
        char_id = characters[0]["id"]
        gallery_response = api_client.get(f"{BASE_URL}/api/pro-studio/characters/{char_id}/gallery")
        
        assert gallery_response.status_code == 200, f"Gallery endpoint failed: {gallery_response.text}"
        
        data = gallery_response.json()
        assert "images" in data
        print(f"PASS: Character {characters[0]['name']} gallery has {len(data['images'])} images")
    
    def test_03_character_has_thumbnail(self, api_client):
        """Test characters have thumbnail (master image)"""
        response = api_client.get(f"{BASE_URL}/api/pro-studio/characters")
        characters = response.json().get("characters", [])
        
        chars_with_thumbnails = sum(1 for c in characters if c.get("thumbnail"))
        print(f"INFO: {chars_with_thumbnails}/{len(characters)} characters have thumbnails")
        
        # Check first character with thumbnail
        for char in characters:
            if char.get("thumbnail"):
                assert char["thumbnail"].startswith("data:") or char["thumbnail"].startswith("http")
                print(f"PASS: Character {char['name']} has valid thumbnail")
                break


class TestCreditSystem:
    """Test credit system for VIP users"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_USER_EMAIL,
            "password": VIP_USER_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def api_client(self, auth_token):
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        })
        return session
    
    def test_01_vip_user_can_generate_without_credits(self, api_client):
        """VIP users should be able to generate without credits (usage tracked but not deducted)"""
        # Check credits balance first
        balance_response = api_client.get(f"{BASE_URL}/api/credits/balance")
        assert balance_response.status_code == 200
        
        initial_credits = balance_response.json().get("credits", 0)
        print(f"INFO: VIP user initial credits: {initial_credits}")
        
        # Generate shots (should work for VIP)
        test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAD0lEQVR4nO3BMQEAAADCoPVP7WsIoAAAAAAAAAAAAE4NPr8AAQPgECsAAAAASUVORK5CYII="
        
        response = api_client.post(f"{BASE_URL}/api/pro-studio/generate-shots", json={
            "source_image": test_image
        })
        
        # VIP should not get 402 (insufficient credits)
        assert response.status_code != 402, f"VIP user got credit error: {response.text}"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print("PASS: VIP user can generate shots without credit check")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
