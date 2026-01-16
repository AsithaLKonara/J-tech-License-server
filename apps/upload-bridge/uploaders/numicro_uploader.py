"""
NuMicro Uploader - Nuvoton chip support
Real implementation using Nu-Link CLI
"""

import subprocess
from pathlib import Path
from typing import Optional
import re

from .base import (
    UploaderBase, BuildResult, UploadResult,
    UploadStatus, BuildError, UploadError
)


class NuMicroUploader(UploaderBase):
    """Uploader for Nuvoton NuMicro chips using Nu-Link"""
    
    SUPPORTED_CHIPS = [
        "numicro_m031",
        "numicro_m251",
        "numicro_m451"
    ]
    
    def get_supported_chips(self):
        return self.SUPPORTED_CHIPS
    
    def get_requirements(self):
        return ["nu-link"]  # Nuvoton Nu-Link CLI tool
    
    def build_firmware(self, pattern, build_opts: dict) -> BuildResult:
        """Build NuMicro firmware"""
        self._report_progress(UploadStatus.BUILDING, 0.0, "Starting NuMicro build...")
        
        try:
            template_path = Path(build_opts.get('template_path',
                                                Path(__file__).parent.parent / 'firmware' / 'templates' / self.chip_id))
            output_dir = Path(build_opts.get('output_dir', './build'))
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate pattern header
            pattern_header = self._generate_pattern_header(pattern, build_opts.get('gpio_pin', 0))
            header_path = output_dir / "pattern_data.h"
            
            with open(header_path, 'w', encoding='utf-8') as f:
                f.write(pattern_header)
            
            self._report_progress(UploadStatus.BUILDING, 0.5, "Compiling...")
            
            # Use Makefile if exists
            makefile = template_path / "Makefile"
            if makefile.exists():
                result = subprocess.run(
                    ["make", "-C", str(template_path), f"BUILD_DIR={output_dir}"],
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                
                if result.returncode == 0:
                    bin_file = output_dir / "firmware.bin"
                    if bin_file.exists():
                        return BuildResult(
                            success=True,
                            firmware_path=str(bin_file),
                            binary_type="bin",
                            size_bytes=bin_file.stat().st_size,
                            chip_model=self.chip_id
                        )
            
            raise BuildError("Build failed - check template")
        
        except Exception as e:
            raise BuildError(f"Build error: {str(e)}")
    
    def upload(self, firmware_path: str, port_params: dict) -> UploadResult:
        """Upload using Nu-Link CLI"""
        import time
        start_time = time.time()
        
        try:
            cmd = [
                "nu-link",
                "program",
                firmware_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return UploadResult(
                    success=True,
                    duration_seconds=duration,
                    bytes_written=Path(firmware_path).stat().st_size,
                    verified=True
                )
            else:
                raise UploadError(f"Nu-Link failed: {result.stderr}")
        
        except Exception as e:
            raise UploadError(f"Upload error: {str(e)}")
    
    def _generate_pattern_header(self, pattern, gpio_pin) -> str:
        """Generate pattern header for NuMicro"""
        header = "#ifndef PATTERN_DATA_H\n#define PATTERN_DATA_H\n\n"
        header += "#include <stdint.h>\n\n"
        header += f"#define LED_COUNT {pattern.led_count}\n"
        header += f"#define FRAME_COUNT {pattern.frame_count}\n"
        header += f"#define BRIGHTNESS {int(pattern.metadata.brightness * 255)}\n\n"
        
        size = 4 + sum(2 + len(f.pixels) * 3 for f in pattern.frames)
        header += f"const uint32_t pattern_data_size = {size};\n\n"
        header += "const uint8_t pattern_data[] = {\n"
        
        header += f"    0x{pattern.led_count & 0xFF:02X}, 0x{(pattern.led_count >> 8) & 0xFF:02X},\n"
        header += f"    0x{pattern.frame_count & 0xFF:02X}, 0x{(pattern.frame_count >> 8) & 0xFF:02X},\n"
        
        for i, frame in enumerate(pattern.frames):
            header += f"    0x{frame.duration_ms & 0xFF:02X}, 0x{(frame.duration_ms >> 8) & 0xFF:02X},\n    "
            for r, g, b in frame.pixels:
                header += f"0x{r:02X}, 0x{g:02X}, 0x{b:02X}, "
            header = header.rstrip(", ")
            if i < pattern.frame_count - 1:
                header += ","
            header += "\n"
        
        header += "};\n\n#endif\n"
        return header
    
    def get_bootloader_instructions(self) -> str:
        return "Connect Nu-Link debugger and power the target board"

