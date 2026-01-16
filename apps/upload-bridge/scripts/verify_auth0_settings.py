#!/usr/bin/env python3
"""
Verify Auth0 Settings - Comprehensive Check

This script helps verify all Auth0 settings are correct
by testing different scenarios and providing detailed feedback.
"""

import sys
import requests
import urllib.parse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config

def test_basic_auth():
    """Test basic authorization without PKCE"""
    print("=" * 70)
    print("Test 1: Basic Authorization (No PKCE)")
    print("=" * 70)
    print()
    
    config = get_config()
    domain = config.get("auth0_domain") or config.get("auth_domain")
    client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    redirect_uri = "http://127.0.0.1:5000/callback"
    
    # Simple authorization URL without PKCE
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid",
        "state": "test123"
    }
    
    url = f"https://{domain}/authorize?" + urllib.parse.urlencode(params)
    
    print(f"📋 Testing URL: {url[:80]}...")
    print()
    
    try:
        response = requests.get(url, allow_redirects=False, timeout=5)
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
                print("✅ Basic authorization accepted")
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Callback URL likely not configured")
        elif response.status_code == 400:
            print("⚠️  400 Bad Request - Check parameters")
        else:
            print(f"⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def test_with_pkce():
    """Test authorization with PKCE"""
    print("=" * 70)
    print("Test 2: Authorization with PKCE")
    print("=" * 70)
    print()
    
    config = get_config()
    domain = config.get("auth0_domain") or config.get("auth_domain")
    client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    redirect_uri = "http://127.0.0.1:5000/callback"
    
    # Generate PKCE challenge
    import secrets
    import base64
    import hashlib
    
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email offline_access",
        "state": "test123",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    url = f"https://{domain}/authorize?" + urllib.parse.urlencode(params)
    
    print(f"📋 Testing with PKCE...")
    print(f"   Code Challenge Method: S256")
    print()
    
    try:
        response = requests.get(url, allow_redirects=False, timeout=5)
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
                
                if 'redirect_uri' in error_desc.lower() or 'callback' in error_desc.lower():
                    print()
                    print("⚠️  This indicates callback URL issue")
            else:
                print("✅ PKCE authorization accepted")
        elif response.status_code == 403:
            print("❌ 403 Forbidden")
            print("   Possible causes:")
            print("   - Callback URL not in Allowed Callback URLs")
            print("   - Application Type is not Native")
            print("   - PKCE not enabled")
        else:
            print(f"⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def check_application_info():
    """Provide application information for verification"""
    print("=" * 70)
    print("Application Information for Verification")
    print("=" * 70)
    print()
    
    config = get_config()
    client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    domain = config.get("auth0_domain") or config.get("auth_domain")
    
    print("📋 Verify these settings in Auth0 Dashboard:")
    print()
    print(f"   1. Client ID: {client_id}")
    print("      → Must match exactly in Auth0")
    print()
    print("   2. Application Type: Native")
    print("      → NOT 'Single Page Application'")
    print("      → NOT 'Regular Web Application'")
    print()
    print("   3. Allowed Callback URLs:")
    print("      → Must contain EXACTLY: http://127.0.0.1:5000/callback")
    print("      → No trailing slash")
    print("      → No quotes")
    print("      → Case-sensitive")
    print()
    print("   4. Grant Types (Enabled):")
    print("      ✅ Authorization Code")
    print("      ✅ Refresh Token")
    print()
    print("   5. Advanced Settings → OAuth:")
    print("      ✅ OIDC Conformant: Enabled")
    print("      ✅ PKCE: Required (or Optional)")
    print()
    print("🔗 Direct Link to Settings:")
    print(f"   https://manage.auth0.com/dashboard/us/{domain.split('.')[0]}/applications/{client_id}/settings")
    print()

def main():
    """Run all tests"""
    print()
    print("🔍 Comprehensive Auth0 Settings Verification")
    print()
    
    test_basic_auth()
    test_with_pkce()
    check_application_info()
    
    print("=" * 70)
    print("✅ Verification Complete")
    print("=" * 70)
    print()
    print("💡 If all tests show 403:")
    print("   1. Double-check 'Allowed Callback URLs' in Auth0")
    print("   2. Verify Application Type is 'Native'")
    print("   3. Check Advanced Settings → OAuth → PKCE is enabled")
    print("   4. Make sure you clicked 'Save Changes'")
    print("   5. Wait 2-3 minutes for changes to propagate")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

