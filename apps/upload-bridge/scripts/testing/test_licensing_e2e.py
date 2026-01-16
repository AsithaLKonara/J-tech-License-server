"""End-to-end smoke test for enterprise licensing.

This script is intended to be run manually during development to verify
that the core licensing flow works end-to-end:

1. License server is running (npm run dev:backend in monorepo root)
2. Desktop app can hit /api/health
3. Enterprise endpoints respond as expected
"""

from __future__ import annotations

import os
from typing import Dict, Any

import requests

BASE_URL = os.getenv("LICENSE_SERVER_URL", "http://localhost:3000")


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=10, **kwargs)


def _post(path: str, json: Dict[str, Any] | None = None, **kwargs) -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", json=json, timeout=10, **kwargs)


def main() -> None:
    print(f"Using license server: {BASE_URL}")

    # 1. Health check
    print("1) Checking /api/health...")
    resp = _get("/api/health")
    print("   status:", resp.status_code)
    print("   body:", resp.json())

    # 2. Feature flags without auth
    print("2) Checking /api/v2/features/check (no auth)...")
    resp = _post("/api/v2/features/check", json={"features": ["pattern_upload", "wifi_upload"]})
    print("   status:", resp.status_code)
    try:
        print("   body:", resp.json())
    except Exception:
        print("   body (non-JSON):", resp.text)

    # 3. Updates check
    print("3) Checking /api/v2/updates/check...")
    resp = _get("/api/v2/updates/check?current_version=0.0.0")
    print("   status:", resp.status_code)
    try:
        print("   body:", resp.json())
    except Exception:
        print("   body (non-JSON):", resp.text)

    print("\nE2E smoke test finished. For full auth + Stripe flows, run manual tests.")


if __name__ == "__main__":
    main()
