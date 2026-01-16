"""
Unit tests for ECDSA signature verification in LicenseManager
"""

import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import hashlib

from core.license_manager import LicenseManager


def _make_temp_manager(tmp_path: Path) -> LicenseManager:
    """Create a LicenseManager instance with temporary directories."""
    mgr = LicenseManager(server_url="http://invalid-server-for-tests")
    mgr.ENCRYPTED_LICENSE_DIR = tmp_path
    mgr.cache_file = tmp_path / "license_cache.json"
    mgr.encrypted_license_file = tmp_path / "license.enc"
    mgr.ENCRYPTED_LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    return mgr


def _create_test_license_data() -> dict:
    """Create a test license data structure."""
    return {
        "license": {
            "license_id": "TEST-LICENSE-ECDSA",
            "product_id": "upload_bridge_pro",
            "issued_to_email": "test@example.com",
            "issued_at": "2025-01-01T00:00:00Z",
            "expires_at": None,
            "features": ["pro"],
            "version": 1,
            "max_devices": 1,
        },
        "format_version": "1.0",
    }


def _sign_license_data(license_data: dict, private_key: ec.EllipticCurvePrivateKey) -> str:
    """Sign license data with private key and return base64-encoded signature."""
    # Create message (license data without signature and public_key)
    message_data = {k: v for k, v in license_data.items() if k not in ('signature', 'public_key')}
    message_json = json.dumps(message_data, sort_keys=True)
    message_bytes = message_json.encode('utf-8')
    
    # Hash the message
    message_hash = hashlib.sha256(message_bytes).digest()
    
    # Sign
    signature = private_key.sign(message_hash, ec.ECDSA(hashes.SHA256()))
    
    # Encode as base64
    return base64.b64encode(signature).decode('utf-8')


def _get_public_key_pem(public_key: ec.EllipticCurvePublicKey) -> str:
    """Get PEM-encoded public key."""
    return public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')


