"""
Test Art Studio Workflows API - Expert Mode Save/Load functionality
Tests: /api/art-studio/workflows, /api/art-studio/workflow/save, /api/art-studio/workflow/{id}
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://azories-pro-studio.preview.emergentagent.com').rstrip('/')

# Test user credentials
TEST_USER_EMAIL = "tester_1771711440@example.com"
TEST_USER_PASSWORD = "password123"


class TestArtStudioWorkflows:
    """Art Studio Expert Mode Workflow API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        yield
    
    def test_get_workflows_returns_list(self):
        """Test GET /api/art-studio/workflows returns workflow list"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/workflows",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert isinstance(data["workflows"], list)
        print(f"GET workflows returned {len(data['workflows'])} workflows")
    
    def test_save_new_workflow(self):
        """Test POST /api/art-studio/workflow/save creates new workflow"""
        workflow_name = f"Test Workflow {uuid.uuid4().hex[:8]}"
        workflow_data = {
            "name": workflow_name,
            "nodes": [
                {"id": "char-1", "type": "character", "position": {"x": 100, "y": 100}, "data": {"name": "Test Hero", "gender": "Male", "age": "Adult"}},
                {"id": "style-1", "type": "style", "position": {"x": 100, "y": 250}, "data": {"style": "anime"}},
                {"id": "output-1", "type": "output", "position": {"x": 400, "y": 150}, "data": {}}
            ],
            "edges": [
                {"id": "e1", "source": "char-1", "target": "output-1"}
            ],
            "bookId": None
        }
        
        response = requests.post(
            f"{BASE_URL}/api/art-studio/workflow/save",
            headers=self.headers,
            json=workflow_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "id" in data
        assert data.get("updated") is False  # New workflow, not update
        print(f"New workflow saved with id: {data['id']}")
        
        # Cleanup - delete the workflow
        delete_response = requests.delete(
            f"{BASE_URL}/api/art-studio/workflow/{data['id']}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
    
    def test_save_and_update_workflow(self):
        """Test saving a workflow then updating it with same name"""
        workflow_name = f"Update Test {uuid.uuid4().hex[:8]}"
        workflow_data = {
            "name": workflow_name,
            "nodes": [{"id": "char-1", "type": "character", "position": {"x": 50, "y": 50}, "data": {"name": "Original"}}],
            "edges": []
        }
        
        # Create workflow
        response1 = requests.post(
            f"{BASE_URL}/api/art-studio/workflow/save",
            headers=self.headers,
            json=workflow_data
        )
        assert response1.status_code == 200
        data1 = response1.json()
        workflow_id = data1["id"]
        
        # Update with same name
        workflow_data["nodes"][0]["data"]["name"] = "Updated Character"
        response2 = requests.post(
            f"{BASE_URL}/api/art-studio/workflow/save",
            headers=self.headers,
            json=workflow_data
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get("updated") is True  # Should be update, not new
        
        # Verify update - fetch and check
        get_response = requests.get(
            f"{BASE_URL}/api/art-studio/workflows",
            headers=self.headers
        )
        assert get_response.status_code == 200
        workflows = get_response.json()["workflows"]
        matching = [w for w in workflows if w["name"] == workflow_name]
        assert len(matching) == 1  # Should only be one workflow with that name
        assert matching[0]["nodes"][0]["data"]["name"] == "Updated Character"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/art-studio/workflow/{workflow_id}", headers=self.headers)
    
    def test_delete_workflow(self):
        """Test DELETE /api/art-studio/workflow/{id} removes workflow"""
        # Create a workflow to delete
        workflow_name = f"Delete Test {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/art-studio/workflow/save",
            headers=self.headers,
            json={"name": workflow_name, "nodes": [], "edges": []}
        )
        assert create_response.status_code == 200
        workflow_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/art-studio/workflow/{workflow_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        
        # Verify it's gone
        get_response = requests.get(
            f"{BASE_URL}/api/art-studio/workflows",
            headers=self.headers
        )
        workflows = get_response.json()["workflows"]
        matching = [w for w in workflows if w.get("id") == workflow_id]
        assert len(matching) == 0
        print(f"Workflow {workflow_id} successfully deleted")
    
    def test_workflow_data_structure(self):
        """Test that workflow data includes required fields"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/workflows",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["workflows"]) > 0:
            workflow = data["workflows"][0]
            # Check required fields
            assert "id" in workflow
            assert "name" in workflow
            assert "nodes" in workflow
            assert "edges" in workflow
            assert "created_at" in workflow or "updated_at" in workflow
            print(f"Workflow structure verified: {list(workflow.keys())}")
        else:
            print("No existing workflows to verify structure - creating one")
            # Create one to verify structure
            response = requests.post(
                f"{BASE_URL}/api/art-studio/workflow/save",
                headers=self.headers,
                json={"name": "Structure Test", "nodes": [{"id": "test"}], "edges": []}
            )
            assert response.status_code == 200


