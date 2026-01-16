#!/usr/bin/env python3
"""
Direct Auth0 Authorization Test

This script tests the Auth0 authorization endpoint directly
and shows the exact error response from Auth0.
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

def test_direct():
    """Test Auth0 authorization endpoint directly"""
    print("=" * 70)
    print("Direct Auth0 Authorization Test")
    print("=" * 70)
    print()
    
    config = get_config()
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    auth0_audience = config.get("auth0_audience") or config.get("auth_audience")
    
    if not auth0_domain or not auth0_client_id:
        print("❌ Auth0 not configured")
        return
    
    redirect_uri = "http://127.0.0.1:5000/callback"
    
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
    
    print("📋 Request Details:")
    print(f"   Domain: {auth0_domain}")
    print(f"   Client ID: {auth0_client_id}")
    print(f"   Redirect URI: {redirect_uri}")
    print(f"   Audience: {auth0_audience}")
    print()
    
    # Parse URL to show exact parameters
    parsed = urllib.parse.urlparse(auth_url)
    params = urllib.parse.parse_qs(parsed.query)
    
    print("📋 URL Parameters Being Sent:")
    for key, value in params.items():
        print(f"   {key}: {value[0] if value else ''}")
    print()
    
    print("🧪 Making request to Auth0...")
    print()
    
    try:
        # Make request with full redirect following to see final response
        response = requests.get(
            auth_url,
            allow_redirects=True,  # Follow redirects to see error page
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        print(f"📊 Final Response Status: {response.status_code}")
        print(f"📊 Final URL: {response.url[:100]}...")
        print()
        
        # Check if we got redirected to an error page
        if 'error' in response.url.lower():
            parsed_error = urllib.parse.urlparse(response.url)
            error_params = urllib.parse.parse_qs(parsed_error.query)
            
            print("❌ Auth0 Error Detected in Redirect:")
            if 'error' in error_params:
                print(f"   Error Code: {error_params['error'][0]}")
            if 'error_description' in error_params:
                print(f"   Description: {error_params['error_description'][0]}")
            print()
        
        # Check response content
        if response.status_code == 200:
            if 'Oops' in response.text or 'something went wrong' in response.text.lower():
                print("❌ Auth0 Error Page Detected")
                print()
                print("   The response contains the 'Oops! Something went wrong' page")
                print()
                
                # Try to extract any error information from the page
                if 'error' in response.text.lower():
                    # Look for error details in the HTML
                    import re
                    error_match = re.search(r'error["\']?\s*[:=]\s*["\']?([^"\']+)', response.text, re.IGNORECASE)
                    if error_match:
                        print(f"   Found error reference: {error_match.group(1)}")
                
                print("   This typically means:")
                print("   1. Callback URL not in 'Allowed Callback URLs'")
                print("   2. Application Type is not 'Native'")
                print("   3. PKCE is not enabled")
                print("   4. Client ID is incorrect or disabled")
            else:
                print("✅ Got 200 response - might be login page")
                print("   Check if you see a login form in the response")
        
        # Check response headers
        print()
        print("📋 Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['location', 'x-auth0-error', 'x-auth0-error-description']:
                print(f"   {key}: {value}")
        
        # Show first 500 chars of response
        print()
        print("📄 Response Content (first 500 chars):")
        print("-" * 70)
        print(response.text[:500])
        print("-" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def check_alternative_redirects():
    """Check if alternative redirect URIs work"""
    print()
    print("=" * 70)
    print("Testing Alternative Redirect URIs")
    print("=" * 70)
    print()
    
    config = get_config()
    auth0_domain = config.get("auth0_domain") or config.get("auth_domain")
    auth0_client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    
    redirect_uris = [
        "http://127.0.0.1:5000/callback",
        "http://localhost:5000/callback",
        "http://127.0.0.1:5000/callback/",
        "https://127.0.0.1:5000/callback",
    ]
    
    for redirect_uri in redirect_uris:
        print(f"🧪 Testing: {redirect_uri}")
        try:
            # Simple test URL
            test_url = f"https://{auth0_domain}/authorize?response_type=code&client_id={auth0_client_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&scope=openid&state=test"
            
            response = requests.get(
                test_url,
                allow_redirects=False,
                timeout=5
            )
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'error' in location.lower():
                    print(f"   ❌ Error in redirect")
                else:
                    print(f"   ✅ Accepted (302 redirect)")
            elif response.status_code == 403:
                print(f"   ❌ Forbidden (403)")
            elif response.status_code == 400:
                print(f"   ❌ Bad Request (400)")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()

def main():
    """Run tests"""
    print()
    print("🔍 Direct Auth0 Authorization Test")
    print()
    
    test_direct()
    check_alternative_redirects()
    
    print("=" * 70)
    print("✅ Test Complete")
    print("=" * 70)
    print()
    print("💡 If you still see errors after configuring Auth0:")
    print("   1. Wait 1-2 minutes for Auth0 changes to propagate")
    print("   2. Clear browser cache and cookies")
    print("   3. Verify Application Type is 'Native' (not 'Single Page Application')")
    print("   4. Check Advanced Settings → OAuth → PKCE is enabled")
    print("   5. Verify Client ID matches exactly")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

