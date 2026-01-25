"""
License Manager - Enterprise License Validation System
Handles both account-based and file-based license validation with multi-layer security
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
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_der_public_key
from cryptography.exceptions import InvalidSignature
import platform
import logging

from core.retry import retry_network_errors

logger = logging.getLogger(__name__)


class LicenseManager:
    """
    Enterprise-grade license manager with multi-layer security.
    Supports both account-based (via AuthManager) and file-based licenses.
    """
    
    # Singleton instance
    _instance: Optional['LicenseManager'] = None
    
    # Cache validity period (7 days)
    CACHE_VALIDITY_DAYS = 7
    # Grace period for offline operation (7 days)
    GRACE_PERIOD_DAYS = 7
    
    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize LicenseManager.
        
        Args:
            server_url: License server URL for online validation (defaults to environment variable or localhost)
        """
        if server_url is None:
            server_url = os.environ.get('LICENSE_SERVER_URL', 'https://j-tech-license-server.up.railway.app')
        self.server_url = server_url
        self.ENCRYPTED_LICENSE_DIR = Path.home() / ".upload_bridge" / "license"
        self.cache_file = self.ENCRYPTED_LICENSE_DIR / "license_cache.json"
        self.encrypted_license_file = self.ENCRYPTED_LICENSE_DIR / "license.enc"
        self.last_validation_file = self.ENCRYPTED_LICENSE_DIR / "last_validation.json"
        
        # Ensure license directory exists
        self.ENCRYPTED_LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Lazy-loaded caches
        self._device_id = None
        self._encryption_key = None
        self._auth_manager = None
        self._cached_license_data = None
    
    @classmethod
    def instance(cls, server_url: Optional[str] = None) -> 'LicenseManager':
        """
        Get singleton instance of LicenseManager.
        
        Args:
            server_url: Optional server URL (only used on first call)
        
        Returns:
            LicenseManager instance
        """
        if cls._instance is None:
            if server_url:
                cls._instance = cls(server_url=server_url)
            else:
                cls._instance = cls()
        return cls._instance
    
    def get_device_id(self) -> str:
        """Generate unique device fingerprint based on hardware (cached)"""
        if self._device_id is None:
            try:
                components = []
                
                # System information
                components.append(platform.machine())
                components.append(platform.node())
                components.append(platform.system())
                components.append(platform.processor())
                
                # Try to get MAC address
                try:
                    import uuid
                    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                   for elements in range(0,2*6,2)][::-1])
                    components.append(mac)
                except:
                    pass
                
                # Try to get disk serial (Windows)
                if platform.system() == 'Windows':
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['wmic', 'diskdrive', 'get', 'serialnumber'],
                            capture_output=True, text=True, timeout=2
                        )
                        if result.returncode == 0:
                            serials = [line.strip() for line in result.stdout.split('\n') 
                                      if line.strip() and 'SerialNumber' not in line]
                            if serials:
                                components.append(serials[0])
                    except:
                        pass
                
                # Try to get CPU serial (Linux)
                if platform.system() == 'Linux':
                    try:
                        with open('/proc/cpuinfo', 'r') as f:
                            cpuinfo = f.read()
                            for line in cpuinfo.split('\n'):
                                if 'Serial' in line or 'serial' in line:
                                    components.append(line.split(':')[1].strip() if ':' in line else line)
                                    break
                    except:
                        pass
                
                # Combine all components and hash
                device_string = '-'.join(filter(None, components))
                device_hash = hashlib.sha256(device_string.encode()).hexdigest()[:32]
                
                self._device_id = f"DEVICE_{device_hash.upper()}"
            except Exception as e:
                logger.warning(f"Error generating device ID: {e}")
                # Fallback
                self._device_id = f"DEVICE_{hash(str(platform.uname())):032X}"
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
    
    def _get_auth_manager(self):
        """Get AuthManager instance (lazy-loaded)"""
        if self._auth_manager is None:
            try:
                from core.auth_manager import AuthManager
                self._auth_manager = AuthManager(server_url=self.server_url)
            except ImportError:
                logger.warning("AuthManager not available")
                self._auth_manager = None
        return self._auth_manager
    
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
    
    def _calculate_integrity_hash(self, license_data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of critical license fields for tamper detection"""
        license_obj = license_data.get('license', {})
        critical_fields = {
            'license_id': license_obj.get('license_id'),
            'product_id': license_obj.get('product_id'),
            'expires_at': license_obj.get('expires_at'),
            'issued_to_email': license_obj.get('issued_to_email'),
        }
        critical_string = json.dumps(critical_fields, sort_keys=True)
        return hashlib.sha256(critical_string.encode()).hexdigest()
    
    def _check_expiry(self, license_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check if license is expired"""
        license_obj = license_data.get('license', {})
        expires_at = license_obj.get('expires_at')
        
        if not expires_at:
            return True, None  # Perpetual license
        
        try:
            expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            now = datetime.utcnow()
            
            if now > expiry_date:
                return False, expires_at  # Expired
            return True, expires_at  # Valid
        except Exception as e:
            logger.error(f"Error checking expiry: {e}")
            return False, expires_at
    
    def _check_device_binding(self, license_data: Dict[str, Any]) -> bool:
        """Check if license is bound to current device"""
        license_obj = license_data.get('license', {})
        bound_device_id = license_obj.get('device_id')
        
        if not bound_device_id:
            # License not bound to any device (legacy or new activation)
            return True
        
        current_device_id = self.get_device_id()
        return bound_device_id == current_device_id
    
    def _validate_license_format(self, license_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate license data structure and format"""
        if not isinstance(license_data, dict):
            return False, "License data is not a dictionary"
        
        if 'license' not in license_data:
            return False, "Missing 'license' field"
        
        license_obj = license_data.get('license', {})
        required_fields = ['license_id', 'product_id']
        
        for field in required_fields:
            if field not in license_obj:
                return False, f"Missing required field: {field}"
        
        return True, "Valid format"
    
    def _validate_account_based_license(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate account-based license from AuthManager"""
        auth_manager = self._get_auth_manager()
        if not auth_manager:
            return False, "AuthManager not available", None
        
        if not auth_manager.has_valid_token():
            return False, "No valid authentication token", None
        
        entitlement_token = auth_manager.entitlement_token
        if not entitlement_token:
            return False, "No entitlement token", None
        
        # Convert entitlement token to license format
        license_info = {
            'source': 'account',
            'license': {
                'license_id': f"ACCOUNT_{entitlement_token.get('sub', 'unknown')}",
                'product_id': entitlement_token.get('product', 'upload_bridge_pro'),
                'plan': entitlement_token.get('plan', 'pro'),
                'features': entitlement_token.get('features', []),
                'expires_at': None,
            },
            'entitlement_token': entitlement_token,
        }
        
        # Check expiry if present
        expires_at = entitlement_token.get('expires_at')
        if expires_at:
            now = int(time.time())
            if now >= expires_at:
                return False, "Entitlement token expired", None
            license_info['license']['expires_at'] = datetime.fromtimestamp(expires_at).isoformat() + 'Z'
        
        return True, "Account-based license valid", license_info
    
    def load_cached_license(self) -> Optional[Dict[str, Any]]:
        """Load cached license from encrypted file or cache file"""
        # Prefer encrypted file over cache file
        if self.encrypted_license_file.exists():
            try:
                with open(self.encrypted_license_file, 'rb') as f:
                    encrypted = f.read()
                license_data = self.decrypt_license(encrypted)
                self._cached_license_data = license_data
                return license_data
            except Exception as e:
                logger.error(f"Failed to load encrypted license: {e}")
        
        # Fallback to cache file
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                license_data = cache.get('license_data')
                if license_data:
                    self._cached_license_data = license_data
                    return license_data
            except Exception as e:
                logger.error(f"Failed to load cache file: {e}")
        
        return None
    
    def save_license(self, license_data: Dict[str, Any], validate_online: bool = True) -> bool:
        """
        Save license to encrypted file and cache with transaction-like guarantees.
        
        Args:
            license_data: License data dictionary
            validate_online: Whether to validate with server before saving
        
        Returns:
            True if saved successfully
        """
        import tempfile
        import shutil
        
        backup_license_file = None
        backup_cache_file = None
        
        try:
            # Validate format first (no writes)
            is_valid, message = self._validate_license_format(license_data)
            if not is_valid:
                logger.error(f"Invalid license format: {message}")
                return False
            
            # Online validation if requested
            if validate_online:
                is_valid, message = self.validate_with_server(license_data)
                if not is_valid:
                    logger.warning(f"Server validation failed: {message}")
                    # Continue anyway for offline licenses
            
            # Bind to device
            license_obj = license_data.get('license', {})
            license_obj['device_id'] = self.get_device_id()
            
            # Calculate integrity hash
            integrity_hash = self._calculate_integrity_hash(license_data)
            license_data['integrity_hash'] = integrity_hash
            
            # Create backups of existing files (like a savepoint)
            if self.encrypted_license_file.exists():
                backup_license_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bak')
                shutil.copy2(self.encrypted_license_file, backup_license_file.name)
                backup_license_file.close()
            
            if self.cache_file.exists():
                backup_cache_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bak')
                shutil.copy2(self.cache_file, backup_cache_file.name)
                backup_cache_file.close()
            
            # Write encrypted license
            try:
                encrypted = self.encrypt_license(license_data)
                with open(self.encrypted_license_file, 'wb') as f:
                    f.write(encrypted)
            except Exception as e:
                logger.error(f"Failed to write encrypted license: {e}")
                # Restore backup
                if backup_license_file and Path(backup_license_file.name).exists():
                    shutil.copy2(backup_license_file.name, self.encrypted_license_file)
                raise
            
            # Write cache (if this fails, at least encrypted file is saved)
            try:
                cache_data = {
                    'license_data': license_data,
                    'validated_at': time.time(),
                    'device_id': self.get_device_id(),
                }
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to write cache file: {e}")
                # Cache failure is not critical, but log it
            
            self._cached_license_data = license_data
            logger.info("License saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save license: {e}", exc_info=True)
            return False
        
        finally:
            # Clean up backup files
            if backup_license_file and Path(backup_license_file.name).exists():
                try:
                    os.unlink(backup_license_file.name)
                except OSError as e:
                    logger.warning(f"Could not clean up backup file: {e}")
            
            if backup_cache_file and Path(backup_cache_file.name).exists():
                try:
                    os.unlink(backup_cache_file.name)
                except OSError as e:
                    logger.warning(f"Could not clean up backup cache file: {e}")
    
    @retry_network_errors(max_attempts=3, delay=1.0, backoff=2.0)
    def _validate_request(self, url: str, payload: dict) -> requests.Response:
        """Internal validation request with retry logic."""
        return requests.post(url, json=payload, timeout=10)
    
    def validate_with_server(self, license_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate license with server.
        
        Args:
            license_data: License data dictionary
        
        Returns:
            (is_valid, message)
        """
        try:
            license_obj = license_data.get('license', {})
            license_id = license_obj.get('license_id')
            device_id = self.get_device_id()
            
            url = f"{self.server_url}/api/validate"
            payload = {
                'license_id': license_id,
                'chip_id': device_id,  # Using chip_id for compatibility
            }
            
            response = self._validate_request(url, payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    return True, "Server validation successful"
                else:
                    return False, data.get('message', 'Server validation failed')
            else:
                return False, f"Server returned status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error("License validation failed after retries: %s", e)
            return False, f"Server connection error: {str(e)}. Please check your internet connection and try again."
        except Exception as e:
            logger.error("License validation error: %s", e)
            return False, f"Validation error: {str(e)}"
    
    def validate_license(self, force_online: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate license with server. Supports offline cache validity period.
        
        Args:
            force_online: Always check with server (default: False, allows cache validity period)
        
        Returns:
            (is_valid, message, license_info)
            license_info contains: status, expires_at, plan, etc.
        """
        # Check cache FIRST if not forcing online - cache works offline without auth
        if not force_online and self._is_cache_recent():
            cached_info = self._get_cached_license_info()
            if cached_info:
                logger.info("Using cached license info (cache still valid)")
                return True, "License valid (offline mode)", cached_info
        
        # For online validation or stale cache, require auth
        auth_manager = self._get_auth_manager()
        if not auth_manager or not auth_manager.has_valid_token():
            # Cache is stale or doesn't exist - need online validation
            return False, "Online validation required.", None
        
        # Verify with server
        try:
            result = self._verify_license_with_server(auth_manager)
            # Update validation timestamp on successful validation
            if result[0]:  # is_valid
                self._update_validation_time()
                # Cache license info
                if result[2]:  # license_info
                    self._save_cached_license_info(result[2])
            return result
        except Exception as e:
            logger.error(f"License verification failed: {e}", exc_info=True)
            # If cache is still recent, return cached info even on error
            if not force_online and self._is_cache_recent():
                cached_info = self._get_cached_license_info()
                if cached_info:
                    logger.info("Using cached license info after verification error (cache still valid)")
                    return True, "License valid (offline mode)", cached_info
            return False, "Online validation required.", None
    
    def _verify_license_with_server(self, auth_manager) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verify license with server using /api/v2/license/verify endpoint.
        Enforces ACTIVE status only.
        """
        try:
            device_fingerprint = self.get_device_id()
            device_name = platform.node() or "Unknown Device"
            
            url = f"{self.server_url}/api/v2/license/verify"
            headers = {
                'Authorization': f"Bearer {auth_manager.session_token}",
                'Content-Type': 'application/json',
            }
            payload = {
                'device_fingerprint': device_fingerprint,
                'device_name': device_name,
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', '').upper()
                
                if status == 'ACTIVE':
                    license_info = {
                        'status': 'ACTIVE',
                        'expires_at': data.get('expires_at'),
                        'plan': data.get('plan', 'unknown'),
                        'starts_at': data.get('starts_at'),
                        'features': data.get('features', []),
                    }
                    return True, "License is ACTIVE", license_info
                else:
                    message = data.get('message', f'License status: {status}')
                    return False, message, {'status': status}
            elif response.status_code == 403:
                data = response.json()
                status = data.get('status', 'UNKNOWN')
                message = data.get('message', 'License is not active')
                return False, message, {'status': status}
            else:
                error_msg = f"Server returned status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                return False, error_msg, None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"License verification request failed: {e}")
            return False, f"Unable to connect to license server. Please check your internet connection.", None
        except Exception as e:
            logger.error(f"License verification error: {e}", exc_info=True)
            return False, f"License verification error: {str(e)}", None
    
    def _validate_license_locally(self, license_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Perform local validation checks"""
        # Format validation
        is_valid, message = self._validate_license_format(license_data)
        if not is_valid:
            return False, message
        
        # Expiry check
        is_valid, expires_at = self._check_expiry(license_data)
        if not is_valid:
            return False, f"License expired on {expires_at}"
        
        # Device binding check
        if not self._check_device_binding(license_data):
            return False, "License not bound to this device"
        
        # Tamper detection (integrity hash)
        stored_hash = license_data.get('integrity_hash')
        if stored_hash:
            calculated_hash = self._calculate_integrity_hash(license_data)
            if stored_hash != calculated_hash:
                return False, "License integrity check failed (possible tampering)"
        
        # Signature verification (if signature present)
        signature = license_data.get('signature')
        public_key = license_data.get('public_key')
        if signature and public_key:
            is_valid, message = self._verify_ecdsa_signature(license_data, signature, public_key)
            if not is_valid:
                return False, message
        
        return True, "License valid"
    
    def _verify_ecdsa_signature(self, license_data: Dict[str, Any], signature: str, public_key: str) -> Tuple[bool, str]:
        """
        Verify ECDSA signature of license data.
        
        Args:
            license_data: License data dictionary
            signature: Base64-encoded signature
            public_key: PEM or DER-encoded public key (or base64-encoded DER)
        
        Returns:
            (is_valid, message)
        """
        try:
            # Create message to verify (license data without signature and public_key)
            message_data = {k: v for k, v in license_data.items() if k not in ('signature', 'public_key')}
            message_json = json.dumps(message_data, sort_keys=True)
            message_bytes = message_json.encode('utf-8')
            
            # Hash the message (SHA-256)
            message_hash = hashlib.sha256(message_bytes).digest()
            
            # Decode public key
            try:
                # Try PEM format first
                if isinstance(public_key, str):
                    # Check if it's base64-encoded DER
                    if not public_key.startswith('-----BEGIN'):
                        try:
                            public_key_bytes = base64.b64decode(public_key)
                            # Try to load as DER
                            pub_key = load_der_public_key(public_key_bytes)
                        except:
                            # Try as PEM
                            pub_key = load_pem_public_key(public_key.encode('utf-8'))
                    else:
                        pub_key = load_pem_public_key(public_key.encode('utf-8'))
                else:
                    pub_key = load_der_public_key(public_key)
            except Exception as e:
                logger.error(f"Failed to load public key: {e}")
                return False, f"Invalid public key format: {str(e)}"
            
            # Verify it's an ECDSA key
            if not isinstance(pub_key, ec.EllipticCurvePublicKey):
                return False, "Public key is not an ECDSA key"
            
            # Decode signature
            try:
                signature_bytes = base64.b64decode(signature)
                # Try to decode as DER first, then as raw (r, s) tuple
                try:
                    # Try DER format
                    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
                    r, s = decode_dss_signature(signature_bytes)
                except:
                    # Try raw format (64 bytes for P-256, 96 bytes for P-384, etc.)
                    if len(signature_bytes) == 64:
                        # P-256: 32 bytes r + 32 bytes s
                        r = int.from_bytes(signature_bytes[:32], 'big')
                        s = int.from_bytes(signature_bytes[32:], 'big')
                    elif len(signature_bytes) == 96:
                        # P-384: 48 bytes r + 48 bytes s
                        r = int.from_bytes(signature_bytes[:48], 'big')
                        s = int.from_bytes(signature_bytes[48:], 'big')
                    else:
                        return False, f"Unsupported signature format (length: {len(signature_bytes)})"
            except Exception as e:
                logger.error(f"Failed to decode signature: {e}")
                return False, f"Invalid signature format: {str(e)}"
            
            # Verify signature
            try:
                pub_key.verify(
                    encode_dss_signature(r, s),
                    message_hash,
                    ec.ECDSA(hashes.SHA256())
                )
                return True, "Signature valid"
            except InvalidSignature:
                return False, "Signature verification failed (invalid signature)"
            except Exception as e:
                logger.error(f"Signature verification error: {e}")
                return False, f"Signature verification error: {str(e)}"
                
        except Exception as e:
            logger.error(f"ECDSA signature verification failed: {e}")
            return False, f"Signature verification failed: {str(e)}"
    
    def _is_cache_recent(self) -> bool:
        """Check if cache is recent (within validity period)"""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            validated_at = cache.get('validated_at', 0)
            days_since_validation = (time.time() - validated_at) / 86400
            return days_since_validation < self.CACHE_VALIDITY_DAYS
        except Exception:
            return False
    
    def get_license_data(self) -> Optional[Dict[str, Any]]:
        """Get current license data (for diagnostic purposes)"""
        # Try account-based first
        is_valid, _, license_info = self._validate_account_based_license()
        if is_valid and license_info:
            return license_info
        
        # Fallback to file-based
        return self.load_cached_license()
    
    def _is_within_grace_period(self) -> bool:
        """Check if last successful validation is within grace period"""
        if not self.last_validation_file.exists():
            return False
        
        try:
            with open(self.last_validation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            last_validation_time = data.get('last_validation_time', 0)
            days_since_validation = (time.time() - last_validation_time) / 86400
            return days_since_validation < self.GRACE_PERIOD_DAYS
        except Exception as e:
            logger.error(f"Error checking grace period: {e}")
            return False
    
    def _get_last_validation_time(self) -> Optional[float]:
        """Get timestamp of last successful validation"""
        if not self.last_validation_file.exists():
            return None
        
        try:
            with open(self.last_validation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('last_validation_time')
        except Exception as e:
            logger.error(f"Error reading last validation time: {e}")
            return None
    
    def _update_validation_time(self) -> None:
        """Update timestamp of last successful validation"""
        try:
            data = {
                'last_validation_time': time.time(),
                'device_id': self.get_device_id(),
            }
            with open(self.last_validation_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating validation time: {e}")
    
    def _get_cached_license_info(self) -> Optional[Dict[str, Any]]:
        """Get cached license info from last successful validation"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            # Try both keys for compatibility
            return cache.get('license_info') or cache.get('license_data')
        except Exception as e:
            logger.error(f"Error reading cached license info: {e}")
            return None
    
    def _save_cached_license_info(self, license_info: Dict[str, Any]) -> None:
        """Save license info to cache for grace period"""
        try:
            cache_data = {
                'license_info': license_info,
                'cached_at': time.time(),
                'device_id': self.get_device_id(),
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cached license info: {e}")

