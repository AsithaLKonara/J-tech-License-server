from __future__ import annotations

import json
import os
import time
from pathlib import Path

from core.license_manager import LicenseManager


def _make_temp_manager(tmp_path: Path) -> LicenseManager:
    """
    Create a LicenseManager instance whose cache/encrypted paths live under tmp_path,
    so tests do not touch the real user cache in ~/.upload_bridge.
    """
    mgr = LicenseManager(server_url="http://invalid-server-for-tests")
    # Redirect cache locations into a temporary directory
    mgr.ENCRYPTED_LICENSE_DIR = tmp_path
    mgr.cache_file = tmp_path / "license_cache.json"
    mgr.encrypted_license_file = tmp_path / "license.enc"
    return mgr


def _basic_license_payload() -> dict:
    return {
        "license": {
            "license_id": "TEST-LICENSE",
            "product_id": "upload_bridge_pro",
            "issued_to_email": "test@example.com",
            "issued_at": "2025-01-01T00:00:00Z",
            "expires_at": None,
            "features": ["pro"],
            "version": 1,
            "max_devices": 1,
        },
        "signature": None,
        "public_key": None,
        "format_version": "1.0",
    }


def test_load_cached_license_prefers_encrypted(tmp_path) -> None:
    mgr = _make_temp_manager(tmp_path)
    payload = _basic_license_payload()

    # Save an encrypted license and a cache file; load_cached_license should return
    # the decrypted payload from the encrypted file, not the cache.
    assert mgr.save_license(payload, validate_online=False)

    # Manually tamper with cache file to ensure encrypted data is preferred.
    if mgr.cache_file.exists():
        with open(mgr.cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        cache["license_data"]["license_id"] = "CACHE-LICENSE"
        with open(mgr.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f)

    loaded = mgr.load_cached_license()
    assert loaded is not None
    assert loaded["license"]["license_id"] == "TEST-LICENSE"


def test_validate_license_uses_cache_when_recent(tmp_path, monkeypatch) -> None:
    mgr = _make_temp_manager(tmp_path)
    payload = _basic_license_payload()
    assert mgr.save_license(payload, validate_online=False)

    # Force cache to look "recent"
    now = time.time()
    with open(mgr.cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)
    cache["validated_at"] = now
    with open(mgr.cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    # Make server validation always fail; validate_license should still pass due to cache.
    def fake_validate_with_server(_license_data):
        return False, "Server unreachable"

    monkeypatch.setattr(mgr, "validate_with_server", fake_validate_with_server)

    ok, message, _info = mgr.validate_license(force_online=False)
    assert ok
    assert "offline mode" in message or "valid" in message.lower()


def test_validate_license_requires_online_when_cache_stale(tmp_path, monkeypatch) -> None:
    mgr = _make_temp_manager(tmp_path)
    payload = _basic_license_payload()
    assert mgr.save_license(payload, validate_online=False)

    # Mark cache as very old
    old_time = time.time() - (mgr.CACHE_VALIDITY_DAYS + 1) * 86400
    with open(mgr.cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)
    cache["validated_at"] = old_time
    with open(mgr.cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    # Simulate server being unavailable
    def fake_validate_with_server(_license_data):
        raise RuntimeError("server down")

    monkeypatch.setattr(mgr, "validate_with_server", fake_validate_with_server)

    ok, message, _info = mgr.validate_license(force_online=False)
    assert not ok
    assert "online validation required" in message.lower()


