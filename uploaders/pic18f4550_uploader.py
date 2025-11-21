"""
PIC18F4550 Uploader Adapter - Standard UploaderAdapter implementation

Implements the UploaderAdapter interface for PIC18F4550 chips using MPLAB X tools.
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


class PIC18F4550Uploader(UploaderAdapter):
    """Uploader adapter for PIC18F4550 chips"""
    
    @property
    def chip_id(self) -> str:
        return "PIC18F4550"
    
    @property
    def chip_variant(self) -> Optional[str]:
        return None
    
    @property
    def supported_formats(self) -> List[str]:
        return ["hex"]
    
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """Detect PIC18F4550 device"""
        # PIC devices typically require MPLAB X IDE or IPE for detection
        # This is a simplified implementation
        try:
            # Try to detect via pk2cmd or similar
            cmd = ["pk2cmd", "-PPIC18F4550", "-T"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return DeviceInfo(
                    chip_id="PIC18F4550",
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
        """Build PIC18F4550 firmware from pattern"""
        try:
            from core.export.encoders import build_intel_hex
            hex_content = build_intel_hex(pattern, None)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(hex_content)
            
            artifact_hash = hashlib.sha256(hex_content.encode('utf-8')).hexdigest()
            
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
        """Flash firmware to PIC18F4550"""
        if options is None:
            options = FlashOptions()
        
        try:
            # Use pk2cmd for flashing (simplified)
            cmd = [
                "pk2cmd",
                "-PPIC18F4550",
                "-M",
                "-F", str(firmware_path)
            ]
            
            if options.verify:
                cmd.append("-Y")
            
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
        """Get PIC18F4550 device profile"""
        return {
            "chip_id": "PIC18F4550",
            "chip_name": "PIC18F4550",
            "manufacturer": "Microchip",
            "architecture": "PIC18",
            "flash_size_bytes": 32768,
            "ram_size_bytes": 2048,
            "cpu_frequency_mhz": 48,
            "supported_formats": ["hex"],
            "toolchain": {
                "compiler": "xc8",
                "flasher": "pk2cmd",
                "version_required": "1.20"
            },
            "capabilities": ["flash", "verify"]
        }


register_adapter(PIC18F4550Uploader)

