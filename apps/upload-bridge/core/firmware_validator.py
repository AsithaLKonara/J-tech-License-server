"""
Firmware Validator - Pre-flash validation to prevent device bricking.

Validates firmware files before flashing to ensure they are:
- Valid format for the target chip
- Non-empty
- Within size limits
- Not corrupted
"""

import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FirmwareValidationError(Exception):
    """Raised when firmware validation fails."""
    pass


class FirmwareValidator:
    """Validates firmware files before flashing to prevent device bricking."""
    
    # Minimum firmware sizes (bytes) - firmware should not be empty
    MIN_FIRMWARE_SIZES = {
        'esp8266': 1024,  # 1KB minimum
        'esp32': 4096,    # 4KB minimum
        'esp32s': 4096,
        'esp32s2': 4096,
        'esp32s3': 4096,
        'esp32c3': 4096,
        'stm32': 512,     # 512 bytes minimum
        'arduino': 512,
        'pic': 256,       # 256 bytes minimum
        'numicro': 512,
    }
    
    # Maximum firmware sizes (bytes) - prevent flashing oversized files
    MAX_FIRMWARE_SIZES = {
        'esp8266': 4 * 1024 * 1024,   # 4MB max (typical flash size)
        'esp32': 16 * 1024 * 1024,    # 16MB max
        'esp32s': 16 * 1024 * 1024,
        'esp32s2': 16 * 1024 * 1024,
        'esp32s3': 16 * 1024 * 1024,
        'esp32c3': 16 * 1024 * 1024,
        'stm32': 2 * 1024 * 1024,     # 2MB max
        'arduino': 256 * 1024,        # 256KB max (typical for ATmega)
        'pic': 64 * 1024,             # 64KB max
        'numicro': 512 * 1024,        # 512KB max
    }
    
    @staticmethod
    def validate_firmware_file(
        firmware_path: Path,
        chip_id: str,
        expected_hash: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate firmware file before flashing.
        
        Args:
            firmware_path: Path to firmware file
            chip_id: Target chip identifier
            expected_hash: Optional expected SHA256 hash
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Raises:
            FirmwareValidationError: If validation fails critically
        """
        try:
            # Check if file exists
            if not firmware_path.exists():
                return False, f"Firmware file not found: {firmware_path}"
            
            # Check if file is readable
            if not firmware_path.is_file():
                return False, f"Firmware path is not a file: {firmware_path}"
            
            # Read file size
            file_size = firmware_path.stat().st_size
            
            # Check minimum size (prevent empty/corrupted files)
            min_size = FirmwareValidator.MIN_FIRMWARE_SIZES.get(chip_id.lower(), 256)
            if file_size < min_size:
                return False, (
                    f"Firmware file too small ({file_size} bytes). "
                    f"Minimum size for {chip_id} is {min_size} bytes. "
                    "File may be corrupted or incomplete."
                )
            
            # Check maximum size (prevent oversized files)
            max_size = FirmwareValidator.MAX_FIRMWARE_SIZES.get(chip_id.lower(), 16 * 1024 * 1024)
            if file_size > max_size:
                return False, (
                    f"Firmware file too large ({file_size} bytes). "
                    f"Maximum size for {chip_id} is {max_size} bytes. "
                    "File may be for wrong chip type or corrupted."
                )
            
            # Read and validate file is not empty or all zeros
            with open(firmware_path, 'rb') as f:
                # Read first 1KB to check if file is all zeros
                first_chunk = f.read(1024)
                if len(first_chunk) > 0 and all(b == 0 for b in first_chunk):
                    # Check if entire file is zeros
                    f.seek(0)
                    file_bytes = f.read()
                    if all(b == 0 for b in file_bytes):
                        return False, (
                            "Firmware file contains only zeros. "
                            "File is likely corrupted or uninitialized."
                        )
                
                # Compute hash for verification
                f.seek(0)
                file_bytes = f.read()
                actual_hash = hashlib.sha256(file_bytes).hexdigest()
            
            # Verify hash if expected hash provided
            if expected_hash:
                if actual_hash.lower() != expected_hash.lower():
                    return False, (
                        f"Firmware hash mismatch. "
                        f"Expected: {expected_hash[:16]}..., "
                        f"Got: {actual_hash[:16]}... "
                        "File may be corrupted or modified."
                    )
            
            # Chip-specific format validation
            validation_error = FirmwareValidator._validate_chip_format(firmware_path, chip_id, file_bytes)
            if validation_error:
                return False, validation_error
            
            logger.info(f"Firmware validation passed: {firmware_path} ({file_size} bytes, hash: {actual_hash[:16]}...)")
            return True, None
            
        except PermissionError as e:
            return False, f"Cannot read firmware file (permission denied): {e}"
        except Exception as e:
            logger.error(f"Firmware validation error: {e}", exc_info=True)
            return False, f"Firmware validation failed: {str(e)}"
    
    @staticmethod
    def _validate_chip_format(
        firmware_path: Path,
        chip_id: str,
        file_bytes: bytes
    ) -> Optional[str]:
        """
        Validate chip-specific firmware format.
        
        Args:
            firmware_path: Path to firmware file
            chip_id: Target chip identifier
            file_bytes: Firmware file bytes
            
        Returns:
            Error message if validation fails, None if valid
        """
        chip_lower = chip_id.lower()
        
        # ESP chips - check for ESP32/ESP8266 magic bytes
        if chip_lower.startswith('esp'):
            # ESP32 firmware typically starts with specific magic bytes
            # This is a basic check - more sophisticated validation could check ESP image headers
            if len(file_bytes) >= 4:
                # Check if file looks like binary (has non-zero bytes)
                if all(b == 0 for b in file_bytes[:4]):
                    return "Firmware file appears to be empty or uninitialized"
        
        # Intel HEX format (for AVR, PIC, etc.)
        if firmware_path.suffix.lower() == '.hex':
            # Check for Intel HEX format signature
            try:
                file_text = file_bytes[:100].decode('ascii', errors='ignore')
                if not file_text.startswith(':'):
                    return "Intel HEX file does not start with ':' (invalid format)"
            except Exception:
                pass  # Binary file, not hex
        
        # Binary files - basic sanity check
        if firmware_path.suffix.lower() in ['.bin', '.dat']:
            # Check that file has some variation (not all same byte value)
            if len(file_bytes) > 256:
                unique_bytes = len(set(file_bytes[:256]))
                if unique_bytes < 4:
                    return "Firmware file has very low entropy (may be corrupted or invalid)"
        
        return None
    
    @staticmethod
    def get_firmware_info(firmware_path: Path) -> Dict[str, Any]:
        """
        Get information about firmware file.
        
        Args:
            firmware_path: Path to firmware file
            
        Returns:
            Dictionary with firmware information
        """
        try:
            if not firmware_path.exists():
                return {'error': 'File not found'}
            
            file_size = firmware_path.stat().st_size
            
            with open(firmware_path, 'rb') as f:
                file_bytes = f.read()
            
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            
            return {
                'path': str(firmware_path),
                'size_bytes': file_size,
                'size_kb': file_size / 1024,
                'sha256_hash': file_hash,
                'extension': firmware_path.suffix.lower(),
            }
        except Exception as e:
            return {'error': str(e)}

