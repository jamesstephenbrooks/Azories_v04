"""
Admin Dashboard Testing - Iteration 30
Tests for:
1. Admin login with credentials: Username='Admin', Password='Routetofreedom'
2. Admin dashboard pending reviews endpoint
3. Book publish request flow (sets status to 'pending_review')
4. Admin run moderation endpoint
5. Admin approve/reject book endpoints
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://image-integrity-1.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD = "Routetofreedom"
VIP_USER_EMAIL = "jamesstephenbrooks@outlook.com"
VIP_USER_PASSWORD = "test123"


class TestAdminLogin:
    """Test dedicated admin login functionality"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "access_token not in response"
        assert "admin_name" in data, "admin_name not in response"
        assert data["admin_name"] == ADMIN_USERNAME
        assert len(data["access_token"]) > 0, "Empty access token"
        print(f"✓ Admin login successful, token received")
        
    def test_admin_login_wrong_username(self):
        """Test admin login with wrong username"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": "WrongAdmin", "password": ADMIN_PASSWORD}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Wrong username correctly rejected")
        
    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": "wrongpassword"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Wrong password correctly rejected")


class TestAdminVerify:
    """Test admin token verification"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin login failed")
    
    def test_admin_verify_valid_token(self, admin_token):
        """Test verifying a valid admin token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/verify",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Verify failed: {response.text}"
        data = response.json()
        assert data.get("valid") == True
        assert data.get("username") == ADMIN_USERNAME
        print(f"✓ Admin token verification successful")
        
    def test_admin_verify_invalid_token(self):
        """Test verifying an invalid admin token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/verify",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Invalid token correctly rejected")


