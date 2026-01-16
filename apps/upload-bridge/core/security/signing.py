"""
Project File Signing - Digital signatures for project files

Provides optional signing for project files to detect tampering.
"""

from pathlib import Path
from typing import Optional, Tuple
import json
import base64

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    rsa = None
    padding = None


class ProjectSigning:
    """
    Digital signature for project files.
    
    Uses RSA-PSS signing for tamper detection.
    """
    
    @staticmethod
    def is_available() -> bool:
        """Check if signing is available"""
        return CRYPTO_AVAILABLE
    
    @staticmethod
    def generate_key_pair() -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair for signing.
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        # Generate 2048-bit RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return (private_pem, public_pem)
    
    @staticmethod
    def sign_project(
        project_data: dict,
        private_key_pem: bytes
    ) -> dict:
        """
        Sign project file with private key.
        
        Args:
            project_data: Project data dictionary
            private_key_pem: Private key in PEM format
            
        Returns:
            Project data dictionary with signature
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )
        
        # Serialize project data (without signature)
        project_data_no_sig = {k: v for k, v in project_data.items() if k != "signature"}
        json_data = json.dumps(project_data_no_sig, sort_keys=True, separators=(',', ':')).encode('utf-8')
        
        # Sign data
        signature = private_key.sign(
            json_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Add signature to project data
        project_data["signature"] = {
            "algorithm": "RSA-PSS-SHA256",
            "value": base64.b64encode(signature).decode('ascii')
        }
        
        return project_data
    
    @staticmethod
    def verify_project(
        project_data: dict,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify project file signature.
        
        Args:
            project_data: Project data dictionary with signature
            public_key_pem: Public key in PEM format
            
        Returns:
            True if signature is valid
        """
        if not CRYPTO_AVAILABLE:
            return False
        
        # Extract signature
        signature_data = project_data.get("signature")
        if not signature_data:
            return False
        
        signature_b64 = signature_data.get("value")
        if not signature_b64:
            return False
        
        signature = base64.b64decode(signature_b64)
        
        # Load public key
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        # Prepare data for verification (without signature)
        project_data_no_sig = {k: v for k, v in project_data.items() if k != "signature"}
        json_data = json.dumps(project_data_no_sig, sort_keys=True, separators=(',', ':')).encode('utf-8')
        
        # Verify signature
        try:
            public_key.verify(
                signature,
                json_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def remove_signature(project_data: dict) -> dict:
        """
        Remove signature from project data.
        
        Args:
            project_data: Project data with signature
            
        Returns:
            Project data without signature
        """
        return {k: v for k, v in project_data.items() if k != "signature"}

