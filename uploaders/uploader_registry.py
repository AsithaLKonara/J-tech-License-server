"""
Uploader Registry - Maps chips to uploader implementations
Real implementation with YAML database
"""

import yaml
import os
from typing import Optional, List, Dict
from pathlib import Path
import logging

from .base import UploaderBase


class UploaderRegistry:
    """
    Central registry for chip → uploader mapping
    Singleton pattern for global access
    """
    
    _instance = None
    
    def __init__(self):
        """Initialize registry and load database"""
        self.uploaders: Dict[str, type] = {}
        self.chip_database: Dict[str, dict] = {}
        self._load_chip_database()
        self._register_uploaders()
    
    @classmethod
    def instance(cls) -> 'UploaderRegistry':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_chip_database(self):
        """Load chip specifications from YAML"""
        # Find config directory relative to this file
        current_dir = Path(__file__).parent.parent
        config_file = current_dir / "config" / "chip_database.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Chip database not found: {config_file}\n"
                "Please ensure chip_database.yaml exists in config/ directory"
            )
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        # Extract chips from the YAML structure
        self.chip_database = data.get('chips', {})
        self.uploader_configs = data.get('uploaders', {})
        self.defaults = data.get('defaults', {})
        
        logging.getLogger(__name__).info("Loaded %s chip definitions from database", len(self.chip_database))
    
    def _register_uploaders(self):
        """Register all uploader implementations"""
        # Import uploaders here to avoid circular imports
        try:
            from .avr_uploader import AvrUploader
            self.uploaders['avr_uploader'] = AvrUploader
        except ImportError:
            logging.getLogger(__name__).warning("AvrUploader not available")
        
        try:
            from .esp_uploader import EspUploader
            self.uploaders['esp_uploader'] = EspUploader
        except ImportError:
            logging.getLogger(__name__).warning("EspUploader not available")
        
        try:
            from .stm32_uploader import Stm32Uploader
            self.uploaders['stm32_uploader'] = Stm32Uploader
        except ImportError:
            logging.getLogger(__name__).warning("Stm32Uploader not available")
        
        try:
            from .pic_uploader import PicUploader
            self.uploaders['pic_uploader'] = PicUploader
        except ImportError:
            logging.getLogger(__name__).warning("PicUploader not available")
        
        try:
            from .numicro_uploader import NuMicroUploader
            self.uploaders['numicro_uploader'] = NuMicroUploader
        except ImportError:
            logging.getLogger(__name__).warning("NuMicroUploader not available")
        
        try:
            from .esp01_uploader import ESP01Uploader
            self.uploaders['esp01_uploader'] = ESP01Uploader
        except ImportError:
            logging.getLogger(__name__).warning("ESP01Uploader not available")
        
        logging.getLogger(__name__).info("Registered %s uploader types", len(self.uploaders))
    
    def get_uploader_for_chip(self, chip_id: str) -> Optional[UploaderBase]:
        """
        Get uploader instance for specific chip
        
        Args:
            chip_id: Chip identifier (e.g., "atmega328p", "esp8266")
        
        Returns:
            UploaderBase instance or None if not supported
        """
        chip_spec = self.chip_database.get(chip_id)
        if not chip_spec:
            logging.getLogger(__name__).warning("Chip '%s' not in database", chip_id)
            return None
        
        uploader_class_name = chip_spec.get('uploader')
        if not uploader_class_name:
            logging.getLogger(__name__).warning("No uploader specified for '%s'", chip_id)
            return None
        
        uploader_class = self.uploaders.get(uploader_class_name)
        if not uploader_class:
            logging.getLogger(__name__).warning("Uploader '%s' not registered", uploader_class_name)
            return None
        
        # Create instance
        try:
            return uploader_class(chip_id)
        except Exception as e:
            logging.getLogger(__name__).error("Error creating uploader for '%s': %s", chip_id, e)
            return None
    
    def get_chip_spec(self, chip_id: str) -> Optional[Dict]:
        """
        Get chip specifications
        
        Args:
            chip_id: Chip identifier
        
        Returns:
            Dictionary with chip specs or None
        """
        return self.chip_database.get(chip_id)
    
    def list_supported_chips(self) -> List[str]:
        """
        Get list of all supported chips
        
        Returns:
            List of chip IDs
        """
        return sorted(self.chip_database.keys())
    
    def get_chips_by_family(self, family: str) -> List[str]:
        """
        Get all chips in a family
        
        Args:
            family: Family name ("avr", "esp", "stm32", "pic", "numicro")
        
        Returns:
            List of chip IDs in that family
        """
        return sorted([
            chip_id
            for chip_id, spec in self.chip_database.items()
            if spec.get('family') == family
        ])
    
    def get_all_families(self) -> List[str]:
        """
        Get list of all chip families
        
        Returns:
            List of family names
        """
        families = set(
            spec.get('family', 'unknown')
            for spec in self.chip_database.values()
        )
        return sorted(families)
    
    def search_chips(self, query: str) -> List[str]:
        """
        Search for chips by name
        
        Args:
            query: Search query (case-insensitive)
        
        Returns:
            List of matching chip IDs
        """
        query_lower = query.lower()
        return sorted([
            chip_id
            for chip_id in self.chip_database.keys()
            if query_lower in chip_id.lower()
        ])
    
    def get_required_tools(self, chip_id: str) -> List[str]:
        """
        Get list of required tools for chip
        
        Args:
            chip_id: Chip identifier
        
        Returns:
            List of tool names
        """
        uploader = self.get_uploader_for_chip(chip_id)
        if uploader:
            return uploader.get_requirements()
        return []
    
    def validate_chip_support(self, chip_id: str) -> tuple[bool, List[str]]:
        """
        Validate if chip is fully supported
        
        Args:
            chip_id: Chip identifier
        
        Returns:
            Tuple of (is_supported, missing_components)
        """
        missing = []
        
        # Check if chip exists in database
        if chip_id not in self.chip_database:
            missing.append(f"Chip '{chip_id}' not in database")
            return (False, missing)
        
        spec = self.chip_database[chip_id]
        
        # Check if uploader is registered
        uploader_name = spec.get('uploader')
        if not uploader_name:
            missing.append("No uploader specified")
        elif uploader_name not in self.uploaders:
            missing.append(f"Uploader '{uploader_name}' not registered")
        
        # Try to create instance
        uploader = self.get_uploader_for_chip(chip_id)
        if not uploader:
            missing.append("Cannot create uploader instance")
        else:
            # Check required tools
            available, missing_tools = uploader.check_requirements()
            if not available:
                for tool in missing_tools:
                    missing.append(f"Required tool '{tool}' not found")
        
        return (len(missing) == 0, missing)
    
    def get_chip_info_string(self, chip_id: str) -> str:
        """
        Get formatted chip information string
        
        Args:
            chip_id: Chip identifier
        
        Returns:
            Multi-line formatted string with chip details
        """
        spec = self.get_chip_spec(chip_id)
        if not spec:
            return f"Chip '{chip_id}' not found"
        
        # Handle string sizes from YAML
        flash_size = spec.get('flash_size', '0')
        ram_size = spec.get('ram_size', '0')
        clock_speed = spec.get('clock_speed', 0)
        
        lines = [
            f"Chip: {chip_id}",
            f"Family: {spec.get('family', 'unknown').upper()}",
            f"Flash: {flash_size}",
            f"RAM: {ram_size}",
            f"Clock: {clock_speed // 1000000}MHz" if isinstance(clock_speed, int) and clock_speed > 0 else f"Clock: {clock_speed}",
            f"Programmers: {', '.join(spec.get('programmer_types', []))}",
            f"Bootloader: {spec.get('bootloader_entry', 'See documentation')}",
        ]
        
        if spec.get('notes'):
            lines.append(f"Notes: {spec['notes']}")
        
        return "\n".join(lines)
    
    def export_chip_list(self, filepath: str, format: str = "text"):
        """
        Export chip list to file
        
        Args:
            filepath: Output file path
            format: "text", "csv", or "json"
        """
        if format == "text":
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("Upload Bridge - Supported Chips\n")
                f.write("=" * 60 + "\n\n")
                
                for family in self.get_all_families():
                    chips = self.get_chips_by_family(family)
                    f.write(f"{family.upper()} Family ({len(chips)} chips):\n")
                    for chip_id in chips:
                        spec = self.get_chip_spec(chip_id)
                        flash_kb = spec.get('flash_size', 0) // 1024
                        f.write(f"  - {chip_id:20s} {flash_kb:4d}KB flash\n")
                    f.write("\n")
        
        elif format == "csv":
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Chip ID', 'Family', 'Flash (KB)', 'RAM (KB)', 'Clock (MHz)', 'Notes'])
                
                for chip_id in self.list_supported_chips():
                    spec = self.get_chip_spec(chip_id)
                    flash_size = spec.get('flash_size', '0')
                    ram_size = spec.get('ram_size', '0')
                    clock_speed = spec.get('clock_speed', 0)
                    writer.writerow([
                        chip_id,
                        spec.get('family', ''),
                        flash_size,
                        ram_size,
                        clock_speed // 1000000 if isinstance(clock_speed, int) and clock_speed > 0 else clock_speed,
                        spec.get('notes', '')
                    ])
        
        elif format == "json":
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                data = {
                    "chips": self.chip_database,
                    "families": self.get_all_families(),
                    "count": len(self.chip_database)
                }
                json.dump(data, f, indent=2)


# Convenience function
def get_uploader(chip_id: str) -> Optional[UploaderBase]:
    """
    Quick access to get uploader for chip
    
    Args:
        chip_id: Chip identifier
    
    Returns:
        UploaderBase instance or None
    """
    return UploaderRegistry.instance().get_uploader_for_chip(chip_id)

