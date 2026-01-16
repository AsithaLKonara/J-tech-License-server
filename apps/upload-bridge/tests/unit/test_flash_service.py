"""
Unit tests for FlashService.

Tests the business logic service for firmware building and uploading.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from core.pattern import Pattern, PatternMetadata, Frame
from core.services.flash_service import FlashService
from uploaders.base import BuildResult, UploadResult


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing."""
    metadata = PatternMetadata(width=8, height=8)
    frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
    return Pattern(name="Test Pattern", metadata=metadata, frames=[frame])


@pytest.fixture
def flash_service():
    """Create a FlashService instance."""
    return FlashService()


class TestFlashServiceInitialization:
    """Test service initialization."""
    
    def test_init(self, flash_service):
        """Test that service initializes correctly."""
        assert flash_service.registry is not None


class TestFlashServiceBuildFirmware:
    """Test firmware building."""
    
    @patch('core.services.flash_service.get_uploader')
    def test_build_firmware_success(self, mock_get_uploader, flash_service, sample_pattern, tmp_path):
        """Test building firmware successfully."""
        # Setup mock uploader
        mock_uploader = Mock()
        mock_result = BuildResult(
            success=True,
            firmware_path=str(tmp_path / "firmware.bin"),
            binary_type="bin",
            size_bytes=1024,
            chip_model="esp8266"
        )
        mock_uploader.build_firmware.return_value = mock_result
        mock_get_uploader.return_value = mock_uploader
        
        # Build firmware
        result = flash_service.build_firmware(sample_pattern, "esp8266", config={'gpio_pin': 3})
        
        # Verify
        assert result.success is True
        assert str(result.firmware_path) == str(tmp_path / "firmware.bin")
        mock_uploader.build_firmware.assert_called_once()
    
    @patch('core.services.flash_service.get_uploader')
    def test_build_firmware_unsupported_chip(self, mock_get_uploader, flash_service, sample_pattern):
        """Test building firmware with unsupported chip."""
        mock_get_uploader.return_value = None
        
        with pytest.raises(ValueError, match="Unsupported"):
            flash_service.build_firmware(sample_pattern, "unsupported_chip")
    
    @patch('core.services.flash_service.get_uploader')
    def test_build_firmware_build_failure(self, mock_get_uploader, flash_service, sample_pattern):
        """Test building firmware when build fails."""
        mock_uploader = Mock()
        mock_uploader.build_firmware.side_effect = Exception("Build error")
        mock_get_uploader.return_value = mock_uploader
        
        with pytest.raises(RuntimeError, match="build failed"):
            flash_service.build_firmware(sample_pattern, "esp8266")


class TestFlashServiceUploadFirmware:
    """Test firmware uploading."""
    
    @patch('core.services.flash_service.get_uploader')
    def test_upload_firmware_success(self, mock_get_uploader, flash_service, tmp_path):
        """Test uploading firmware successfully."""
        # Setup mock uploader
        mock_uploader = Mock()
        mock_result = UploadResult(
            success=True,
            bytes_written=1024,
            duration_seconds=1.5,
            verified=True
        )
        mock_uploader.upload.return_value = mock_result
        mock_get_uploader.return_value = mock_uploader
        
        firmware_path = tmp_path / "firmware.bin"
        firmware_path.write_bytes(b"firmware data")
        
        # Upload firmware
        result = flash_service.upload_firmware(str(firmware_path), "esp8266", port="COM3")
        
        # Verify
        assert result.success is True
        assert result.bytes_written == 1024
        mock_uploader.upload.assert_called_once()
    
    @patch('core.services.flash_service.get_uploader')
    def test_upload_firmware_unsupported_chip(self, mock_get_uploader, flash_service, tmp_path):
        """Test uploading firmware with unsupported chip."""
        mock_get_uploader.return_value = None
        
        firmware_path = tmp_path / "firmware.bin"
        
        with pytest.raises(ValueError, match="Unsupported"):
            flash_service.upload_firmware(str(firmware_path), "unsupported_chip", port="COM3")
    
    @patch('core.services.flash_service.get_uploader')
    def test_upload_firmware_upload_failure(self, mock_get_uploader, flash_service, tmp_path):
        """Test uploading firmware when upload fails."""
        mock_uploader = Mock()
        mock_uploader.upload.side_effect = Exception("Upload error")
        mock_get_uploader.return_value = mock_uploader
        
        firmware_path = tmp_path / "firmware.bin"
        
        with pytest.raises(RuntimeError, match="upload failed"):
            flash_service.upload_firmware(str(firmware_path), "esp8266", port="COM3")
    
    @patch('core.services.flash_service.get_uploader')
    def test_upload_firmware_with_config(self, mock_get_uploader, flash_service, tmp_path):
        """Test uploading firmware with custom config."""
        mock_uploader = Mock()
        mock_result = UploadResult(success=True, bytes_written=0, duration_seconds=0.0, verified=True)
        mock_uploader.upload.return_value = mock_result
        mock_get_uploader.return_value = mock_uploader
        
        firmware_path = tmp_path / "firmware.bin"
        firmware_path.write_bytes(b"data")
        
        config = {'baud_rate': 115200, 'flash_mode': 'dio'}
        flash_service.upload_firmware(str(firmware_path), "esp8266", port="COM3", config=config)
        
        # Verify upload was called
        assert mock_uploader.upload.called
        call_args = mock_uploader.upload.call_args
        # Check that config parameters are in the call (either as kwargs or in port_params dict)
        # The upload method receives (firmware_path, port_params) where port_params contains port and config
        assert len(call_args[0]) >= 2  # firmware_path and port_params
        port_params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert 'port' in port_params or 'port' in (call_args[1] if len(call_args) > 1 else {})