class TestBookPublishFlow:
    """Test book publish request workflow"""
    
    @pytest.fixture
    def vip_user_token(self):
        """Get VIP user token for creating books"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": VIP_USER_EMAIL, "password": VIP_USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("VIP user login failed")
        
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def test_book(self, vip_user_token):
        """Create a test book for testing publish flow"""
        unique_title = f"TEST_AdminDashboard_Book_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/books",
            json={
                "title": unique_title,
                "description": "Test book for admin dashboard testing",
                "genre": "Adventure"
            },
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        if response.status_code == 200:
            book = response.json()
            yield book
            # Cleanup - delete the test book
            requests.delete(
                f"{BASE_URL}/api/books/{book['id']}",
                headers={"Authorization": f"Bearer {vip_user_token}"}
            )
        else:
            pytest.skip(f"Could not create test book: {response.text}")
    
    def test_request_publish_sets_pending_review(self, vip_user_token, test_book):
        """Test that requesting publish sets status to 'pending_review'"""
        book_id = test_book["id"]
        
        # Request publish
        response = requests.post(
            f"{BASE_URL}/api/books/{book_id}/request-publish",
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        assert response.status_code == 200, f"Request publish failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "pending_review", f"Expected pending_review, got {data.get('status')}"
        assert data.get("success") == True
        print(f"✓ Book status set to 'pending_review'")
        
        # Verify by fetching the book
        book_response = requests.get(f"{BASE_URL}/api/books/{book_id}")
        assert book_response.status_code == 200
        book_data = book_response.json()
        assert book_data.get("publish_status") == "pending_review", \
            f"Book publish_status not updated: {book_data.get('publish_status')}"
        print(f"✓ Book publish_status verified in database")


class TestAdminPendingReviews:
    """Test admin pending reviews endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin login failed")
    
    def test_get_pending_reviews(self, admin_token):
        """Test getting pending reviews list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/pending-reviews",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get pending reviews failed: {response.text}"
        data = response.json()
        
        assert "books" in data, "books not in response"
        assert "count" in data, "count not in response"
        assert isinstance(data["books"], list), "books should be a list"
        assert isinstance(data["count"], int), "count should be an integer"
        print(f"✓ Pending reviews endpoint working, found {data['count']} pending books")
    
    def test_pending_reviews_requires_admin_auth(self):
        """Test that pending reviews requires admin authentication"""
        # Try without auth
        response = requests.get(f"{BASE_URL}/api/admin/pending-reviews")
        assert response.status_code in [401, 422], f"Expected auth error, got {response.status_code}"
        
        # Try with regular user token
        user_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": VIP_USER_EMAIL, "password": VIP_USER_PASSWORD}
        )
        if user_response.status_code == 200:
            user_token = user_response.json()["access_token"]
            response = requests.get(
                f"{BASE_URL}/api/admin/pending-reviews",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            # Regular user token should not work for admin endpoints
            assert response.status_code in [401, 403], f"Expected auth/forbidden, got {response.status_code}"
            print(f"✓ Regular user correctly denied access to admin endpoint")


class TestAdminModeration:
    """Test admin moderation functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def vip_user_token(self):
        """Get VIP user token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": VIP_USER_EMAIL, "password": VIP_USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("VIP user login failed")
    
    @pytest.fixture
    def test_book_for_moderation(self, vip_user_token):
        """Create a test book for moderation testing"""
        unique_title = f"TEST_Moderation_Book_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/books",
            json={
                "title": unique_title,
                "description": "A clean test book for moderation testing",
                "genre": "Adventure"
            },
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        if response.status_code == 200:
            book = response.json()
            yield book
            # Cleanup
            requests.delete(
                f"{BASE_URL}/api/books/{book['id']}",
                headers={"Authorization": f"Bearer {vip_user_token}"}
            )
        else:
            pytest.skip(f"Could not create test book: {response.text}")
    
    def test_run_moderation(self, admin_token, test_book_for_moderation):
        """Test admin can run moderation on a book"""
        book_id = test_book_for_moderation["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/books/{book_id}/run-moderation",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Run moderation failed: {response.text}"
        data = response.json()
        
        assert "success" in data, "success not in response"
        assert "flagged" in data, "flagged not in response"
        assert "categories" in data, "categories not in response"
        assert "message" in data, "message not in response"
        assert data["success"] == True
        print(f"✓ Moderation run successful, flagged={data['flagged']}, categories={data['categories']}")


class TestAdminApproveReject:
    """Test admin approve and reject functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def vip_user_token(self):
        """Get VIP user token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": VIP_USER_EMAIL, "password": VIP_USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("VIP user login failed")
    
    @pytest.fixture
    def test_book_for_approval(self, vip_user_token):
        """Create a test book for approval testing"""
        unique_title = f"TEST_Approval_Book_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/books",
            json={
                "title": unique_title,
                "description": "Test book for approval testing",
                "genre": "Adventure"
            },
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        if response.status_code == 200:
            book = response.json()
            yield book
            # Cleanup
            requests.delete(
                f"{BASE_URL}/api/books/{book['id']}",
                headers={"Authorization": f"Bearer {vip_user_token}"}
            )
        else:
            pytest.skip(f"Could not create test book: {response.text}")
    
    def test_admin_approve_book(self, admin_token, vip_user_token, test_book_for_approval):
        """Test admin can approve a book"""
        book_id = test_book_for_approval["id"]
        
        # First request publish
        requests.post(
            f"{BASE_URL}/api/books/{book_id}/request-publish",
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        # Admin approves
        response = requests.post(
            f"{BASE_URL}/api/admin/books/{book_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Approve failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Book approved successfully")
        
        # Verify book is now published
        book_response = requests.get(f"{BASE_URL}/api/books/{book_id}")
        assert book_response.status_code == 200
        book_data = book_response.json()
        assert book_data.get("publish_status") == "published", \
            f"Expected published, got {book_data.get('publish_status')}"
        assert book_data.get("is_published") == True, "is_published should be True"
        print(f"✓ Book publish_status verified as 'published'")
    
    @pytest.fixture
    def test_book_for_rejection(self, vip_user_token):
        """Create a test book for rejection testing"""
        unique_title = f"TEST_Rejection_Book_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/books",
            json={
                "title": unique_title,
                "description": "Test book for rejection testing",
                "genre": "Adventure"
            },
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        if response.status_code == 200:
            book = response.json()
            yield book
            # Cleanup
            requests.delete(
                f"{BASE_URL}/api/books/{book['id']}",
                headers={"Authorization": f"Bearer {vip_user_token}"}
            )
        else:
            pytest.skip(f"Could not create test book: {response.text}")
    
    def test_admin_reject_book(self, admin_token, vip_user_token, test_book_for_rejection):
        """Test admin can reject a book"""
        book_id = test_book_for_rejection["id"]
        
        # First request publish
        requests.post(
            f"{BASE_URL}/api/books/{book_id}/request-publish",
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        # Admin rejects
        reason = "Content does not meet community guidelines"
        response = requests.post(
            f"{BASE_URL}/api/admin/books/{book_id}/reject?reason={reason}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Reject failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Book rejected successfully")
        
        # Verify book status
        book_response = requests.get(f"{BASE_URL}/api/books/{book_id}")
        assert book_response.status_code == 200
        book_data = book_response.json()
        assert book_data.get("publish_status") == "rejected", \
            f"Expected rejected, got {book_data.get('publish_status')}"
        assert book_data.get("is_published") == False, "is_published should be False"
        print(f"✓ Book publish_status verified as 'rejected'")


class TestPublishStatusBadges:
    """Test that publish status correctly shows different states"""
    
    @pytest.fixture
    def vip_user_token(self):
        """Get VIP user token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": VIP_USER_EMAIL, "password": VIP_USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("VIP user login failed")
    
    def test_new_book_has_draft_status(self, vip_user_token):
        """Test that new books start with 'draft' status"""
        unique_title = f"TEST_Draft_Book_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/books",
            json={"title": unique_title, "description": "Test draft book"},
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )
        
        assert response.status_code == 200, f"Create book failed: {response.text}"
        book = response.json()
        
        assert book.get("publish_status") == "draft", \
            f"Expected draft status, got {book.get('publish_status')}"
        assert book.get("is_published") == False
        print(f"✓ New book correctly has 'draft' status")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/books/{book['id']}",
            headers={"Authorization": f"Bearer {vip_user_token}"}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
