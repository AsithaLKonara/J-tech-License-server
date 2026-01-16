"""OAuth handler for browser-based Auth0 login (PKCE + local callback).

This module provides a small HTTP server to receive the OAuth redirect
and helper functions to perform the authorization-code-with-PKCE flow
for desktop apps.

High-level flow:

1. Generate code_verifier and code_challenge (PKCE)
2. Start local HTTP server on 127.0.0.1:<random_port>
3. Build Auth0 authorize URL with redirect_uri=http://127.0.0.1:<port>/callback
4. Open browser to the authorize URL
5. Local server receives /callback?code=...&state=...
6. Exchange authorization code for tokens at Auth0 /oauth/token
7. Return token response to caller

Note: This is a generic implementation; concrete Auth0 parameters
(client_id, domain, audience, scopes) are passed in from the caller.
"""

from __future__ import annotations

import http.server
import socket
import threading
import time
import secrets
import base64
import hashlib
import urllib.parse
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

import requests


@dataclass
class OAuthConfig:
    """Configuration for OAuth/PKCE flow.

    Attributes:
        auth_domain: Auth0 domain, e.g. "your-tenant.auth0.com"
        client_id: Auth0 client ID
        client_secret: Optional client secret (may not be needed with PKCE)
        audience: API audience (for access token)
        scope: OAuth scopes, e.g. "openid profile email offline_access"
        timeout: Total timeout for the whole flow (seconds)
    """

    auth_domain: str
    client_id: str
    client_secret: Optional[str] = None
    audience: Optional[str] = None
    scope: str = "openid profile email offline_access"
    timeout: int = 300


@dataclass
class OAuthResult:
    """Result of the OAuth flow."""

    success: bool
    message: str
    tokens: Dict[str, Any]


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    """Internal HTTP handler to capture the OAuth callback.

    It stores the received query params on the parent server instance.
    """

    # Reference to parent server set at runtime
    def do_GET(self):  # type: ignore[override]
        # We only care about /callback
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        query = urllib.parse.parse_qs(parsed.query)
        # Store on server for retrieval
        self.server.oauth_query = query  # type: ignore[attr-defined]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Login complete</h1>"
            b"<p>You can close this window and return to Upload Bridge.</p>"
            b"</body></html>"
        )

    # Suppress noisy logging
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class OAuthCallbackServer:
    """Small HTTP server to receive the OAuth redirect callback."""

    def __init__(self) -> None:
        self._server: Optional[http.server.HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._query: Optional[Dict[str, Any]] = None

    def _find_free_port(self) -> int:
        # Use a fixed port since Auth0 does not allow wildcards for dynamic ports.
        # Ensure this port is available on the user's system.
        return 5000 # Example fixed port

    def start(self) -> str:
        """Start the callback server and return the redirect_uri."""
        port = self._find_free_port()
        self._server = http.server.HTTPServer(("127.0.0.1", port), _CallbackHandler)
        # Attach storage for query params
        self._server.oauth_query = None  # type: ignore[attr-defined]

        def _run() -> None:
            try:
                self._server.serve_forever()
            except Exception:
                pass

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        return f"http://127.0.0.1:{port}/callback"

    def wait_for_callback(self, timeout: int = 300) -> Tuple[bool, Dict[str, Any]]:
        """Wait until callback is received or timeout.

        Returns: (success, query_params)
        """
        if not self._server:
            return False, {}

        deadline = time.time() + timeout
        while time.time() < deadline:
            query = getattr(self._server, "oauth_query", None)  # type: ignore[attr-defined]
            if query is not None:
                self._query = query
                break
            time.sleep(0.25)

        # Stop server
        try:
            self._server.shutdown()
        except Exception:
            pass

        if not self._query:
            return False, {}
        return True, self._query


def generate_pkce_pair() -> Tuple[str, str]:
    """Generate (code_verifier, code_challenge) for PKCE."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_auth_url(config: OAuthConfig, redirect_uri: str, state: str, code_challenge: str) -> str:
    """Build the Auth0 authorize URL for browser-based login."""
    base = f"https://{config.auth_domain}/authorize"
    params = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "scope": config.scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if config.audience:
        params["audience"] = config.audience
    return f"{base}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    config: OAuthConfig,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> OAuthResult:
    """Exchange authorization code for tokens using Auth0 /oauth/token endpoint."""
    token_url = f"https://{config.auth_domain}/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": config.client_id,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    if config.client_secret:
        data["client_secret"] = config.client_secret
    if config.audience:
        data["audience"] = config.audience

    try:
        resp = requests.post(token_url, data=data, timeout=10)
        if resp.status_code != 200:
            try:
                err = resp.json()
            except Exception:
                err = {"error": resp.text}
            return OAuthResult(False, f"Token request failed: {err}", {})
        tokens = resp.json()
        return OAuthResult(True, "OK", tokens)
    except requests.RequestException as e:
        return OAuthResult(False, f"Network error: {e}", {})


def run_oauth_flow(config: OAuthConfig) -> OAuthResult:
    """Run the full browser-based OAuth flow and return tokens.

    This function opens the browser to Auth0 Universal Login, then waits
    for the local callback and exchanges the authorization code for
    tokens. It can be called from the UI thread for simplicity, or from
    a background thread for better responsiveness.
    """
    import webbrowser

    # 1. Start callback server
    callback_server = OAuthCallbackServer()
    redirect_uri = callback_server.start()

    # 2. Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()

    # 3. Generate state
    state = secrets.token_urlsafe(16)

    # 4. Build auth URL and open in browser
    auth_url = build_auth_url(config, redirect_uri, state, code_challenge)
    webbrowser.open(auth_url)

    # Wait for callback
    ok, query = callback_server.wait_for_callback(timeout=config.timeout)
    if not ok:
        return OAuthResult(False, "Timeout waiting for OAuth callback", {})

    # Validate state
    received_state = query.get("state", [None])[0]
    if received_state != state:
        return OAuthResult(False, "Invalid state received in callback", {})

    # Get code or error
    if "error" in query:
        err = query.get("error", [""])[0]
        desc = query.get("error_description", [""])[0]
        return OAuthResult(False, f"OAuth error: {err} {desc}", {})

    code = query.get("code", [None])[0]
    if not code:
        return OAuthResult(False, "No authorization code in callback", {})

    # Exchange for tokens
    token_result = exchange_code_for_tokens(config, code, redirect_uri, code_verifier)
    if not token_result.success:
        return token_result

    # Attach auth_url for debugging/telemetry if desired
    token_result.tokens.setdefault("_meta", {})["auth_url"] = auth_url
    return token_result
