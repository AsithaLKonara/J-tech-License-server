"""
Tests for Budurasmala Device Manager.
"""

import pytest
from unittest.mock import Mock, patch
from core.services.device_manager import (
    DeviceManager,
    BudurasmalaDevice,
    DeviceStatus,
    DeviceCommand
)


class TestDeviceManager:
    """Test device manager functionality."""
    
    def test_device_creation(self):
        """Test device creation."""
        device = BudurasmalaDevice(
            device_id="test_device_1",
            name="Test Device",
            ip_address="192.168.1.100",
            port=80,
            device_type="ESP32"
        )
        
        assert device.device_id == "test_device_1"
        assert device.name == "Test Device"
        assert device.ip_address == "192.168.1.100"
        assert device.status == DeviceStatus.OFFLINE
    
    def test_device_manager_initialization(self):
        """Test device manager initialization."""
        manager = DeviceManager()
        
        assert manager._devices == {}
        assert len(manager._status_callbacks) == 0
        assert len(manager._preview_callbacks) == 0
    
    def test_add_remove_device(self):
        """Test adding and removing devices."""
        manager = DeviceManager()
        
        device = BudurasmalaDevice(
            device_id="test_1",
            name="Test",
            ip_address="192.168.1.100"
        )
        
        manager.add_device(device)
        assert len(manager.list_devices()) == 1
        assert manager.get_device("test_1") == device
        
        assert manager.remove_device("test_1") is True
        assert len(manager.list_devices()) == 0
        assert manager.get_device("test_1") is None
    
    def test_device_command_creation(self):
        """Test device command creation."""
        command = DeviceCommand(
            command="play",
            parameters={"pattern": "test_pattern"}
        )
        
        assert command.command == "play"
        assert command.parameters == {"pattern": "test_pattern"}
        assert command.timestamp is not None
    
    @patch('requests.post')
    def test_send_command(self, mock_post):
        """Test sending command to device."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}
        
        manager = DeviceManager()
        device = BudurasmalaDevice(
            device_id="test_1",
            name="Test",
            ip_address="192.168.1.100"
        )
        manager.add_device(device)
        
        command = DeviceCommand("play")
        result = manager.send_command("test_1", command)
        
        assert result is True
        mock_post.assert_called_once()
    
    def test_schedule_pattern(self):
        """Test pattern scheduling."""
        manager = DeviceManager()
        device = BudurasmalaDevice(
            device_id="test_1",
            name="Test",
            ip_address="192.168.1.100"
        )
        manager.add_device(device)
        
        from datetime import datetime, timedelta
        start_time = datetime.now() + timedelta(hours=1)
        
        schedule_id = manager.schedule_pattern(
            device_id="test_1",
            pattern_name="Test Pattern",
            pattern_data=b"pattern_data",
            start_time=start_time
        )
        
        assert schedule_id is not None
        assert schedule_id.startswith("test_1_")

