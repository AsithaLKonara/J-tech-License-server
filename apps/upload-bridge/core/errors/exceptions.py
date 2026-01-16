"""
Custom exception classes for the application.

Provides domain-specific exceptions that provide better error context
than generic Python exceptions.
"""


class PatternError(Exception):
    """Base exception for pattern-related errors."""
    pass


class PatternLoadError(PatternError):
    """Exception raised when pattern loading fails."""
    
    def __init__(self, message: str, file_path: str = None, original_error: Exception = None):
        """
        Initialize pattern load error.
        
        Args:
            message: Error message
            file_path: Optional file path that failed to load
            original_error: Optional original exception
        """
        super().__init__(message)
        self.file_path = file_path
        self.original_error = original_error


class PatternSaveError(PatternError):
    """Exception raised when pattern saving fails."""
    
    def __init__(self, message: str, file_path: str = None, original_error: Exception = None):
        """
        Initialize pattern save error.
        
        Args:
            message: Error message
            file_path: Optional file path that failed to save
            original_error: Optional original exception
        """
        super().__init__(message)
        self.file_path = file_path
        self.original_error = original_error


class PatternValidationError(PatternError):
    """Exception raised when pattern validation fails."""
    
    def __init__(self, message: str, validation_errors: list = None):
        """
        Initialize pattern validation error.
        
        Args:
            message: Error message
            validation_errors: Optional list of specific validation errors
        """
        super().__init__(message)
        self.validation_errors = validation_errors or []


class ExportError(Exception):
    """Base exception for export-related errors."""
    pass


class ExportValidationError(ExportError):
    """Exception raised when export validation fails."""
    
    def __init__(self, message: str, format: str = None, validation_errors: list = None):
        """
        Initialize export validation error.
        
        Args:
            message: Error message
            format: Optional export format that failed validation
            validation_errors: Optional list of specific validation errors
        """
        super().__init__(message)
        self.format = format
        self.validation_errors = validation_errors or []


class FlashError(Exception):
    """Base exception for flash-related errors."""
    pass


class FlashBuildError(FlashError):
    """Exception raised when firmware build fails."""
    
    def __init__(self, message: str, chip_id: str = None, original_error: Exception = None):
        """
        Initialize flash build error.
        
        Args:
            message: Error message
            chip_id: Optional chip ID that failed to build
            original_error: Optional original exception
        """
        super().__init__(message)
        self.chip_id = chip_id
        self.original_error = original_error


class FlashUploadError(FlashError):
    """Exception raised when firmware upload fails."""
    
    def __init__(self, message: str, chip_id: str = None, port: str = None, original_error: Exception = None):
        """
        Initialize flash upload error.
        
        Args:
            message: Error message
            chip_id: Optional chip ID that failed to upload
            port: Optional serial port
            original_error: Optional original exception
        """
        super().__init__(message)
        self.chip_id = chip_id
        self.port = port
        self.original_error = original_error


class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass

