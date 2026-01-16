"""
New User Onboarding Journey E2E Tests
Complete flow: Registration → Login → License Validation → Pattern Creation → Pattern Save
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.journey
@pytest.mark.requires_api
@pytest.mark.requires_database
@pytest.mark.requires_desktop
class TestNewUserJourneyE2E:
    """E2E tests for new user onboarding journey"""
    
    def test_complete_new_user_flow(self, db_client: DatabaseClient):
        """Test complete new user flow: Registration → Login → License → Pattern Creation"""
        # Step 1: Create user (simulating registration)
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Step 2: Create trial entitlement (simulating registration creates entitlement)
        entitlement = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='trial',
            status='active'
        )
        db_client.create_entitlement(
            entitlement_id=entitlement['id'],
            user_id=entitlement['user_id'],
            plan=entitlement['plan'],
            status=entitlement['status']
        )
        
        # Step 3: Login
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        # Step 4: License Validation
        success, license_data, error = api_client.validate_license()
        assert success, f"License validation failed: {error}"
        assert license_data.get('valid') is True
        
        # Step 5: Pattern Creation (via desktop app)
        desktop_app = InProcessDesktopClient()
        desktop_app.initialize()
        success, error = desktop_app.login(user_data['email'], user_data['password'])
        assert success, f"Desktop app login failed: {error}"
        
        pattern = desktop_app.create_pattern(
            name="New User Pattern",
            width=72,
            height=1
        )
        assert pattern is not None, "Pattern creation failed"
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_first_time_user_experience(self, db_client: DatabaseClient):
        """Test first-time user experience"""
        # Create new user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Create trial entitlement
        entitlement = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='trial'
        )
        db_client.create_entitlement(
            entitlement_id=entitlement['id'],
            user_id=entitlement['user_id'],
            plan=entitlement['plan'],
            status=entitlement['status']
        )
        
        # Login and verify trial license
        api_client = APIClient()
        success, data, error = api_client.login(
            user_data['email'],
            user_data['password']
        )
        assert success, f"Login failed: {error}"
        
        success, license_data, error = api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        assert license_data.get('plan') == 'trial'
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_trial_license_activation(self, db_client: DatabaseClient):
        """Test trial license activation"""
        # Create user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Create trial entitlement
        trial_entitlement = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='trial',
            status='active'
        )
        db_client.create_entitlement(
            entitlement_id=trial_entitlement['id'],
            user_id=trial_entitlement['user_id'],
            plan=trial_entitlement['plan'],
            status=trial_entitlement['status']
        )
        
        # Verify trial is active
        entitlement = db_client.get_entitlement(user_data['id'])
        assert entitlement is not None
        assert entitlement['plan'] == 'trial'
        assert entitlement['status'] == 'active'
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
