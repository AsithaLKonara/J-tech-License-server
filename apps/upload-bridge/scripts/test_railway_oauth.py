"""
Test OAuth Flow with Railway License Server

This script tests the complete OAuth flow:
1. OAuth login via Auth0
2. Exchange Auth0 token for session/entitlement tokens
3. Verify license server integration
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.auth_manager import AuthManager
from core.oauth_handler import run_oauth_flow, OAuthConfig

def test_oauth_flow():
    """Test the complete OAuth flow with Railway license server."""
    
    print("=" * 60)
    print("Testing OAuth Flow with Railway License Server")
    print("=" * 60)
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
        timeout=300
    )
    
    print("🔐 Starting OAuth flow...")
    print("   This will open your browser for Auth0 login")
    print()
    
    # Run OAuth flow
    result = run_oauth_flow(oauth_config)
    
    if not result.success:
        print(f"❌ OAuth flow failed: {result.message}")
        return False
    
    print("✅ OAuth flow successful!")
    print(f"   Received tokens: {list(result.tokens.keys())}")
    print()
    
    # Extract access token
    access_token = result.tokens.get("access_token")
    if not access_token:
        print("❌ No access token in OAuth response")
        return False
    
    print("🔑 Exchanging Auth0 token for session/entitlement tokens...")
    print()
    
    # Create AuthManager and login
    auth_manager = AuthManager(server_url=auth_server_url)
    success, message = auth_manager.login(access_token)
    
    if not success:
        print(f"❌ Login failed: {message}")
        return False
    
    print("✅ Login successful!")
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
    else:
        print("❌ No entitlement token")
        return False
    
    if auth_manager.user_info:
        print(f"✅ User Info:")
        print(f"   Email: {auth_manager.user_info.get('email', 'N/A')}")
        print(f"   ID: {auth_manager.user_info.get('id', 'N/A')}")
    
    print()
    print("=" * 60)
    print("✅ OAuth Flow Test Complete - All Checks Passed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_oauth_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

