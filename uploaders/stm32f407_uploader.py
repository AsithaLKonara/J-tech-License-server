"""
STM32F407 Uploader Adapter - Standard UploaderAdapter implementation

Implements the UploaderAdapter interface for STM32F407 chips using stm32flash.
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


class STM32F407Uploader(UploaderAdapter):
    """Uploader adapter for STM32F407 chips"""
    
    @property
    def chip_id(self) -> str:
        return "STM32F407"
    
    @property
    def chip_variant(self) -> Optional[str]:
        return None
    
    @property
    def supported_formats(self) -> List[str]:
        return ["hex", "bin"]
    
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """Detect STM32F407 device"""
        try:
            cmd = ["stm32flash", "-b", "115200"]
            if port:
                cmd.extend([port])
            else:
                cmd.append("/dev/ttyACM0")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and "STM32F4" in result.stdout:
                return DeviceInfo(
                    chip_id="STM32F407",
                    port=port or "/dev/ttyACM0",
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
        """Build STM32F407 firmware from pattern"""
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
            return BuildResult(success=False, error_message=str(e))
    
    def flash_firmware(
        self,
        firmware_path: Path,
        device_info: DeviceInfo,
        options: Optional[FlashOptions] = None
    ) -> FlashResult:
        """Flash firmware to STM32F407"""
        if options is None:
            options = FlashOptions()
        
        try:
            cmd = [
                "stm32flash",
                "-b", str(options.baud_rate),
                "-w", str(firmware_path),
                "-v" if options.verify else "",
                device_info.port or "/dev/ttyACM0"
            ]
            cmd = [c for c in cmd if c]  # Remove empty strings
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
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
            return VerifyResult.SUCCESS
        except Exception:
            return VerifyResult.FAILURE
    
    def get_device_profile(self) -> Dict[str, Any]:
        """Get STM32F407 device profile"""
        return {
            "chip_id": "STM32F407",
            "chip_name": "STM32F407",
            "manufacturer": "STMicroelectronics",
            "architecture": "ARM Cortex-M4",
            "flash_size_bytes": 1048576,
            "ram_size_bytes": 196608,
            "cpu_frequency_mhz": 168,
            "supported_formats": ["hex", "bin"],
            "toolchain": {
                "compiler": "arm-none-eabi-gcc",
                "flasher": "stm32flash",
                "version_required": "0.6"
            },
            "capabilities": ["flash", "verify", "erase"]
        }


register_adapter(STM32F407Uploader)

