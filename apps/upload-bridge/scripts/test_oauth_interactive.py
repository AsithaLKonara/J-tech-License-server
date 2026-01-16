#!/usr/bin/env python3
"""
Interactive OAuth Login Test

This script provides an interactive OAuth login test with better feedback
and manual steps if needed.

Usage:
    python scripts/test_oauth_interactive.py
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.auth_manager import AuthManager
from core.license_manager import LicenseManager
from core.oauth_handler import run_oauth_flow, OAuthConfig, build_auth_url, generate_pkce_pair
import secrets
import webbrowser

def test_oauth_interactive():
    """Interactive OAuth login test with step-by-step feedback."""
    
    print("=" * 70)
    print("Interactive OAuth Login Test")
    print("=" * 70)
    print()
    
    # Load configuration
    config = get_config()
    auth_server_url = config.get("auth_server_url", "https://j-tech-license-server-production.up.railway.app")
    
    print(f"📡 License Server URL: {auth_server_url}")
    print()
    
    # Check Auth0 configuration
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    auth0_audience = config.get("auth0_audience") or config.get("auth_audience")
    
    if not auth0_domain or not auth0_client_id:
        print("❌ Auth0 not configured!")
        print("   Set AUTH0_DOMAIN and AUTH0_CLIENT_ID in config or environment")
        return False
    
    print(f"✅ Auth0 Configuration:")
    print(f"   Domain: {auth0_domain}")
    print(f"   Client ID: {auth0_client_id}")
    if auth0_audience:
        print(f"   Audience: {auth0_audience}")
    print()
    
    # Create OAuth config
    oauth_config = OAuthConfig(
        auth_domain=auth0_domain,
        client_id=auth0_client_id,
        client_secret=config.get("auth0_client_secret"),
        audience=auth0_audience,
        scope="openid profile email offline_access",
        timeout=600  # 10 minutes for manual testing
    )
    
    # Generate PKCE and state
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    
    # Build authorization URL
    redirect_uri = "http://127.0.0.1:5000/callback"
    auth_url = build_auth_url(oauth_config, redirect_uri, state, code_challenge)
    
    print("🔐 OAuth Flow Setup")
    print("-" * 70)
    print(f"📋 Authorization URL:")
    print(f"   {auth_url}")
    print()
    print(f"📋 Redirect URI: {redirect_uri}")
    print(f"📋 State: {state[:20]}...")
    print()
    
    # Check if callback URL is configured
    print("⚠️  IMPORTANT: Make sure the callback URL is configured in Auth0!")
    print(f"   Callback URL: {redirect_uri}")
    print()
    
    response = input("Press Enter to open browser for Auth0 login (or 'q' to quit): ")
    if response.lower() == 'q':
        print("Test cancelled.")
        return False
    
    print()
    print("🌐 Opening browser...")
    print("   Please complete the login in the browser window.")
    print("   After login, you will be redirected back to the application.")
    print()
    
    # Open browser
    try:
        webbrowser.open(auth_url)
        print("✅ Browser opened. Please complete the login.")
        print()
        print("⏳ Waiting for callback...")
        print("   (This may take a few minutes - complete the login in the browser)")
        print()
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print()
        print("📋 Please manually open this URL in your browser:")
        print(f"   {auth_url}")
        print()
    
    # Run OAuth flow
    print("🔄 Starting OAuth callback server...")
    result = run_oauth_flow(oauth_config)
    
    if not result.success:
        print()
        print(f"❌ OAuth flow failed: {result.message}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Make sure you completed the login in the browser")
        print(f"   2. Verify callback URL is configured in Auth0: {redirect_uri}")
        print("   3. Check that port 5000 is not blocked by firewall")
        print("   4. Try running the test again")
        return False
    
    print()
    print("✅ OAuth flow successful!")
    print(f"   Received tokens: {list(result.tokens.keys())}")
    print()
    
    # Extract access token
    access_token = result.tokens.get("access_token")
    if not access_token:
        print("❌ No access token in OAuth response")
        print(f"   Response: {result.tokens}")
        return False
    
    print(f"✅ Access Token: {access_token[:50]}...")
    print()
    print("🔑 Exchanging Auth0 token for session/entitlement tokens...")
    print()
    
    # Create AuthManager and login
    auth_manager = AuthManager(server_url=auth_server_url)
    success, message = auth_manager.login(access_token)
    
    if not success:
        print(f"❌ Login to license server failed: {message}")
        return False
    
    print("✅ Login to license server successful!")
    print()
    
    # Verify tokens
    if auth_manager.session_token:
        print(f"✅ Session Token: {auth_manager.session_token[:50]}...")
    else:
        print("❌ No session token")
        return False
    
    if auth_manager.entitlement_token:
        print(f"✅ Entitlement Token:")
        print(f"   Plan: {auth_manager.entitlement_token.get('plan', 'N/A')}")
        print(f"   Features: {auth_manager.entitlement_token.get('features', [])}")
        print(f"   Product: {auth_manager.entitlement_token.get('product', 'N/A')}")
        expires_at = auth_manager.entitlement_token.get('expires_at')
        if expires_at:
            from datetime import datetime
            exp_date = datetime.fromtimestamp(expires_at)
            print(f"   Expires: {exp_date}")
        else:
            print(f"   Expires: Never (perpetual)")
    else:
        print("❌ No entitlement token")
        return False
    
    if auth_manager.user_info:
        print(f"✅ User Info:")
        print(f"   Email: {auth_manager.user_info.get('email', 'N/A')}")
        print(f"   ID: {auth_manager.user_info.get('id', 'N/A')}")
    
    print()
    print("🔍 Testing License Validation...")
    print()
    
    # Test license validation
    license_manager = LicenseManager.instance(server_url=auth_server_url)
    is_valid, message, license_info = license_manager.validate_license()
    
    if is_valid and license_info:
        print(f"✅ License Validation: {message}")
        print(f"   Source: {license_info.get('source', 'N/A')}")
        license_obj = license_info.get('license', {})
        print(f"   Plan: {license_obj.get('plan', 'N/A')}")
        print(f"   Features: {license_obj.get('features', [])}")
    else:
        print(f"❌ License Validation Failed: {message}")
    
    print()
    print("=" * 70)
    print("✅ OAuth Login Test Complete!")
    print("=" * 70)
    print()
    print("📝 Summary:")
    print("   ✅ OAuth flow completed")
    print("   ✅ Auth0 token received")
    print("   ✅ License server login successful")
    print("   ✅ Session and entitlement tokens received")
    if is_valid:
        print("   ✅ License validation successful")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_oauth_interactive()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

