#!/usr/bin/env python3
"""
Test if Auth0 Callback URL is Configured

This script attempts to access the Auth0 authorization endpoint
and checks if the callback URL is properly configured.
"""

import sys
import requests
import urllib.parse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.oauth_handler import build_auth_url, generate_pkce_pair, OAuthConfig
import secrets

def test_callback_config():
    """Test if callback URL is configured in Auth0"""
    print("=" * 70)
    print("Testing Auth0 Callback URL Configuration")
    print("=" * 70)
    print()
    
    config = get_config()
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    auth0_audience = config.get("auth0_audience") or config.get("auth_audience")
    
    if not auth0_domain or not auth0_client_id:
        print("❌ Auth0 not configured")
        return False
    
    redirect_uri = "http://127.0.0.1:5000/callback"
    
    print(f"📋 Configuration:")
    print(f"   Domain: {auth0_domain}")
    print(f"   Client ID: {auth0_client_id}")
    print(f"   Callback URL: {redirect_uri}")
    print()
    
    # Build authorization URL
    oauth_config = OAuthConfig(
        auth_domain=auth0_domain,
        client_id=auth0_client_id,
        audience=auth0_audience,
        scope="openid profile email offline_access"
    )
    
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    
    auth_url = build_auth_url(oauth_config, redirect_uri, state, code_challenge)
    
    print("🧪 Testing authorization endpoint...")
    print()
    
    try:
        response = requests.get(
            auth_url,
            allow_redirects=False,
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print()
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'error' in location.lower():
                # Parse error
                parsed = urllib.parse.urlparse(location)
                params = urllib.parse.parse_qs(parsed.query)
                error = params.get('error', [''])[0]
                error_desc = params.get('error_description', [''])[0]
                
                print("❌ Auth0 Error Detected:")
                print(f"   Error: {error}")
                print(f"   Description: {error_desc}")
                print()
                
                if 'redirect_uri' in error_desc.lower() or 'callback' in error_desc.lower():
                    print("⚠️  This indicates the callback URL is NOT configured!")
                    print()
                    print("   Action Required:")
                    print("   1. Go to Auth0 Dashboard")
                    print("   2. Applications → Your App → Settings")
                    print(f"   3. Add to 'Allowed Callback URLs': {redirect_uri}")
                    print("   4. Save changes")
                    return False
            else:
                print("✅ Authorization URL accepted (302 redirect)")
                print("   Callback URL appears to be configured correctly")
                return True
        elif response.status_code == 400:
            print("❌ Bad Request (400)")
            print("   This usually means invalid parameters")
            return False
        elif response.status_code == 403:
            print("❌ Forbidden (403)")
            print("   This means the callback URL is NOT configured in Auth0")
            print()
            print("   Action Required:")
            print("   1. Go to: https://manage.auth0.com/dashboard/us/dev-oczlciw58f2a4oei/applications")
            print(f"   2. Find application: {auth0_client_id}")
            print("   3. Settings → Allowed Callback URLs")
            print(f"   4. Add: {redirect_uri}")
            print("   5. Save changes")
            return False
        elif response.status_code == 200:
            # Check if it's the error page
            if 'Oops' in response.text or 'something went wrong' in response.text.lower():
                print("❌ Auth0 Error Page Returned")
                print("   The 'Oops! Something went wrong' page was returned")
                print()
                print("   This means the callback URL is NOT configured")
                print()
                print("   Action Required:")
                print("   1. Go to Auth0 Dashboard")
                print("   2. Applications → Your App → Settings")
                print(f"   3. Add to 'Allowed Callback URLs': {redirect_uri}")
                print("   4. Save changes")
                return False
            else:
                print("✅ Authorization page returned (200)")
                print("   This might be the login page - callback URL may be configured")
                return True
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run test"""
    print()
    print("🔍 Auth0 Callback URL Configuration Test")
    print()
    
    is_configured = test_callback_config()
    
    print("=" * 70)
    if is_configured:
        print("✅ Callback URL appears to be configured")
        print("   You can try the OAuth login now")
    else:
        print("❌ Callback URL is NOT configured")
        print("   Please configure it in Auth0 Dashboard first")
    print("=" * 70)
    print()
    
    if not is_configured:
        print("📋 Quick Fix:")
        print("   1. Go to: https://manage.auth0.com/dashboard/us/dev-oczlciw58f2a4oei/applications")
        print("   2. Find your application")
        print("   3. Settings → Allowed Callback URLs")
        print("   4. Add: http://127.0.0.1:5000/callback")
        print("   5. Save changes")
        print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

