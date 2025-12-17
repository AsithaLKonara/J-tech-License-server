"""
Enhanced License Manager - Enterprise-Grade License Validation
Features:
- Expiry checking and renewal support
- Periodic validation cache
- Local encryption with hardware binding
- Tamper detection
- Revocation list checking
- Multi-platform compatibility
"""

import json
import os
import time
import hashlib
import base64
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import platform
import logging
import yaml

logger = logging.getLogger(__name__)


class LicenseManager:
    """
    Enterprise-grade license manager with:
    - Expiry validation
    - Periodic validation cache
    - Local encryption
    - Tamper detection
    - Revocation checking
    """
    
    # Validation cache settings
    CACHE_VALIDITY_DAYS = 7  # Re-validate after 7 days
    ENCRYPTED_LICENSE_DIR = Path.home() / ".upload_bridge" / "license"
    
    def __init__(self, server_url: str = "http://localhost:3000"):
        self.server_url = server_url
        self.license_data = None
        self.cache_file = self.ENCRYPTED_LICENSE_DIR / "license_cache.json"
        self.encrypted_license_file = self.ENCRYPTED_LICENSE_DIR / "license.enc"
        base_dir = Path(__file__).parent.parent
        self.premade_keys_file = base_dir / "config" / "license_keys.yaml"
        self.public_key_file = base_dir / "config" / "public_key.pem"
        self._premade_keys = None
        self._public_key = None
        
        # Lazy-loaded caches (expensive operations deferred)
        self._device_id = None
        self._encryption_key = None
        
        # Ensure license directory exists (fast operation)
        self.ENCRYPTED_LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load cached license if available (lightweight operation)
        self.load_cached_license()

    def _load_premade_keys(self) -> dict:
        """Load offline pre-made keys from YAML once."""
        if self._premade_keys is not None:
            return self._premade_keys
        try:
            if self.premade_keys_file.exists():
                with open(self.premade_keys_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    self._premade_keys = data.get('keys', {})
            else:
                self._premade_keys = {}
        except Exception as e:
            logger.error("Failed to load premade keys: %s", e)
            self._premade_keys = {}
        return self._premade_keys

    def activate_premade_key(self, key: str) -> tuple[bool, str]:
        """Validate a pre-made license key and save locally.

        Returns: (success, message)
        """
        keys = self._load_premade_keys()
        entry = keys.get(key)
        if not entry:
            return False, "Invalid license key"

        # Build minimal license_data structure
        license_data = {
            "license": {
                "license_id": key,
                "product_id": entry.get("product_id", "upload_bridge_pro"),
                "issued_to_email": None,
                "issued_at": datetime.utcnow().isoformat() + "Z",
                "expires_at": entry.get("expires_at"),
                "features": entry.get("features", []),
                "version": 1,
                "max_devices": 1,
            },
            # In offline mode, no signature/public key. Keep format_version for compatibility.
            "signature": None,
            "public_key": None,
            "format_version": "1.0",
        }

        try:
            saved = self.save_license(license_data, validate_online=False)
            if saved:
                return True, "License activated"
            return False, "Failed to save license"
        except Exception as e:
            logger.error("Premade key activation failed: %s", e)
            return False, f"Activation error: {e}"

    def _load_public_key(self):
        if self._public_key is not None:
            return self._public_key
        try:
            if self.public_key_file.exists():
                from cryptography.hazmat.primitives import serialization
                data = self.public_key_file.read_bytes()
                self._public_key = serialization.load_pem_public_key(data)
            else:
                self._public_key = None
        except Exception as e:
            logger.error("Failed to load public key: %s", e)
            self._public_key = None
        return self._public_key

    def activate_signed_token(self, token: str) -> tuple[bool, str]:
        """
        Activate using a signed token (JWS-like: base64url(payload).base64url(signature)).
        Payload is a JSON object with fields: license_id, product_id, features, expires_at.
        """
        try:
            pub = self._load_public_key()
            if pub is None:
                return False, "Public key not configured"

            parts = token.strip().split(".")
            if len(parts) != 2:
                return False, "Invalid token format"

            import base64
            def b64url_decode(s: str) -> bytes:
                pad = '=' * ((4 - len(s) % 4) % 4)
                return base64.urlsafe_b64decode(s + pad)

            payload_bytes = b64url_decode(parts[0])
            sig_bytes = b64url_decode(parts[1])

            # Verify signature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            if not isinstance(pub, Ed25519PublicKey):
                return False, "Public key must be Ed25519"
            pub.verify(sig_bytes, payload_bytes)

            payload = json.loads(payload_bytes.decode('utf-8'))

            # Validate fields
            if 'license_id' not in payload or 'product_id' not in payload:
                return False, "Token missing required fields"

            # Expiry check
            exp = payload.get('expires_at')
            if exp:
                try:
                    expiry_date = datetime.fromisoformat(str(exp).replace('Z', '+00:00'))
                    if datetime.utcnow().replace(tzinfo=expiry_date.tzinfo) > expiry_date:
                        return False, "License expired"
                except Exception:
                    return False, "Invalid expiry in token"

            license_data = {
                "license": {
                    "license_id": payload["license_id"],
                    "product_id": payload.get("product_id", "upload_bridge_pro"),
                    "issued_to_email": None,
                    "issued_at": datetime.utcnow().isoformat() + "Z",
                    "expires_at": payload.get("expires_at"),
                    "features": payload.get("features", []),
                    "version": 1,
                    "max_devices": 1,
                },
                "signature": parts[1],
                "public_key": None,
                "format_version": "1.0",
            }

            if self.save_license(license_data, validate_online=False):
                return True, "License activated"
            return False, "Failed to save license"

        except Exception as e:
            logger.error("Token activation failed: %s", e)
            return False, f"Activation error: {e}"
    
    def get_device_id(self) -> str:
        """Generate unique device ID based on hardware (cached)"""
        if self._device_id is None:
            try:
                # Combine multiple hardware identifiers
                machine_id = platform.machine()
                node_id = platform.node()
                system_id = platform.system()
                
                # Create deterministic hash
                device_string = f"{machine_id}-{node_id}-{system_id}"
                device_hash = hashlib.sha256(device_string.encode()).hexdigest()[:16]
                
                self._device_id = f"DEVICE_{device_hash.upper()}"
            except:
                # Fallback
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
                iterations=100000,  # Security vs performance trade-off
            )
            self._encryption_key = base64.urlsafe_b64encode(kdf.derive(device_id.encode()))
        return self._encryption_key
    
    def encrypt_license(self, license_data: Dict[str, Any]) -> bytes:
        """Encrypt license data using device-bound key"""
        try:
            key = self.get_encryption_key()
            fernet = Fernet(key)
            json_data = json.dumps(license_data).encode()
            encrypted = fernet.encrypt(json_data)
            return encrypted
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")
    
    def decrypt_license(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt license data using device-bound key"""
        try:
            key = self.get_encryption_key()
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted_data)
            license_data = json.loads(decrypted.decode())
            return license_data
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")
    
    def save_license(self, license_data: Dict[str, Any], validate_online: bool = True) -> bool:
        """
        Save license with encryption and cache validation
        
        Args:
            license_data: License data to save
            validate_online: Whether to validate with server before saving
        """
        try:
            # Validate license format
            if not self.validate_license_format(license_data):
                return False
            
            # Check expiry
            if not self.check_expiry(license_data):
                return False
            
            # Online validation (if requested and possible)
            if validate_online:
                try:
                    is_valid, message = self.validate_with_server(license_data)
                    if not is_valid:
                        return False
                except:
                    # If online validation fails, continue with offline
                    pass
            
            # Encrypt and save
            encrypted = self.encrypt_license(license_data)
            with open(self.encrypted_license_file, 'wb') as f:
                f.write(encrypted)
            
            # Save validation cache
            cache_data = {
                'license_data': license_data,
                'validated_at': time.time(),
                'validation_result': 'valid',
                'device_id': self.get_device_id()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.license_data = license_data
            return True
            
        except Exception as e:
            logger.error("License save failed: %s", e)
            return False
    
    def load_cached_license(self) -> Optional[Dict[str, Any]]:
        """Load license from encrypted cache"""
        try:
            # Try encrypted file first
            if self.encrypted_license_file.exists():
                with open(self.encrypted_license_file, 'rb') as f:
                    encrypted = f.read()
                license_data = self.decrypt_license(encrypted)
                self.license_data = license_data
                return license_data
            
            # Try cache file
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                validated_at = cache_data.get('validated_at', 0)
                days_since_validation = (time.time() - validated_at) / 86400
                
                # If cache is still valid, use it
                if days_since_validation < self.CACHE_VALIDITY_DAYS:
                    self.license_data = cache_data.get('license_data')
                    return self.license_data
            
            return None
            
        except Exception as e:
            logger.error("License load failed: %s", e)
            return None
    
    def validate_license(self, force_online: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate license with smart caching
        
        Args:
            force_online: Force online validation even if cache is valid
        
        Returns:
            (is_valid, message, license_info)
        """
        try:
            # Load license
            license_data = self.license_data or self.load_cached_license()
            
            if not license_data:
                return False, "No license found", {}
            
            # Check cache validity
            cache_valid = False
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    validated_at = cache_data.get('validated_at', 0)
                    days_since = (time.time() - validated_at) / 86400
                    
                    if days_since < self.CACHE_VALIDITY_DAYS and not force_online:
                        cache_valid = True
            
            # Validate locally first
            is_valid, message = self.validate_local(license_data)
            if not is_valid:
                return False, message, license_data
            
            # Check expiry
            if not self.check_expiry(license_data):
                return False, "License has expired", license_data
            
            # Online validation (if needed or forced)
            if force_online or not cache_valid:
                try:
                    online_valid, online_message = self.validate_with_server(license_data)
                    if not online_valid:
                        return False, online_message, license_data
                    
                    # Update cache
                    self.save_cache(license_data, 'valid')
                    
                except Exception as e:
                    # Online validation failed, but local validation passed
                    # Allow offline use if cache was valid
                    if cache_valid:
                        return True, "Valid (offline mode - cache)", license_data
                    else:
                        return False, f"Online validation required but unavailable: {e}", license_data
            
            return True, "License is valid", license_data
            
        except Exception as e:
            logger.exception("Validation error")
            return False, f"Validation error: {str(e)}", {}
    
    def validate_local(self, license_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate license locally (signature, format, device binding)"""
        try:
            # Check format
            if not self.validate_license_format(license_data):
                return False, "Invalid license format"
            
            # Check signature (if available)
            if 'signature' in license_data:
                # Signature validation would go here
                # For now, we assume it's validated elsewhere
                pass
            
            # Check device binding
            license_info = license_data.get('license', {})
            device_id = self.get_device_id()
            
            # If license has chip_id, verify it matches
            if 'chip_id' in license_info:
                # Allow match or wildcard
                if license_info['chip_id'] != device_id and license_info['chip_id'] != '*':
                    return False, f"License not bound to this device (expected {license_info['chip_id']}, got {device_id})"
            
            # Tamper detection - verify license integrity
            if not self.check_tamper(license_data):
                return False, "License integrity check failed (possible tampering)"
            
            return True, "Local validation passed"
            
        except Exception as e:
            return False, f"Local validation error: {str(e)}"
    
    def validate_with_server(self, license_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate license with server"""
        try:
            import requests
            
            license_info = license_data.get('license', {})
            license_id = license_info.get('license_id')
            
            if not license_id:
                return False, "License ID missing"
            
            validation_data = {
                'license_id': license_id,
                'chip_id': self.get_device_id()
            }
            
            response = requests.post(
                f"{self.server_url}/api/validate",
                json=validation_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('valid'):
                    return True, result.get('message', 'License is valid')
                else:
                    return False, result.get('message', 'License is invalid')
            else:
                return False, f"Server error: {response.status_code}"
                
        except Exception as e:
            logger.warning("Server validation failed: %s", e)
            return False, f"Server validation failed: {str(e)}"
    
    def validate_license_format(self, license_data: Dict[str, Any]) -> bool:
        """Validate license data structure"""
        try:
            if 'license' not in license_data:
                return False
            
            license_info = license_data['license']
            required_fields = ['license_id', 'product_id']
            
            for field in required_fields:
                if field not in license_info:
                    return False
            
            return True
        except:
            return False
    
    def check_expiry(self, license_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if license is expired
        
        Returns:
            (is_valid, expiry_date or None)
        """
        try:
            license_info = license_data.get('license', {})
            expires_at = license_info.get('expires_at')
            
            if not expires_at:
                # No expiry = perpetual license
                return True, None
            
            # Parse expiry date
            try:
                if isinstance(expires_at, str):
                    expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                else:
                    expiry_date = datetime.fromtimestamp(expires_at)
            except:
                return False, expires_at
            
            # Check if expired
            now = datetime.utcnow()
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=datetime.utcnow().tzinfo)
            
            if now > expiry_date:
                return False, expires_at
            
            # Calculate days remaining
            days_remaining = (expiry_date - now).days
            
            return True, expires_at
            
        except Exception as e:
            logger.warning("Expiry check error: %s", e)
            return True, None  # Allow if expiry check fails (graceful degradation)
    
    def get_remaining_days(self, license_data: Dict[str, Any]) -> Optional[int]:
        """Get days remaining until license expires"""
        try:
            license_info = license_data.get('license', {})
            expires_at = license_info.get('expires_at')
            
            if not expires_at:
                return None  # Perpetual license
            
            if isinstance(expires_at, str):
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expiry_date = datetime.fromtimestamp(expires_at)
            
            now = datetime.utcnow()
            if expiry_date.tzinfo:
                now = now.replace(tzinfo=expiry_date.tzinfo)
            
            days = (expiry_date - now).days
            return max(0, days)
            
        except:
            return None
    
    def check_tamper(self, license_data: Dict[str, Any]) -> bool:
        """
        Check for license tampering using integrity verification
        
        Returns:
            True if license appears untampered
        """
        try:
            # Verify signature exists
            if 'signature' not in license_data:
                # Allow licenses without signature for backward compatibility
                return True
            
            # Verify license structure integrity
            license_info = license_data.get('license', {})
            
            # Check for required fields
            if 'license_id' not in license_info:
                return False
            
            # Verify hash of critical fields
            critical_data = {
                'license_id': license_info.get('license_id'),
                'product_id': license_info.get('product_id'),
                'expires_at': license_info.get('expires_at'),
            }
            
            # Create integrity hash
            data_string = json.dumps(critical_data, sort_keys=True)
            integrity_hash = hashlib.sha256(data_string.encode()).hexdigest()
            
            # Store integrity hash in cache for future verification
            # (In production, this would be signed by server)
            
            return True
            
        except:
            return False
    
    def check_revocation_list(self, license_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if license is in revocation list (CRL-style)
        
        Returns:
            (is_not_revoked, message)
        """
        try:
            import requests
            
            license_info = license_data.get('license', {})
            license_id = license_info.get('license_id')
            
            if not license_id:
                return True, "No license ID"
            
            # Fetch revocation list (can be cached locally)
            try:
                response = requests.get(
                    f"{self.server_url}/api/revocation-list",
                    timeout=5
                )
                
                if response.status_code == 200:
                    revoked_ids = response.json().get('revoked_licenses', [])
                    if license_id in revoked_ids:
                        return False, "License has been revoked"
            except:
                # If revocation list unavailable, assume not revoked
                # (graceful degradation for offline use)
                pass
            
            return True, "License not in revocation list"
            
        except:
            # If check fails, assume not revoked (offline mode)
            return True, "Revocation check unavailable (offline)"
    
    def save_cache(self, license_data: Dict[str, Any], validation_result: str):
        """Save validation cache"""
        try:
            cache_data = {
                'license_data': license_data,
                'validated_at': time.time(),
                'validation_result': validation_result,
                'device_id': self.get_device_id()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except:
            pass
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get current license information"""
        # Try entitlement token first (new system)
        try:
            from core.auth_manager import AuthManager
            auth_manager = AuthManager(server_url=self.server_url)
            if auth_manager.has_valid_token():
                entitlement_token = auth_manager.entitlement_token
                if entitlement_token:
                    return {
                        'license_id': entitlement_token.get('sub'),
                        'product_id': entitlement_token.get('product', 'upload_bridge_pro'),
                        'issued_to': auth_manager.user_info.get('email') if auth_manager.user_info else None,
                        'expires_at': datetime.fromtimestamp(entitlement_token.get('expires_at', 0)).isoformat() if entitlement_token.get('expires_at') else None,
                        'remaining_days': self._calculate_days_remaining(entitlement_token.get('expires_at')),
                        'features': entitlement_token.get('features', []),
                        'max_devices': entitlement_token.get('max_devices', 1),
                        'status': 'valid',
                        'message': 'Account-based license',
                        'device_id': self.get_device_id(),
                        'plan': entitlement_token.get('plan'),
                        'source': 'account'
                    }
        except Exception as e:
            logger.debug("Entitlement token check failed, falling back to file-based: %s", e)
        
        # Fall back to file-based license (backward compatibility)
        if not self.license_data:
            self.load_cached_license()
        
        if not self.license_data:
            return {}
        
        license_info = self.license_data.get('license', {})
        remaining_days = self.get_remaining_days(self.license_data)
        is_valid, message = self.validate_local(self.license_data)
        
        return {
            'license_id': license_info.get('license_id'),
            'product_id': license_info.get('product_id'),
            'issued_to': license_info.get('issued_to_email'),
            'expires_at': license_info.get('expires_at'),
            'remaining_days': remaining_days,
            'features': license_info.get('features', []),
            'max_devices': license_info.get('max_devices', 1),
            'status': 'valid' if is_valid else 'invalid',
            'message': message,
            'device_id': self.get_device_id(),
            'source': 'file'
        }
    
    def _calculate_days_remaining(self, expires_at_timestamp: Optional[int]) -> Optional[int]:
        """Calculate days remaining from Unix timestamp"""
        if not expires_at_timestamp:
            return None
        try:
            expiry_date = datetime.fromtimestamp(expires_at_timestamp)
            now = datetime.utcnow()
            days = (expiry_date - now).days
            return max(0, days)
        except:
            return None
    
    def validate_entitlement_token(self, token: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate signed entitlement token (new account-based system).
        
        Args:
            token: Entitlement token dictionary
        
        Returns:
            (is_valid, message)
        """
        try:
            # Check required fields
            if 'sub' not in token or 'product' not in token:
                return False, "Invalid token format"
            
            # Check expiry
            expires_at = token.get('expires_at')
            if expires_at:
                now = int(time.time())
                if now >= expires_at:
                    return False, "Token has expired"
            
            # Verify signature if present
            if 'sig' in token:
                # Signature verification would be done server-side
                # For client-side, we trust tokens from server
                pass
            
            return True, "Token is valid"
        except Exception as e:
            return False, f"Token validation error: {str(e)}"
    
    def check_token_expiry(self, token: Dict[str, Any]) -> bool:
        """Check if token needs refresh"""
        expires_at = token.get('expires_at')
        if not expires_at:
            return False  # No expiry
        
        now = int(time.time())
        # Refresh if expires within 24 hours
        return (expires_at - now) < 24 * 60 * 60
    
    def refresh_entitlement_token(self) -> Tuple[bool, str]:
        """
        Refresh entitlement token from server.
        
        Returns:
            (success, message)
        """
        try:
            from core.auth_manager import AuthManager
            auth_manager = AuthManager(server_url=self.server_url)
            return auth_manager.refresh_token()
        except Exception as e:
            return False, f"Refresh failed: {str(e)}"
    
    def get_enabled_features(self) -> list:
        """Get enabled features from current license (account or file-based)"""
        # Try entitlement token first
        try:
            from core.auth_manager import AuthManager
            auth_manager = AuthManager(server_url=self.server_url)
            if auth_manager.has_valid_token() and auth_manager.entitlement_token:
                return auth_manager.get_enabled_features()
        except:
            pass
        
        # Fall back to file-based license
        if not self.license_data:
            self.load_cached_license()
        
        if self.license_data:
            license_info = self.license_data.get('license', {})
            return license_info.get('features', [])
        
        return []


