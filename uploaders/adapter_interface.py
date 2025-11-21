"""
UploaderAdapter Interface - Standard interface for all chip uploaders

Defines the ABC (Abstract Base Class) for all uploader adapters with
required methods for device detection, firmware building, flashing, and verification.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum


class FlashResult(Enum):
    """Flash operation result"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    VERIFICATION_FAILED = "verification_failed"


class VerifyResult(Enum):
    """Verification operation result"""
    SUCCESS = "success"
    FAILURE = "failure"
    HASH_MISMATCH = "hash_mismatch"
    TIMEOUT = "timeout"


@dataclass
class DeviceInfo:
    """Device information"""
    chip_id: str  # Chip identifier (e.g., "ESP32", "STM32F407")
    chip_variant: Optional[str] = None  # Variant (e.g., "ESP32-S3", "ESP32-C3")
    port: Optional[str] = None  # Serial port
    firmware_version: Optional[str] = None
    capabilities: List[str] = None  # List of capabilities (e.g., ["flash", "verify", "erase"])
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class FlashOptions:
    """Flash operation options"""
    verify: bool = True  # Verify after flash
    erase: bool = False  # Erase before flash
    baud_rate: int = 115200  # Serial baud rate
    flash_size: Optional[str] = None  # Flash size (e.g., "4MB", "8MB")
    flash_mode: Optional[str] = None  # Flash mode (e.g., "qio", "dio")
    flash_freq: Optional[str] = None  # Flash frequency (e.g., "40m", "80m")
    partition_table: Optional[Path] = None  # Partition table path
    extra_options: Dict[str, Any] = None  # Chip-specific options
    
    def __post_init__(self):
        if self.extra_options is None:
            self.extra_options = {}


@dataclass
class BuildResult:
    """Firmware build result"""
    success: bool
    firmware_path: Optional[Path] = None
    build_log: Optional[str] = None
    error_message: Optional[str] = None
    artifact_hash: Optional[str] = None  # SHA256 hash of firmware binary


class UploaderAdapter(ABC):
    """
    Abstract base class for chip uploader adapters.
    
    All chip-specific uploaders must implement this interface.
    """
    
    @property
    @abstractmethod
    def chip_id(self) -> str:
        """
        Chip identifier (e.g., "ESP32", "STM32F407").
        
        Returns:
            Chip ID string
        """
        pass
    
    @property
    @abstractmethod
    def chip_variant(self) -> Optional[str]:
        """
        Chip variant if applicable (e.g., "ESP32-S3", "ESP32-C3").
        
        Returns:
            Variant string or None
        """
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Supported firmware formats (e.g., ["bin", "elf", "hex"]).
        
        Returns:
            List of format strings
        """
        pass
    
    @abstractmethod
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """
        Detect connected device.
        
        Args:
            port: Optional serial port (auto-detect if None)
            
        Returns:
            DeviceInfo if device detected, None otherwise
        """
        pass
    
    @abstractmethod
    def build_firmware(
        self,
        pattern: Any,  # Pattern object
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> BuildResult:
        """
        Build firmware from pattern.
        
        Args:
            pattern: Pattern object
            output_path: Path to save firmware binary
            options: Optional build options (chip-specific)
            
        Returns:
            BuildResult with success status and firmware path
        """
        pass
    
    @abstractmethod
    def flash_firmware(
        self,
        firmware_path: Path,
        device_info: DeviceInfo,
        options: Optional[FlashOptions] = None
    ) -> FlashResult:
        """
        Flash firmware to device.
        
        Args:
            firmware_path: Path to firmware binary
            device_info: Device information
            options: Optional flash options
            
        Returns:
            FlashResult enum
        """
        pass
    
    @abstractmethod
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
            expected_hash: Optional expected hash for verification
            
        Returns:
            VerifyResult enum
        """
        pass
    
    @abstractmethod
    def get_device_profile(self) -> Dict[str, Any]:
        """
        Get device profile (JSON-serializable dictionary).
        
        Returns:
            Device profile dictionary
        """
        pass
    
    def supports_operation(self, operation: str) -> bool:
        """
        Check if adapter supports an operation.
        
        Args:
            operation: Operation name (e.g., "flash", "verify", "erase")
            
        Returns:
            True if operation is supported
        """
        return operation in self.get_capabilities()
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of supported capabilities.
        
        Returns:
            List of capability strings
        """
        return ["flash", "verify"]  # Default capabilities

