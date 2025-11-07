"""
ESP8266/ESP32 Uploader - Clean Version
Handles firmware building and uploading for ESP chips
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

from .base import BaseUploader, UploadStatus, UploadResult, BuildResult, UploadError, BuildError, DeviceInfo


class EspUploader(BaseUploader):
    """ESP8266/ESP32 uploader using esptool.py"""
    
    def __init__(self, chip_id: str):
        super().__init__(chip_id)
        
        # ESP chip settings
        self.chip_settings = {
            "esp8266": {
                "default_baud": 115200,
                "flash_size": "4MB",
                "flash_mode": "dio",
                "flash_freq": "40m"
            },
            "esp32": {
                "default_baud": 921600,
                "flash_size": "4MB",
                "flash_mode": "dio",
                "flash_freq": "80m"
            },
            "esp32s2": {
                "default_baud": 921600,
                "flash_size": "4MB",
                "flash_mode": "dio",
                "flash_freq": "80m"
            },
            "esp32s3": {
                "default_baud": 921600,
                "flash_size": "4MB",
                "flash_mode": "dio",
                "flash_freq": "80m"
            },
            "esp32c3": {
                "default_baud": 921600,
                "flash_size": "4MB",
                "flash_mode": "dio",
                "flash_freq": "80m"
            }
        }
    
    def get_supported_chips(self):
        return ["esp8266", "esp32", "esp32s2", "esp32s3", "esp32c3"]
    
    def get_requirements(self):
        return ["esptool.py", "arduino-cli"]
    
    def get_chip_spec(self):
        from .uploader_registry import UploaderRegistry
        registry = UploaderRegistry.instance()
        spec = registry.get_chip_spec(self.chip_id)
        return spec or super().get_chip_spec()
    
    def build_firmware(self, pattern, build_opts: dict) -> BuildResult:
        """
        Build ESP firmware using universal pattern generator
        """
        self._report_progress(UploadStatus.BUILDING, 0.0, "Starting firmware build...")
        
        try:
            # Get build settings
            output_dir = Path(build_opts.get('output_dir', './build'))
            gpio_pin = build_opts.get('gpio_pin', 2)
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Use universal pattern generator to create firmware
            self._report_progress(UploadStatus.BUILDING, 0.1, "Generating firmware with universal generator...")
            
            from firmware.universal_pattern_generator import generate_universal_firmware
            
            # Generate firmware using universal pattern generator
            firmware_path = generate_universal_firmware(
                pattern=pattern,
                chip_id=self.chip_id,
                output_dir=output_dir,
                config={"gpio_pin": gpio_pin}
            )
            
            self._report_progress(UploadStatus.BUILDING, 0.9, "Build successful!")
            
            # Return success
            return BuildResult(
                success=True,
                firmware_path=firmware_path,
                size_bytes=firmware_path.stat().st_size if firmware_path.exists() else 0,
                build_log="Universal pattern generator completed successfully"
            )
                
        except Exception as e:
            raise BuildError(f"Build error: {str(e)}")
    
    def upload(self, firmware_path: str, port_params: dict) -> UploadResult:
        """Upload firmware to ESP device using esptool.py"""
        self._report_progress(UploadStatus.UPLOADING, 0.0, "Starting upload...")
        
        try:
            port = port_params['port']
            baud = port_params.get('baud', self.chip_settings[self.chip_id]['default_baud'])
            
            # ESP8266/ESP32 specific settings
            settings = self.chip_settings[self.chip_id]
            
            # Build esptool command
            cmd = [
                "esptool.py",
                "--port", port,
                "--baud", str(baud),
                "write_flash",
                "--flash_mode", settings['flash_mode'],
                "--flash_freq", settings['flash_freq'],
                "--flash_size", settings['flash_size'],
                "0x00000", firmware_path
            ]
            
            self._report_progress(UploadStatus.UPLOADING, 0.2, "Flashing firmware...")
            
            # Execute esptool
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=120  # 2 minute timeout
            )
            
            duration = time.time() - time.time()
            
            if result.returncode == 0:
                # Parse bytes written from output
                bytes_written = self._parse_bytes_written(result.stdout)
                
                self._report_progress(UploadStatus.UPLOADING, 1.0, f"Upload complete! {bytes_written} bytes written")
                
                return UploadResult(
                    success=True,
                    bytes_written=bytes_written,
                    duration_seconds=duration,
                    warnings=self._parse_upload_warnings(result.stdout),
                    verified=True  # esptool verifies by default
                )
            else:
                error_msg = self._parse_upload_error(result.stderr or result.stdout)
                raise UploadError(f"Upload failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise UploadError("Upload timeout - device may not be responding")
        except Exception as e:
            raise UploadError(f"Upload error: {str(e)}")
    
    def probe_device(self, port: str) -> Optional[DeviceInfo]:
        """Probe device information using esptool"""
        try:
            cmd = ["esptool.py", "--port", port, "chip_id"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                
                # Parse chip ID from output
                chip_id = None
                if "Chip is ESP8266" in output:
                    chip_id = "esp8266"
                elif "Chip is ESP32" in output:
                    chip_id = "esp32"
                elif "Chip is ESP32-S2" in output:
                    chip_id = "esp32s2"
                elif "Chip is ESP32-S3" in output:
                    chip_id = "esp32s3"
                elif "Chip is ESP32-C3" in output:
                    chip_id = "esp32c3"
                
                if chip_id:
                    return DeviceInfo(
                        chip_id=chip_id,
                        port=port,
                        connected=True,
                        info=output
                    )
            
            return None
            
        except Exception:
            return None
    
    def _parse_bytes_written(self, output: str) -> int:
        """Parse bytes written from esptool output"""
        import re
        
        # Look for "Wrote X bytes" pattern
        match = re.search(r'Wrote (\d+) bytes', output)
        if match:
            return int(match.group(1))
        
        # Look for "Hash of data verified" pattern
        match = re.search(r'Hash of data verified \((\d+) bytes\)', output)
        if match:
            return int(match.group(1))
        
        return 0
    
    def _parse_upload_warnings(self, output: str) -> list:
        """Parse upload warnings from esptool output"""
        warnings = []
        
        if "WARNING" in output:
            lines = output.split('\n')
            for line in lines:
                if "WARNING" in line:
                    warnings.append(line.strip())
        
        return warnings
    
    def _parse_upload_error(self, output: str) -> str:
        """Parse upload error from esptool output"""
        if "A fatal error occurred" in output:
            return "Fatal error during upload"
        elif "Failed to connect" in output:
            return "Failed to connect to device"
        elif "Permission denied" in output:
            return "Permission denied - check if port is in use"
        elif "No such file" in output:
            return "Firmware file not found"
        else:
            return output.strip() or "Unknown upload error"
    
    def get_bootloader_instructions(self) -> str:
        """Get bootloader instructions for this chip"""
        if self.chip_id.startswith("esp32"):
            return "Hold BOOT button, press RESET, release BOOT"
        else:
            return "Hold GPIO0 LOW, press RESET, release GPIO0"
