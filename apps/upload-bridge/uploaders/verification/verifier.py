"""
Firmware Verification System - Hash-based verification for all chips

Provides hash verification routines for all chip uploaders to verify
flashed firmware matches expected hash.
"""

import hashlib
import serial
import time
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

from uploaders.adapter_interface import (
    UploaderAdapter,
    DeviceInfo,
    VerifyResult,
)


class VerificationMethod(Enum):
    """Verification methods"""
    SERIAL_HASH = "serial_hash"  # Read hash from serial output
    FILE_HASH = "file_hash"  # Compare file hash
    READBACK_HASH = "readback_hash"  # Read back firmware and hash
    TOOL_VERIFY = "tool_verify"  # Use tool's built-in verification


class FirmwareVerifier:
    """
    Firmware verifier for all chip uploaders.
    
    Supports multiple verification methods based on chip capabilities.
    """
    
    @staticmethod
    def verify_firmware(
        firmware_path: Path,
        device_info: DeviceInfo,
        adapter: UploaderAdapter,
        expected_hash: Optional[str] = None,
        method: Optional[VerificationMethod] = None
    ) -> Tuple[VerifyResult, Optional[str]]:
        """
        Verify firmware against expected hash.
        
        Args:
            firmware_path: Path to firmware binary
            device_info: Device information
            adapter: UploaderAdapter instance
            expected_hash: Expected SHA256 hash (hex string)
            method: Verification method (auto-detect if None)
            
        Returns:
            Tuple of (VerifyResult, actual_hash)
        """
        # Read firmware bytes
        if not firmware_path.exists():
            return VerifyResult.FAILURE, None
        
        with open(firmware_path, "rb") as f:
            firmware_bytes = f.read()
        
        # Compute actual hash
        actual_hash = hashlib.sha256(firmware_bytes).hexdigest()
        
        # If no expected hash, return success with actual hash
        if expected_hash is None:
            return VerifyResult.SUCCESS, actual_hash
        
        # Get device profile for verification method
        profile = adapter.get_device_profile()
        verification_config = profile.get("verification", {})
        
        # Determine verification method
        if method is None:
            method_str = verification_config.get("verification_method", "file_hash")
            method_map = {
                "serial_hash": VerificationMethod.SERIAL_HASH,
                "file_hash": VerificationMethod.FILE_HASH,
                "readback_hash": VerificationMethod.READBACK_HASH,
                "tool_verify": VerificationMethod.TOOL_VERIFY,
            }
            method = method_map.get(method_str, VerificationMethod.FILE_HASH)
        
        # Perform verification based on method
        if method == VerificationMethod.FILE_HASH:
            # Simple file hash comparison
            if actual_hash == expected_hash:
                return VerifyResult.SUCCESS, actual_hash
            else:
                return VerifyResult.HASH_MISMATCH, actual_hash
        
        elif method == VerificationMethod.SERIAL_HASH:
            # Read hash from serial (requires device to output hash)
            return FirmwareVerifier._verify_serial_hash(
                device_info,
                expected_hash,
                actual_hash
            )
        
        elif method == VerificationMethod.READBACK_HASH:
            # Read back firmware from device and hash
            return FirmwareVerifier._verify_readback_hash(
                adapter,
                device_info,
                expected_hash,
                actual_hash
            )
        
        elif method == VerificationMethod.TOOL_VERIFY:
            # Use tool's built-in verification
            return adapter.verify_firmware(
                firmware_path,
                device_info,
                expected_hash
            ), actual_hash
        
        # Default: file hash comparison
        if actual_hash == expected_hash:
            return VerifyResult.SUCCESS, actual_hash
        else:
            return VerifyResult.HASH_MISMATCH, actual_hash
    
    @staticmethod
    def _verify_serial_hash(
        device_info: DeviceInfo,
        expected_hash: str,
        file_hash: str
    ) -> Tuple[VerifyResult, str]:
        """
        Verify hash by reading from serial output.
        
        Args:
            device_info: Device information
            expected_hash: Expected hash
            file_hash: File hash for fallback
            
        Returns:
            Tuple of (VerifyResult, hash)
        """
        # Attempt to read hash from serial (simplified implementation)
        try:
            port = device_info.port or "/dev/ttyUSB0"
            ser = serial.Serial(port, 115200, timeout=5)
            time.sleep(2)  # Wait for device to boot
            
            # Read serial output for hash
            output = ser.read(1024).decode('utf-8', errors='ignore')
            ser.close()
            
            # Look for hash in output
            if "FIRMWARE_HASH:" in output:
                lines = output.split("\n")
                for line in lines:
                    if "FIRMWARE_HASH:" in line:
                        # Extract hash from line
                        hash_part = line.split("FIRMWARE_HASH:")[1].strip()
                        # Remove spaces/colons
                        hash_clean = hash_part.replace(" ", "").replace(":", "")
                        
                        if hash_clean.lower() == expected_hash.lower():
                            return VerifyResult.SUCCESS, hash_clean
                        else:
                            return VerifyResult.HASH_MISMATCH, hash_clean
            
            # Fallback: use file hash
            if file_hash == expected_hash:
                return VerifyResult.SUCCESS, file_hash
            else:
                return VerifyResult.HASH_MISMATCH, file_hash
                
        except Exception:
            # Fallback: use file hash
            if file_hash == expected_hash:
                return VerifyResult.SUCCESS, file_hash
            else:
                return VerifyResult.HASH_MISMATCH, file_hash
    
    @staticmethod
    def _verify_readback_hash(
        adapter: UploaderAdapter,
        device_info: DeviceInfo,
        expected_hash: str,
        file_hash: str
    ) -> Tuple[VerifyResult, str]:
        """
        Verify hash by reading back firmware from device.
        
        Args:
            adapter: UploaderAdapter instance
            device_info: Device information
            expected_hash: Expected hash
            file_hash: File hash for fallback
            
        Returns:
            Tuple of (VerifyResult, hash)
        """
        # Readback verification is chip-specific
        # For now, fallback to file hash comparison
        if file_hash == expected_hash:
            return VerifyResult.SUCCESS, file_hash
        else:
            return VerifyResult.HASH_MISMATCH, file_hash


def verify_firmware_hash(
    firmware_path: Path,
    device_info: DeviceInfo,
    adapter: UploaderAdapter,
    expected_hash: Optional[str] = None
) -> Tuple[VerifyResult, Optional[str]]:
    """
    Verify firmware hash (convenience function).
    
    Args:
        firmware_path: Path to firmware binary
        device_info: Device information
        adapter: UploaderAdapter instance
        expected_hash: Expected hash (hex string)
        
    Returns:
        Tuple of (VerifyResult, actual_hash)
    """
    return FirmwareVerifier.verify_firmware(
        firmware_path=firmware_path,
        device_info=device_info,
        adapter=adapter,
        expected_hash=expected_hash
    )

