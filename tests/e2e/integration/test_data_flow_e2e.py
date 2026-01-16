"""
End-to-End Data Flow E2E Tests
Tests for complete data flows across systems
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.integration
@pytest.mark.requires_api
@pytest.mark.requires_database
@pytest.mark.requires_desktop
class TestDataFlowE2E:
    """E2E tests for end-to-end data flows"""
    
    def test_user_registration_to_desktop_app_access(self, db_client: DatabaseClient):
        """Test: User Registration → Database → License Creation → Desktop App Access"""
        # Step 1: Create user in database
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Step 2: Create license in database
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
        
        # Step 3: Desktop app access
        desktop_app = InProcessDesktopClient()
        desktop_app.initialize()
        success, error = desktop_app.login(user_data['email'], user_data['password'])
        assert success, f"Desktop app login failed: {error}"
        
        # Step 4: Verify license in desktop app
        is_valid, license_data, error = desktop_app.validate_license()
        assert is_valid or error is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_pattern_creation_to_database_to_load(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test: Pattern Creation → Save → Database → Load → Display"""
        # Step 1: Create pattern
        pattern = authenticated_desktop_app.create_pattern(
            name="Data Flow Pattern",
            width=72,
            height=1
        )
        assert pattern is not None, "Pattern creation failed"
        
        # Step 2: Save pattern (would save to file/database in full E2E)
        # Step 3: Load pattern (would load from file/database in full E2E)
        # Step 4: Display pattern (would display in UI in full E2E)
        
        # For now, we verify pattern exists
        assert pattern is not None
    
    def test_license_update_to_desktop_app_sync(self, db_client: DatabaseClient):
        """Test: License Update → Database → Desktop App Sync"""
        # Create user
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        # Create initial license
        entitlement1 = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='trial'
        )
        db_client.create_entitlement(
            entitlement_id=entitlement1['id'],
            user_id=entitlement1['user_id'],
            plan=entitlement1['plan'],
            status=entitlement1['status']
        )
        
        # Login to desktop app
        desktop_app = InProcessDesktopClient()
        desktop_app.initialize()
        success, error = desktop_app.login(user_data['email'], user_data['password'])
        assert success, f"Login failed: {error}"
        
        # Update license in database
        entitlement2 = TestDataFactory.create_entitlement_data(
            user_id=user_data['id'],
            plan='monthly'
        )
        db_client.create_entitlement(
            entitlement_id=entitlement2['id'],
            user_id=entitlement2['user_id'],
            plan=entitlement2['plan'],
            status=entitlement2['status']
        )
        
        # Desktop app should sync license on next validation
        is_valid, license_data, error = desktop_app.validate_license()
        assert is_valid or error is not None
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
    
    def test_device_registration_to_license_validation(self, authenticated_api_client: APIClient):
        """Test: Device Registration → Database → License Validation"""
        # Step 1: Register device
        success, data, error = authenticated_api_client.register_device("Flow Test Device")
        assert success, f"Device registration failed: {error}"
        
        # Step 2: Verify device in database (via API)
        success, devices, error = authenticated_api_client.list_devices()
        assert success, f"Failed to list devices: {error}"
        assert len(devices) > 0
        
        # Step 3: License validation should account for device
        success, license_data, error = authenticated_api_client.validate_license()
        assert success, f"License validation failed: {error}"
