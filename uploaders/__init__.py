"""
Upload Bridge Uploaders Module
"""

from .base import (
    UploaderBase,
    BuildResult,
    UploadResult,
    DeviceInfo,
    UploadStatus
)
from .uploader_registry import UploaderRegistry

# Import adapter interface and registry
try:
    from .adapter_interface import UploaderAdapter
    from .adapter_registry import UploaderAdapterRegistry, get_adapter, detect_adapter
    from .types import FlashResult, VerifyResult
    
    # Auto-register all adapters on import
    try:
        from . import adapter_init  # noqa: F401
    except ImportError:
        # Some adapters might not be available in all environments
        pass
except ImportError:
    # Adapter system might not be available in older versions
    UploaderAdapter = None
    UploaderAdapterRegistry = None
    get_adapter = None
    detect_adapter = None
    FlashResult = None
    VerifyResult = None

__all__ = [
    'UploaderBase',
    'BuildResult',
    'UploadResult',
    'DeviceInfo',
    'UploadStatus',
    'UploaderRegistry'
]

# Add adapter exports if available
if UploaderAdapter is not None:
    __all__.extend([
        'UploaderAdapter',
        'UploaderAdapterRegistry',
        'get_adapter',
        'detect_adapter',
        'FlashResult',
        'VerifyResult',
    ])

