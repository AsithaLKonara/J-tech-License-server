"""
REST API - RESTful API for Budurasmala device control.

Provides HTTP endpoints for programmatic control of Budurasmala devices.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional, List

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    request = None
    jsonify = None
    CORS = None

logger = logging.getLogger(__name__)


class BudurasmalaRESTAPI:
    """
    REST API server for Budurasmala device control.
    
    Endpoints:
    - GET /api/devices - List all devices
    - GET /api/devices/<device_id> - Get device info
    - POST /api/devices/<device_id>/play - Play pattern
    - POST /api/devices/<device_id>/pause - Pause device
    - POST /api/devices/<device_id>/stop - Stop device
    - POST /api/devices/<device_id>/brightness - Set brightness
    - GET /api/devices/<device_id>/status - Get device status
    - GET /api/devices/<device_id>/preview - Get live preview
    """
    
    def __init__(self, device_manager, host: str = "0.0.0.0", port: int = 5000):
        """
        Initialize REST API server.
        
        Args:
            device_manager: DeviceManager instance
            host: Host to bind to
            port: Port to listen on
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for REST API. Install with: pip install flask flask-cors")
        
        self.device_manager = device_manager
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for web clients
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.route('/api/devices', methods=['GET'])
        def list_devices():
            """List all devices."""
            devices = self.device_manager.list_devices()
            return jsonify([{
                'device_id': d.device_id,
                'name': d.name,
                'ip_address': d.ip_address,
                'port': d.port,
                'status': d.status.value,
                'firmware_version': d.firmware_version,
                'current_pattern': d.current_pattern,
                'brightness': d.brightness
            } for d in devices])
        
        @self.app.route('/api/devices/<device_id>', methods=['GET'])
        def get_device(device_id: str):
            """Get device information."""
            device = self.device_manager.get_device(device_id)
            if not device:
                return jsonify({'error': 'Device not found'}), 404
            
            return jsonify({
                'device_id': device.device_id,
                'name': device.name,
                'ip_address': device.ip_address,
                'port': device.port,
                'device_type': device.device_type,
                'status': device.status.value,
                'firmware_version': device.firmware_version,
                'current_pattern': device.current_pattern,
                'brightness': device.brightness,
                'metadata': device.metadata
            })
        
        @self.app.route('/api/devices/<device_id>/play', methods=['POST'])
        def play_device(device_id: str):
            """Play pattern on device."""
            data = request.get_json() or {}
            pattern_data = data.get('pattern_data')
            pattern_name = data.get('pattern_name', 'Pattern')
            
            if not pattern_data:
                return jsonify({'error': 'pattern_data required'}), 400
            
            # Decode base64 pattern data
            import base64
            try:
                pattern_bytes = base64.b64decode(pattern_data)
            except Exception as e:
                return jsonify({'error': f'Invalid pattern data: {e}'}), 400
            
            success = self.device_manager.play_pattern(device_id, pattern_bytes, pattern_name)
            
            if success:
                return jsonify({'status': 'success', 'message': 'Pattern playing'})
            else:
                return jsonify({'error': 'Failed to play pattern'}), 500
        
        @self.app.route('/api/devices/<device_id>/pause', methods=['POST'])
        def pause_device(device_id: str):
            """Pause device."""
            success = self.device_manager.pause_device(device_id)
            if success:
                return jsonify({'status': 'success', 'message': 'Device paused'})
            else:
                return jsonify({'error': 'Failed to pause device'}), 500
        
        @self.app.route('/api/devices/<device_id>/stop', methods=['POST'])
        def stop_device(device_id: str):
            """Stop device."""
            success = self.device_manager.stop_device(device_id)
            if success:
                return jsonify({'status': 'success', 'message': 'Device stopped'})
            else:
                return jsonify({'error': 'Failed to stop device'}), 500
        
        @self.app.route('/api/devices/<device_id>/brightness', methods=['POST'])
        def set_brightness(device_id: str):
            """Set device brightness."""
            data = request.get_json() or {}
            brightness = data.get('brightness')
            
            if brightness is None:
                return jsonify({'error': 'brightness required'}), 400
            
            success = self.device_manager.set_brightness(device_id, brightness)
            if success:
                return jsonify({'status': 'success', 'message': f'Brightness set to {brightness}%'})
            else:
                return jsonify({'error': 'Failed to set brightness'}), 500
        
        @self.app.route('/api/devices/<device_id>/status', methods=['GET'])
        def get_status(device_id: str):
            """Get device status."""
            device = self.device_manager.get_device(device_id)
            if not device:
                return jsonify({'error': 'Device not found'}), 404
            
            return jsonify({
                'device_id': device.device_id,
                'status': device.status.value,
                'current_pattern': device.current_pattern,
                'brightness': device.brightness,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None
            })
        
        @self.app.route('/api/devices/<device_id>/preview', methods=['GET'])
        def get_preview(device_id: str):
            """Get live preview from device."""
            preview = self.device_manager.get_live_preview(device_id)
            if preview:
                import base64
                preview_b64 = base64.b64encode(preview).decode('utf-8')
                return jsonify({
                    'preview': preview_b64,
                    'format': 'rgb24'  # or whatever format device uses
                })
            else:
                return jsonify({'error': 'Preview not available'}), 404
        
        @self.app.route('/api/discover', methods=['POST'])
        def discover_devices():
            """Discover devices on network."""
            data = request.get_json() or {}
            network_range = data.get('network_range', '192.168.1.0/24')
            timeout = data.get('timeout', 5.0)
            
            devices = self.device_manager.discover_devices(network_range, timeout)
            
            return jsonify({
                'count': len(devices),
                'devices': [{
                    'device_id': d.device_id,
                    'name': d.name,
                    'ip_address': d.ip_address
                } for d in devices]
            })
    
    def start(self, debug: bool = False):
        """Start the API server."""
        logger.info(f"Starting REST API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)
    
    def stop(self):
        """Stop the API server."""
        # Flask doesn't have a built-in stop method
        # In production, use a proper WSGI server like gunicorn
        logger.info("REST API server stopped")

