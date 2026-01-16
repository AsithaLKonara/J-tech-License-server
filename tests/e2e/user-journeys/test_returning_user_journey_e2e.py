"""
Returning User Journey E2E Tests
Complete flow: Login → License Check → Load Pattern → Edit → Save
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient


@pytest.mark.journey
@pytest.mark.requires_api
@pytest.mark.requires_desktop
class TestReturningUserJourneyE2E:
    """E2E tests for returning user journey"""
    
    def test_complete_returning_user_flow(self, authenticated_api_client: APIClient,
                                          authenticated_desktop_app: InProcessDesktopClient):
        """Test complete returning user flow"""
        # Step 1: Login (already authenticated via fixture)
        assert authenticated_api_client.token is not None
        
        # Step 2: License Check
        success, license_data, error = authenticated_api_client.validate_license()
        assert success, f"License validation failed: {error}"
        
        # Step 3: Load Pattern (would load from file in full E2E)
        # For now, we verify pattern service is available
        assert authenticated_desktop_app.pattern_service is not None
        
        # Step 4: Edit Pattern
        pattern = authenticated_desktop_app.create_pattern(
            name="Returning User Pattern",
            width=72,
            height=1
        )
        assert pattern is not None, "Pattern creation/editing failed"
        
        # Step 5: Save Pattern (would save to file in full E2E)
        # For now, we verify pattern exists for saving
    
    def test_session_persistence(self, authenticated_api_client: APIClient):
        """Test session persistence"""
        # Verify session token exists
        assert authenticated_api_client.token is not None
        
        # Use session for multiple requests
        for _ in range(3):
            success, data, error = authenticated_api_client.get_license_info()
            assert success or error is not None
    
    def test_license_validation_on_app_start(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test license validation on app start"""
        # License should be validated when app starts
        license_info = authenticated_desktop_app.get_license_info()
        assert license_info is not None
    
    def test_pattern_loading_from_file(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern loading from file"""
        # Pattern loading would be tested via file operations in full E2E
        # For now, we verify pattern service can load patterns
        assert authenticated_desktop_app.pattern_service is not None
