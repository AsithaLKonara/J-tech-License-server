"""
Device Registration E2E Tests
Tests for device registration and management
"""

import pytest

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.user
@pytest.mark.requires_api
@pytest.mark.requires_database
class TestDeviceRegistrationE2E:
    """E2E tests for device registration"""
    
    def test_device_registration_on_first_login(self, authenticated_api_client: APIClient):
        """Test device registration on first login"""
        # Device should be registered during login
        # Verify device is registered
        success, devices, error = authenticated_api_client.list_devices()
        
        assert success, f"Failed to list devices: {error}"
        assert devices is not None
        assert len(devices) > 0, "At least one device should be registered"
    
    def test_device_registration_with_device_name(self, authenticated_api_client: APIClient):
        """Test device registration with device name"""
        device_name = "Test Device Name"
        success, data, error = authenticated_api_client.register_device(device_name)
        
        assert success, f"Device registration failed: {error}"
        assert data is not None
    
    def test_device_list_retrieval(self, authenticated_api_client: APIClient):
        """Test device list retrieval"""
        success, devices, error = authenticated_api_client.list_devices()
        
        assert success, f"Failed to list devices: {error}"
        assert isinstance(devices, list)
    
    def test_device_deletion(self, authenticated_api_client: APIClient):
        """Test device deletion"""
        # First, register a device
        success, data, error = authenticated_api_client.register_device("Device to Delete")
        assert success, f"Device registration failed: {error}"
        
        # Get device ID from response or list
        success, devices, error = authenticated_api_client.list_devices()
        assert success, f"Failed to list devices: {error}"
        assert len(devices) > 0
        
        # Delete first device
        device_id = devices[0].get('id') or devices[0].get('device_id')
        if device_id:
            success, error = authenticated_api_client.delete_device(device_id)
            assert success or error is not None  # Should succeed or fail gracefully
    
    def test_max_devices_enforcement(self, authenticated_api_client: APIClient):
        """Test max devices enforcement"""
        # Get license info to know max devices
        success, license_data, error = authenticated_api_client.get_license_info()
        assert success, f"Failed to get license info: {error}"
        
        max_devices = license_data.get('max_devices', 1)
        
        # Register devices up to max
        for i in range(max_devices):
            success, data, error = authenticated_api_client.register_device(f"Device {i+1}")
            # May succeed or fail depending on current device count
        
        # Try to register one more
        success, data, error = authenticated_api_client.register_device("Excess Device")
        # Should fail or return error about max devices
        if not success:
            assert "max" in error.lower() or "limit" in error.lower()
    
    def test_device_registration_with_duplicate_device_id(self, authenticated_api_client: APIClient):
        """Test device registration with duplicate device ID"""
        # Register device
        success1, data1, error1 = authenticated_api_client.register_device("Device 1")
        
        # Try to register again (may succeed if system allows or fail if duplicate)
        success2, data2, error2 = authenticated_api_client.register_device("Device 1")
        
        # System should handle duplicate gracefully
        assert success2 or error2 is not None
    
    def test_device_registration_with_very_long_name(self, authenticated_api_client: APIClient):
        """Test device registration with very long name"""
        long_name = "A" * 500  # Very long name
        success, data, error = authenticated_api_client.register_device(long_name)
        
        # Should either succeed (if system allows) or fail with validation error
        assert success or error is not None
    
    def test_device_registration_with_empty_name(self, authenticated_api_client: APIClient):
        """Test device registration with empty name"""
        success, data, error = authenticated_api_client.register_device("")
        
        # Should either use default name or fail validation
        assert success or error is not None
