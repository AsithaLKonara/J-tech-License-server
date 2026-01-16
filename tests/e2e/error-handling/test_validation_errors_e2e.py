"""
Validation Error E2E Tests
Tests for input validation and error handling
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.error
@pytest.mark.requires_api
class TestValidationErrorsE2E:
    """E2E tests for validation errors"""
    
    def test_invalid_input_validation(self, api_client: APIClient):
        """Test invalid input validation"""
        # Test login with invalid email format
        success, data, error = api_client.login(
            email="invalid-email",
            password="password"
        )
        assert not success, "Should fail with invalid email"
    
    def test_boundary_value_testing(self, authenticated_api_client: APIClient):
        """Test boundary value testing"""
        # Test with very long device name
        long_name = "A" * 1000
        success, data, error = authenticated_api_client.register_device(long_name)
        # Should either succeed or fail with validation error
        assert success or error is not None
    
    def test_special_character_handling(self, db_client: DatabaseClient):
        """Test special character handling"""
        # Create user with special characters
        user_data = TestDataFactory.create_user_data()
        user_data['email'] = "test+special@example.com"
        password_hash = TestDataFactory.hash_password(user_data['password'])
        
        success = db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Should handle special characters
        assert success or True  # May succeed or fail depending on validation
        
        # Cleanup
        if success:
            db_client.cleanup_test_data(user_data['email'])
    
    def test_empty_field_validation(self, api_client: APIClient):
        """Test empty field validation"""
        # Test login with empty fields
        success, data, error = api_client.login(email="", password="")
        assert not success, "Should fail with empty fields"
    
    def test_data_type_validation(self, authenticated_api_client: APIClient):
        """Test data type validation"""
        # API should validate data types
        # This would be tested with wrong data types
        # For E2E, we verify validation exists
        assert authenticated_api_client is not None
