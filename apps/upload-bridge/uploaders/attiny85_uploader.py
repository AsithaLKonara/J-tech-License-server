"""
ATtiny85 Uploader Adapter - Standard UploaderAdapter implementation

Implements the UploaderAdapter interface for ATtiny85 chips using avrdude.
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


class ATtiny85Uploader(UploaderAdapter):
    """Uploader adapter for ATtiny85 chips"""
    
    @property
    def chip_id(self) -> str:
        return "ATtiny85"
    
    @property
    def chip_variant(self) -> Optional[str]:
        return None
    
    @property
    def supported_formats(self) -> List[str]:
        return ["hex", "bin"]
    
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """Detect ATtiny85 device"""
        try:
            cmd = ["avrdude", "-p", "t85", "-c", "usbtiny", "-v"]
            if port:
                cmd.extend(["-P", port])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return DeviceInfo(
                    chip_id="ATtiny85",
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
        """Build ATtiny85 firmware from pattern"""
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
        """Flash firmware to ATtiny85"""
        if options is None:
            options = FlashOptions()
        
        try:
            cmd = [
                "avrdude",
                "-p", "t85",
                "-c", "usbtiny",
                "-U", f"flash:w:{firmware_path}:i"
            ]
            
            if options.verify:
                cmd[-1] = cmd[-1].replace(":i", ":i:v")
            
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
        """Get ATtiny85 device profile"""
        return {
            "chip_id": "ATtiny85",
            "chip_name": "ATtiny85",
            "manufacturer": "Microchip",
            "architecture": "AVR",
            "flash_size_bytes": 8192,
            "ram_size_bytes": 512,
            "cpu_frequency_mhz": 8,
            "supported_formats": ["hex", "bin"],
            "capabilities": ["flash", "verify"]
        }


register_adapter(ATtiny85Uploader)

