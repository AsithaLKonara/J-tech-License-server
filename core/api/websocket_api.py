"""
WebSocket API - Real-time bidirectional communication for Budurasmala devices.

Provides WebSocket endpoints for real-time device control and monitoring.
"""

from __future__ import annotations

import json
import logging
import asyncio
from typing import Dict, Set, Optional, Callable
from datetime import datetime

try:
    from websockets.server import serve, WebSocketServerProtocol
    from websockets.exceptions import ConnectionClosed
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = None

logger = logging.getLogger(__name__)


class BudurasmalaWebSocketAPI:
    """
    WebSocket API server for real-time Budurasmala device control.
    
    Features:
    - Real-time device status updates
    - Live preview streaming
    - Bidirectional command/response
    - Multi-client support
    """
    
    def __init__(self, device_manager, host: str = "0.0.0.0", port: int = 8765):
        """
        Initialize WebSocket API server.
        
        Args:
            device_manager: DeviceManager instance
            host: Host to bind to
            port: Port to listen on
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library not available. Install with: pip install websockets")
        
        self.device_manager = device_manager
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.device_subscriptions: Dict[str, Set[WebSocketServerProtocol]] = {}
        
        # Setup device manager callbacks
        self.device_manager.add_status_callback(self._on_device_status_changed)
        self.device_manager.add_preview_callback(self._on_preview_update)
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket client connection."""
        self.clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"WebSocket client connected: {client_id}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': 'Connected to Budurasmala WebSocket API',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON'
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))
        
        except ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            # Remove from device subscriptions
            for device_id, subscribers in self.device_subscriptions.items():
                subscribers.discard(websocket)
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle incoming WebSocket message."""
        msg_type = data.get('type')
        
        if msg_type == 'subscribe_device':
            device_id = data.get('device_id')
            if device_id:
                if device_id not in self.device_subscriptions:
                    self.device_subscriptions[device_id] = set()
                self.device_subscriptions[device_id].add(websocket)
                await websocket.send(json.dumps({
                    'type': 'subscribed',
                    'device_id': device_id
                }))
        
        elif msg_type == 'unsubscribe_device':
            device_id = data.get('device_id')
            if device_id and device_id in self.device_subscriptions:
                self.device_subscriptions[device_id].discard(websocket)
                await websocket.send(json.dumps({
                    'type': 'unsubscribed',
                    'device_id': device_id
                }))
        
        elif msg_type == 'command':
            device_id = data.get('device_id')
            command = data.get('command')
            parameters = data.get('parameters', {})
            
            if device_id and command:
                from core.services.device_manager import DeviceCommand
                cmd = DeviceCommand(command, parameters)
                success = self.device_manager.send_command(device_id, cmd)
                
                await websocket.send(json.dumps({
                    'type': 'command_result',
                    'device_id': device_id,
                    'command': command,
                    'success': success
                }))
        
        elif msg_type == 'get_devices':
            devices = self.device_manager.list_devices()
            await websocket.send(json.dumps({
                'type': 'devices',
                'devices': [{
                    'device_id': d.device_id,
                    'name': d.name,
                    'ip_address': d.ip_address,
                    'status': d.status.value,
                    'current_pattern': d.current_pattern,
                    'brightness': d.brightness
                } for d in devices]
            }))
        
        elif msg_type == 'get_device_status':
            device_id = data.get('device_id')
            if device_id:
                device = self.device_manager.get_device(device_id)
                if device:
                    await websocket.send(json.dumps({
                        'type': 'device_status',
                        'device_id': device_id,
                        'status': device.status.value,
                        'current_pattern': device.current_pattern,
                        'brightness': device.brightness,
                        'last_seen': device.last_seen.isoformat() if device.last_seen else None
                    }))
                else:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Device {device_id} not found'
                    }))
    
    def _on_device_status_changed(self, device_id: str, status):
        """Handle device status change - broadcast to subscribers."""
        if device_id in self.device_subscriptions:
            message = json.dumps({
                'type': 'device_status_update',
                'device_id': device_id,
                'status': status.value,
                'timestamp': datetime.now().isoformat()
            })
            
            # Broadcast to all subscribers
            disconnected = set()
            for websocket in self.device_subscriptions[device_id]:
                try:
                    asyncio.create_task(websocket.send(message))
                except Exception:
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            for ws in disconnected:
                self.device_subscriptions[device_id].discard(ws)
    
    def _on_preview_update(self, device_id: str, preview_data: bytes):
        """Handle preview update - broadcast to subscribers."""
        if device_id in self.device_subscriptions:
            import base64
            preview_b64 = base64.b64encode(preview_data).decode('utf-8')
            
            message = json.dumps({
                'type': 'preview_update',
                'device_id': device_id,
                'preview': preview_b64,
                'format': 'rgb24',
                'timestamp': datetime.now().isoformat()
            })
            
            # Broadcast to all subscribers
            disconnected = set()
            for websocket in self.device_subscriptions[device_id]:
                try:
                    asyncio.create_task(websocket.send(message))
                except Exception:
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            for ws in disconnected:
                self.device_subscriptions[device_id].discard(ws)
    
    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket API server on {self.host}:{self.port}")
        async with serve(self._handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    def run(self):
        """Run the WebSocket server (blocking)."""
        asyncio.run(self.start())

