"""
Flash Service - Business logic for firmware building and uploading.

This service provides a clean interface for building firmware and uploading
to devices, decoupling the UI layer from hardware-specific logic.
"""

from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import logging
import time

from core.pattern import Pattern
from uploaders.uploader_registry import UploaderRegistry, get_uploader
from uploaders.base import UploaderBase, BuildResult, UploadResult
from core.events import get_event_bus
from core.events.flash_events import (
    FirmwareBuildStartedEvent,
    FirmwareBuildCompletedEvent,
    FirmwareBuildFailedEvent,
    FirmwareUploadStartedEvent,
    FirmwareUploadCompletedEvent,
    FirmwareUploadFailedEvent
)
from core.errors import get_error_handler

logger = logging.getLogger(__name__)

# #region agent log
try:
    from core.debug_logger import debug_log, debug_log_error, debug_log_function_entry, debug_log_function_exit
except Exception:
    debug_log = debug_log_error = debug_log_function_entry = debug_log_function_exit = lambda *args, **kwargs: None
# #endregion


def _get_enterprise_logger():
    """Get enterprise logger for audit and performance logging."""
    try:
        from core.logging import EnterpriseLogger
        return EnterpriseLogger.instance()
    except Exception:
        return None


class FlashService:
    """
    Service for firmware building and uploading operations.
    
    This service encapsulates business logic for building firmware
    and uploading to various microcontroller chips.
    """
    
    def __init__(self):
        """Initialize the flash service."""
        self.registry = UploaderRegistry.instance()
        self.event_bus = get_event_bus()
        self.error_handler = get_error_handler()
    
    def build_firmware(
        self,
        pattern: Pattern,
        chip_id: str,
        chip_variant: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BuildResult:
        """
        Build firmware for a pattern and chip.
        
        Args:
            pattern: The pattern to build firmware for
            chip_id: Chip identifier (e.g., 'esp8266', 'esp32')
            chip_variant: Optional chip variant (not used with current registry)
            config: Optional build configuration
        
        Returns:
            BuildResult with firmware path and metadata
        
        Raises:
            ValueError: If chip is not supported
            RuntimeError: If build fails
        """
        # #region agent log
        try:
            debug_log_function_entry("FlashService.build_firmware", "flash_service.py:53", {
                "chip_id": chip_id,
                "chip_variant": chip_variant,
                "has_config": config is not None,
                "pattern_led_count": pattern.led_count if pattern else None
            }, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        logger.info(f"Building firmware for chip: {chip_id}")
        start_time = time.time()
        
        # Publish build started event
        # #region agent log
        try:
            debug_log("flash_service.py:80", "Publishing build started event", {"chip_id": chip_id}, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        self.event_bus.publish(FirmwareBuildStartedEvent(pattern, chip_id, source="FlashService"))
        
        # Get uploader from registry
        # #region agent log
        try:
            debug_log("flash_service.py:85", "Getting uploader from registry", {"chip_id": chip_id}, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        uploader = get_uploader(chip_id)
        if not uploader:
            # #region agent log
            try:
                debug_log("flash_service.py:88", "Unsupported chip - no uploader found", {"chip_id": chip_id}, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            error = ValueError(f"Unsupported chip: {chip_id}")
            self.error_handler.handle_flash_error(error, chip_id)
            self.event_bus.publish(FirmwareBuildFailedEvent(pattern, chip_id, error, source="FlashService"))
            raise error
        
        # Prepare build options
        build_opts = config or {}
        # #region agent log
        try:
            debug_log("flash_service.py:95", "Before build_firmware call", {"chip_id": chip_id, "has_build_opts": bool(build_opts)}, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        
        # Build firmware
        try:
            result = uploader.build_firmware(pattern, build_opts)
            # #region agent log
            try:
                debug_log("flash_service.py:99", "Firmware build completed", {
                    "chip_id": chip_id,
                    "firmware_path": str(result.firmware_path) if result else None
                }, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            
            # Audit and performance logging
            duration_ms = (time.time() - start_time) * 1000
            enterprise_logger = _get_enterprise_logger()
            if enterprise_logger:
                enterprise_logger.log_audit("firmware_built", details={
                    'chip_id': chip_id,
                    'firmware_path': str(result.firmware_path),
                    'pattern_name': pattern.name,
                    'led_count': pattern.led_count
                })
                enterprise_logger.log_performance("firmware_build", duration_ms, details={
                    'chip_id': chip_id
                })
            
            # Publish build completed event
            self.event_bus.publish(FirmwareBuildCompletedEvent(
                pattern, chip_id, str(result.firmware_path), duration_ms, source="FlashService"
            ))
            
            logger.info(f"Firmware built successfully: {result.firmware_path}")
            # #region agent log
            try:
                debug_log_function_exit("FlashService.build_firmware", "flash_service.py:117", {"success": True, "firmware_path": str(result.firmware_path)}, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            return result
        except Exception as e:
            # #region agent log
            try:
                debug_log_error("flash_service.py:122", e, {"chip_id": chip_id, "build_failed": True}, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            duration_ms = (time.time() - start_time) * 1000
            self.error_handler.handle_flash_error(e, chip_id)
            self.event_bus.publish(FirmwareBuildFailedEvent(pattern, chip_id, e, source="FlashService"))
            logger.error(f"Firmware build failed: {e}", exc_info=True)
            raise RuntimeError(f"Firmware build failed: {str(e)}") from e
    
    def upload_firmware(
        self,
        firmware_path: str,
        chip_id: str,
        chip_variant: Optional[str] = None,
        port: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """
        Upload firmware to a device.
        
        Args:
            firmware_path: Path to firmware binary
            chip_id: Chip identifier
            chip_variant: Optional chip variant (not used with current registry)
            port: Serial port (required)
            config: Optional upload configuration
        
        Returns:
            UploadResult with upload status and metadata
        
        Raises:
            ValueError: If chip is not supported
            RuntimeError: If upload fails
        """
        # #region agent log
        try:
            debug_log_function_entry("FlashService.upload_firmware", "flash_service.py:132", {
                "chip_id": chip_id,
                "port": port,
                "firmware_path": firmware_path,
                "has_config": config is not None
            }, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        logger.info(f"Uploading firmware to chip: {chip_id} on port: {port}")
        start_time = time.time()
        
        # Publish upload started event
        # #region agent log
        try:
            debug_log("flash_service.py:161", "Publishing upload started event", {"chip_id": chip_id, "port": port}, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        self.event_bus.publish(FirmwareUploadStartedEvent(chip_id, firmware_path, port, source="FlashService"))
        
        # Get uploader from registry
        # #region agent log
        try:
            debug_log("flash_service.py:165", "Getting uploader from registry", {"chip_id": chip_id}, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        uploader = get_uploader(chip_id)
        if not uploader:
            # #region agent log
            try:
                debug_log("flash_service.py:168", "Unsupported chip - no uploader found", {"chip_id": chip_id}, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            error = ValueError(f"Unsupported chip: {chip_id}")
            self.error_handler.handle_flash_error(error, chip_id, port)
            self.event_bus.publish(FirmwareUploadFailedEvent(chip_id, firmware_path, port, error, source="FlashService"))
            raise error
        
        # Prepare upload parameters
        port_params = config or {}
        if port:
            port_params['port'] = port
        # #region agent log
        try:
            debug_log("flash_service.py:178", "Before upload call", {"chip_id": chip_id, "port": port, "has_port_params": bool(port_params)}, hypothesis_id="F")
        except Exception:
            pass
        # #endregion
        
        # Upload firmware
        try:
            result = uploader.upload(firmware_path, port_params)
            # #region agent log
            try:
                debug_log("flash_service.py:183", "Upload completed", {
                    "chip_id": chip_id,
                    "port": port,
                    "success": result.success if result else None
                }, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            
            # Audit and performance logging
            duration_ms = (time.time() - start_time) * 1000
            enterprise_logger = _get_enterprise_logger()
            if enterprise_logger:
                enterprise_logger.log_audit("firmware_uploaded", details={
                    'chip_id': chip_id,
                    'port': port,
                    'firmware_path': firmware_path,
                    'success': result.success
                })
                enterprise_logger.log_performance("firmware_upload", duration_ms, details={
                    'chip_id': chip_id,
                    'port': port
                })
            
            # Publish upload completed event
            self.event_bus.publish(FirmwareUploadCompletedEvent(
                chip_id, firmware_path, port, result.success, duration_ms, source="FlashService"
            ))
            
            logger.info(f"Firmware uploaded successfully: {result.success}")
            # #region agent log
            try:
                debug_log_function_exit("FlashService.upload_firmware", "flash_service.py:201", {"success": result.success}, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            return result
        except Exception as e:
            # #region agent log
            try:
                debug_log_error("flash_service.py:205", e, {"chip_id": chip_id, "port": port, "upload_failed": True}, hypothesis_id="F")
            except Exception:
                pass
            # #endregion
            duration_ms = (time.time() - start_time) * 1000
            self.error_handler.handle_flash_error(e, chip_id, port)
            self.event_bus.publish(FirmwareUploadFailedEvent(chip_id, firmware_path, port, e, source="FlashService"))
            logger.error(f"Firmware upload failed: {e}", exc_info=True)
            raise RuntimeError(f"Firmware upload failed: {str(e)}") from e
    
    def verify_upload(
        self,
        chip_id: str,
        chip_variant: Optional[str] = None,
        port: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that firmware was uploaded successfully.
        
        Args:
            chip_id: Chip identifier
            chip_variant: Optional chip variant (not used with current registry)
            port: Serial port
            config: Optional verification configuration
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        logger.info(f"Verifying upload for chip: {chip_id}")
        
        # Get uploader from registry
        uploader = get_uploader(chip_id)
        if not uploader:
            return False, f"Unsupported chip: {chip_id}"
        
        # Check if uploader supports verification
        if not hasattr(uploader, 'verify'):
            return True, None  # Verification not supported, assume success
        
        try:
            # Prepare verification parameters
            verify_params = config or {}
            if port:
                verify_params['port'] = port
            
            # Verify (uploader.verify takes firmware_path and port_params)
            firmware_path = verify_params.get('firmware_path', '')
            verified = uploader.verify(firmware_path, verify_params)
            
            if verified:
                logger.info("Upload verification successful")
                return True, None
            else:
                logger.warning("Upload verification failed")
                return False, "Verification failed"
        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            return False, str(e)
    
    def list_supported_chips(self) -> List[str]:
        """
        Get list of supported chips.
        
        Returns:
            List of chip_id strings
        """
        return self.registry.list_supported_chips()
    
    def is_chip_supported(
        self,
        chip_id: str,
        chip_variant: Optional[str] = None
    ) -> bool:
        """
        Check if a chip is supported.
        
        Args:
            chip_id: Chip identifier
            chip_variant: Optional chip variant (not used with current registry)
        
        Returns:
            True if chip is supported
        """
        uploader = get_uploader(chip_id)
        return uploader is not None

