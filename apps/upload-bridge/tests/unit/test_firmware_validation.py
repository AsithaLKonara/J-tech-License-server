"""
Unit tests for firmware validation functionality.

Tests the validate_firmware() method in UploaderBase to ensure
firmware files are properly validated before uploading.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from uploaders.base import UploaderBase, UploadError


class TestUploaderBase(UploaderBase):
    """Concrete implementation for testing base class methods"""
    
    def build_firmware(self, pattern, build_opts: dict):
        return Mock()
    
    def upload(self, firmware_path: str, port_params: dict):
        return Mock()
    
    def get_supported_chips(self):
        return ["test_chip"]
    
    def get_requirements(self):
        return []


class TestFirmwareValidation(unittest.TestCase):
    """Test firmware validation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.uploader = TestUploaderBase("test_chip")
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_nonexistent_file(self):
        """Test validation fails for non-existent file"""
        firmware_path = Path(self.temp_dir) / "nonexistent.bin"
        is_valid, error_message = self.uploader.validate_firmware(str(firmware_path))
        
        self.assertFalse(is_valid)
        self.assertIn("not found", error_message)
    
    def test_validate_empty_file(self):
        """Test validation fails for empty file"""
        firmware_path = Path(self.temp_dir) / "empty.bin"
        firmware_path.write_bytes(b"")
        
        is_valid, error_message = self.uploader.validate_firmware(str(firmware_path))
        
        self.assertFalse(is_valid)
        self.assertIn("empty", error_message.lower())
    
    def test_validate_file_too_small(self):
        """Test validation fails for suspiciously small file"""
        firmware_path = Path(self.temp_dir) / "tiny.bin"
        firmware_path.write_bytes(b"x" * 500)  # Less than 1KB
        
        is_valid, error_message = self.uploader.validate_firmware(str(firmware_path))
        
        self.assertFalse(is_valid)
        self.assertIn("small", error_message.lower())
    
    def test_validate_file_too_large(self):
        """Test validation fails for suspiciously large file"""
        firmware_path = Path(self.temp_dir) / "huge.bin"
        # Create file larger than 16MB (write in chunks to avoid memory issues)
        with open(firmware_path, 'wb') as f:
            for _ in range(17):  # 17 * 1024 * 1024 = 17MB
                f.write(b"x" * (1024 * 1024))
        
        is_valid, error_message = self.uploader.validate_firmware(str(firmware_path))
        
        self.assertFalse(is_valid)
        self.assertIn("large", error_message.lower())
    
    def test_validate_valid_firmware(self):
        """Test validation passes for valid firmware file"""
        firmware_path = Path(self.temp_dir) / "firmware.bin"
        firmware_path.write_bytes(b"x" * 50000)  # 50KB - reasonable size
        
        is_valid, error_message = self.uploader.validate_firmware(str(firmware_path))
        
        self.assertTrue(is_valid)
        self.assertEqual(error_message, "")
    
    def test_validate_valid_hex_file(self):
        """Test validation passes for HEX format file"""
        firmware_path = Path(self.temp_dir) / "firmware.hex"
        firmware_path.write_bytes(b":10000000" + b"x" * 10000)  # Valid HEX format
        
        is_valid, error_message = self.uploader.validate_firmware(str(firmware_path))
        
        self.assertTrue(is_valid)
    
    def test_validate_file_with_valid_extension(self):
        """Test validation passes for files with valid extensions"""
        for ext in ['.bin', '.hex', '.elf']:
            firmware_path = Path(self.temp_dir) / f"firmware{ext}"
            firmware_path.write_bytes(b"x" * 10000)
            
            is_valid, error_message = self.uploader.validate_firmware(str(firmware_path))
            self.assertTrue(is_valid, f"Failed for extension {ext}")
    
    def test_validate_directory_instead_of_file(self):
        """Test validation fails for directory"""
        dir_path = Path(self.temp_dir) / "not_a_file"
        dir_path.mkdir()
        
        is_valid, error_message = self.uploader.validate_firmware(str(dir_path))
        
        self.assertFalse(is_valid)
        self.assertIn("not a file", error_message.lower())
    
    def test_validation_in_upload_method(self):
        """Test that upload method calls validation"""
        firmware_path = Path(self.temp_dir) / "invalid.bin"
        firmware_path.write_bytes(b"")  # Empty file should fail validation
        
        with self.assertRaises(UploadError) as context:
            self.uploader.upload(str(firmware_path), {"port": "COM1"})
        
        self.assertIn("validation failed", str(context.exception).lower())
    
    def test_validation_passes_in_upload_method(self):
        """Test that upload proceeds when validation passes"""
        firmware_path = Path(self.temp_dir) / "valid.bin"
        firmware_path.write_bytes(b"x" * 50000)  # Valid firmware
        
        # Mock the actual upload logic to avoid real upload attempt
        with patch.object(self.uploader, '_report_progress'):
            # Since upload is abstract in base, we test that validation
            # doesn't raise an error
            is_valid, _ = self.uploader.validate_firmware(str(firmware_path))
            self.assertTrue(is_valid)


if __name__ == '__main__':
    unittest.main()

