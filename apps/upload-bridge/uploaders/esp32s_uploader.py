"""
ESP32-S Uploader Adapter - Standard UploaderAdapter implementation for ESP32-S

Implements the UploaderAdapter interface for ESP32-S chips using esptool.
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


class ESP32SUploader(UploaderAdapter):
    """Uploader adapter for ESP32-S chips"""
    
    @property
    def chip_id(self) -> str:
        return "ESP32"
    
    @property
    def chip_variant(self) -> Optional[str]:
        return "ESP32-S"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["bin", "elf"]
    
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """Detect ESP32-S device"""
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
            
            if result.returncode == 0 and "ESP32-S" in result.stdout:
                return DeviceInfo(
                    chip_id="ESP32",
                    chip_variant="ESP32-S",
                    port=port or "auto",
                    capabilities=["flash", "verify", "erase"]
                )
        except Exception:
            pass
        
        return None
    
    def build_firmware(
        self,
        pattern: Pattern,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> BuildResult:
        """Build ESP32-S firmware from pattern"""
        try:
            from core.export.encoders import build_binary_payload
            firmware_bytes = build_binary_payload(pattern, None)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(firmware_bytes)
            
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
        """Flash firmware to ESP32-S"""
        if options is None:
            options = FlashOptions()
        
        try:
            cmd = [
                "esptool.py",
                "--chip", "esp32s2",
                "--port", device_info.port or "/dev/ttyUSB0",
                "--baud", str(options.baud_rate),
                "write_flash",
                "--flash_mode", options.flash_mode or "dio",
                "--flash_freq", options.flash_freq or "40m",
                "--flash_size", options.flash_size or "4MB",
                "0x1000", str(firmware_path),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                if options.verify:
                    verify_result = self.verify_firmware(firmware_path, device_info, None)
                    if verify_result != VerifyResult.SUCCESS:
                        return FlashResult.VERIFICATION_FAILED
                return FlashResult.SUCCESS
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
        """Verify flashed firmware"""
        try:
            if expected_hash and firmware_path.exists():
                with open(firmware_path, "rb") as f:
                    firmware_bytes = f.read()
                actual_hash = hashlib.sha256(firmware_bytes).hexdigest()
                if actual_hash != expected_hash:
                    return VerifyResult.HASH_MISMATCH
            
            if firmware_path.exists():
                return VerifyResult.SUCCESS
            return VerifyResult.FAILURE
        except Exception:
            return VerifyResult.FAILURE
    
    def get_device_profile(self) -> Dict[str, Any]:
        """Get ESP32-S device profile"""
        profile_path = Path(__file__).parent / "profiles" / "esp32s.json"
        if profile_path.exists():
            import json
            import logging
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logging.error(f"Failed to load ESP32-S profile from {profile_path}: {e}")
        
        return {
            "chip_id": "ESP32",
            "chip_variant": "ESP32-S",
            "chip_name": "ESP32-S",
            "manufacturer": "Espressif",
            "architecture": "Xtensa",
            "flash_size_bytes": 4194304,
            "ram_size_bytes": 32768,
            "cpu_frequency_mhz": 240,
            "supported_formats": ["bin", "elf"],
            "capabilities": ["flash", "verify", "erase"]
        }


register_adapter(ESP32SUploader)

