"""
Test collaboration API endpoints for Azories
- POST /api/books/{id}/collaborators/invite
- POST /api/books/{id}/invite-link
- GET /api/books/{id}/collaborators
- PUT /api/books/{id}/collaborators/{user_id}
- DELETE /api/books/{id}/collaborators/{user_id}
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def test_users():
    """Create test users for collaboration testing"""
    users = {}
    
    # Create owner user
    owner_email = f"TEST_owner_{uuid.uuid4().hex[:8]}@test.com"
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": owner_email,
        "password": "password123",
        "name": "Test Owner"
    })
    assert res.status_code == 200, f"Failed to create owner: {res.text}"
    users['owner'] = {
        'email': owner_email,
        'token': res.json()['access_token'],
        'id': res.json()['user']['id']
    }
    
    # Create collaborator user
    collab_email = f"TEST_collab_{uuid.uuid4().hex[:8]}@test.com"
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": collab_email,
        "password": "password123",
        "name": "Test Collaborator"
    })
    assert res.status_code == 200, f"Failed to create collaborator: {res.text}"
    users['collaborator'] = {
        'email': collab_email,
        'token': res.json()['access_token'],
        'id': res.json()['user']['id']
    }
    
    return users

@pytest.fixture(scope="module")
def test_book(test_users):
    """Create a test book for collaboration"""
    headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
    res = requests.post(f"{BASE_URL}/api/books", json={
        "title": f"TEST_Collaboration_Book_{uuid.uuid4().hex[:8]}",
        "description": "Book for testing collaboration features"
    }, headers=headers)
    assert res.status_code == 200, f"Failed to create book: {res.text}"
    return res.json()

class TestCollaborationAPI:
    """Test collaboration endpoints"""
    
    def test_invite_collaborator_by_email(self, test_users, test_book):
        """Test POST /api/books/{id}/collaborators/invite"""
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        
        # Invite the collaborator user
        res = requests.post(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators/invite",
            json={
                "email": test_users['collaborator']['email'],
                "role": "editor"
            },
            headers=headers
        )
        
        assert res.status_code == 200, f"Invite failed: {res.text}"
        data = res.json()
        assert data.get('success') == True
        print(f"✓ Successfully invited collaborator: {data}")
    
    def test_invite_nonexistent_user(self, test_users, test_book):
        """Test inviting a user that doesn't exist"""
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        
        res = requests.post(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators/invite",
            json={
                "email": "nonexistent_user_12345@test.com",
                "role": "viewer"
            },
            headers=headers
        )
        
        assert res.status_code == 404, f"Expected 404, got: {res.status_code}"
        print(f"✓ Correctly returned 404 for nonexistent user")
    
    def test_invite_duplicate_collaborator(self, test_users, test_book):
        """Test inviting the same user twice"""
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        
        res = requests.post(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators/invite",
            json={
                "email": test_users['collaborator']['email'],
                "role": "editor"
            },
            headers=headers
        )
        
        assert res.status_code == 400, f"Expected 400, got: {res.status_code}"
        print(f"✓ Correctly returned 400 for duplicate invite")
    
    def test_get_collaborators(self, test_users, test_book):
        """Test GET /api/books/{id}/collaborators"""
        # Owner can see collaborators
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        res = requests.get(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators",
            headers=headers
        )
        
        assert res.status_code == 200, f"Failed to get collaborators: {res.text}"
        data = res.json()
        assert 'collaborators' in data
        assert len(data['collaborators']) >= 1
        
        # Check collaborator data
        collab = next((c for c in data['collaborators'] if c['email'] == test_users['collaborator']['email']), None)
        assert collab is not None, "Collaborator not found in list"
        assert collab['role'] == 'editor'
        print(f"✓ Found {len(data['collaborators'])} collaborator(s)")
    
    def test_update_collaborator_role(self, test_users, test_book):
        """Test PUT /api/books/{id}/collaborators/{user_id}"""
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        
        # Update role from editor to viewer
        res = requests.put(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators/{test_users['collaborator']['id']}",
            json={"role": "viewer"},
            headers=headers
        )
        
        assert res.status_code == 200, f"Failed to update role: {res.text}"
        print(f"✓ Updated collaborator role to viewer")
        
        # Verify the change
        res = requests.get(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators",
            headers=headers
        )
        data = res.json()
        collab = next((c for c in data['collaborators'] if c['user_id'] == test_users['collaborator']['id']), None)
        assert collab['role'] == 'viewer', f"Role not updated: {collab['role']}"
        print(f"✓ Verified role is now viewer")
    
    def test_generate_invite_link(self, test_users, test_book):
        """Test POST /api/books/{id}/invite-link"""
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        
        res = requests.post(
            f"{BASE_URL}/api/books/{test_book['id']}/invite-link",
            json={"role": "editor"},
            headers=headers
        )
        
        assert res.status_code == 200, f"Failed to generate invite link: {res.text}"
        data = res.json()
        assert 'invite_link' in data, "No invite_link in response"
        assert 'token' in data, "No token in response"
        assert data['invite_link'].startswith('http'), f"Invalid invite link: {data['invite_link']}"
        print(f"✓ Generated invite link: {data['invite_link'][:50]}...")
    
    def test_non_owner_cannot_invite(self, test_users, test_book):
        """Test that non-owners cannot invite collaborators"""
        # Use collaborator's token (they're not the owner)
        headers = {"Authorization": f"Bearer {test_users['collaborator']['token']}"}
        
        res = requests.post(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators/invite",
            json={
                "email": "someone@test.com",
                "role": "viewer"
            },
            headers=headers
        )
        
        assert res.status_code == 403, f"Expected 403, got: {res.status_code}"
        print(f"✓ Non-owner correctly blocked from inviting")
    
    def test_remove_collaborator(self, test_users, test_book):
        """Test DELETE /api/books/{id}/collaborators/{user_id}"""
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        
        res = requests.delete(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators/{test_users['collaborator']['id']}",
            headers=headers
        )
        
        assert res.status_code == 200, f"Failed to remove collaborator: {res.text}"
        print(f"✓ Removed collaborator")
        
        # Verify removal
        res = requests.get(
            f"{BASE_URL}/api/books/{test_book['id']}/collaborators",
            headers=headers
        )
        data = res.json()
        collab = next((c for c in data['collaborators'] if c['user_id'] == test_users['collaborator']['id']), None)
        assert collab is None, "Collaborator should be removed"
        print(f"✓ Verified collaborator removed")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup(self, test_users, test_book):
        """Delete test book and data"""
        headers = {"Authorization": f"Bearer {test_users['owner']['token']}"}
        
        # Delete the test book
        res = requests.delete(
            f"{BASE_URL}/api/books/{test_book['id']}",
            headers=headers
        )
        assert res.status_code == 200
        print(f"✓ Cleaned up test book: {test_book['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
