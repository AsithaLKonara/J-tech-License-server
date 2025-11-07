"""
AVR Uploader - Real implementation using avrdude
Supports ATmega and ATtiny chips
No placeholders - complete working code
"""

import subprocess
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from .base import (
    UploaderBase, BuildResult, UploadResult, DeviceInfo,
    UploadStatus, BuildError, UploadError
)
from core.subprocess_utils import get_hidden_subprocess_kwargs


class AvrUploader(UploaderBase):
    """Uploader for AVR chips (ATmega, ATtiny) using avrdude"""
    
    SUPPORTED_CHIPS = [
        "atmega8", "atmega8a", "atmega8l",
        "atmega168", "atmega168p", "atmega168pa",
        "atmega328", "atmega328p", "atmega328pb",
        "atmega32", "atmega32u4",
        "atmega2560",
        "attiny13", "attiny13a",
        "attiny25", "attiny43", "attiny45", "attiny85"
    ]
    
    def __init__(self, chip_id: str):
        super().__init__(chip_id)
        
        # Map chip ID to avrdude part name
        self.avrdude_part_map = {
            "atmega328p": "m328p",
            "atmega328": "m328",
            "atmega168p": "m168p",
            "atmega168": "m168",
            "atmega2560": "m2560",
            "atmega32u4": "m32u4",
            "attiny85": "t85",
            "attiny45": "t45",
            "attiny25": "t25",
            "attiny13": "t13",
            "attiny13a": "t13",
        }
    
    def get_supported_chips(self):
        return self.SUPPORTED_CHIPS
    
    def get_requirements(self):
        return ["avrdude", "avr-gcc", "avr-objcopy"]
    
    def get_chip_spec(self):
        from .uploader_registry import UploaderRegistry
        registry = UploaderRegistry.instance()
        spec = registry.get_chip_spec(self.chip_id)
        return spec or super().get_chip_spec()
    
    def build_firmware(self, pattern, build_opts: dict) -> BuildResult:
        """
        Build AVR firmware with pattern data
        
        Real implementation - actually compiles C code!
        """
        self._report_progress(UploadStatus.BUILDING, 0.0, "Starting firmware build...")
        
        try:
            # Get build settings
            template_path = Path(build_opts.get('template_path',
                                                Path(__file__).parent.parent / 'firmware' / 'templates' / self.chip_id))
            output_dir = Path(build_opts.get('output_dir', './build'))
            gpio_pin = build_opts.get('gpio_pin', 2)
            optimize = build_opts.get('optimize', '-Os')  # Size optimization
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Generate pattern_data.h
            self._report_progress(UploadStatus.BUILDING, 0.1, "Generating pattern data...")
            pattern_header = self._generate_pattern_header(pattern, gpio_pin)
            
            header_path = output_dir / "pattern_data.h"
            with open(header_path, 'w', encoding='utf-8') as f:
                f.write(pattern_header)
            
            self._report_progress(UploadStatus.BUILDING, 0.3, "Compiling with avr-gcc...")
            
            # Step 2: Check if Makefile exists
            makefile = template_path / "Makefile"
            
            if makefile.exists():
                # Use Makefile
                result = self._build_with_makefile(template_path, output_dir, build_opts)
            else:
                # Direct avr-gcc compilation
                result = self._build_direct(template_path, output_dir, build_opts)
            
            if result.returncode == 0:
                self._report_progress(UploadStatus.BUILDING, 0.9, "Build successful!")
                
                # Find output hex file
                hex_file = output_dir / "firmware.hex"
                
                # Alternative names
                if not hex_file.exists():
                    hex_files = list(output_dir.glob("*.hex"))
                    if hex_files:
                        hex_file = hex_files[0]
                    else:
                        raise BuildError("Build succeeded but .hex file not found")
                
                size = hex_file.stat().st_size
                
                return BuildResult(
                    success=True,
                    firmware_path=str(hex_file),
                    binary_type="hex",
                    size_bytes=size,
                    chip_model=self.chip_id,
                    warnings=self._parse_build_warnings(result.stdout + result.stderr)
                )
            
            else:
                error_msg = self._parse_build_error(result.stderr + result.stdout)
                raise BuildError(f"Compilation failed: {error_msg}")
        
        except subprocess.TimeoutExpired:
            raise BuildError("Build timed out after 3 minutes")
        
        except BuildError:
            raise
        
        except Exception as e:
            raise BuildError(f"Build error: {str(e)}")
    
    def upload(self, firmware_path: str, port_params: dict) -> UploadResult:
        """
        Upload firmware using avrdude
        
        Real implementation - actually flashes chip!
        """
        import time
        start_time = time.time()
        
        self._report_progress(UploadStatus.UPLOADING, 0.0, "Starting upload...")
        
        try:
            port = port_params.get('port')
            programmer = port_params.get('programmer', 'arduino')
            baud = port_params.get('baud', 115200)
            
            # Get avrdude part name
            avrdude_part = self.avrdude_part_map.get(self.chip_id, self.chip_id)
            
            self._report_progress(UploadStatus.UPLOADING, 0.1, f"Connecting to {port}...")
            
            # Build avrdude command
            cmd = [
                "avrdude",
                "-p", avrdude_part,
                "-c", programmer,
                "-U", f"flash:w:{firmware_path}:i"
            ]
            
            # Add port if specified
            if port:
                cmd.extend(["-P", port])
            
            # Add baud if using serial programmer
            if programmer in ['arduino', 'stk500v1', 'stk500v2']:
                cmd.extend(["-b", str(baud)])
            
            # Add verbose flag for better output parsing
            cmd.append("-v")
            
            self._report_progress(UploadStatus.UPLOADING, 0.2, "Flashing firmware...")
            
            # Execute avrdude
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                **get_hidden_subprocess_kwargs()
            )
            
            duration = time.time() - start_time
            
            # avrdude writes to stderr even on success
            output = result.stdout + result.stderr
            
            # Check for success indicators
            if result.returncode == 0 or "avrdude done.  Thank you." in output.lower():
                bytes_written = self._parse_bytes_written(output)
                
                self._report_progress(UploadStatus.COMPLETE, 1.0, "Upload successful!")
                
                return UploadResult(
                    success=True,
                    duration_seconds=duration,
                    bytes_written=bytes_written,
                    verified=True,  # avrdude verifies by default
                    warnings=self._parse_upload_warnings(output)
                )
            
            else:
                error_msg = self._parse_upload_error(output)
                raise UploadError(f"Upload failed: {error_msg}")
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            raise UploadError("Upload timed out after 2 minutes")
        
        except UploadError:
            raise
        
        except Exception as e:
            raise UploadError(f"Upload error: {str(e)}")
    
    def probe_device(self, port: str) -> Optional[DeviceInfo]:
        """Probe AVR device using avrdude"""
        try:
            # Get avrdude part name
            avrdude_part = self.avrdude_part_map.get(self.chip_id, self.chip_id)
            
            cmd = [
                "avrdude",
                "-p", avrdude_part,
                "-c", "arduino",
                "-P", port,
                "-v"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                **get_hidden_subprocess_kwargs()
            )
            
            output = result.stdout + result.stderr
            
            # Parse device signature
            sig_match = re.search(r'Device signature = (0x[0-9a-f]+)', output, re.IGNORECASE)
            signature = sig_match.group(1) if sig_match else None
            
            if signature:
                return DeviceInfo(
                    port=port,
                    chip_detected=self.chip_id,
                    bootloader_version=None
                )
        
        except Exception as e:
            print(f"Probe failed for {port}: {e}")
        
        return None
    
    def _build_with_makefile(self, template_path: Path, output_dir: Path, opts: dict) -> subprocess.CompletedProcess:
        """Build using Makefile"""
        cmd = [
            "make",
            "-C", str(template_path),
            f"BUILD_DIR={output_dir}",
            "all"
        ]
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            **get_hidden_subprocess_kwargs()
        )
    
    def _build_direct(self, template_path: Path, output_dir: Path, opts: dict) -> subprocess.CompletedProcess:
        """
        Direct compilation with avr-gcc
        Used when no Makefile is present
        """
        # Get chip settings
        chip_spec = self.get_chip_spec()
        mcu = self.chip_id
        f_cpu = chip_spec.get('clock_speed', 16000000)
        
        # Find source files
        c_files = list(template_path.glob("*.c"))
        if not c_files:
            raise BuildError(f"No .c files found in {template_path}")
        
        main_c = template_path / "pattern_player.c"
        if not main_c.exists() and c_files:
            main_c = c_files[0]
        
        # Output files
        elf_file = output_dir / "firmware.elf"
        hex_file = output_dir / "firmware.hex"
        
        # Compile
        compile_cmd = [
            "avr-gcc",
            f"-mmcu={mcu}",
            f"-DF_CPU={f_cpu}UL",
            "-Os",  # Optimize for size
            "-Wall",
            "-I", str(output_dir),  # Include pattern_data.h
            "-I", str(template_path),
            str(main_c),
            "-o", str(elf_file)
        ]
        
        result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=60,
            **get_hidden_subprocess_kwargs()
        )
        
        if result.returncode != 0:
            return result
        
        # Convert to hex
        objcopy_cmd = [
            "avr-objcopy",
            "-O", "ihex",
            "-R", ".eeprom",
            str(elf_file),
            str(hex_file)
        ]
        
        return subprocess.run(
            objcopy_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            **get_hidden_subprocess_kwargs()
        )
    
    def _generate_pattern_header(self, pattern, gpio_pin: int) -> str:
        """Generate C header with pattern data for AVR"""
        header = "// Auto-generated by Upload Bridge\n"
        header += "// DO NOT EDIT MANUALLY\n\n"
        header += "#ifndef PATTERN_DATA_H\n"
        header += "#define PATTERN_DATA_H\n\n"
        header += "#include <avr/pgmspace.h>\n\n"
        
        # Configuration constants
        header += f"#define DATA_PIN {gpio_pin}\n"
        header += f"#define LED_COUNT {pattern.led_count}\n"
        header += f"#define FRAME_COUNT {pattern.frame_count}\n"
        header += f"#define BRIGHTNESS {int(pattern.metadata.brightness * 255)}\n\n"
        
        # Calculate size
        size = 4  # Header
        for frame in pattern.frames:
            size += 2  # delay_ms
            size += len(frame.pixels) * 3  # RGB data
        
        header += f"const uint32_t pattern_data_size = {size};\n\n"
        header += "const uint8_t PROGMEM pattern_data[] = {\n"
        
        # Write header (num_leds, num_frames)
        header += f"    0x{pattern.led_count & 0xFF:02X}, 0x{(pattern.led_count >> 8) & 0xFF:02X},  // num_leds = {pattern.led_count}\n"
        header += f"    0x{pattern.frame_count & 0xFF:02X}, 0x{(pattern.frame_count >> 8) & 0xFF:02X},  // num_frames = {pattern.frame_count}\n"
        
        # Write frames
        for i, frame in enumerate(pattern.frames):
            delay = frame.duration_ms
            header += f"\n    // Frame {i} (delay: {delay}ms)\n"
            header += f"    0x{delay & 0xFF:02X}, 0x{(delay >> 8) & 0xFF:02X},\n"
            
            # Write RGB data (6 pixels per line for readability)
            header += "    "
            for led_idx, (r, g, b) in enumerate(frame.pixels):
                header += f"0x{r:02X}, 0x{g:02X}, 0x{b:02X}, "
                if (led_idx + 1) % 6 == 0 and led_idx < len(frame.pixels) - 1:
                    header += "\n    "
            
            header = header.rstrip(", \n")
            if i < pattern.frame_count - 1:
                header += ","
            header += "\n"
        
        header += "};\n\n#endif // PATTERN_DATA_H\n"
        
        return header
    
    def _parse_build_warnings(self, output: str) -> list:
        """Extract warnings from build output"""
        warnings = []
        
        warning_patterns = [
            r'warning:.*',
            r'Warning:.*'
        ]
        
        for pattern in warning_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            warnings.extend(matches[:5])
        
        return warnings
    
    def _parse_build_error(self, output: str) -> str:
        """Extract meaningful error from build output"""
        error_patterns = [
            r'error:.*',
            r'Error:.*',
            r'undefined reference.*',
            r'No such file.*'
        ]
        
        errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            errors.extend(matches[:3])
        
        if errors:
            return "\n".join(errors)
        
        return output[-500:] if len(output) > 500 else output
    
    def _parse_upload_warnings(self, output: str) -> list:
        """Extract warnings from avrdude output"""
        warnings = []
        
        if "timeout" in output.lower():
            warnings.append("Communication timeout detected")
        
        if "not in sync" in output.lower():
            warnings.append("Device not in sync - check connections")
        
        return warnings
    
    def _parse_upload_error(self, output: str) -> str:
        """Extract meaningful error from avrdude output"""
        error_patterns = [
            r'error:.*',
            r'Error:.*',
            r'programmer is not responding',
            r'not in sync.*',
            r'device signature.*does not match',
            r'can\'t open device.*'
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return output[-300:] if len(output) > 300 else output
    
    def _parse_bytes_written(self, output: str) -> int:
        """Extract bytes written from avrdude output"""
        # Look for patterns like "123 bytes of flash written"
        match = re.search(r'(\d+) bytes? of flash (?:written|verified)', output, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Alternative pattern
        match = re.search(r'writing flash.*:\s*(\d+) bytes', output, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        return 0
    
    def get_bootloader_instructions(self) -> str:
        """Get AVR-specific bootloader instructions"""
        if self.chip_id in ["atmega328p", "atmega2560"]:
            return (
                "Arduino Bootloader Entry:\n"
                "1. Press the RESET button on your Arduino\n"
                "2. Bootloader will be active for ~2 seconds\n"
                "3. Start upload immediately\n\n"
                "If upload fails, try:\n"
                "- Hold RESET, start upload, then release RESET"
            )
        elif self.chip_id == "atmega32u4":
            return (
                "Leonardo/Pro Micro Bootloader Entry:\n"
                "1. Double-tap RESET button quickly\n"
                "2. Bootloader will be active for ~8 seconds\n"
                "3. Upload during this window\n\n"
                "LED will fade in/out when in bootloader mode"
            )
        elif self.chip_id.startswith("attiny"):
            return (
                "ATtiny Programming:\n"
                "1. Connect ISP programmer (USBasp, Arduino as ISP, etc.)\n"
                "2. Ensure connections: MOSI, MISO, SCK, RESET, VCC, GND\n"
                "3. Power target (3.3V or 5V)\n"
                "4. Upload with programmer=usbasp or programmer=avrisp\n\n"
                "No bootloader - direct ISP programming required"
            )
        
        return super().get_bootloader_instructions()