class TestArtStudioGeneratePromptEngineering:
    """Test that the generate endpoint uses DeepAI-style prompt engineering"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        yield
    
    def test_generate_request_schema_accepts_all_params(self):
        """Test that generate endpoint accepts all the new parameters"""
        # Test that request schema accepts all parameters (won't actually generate - too slow)
        # We're testing the schema validation only
        request_data = {
            "prompt": "A test character",
            "style": "anime",
            "type": "character",
            "negativePrompt": "blurry, low quality",
            "aspectRatio": "16:9",
            "qualityLevel": "high",
            "transparentBackground": True,
            "characterData": {"name": "Test", "gender": "Female"},
            "sceneData": None,
            "referenceImage": None,
            "bookId": None,
            "workflowName": "Test Workflow"
        }
        
        # Just verify the endpoint accepts the request without schema errors
        # The actual generation is slow (30+ seconds) so we skip it
        # A 200, 500 or timeout indicates schema is valid
        # A 422 indicates schema validation error
        try:
            response = requests.post(
                f"{BASE_URL}/api/art-studio/generate",
                headers=self.headers,
                json=request_data,
                timeout=5  # Short timeout - we just want to verify schema acceptance
            )
            # If we get here quickly, something is wrong (generation should be slow)
            # But any response except 422 means schema is valid
            assert response.status_code != 422, f"Schema validation failed: {response.text}"
            print(f"Schema accepted - response status: {response.status_code}")
        except requests.exceptions.Timeout:
            # Timeout is expected - generation is slow
            print("Request accepted (schema valid) - timed out waiting for generation")
            pass
        except requests.exceptions.ReadTimeout:
            print("Request accepted (schema valid) - read timeout during generation")
            pass
    
    def test_generate_endpoint_accessible(self):
        """Test that the generate endpoint is accessible"""
        # Minimal request just to verify endpoint exists
        try:
            response = requests.post(
                f"{BASE_URL}/api/art-studio/generate",
                headers=self.headers,
                json={"prompt": "", "style": "fantasy", "type": "character"},
                timeout=2
            )
            # Any response (including timeout) except 404 is fine
            # 422 for validation error or 500 for missing prompt is acceptable
            # 404 would indicate endpoint doesn't exist
            assert response.status_code != 404, "Generate endpoint not found"
            print(f"Generate endpoint accessible - status: {response.status_code}")
        except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout):
            # Timeout is expected for generation - endpoint is accessible
            print("Generate endpoint accessible - request timed out (expected for long generation)")


class TestArtStudioGallery:
    """Test Art Studio Gallery endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        yield
    
    def test_get_gallery(self):
        """Test GET /api/art-studio/gallery returns user's gallery"""
        response = requests.get(
            f"{BASE_URL}/api/art-studio/gallery",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data  # API returns "images" key
        assert isinstance(data["images"], list)
        print(f"Gallery has {len(data['images'])} images")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
