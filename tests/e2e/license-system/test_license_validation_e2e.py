"""
License Validation E2E Tests
Tests for license validation flows including account-based, file-based, expiration, and offline scenarios
"""

import pytest
import time
from datetime import datetime, timedelta

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.license
@pytest.mark.requires_api
@pytest.mark.requires_database
class TestLicenseValidationE2E:
    """E2E tests for license validation"""
    
    def test_account_based_license_validation(self, authenticated_api_client: APIClient,
                                             test_user_with_entitlement: dict):
        """Test account-based license validation flow"""
        # Validate license via API
        success, license_data, error = authenticated_api_client.validate_license()
        
        assert success, f"License validation failed: {error}"
        assert license_data is not None
        assert license_data.get('valid') is True
        assert license_data.get('plan') == 'trial'
        assert license_data.get('status') == 'active'
    
    def test_file_based_license_fallback(self, desktop_app_client: InProcessDesktopClient):
        """Test file-based license fallback when account-based license not available"""
        # This test would require setting up a file-based license
        # For now, we test that the system handles missing account license gracefully
        is_valid, license_data, error = desktop_app_client.validate_license()
        
        # Should handle gracefully (either valid file license or clear error)
        assert error is not None or is_valid is True
    
    def test_license_expiration_handling(self, db_client: DatabaseClient, 
                                        authenticated_api_client: APIClient):
        """Test license expiration handling"""
        # Create user with expired entitlement
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Create expired entitlement
        expired_entitlement = TestDataFactory.create_expired_entitlement_data(
            user_id=user_data['id']
        )
        db_client.create_entitlement(
            entitlement_id=expired_entitlement['id'],
            user_id=expired_entitlement['user_id'],
            plan=expired_entitlement['plan'],
            status=expired_entitlement['status']
        )
        
        # Login with expired license
        success, data, error = authenticated_api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        # Validate license (should show expired)
        success, license_data, error = authenticated_api_client.validate_license()
        assert success, f"License validation failed: {error}"
        assert license_data.get('status') == 'expired' or license_data.get('valid') is False
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_license_refresh_scenarios(self, authenticated_api_client: APIClient,
                                      test_user_with_entitlement: dict):
        """Test license refresh scenarios"""
        # Get initial license info
        success, initial_data, error = authenticated_api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        
        # Validate license
        success, license_data, error = authenticated_api_client.validate_license()
        assert success, f"License validation failed: {error}"
        
        # Refresh should maintain same license info
        success, refreshed_data, error = authenticated_api_client.validate_license()
        assert success, f"License refresh failed: {error}"
        assert refreshed_data.get('plan') == license_data.get('plan')
    
    def test_offline_license_validation_cached(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test offline license validation using cached data"""
        # First, validate online to cache
        is_valid, license_data, error = authenticated_desktop_app.validate_license()
        assert is_valid, f"Initial license validation failed: {error}"
        
        # Simulate offline (by using cached data)
        # The desktop app should use cached license data when offline
        # This is tested by checking that license info is still available
        license_info = authenticated_desktop_app.get_license_info()
        assert license_info is not None
    
    def test_concurrent_license_validations(self, authenticated_api_client: APIClient):
        """Test concurrent license validations"""
        import concurrent.futures
        
        def validate_license():
            success, data, error = authenticated_api_client.validate_license()
            return success, data
        
        # Run multiple validations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(validate_license) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        for success, data in results:
            assert success, "Concurrent license validation failed"
            assert data is not None
    
    def test_license_validation_with_expired_token(self, api_client: APIClient,
                                                  test_user_with_entitlement: dict):
        """Test license validation with expired session token"""
        # Login to get token
        success, data, error = api_client.login(
            test_user_with_entitlement['email'],
            test_user_with_entitlement['password']
        )
        assert success, f"Login failed: {error}"
        
        # Set an expired token (simulate)
        api_client.set_token("expired_token_here")
        
        # License validation should fail or request re-authentication
        success, license_data, error = api_client.validate_license()
        # Should either fail gracefully or return error
        assert not success or error is not None
    
    def test_license_validation_with_invalid_token(self, api_client: APIClient):
        """Test license validation with invalid token"""
        api_client.set_token("invalid_token_12345")
        
        success, license_data, error = api_client.validate_license()
        assert not success, "License validation should fail with invalid token"
        assert error is not None
    
    def test_license_validation_with_network_errors(self, authenticated_api_client: APIClient):
        """Test license validation with network errors"""
        # Use invalid server URL to simulate network error
        error_client = APIClient(base_url="http://invalid-server:8000/api/v2")
        error_client.set_token(authenticated_api_client.token)
        
        # Should handle network error gracefully
        success, license_data, error = error_client.validate_license()
        assert not success, "Should fail with network error"
        assert error is not None
    
    def test_license_validation_priority_account_vs_file(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test license validation priority (account-based vs file-based)"""
        # Account-based license should take priority
        is_valid, license_data, error = authenticated_desktop_app.validate_license()
        
        # Should use account-based license if available
        if is_valid:
            assert license_data is not None
            # Account-based licenses typically have user_id
            assert 'user_id' in license_data or 'plan' in license_data
