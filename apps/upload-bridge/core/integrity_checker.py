"""
Integrity Checker - Detects Patched Binaries
Periodic integrity checks to detect tampering
"""

import hashlib
import time
import requests
import platform
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IntegrityChecker:
    """
    Performs integrity checks to detect patched binaries.
    Sends runtime state hash to server for anomaly detection.
    """
    
    def __init__(self, server_url: str = "http://localhost:3000", auth_manager=None):
        self.server_url = server_url
        self.auth_manager = auth_manager
        self.last_check_time = 0
        self.check_interval = 3600  # 1 hour
    
    def get_runtime_state_hash(self) -> str:
        """
        Generate hash of runtime state for integrity checking.
        
        Returns:
            SHA-256 hash of runtime state
        """
        try:
            # Collect runtime state information
            state_data = {
                'python_version': sys.version,
                'platform': platform.platform(),
                'executable': sys.executable,
                'argv': sys.argv[:1],  # Only first arg (script name)
                'path_count': len(sys.path),
                'modules_count': len(sys.modules),
            }
            
            # Create deterministic hash
            state_string = str(sorted(state_data.items()))
            state_hash = hashlib.sha256(state_string.encode()).hexdigest()
            
            return state_hash
        except Exception as e:
            logger.error("Failed to generate runtime state hash: %s", e)
            return ""
    
    def sign_state_hash(self, state_hash: str) -> Optional[str]:
        """
        Sign state hash (placeholder - would use actual signing in production).
        
        Args:
            state_hash: State hash to sign
        
        Returns:
            Signed hash or None
        """
        # In production, this would use cryptographic signing
        # For now, return a simple signature
        try:
            if self.auth_manager and hasattr(self.auth_manager, 'get_device_id'):
                device_id = self.auth_manager.get_device_id()
                signature_data = f"{state_hash}:{device_id}:{int(time.time())}"
                signature = hashlib.sha256(signature_data.encode()).hexdigest()
                return signature
        except Exception as e:
            logger.error("Failed to sign state hash: %s", e)
        return None
    
    def send_heartbeat(self) -> bool:
        """
        Send integrity heartbeat to server.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if enough time has passed
            now = time.time()
            if (now - self.last_check_time) < self.check_interval:
                return True  # Skip if too soon
            
            # Generate state hash
            state_hash = self.get_runtime_state_hash()
            if not state_hash:
                return False
            
            # Sign hash
            signature = self.sign_state_hash(state_hash)
            
            # Get device ID
            device_id = None
            if self.auth_manager and hasattr(self.auth_manager, 'get_device_id'):
                device_id = self.auth_manager.get_device_id()
            
            # Get user token
            user_token = None
            if self.auth_manager and hasattr(self.auth_manager, 'session_token'):
                user_token = self.auth_manager.session_token
            
            # Send to server
            headers = {}
            if user_token:
                headers['Authorization'] = f'Bearer {user_token}'
            
            response = requests.post(
                f"{self.server_url}/api/v2/integrity/heartbeat",
                json={
                    'state_hash': state_hash,
                    'signature': signature,
                    'device_id': device_id,
                    'timestamp': int(now)
                },
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                self.last_check_time = now
                return True
            else:
                logger.warning("Integrity heartbeat failed: %s", response.status_code)
                return False
                
        except Exception as e:
            logger.debug("Integrity heartbeat error (non-critical): %s", e)
            return False  # Don't fail on heartbeat errors
    
    def start_periodic_checks(self, interval: int = 3600):
        """
        Start periodic integrity checks (would use threading in production).
        
        Args:
            interval: Check interval in seconds
        """
        self.check_interval = interval
        # In production, this would start a background thread
        # For now, checks are done on-demand via send_heartbeat()
        logger.info("Integrity checker initialized (checks on-demand)")


def get_integrity_checker(server_url: str = "http://localhost:3000", auth_manager=None) -> IntegrityChecker:
    """Get or create integrity checker instance"""
    return IntegrityChecker(server_url, auth_manager)
