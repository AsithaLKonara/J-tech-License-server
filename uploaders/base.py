"""
Uploader Base Classes - Interface for all chip uploaders
Complete implementation with real error handling
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Callable
from enum import Enum


class UploadStatus(Enum):
    """Upload process status"""
    IDLE = "idle"
    VALIDATING = "validating"
    BUILDING = "building"
    UPLOADING = "uploading"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class BuildResult:
    """Result of firmware build operation"""
    success: bool
    firmware_path: str
    binary_type: str  # "hex", "bin", "elf"
    size_bytes: int
    chip_model: str
    warnings: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class UploadResult:
    """Result of firmware upload operation"""
    success: bool
    duration_seconds: float
    bytes_written: int
    verified: bool
    warnings: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class DeviceInfo:
    """Information about connected device"""
    port: str
    chip_detected: Optional[str] = None
    bootloader_version: Optional[str] = None
    flash_size: Optional[int] = None
    ram_size: Optional[int] = None
    mac_address: Optional[str] = None


class UploaderBase(ABC):
    """
    Base class for all chip uploaders
    
    Each chip family (AVR, ESP, STM32, PIC, etc.) implements this interface
    """
    
    def __init__(self, chip_id: str):
        """
        Initialize uploader for specific chip
        
        Args:
            chip_id: Chip identifier (e.g., "atmega328p", "esp8266")
        """
        self.chip_id = chip_id
        self.status = UploadStatus.IDLE
        self.progress_callback: Optional[Callable] = None
        self.last_error: Optional[str] = None
    
    @abstractmethod
    def build_firmware(self, pattern, build_opts: dict) -> BuildResult:
        """
        Build firmware with embedded pattern data
        
        Args:
            pattern: Pattern object to embed
            build_opts: Build configuration dictionary containing:
                - template_path: Path to firmware template directory
                - output_dir: Build output directory
                - optimize_level: Optimization level (0-3)
                - gpio_pin: Data pin for LEDs
                - Additional chip-specific options
        
        Returns:
            BuildResult with firmware path and metadata
        
        Raises:
            RuntimeError: If build fails critically
        """
        pass
    
    @abstractmethod
    def upload(self, firmware_path: str, port_params: dict) -> UploadResult:
        """
        Upload firmware to device
        
        Args:
            firmware_path: Path to compiled firmware binary
            port_params: Upload configuration dictionary containing:
                - port: Serial port (e.g., "COM3", "/dev/ttyUSB0")
                - baud: Baud rate (optional, uses default if not specified)
                - programmer: Programmer type (optional, chip-dependent)
                - timeout: Upload timeout in seconds (optional)
                - Additional chip-specific parameters
        
        Returns:
            UploadResult with success status and metrics
        
        Raises:
            RuntimeError: If upload fails critically
        """
        pass
    
    def verify(self, firmware_path: str, port_params: dict) -> bool:
        """
        Verify firmware after upload (optional)
        
        Args:
            firmware_path: Path to firmware that was uploaded
            port_params: Port configuration (same as upload)
        
        Returns:
            True if verification successful, False otherwise
        
        Note:
            Default implementation returns True (assume success).
            Override if chip supports read-back verification.
        """
        return True
    
    def probe_device(self, port: str) -> Optional[DeviceInfo]:
        """
        Auto-detect device information (optional)
        
        Args:
            port: Serial port to probe
        
        Returns:
            DeviceInfo if device detected, None otherwise
        
        Note:
            Default implementation returns None.
            Override if chip supports auto-detection.
        """
        return None
    
    def set_progress_callback(self, callback: Callable[[UploadStatus, float, str], None]):
        """
        Set callback for progress updates
        
        Args:
            callback: Function(status, progress, message)
                - status: UploadStatus enum value
                - progress: Float 0.0-1.0
                - message: Human-readable status message
        """
        self.progress_callback = callback
    
    def _report_progress(self, status: UploadStatus, progress: float, message: str):
        """
        Internal: Report progress to callback
        
        Args:
            status: Current upload status
            progress: Progress 0.0-1.0
            message: Status message
        """
        self.status = status
        if self.progress_callback:
            try:
                self.progress_callback(status, progress, message)
            except Exception as e:
                # Don't let callback errors break upload
                print(f"Warning: Progress callback error: {e}")
    
    @abstractmethod
    def get_supported_chips(self) -> List[str]:
        """
        Get list of chip IDs this uploader supports
        
        Returns:
            List of chip ID strings
        """
        pass
    
    @abstractmethod
    def get_requirements(self) -> List[str]:
        """
        Get list of required external tools
        
        Returns:
            List of tool names (e.g., ["avrdude", "make"])
        """
        pass
    
    def check_requirements(self) -> tuple[bool, List[str]]:
        """
        Check if all required tools are available
        
        Returns:
            Tuple of (all_available: bool, missing_tools: List[str])
        """
        import shutil
        
        missing = []
        for tool in self.get_requirements():
            if not shutil.which(tool):
                missing.append(tool)
        
        return (len(missing) == 0, missing)
    
    def get_chip_spec(self) -> dict:
        """
        Get chip specifications
        
        Returns:
            Dictionary with chip specs (flash size, RAM, etc.)
        
        Note:
            Override to provide chip-specific details
        """
        return {
            "chip_id": self.chip_id,
            "family": "unknown",
            "flash_size": 0,
            "ram_size": 0
        }
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if uploader supports specific feature
        
        Args:
            feature: Feature name ("verify", "probe", "ota", etc.)
        
        Returns:
            True if feature supported
        """
        features = {
            "verify": self.verify.__func__ != UploaderBase.verify,
            "probe": self.probe_device.__func__ != UploaderBase.probe_device,
            "ota": False  # Override in ESP uploader
        }
        return features.get(feature, False)
    
    def estimate_upload_time(self, firmware_size_bytes: int) -> float:
        """
        Estimate upload time in seconds
        
        Args:
            firmware_size_bytes: Size of firmware binary
        
        Returns:
            Estimated time in seconds
        
        Note:
            Override for chip-specific calculations
        """
        # Default: assume 115200 baud, ~11520 bytes/sec, plus 30s overhead
        transfer_time = firmware_size_bytes / 11520.0
        return transfer_time + 30.0
    
    def get_bootloader_instructions(self) -> str:
        """
        Get human-readable bootloader entry instructions
        
        Returns:
            Instruction string for entering bootloader mode
        
        Note:
            Override with chip-specific instructions
        """
        return f"Connect {self.chip_id} via USB and ensure bootloader is active."
    
    def _parse_flash_size_string(self, size_str: str) -> int:
        """
        Parse flash size string like "4MB", "80KB" to bytes
        
        Args:
            size_str: String like "4MB", "80KB", "512KB", "1GB"
        
        Returns:
            Size in bytes as integer
        
        Raises:
            ValueError: If string format is invalid
        """
        size_str = size_str.strip().upper()
        
        # Find the unit
        units = {'KB': 1024, 'MB': 1024 * 1024, 'GB': 1024 * 1024 * 1024}
        unit = None
        number_str = None
        
        for u, multiplier in units.items():
            if size_str.endswith(u):
                unit = u
                number_str = size_str[:-len(u)]
                break
        
        if unit is None:
            # Try to parse as pure number (assume bytes)
            return int(size_str)
        
        # Parse the number
        try:
            number = float(number_str)
            return int(number * units[unit])
        except ValueError:
            raise ValueError(f"Invalid flash size format: {size_str}")
    
    def validate_pattern_for_chip(self, pattern) -> tuple[bool, List[str]]:
        """
        Validate if pattern is compatible with chip
        
        Args:
            pattern: Pattern object to validate
        
        Returns:
            Tuple of (is_valid: bool, warnings: List[str])
        """
        warnings = []
        
        # Check pattern size vs chip flash
        pattern_size = pattern.estimate_memory_bytes()
        chip_spec = self.get_chip_spec()
        flash_size = chip_spec.get('flash_size', '0')
        
        # Handle string flash sizes (e.g., "4MB", "80KB")
        if isinstance(flash_size, str):
            try:
                # Parse string sizes like "4MB", "80KB", "1GB", etc.
                flash_size = self._parse_flash_size_string(flash_size)
            except (ValueError, TypeError):
                # If parsing fails, skip validation
                return (True, [])
        
        if isinstance(flash_size, (int, float)) and flash_size > 0:
            # Firmware typically uses 30-50KB, pattern gets the rest
            available = flash_size - 50000  # Conservative estimate
            
            if pattern_size > available:
                warnings.append(
                    f"Pattern size ({pattern_size} bytes) may exceed "
                    f"available flash ({available} bytes)"
                )
        
        # Check frame count for RAM limitations
        if pattern.frame_count > 10000:
            warnings.append(
                f"Very large frame count ({pattern.frame_count}), "
                "may cause playback issues"
            )
        
        return (len(warnings) == 0, warnings)


class UploaderError(Exception):
    """Base exception for uploader errors"""
    pass


class BuildError(UploaderError):
    """Raised when firmware build fails"""
    pass


class UploadError(UploaderError):
    """Raised when firmware upload fails"""
    pass


class VerificationError(UploaderError):
    """Raised when firmware verification fails"""
    pass

