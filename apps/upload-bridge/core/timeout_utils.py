"""
Timeout Utilities for Network Operations
Provides adaptive timeout calculation based on file size and operation type
"""

import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of network operations"""
    STATUS_CHECK = "status"
    PATTERN_UPLOAD = "upload"
    FIRMWARE_UPDATE = "firmware"
    LIBRARY_CHECK = "library"


class TimeoutCalculator:
    """
    Calculates appropriate timeout values based on operation type and data size.
    
    Timeout Strategy:
    - Status checks: Fixed 5-10 seconds
    - Pattern uploads: 10 seconds + 5 seconds per MB
    - Firmware updates: 30 seconds + 10 seconds per MB
    - Library operations: Fixed 10 seconds
    """
    
    # Timeout configurations (in seconds)
    TIMEOUT_CONFIGS = {
        OperationType.STATUS_CHECK: {
            'base': 5.0,
            'per_mb': 0.0,
            'min': 3.0,
            'max': 15.0
        },
        OperationType.PATTERN_UPLOAD: {
            'base': 10.0,
            'per_mb': 5.0,
            'min': 10.0,
            'max': 120.0
        },
        OperationType.FIRMWARE_UPDATE: {
            'base': 30.0,
            'per_mb': 10.0,
            'min': 30.0,
            'max': 300.0
        },
        OperationType.LIBRARY_CHECK: {
            'base': 10.0,
            'per_mb': 0.0,
            'min': 5.0,
            'max': 20.0
        }
    }
    
    @staticmethod
    def calculate(
        operation_type: OperationType,
        data_size_bytes: Optional[int] = None
    ) -> float:
        """
        Calculate timeout for an operation.
        
        Args:
            operation_type: Type of operation
            data_size_bytes: Size of data being transferred (optional)
        
        Returns:
            Timeout in seconds
        """
        config = TimeoutCalculator.TIMEOUT_CONFIGS[operation_type]
        
        # Calculate timeout
        timeout = config['base']
        if data_size_bytes is not None:
            data_size_mb = data_size_bytes / (1024 * 1024)
            timeout += config['per_mb'] * data_size_mb
        
        # Apply bounds
        timeout = max(config['min'], min(timeout, config['max']))
        
        logger.debug(
            f"Calculated timeout for {operation_type.value}: "
            f"{timeout:.1f}s "
            f"(data: {data_size_bytes / (1024*1024) if data_size_bytes else 0:.1f}MB)"
        )
        
        return timeout
    
    @staticmethod
    def for_status_check() -> float:
        """Get timeout for status check"""
        return TimeoutCalculator.calculate(OperationType.STATUS_CHECK)
    
    @staticmethod
    def for_pattern_upload(file_size_bytes: int) -> float:
        """Get timeout for pattern upload"""
        return TimeoutCalculator.calculate(OperationType.PATTERN_UPLOAD, file_size_bytes)
    
    @staticmethod
    def for_firmware_update(file_size_bytes: int) -> float:
        """Get timeout for firmware update"""
        return TimeoutCalculator.calculate(OperationType.FIRMWARE_UPDATE, file_size_bytes)
    
    @staticmethod
    def for_library_check() -> float:
        """Get timeout for library check"""
        return TimeoutCalculator.calculate(OperationType.LIBRARY_CHECK)
    
    @staticmethod
    def get_config(operation_type: OperationType) -> dict:
        """
        Get timeout configuration for operation type.
        
        Args:
            operation_type: Type of operation
        
        Returns:
            Configuration dictionary
        """
        return TimeoutCalculator.TIMEOUT_CONFIGS[operation_type].copy()


class AdaptiveTimeout:
    """
    Manages timeout with automatic adjustment based on network conditions.
    """
    
    def __init__(
        self,
        initial_timeout: float,
        min_timeout: float = 5.0,
        max_timeout: float = 300.0
    ):
        """
        Initialize adaptive timeout.
        
        Args:
            initial_timeout: Initial timeout value in seconds
            min_timeout: Minimum allowed timeout in seconds
            max_timeout: Maximum allowed timeout in seconds
        """
        self.initial_timeout = initial_timeout
        self.min_timeout = min_timeout
        self.max_timeout = max_timeout
        self.current_timeout = initial_timeout
        self.adjustment_factor = 1.0
        self.failures = 0
        self.successes = 0
    
    def record_success(self) -> None:
        """Record a successful operation"""
        self.successes += 1
        self.failures = 0
        
        # Decrease timeout slightly on success
        if self.successes > 2 and self.current_timeout > self.initial_timeout * 0.8:
            self.adjustment_factor = max(0.95, self.adjustment_factor - 0.05)
            self.current_timeout = self.initial_timeout * self.adjustment_factor
    
    def record_failure(self) -> None:
        """Record a failed operation (timeout)"""
        self.failures += 1
        self.successes = 0
        
        # Increase timeout on failure
        if self.failures > 1:
            self.adjustment_factor = min(2.0, self.adjustment_factor + 0.25)
            new_timeout = self.initial_timeout * self.adjustment_factor
            self.current_timeout = min(new_timeout, self.max_timeout)
            
            logger.warning(
                f"Timeout failure. Adjusted timeout to {self.current_timeout:.1f}s "
                f"(factor: {self.adjustment_factor:.2f})"
            )
    
    def reset(self) -> None:
        """Reset timeout to initial value"""
        self.current_timeout = self.initial_timeout
        self.adjustment_factor = 1.0
        self.failures = 0
        self.successes = 0
        logger.debug("Timeout reset to initial value")
    
    def __float__(self) -> float:
        """Allow use as float in function calls"""
        return self.current_timeout
    
    def __repr__(self) -> str:
        return (
            f"AdaptiveTimeout("
            f"current={self.current_timeout:.1f}s, "
            f"adjustment={self.adjustment_factor:.2f}, "
            f"failures={self.failures})"
        )
