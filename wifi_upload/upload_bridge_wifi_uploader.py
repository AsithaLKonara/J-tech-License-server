"""
WiFi Uploader for Upload Bridge
Integrates WiFi upload capabilities with the Upload Bridge pattern system
"""

import os
import sys
import requests
import json
import time
import threading
from typing import Optional, Dict, Any, Tuple
from PySide6.QtCore import QObject, Signal, QThread
import logging

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern import Pattern


class WiFiUploadWorker(QThread):
    """Worker thread for WiFi upload operations in Upload Bridge"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    upload_complete = Signal(bool, str)
    
    def __init__(self, pattern: Pattern, esp_ip: str, esp_port: int = 80):
        super().__init__()
        self.pattern = pattern
        self.esp_ip = esp_ip
        self.esp_port = esp_port
        self.cancelled = False
    
    def run(self):
        """Perform WiFi upload"""
        try:
            self.status_updated.emit("Connecting to ESP8266...")
            
            # Check connection
            if not self.check_connection():
                self.upload_complete.emit(False, "Cannot connect to ESP8266. Check IP address and WiFi connection.")
                return
            
            self.status_updated.emit("Converting pattern to binary format...")
            
            # Convert pattern to binary format
            binary_data = self.convert_pattern_to_binary()
            if not binary_data:
                self.upload_complete.emit(False, "Failed to convert pattern to binary format.")
                return
            
            self.status_updated.emit("Uploading pattern...")
            
            # Upload binary data
            success, message = self.upload_binary_data(binary_data)
            self.upload_complete.emit(success, message)
            
        except Exception as e:
            self.upload_complete.emit(False, f"Upload error: {str(e)}")
    
    def check_connection(self) -> bool:
        """Check if ESP8266 is reachable"""
        try:
            response = requests.get(f"http://{self.esp_ip}/api/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def convert_pattern_to_binary(self) -> Optional[bytes]:
        """Convert Upload Bridge pattern to binary format"""
        try:
            # Create binary header
            header = bytearray()
            
            # LED count (2 bytes, little-endian)
            header.extend(self.pattern.led_count.to_bytes(2, 'little'))
            
            # Frame count (2 bytes, little-endian)
            header.extend(self.pattern.frame_count.to_bytes(2, 'little'))
            
            # Convert frames to binary
            binary_data = bytearray(header)
            
            for frame in self.pattern.frames:
                # Frame delay (2 bytes, little-endian)
                binary_data.extend(frame.duration_ms.to_bytes(2, 'little'))
                
                # RGB data for each LED
                for pixel in frame.pixels:
                    r, g, b = pixel
                    binary_data.extend([r, g, b])
            
            return bytes(binary_data)
            
        except Exception as e:
            logging.getLogger(__name__).error("Pattern conversion error: %s", e)
            return None
    
    def upload_binary_data(self, binary_data: bytes) -> Tuple[bool, str]:
        """Upload binary data to ESP8266"""
        try:
            url = f"http://{self.esp_ip}/api/upload"
            
            # Create a temporary file for upload
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as temp_file:
                temp_file.write(binary_data)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'pattern': ('pattern.bin', f, 'application/octet-stream')}
                    
                    response = requests.post(url, files=files, timeout=60)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            message = f"Pattern uploaded successfully: {result.get('message', '')}"
                            return True, message
                        else:
                            return False, f"Upload failed: {result.get('message', 'Unknown error')}"
                    else:
                        return False, f"Upload failed with HTTP status {response.status_code}"
                        
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to ESP8266 at {self.esp_ip}. Check IP address and WiFi connection."
        except requests.exceptions.Timeout:
            return False, f"Upload timed out after 60 seconds"
        except Exception as e:
            return False, f"Upload error: {str(e)}"
    
    def cancel(self):
        """Cancel the upload operation"""
        self.cancelled = True


class UploadBridgeWiFiUploader(QObject):
    """
    WiFi Uploader integrated with Upload Bridge pattern system
    
    Features:
    - Converts Upload Bridge patterns to binary format
    - Uploads to ESP8266 over WiFi
    - Real-time status monitoring
    - Progress tracking
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.esp_ip = "192.168.4.1"
        self.esp_port = 80
        self.upload_worker = None
    
    def set_esp_config(self, ip: str, port: int = 80):
        """Set ESP8266 configuration"""
        self.esp_ip = ip
        self.esp_port = port
    
    def check_connection(self) -> bool:
        """Check if ESP8266 is reachable"""
        try:
            response = requests.get(f"http://{self.esp_ip}/api/status", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get ESP8266 status information"""
        try:
            response = requests.get(f"http://{self.esp_ip}/api/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            logging.getLogger(__name__).warning("Status check failed: %s", e)
            return None
    
    def upload_pattern(self, pattern: Pattern, progress_callback=None, status_callback=None) -> bool:
        """
        Upload Upload Bridge pattern to ESP8266
        
        Args:
            pattern: Upload Bridge Pattern object
            progress_callback: Optional callback for upload progress
            status_callback: Optional callback for status updates
        
        Returns:
            bool: True if upload started successfully
        """
        if not pattern:
            return False
        
        if self.upload_worker and self.upload_worker.isRunning():
            return False  # Upload already in progress
        
        # Create and start upload worker
        self.upload_worker = WiFiUploadWorker(pattern, self.esp_ip, self.esp_port)
        
        if progress_callback:
            self.upload_worker.progress_updated.connect(progress_callback)
        if status_callback:
            self.upload_worker.status_updated.connect(status_callback)
        
        self.upload_worker.start()
        return True
    
    def cancel_upload(self):
        """Cancel current upload"""
        if self.upload_worker and self.upload_worker.isRunning():
            self.upload_worker.cancel()
            self.upload_worker.quit()
            self.upload_worker.wait()
    
    def is_uploading(self) -> bool:
        """Check if upload is in progress"""
        return self.upload_worker and self.upload_worker.isRunning()
    
    def validate_pattern_for_esp8266(self, pattern: Pattern) -> Tuple[bool, str]:
        """
        Validate pattern for ESP8266 upload
        
        Args:
            pattern: Upload Bridge Pattern object
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        if not pattern:
            return False, "No pattern loaded"
        
        # Check LED count
        if pattern.led_count > 512:
            return False, f"Too many LEDs ({pattern.led_count}). ESP8266 supports up to 512 LEDs."
        
        if pattern.led_count == 0:
            return False, "Invalid LED count: 0"
        
        # Check frame count
        if pattern.frame_count == 0:
            return False, "Invalid frame count: 0"
        
        # Estimate memory usage
        estimated_size = 4 + (pattern.frame_count * (2 + pattern.led_count * 3))
        
        if estimated_size > 900000:  # ~900KB limit for 1MB flash
            return False, f"Pattern too large ({estimated_size:,} bytes). ESP8266 flash limit exceeded."
        
        return True, f"Pattern valid: {pattern.led_count} LEDs × {pattern.frame_count} frames ({estimated_size:,} bytes)"
    
    def get_pattern_info(self) -> Optional[Dict[str, Any]]:
        """Get current pattern information from ESP8266"""
        status = self.get_status()
        if status and status.get('pattern_loaded'):
            return {
                'leds': status.get('num_leds', 0),
                'frames': status.get('num_frames', 0),
                'size': status.get('pattern_size', 0),
                'status': status.get('status', 'Unknown')
            }
        return None
    
    def open_web_interface(self):
        """Open ESP8266 web interface in browser"""
        try:
            import webbrowser
            url = f"http://{self.esp_ip}"
            webbrowser.open(url)
            return True
        except Exception as e:
            logging.getLogger(__name__).error("Failed to open web interface: %s", e)
            return False


# Legacy compatibility with original WiFi uploader
class ESP8266WiFiUploader(UploadBridgeWiFiUploader):
    """Legacy compatibility class"""
    
    def upload_pattern_file(self, file_path: str, progress_callback=None) -> Tuple[bool, str]:
        """Upload pattern file (legacy method)"""
        try:
            # Try to load as Upload Bridge pattern
            from parsers.parser_registry import parse_pattern_file
            
            # Extract LED and frame count from filename or ask user
            # This is a simplified version - in practice, you'd want more robust detection
            pattern = parse_pattern_file(file_path)
            
            if self.upload_pattern(pattern, progress_callback):
                return True, "Upload started"
            else:
                return False, "Failed to start upload"
                
        except Exception as e:
            return False, f"Error loading pattern: {str(e)}"

