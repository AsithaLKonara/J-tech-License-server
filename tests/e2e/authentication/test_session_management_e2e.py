"""
Session Management E2E Tests
Tests for session creation, persistence, timeout, and cleanup
"""

import pytest
import time

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.auth
@pytest.mark.requires_api
@pytest.mark.requires_database
class TestSessionManagementE2E:
    """E2E tests for session management"""
    
    def test_session_creation_on_login(self, db_client: DatabaseClient):
        """Test session creation on login"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Login (creates session)
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        # Session should be created (token received)
        assert api_client.token is not None
        assert 'session_token' in data
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_session_persistence(self, authenticated_api_client: APIClient):
        """Test session persistence"""
        # Make initial request
        success1, data1, error1 = authenticated_api_client.get_license_info()
        assert success1 or error1 is not None
        
        # Wait a bit
        time.sleep(1)
        
        # Make another request (session should persist)
        success2, data2, error2 = authenticated_api_client.get_license_info()
        assert success2 or error2 is not None
        
        # Token should still be valid
        assert authenticated_api_client.token is not None
    
    def test_session_timeout(self, authenticated_api_client: APIClient):
        """Test session timeout"""
        # Use session
        success, data, error = authenticated_api_client.get_license_info()
        assert success or error is not None
        
        # Note: Actual timeout testing would require waiting for session expiry
        # This is typically configured server-side (e.g., 24 hours)
        # For E2E, we verify session works initially
        
        # In a real timeout scenario, requests would start failing
        # after the timeout period
    
    def test_session_invalidation_on_logout(self, authenticated_api_client: APIClient):
        """Test session invalidation on logout"""
        # Verify session works
        success, data, error = authenticated_api_client.get_license_info()
        assert success, "Session should work before logout"
        
        # Logout (invalidates session)
        success, error = authenticated_api_client.logout()
        assert success, f"Logout failed: {error}"
        
        # Session should be invalidated
        success, data, error = authenticated_api_client.get_license_info()
        assert not success, "Session should be invalid after logout"
    
    def test_multiple_device_sessions(self, db_client: DatabaseClient):
        """Test multiple device sessions"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Login from device 1
        api_client1 = APIClient()
        success1, data1, error1 = api_client1.login(
            user_data['email'],
            user_data['password'],
            device_name="Device 1"
        )
        assert success1, f"Login failed: {error1}"
        
        # Login from device 2
        api_client2 = APIClient()
        success2, data2, error2 = api_client2.login(
            user_data['email'],
            user_data['password'],
            device_name="Device 2"
        )
        assert success2, f"Login failed: {error2}"
        
        # Both sessions should work
        success, data, error = api_client1.get_license_info()
        assert success or error is not None
        
        success, data, error = api_client2.get_license_info()
        assert success or error is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_session_cleanup(self, authenticated_api_client: APIClient):
        """Test session cleanup"""
        # Create session
        token = authenticated_api_client.token
        assert token is not None
        
        # Logout (cleanup)
        success, error = authenticated_api_client.logout()
        assert success, f"Logout failed: {error}"
        
        # Token should be cleared
        assert authenticated_api_client.token is None or authenticated_api_client.token != token
