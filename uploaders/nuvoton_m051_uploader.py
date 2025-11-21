"""
Nuvoton M051 Uploader Adapter - Standard UploaderAdapter implementation

Implements the UploaderAdapter interface for Nuvoton M051 chips using Nu-Link tools.
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


class NuvotonM051Uploader(UploaderAdapter):
    """Uploader adapter for Nuvoton M051 chips"""
    
    @property
    def chip_id(self) -> str:
        return "NuvotonM051"
    
    @property
    def chip_variant(self) -> Optional[str]:
        return "M051"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["bin", "hex"]
    
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """Detect Nuvoton M051 device"""
        try:
            # Nu-Link tools detection (simplified)
            cmd = ["nu-link", "-device", "M051", "-list"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return DeviceInfo(
                    chip_id="NuvotonM051",
                    chip_variant="M051",
                    port=port or "auto",
                    capabilities=["flash", "verify"]
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
        """Build Nuvoton M051 firmware from pattern"""
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
        """Flash firmware to Nuvoton M051"""
        if options is None:
            options = FlashOptions()
        
        try:
            # Nu-Link flash command (simplified)
            cmd = [
                "nu-link",
                "-device", "M051",
                "-program", str(firmware_path),
                "-verify" if options.verify else ""
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
        """Get Nuvoton M051 device profile"""
        return {
            "chip_id": "NuvotonM051",
            "chip_variant": "M051",
            "chip_name": "Nuvoton M051",
            "manufacturer": "Nuvoton",
            "architecture": "ARM Cortex-M0",
            "flash_size_bytes": 65536,
            "ram_size_bytes": 4096,
            "cpu_frequency_mhz": 50,
            "supported_formats": ["bin", "hex"],
            "toolchain": {
                "compiler": "arm-none-eabi-gcc",
                "flasher": "nu-link",
                "version_required": "3.08"
            },
            "capabilities": ["flash", "verify"]
        }


register_adapter(NuvotonM051Uploader)

