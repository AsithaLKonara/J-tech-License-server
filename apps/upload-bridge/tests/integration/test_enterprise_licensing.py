"""Integration tests for enterprise licensing system.

These tests are designed to be run against a running license server
instance (e.g. `npm run dev:backend` in monorepo root). They perform basic
smoke checks of the enterprise endpoints.
"""

import os
import time
from typing import Dict, Any

import requests

BASE_URL = os.getenv("LICENSE_SERVER_URL", "http://localhost:3000")


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=10, **kwargs)


def _post(path: str, json: Dict[str, Any] | None = None, **kwargs) -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", json=json, timeout=10, **kwargs)


def test_health_endpoint():
    """Server health endpoint should respond with basic status info."""
    resp = _get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"
    assert "version" in data


def test_entitlements_requires_auth():
    """Entitlements endpoint should require authentication."""
    resp = _get("/api/v2/entitlements/current")
    assert resp.status_code in (401, 403)


def test_features_check_works_without_auth():
    """Feature flags endpoint should work without auth and return flags dict."""
    resp = _post("/api/v2/features/check", json={"features": ["pattern_upload", "wifi_upload"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "flags" in data
    assert isinstance(data["flags"], dict)


def test_updates_check():
    """Updates check should respond even without auth."""
    resp = _get("/api/v2/updates/check?current_version=0.0.0")
    # May return 200 or 401 depending on config; allow both but require JSON
    assert resp.status_code in (200, 401, 403)
    # If 200, must have JSON body
    if resp.status_code == 200:
        data = resp.json()
        assert "latest_version" in data


def test_rate_limiting_metadata():
    """Hitting an endpoint many times should eventually show rate limiting or still be stable.

    This is a light-touch check to ensure /api/v2/features/check doesn't
    crash or misbehave under repeated calls.
    """
    for _ in range(5):
        resp = _post("/api/v2/features/check", json={"features": ["pattern_upload"]})
        assert resp.status_code in (200, 429)
        time.sleep(0.1)


def test_admin_migrate_license_endpoint_shape():
    """
    Admin migrate-license endpoint should exist and validate payload shape.

    This does not require a real Auth0 token; we only check that the endpoint
    is present and responds with a useful error when unauthenticated.
    """
    resp = _post(
        "/api/v2/admin/migrate-license",
        json={"userEmail": "user@example.com", "licenseData": {"product_id": "upload_bridge_pro"}},
    )
    # Without auth we expect 401/403, but not 404
    assert resp.status_code in (401, 403)
