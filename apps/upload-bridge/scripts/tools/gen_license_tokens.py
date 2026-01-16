#!/usr/bin/env python3
"""
Generate signed offline license tokens (Ed25519).

Usage (one-time):
  python tools/gen_license_tokens.py --generate-keypair
  python tools/gen_license_tokens.py --sign --private-key private_key.pem --license-id ULBP-XXXX-.... --product upload_bridge_pro --features pattern_upload wifi_upload --expires 2026-01-01T00:00:00Z

Token format:
  base64url(payload_json).base64url(signature)

Place public_key.pem under config/ and distribute tokens to users.
"""
from __future__ import annotations

import argparse
import base64
import json
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=") .decode("ascii")


def generate_keypair():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open("private_key.pem", "wb") as f:
        f.write(priv_pem)
    with open("public_key.pem", "wb") as f:
        f.write(pub_pem)
    print("Generated private_key.pem and public_key.pem")


def sign_token(private_key_path: str, license_id: str, product: str, features: list[str], expires: str | None):
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    payload = {
        "license_id": license_id,
        "product_id": product,
        "features": features,
        "expires_at": expires,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = private_key.sign(payload_bytes)
    token = f"{b64url(payload_bytes)}.{b64url(sig)}"
    print(token)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate-keypair", action="store_true", help="Generate Ed25519 keypair")
    ap.add_argument("--sign", action="store_true", help="Sign a token")
    ap.add_argument("--private-key", help="Path to private key")
    ap.add_argument("--license-id", help="License ID string")
    ap.add_argument("--product", default="upload_bridge_pro")
    ap.add_argument("--features", nargs="*", default=["pattern_upload", "wifi_upload"])
    ap.add_argument("--expires", default=None, help="ISO8601 timestamp or omit for perpetual")
    args = ap.parse_args()

    if args.generate_keypair:
        generate_keypair()
        return
    if args.sign:
        if not args.private_key or not args.license_id:
            ap.error("--private-key and --license-id are required for --sign")
        sign_token(args.private_key, args.license_id, args.product, args.features, args.expires)
        return
    ap.print_help()


if __name__ == "__main__":
    main()


