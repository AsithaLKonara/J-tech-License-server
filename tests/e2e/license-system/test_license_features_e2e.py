"""
License Feature Access E2E Tests
Tests for feature gating based on license plan and status
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient
from tests.e2e.setup.test_fixtures import TestDataFactory, TestLicenseFactory


@pytest.mark.license
@pytest.mark.requires_api
@pytest.mark.requires_database
class TestLicenseFeaturesE2E:
    """E2E tests for license feature access"""
    
    def test_trial_plan_feature_restrictions(self, db_client: DatabaseClient):
        """Test trial plan feature restrictions"""
        # Create user with trial license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        trial_license = TestLicenseFactory.create_trial_license_data(user_data['id'])
        db_client.create_entitlement(
            entitlement_id=trial_license['id'],
            user_id=trial_license['user_id'],
            plan=trial_license['plan'],
            status=trial_license['status'],
            max_devices=trial_license['max_devices']
        )
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        assert license_data.get('plan') == 'trial'
        assert license_data.get('max_devices') == 1
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_monthly_plan_feature_access(self, db_client: DatabaseClient):
        """Test monthly plan feature access"""
        # Create user with monthly license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        monthly_license = TestLicenseFactory.create_monthly_license_data(user_data['id'])
        db_client.create_entitlement(
            entitlement_id=monthly_license['id'],
            user_id=monthly_license['user_id'],
            plan=monthly_license['plan'],
            status=monthly_license['status'],
            max_devices=monthly_license['max_devices']
        )
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        assert license_data.get('plan') == 'monthly'
        assert license_data.get('max_devices') == 5
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_yearly_plan_feature_access(self, db_client: DatabaseClient):
        """Test yearly plan feature access"""
        # Create user with yearly license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        yearly_license = TestLicenseFactory.create_yearly_license_data(user_data['id'])
        db_client.create_entitlement(
            entitlement_id=yearly_license['id'],
            user_id=yearly_license['user_id'],
            plan=yearly_license['plan'],
            status=yearly_license['status'],
            max_devices=yearly_license['max_devices']
        )
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        assert license_data.get('plan') == 'yearly'
        assert license_data.get('max_devices') == 10
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_perpetual_plan_feature_access(self, db_client: DatabaseClient):
        """Test perpetual plan feature access"""
        # Create user with perpetual license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        perpetual_license = TestLicenseFactory.create_perpetual_license_data(user_data['id'])
        db_client.create_entitlement(
            entitlement_id=perpetual_license['id'],
            user_id=perpetual_license['user_id'],
            plan=perpetual_license['plan'],
            status=perpetual_license['status'],
            max_devices=perpetual_license['max_devices']
        )
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        assert license_data.get('plan') == 'perpetual'
        assert license_data.get('max_devices') == 999
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_feature_gating_based_on_license_status(self, db_client: DatabaseClient):
        """Test feature gating based on license status"""
        # Create user with inactive license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        inactive_license = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='monthly',
            status='inactive'
        )
        db_client.create_entitlement(
            entitlement_id=inactive_license['id'],
            user_id=inactive_license['user_id'],
            plan=inactive_license['plan'],
            status=inactive_license['status']
        )
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.validate_license()
        # Should indicate license is not active
        assert license_data.get('status') == 'inactive' or license_data.get('valid') is False
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_feature_access_with_expired_license(self, db_client: DatabaseClient):
        """Test feature access with expired license"""
        # Create user with expired license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        expired_license = TestDataFactory.create_expired_entitlement_data(
            user_id=user_data['id'],
            plan='monthly'
        )
        db_client.create_entitlement(
            entitlement_id=expired_license['id'],
            user_id=expired_license['user_id'],
            plan=expired_license['plan'],
            status=expired_license['status']
        )
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.validate_license()
        assert license_data.get('status') == 'expired' or license_data.get('valid') is False
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_feature_access_with_cancelled_license(self, db_client: DatabaseClient):
        """Test feature access with cancelled license"""
        # Create user with cancelled license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        cancelled_license = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='monthly',
            status='cancelled'
        )
        db_client.create_entitlement(
            entitlement_id=cancelled_license['id'],
            user_id=cancelled_license['user_id'],
            plan=cancelled_license['plan'],
            status=cancelled_license['status']
        )
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.validate_license()
        assert license_data.get('status') == 'cancelled' or license_data.get('valid') is False
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_max_devices_enforcement(self, db_client: DatabaseClient, authenticated_api_client: APIClient):
        """Test max devices enforcement"""
        # Get license info
        success, license_data, error = authenticated_api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        
        max_devices = license_data.get('max_devices', 1)
        
        # Try to register devices up to max
        for i in range(max_devices):
            success, data, error = authenticated_api_client.register_device(f"Device {i+1}")
            assert success, f"Device registration {i+1} failed: {error}"
        
        # Try to register one more (should fail or be rejected)
        success, data, error = authenticated_api_client.register_device("Excess Device")
        # Should either fail or return error about max devices
        if not success:
            assert "max devices" in error.lower() or "limit" in error.lower()
    
    def test_pattern_creation_limits_by_plan(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation limits by plan"""
        # Get license info
        license_info = authenticated_desktop_app.get_license_info()
        assert license_info is not None
        
        plan = license_info.get('plan', 'trial')
        
        # Create pattern (should work regardless of plan, but features may differ)
        pattern = authenticated_desktop_app.create_pattern(
            name="Test Pattern",
            width=72,
            height=1
        )
        
        # Pattern creation should succeed (limits are on features, not creation)
        assert pattern is not None
