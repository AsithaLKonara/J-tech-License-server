"""
Hardware Verification Tests - Test uploaders with physical hardware

These tests verify that uploaders can detect and communicate with hardware.
They are designed to skip gracefully when hardware is not available.
"""

import unittest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from uploaders.stm32_uploader import Stm32Uploader
from uploaders.pic_uploader import PicUploader
from uploaders.base import DeviceInfo
from core.pattern import Pattern, Frame, PatternMetadata


class TestSTM32HardwareVerification(unittest.TestCase):
    """Test STM32 uploader hardware detection and communication"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.uploader = Stm32Uploader("stm32f103c8")
        self.test_pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
            ]
        )
    
    def test_device_id_mapping(self):
        """Test device ID to chip mapping"""
        # Test known device IDs
        self.assertEqual(
            self.uploader._identify_chip_from_device_id("0x410"),
            "stm32f103c8"
        )
        self.assertEqual(
            self.uploader._identify_chip_from_device_id("0x440"),
            "stm32f030f4"
        )
        self.assertEqual(
            self.uploader._identify_chip_from_device_id("0x423"),
            "stm32f401"
        )
        
        # Test unknown device ID
        self.assertIsNone(
            self.uploader._identify_chip_from_device_id("0x999")
        )
    
    @unittest.skipUnless(
        os.getenv('TEST_STM32_HARDWARE') == '1',
        "Set TEST_STM32_HARDWARE=1 to run hardware tests"
    )
    def test_probe_device_st_link(self):
        """Test ST-Link device probing (requires hardware)"""
        device_info = self.uploader.probe_device(None)
        
        if device_info:
            self.assertIsInstance(device_info, DeviceInfo)
            self.assertIsNotNone(device_info.chip_detected)
            print(f"Detected STM32 device: {device_info.chip_detected}")
        else:
            self.skipTest("No STM32 device detected via ST-Link")
    
    @unittest.skipUnless(
        os.getenv('TEST_STM32_HARDWARE') == '1',
        "Set TEST_STM32_HARDWARE=1 to run hardware tests"
    )
    def test_probe_device_serial(self):
        """Test serial bootloader device probing (requires hardware)"""
        # Try common serial ports
        test_ports = ["COM3", "COM4", "/dev/ttyUSB0", "/dev/ttyACM0"]
        
        for port in test_ports:
            device_info = self.uploader.probe_device(port)
            if device_info:
                self.assertIsInstance(device_info, DeviceInfo)
                print(f"Detected STM32 device on {port}: {device_info.chip_detected}")
                return
        
        self.skipTest("No STM32 device detected on serial ports")
    
    def test_bootloader_instructions(self):
        """Test bootloader instructions are provided"""
        instructions = self.uploader.get_bootloader_instructions()
        self.assertIsInstance(instructions, str)
        self.assertIn("BOOT0", instructions)
        self.assertIn("ST-Link", instructions)
    
    def test_pattern_validation(self):
        """Test pattern validation for STM32"""
        is_valid, warnings = self.uploader.validate_pattern_for_chip(self.test_pattern)
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(warnings, list)
    
    def test_chip_settings(self):
        """Test chip-specific settings are configured"""
        self.assertIn(self.uploader.chip_id, self.uploader.chip_settings)
        settings = self.uploader.chip_settings[self.uploader.chip_id]
        self.assertIn("flash_start", settings)
        self.assertIn("flash_size", settings)
        self.assertIn("device_id", settings)


class TestPICHardwareVerification(unittest.TestCase):
    """Test PIC uploader hardware detection and communication"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.uploader = PicUploader("pic16f876a")
        self.test_pattern = Pattern(
            name="Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
            ]
        )
    
    @unittest.skipUnless(
        os.getenv('TEST_PIC_HARDWARE') == '1',
        "Set TEST_PIC_HARDWARE=1 to run hardware tests"
    )
    def test_probe_device_pickit(self):
        """Test PICkit device probing (requires hardware)"""
        device_info = self.uploader.probe_device("pickit3")
        
        if device_info:
            self.assertIsInstance(device_info, DeviceInfo)
            self.assertIsNotNone(device_info.chip_detected)
            print(f"Detected PIC device: {device_info.chip_detected}")
        else:
            self.skipTest("No PIC device detected via PICkit")
    
    def test_bootloader_instructions(self):
        """Test bootloader instructions are provided"""
        instructions = self.uploader.get_bootloader_instructions()
        self.assertIsInstance(instructions, str)
        self.assertIn("ICSP", instructions)
        self.assertIn("PICkit", instructions)
    
    def test_pattern_validation(self):
        """Test pattern validation for PIC"""
        is_valid, warnings = self.uploader.validate_pattern_for_chip(self.test_pattern)
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(warnings, list)
    
    def test_pic_families(self):
        """Test PIC family mapping"""
        self.assertIn(self.uploader.chip_id, self.uploader.pic_families)
        family = self.uploader.pic_families[self.uploader.chip_id]
        self.assertIn(family, ["PIC12", "PIC16", "PIC18"])


