# utils/wifi_uploader.py
# WiFi Upload Server for ESP8266 Pattern Flasher
# Handles over-the-air pattern uploads to ESP8266 boards

import os
import requests
import json
import time
import threading
from typing import Optional, Dict, Any


class ESP8266WiFiUploader:
    """WiFi uploader for ESP8266 LED Matrix boards"""
    
    def __init__(self, ip_address: str = "192.168.4.1", timeout: int = 60):
        self.ip_address = ip_address
        self.timeout = timeout
        self.base_url = f"http://{ip_address}"
        self.status_url = f"{self.base_url}/api/status"
        self.upload_url = f"{self.base_url}/api/upload"
    
    def check_connection(self) -> bool:
        """Check if ESP8266 is reachable"""
        try:
            response = requests.get(self.status_url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get ESP8266 status information"""
        try:
            response = requests.get(self.status_url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Status check failed: {e}")
            return None
    
    def upload_pattern(self, file_path: str, progress_callback=None) -> tuple[bool, str]:
        """
        Upload pattern file to ESP8266
        
        Args:
            file_path: Path to pattern file (.bin, .hex, .dat)
            progress_callback: Optional callback for upload progress (bytes_sent, total_bytes)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        try:
            # Validate file extension
            if not any(file_name.lower().endswith(ext) for ext in ['.bin', '.hex', '.dat', '.leds', '.ledadmin']):
                return False, "Invalid file format. Use .bin, .hex, .dat, .leds, or .ledadmin files."
            
            # Check connection first
            if not self.check_connection():
                return False, f"Cannot connect to ESP8266 at {self.ip_address}. Check WiFi connection."
            
            # Upload file
            with open(file_path, 'rb') as f:
                files = {'pattern': (file_name, f, 'application/octet-stream')}
                
                # Custom session for progress tracking
                session = requests.Session()
                
                def upload_with_progress():
                    response = session.post(
                        self.upload_url, 
                        files=files, 
                        timeout=self.timeout,
                        stream=True
                    )
                    return response
                
                response = upload_with_progress()
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        message = f"Pattern uploaded successfully: {result.get('message', '')}"
                        return True, message
                    else:
                        return False, f"Upload failed: {result.get('message', 'Unknown error')}"
                else:
                    return False, f"Upload failed with HTTP status {response.status_code}"
                    
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to ESP8266 at {self.ip_address}. Check IP address and WiFi connection."
        except requests.exceptions.Timeout:
            return False, f"Upload timed out after {self.timeout} seconds"
        except Exception as e:
            return False, f"Upload error: {str(e)}"
    
    def validate_pattern_file(self, file_path: str) -> tuple[bool, str, int]:
        """
        Validate pattern file format
        
        Returns:
            Tuple of (is_valid: bool, message: str, file_size: int)
        """
        if not os.path.exists(file_path):
            return False, "File not found", 0
        
        file_size = os.path.getsize(file_path)
        
        if file_size < 4:
            return False, "File too small (minimum 4 bytes for header)", file_size
        
        try:
            with open(file_path, 'rb') as f:
                # Read header (4 bytes)
                header = f.read(4)
                if len(header) < 4:
                    return False, "Incomplete header", file_size
                
                # Parse header (little-endian)
                num_leds = header[0] | (header[1] << 8)
                num_frames = header[2] | (header[3] << 8)
                
                if num_leds == 0:
                    return False, "Invalid LED count: 0", file_size
                
                if num_frames == 0:
                    return False, "Invalid frame count: 0", file_size
                
                # Calculate expected size
                expected_size = 4 + (num_frames * (2 + num_leds * 3))
                
                if file_size != expected_size:
                    return False, f"Size mismatch. Expected: {expected_size}, Got: {file_size}", file_size
                
                return True, f"Valid pattern: {num_leds} LEDs × {num_frames} frames", file_size
                
        except Exception as e:
            return False, f"Validation error: {str(e)}", file_size
    
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
    
    def restart_esp8266(self) -> bool:
        """Restart ESP8266 (if supported)"""
        try:
            # This would require additional endpoint on ESP8266
            response = requests.post(f"{self.base_url}/api/restart", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logging.getLogger(__name__).error(f"Failed to restart ESP8266: {e}")
            return False
        except Exception as e:
            logging.getLogger(__name__).error(f"Unexpected error during restart: {e}", exc_info=True)
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """Set LED brightness (0-255)"""
        try:
            data = {'brightness': max(0, min(255, brightness))}
            response = requests.post(f"{self.base_url}/api/brightness", json=data, timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logging.getLogger(__name__).error(f"Failed to set brightness: {e}")
            return False
        except Exception as e:
            logging.getLogger(__name__).error(f"Unexpected error setting brightness: {e}", exc_info=True)
            return False


class WiFiUploadManager:
    """Manager for multiple ESP8266 WiFi uploaders"""
    
    def __init__(self):
        self.uploaders = {}
        self.scan_results = []
    
    def add_uploader(self, name: str, ip_address: str) -> ESP8266WiFiUploader:
        """Add a new ESP8266 uploader"""
        uploader = ESP8266WiFiUploader(ip_address)
        self.uploaders[name] = uploader
        return uploader
    
    def scan_network(self, base_ip: str = "192.168.4") -> list:
        """Scan network for ESP8266 devices"""
        import threading
        devices = []
        devices_lock = threading.Lock()
        
        def scan_ip(ip):
            try:
                uploader = ESP8266WiFiUploader(ip)
                if uploader.check_connection():
                    status = uploader.get_status()
                    if status:
                        # Thread-safe append
                        with devices_lock:
                            devices.append({
                                'ip': ip,
                                'status': status.get('status', 'Unknown'),
                                'pattern_loaded': status.get('pattern_loaded', False),
                                'ssid': status.get('ssid', 'Unknown')
                            })
            except requests.exceptions.RequestException as e:
                logging.getLogger(__name__).debug(f"Failed to scan IP {ip}: {e}")
            except Exception as e:
                logging.getLogger(__name__).debug(f"Unexpected error scanning {ip}: {e}")
        
        # Scan common IPs
        threads = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            thread = threading.Thread(target=scan_ip, args=(ip,))
            thread.start()
            threads.append(thread)
        
        # Wait for all scans to complete
        for thread in threads:
            thread.join(timeout=1)
        
        return devices
    
    def upload_to_all(self, file_path: str, progress_callback=None) -> Dict[str, tuple[bool, str]]:
        """Upload pattern to all registered ESP8266 devices"""
        results = {}
        
        for name, uploader in self.uploaders.items():
            success, message = uploader.upload_pattern(file_path, progress_callback)
            results[name] = (success, message)
        
        return results


def main():
    """Test the WiFi uploader"""
    uploader = ESP8266WiFiUploader()
    
    print("ESP8266 WiFi Uploader Test")
    print("=" * 30)
    
    # Check connection
    if uploader.check_connection():
        print("✓ ESP8266 is reachable")
        
        # Get status
        status = uploader.get_status()
        if status:
            print(f"Status: {status.get('status', 'Unknown')}")
            print(f"WiFi Mode: {status.get('wifi_mode', 'Unknown')}")
            print(f"SSID: {status.get('ssid', 'Unknown')}")
            
            if status.get('pattern_loaded'):
                print(f"Pattern: {status.get('num_leds', 0)} LEDs × {status.get('num_frames', 0)} frames")
                print(f"Size: {status.get('pattern_size', 0):,} bytes")
            else:
                print("No pattern currently loaded")
    else:
        print("✗ Cannot connect to ESP8266")
        print("Make sure ESP8266 is powered on and WiFi firmware is flashed")
        print("Connect to WiFi network: LEDMatrix_ESP8266")
        print("Password: ledmatrix123")


if __name__ == "__main__":
    main()

