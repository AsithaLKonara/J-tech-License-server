"""
ESP8266/ESP32 Uploader - Clean Version
Handles firmware building and uploading for ESP chips
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

from .base import UploaderBase, UploadStatus, UploadResult, BuildResult, UploadError, BuildError, DeviceInfo
from core.subprocess_utils import get_hidden_subprocess_kwargs

# #region agent log
try:
    from core.debug_logger import debug_log, debug_log_error, debug_log_function_entry, debug_log_function_exit
except Exception:
    debug_log = debug_log_error = debug_log_function_entry = debug_log_function_exit = lambda *args, **kwargs: None
# #endregion


class EspUploader(UploaderBase):
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
        return ["python -m esptool", "arduino-cli"]
    
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
            gpio_pin = build_opts.get('gpio_pin', 3)
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Use simple firmware generator to create firmware source
            self._report_progress(UploadStatus.BUILDING, 0.1, "Generating firmware source...")
            
            from firmware.simple_firmware_generator import generate_simple_firmware

            # Generate firmware source using simple firmware generator (compatible with old format)
            source_path = generate_simple_firmware(
                pattern=pattern,
                chip_id=self.chip_id,
                output_dir=output_dir,
                config={"gpio_pin": gpio_pin}
            )
            
            # Step 2: The universal pattern generator already creates the file with the correct name
            self._report_progress(UploadStatus.BUILDING, 0.2, "Preparing sketch for compilation...")
            
            target_ino = Path(source_path)
            
            # Step 3: Compile the .ino file to .bin using Arduino CLI
            self._report_progress(UploadStatus.BUILDING, 0.3, "Compiling with Arduino CLI...")
            
            # Determine FQBN (Fully Qualified Board Name)
            fqbn_map = {
                "esp8266": "esp8266:esp8266:nodemcuv2",
                "esp32": "esp32:esp32:esp32",
                "esp32s2": "esp32:esp32:esp32s2",
                "esp32s3": "esp32:esp32:esp32s3",
                "esp32c3": "esp32:esp32:esp32c3"
            }
            fqbn = fqbn_map.get(self.chip_id, fqbn_map["esp8266"])
            
            # Create a separate build directory for Arduino CLI
            build_dir = output_dir / "arduino_build"
            build_dir.mkdir(exist_ok=True)
            
            # Compile using Arduino CLI
            cmd = [
                "arduino-cli", "compile",
                "--fqbn", fqbn,
                "--build-path", str(build_dir),
                "--output-dir", str(output_dir),
                str(target_ino)
            ]
            
            self._report_progress(UploadStatus.BUILDING, 0.5, "Invoking compiler...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=180,  # 3 minute timeout
                **get_hidden_subprocess_kwargs()
            )
            
            if result.returncode == 0:
                self._report_progress(UploadStatus.BUILDING, 0.9, "Compilation successful!")
                
                # Find the generated binary file
                binary_files = list(output_dir.glob("*.bin"))
                if binary_files:
                    firmware_path = binary_files[0]
                else:
                    # Look for .ino.bin files
                    ino_bin_files = list(output_dir.glob("*.ino.bin"))
                    if ino_bin_files:
                        firmware_path = ino_bin_files[0]
                    else:
                        raise BuildError(f"Compilation succeeded but no .bin file found in {output_dir}")
                
                # Check file size
                firmware_path_obj = Path(firmware_path)
                size_bytes = firmware_path_obj.stat().st_size
                if size_bytes == 0:
                    raise BuildError("Compilation succeeded but binary file is empty")
                
                self._report_progress(UploadStatus.BUILDING, 1.0, f"Build complete! Size: {size_bytes} bytes")
                
                return BuildResult(
                    success=True,
                    firmware_path=str(firmware_path),
                    binary_type="bin",
                    size_bytes=size_bytes,
                    chip_model=self.chip_id,
                    warnings=[]
                )
            else:
                # Compilation failed
                error_msg = result.stderr or result.stdout or "Unknown compilation error"
                raise BuildError(f"Compilation failed: {error_msg}")
                
        except Exception as e:
            raise BuildError(f"Build error: {str(e)}")
    
    def upload(self, firmware_path: str, port_params: dict) -> UploadResult:
        """Upload firmware to ESP device using esptool.py"""
        # #region agent log
        try:
            debug_log_function_entry("EspUploader.upload", "esp_uploader.py:176", {
                "chip_id": self.chip_id,
                "firmware_path": firmware_path,
                "port": port_params.get('port')
            }, hypothesis_id="G")
        except Exception:
            pass
        # #endregion
        self._report_progress(UploadStatus.UPLOADING, 0.0, "Starting upload...")

        try:
            port = port_params['port']
            baud = port_params.get('baud', self.chip_settings[self.chip_id]['default_baud'])
            # #region agent log
            try:
                debug_log("esp_uploader.py:184", "Port and baud resolved", {"port": port, "baud": baud, "chip_id": self.chip_id}, hypothesis_id="G")
            except Exception:
                pass
            # #endregion

            # ESP8266/ESP32 specific settings
            settings = self.chip_settings[self.chip_id]

            # Build esptool command
            cmd = [
                "python", "-m", "esptool",
                "--port", port,
                "--baud", str(baud),
                "write_flash",
                "--flash_mode", settings['flash_mode'],
                "--flash_freq", settings['flash_freq'],
                "--flash_size", settings['flash_size'],
                "0x00000", firmware_path
            ]
            # #region agent log
            try:
                debug_log("esp_uploader.py:199", "esptool command built", {"cmd": ' '.join(cmd[:5])}, hypothesis_id="G")
            except Exception:
                pass
            # #endregion

            self._report_progress(UploadStatus.UPLOADING, 0.2, "Flashing firmware...")

            # Execute esptool
            # #region agent log
            try:
                debug_log("esp_uploader.py:204", "Before subprocess.run", {"timeout": 120}, hypothesis_id="G")
            except Exception:
                pass
            # #endregion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=120,  # 2 minute timeout
                **get_hidden_subprocess_kwargs()
            )
            # #region agent log
            try:
                debug_log("esp_uploader.py:214", "subprocess.run completed", {"returncode": result.returncode}, hypothesis_id="G")
            except Exception:
                pass
            # #endregion

            duration = time.time() - time.time()

            if result.returncode == 0:
                # Parse bytes written from output
                bytes_written = self._parse_bytes_written(result.stdout)
                # #region agent log
                try:
                    debug_log("esp_uploader.py:220", "Upload successful", {"bytes_written": bytes_written}, hypothesis_id="G")
                except Exception:
                    pass
                # #endregion

                self._report_progress(UploadStatus.UPLOADING, 1.0, f"Upload complete! {bytes_written} bytes written")

                # #region agent log
                try:
                    debug_log_function_exit("EspUploader.upload", "esp_uploader.py:226", {"success": True}, hypothesis_id="G")
                except Exception:
                    pass
                # #endregion
                return UploadResult(
                    success=True,
                    bytes_written=bytes_written,
                    duration_seconds=duration,
                    warnings=self._parse_upload_warnings(result.stdout),
                    verified=True  # esptool verifies by default
                )
            else:
                # #region agent log
                try:
                    debug_log("esp_uploader.py:234", "Upload failed - non-zero return code", {"returncode": result.returncode}, hypothesis_id="G")
                except Exception:
                    pass
                # #endregion
                error_msg = self._parse_upload_error(result.stderr or result.stdout)
                raise UploadError(f"Upload failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            # #region agent log
            try:
                debug_log_error("esp_uploader.py:241", subprocess.TimeoutExpired("", 120), {"timeout": True}, hypothesis_id="G")
            except Exception:
                pass
            # #endregion
            raise UploadError("Upload timeout - device may not be responding")
        except Exception as e:
            # #region agent log
            try:
                debug_log_error("esp_uploader.py:246", e, {"upload_error": True}, hypothesis_id="G")
            except Exception:
                pass
            # #endregion
            raise UploadError(f"Upload error: {str(e)}")
    
    def probe_device(self, port: str) -> Optional[DeviceInfo]:
        """Probe device information using esptool"""
        try:
            cmd = ["python", "-m", "esptool", "--port", port, "chip-id"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10,
                **get_hidden_subprocess_kwargs()
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