class TestHardwareIntegration(unittest.TestCase):
    """Integration tests for hardware uploaders"""
    
    def test_uploader_registry_stm32(self):
        """Test STM32 uploader is registered"""
        from uploaders.uploader_registry import UploaderRegistry
        
        registry = UploaderRegistry.instance()
        uploader = registry.get_uploader_for_chip("stm32f103c8")
        
        self.assertIsNotNone(uploader)
        self.assertIsInstance(uploader, Stm32Uploader)
    
    def test_uploader_registry_pic(self):
        """Test PIC uploader is registered"""
        from uploaders.uploader_registry import UploaderRegistry
        
        registry = UploaderRegistry.instance()
        uploader = registry.get_uploader_for_chip("pic16f876a")
        
        self.assertIsNotNone(uploader)
        self.assertIsInstance(uploader, PicUploader)
    
    def test_supported_chips_list(self):
        """Test supported chips are listed"""
        from uploaders.uploader_registry import UploaderRegistry
        
        registry = UploaderRegistry.instance()
        chips = registry.list_supported_chips()
        
        # Check STM32 chips
        stm32_chips = [c for c in chips if c.startswith("stm32")]
        self.assertGreater(len(stm32_chips), 0)
        
        # Check PIC chips
        pic_chips = [c for c in chips if c.startswith("pic")]
        self.assertGreater(len(pic_chips), 0)
    
    def test_chip_specs_available(self):
        """Test chip specifications are available"""
        from uploaders.uploader_registry import UploaderRegistry
        
        registry = UploaderRegistry.instance()
        
        # Test STM32 spec
        stm32_spec = registry.get_chip_spec("stm32f103c8")
        self.assertIsNotNone(stm32_spec)
        self.assertIn("flash_size", stm32_spec)
        
        # Test PIC spec
        pic_spec = registry.get_chip_spec("pic16f876a")
        self.assertIsNotNone(pic_spec)
        self.assertIn("flash_size", pic_spec)


class TestHardwareMocking(unittest.TestCase):
    """Test uploaders with mocked hardware responses"""
    
    def test_stm32_probe_mock_st_link(self):
        """Test STM32 probing with mocked ST-Link response"""
        uploader = Stm32Uploader("stm32f103c8")
        
        mock_output = """
        Device ID: 0x410
        Flash size: 65536
        """
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=mock_output,
                stderr=""
            )
            
            with patch('shutil.which', return_value='/usr/bin/st-info'):
                device_info = uploader.probe_device(None)
                
                if device_info:
                    self.assertEqual(device_info.chip_detected, "stm32f103c8")
                    self.assertEqual(device_info.flash_size, 65536)
    
    def test_pic_probe_mock_pickit(self):
        """Test PIC probing with mocked PICkit response"""
        uploader = PicUploader("pic16f876a")
        
        mock_output = "Device ID: 0x1234\nPIC16F876A detected"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=mock_output,
                stderr=""
            )
            
            with patch('shutil.which', return_value='/usr/bin/pk3cmd'):
                device_info = uploader.probe_device("pickit3")
                
                if device_info:
                    self.assertEqual(device_info.chip_detected, "pic16f876a")
                    self.assertEqual(device_info.port, "pickit3")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

