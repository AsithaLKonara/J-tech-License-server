"""
Mobile API Client - Client library for mobile apps to control Budurasmala devices.

This module provides a Python client that can be used as a reference for
mobile app implementations (iOS/Android).
"""

from __future__ import annotations

import requests
import json
import base64
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DeviceInfo:
    """Device information."""
    device_id: str
    name: str
    ip_address: str
    status: str
    current_pattern: Optional[str]
    brightness: int


class BudurasmalaMobileClient:
    """
    Mobile API client for controlling Budurasmala devices.
    
    This client can be used as a reference for implementing mobile apps.
    Mobile apps (iOS/Android) would implement similar functionality using
    native HTTP/WebSocket libraries.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        """
        Initialize mobile client.
        
        Args:
            api_base_url: Base URL of REST API server
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.session = requests.Session()
    
    def discover_devices(self, network_range: str = "192.168.1.0/24") -> List[DeviceInfo]:
        """
        Discover devices on network.
        
        Args:
            network_range: Network range to scan
            
        Returns:
            List of discovered devices
        """
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/discover",
                json={"network_range": network_range},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                devices = []
                for dev_data in data.get('devices', []):
                    devices.append(DeviceInfo(
                        device_id=dev_data['device_id'],
                        name=dev_data['name'],
                        ip_address=dev_data['ip_address'],
                        status="online",
                        current_pattern=None,
                        brightness=100
                    ))
                return devices
        except Exception as e:
            print(f"Discovery error: {e}")
        
        return []
    
    def list_devices(self) -> List[DeviceInfo]:
        """List all known devices."""
        try:
            response = self.session.get(f"{self.api_base_url}/api/devices", timeout=5)
            if response.status_code == 200:
                devices = []
                for dev_data in response.json():
                    devices.append(DeviceInfo(
                        device_id=dev_data['device_id'],
                        name=dev_data['name'],
                        ip_address=dev_data['ip_address'],
                        status=dev_data['status'],
                        current_pattern=dev_data.get('current_pattern'),
                        brightness=dev_data.get('brightness', 100)
                    ))
                return devices
        except Exception:
            pass
        
        return []
    
    def get_device_status(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device status."""
        try:
            response = self.session.get(
                f"{self.api_base_url}/api/devices/{device_id}/status",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return DeviceInfo(
                    device_id=data['device_id'],
                    name="",  # Would need full device info
                    ip_address="",
                    status=data['status'],
                    current_pattern=data.get('current_pattern'),
                    brightness=data.get('brightness', 100)
                )
        except Exception:
            pass
        
        return None
    
    def play_pattern(self, device_id: str, pattern_data: bytes, pattern_name: str = "Pattern") -> bool:
        """Play pattern on device."""
        try:
            pattern_b64 = base64.b64encode(pattern_data).decode('utf-8')
            response = self.session.post(
                f"{self.api_base_url}/api/devices/{device_id}/play",
                json={
                    "pattern_data": pattern_b64,
                    "pattern_name": pattern_name
                },
                timeout=30
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def pause_device(self, device_id: str) -> bool:
        """Pause device."""
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/devices/{device_id}/pause",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def stop_device(self, device_id: str) -> bool:
        """Stop device."""
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/devices/{device_id}/stop",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def set_brightness(self, device_id: str, brightness: int) -> bool:
        """Set device brightness (0-100)."""
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/devices/{device_id}/brightness",
                json={"brightness": brightness},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_preview(self, device_id: str) -> Optional[bytes]:
        """Get live preview from device."""
        try:
            response = self.session.get(
                f"{self.api_base_url}/api/devices/{device_id}/preview",
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                return base64.b64decode(data['preview'])
        except Exception:
            pass
        
        return None


# Example usage for mobile app developers
"""
# iOS (Swift) Example:
# 
# import Foundation
# 
# func playPattern(deviceId: String, patternData: Data) {
#     let url = URL(string: "http://localhost:5000/api/devices/\(deviceId)/play")!
#     var request = URLRequest(url: url)
#     request.httpMethod = "POST"
#     request.setValue("application/json", forHTTPHeaderField: "Content-Type")
#     
#     let patternBase64 = patternData.base64EncodedString()
#     let body = ["pattern_data": patternBase64, "pattern_name": "Pattern"]
#     request.httpBody = try? JSONSerialization.data(withJSONObject: body)
#     
#     URLSession.shared.dataTask(with: request) { data, response, error in
#         // Handle response
#     }.resume()
# }

# Android (Kotlin) Example:
# 
# fun playPattern(deviceId: String, patternData: ByteArray) {
#     val url = "http://localhost:5000/api/devices/$deviceId/play"
#     val client = OkHttpClient()
#     val patternBase64 = Base64.encodeToString(patternData, Base64.NO_WRAP)
#     val body = JSONObject().apply {
#         put("pattern_data", patternBase64)
#         put("pattern_name", "Pattern")
#     }
#     
#     val request = Request.Builder()
#         .url(url)
#         .post(body.toString().toRequestBody("application/json".toMediaType()))
#         .build()
#     
#     client.newCall(request).enqueue(object : Callback {
#         override fun onResponse(call: Call, response: Response) {
#             // Handle response
#         }
#         override fun onFailure(call: Call, e: IOException) {
#             // Handle error
#         }
#     })
# }
"""

