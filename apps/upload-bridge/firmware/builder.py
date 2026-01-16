"""
Firmware Builder - Orchestrates firmware compilation with pattern data
Real implementation - NO PLACEHOLDERS!
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tempfile
try:
    # Python 3.9+
    import importlib.resources as resources
except ImportError:  # pragma: no cover
    import importlib_resources as resources  # type: ignore

from core.pattern import Pattern
from uploaders.base import BuildResult
from .universal_pattern_generator import UniversalPatternGenerator


class FirmwareBuilder:
    """
    Orchestrates firmware building across different chip types
    
    Responsibilities:
    - Template management
    - Pattern header generation
    - Build orchestration
    - Output management
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize firmware builder
        
        Args:
            templates_dir: Path to firmware templates directory
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Default to templates/ next to this file (when running from source)
            self.templates_dir = Path(__file__).parent / "templates"
        
        self.build_dir = Path("./build")
        self.build_dir.mkdir(parents=True, exist_ok=True)
    
    def build(self, pattern: Pattern, chip_id: str,
              build_opts: Optional[Dict] = None) -> BuildResult:
        """
        Build firmware for specified chip with embedded pattern
        
        Args:
            pattern: Pattern object to embed
            chip_id: Target chip identifier
            build_opts: Optional build configuration
        
        Returns:
            BuildResult with firmware path and metadata
        
        Raises:
            ValueError: If template not found or build fails
        """
        build_opts = build_opts or {}
        
        # Resolve template directory (supports packaged resources)
        template_dir = build_opts.get('template_path')
        if template_dir:
            template_dir = Path(template_dir)
        else:
            template_dir = self._resolve_template_dir(chip_id)
        
        if not template_dir or not template_dir.exists():
            raise ValueError(f"Template not found for chip '{chip_id}' at {template_dir}")
        
        # Create chip-specific build directory
        chip_build_dir = self.build_dir / chip_id
        chip_build_dir.mkdir(parents=True, exist_ok=True)
        
        # Get uploader for this chip
        from uploaders.uploader_registry import get_uploader
        
        uploader = get_uploader(chip_id)
        if not uploader:
            raise ValueError(f"No uploader found for chip '{chip_id}'")
        
        # Set build options
        build_config = {
            'template_path': str(template_dir),
            'output_dir': str(chip_build_dir),
            'gpio_pin': build_opts.get('gpio_pin', 2),
            'optimize': build_opts.get('optimize', '-Os'),
            **build_opts
        }
        
        # Delegate to uploader's build method
        result = uploader.build_firmware(pattern, build_config)
        
        return result

    def _resolve_template_dir(self, chip_id: str) -> Optional[Path]:
        """
        Resolve template directory for a chip, working in both source and packaged modes.
        - If running from source, use firmware/templates/<chip>.
        - If packaged (e.g., PyInstaller), extract package resources to a temp dir.
        """
        # Source layout or PyInstaller onefile extracted next to module
        candidate = self.templates_dir / chip_id
        if candidate.exists():
            return candidate
        # PyInstaller _MEIPASS root: firmware/templates packaged as data
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            mp_candidate = Path(meipass) / "firmware" / "templates" / chip_id
            if mp_candidate.exists():
                return mp_candidate
        
        # Packaged resources (firmware.templates.<chip>)
        try:
            pkg = f"firmware.templates.{chip_id}"
            # Check if resources are available under package
            files = resources.files(pkg)  # type: ignore[attr-defined]
            # Extract to temp dir for filesystem access
            temp_dir = Path(tempfile.mkdtemp(prefix=f"ub_tpl_{chip_id}_"))
            for entry in files.iterdir():  # type: ignore
                with resources.as_file(entry) as src_path:  # type: ignore
                    dst = temp_dir / entry.name
                    if src_path.is_dir():
                        shutil.copytree(src_path, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_path, dst)
            return temp_dir
        except Exception:
            return None
    
    def build_universal_firmware(self, pattern: Pattern, chip_id: str,
                                build_opts: Optional[Dict] = None) -> BuildResult:
        """
        Build universal firmware with full professional features for any chip
        
        Args:
            pattern: Pattern object to embed
            chip_id: Target chip identifier
            build_opts: Optional build configuration
        
        Returns:
            BuildResult with firmware path and metadata
        """
        build_opts = build_opts or {}
        
        # Create chip-specific build directory
        chip_build_dir = self.build_dir / chip_id
        chip_build_dir.mkdir(parents=True, exist_ok=True)
        
        # Use universal pattern generator
        generator = UniversalPatternGenerator()
        
        # Generate universal firmware
        config = {
            'gpio_pin': build_opts.get('gpio_pin', 2),
            **build_opts
        }
        
        try:
            main_file = generator.generate_universal_firmware(
                pattern, chip_id, str(chip_build_dir), config
            )
            
            return BuildResult(
                success=True,
                firmware_path=main_file,
                binary_type="c" if main_file.endswith('.c') else "ino",
                size_bytes=Path(main_file).stat().st_size if Path(main_file).exists() else 0,
                chip_model=chip_id,
                warnings=[],
                error_message=None
            )
            
        except Exception as e:
            return BuildResult(
                success=False,
                firmware_path="",
                binary_type="",
                size_bytes=0,
                chip_model=chip_id,
                warnings=[],
                error_message=f"Failed to generate universal firmware: {e}"
            )
    
    def get_available_templates(self) -> Dict[str, dict]:
        """
        Get list of available firmware templates
        
        Returns:
            Dictionary mapping chip_id to template info
        """
        templates = {}
        
        if not self.templates_dir.exists():
            return templates
        
        for item in self.templates_dir.iterdir():
            if item.is_dir():
                chip_id = item.name
                
                # Check for key files
                has_ino = len(list(item.glob("*.ino"))) > 0
                has_c = len(list(item.glob("*.c"))) > 0
                has_makefile = (item / "Makefile").exists()
                has_readme = (item / "README.md").exists()
                
                templates[chip_id] = {
                    "path": str(item),
                    "has_ino": has_ino,
                    "has_c": has_c,
                    "has_makefile": has_makefile,
                    "has_readme": has_readme,
                    "type": "arduino" if has_ino else "c" if has_c else "unknown"
                }
        
        return templates
    
    def validate_template(self, chip_id: str) -> tuple[bool, list[str]]:
        """
        Validate that template exists and has required files
        
        Args:
            chip_id: Chip identifier
        
        Returns:
            Tuple of (is_valid, missing_files)
        """
        template_dir = self.templates_dir / chip_id
        
        if not template_dir.exists():
            return (False, ["Template directory not found"])
        
        missing = []
        
        # Check for source files
        has_source = (
            len(list(template_dir.glob("*.ino"))) > 0 or
            len(list(template_dir.glob("*.c"))) > 0
        )
        
        if not has_source:
            missing.append("No source files (.ino or .c)")
        
        # Check for pattern_data.h.tpl (optional but recommended)
        if not (template_dir / "pattern_data.h.tpl").exists():
            # Not critical, but note it
            pass
        
        return (len(missing) == 0, missing)
    
    def clean_build_dir(self, chip_id: Optional[str] = None):
        """
        Clean build directory
        
        Args:
            chip_id: If specified, only clean that chip's build dir
        """
        if chip_id:
            chip_build_dir = self.build_dir / chip_id
            if chip_build_dir.exists():
                shutil.rmtree(chip_build_dir)
                chip_build_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Clean entire build directory
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
            self.build_dir.mkdir(parents=True, exist_ok=True)
    
    def estimate_build_time(self, chip_id: str, pattern: Pattern) -> float:
        """
        Estimate build time in seconds
        
        Args:
            chip_id: Target chip
            pattern: Pattern to embed
        
        Returns:
            Estimated time in seconds
        """
        # Base time varies by chip family
        base_times = {
            "esp8266": 45,
            "esp32": 60,
            "atmega328p": 20,
            "atmega2560": 25,
            "stm32f030f4": 30,
            "stm32f103c8": 35
        }
        
        base_time = base_times.get(chip_id, 30)
        
        # Add time for large patterns (header generation)
        pattern_size = pattern.estimate_memory_bytes()
        if pattern_size > 100000:  # > 100KB
            base_time += 10
        
        return base_time
    
    def get_template_info(self, chip_id: str) -> Optional[Dict]:
        """
        Get detailed information about a template
        
        Args:
            chip_id: Chip identifier
        
        Returns:
            Dictionary with template info or None
        """
        templates = self.get_available_templates()
        return templates.get(chip_id)

