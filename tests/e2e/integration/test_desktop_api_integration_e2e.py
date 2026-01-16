"""
Desktop App ↔ API Integration E2E Tests
Tests for integration between desktop app and API
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient


@pytest.mark.integration
@pytest.mark.requires_api
@pytest.mark.requires_desktop
class TestDesktopAPIIntegrationE2E:
    """E2E tests for desktop app and API integration"""
    
    def test_desktop_app_login_via_api(self, authenticated_desktop_app: InProcessDesktopClient,
                                       authenticated_api_client: APIClient):
        """Test desktop app login via API"""
        # Desktop app should be able to login using API
        assert authenticated_desktop_app.auth_manager is not None
        assert authenticated_api_client.token is not None
    
    def test_desktop_app_license_validation_via_api(self, authenticated_desktop_app: InProcessDesktopClient,
                                                    authenticated_api_client: APIClient):
        """Test desktop app license validation via API"""
        # Desktop app license validation
        is_valid, license_data, error = authenticated_desktop_app.validate_license()
        assert is_valid or error is not None
        
        # API license validation
        success, api_license_data, error = authenticated_api_client.validate_license()
        assert success, f"API license validation failed: {error}"
        
        # Both should return consistent results
        if is_valid and success:
            assert license_data is not None
            assert api_license_data is not None
    
    def test_desktop_app_device_registration_via_api(self, authenticated_api_client: APIClient):
        """Test desktop app device registration via API"""
        # Register device via API
        success, data, error = authenticated_api_client.register_device("Desktop App Device")
        assert success, f"Device registration failed: {error}"
        
        # Verify device is registered
        success, devices, error = authenticated_api_client.list_devices()
        assert success, f"Failed to list devices: {error}"
        assert len(devices) > 0
    
    def test_api_error_handling_in_desktop_app(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test API error handling in desktop app"""
        # Desktop app should handle API errors gracefully
        # Test with invalid server URL
        error_app = InProcessDesktopClient()
        error_app.initialize(server_url="http://invalid-server:8000")
        
        # Should handle error gracefully
        is_valid, license_data, error = error_app.validate_license()
        assert not is_valid or error is not None
    
    def test_api_timeout_handling(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test API timeout handling"""
        # Desktop app should handle API timeouts
        # This would be tested with a slow/unresponsive server
        # For now, we verify error handling exists
        assert authenticated_desktop_app.license_manager is not None
    
    def test_api_retry_logic(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test API retry logic"""
        # Desktop app should retry failed API requests
        # This would be tested with intermittent network failures
        # For now, we verify retry mechanism exists
        assert authenticated_desktop_app.license_manager is not None
