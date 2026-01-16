#!/usr/bin/env python3
"""
Verify Auth0 Setup and Configuration

This script verifies:
1. Configuration is correct
2. Auth0 endpoints are accessible
3. Application settings checklist
4. Callback URL configuration
"""

import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.oauth_handler import build_auth_url, generate_pkce_pair, OAuthConfig
import secrets

def verify_config():
    """Verify configuration is correct"""
    print("=" * 70)
    print("Configuration Verification")
    print("=" * 70)
    print()
    
    config = get_config()
    
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    auth0_audience = config.get("auth0_audience") or config.get("auth_audience")
    server_url = config.get("auth_server_url")
    
    print("📋 Current Configuration:")
    print(f"   Domain: {auth0_domain or 'NOT SET'}")
    print(f"   Client ID: {auth0_client_id or 'NOT SET'}")
    print(f"   Audience: {auth0_audience or 'NOT SET'}")
    print(f"   Server URL: {server_url or 'NOT SET'}")
    print()
    
    if not auth0_domain or not auth0_client_id:
        print("❌ Auth0 not fully configured!")
        return False
    
    print("✅ Configuration looks good")
    print()
    return True

def verify_auth0_endpoints(domain):
    """Verify Auth0 endpoints are accessible"""
    print("=" * 70)
    print("Auth0 Endpoints Verification")
    print("=" * 70)
    print()
    
    endpoints = {
        "OpenID Configuration": f"https://{domain}/.well-known/openid-configuration",
        "JWKS": f"https://{domain}/.well-known/jwks.json",
    }
    
    all_ok = True
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Accessible")
                if name == "OpenID Configuration":
                    data = response.json()
                    print(f"   Issuer: {data.get('issuer')}")
            else:
                print(f"❌ {name}: Status {response.status_code}")
                all_ok = False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            all_ok = False
    
    print()
    return all_ok

def verify_authorization_url(config):
    """Verify authorization URL can be generated"""
    print("=" * 70)
    print("Authorization URL Verification")
    print("=" * 70)
    print()
    
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    auth0_audience = config.get("auth0_audience") or config.get("auth_audience")
    
    try:
        oauth_config = OAuthConfig(
            auth_domain=auth0_domain,
            client_id=auth0_client_id,
            audience=auth0_audience,
            scope="openid profile email offline_access"
        )
        
        code_verifier, code_challenge = generate_pkce_pair()
        state = secrets.token_urlsafe(16)
        redirect_uri = "http://127.0.0.1:5000/callback"
        
        auth_url = build_auth_url(oauth_config, redirect_uri, state, code_challenge)
        
        print("✅ Authorization URL generated successfully")
        print()
        print("📋 URL Components:")
        print(f"   Base: https://{auth0_domain}/authorize")
        print(f"   Client ID: {auth0_client_id}")
        print(f"   Redirect URI: {redirect_uri}")
        print(f"   Audience: {auth0_audience}")
        print()
        print("📋 Full URL (first 100 chars):")
        print(f"   {auth_url[:100]}...")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Failed to generate authorization URL: {e}")
        print()
        return False

def check_callback_url():
    """Check callback URL configuration"""
    print("=" * 70)
    print("Callback URL Configuration")
    print("=" * 70)
    print()
    
    callback_url = "http://127.0.0.1:5000/callback"
    
    print(f"📋 Required Callback URL: {callback_url}")
    print()
    print("⚠️  CRITICAL: This URL MUST be configured in Auth0!")
    print()
    print("   Steps to configure:")
    print("   1. Go to: https://manage.auth0.com/dashboard/us/dev-oczlciw58f2a4oei/applications")
    print("   2. Click on your application (Client ID: AVLPE7EULVWdJV5NIzFI56EAeHmnt2Um)")
    print("   3. Go to 'Settings' tab")
    print("   4. Scroll to 'Allowed Callback URLs'")
    print(f"   5. Add: {callback_url}")
    print("   6. Also add: http://localhost:5000/callback")
    print("   7. Click 'Save Changes'")
    print()
    print("   ⚠️  Without this, you will get 'Oops! Something went wrong' error")
    print()

def check_application_type():
    """Check application type requirements"""
    print("=" * 70)
    print("Application Type Requirements")
    print("=" * 70)
    print()
    
    print("📋 Required Application Settings:")
    print()
    print("   1. Application Type: Native")
    print("      → Required for PKCE flow")
    print("      → Does not require client secret")
    print()
    print("   2. Grant Types (Enabled):")
    print("      ✅ Authorization Code")
    print("      ✅ Refresh Token")
    print()
    print("   3. Advanced Settings → OAuth:")
    print("      ✅ OIDC Conformant: Enabled")
    print("      ✅ PKCE: Required (or Optional)")
    print()
    print("   4. Allowed URLs:")
    print("      Callback: http://127.0.0.1:5000/callback")
    print("      Logout: http://127.0.0.1:5000")
    print("      Web Origins: http://127.0.0.1:5000")
    print()

def test_authorization_endpoint():
    """Test if authorization endpoint accepts our parameters"""
    print("=" * 70)
    print("Authorization Endpoint Test")
    print("=" * 70)
    print()
    
    config = get_config()
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    
    if not auth0_domain or not auth0_client_id:
        print("❌ Configuration not available")
        return False
    
    # Build a test URL
    redirect_uri = "http://127.0.0.1:5000/callback"
    test_url = f"https://{auth0_domain}/authorize?response_type=code&client_id={auth0_client_id}&redirect_uri={redirect_uri}&scope=openid&state=test"
    
    print(f"📋 Testing authorization endpoint...")
    print(f"   URL: {test_url[:80]}...")
    print()
    
    try:
        # Make a HEAD request to check if endpoint is accessible
        response = requests.head(
            f"https://{auth0_domain}/authorize",
            params={
                "response_type": "code",
                "client_id": auth0_client_id,
                "redirect_uri": redirect_uri,
                "scope": "openid",
                "state": "test"
            },
            allow_redirects=False,
            timeout=5
        )
        
        # Auth0 will redirect (302) if valid, or return 400 if invalid
        if response.status_code in [302, 400]:
            if response.status_code == 302:
                print("✅ Authorization endpoint is accessible")
                print("   (302 redirect is expected)")
            else:
                print("⚠️  Authorization endpoint returned 400")
                print("   This might indicate:")
                print("   - Callback URL not configured")
                print("   - Invalid client ID")
                print("   - Application type mismatch")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        print()
        return False

def main():
    """Run all verifications"""
    print()
    print("🔍 Auth0 Setup Verification")
    print()
    
    # Verify config
    if not verify_config():
        print("❌ Configuration verification failed")
        sys.exit(1)
    
    config = get_config()
    domain = config.get("auth0_domain") or config.get("auth_domain")
    
    # Verify endpoints
    if domain:
        verify_auth0_endpoints(domain)
        verify_authorization_url(config)
        test_authorization_endpoint()
    
    # Check requirements
    check_callback_url()
    check_application_type()
    
    print("=" * 70)
    print("✅ Verification Complete")
    print("=" * 70)
    print()
    print("💡 Most Common Issue:")
    print("   The 'Oops! Something went wrong' error is usually caused by")
    print("   the callback URL not being configured in Auth0 Dashboard.")
    print()
    print("   Make sure you add: http://127.0.0.1:5000/callback")
    print("   to 'Allowed Callback URLs' in Auth0 application settings.")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

