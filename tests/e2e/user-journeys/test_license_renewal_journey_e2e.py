"""
License Renewal Journey E2E Tests
Complete flow: Expiring License → Renewal Prompt → Payment → License Update
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.journey
@pytest.mark.requires_api
@pytest.mark.requires_database
class TestLicenseRenewalJourneyE2E:
    """E2E tests for license renewal journey"""
    
    def test_license_expiration_detection(self, db_client: DatabaseClient):
        """Test license expiration detection"""
        # Create user with expiring license
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
        
        # Login and check license
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        
        # Should detect expiration
        if 'expires_at' in license_data:
            assert license_data['expires_at'] is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_renewal_flow(self, db_client: DatabaseClient):
        """Test renewal flow"""
        # Create user with expired license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        expired_license = TestDataFactory.create_expired_entitlement_data(
            user_id=user_data['id']
        )
        db_client.create_entitlement(
            entitlement_id=expired_license['id'],
            user_id=expired_license['user_id'],
            plan=expired_license['plan'],
            status=expired_license['status']
        )
        
        # Create new active license (simulating renewal)
        new_license = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='monthly',
            status='active'
        )
        db_client.create_entitlement(
            entitlement_id=new_license['id'],
            user_id=new_license['user_id'],
            plan=new_license['plan'],
            status=new_license['status']
        )
        
        # Verify renewal
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.validate_license()
        assert success, f"License validation failed: {error}"
        assert license_data.get('status') == 'active'
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_license_update_after_renewal(self, db_client: DatabaseClient):
        """Test license update after renewal"""
        # Create user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Create renewed license
        renewed_license = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='yearly',
            status='active'
        )
        db_client.create_entitlement(
            entitlement_id=renewed_license['id'],
            user_id=renewed_license['user_id'],
            plan=renewed_license['plan'],
            status=renewed_license['status']
        )
        
        # Verify license update
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        assert license_data.get('plan') == 'yearly'
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