def _get_public_key_der_base64(public_key: ec.EllipticCurvePublicKey) -> str:
    """Get base64-encoded DER public key."""
    der_bytes = public_key.public_bytes(
        encoding=Encoding.DER,
        format=PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(der_bytes).decode('utf-8')


def test_ecdsa_signature_verification_valid_pem(tmp_path):
    """Test ECDSA signature verification with valid PEM public key."""
    mgr = _make_temp_manager(tmp_path)
    
    # Generate key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Create license data
    license_data = _create_test_license_data()
    
    # Sign license data
    signature = _sign_license_data(license_data, private_key)
    public_key_pem = _get_public_key_pem(public_key)
    
    # Add signature and public key to license data
    license_data['signature'] = signature
    license_data['public_key'] = public_key_pem
    
    # Verify signature
    is_valid, message = mgr._verify_ecdsa_signature(license_data, signature, public_key_pem)
    
    assert is_valid, f"Signature verification should pass, but got: {message}"
    assert "valid" in message.lower()


def test_ecdsa_signature_verification_valid_der_base64(tmp_path):
    """Test ECDSA signature verification with valid base64-encoded DER public key."""
    mgr = _make_temp_manager(tmp_path)
    
    # Generate key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Create license data
    license_data = _create_test_license_data()
    
    # Sign license data
    signature = _sign_license_data(license_data, private_key)
    public_key_der_b64 = _get_public_key_der_base64(public_key)
    
    # Add signature and public key to license data
    license_data['signature'] = signature
    license_data['public_key'] = public_key_der_b64
    
    # Verify signature
    is_valid, message = mgr._verify_ecdsa_signature(license_data, signature, public_key_der_b64)
    
    assert is_valid, f"Signature verification should pass, but got: {message}"
    assert "valid" in message.lower()


def test_ecdsa_signature_verification_invalid_signature(tmp_path):
    """Test ECDSA signature verification with invalid signature."""
    mgr = _make_temp_manager(tmp_path)
    
    # Generate key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Create license data
    license_data = _create_test_license_data()
    
    # Sign license data
    signature = _sign_license_data(license_data, private_key)
    public_key_pem = _get_public_key_pem(public_key)
    
    # Tamper with signature
    tampered_signature = base64.b64encode(b"invalid_signature_data").decode('utf-8')
    
    # Add signature and public key to license data
    license_data['signature'] = tampered_signature
    license_data['public_key'] = public_key_pem
    
    # Verify signature (should fail)
    is_valid, message = mgr._verify_ecdsa_signature(license_data, tampered_signature, public_key_pem)
    
    assert not is_valid, "Signature verification should fail for invalid signature"
    assert any(word in message.lower() for word in ["invalid", "failed", "unsupported", "error"])


def test_ecdsa_signature_verification_wrong_key(tmp_path):
    """Test ECDSA signature verification with wrong public key."""
    mgr = _make_temp_manager(tmp_path)
    
    # Generate two key pairs
    private_key1 = ec.generate_private_key(ec.SECP256R1())
    private_key2 = ec.generate_private_key(ec.SECP256R1())
    public_key2 = private_key2.public_key()
    
    # Create license data
    license_data = _create_test_license_data()
    
    # Sign license data with key1
    signature = _sign_license_data(license_data, private_key1)
    
    # Use public key from key2 (wrong key)
    public_key_pem = _get_public_key_pem(public_key2)
    
    # Add signature and public key to license data
    license_data['signature'] = signature
    license_data['public_key'] = public_key_pem
    
    # Verify signature (should fail)
    is_valid, message = mgr._verify_ecdsa_signature(license_data, signature, public_key_pem)
    
    assert not is_valid, "Signature verification should fail with wrong public key"
    assert "invalid" in message.lower() or "failed" in message.lower()


def test_ecdsa_signature_verification_tampered_data(tmp_path):
    """Test ECDSA signature verification with tampered license data."""
    mgr = _make_temp_manager(tmp_path)
    
    # Generate key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Create license data
    license_data = _create_test_license_data()
    
    # Sign license data
    signature = _sign_license_data(license_data, private_key)
    public_key_pem = _get_public_key_pem(public_key)
    
    # Tamper with license data
    license_data['license']['license_id'] = 'TAMPERED-LICENSE'
    
    # Add signature and public key to license data
    license_data['signature'] = signature
    license_data['public_key'] = public_key_pem
    
    # Verify signature (should fail because data was tampered)
    is_valid, message = mgr._verify_ecdsa_signature(license_data, signature, public_key_pem)
    
    assert not is_valid, "Signature verification should fail for tampered data"
    assert "invalid" in message.lower() or "failed" in message.lower()


def test_ecdsa_signature_verification_invalid_public_key(tmp_path):
    """Test ECDSA signature verification with invalid public key format."""
    mgr = _make_temp_manager(tmp_path)
    
    # Create license data
    license_data = _create_test_license_data()
    signature = "dummy_signature"
    invalid_public_key = "not_a_valid_public_key"
    
    # Verify signature (should fail)
    is_valid, message = mgr._verify_ecdsa_signature(license_data, signature, invalid_public_key)
    
    assert not is_valid, "Signature verification should fail for invalid public key"
    assert "invalid" in message.lower() or "format" in message.lower()


def test_ecdsa_signature_verification_missing_signature(tmp_path):
    """Test that license validation works when signature is missing."""
    mgr = _make_temp_manager(tmp_path)
    
    # Create license data without signature
    license_data = _create_test_license_data()
    license_data['license']['device_id'] = mgr.get_device_id()
    license_data['integrity_hash'] = mgr._calculate_integrity_hash(license_data)
    
    # Validate (should pass because signature is optional)
    is_valid, message = mgr._validate_license_locally(license_data)
    
    assert is_valid, f"License should be valid without signature, but got: {message}"


def test_ecdsa_signature_verification_integration(tmp_path):
    """Test ECDSA signature verification integrated with license validation."""
    mgr = _make_temp_manager(tmp_path)
    
    # Generate key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Create license data
    license_data = _create_test_license_data()
    license_data['license']['device_id'] = mgr.get_device_id()
    license_data['integrity_hash'] = mgr._calculate_integrity_hash(license_data)
    
    # Sign license data
    signature = _sign_license_data(license_data, private_key)
    public_key_pem = _get_public_key_pem(public_key)
    
    # Add signature and public key
    license_data['signature'] = signature
    license_data['public_key'] = public_key_pem
    
    # Validate license (should pass)
    is_valid, message = mgr._validate_license_locally(license_data)
    
    assert is_valid, f"License validation should pass with valid signature, but got: {message}"
