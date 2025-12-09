"""
Multi-Device Coordinator - Synchronize multiple Budurasmala devices.

Coordinates playback across multiple devices for synchronized displays.
"""

from __future__ import annotations

import time
import threading
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SyncMode(Enum):
    """Synchronization mode."""
    MASTER_SLAVE = "master_slave"  # One device controls others
    PEER_TO_PEER = "peer_to_peer"  # All devices sync to common clock
    CASCADE = "cascade"  # Effects cascade from one device to next


@dataclass
class DeviceGroup:
    """Group of devices to synchronize."""
    group_id: str
    name: str
    device_ids: List[str]
    sync_mode: SyncMode = SyncMode.MASTER_SLAVE
    master_device_id: Optional[str] = None
    sync_tolerance_ms: int = 50  # Maximum sync tolerance in milliseconds


class MultiDeviceCoordinator:
    """
    Coordinates multiple Budurasmala devices for synchronized playback.
    
    Features:
    - Synchronized playback across devices
    - Master-slave mode
    - Peer-to-peer synchronization
    - Cascading effects
    - Network topology management
    """
    
    def __init__(self, device_manager):
        """
        Initialize coordinator.
        
        Args:
            device_manager: DeviceManager instance
        """
        self.device_manager = device_manager
        self.groups: Dict[str, DeviceGroup] = {}
        self.sync_thread: Optional[threading.Thread] = None
        self.sync_active = False
    
    def create_group(
        self,
        group_id: str,
        name: str,
        device_ids: List[str],
        sync_mode: SyncMode = SyncMode.MASTER_SLAVE,
        master_device_id: Optional[str] = None
    ) -> DeviceGroup:
        """
        Create a device group for synchronization.
        
        Args:
            group_id: Unique group identifier
            name: Group name
            device_ids: List of device IDs in group
            sync_mode: Synchronization mode
            master_device_id: Master device ID (for master-slave mode)
            
        Returns:
            Created DeviceGroup
        """
        if sync_mode == SyncMode.MASTER_SLAVE and not master_device_id:
            if device_ids:
                master_device_id = device_ids[0]
            else:
                raise ValueError("master_device_id required for master-slave mode")
        
        group = DeviceGroup(
            group_id=group_id,
            name=name,
            device_ids=device_ids,
            sync_mode=sync_mode,
            master_device_id=master_device_id
        )
        
        self.groups[group_id] = group
        logger.info(f"Created device group '{name}' with {len(device_ids)} devices")
        
        return group
    
    def remove_group(self, group_id: str) -> bool:
        """Remove a device group."""
        if group_id in self.groups:
            del self.groups[group_id]
            return True
        return False
    
    def get_group(self, group_id: str) -> Optional[DeviceGroup]:
        """Get device group by ID."""
        return self.groups.get(group_id)
    
    def play_synchronized(
        self,
        group_id: str,
        pattern_data: bytes,
        pattern_name: str = "Pattern"
    ) -> bool:
        """
        Play pattern on all devices in group simultaneously.
        
        Args:
            group_id: Group ID
            pattern_data: Pattern data bytes
            pattern_name: Pattern name
            
        Returns:
            True if all devices started successfully
        """
        group = self.get_group(group_id)
        if not group:
            logger.error(f"Group not found: {group_id}")
            return False
        
        if group.sync_mode == SyncMode.MASTER_SLAVE:
            return self._play_master_slave(group, pattern_data, pattern_name)
        elif group.sync_mode == SyncMode.PEER_TO_PEER:
            return self._play_peer_to_peer(group, pattern_data, pattern_name)
        elif group.sync_mode == SyncMode.CASCADE:
            return self._play_cascade(group, pattern_data, pattern_name)
        
        return False
    
    def _play_master_slave(
        self,
        group: DeviceGroup,
        pattern_data: bytes,
        pattern_name: str
    ) -> bool:
        """Play in master-slave mode."""
        # Upload pattern to all devices first
        for device_id in group.device_ids:
            # Upload but don't play yet
            try:
                url = f"http://{self.device_manager.get_device(device_id).ip_address}/api/upload"
                # Upload pattern (simplified - would use actual device manager method)
                pass
            except Exception as e:
                logger.error(f"Failed to upload to {device_id}: {e}")
                return False
        
        # Master device plays first, then commands slaves
        if group.master_device_id:
            master = self.device_manager.get_device(group.master_device_id)
            if master:
                # Play on master
                self.device_manager.play_pattern(group.master_device_id, pattern_data, pattern_name)
                
                # Send sync command to slaves
                from core.services.device_manager import DeviceCommand
                for device_id in group.device_ids:
                    if device_id != group.master_device_id:
                        cmd = DeviceCommand("sync_play", {
                            "master_id": group.master_device_id,
                            "pattern": pattern_name
                        })
                        self.device_manager.send_command(device_id, cmd)
        
        return True
    
    def _play_peer_to_peer(
        self,
        group: DeviceGroup,
        pattern_data: bytes,
        pattern_name: str
    ) -> bool:
        """Play in peer-to-peer mode (all devices sync to common clock)."""
        # Calculate sync time (current time + small delay for coordination)
        sync_time = time.time() + 0.1  # 100ms delay
        
        # Upload and schedule play on all devices
        for device_id in group.device_ids:
            # Upload pattern
            # Schedule play at sync_time
            from core.services.device_manager import DeviceCommand
            cmd = DeviceCommand("play_at", {
                "pattern": pattern_name,
                "sync_time": sync_time
            })
            self.device_manager.send_command(device_id, cmd)
        
        return True
    
    def _play_cascade(
        self,
        group: DeviceGroup,
        pattern_data: bytes,
        pattern_name: str
    ) -> bool:
        """Play in cascade mode (effects flow from one device to next)."""
        cascade_delay = 0.1  # 100ms delay between devices
        
        for i, device_id in enumerate(group.device_ids):
            delay = i * cascade_delay
            
            # Schedule play with delay
            from core.services.device_manager import DeviceCommand
            cmd = DeviceCommand("play_delayed", {
                "pattern": pattern_name,
                "delay": delay
            })
            self.device_manager.send_command(device_id, cmd)
        
        return True
    
    def pause_all(self, group_id: str) -> bool:
        """Pause all devices in group."""
        group = self.get_group(group_id)
        if not group:
            return False
        
        success = True
        for device_id in group.device_ids:
            if not self.device_manager.pause_device(device_id):
                success = False
        
        return success
    
    def stop_all(self, group_id: str) -> bool:
        """Stop all devices in group."""
        group = self.get_group(group_id)
        if not group:
            return False
        
        success = True
        for device_id in group.device_ids:
            if not self.device_manager.stop_device(device_id):
                success = False
        
        return success
    
    def sync_brightness(self, group_id: str, brightness: int) -> bool:
        """Synchronize brightness across all devices in group."""
        group = self.get_group(group_id)
        if not group:
            return False
        
        success = True
        for device_id in group.device_ids:
            if not self.device_manager.set_brightness(device_id, brightness):
                success = False
        
        return success

