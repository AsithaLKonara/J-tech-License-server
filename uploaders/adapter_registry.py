"""
UploaderAdapter Registry - Discover and register chip uploaders

Provides adapter discovery and registration system for all chip uploaders.
"""

from typing import Dict, List, Optional, Type
from pathlib import Path

from uploaders.adapter_interface import UploaderAdapter, DeviceInfo


class UploaderAdapterRegistry:
    """
    Registry for uploader adapters.
    
    Manages discovery and registration of all chip uploaders.
    """
    
    _instance: Optional['UploaderAdapterRegistry'] = None
    _adapters: Dict[str, Type[UploaderAdapter]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._adapters = {}
        return cls._instance
    
    def register(self, adapter_class: Type[UploaderAdapter]) -> None:
        """
        Register an uploader adapter.
        
        Args:
            adapter_class: UploaderAdapter class to register
        """
        adapter = adapter_class()
        chip_key = self._get_chip_key(adapter.chip_id, adapter.chip_variant)
        self._adapters[chip_key] = adapter_class
    
    def get_adapter(
        self,
        chip_id: str,
        chip_variant: Optional[str] = None
    ) -> Optional[UploaderAdapter]:
        """
        Get uploader adapter for chip.
        
        Args:
            chip_id: Chip identifier
            chip_variant: Optional chip variant
            
        Returns:
            UploaderAdapter instance or None if not found
        """
        chip_key = self._get_chip_key(chip_id, chip_variant)
        adapter_class = self._adapters.get(chip_key)
        if adapter_class:
            return adapter_class()
        return None
    
    def list_chips(self) -> List[tuple[str, Optional[str]]]:
        """
        List all registered chips.
        
        Returns:
            List of (chip_id, chip_variant) tuples
        """
        chips = []
        for chip_key in self._adapters.keys():
            chip_id, chip_variant = self._parse_chip_key(chip_key)
            chips.append((chip_id, chip_variant))
        return chips
    
    def detect_adapter(self, port: Optional[str] = None) -> Optional[tuple[UploaderAdapter, DeviceInfo]]:
        """
        Auto-detect adapter for connected device.
        
        Args:
            port: Optional serial port
            
        Returns:
            Tuple of (UploaderAdapter, DeviceInfo) if detected, None otherwise
        """
        for adapter_class in self._adapters.values():
            adapter = adapter_class()
            device_info = adapter.detect_device(port)
            if device_info:
                return (adapter, device_info)
        return None
    
    def _get_chip_key(self, chip_id: str, chip_variant: Optional[str] = None) -> str:
        """
        Get registry key for chip.
        
        Args:
            chip_id: Chip identifier
            chip_variant: Optional chip variant
            
        Returns:
            Registry key string
        """
        if chip_variant:
            return f"{chip_id}:{chip_variant}"
        return chip_id
    
    def _parse_chip_key(self, chip_key: str) -> tuple[str, Optional[str]]:
        """
        Parse registry key to chip ID and variant.
        
        Args:
            chip_key: Registry key string
            
        Returns:
            Tuple of (chip_id, chip_variant)
        """
        if ":" in chip_key:
            parts = chip_key.split(":", 1)
            return (parts[0], parts[1])
        return (chip_key, None)


# Global registry instance
_registry = UploaderAdapterRegistry()


def register_adapter(adapter_class: Type[UploaderAdapter]) -> None:
    """
    Register an uploader adapter (convenience function).
    
    Args:
        adapter_class: UploaderAdapter class to register
    """
    _registry.register(adapter_class)


def get_adapter(
    chip_id: str,
    chip_variant: Optional[str] = None
) -> Optional[UploaderAdapter]:
    """
    Get uploader adapter for chip (convenience function).
    
    Args:
        chip_id: Chip identifier (case-insensitive)
        chip_variant: Optional chip variant (case-insensitive)
        
    Returns:
        UploaderAdapter instance or None if not found
    """
    # Try exact match first
    adapter = _registry.get_adapter(chip_id, chip_variant)
    if adapter:
        return adapter
    
    # Try case-insensitive match
    chips = _registry.list_chips()
    for registered_id, registered_variant in chips:
        if chip_id.upper() == registered_id.upper():
            if chip_variant is None and registered_variant is None:
                return _registry.get_adapter(registered_id, None)
            elif chip_variant and registered_variant:
                if chip_variant.upper() == registered_variant.upper():
                    return _registry.get_adapter(registered_id, registered_variant)
    
    return None


def detect_adapter(port: Optional[str] = None) -> Optional[tuple[UploaderAdapter, DeviceInfo]]:
    """
    Auto-detect adapter for connected device (convenience function).
    
    Args:
        port: Optional serial port
        
    Returns:
        Tuple of (UploaderAdapter, DeviceInfo) if detected, None otherwise
    """
    return _registry.detect_adapter(port)


def list_chips() -> List[tuple[str, Optional[str]]]:
    """
    List all registered chips (convenience function).
    
    Returns:
        List of (chip_id, chip_variant) tuples
    """
    return _registry.list_chips()

