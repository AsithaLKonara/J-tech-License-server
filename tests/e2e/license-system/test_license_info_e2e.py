"""
License Information E2E Tests
Tests for license information retrieval and display
"""

import pytest
from datetime import datetime

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient
from tests.e2e.setup.test_fixtures import TestDataFactory, TestLicenseFactory


@pytest.mark.license
@pytest.mark.requires_api
@pytest.mark.requires_database
class TestLicenseInfoE2E:
    """E2E tests for license information"""
    
    def test_license_info_retrieval(self, authenticated_api_client: APIClient):
        """Test license info retrieval"""
        success, license_data, error = authenticated_api_client.get_license_info()
        
        assert success, f"Failed to get license info: {error}"
        assert license_data is not None
        assert 'plan' in license_data
        assert 'status' in license_data
    
    def test_license_expiration_date_display(self, authenticated_api_client: APIClient):
        """Test license expiration date display"""
        success, license_data, error = authenticated_api_client.get_license_info()
        
        assert success, f"Failed to get license info: {error}"
        
        # Check if expiration date is present (may be None for perpetual)
        if 'expires_at' in license_data:
            expires_at = license_data['expires_at']
            # If expiration exists, it should be a valid date string or None
            assert expires_at is None or isinstance(expires_at, str)
    
    def test_license_plan_type_display(self, authenticated_api_client: APIClient):
        """Test license plan type display"""
        success, license_data, error = authenticated_api_client.get_license_info()
        
        assert success, f"Failed to get license info: {error}"
        assert 'plan' in license_data
        
        plan = license_data['plan']
        assert plan in ['trial', 'monthly', 'yearly', 'perpetual']
    
    def test_license_status_display(self, authenticated_api_client: APIClient):
        """Test license status display"""
        success, license_data, error = authenticated_api_client.get_license_info()
        
        assert success, f"Failed to get license info: {error}"
        assert 'status' in license_data
        
        status = license_data['status']
        assert status in ['active', 'inactive', 'cancelled', 'expired']
    
    def test_device_count_display(self, authenticated_api_client: APIClient):
        """Test device count display"""
        success, license_data, error = authenticated_api_client.get_license_info()
        
        assert success, f"Failed to get license info: {error}"
        assert 'max_devices' in license_data
        
        max_devices = license_data['max_devices']
        assert isinstance(max_devices, int)
        assert max_devices > 0
    
    def test_license_renewal_prompts(self, db_client: DatabaseClient):
        """Test license renewal prompts for expiring licenses"""
        # Create user with expiring soon license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        expiring_license = TestDataFactory.create_expiring_soon_entitlement_data(
            user_id=user_data['id'],
            plan='monthly',
            days_until_expiry=3
        )
        db_client.create_entitlement(
            entitlement_id=expiring_license['id'],
            user_id=expiring_license['user_id'],
            plan=expiring_license['plan'],
            status=expiring_license['status']
        )
        
        # Login and get license info
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        
        # Check if expiration info is present
        if 'expires_at' in license_data:
            expires_at = license_data['expires_at']
            # Should indicate expiration is soon
            assert expires_at is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_license_info_via_desktop_app(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test license info retrieval via desktop app"""
        license_info = authenticated_desktop_app.get_license_info()
        
        assert license_info is not None
        assert 'plan' in license_info or 'status' in license_info
    
    def test_license_info_consistency_api_vs_desktop(self, authenticated_api_client: APIClient,
                                                     authenticated_desktop_app: InProcessDesktopClient):
        """Test license info consistency between API and desktop app"""
        # Get license info from API
        success, api_license_data, error = authenticated_api_client.get_license_info()
        assert success, f"Failed to get license info from API: {error}"
        
        # Get license info from desktop app
        desktop_license_info = authenticated_desktop_app.get_license_info()
        assert desktop_license_info is not None
        
        # Compare key fields
        if 'plan' in api_license_data and 'plan' in desktop_license_info:
            assert api_license_data['plan'] == desktop_license_info['plan']
        
        if 'status' in api_license_data and 'status' in desktop_license_info:
            assert api_license_data['status'] == desktop_license_info['status']
    
    def test_license_info_with_multiple_entitlements(self, db_client: DatabaseClient):
        """Test license info when user has multiple entitlements"""
        # Create user with multiple entitlements
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Create active entitlement
        active_license = TestLicenseFactory.create_monthly_license_data(user_data['id'])
        db_client.create_entitlement(
            entitlement_id=active_license['id'],
            user_id=active_license['user_id'],
            plan=active_license['plan'],
            status=active_license['status']
        )
        
        # Create inactive entitlement
        inactive_license = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='yearly',
            status='inactive'
        )
        db_client.create_entitlement(
            entitlement_id=inactive_license['id'],
            user_id=inactive_license['user_id'],
            plan=inactive_license['plan'],
            status=inactive_license['status']
        )
        
        # Login and get license info (should return active one)
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        assert license_data.get('status') == 'active'
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