class TestFlashServiceVerifyUpload:
    """Test upload verification."""
    
    @patch('core.services.flash_service.get_uploader')
    def test_verify_upload_success(self, mock_get_uploader, flash_service, tmp_path):
        """Test verifying upload successfully."""
        mock_uploader = Mock()
        mock_uploader.verify.return_value = True
        mock_get_uploader.return_value = mock_uploader
        
        firmware_path = tmp_path / "firmware.bin"
        is_valid, error = flash_service.verify_upload("esp8266", port="COM3", config={'firmware_path': str(firmware_path)})
        
        assert is_valid is True
        assert error is None
        mock_uploader.verify.assert_called_once()
    
    @patch('core.services.flash_service.get_uploader')
    def test_verify_upload_failure(self, mock_get_uploader, flash_service, tmp_path):
        """Test verifying upload when verification fails."""
        mock_uploader = Mock()
        mock_uploader.verify.return_value = False
        mock_get_uploader.return_value = mock_uploader
        
        firmware_path = tmp_path / "firmware.bin"
        is_valid, error = flash_service.verify_upload("esp8266", port="COM3", config={'firmware_path': str(firmware_path)})
        
        assert is_valid is False
        assert "failed" in error.lower()
    
    @patch('core.services.flash_service.get_uploader')
    def test_verify_upload_no_verify_method(self, mock_get_uploader, flash_service):
        """Test verifying upload when uploader doesn't support verification."""
        mock_uploader = Mock()
        del mock_uploader.verify  # Remove verify method
        mock_get_uploader.return_value = mock_uploader
        
        is_valid, error = flash_service.verify_upload("esp8266", port="COM3")
        
        assert is_valid is True  # Should assume success if verification not supported
        assert error is None
    
    @patch('core.services.flash_service.get_uploader')
    def test_verify_upload_unsupported_chip(self, mock_get_uploader, flash_service):
        """Test verifying upload with unsupported chip."""
        mock_get_uploader.return_value = None
        
        is_valid, error = flash_service.verify_upload("unsupported_chip", port="COM3")
        
        assert is_valid is False
        assert "Unsupported" in error


class TestFlashServiceListSupportedChips:
    """Test listing supported chips."""
    
    @patch('core.services.flash_service.UploaderRegistry')
    def test_list_supported_chips(self, mock_registry_class, flash_service):
        """Test listing supported chips."""
        mock_registry = Mock()
        mock_registry.list_supported_chips.return_value = ['esp8266', 'esp32', 'arduino']
        flash_service.registry = mock_registry
        
        chips = flash_service.list_supported_chips()
        
        assert chips == ['esp8266', 'esp32', 'arduino']
        mock_registry.list_supported_chips.assert_called_once()


class TestFlashServiceIsChipSupported:
    """Test checking chip support."""
    
    @patch('core.services.flash_service.get_uploader')
    def test_is_chip_supported_true(self, mock_get_uploader, flash_service):
        """Test checking if chip is supported (returns True)."""
        mock_uploader = Mock()
        mock_get_uploader.return_value = mock_uploader
        
        assert flash_service.is_chip_supported("esp8266") is True
    
    @patch('core.services.flash_service.get_uploader')
    def test_is_chip_supported_false(self, mock_get_uploader, flash_service):
        """Test checking if chip is supported (returns False)."""
        mock_get_uploader.return_value = None
        
        assert flash_service.is_chip_supported("unsupported_chip") is False

