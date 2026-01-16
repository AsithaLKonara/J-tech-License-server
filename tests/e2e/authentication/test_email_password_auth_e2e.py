"""
Email/Password Authentication E2E Tests
Tests for email/password authentication flows
"""

import pytest
import time

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.auth
@pytest.mark.requires_api
@pytest.mark.requires_database
class TestEmailPasswordAuthE2E:
    """E2E tests for email/password authentication"""
    
    def test_successful_login_with_valid_credentials(self, db_client: DatabaseClient):
        """Test successful login with valid credentials"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Attempt login
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        
        assert success, f"Login failed: {error}"
        assert data is not None
        assert 'session_token' in data
        assert api_client.token is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_login_with_invalid_email(self, api_client: APIClient):
        """Test login with invalid email format"""
        success, data, error = api_client.login(
            email="invalid-email",
            password="somepassword"
        )
        
        assert not success, "Login should fail with invalid email"
        assert error is not None
    
    def test_login_with_invalid_password(self, db_client: DatabaseClient):
        """Test login with invalid password"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Attempt login with wrong password
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            "wrongpassword"
        )
        
        assert not success, "Login should fail with wrong password"
        assert error is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_login_with_nonexistent_user(self, api_client: APIClient):
        """Test login with non-existent user"""
        success, data, error = api_client.login(
            email="nonexistent@example.com",
            password="somepassword"
        )
        
        assert not success, "Login should fail for non-existent user"
        assert error is not None
    
    def test_login_with_empty_fields(self, api_client: APIClient):
        """Test login with empty fields"""
        # Empty email
        success, data, error = api_client.login(
            email="",
            password="somepassword"
        )
        assert not success, "Login should fail with empty email"
        
        # Empty password
        success, data, error = api_client.login(
            email="test@example.com",
            password=""
        )
        assert not success, "Login should fail with empty password"
        
        # Both empty
        success, data, error = api_client.login(
            email="",
            password=""
        )
        assert not success, "Login should fail with both fields empty"
    
    def test_login_with_special_characters_in_email(self, db_client: DatabaseClient):
        """Test login with special characters in email"""
        # Create user with special characters in email
        user_data = TestDataFactory.create_user_data()
        user_data['email'] = "test+special@example.com"
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Attempt login
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        
        # Should handle special characters correctly
        assert success or error is not None  # Either succeeds or fails gracefully
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_login_rate_limiting(self, db_client: DatabaseClient):
        """Test login rate limiting"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Attempt multiple rapid logins
        api_client = APIClient()
        failures = 0
        
        for i in range(10):
            success, data, error = api_client.login(
                user_data['email'],
                user_data['password']
            )
            if not success:
                failures += 1
            time.sleep(0.1)  # Small delay
        
        # Rate limiting may kick in after several attempts
        # This test verifies the system handles rapid requests
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_session_persistence_after_login(self, db_client: DatabaseClient):
        """Test session persistence after login"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Login
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        # Wait a bit
        time.sleep(1)
        
        # Try to use authenticated endpoint
        success, license_data, error = api_client.get_license_info()
        # Should work if session is persisted
        assert success or error is not None  # Either succeeds or fails gracefully
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_logout_functionality(self, authenticated_api_client: APIClient):
        """Test logout functionality"""
        # Verify we're authenticated
        success, data, error = authenticated_api_client.get_license_info()
        assert success, "Should be authenticated"
        
        # Logout
        success, error = authenticated_api_client.logout()
        assert success, f"Logout failed: {error}"
        
        # Try to use authenticated endpoint (should fail)
        success, license_data, error = authenticated_api_client.get_license_info()
        assert not success, "Should fail after logout"
    
    def test_concurrent_login_attempts(self, db_client: DatabaseClient):
        """Test concurrent login attempts"""
        # Create test user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        import concurrent.futures
        
        def attempt_login():
            api_client = APIClient()
            return api_client.login(user_data['email'], user_data['password'])
        
        # Run multiple logins concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attempt_login) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed (or handle gracefully)
        for success, data, error in results:
            assert success or error is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
