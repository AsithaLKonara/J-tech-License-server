#!/usr/bin/env python3
"""
Test Auth0 Authorization Without PKCE

This script tests if Auth0 authorization works without explicit PKCE,
since Native applications may have PKCE enabled by default.
"""

import sys
import requests
import urllib.parse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config

def test_without_pkce():
    """Test authorization without PKCE parameters"""
    print("=" * 70)
    print("Testing Auth0 Authorization Without PKCE")
    print("=" * 70)
    print()
    
    config = get_config()
    domain = config.get("auth0_domain") or config.get("auth_domain")
    client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    redirect_uri = "http://127.0.0.1:5000/callback"
    
    print("📋 Configuration:")
    print(f"   Domain: {domain}")
    print(f"   Client ID: {client_id}")
    print(f"   Redirect URI: {redirect_uri}")
    print()
    
    # Test 1: Without PKCE (simple authorization code flow)
    print("🧪 Test 1: Authorization Code Flow (No PKCE)")
    print("-" * 70)
    
    params1 = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email offline_access",
        "state": "test123"
    }
    
    url1 = f"https://{domain}/authorize?" + urllib.parse.urlencode(params1)
    
    try:
        response = requests.get(url1, allow_redirects=False, timeout=5)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'error' in location.lower():
                parsed = urllib.parse.urlparse(location)
                error_params = urllib.parse.parse_qs(parsed.query)
                error = error_params.get('error', [''])[0]
                error_desc = error_params.get('error_description', [''])[0]
                print(f"❌ Error: {error}")
                print(f"   Description: {error_desc}")
            else:
                print("✅ Authorization accepted (302 redirect)")
                print("   This means callback URL is configured correctly!")
        elif response.status_code == 403:
            print("❌ 403 Forbidden")
            print("   Callback URL still not configured")
        elif response.status_code == 400:
            print("⚠️  400 Bad Request")
            print("   Might need PKCE for Native applications")
        else:
            print(f"⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: With PKCE (as our code does)
    print("🧪 Test 2: Authorization Code Flow WITH PKCE")
    print("-" * 70)
    
    import secrets
    import base64
    import hashlib
    
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    params2 = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email offline_access",
        "state": "test123",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    url2 = f"https://{domain}/authorize?" + urllib.parse.urlencode(params2)
    
    try:
        response = requests.get(url2, allow_redirects=False, timeout=5)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'error' in location.lower():
                parsed = urllib.parse.urlparse(location)
                error_params = urllib.parse.parse_qs(parsed.query)
                error = error_params.get('error', [''])[0]
                error_desc = error_params.get('error_description', [''])[0]
                print(f"❌ Error: {error}")
                print(f"   Description: {error_desc}")
            else:
                print("✅ Authorization accepted (302 redirect)")
                print("   PKCE flow works correctly!")
        elif response.status_code == 403:
            print("❌ 403 Forbidden")
            print("   Callback URL not configured")
        elif response.status_code == 400:
            print("⚠️  400 Bad Request")
            parsed = urllib.parse.urlparse(response.url if hasattr(response, 'url') else '')
            print("   Check error details")
        else:
            print(f"⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def main():
    """Run tests"""
    print()
    print("🔍 Testing Auth0 Authorization (With and Without PKCE)")
    print()
    
    test_without_pkce()
    
    print("=" * 70)
    print("✅ Test Complete")
    print("=" * 70)
    print()
    print("💡 About PKCE:")
    print("   - For Native applications, PKCE is often enabled by default")
    print("   - You might not see a PKCE setting in Advanced Settings")
    print("   - If Test 1 (without PKCE) works, callback URL is configured")
    print("   - If Test 2 (with PKCE) works, PKCE is supported")
    print()
    print("   If both show 403, the callback URL is still not configured correctly")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

