"""
Authentication Manager - Enterprise Account-Based Authentication
Handles login, token refresh, and session management for desktop client
"""

import json
import os
import time
import hashlib
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import platform
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Authentication manager for account-based licensing.
    Handles Auth0 login, token management, and entitlement validation.
    """
    
    AUTH_DIR = Path.home() / ".upload_bridge" / "auth"
    TOKEN_FILE = AUTH_DIR / "token.enc"
    SESSION_FILE = AUTH_DIR / "session.json"
    
    # Offline support durations (in seconds)
    OFFLINE_DURATIONS = {
        'trial': 0,           # No offline
        'monthly': 3 * 24 * 60 * 60,    # 3 days
        'yearly': 14 * 24 * 60 * 60,    # 14 days
        'perpetual': 30 * 24 * 60 * 60  # 30 days
    }
    
    def __init__(self, server_url: str = "http://localhost:3000"):
        self.server_url = server_url
        self.session_token = None
        self.entitlement_token = None
        self.user_info = None
        
        # Lazy-loaded caches
        self._device_id = None
        self._encryption_key = None
        
        # Ensure auth directory exists
        self.AUTH_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load cached session if available
        self.load_session()
    
    def get_device_id(self) -> str:
        """Generate unique device ID based on hardware (cached)"""
        if self._device_id is None:
            try:
                machine_id = platform.machine()
                node_id = platform.node()
                system_id = platform.system()
                
                device_string = f"{machine_id}-{node_id}-{system_id}"
                device_hash = hashlib.sha256(device_string.encode()).hexdigest()[:16]
                
                self._device_id = f"DEVICE_{device_hash.upper()}"
            except:
                self._device_id = f"DEVICE_{hash(str(platform.uname())):016X}"
        return self._device_id
    
    def get_encryption_key(self) -> bytes:
        """Derive encryption key from device ID (hardware-bound, cached)"""
        if self._encryption_key is None:
            device_id = self.get_device_id()
            salt = device_id.encode()[:16].ljust(16, b'0')
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            self._encryption_key = base64.urlsafe_b64encode(kdf.derive(device_id.encode()))
        return self._encryption_key
    
    def encrypt_token(self, token_data: Dict[str, Any]) -> bytes:
        """Encrypt token data using device-bound key"""
        try:
            key = self.get_encryption_key()
            fernet = Fernet(key)
            json_data = json.dumps(token_data).encode()
            encrypted = fernet.encrypt(json_data)
            return encrypted
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")
    
    def decrypt_token(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt token data using device-bound key"""
        try:
            key = self.get_encryption_key()
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted_data)
            token_data = json.loads(decrypted.decode())
            return token_data
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")
    
    def login(self, auth0_token: str, device_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Login with Auth0 token and get session/entitlement tokens.
        
        Args:
            auth0_token: JWT token from Auth0
            device_name: Optional device name for registration
        
        Returns:
            (success, message)
        """
        try:
            device_id = self.get_device_id()
            
            response = requests.post(
                f"{self.server_url}/api/v2/auth/login",
                json={
                    'auth0_token': auth0_token,
                    'device_id': device_id,
                    'device_name': device_name or f"{platform.system()} Device"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                return False, error_data.get('error', f'Login failed: {response.status_code}')
            
            data = response.json()
            
            # Store tokens
            self.session_token = data.get('session_token')
            self.entitlement_token = data.get('entitlement_token')
            self.user_info = data.get('user', {})
            
            # Save session
            self.save_session()
            
            return True, "Login successful"
            
        except requests.exceptions.RequestException as e:
            logger.error("Login request failed: %s", e)
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            logger.error("Login error: %s", e)
            return False, f"Login failed: {str(e)}"
    
    def refresh_token(self) -> Tuple[bool, str]:
        """
        Refresh entitlement token.
        
        Returns:
            (success, message)
        """
        try:
            if not self.session_token:
                return False, "No session token available"
            
            response = requests.post(
                f"{self.server_url}/api/v2/auth/refresh",
                json={
                    'session_token': self.session_token,
                    'device_id': self.get_device_id()
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                return False, error_data.get('error', f'Refresh failed: {response.status_code}')
            
            data = response.json()
            self.entitlement_token = data.get('entitlement_token')
            
            # Update saved session
            self.save_session()
            
            return True, "Token refreshed"
            
        except requests.exceptions.RequestException as e:
            logger.error("Token refresh request failed: %s", e)
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            logger.error("Token refresh error: %s", e)
            return False, f"Refresh failed: {str(e)}"
    
    def has_valid_token(self) -> bool:
        """
        Check if we have a valid entitlement token (cached or fresh).
        
        Returns:
            True if token is valid, False otherwise
        """
        # Load session if not already loaded
        if not self.entitlement_token:
            self.load_session()
        
        if not self.entitlement_token:
            return False
        
        # Check token expiry
        if self.is_token_expired(self.entitlement_token):
            # Try to refresh
            success, _ = self.refresh_token()
            if not success:
                return False
        
        # Check offline grace period
        plan = self.entitlement_token.get('plan', 'monthly')
        if not self.is_within_offline_grace_period(plan):
            # Need to refresh from server
            success, _ = self.refresh_token()
            return success
        
        return True
    
    def is_token_expired(self, token: Dict[str, Any]) -> bool:
        """Check if token is expired"""
        expires_at = token.get('expires_at')
        if not expires_at:
            return False  # No expiry
        
        now = int(time.time())
        return now >= expires_at
    
    def is_within_offline_grace_period(self, plan: str) -> bool:
        """
        Check if we're within offline grace period for the plan.
        
        Returns:
            True if within grace period or online, False if grace period expired
        """
        if plan not in self.OFFLINE_DURATIONS:
            return False
        
        offline_duration = self.OFFLINE_DURATIONS[plan]
        if offline_duration == 0:
            return False  # Trial - no offline
        
        # Check when token was last refreshed
        if not self.entitlement_token:
            return False
        
        issued_at = self.entitlement_token.get('issued_at', 0)
        if not issued_at:
            return False
        
        elapsed = int(time.time()) - issued_at
        return elapsed < offline_duration
    
    def get_enabled_features(self) -> list:
        """Get list of enabled features from entitlement token"""
        if not self.entitlement_token:
            return []
        
        return self.entitlement_token.get('features', [])
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        return self.user_info
    
    def logout(self):
        """Logout and clear session"""
        self.session_token = None
        self.entitlement_token = None
        self.user_info = None
        
        # Delete session files
        if self.TOKEN_FILE.exists():
            self.TOKEN_FILE.unlink()
        if self.SESSION_FILE.exists():
            self.SESSION_FILE.unlink()
    
    def save_session(self):
        """Save session to encrypted file"""
        try:
            if not self.entitlement_token:
                return
            
            session_data = {
                'session_token': self.session_token,
                'entitlement_token': self.entitlement_token,
                'user_info': self.user_info,
                'saved_at': time.time()
            }
            
            encrypted = self.encrypt_token(session_data)
            with open(self.TOKEN_FILE, 'wb') as f:
                f.write(encrypted)
                
        except Exception as e:
            logger.error("Failed to save session: %s", e)
    
    def load_session(self):
        """Load session from encrypted file"""
        try:
            if not self.TOKEN_FILE.exists():
                return
            
            with open(self.TOKEN_FILE, 'rb') as f:
                encrypted = f.read()
            
            session_data = self.decrypt_token(encrypted)
            
            self.session_token = session_data.get('session_token')
            self.entitlement_token = session_data.get('entitlement_token')
            self.user_info = session_data.get('user_info')
            
        except Exception as e:
            logger.error("Failed to load session: %s", e)
            # Clear invalid session
            if self.TOKEN_FILE.exists():
                self.TOKEN_FILE.unlink()


class EntitlementManager:
    """
    Manages entitlement tokens and validation.
    Works with AuthManager to provide entitlement checking.
    """
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled"""
        features = self.auth_manager.get_enabled_features()
        return feature in features
    
    def get_entitlement_info(self) -> Optional[Dict[str, Any]]:
        """Get current entitlement information"""
        token = self.auth_manager.entitlement_token
        if not token:
            return None
        
        return {
            'plan': token.get('plan'),
            'features': token.get('features', []),
            'max_devices': token.get('max_devices', 1),
            'expires_at': token.get('expires_at'),
            'product': token.get('product')
        }


class DeviceManager:
    """
    Handles device registration and management.
    """
    
    def __init__(self, auth_manager: AuthManager, server_url: str = "http://localhost:3000"):
        self.auth_manager = auth_manager
        self.server_url = server_url
    
    def register_device(self, device_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Register current device with server.
        
        Returns:
            (success, message)
        """
        try:
            if not self.auth_manager.session_token:
                return False, "Not authenticated"
            
            device_id = self.auth_manager.get_device_id()
            
            response = requests.post(
                f"{self.server_url}/api/v2/devices/register",
                json={
                    'device_id': device_id,
                    'device_name': device_name or f"{platform.system()} Device"
                },
                headers={
                    'Authorization': f'Bearer {self.auth_manager.session_token}'
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                return False, error_data.get('error', f'Registration failed: {response.status_code}')
            
            return True, "Device registered successfully"
            
        except requests.exceptions.RequestException as e:
            logger.error("Device registration failed: %s", e)
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            logger.error("Device registration error: %s", e)
            return False, f"Registration failed: {str(e)}"
    
    def list_devices(self) -> list:
        """List all registered devices for current user"""
        try:
            if not self.auth_manager.session_token:
                return []
            
            response = requests.get(
                f"{self.server_url}/api/v2/devices",
                headers={
                    'Authorization': f'Bearer {self.auth_manager.session_token}'
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return data.get('devices', [])
            
        except Exception as e:
            logger.error("List devices error: %s", e)
            return []
    
    def revoke_device(self, device_id: str) -> Tuple[bool, str]:
        """
        Revoke a device.
        
        Returns:
            (success, message)
        """
        try:
            if not self.auth_manager.session_token:
                return False, "Not authenticated"
            
            response = requests.delete(
                f"{self.server_url}/api/v2/devices/{device_id}",
                headers={
                    'Authorization': f'Bearer {self.auth_manager.session_token}'
                },
                timeout=10
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                return False, error_data.get('error', f'Revocation failed: {response.status_code}')
            
            return True, "Device revoked successfully"
            
        except Exception as e:
            logger.error("Device revocation error: %s", e)
            return False, f"Revocation failed: {str(e)}"
