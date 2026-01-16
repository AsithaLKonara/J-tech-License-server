"""
Project File Encryption - Optional encryption for .ledproj files

Provides optional encryption for project files (enterprise feature).
"""

from pathlib import Path
from typing import Optional
import json
import base64

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None


class ProjectEncryption:
    """
    Optional encryption for project files.
    
    Uses Fernet (symmetric encryption) with password-derived key.
    """
    
    @staticmethod
    def is_available() -> bool:
        """Check if encryption is available (cryptography library installed)"""
        return CRYPTO_AVAILABLE
    
    @staticmethod
    def encrypt_project(
        project_data: dict,
        password: str,
        output_path: Path
    ) -> bool:
        """
        Encrypt project file.
        
        Args:
            project_data: Project data dictionary
            password: Encryption password
            output_path: Path to save encrypted file
            
        Returns:
            True if encryption successful
        """
        if not CRYPTO_AVAILABLE:
            return False
        
        try:
            # Derive key from password
            password_bytes = password.encode('utf-8')
            salt = b'upload_bridge_salt'  # In production, use random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            fernet = Fernet(key)
            
            # Serialize project data
            json_data = json.dumps(project_data, ensure_ascii=False)
            encrypted_data = fernet.encrypt(json_data.encode('utf-8'))
            
            # Save encrypted file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def decrypt_project(
        encrypted_path: Path,
        password: str
    ) -> Optional[dict]:
        """
        Decrypt project file.
        
        Args:
            encrypted_path: Path to encrypted file
            password: Decryption password
            
        Returns:
            Project data dictionary or None if decryption fails
        """
        if not CRYPTO_AVAILABLE:
            return None
        
        try:
            # Read encrypted data
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Derive key from password
            password_bytes = password.encode('utf-8')
            salt = b'upload_bridge_salt'  # Must match encryption salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            fernet = Fernet(key)
            
            # Decrypt
            decrypted_data = fernet.decrypt(encrypted_data)
            project_data = json.loads(decrypted_data.decode('utf-8'))
            
            return project_data
        except Exception:
            return None

