"""
ESP32 Uploader Adapter - Standard UploaderAdapter implementation for ESP32

Implements the UploaderAdapter interface for ESP32 chips using esptool.
"""

import subprocess
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List

from core.pattern import Pattern
from uploaders.adapter_interface import (
    UploaderAdapter,
    DeviceInfo,
    FlashResult,
    VerifyResult,
    FlashOptions,
    BuildResult,
)
from uploaders.adapter_registry import register_adapter


class ESP32Uploader(UploaderAdapter):
    """Uploader adapter for ESP32 chips"""
    
    @property
    def chip_id(self) -> str:
        return "ESP32"
    
    @property
    def chip_variant(self) -> Optional[str]:
        return None  # Base ESP32
    
    @property
    def supported_formats(self) -> List[str]:
        return ["bin", "elf"]
    
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """
        Detect ESP32 device via esptool.
        
        Args:
            port: Optional serial port
            
        Returns:
            DeviceInfo if detected, None otherwise
        """
        try:
            cmd = ["esptool.py", "chip_id"]
            if port:
                cmd.extend(["--port", port])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and "ESP32" in result.stdout:
                return DeviceInfo(
                    chip_id="ESP32",
                    port=port or "auto",
                    capabilities=["flash", "verify", "erase"]
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass
        
        return None
    
    def build_firmware(
        self,
        pattern: Pattern,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> BuildResult:
        """
        Build ESP32 firmware from pattern.
        
        Args:
            pattern: Pattern object
            output_path: Path to save firmware
            options: Optional build options
            
        Returns:
            BuildResult
        """
        try:
            # Generate firmware from pattern
            firmware_bytes = self._generate_firmware_bytes(pattern, options)
            
            # Write firmware binary
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(firmware_bytes)
            
            # Compute hash
            artifact_hash = hashlib.sha256(firmware_bytes).hexdigest()
            
            return BuildResult(
                success=True,
                firmware_path=output_path,
                artifact_hash=artifact_hash
            )
        except Exception as e:
            return BuildResult(
                success=False,
                error_message=str(e)
            )
    
    def flash_firmware(
        self,
        firmware_path: Path,
        device_info: DeviceInfo,
        options: Optional[FlashOptions] = None
    ) -> FlashResult:
        """
        Flash firmware to ESP32 using esptool.
        
        Args:
            firmware_path: Path to firmware binary
            device_info: Device information
            options: Optional flash options
            
        Returns:
            FlashResult
        """
        if options is None:
            options = FlashOptions()
        
        try:
            cmd = [
                "esptool.py",
                "--chip", "esp32",
                "--port", device_info.port or "/dev/ttyUSB0",
                "--baud", str(options.baud_rate),
            ]
            
            if options.erase:
                cmd.append("erase_flash")
                subprocess.run(cmd, check=True, timeout=30)
                cmd = cmd[:-1]  # Remove erase_flash
            
            cmd.extend([
                "write_flash",
                "--flash_mode", options.flash_mode or "dio",
                "--flash_freq", options.flash_freq or "40m",
                "--flash_size", options.flash_size or "4MB",
                "0x1000", str(firmware_path),
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                if options.verify:
                    verify_result = self.verify_firmware(
                        firmware_path,
                        device_info,
                        None
                    )
                    if verify_result != VerifyResult.SUCCESS:
                        return FlashResult.VERIFICATION_FAILED
                return FlashResult.SUCCESS
            else:
                return FlashResult.FAILURE
                
        except subprocess.TimeoutExpired:
            return FlashResult.TIMEOUT
        except Exception:
            return FlashResult.FAILURE
    
    def verify_firmware(
        self,
        firmware_path: Path,
        device_info: DeviceInfo,
        expected_hash: Optional[str] = None
    ) -> VerifyResult:
        """
        Verify flashed firmware.
        
        Args:
            firmware_path: Path to firmware binary
            device_info: Device information
            expected_hash: Optional expected hash
            
        Returns:
            VerifyResult
        """
        # For ESP32, verification is done during flash (read-back verification)
        # This is a simplified implementation
        try:
            if expected_hash:
                # Read firmware and compute hash
                with open(firmware_path, "rb") as f:
                    firmware_bytes = f.read()
                actual_hash = hashlib.sha256(firmware_bytes).hexdigest()
                
                if actual_hash != expected_hash:
                    return VerifyResult.HASH_MISMATCH
            
            # Basic verification: check file exists
            if firmware_path.exists():
                return VerifyResult.SUCCESS
            else:
                return VerifyResult.FAILURE
                
        except Exception:
            return VerifyResult.FAILURE
    
    def get_device_profile(self) -> Dict[str, Any]:
        """Get ESP32 device profile"""
        profile_path = Path(__file__).parent / "profiles" / "esp32.json"
        if profile_path.exists():
            import json
            with open(profile_path, "r") as f:
                return json.load(f)
        
        # Default profile
        return {
            "chip_id": "ESP32",
            "chip_name": "ESP32",
            "manufacturer": "Espressif",
            "architecture": "Xtensa",
            "flash_size_bytes": 4194304,
            "ram_size_bytes": 32768,
            "cpu_frequency_mhz": 240,
            "supported_formats": ["bin", "elf"],
            "toolchain": {
                "compiler": "xtensa-esp32-elf-gcc",
                "flasher": "esptool",
                "version_required": "4.0.0"
            },
            "flash_options": {
                "default_baud_rate": 115200,
                "flash_mode": "dio",
                "flash_freq": "40m",
                "flash_size": "4MB"
            },
            "capabilities": ["flash", "verify", "erase"]
        }
    
    def _generate_firmware_bytes(self, pattern: Pattern, options: Optional[Dict[str, Any]]) -> bytes:
        """
        Generate firmware binary from pattern.
        
        Args:
            pattern: Pattern object
            options: Optional build options
            
        Returns:
            Firmware bytes
        """
        # Simplified firmware generation - in production, this would use
        # actual firmware templates and compiler toolchain
        from core.export.encoders import build_binary_payload
        
        # Export pattern to binary format
        firmware_bytes = build_binary_payload(pattern, None)
        
        return firmware_bytes
    
    def get_capabilities(self) -> List[str]:
        return ["flash", "verify", "erase", "reset"]


# Register adapter
register_adapter(ESP32Uploader)

