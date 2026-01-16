"""
Device Manager - Real-time device control and monitoring for Budurasmala displays.

This service manages connections to Budurasmala devices, provides real-time control,
monitoring, and pattern scheduling capabilities.
"""

from __future__ import annotations

import time
import logging
import threading
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import requests

from core.retry import retry_network_errors, retry_device_errors

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Device connection status."""
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    UPDATING = "updating"
    ERROR = "error"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class BudurasmalaDevice:
    """Represents a Budurasmala display device."""
    device_id: str
    name: str
    ip_address: str
    port: int = 80
    device_type: str = "ESP32"  # ESP32, ESP8266, etc.
    firmware_version: Optional[str] = None
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_seen: Optional[datetime] = None
    current_pattern: Optional[str] = None
    brightness: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Device capabilities
    supports_ota: bool = True
    supports_live_preview: bool = True
    supports_scheduling: bool = True
    max_leds: int = 1000


@dataclass
class DeviceCommand:
    """Command to send to device."""
    command: str  # "play", "pause", "stop", "set_brightness", "load_pattern", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ScheduledPattern:
    """Scheduled pattern to play on device."""
    schedule_id: str
    device_id: str
    pattern_name: str
    pattern_data: bytes
    start_time: datetime
    end_time: Optional[datetime] = None
    repeat: bool = False
    enabled: bool = True


class DeviceManager:
    """
    Manages Budurasmala devices and provides real-time control.
    
    Features:
    - Device discovery and connection
    - Real-time control (play, pause, stop, brightness)
    - Live preview from devices
    - Device status monitoring
    - Pattern scheduling
    - Multi-device coordination
    """
    
    def __init__(self):
        self._devices: Dict[str, BudurasmalaDevice] = {}
        self._schedules: Dict[str, ScheduledPattern] = {}
        self._status_callbacks: List[Callable[[str, DeviceStatus], None]] = []
        self._preview_callbacks: List[Callable[[str, bytes], None]] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._schedule_thread: Optional[threading.Thread] = None
        self._schedule_active = False
    
    def discover_devices(self, network_range: str = "192.168.1.0/24", timeout: float = 5.0) -> List[BudurasmalaDevice]:
        """
        Discover Budurasmala devices on the network.
        
        Args:
            network_range: Network range to scan (CIDR notation)
            timeout: Timeout per device in seconds
            
        Returns:
            List of discovered devices
        """
        discovered = []
        
        try:
            logger.info(f"Scanning network {network_range} for Budurasmala devices...")
            
            # Extract base IP from range
            base_ip = network_range.split('/')[0]
            base_parts = base_ip.rsplit('.', 1)
            if len(base_parts) == 2:
                base = base_parts[0]
                
                # Scan common IPs (1-254)
                for i in range(1, 255):
                    ip = f"{base}.{i}"
                    device = self._probe_device(ip, timeout)
                    if device:
                        discovered.append(device)
                        self.add_device(device)
            
        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
        
        return discovered
    
    @retry_network_errors(max_attempts=2, delay=0.5, backoff=1.5)
    def _probe_device_request(self, ip: str, timeout: float) -> requests.Response:
        """Internal probe request with retry."""
        return requests.get(f"http://{ip}/api/status", timeout=timeout)
    
    def _probe_device(self, ip: str, timeout: float) -> Optional[BudurasmalaDevice]:
        """Probe a specific IP address for Budurasmala device."""
        try:
            # Try to connect to device API
            response = self._probe_device_request(ip, timeout)
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's a Budurasmala device
                if data.get('device_type') == 'budurasmala' or 'budurasmala' in data.get('name', '').lower():
                    device = BudurasmalaDevice(
                        device_id=data.get('device_id', ip),
                        name=data.get('name', f'Budurasmala {ip}'),
                        ip_address=ip,
                        port=data.get('port', 80),
                        device_type=data.get('chip_type', 'ESP32'),
                        firmware_version=data.get('firmware_version'),
                        status=DeviceStatus.ONLINE,
                        last_seen=datetime.now(),
                        current_pattern=data.get('current_pattern'),
                        brightness=data.get('brightness', 100),
                        metadata=data
                    )
                    return device
        except Exception:
            pass
        
        return None
    
    def add_device(self, device: BudurasmalaDevice) -> None:
        """Add a device to the manager."""
        self._devices[device.device_id] = device
        logger.info(f"Added device: {device.name} ({device.device_id}) at {device.ip_address}")
    
    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the manager."""
        if device_id in self._devices:
            del self._devices[device_id]
            # Remove associated schedules
            schedules_to_remove = [s for s in self._schedules.values() if s.device_id == device_id]
            for schedule in schedules_to_remove:
                del self._schedules[schedule.schedule_id]
            return True
        return False
    
    def get_device(self, device_id: str) -> Optional[BudurasmalaDevice]:
        """Get device by ID."""
        return self._devices.get(device_id)
    
    def list_devices(self) -> List[BudurasmalaDevice]:
        """List all devices."""
        return list(self._devices.values())
    
    def send_command(self, device_id: str, command: DeviceCommand) -> bool:
        """
        Send command to device.
        
        Args:
            device_id: Device ID
            command: Command to send
            
        Returns:
            True if command was sent successfully
        """
        device = self.get_device(device_id)
        if not device:
            logger.error(f"Device not found: {device_id}")
            return False
        
        @retry_network_errors(max_attempts=2, delay=0.5, backoff=1.5)
        def _send_command_request(url: str, payload: dict) -> requests.Response:
            return requests.post(url, json=payload, timeout=5)
        
        try:
            url = f"http://{device.ip_address}:{device.port}/api/command"
            payload = {
                "command": command.command,
                "parameters": command.parameters,
                "timestamp": command.timestamp.isoformat()
            }
            response = _send_command_request(url, payload)
            
            if response.status_code == 200:
                logger.info(f"Command '{command.command}' sent to {device.name}")
                return True
            else:
                logger.error(f"Command failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send command to {device_id}: {e}")
            device.status = DeviceStatus.ERROR
            return False
    
    def play_pattern(self, device_id: str, pattern_data: bytes, pattern_name: str = "Pattern") -> bool:
        """Play pattern on device."""
        device = self.get_device(device_id)
        if not device:
            return False
        
        # Upload pattern
        @retry_network_errors(max_attempts=2, delay=1.0, backoff=2.0)
        def _upload_pattern_request(url: str, files: dict) -> requests.Response:
            return requests.post(url, files=files, timeout=30)
        
        try:
            url = f"http://{device.ip_address}:{device.port}/api/upload"
            files = {'pattern': (pattern_name, pattern_data, 'application/octet-stream')}
            response = _upload_pattern_request(url, files)
            
            if response.status_code == 200:
                # Send play command
                command = DeviceCommand("play", {"pattern": pattern_name})
                if self.send_command(device_id, command):
                    device.current_pattern = pattern_name
                    device.status = DeviceStatus.PLAYING
                    return True
        except Exception as e:
            logger.error(f"Failed to play pattern on {device_id}: {e}")
        
        return False
    
    def pause_device(self, device_id: str) -> bool:
        """Pause playback on device."""
        command = DeviceCommand("pause")
        if self.send_command(device_id, command):
            device = self.get_device(device_id)
            if device:
                device.status = DeviceStatus.PAUSED
            return True
        return False
    
    def stop_device(self, device_id: str) -> bool:
        """Stop playback on device."""
        command = DeviceCommand("stop")
        if self.send_command(device_id, command):
            device = self.get_device(device_id)
            if device:
                device.status = DeviceStatus.STOPPED
            return True
        return False
    
    def set_brightness(self, device_id: str, brightness: int) -> bool:
        """Set device brightness (0-100)."""
        brightness = max(0, min(100, brightness))
        command = DeviceCommand("set_brightness", {"brightness": brightness})
        if self.send_command(device_id, command):
            device = self.get_device(device_id)
            if device:
                device.brightness = brightness
            return True
        return False
    
    def get_live_preview(self, device_id: str) -> Optional[bytes]:
        """Get live preview frame from device."""
        device = self.get_device(device_id)
        if not device or not device.supports_live_preview:
            return None
        
        try:
            url = f"http://{device.ip_address}:{device.port}/api/preview"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        
        return None
    
    def start_monitoring(self, interval: float = 5.0):
        """Start monitoring device status."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Device monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring device status."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2)
        logger.info("Device monitoring stopped")
    
    def _monitoring_loop(self, interval: float):
        """Monitoring loop thread."""
        while self._monitoring_active:
            try:
                for device in list(self._devices.values()):
                    # Check device status
                    old_status = device.status
                    device = self._update_device_status(device)
                    
                    # Notify callbacks if status changed
                    if device.status != old_status:
                        for callback in self._status_callbacks:
                            try:
                                callback(device.device_id, device.status)
                            except Exception as e:
                                logger.error(f"Status callback error: {e}")
                    
                    # Get live preview if supported
                    if device.supports_live_preview and device.status == DeviceStatus.PLAYING:
                        preview = self.get_live_preview(device.device_id)
                        if preview:
                            for callback in self._preview_callbacks:
                                try:
                                    callback(device.device_id, preview)
                                except Exception as e:
                                    logger.error(f"Preview callback error: {e}")
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)
    
    def _update_device_status(self, device: BudurasmalaDevice) -> BudurasmalaDevice:
        """Update device status by querying device."""
        try:
            url = f"http://{device.ip_address}:{device.port}/api/status"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                device.status = DeviceStatus(data.get('status', 'offline'))
                device.last_seen = datetime.now()
                device.current_pattern = data.get('current_pattern')
                device.brightness = data.get('brightness', 100)
            else:
                device.status = DeviceStatus.OFFLINE
        except Exception:
            device.status = DeviceStatus.OFFLINE
        
        return device
    
    def add_status_callback(self, callback: Callable[[str, DeviceStatus], None]):
        """Add callback for device status changes."""
        self._status_callbacks.append(callback)
    
    def add_preview_callback(self, callback: Callable[[str, bytes], None]):
        """Add callback for live preview updates."""
        self._preview_callbacks.append(callback)
    
    # Scheduling functions
    def schedule_pattern(
        self,
        device_id: str,
        pattern_name: str,
        pattern_data: bytes,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        repeat: bool = False
    ) -> str:
        """Schedule a pattern to play on device."""
        schedule_id = f"{device_id}_{int(start_time.timestamp())}"
        
        schedule = ScheduledPattern(
            schedule_id=schedule_id,
            device_id=device_id,
            pattern_name=pattern_name,
            pattern_data=pattern_data,
            start_time=start_time,
            end_time=end_time,
            repeat=repeat
        )
        
        self._schedules[schedule_id] = schedule
        
        # Start scheduler if not running
        if not self._schedule_active:
            self.start_scheduler()
        
        logger.info(f"Scheduled pattern '{pattern_name}' for {device_id} at {start_time}")
        return schedule_id
    
    def cancel_schedule(self, schedule_id: str) -> bool:
        """Cancel a scheduled pattern."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False
    
    def start_scheduler(self):
        """Start pattern scheduler."""
        if self._schedule_active:
            return
        
        self._schedule_active = True
        self._schedule_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._schedule_thread.start()
        logger.info("Pattern scheduler started")
    
    def stop_scheduler(self):
        """Stop pattern scheduler."""
        self._schedule_active = False
        if self._schedule_thread:
            self._schedule_thread.join(timeout=2)
        logger.info("Pattern scheduler stopped")
    
    def _scheduler_loop(self):
        """Scheduler loop thread."""
        while self._schedule_active:
            try:
                now = datetime.now()
                
                for schedule in list(self._schedules.values()):
                    if not schedule.enabled:
                        continue
                    
                    # Check if it's time to start
                    if schedule.start_time <= now:
                        if schedule.end_time is None or now <= schedule.end_time:
                            # Play pattern
                            device = self.get_device(schedule.device_id)
                            if device and device.status != DeviceStatus.PLAYING:
                                self.play_pattern(
                                    schedule.device_id,
                                    schedule.pattern_data,
                                    schedule.pattern_name
                                )
                        
                        # Handle end time
                        if schedule.end_time and now > schedule.end_time:
                            if schedule.repeat:
                                # Reschedule for next occurrence
                                duration = schedule.end_time - schedule.start_time
                                schedule.start_time = now + timedelta(days=1)
                                schedule.end_time = schedule.start_time + duration
                            else:
                                # Remove one-time schedule
                                del self._schedules[schedule.schedule_id]
                
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(1)

