#!/usr/bin/env python3
"""
Debug Auth0 "Oops! Something went wrong" Error

This script helps diagnose the exact cause of the Auth0 error by:
1. Testing the authorization URL directly
2. Checking callback URL configuration
3. Verifying all Auth0 settings
4. Providing detailed error analysis
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

def test_authorization_url():
    """Test the authorization URL and see what error Auth0 returns"""
    print("=" * 70)
    print("Testing Authorization URL")
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
    
    print("📋 Authorization URL Components:")
    print(f"   Domain: {auth0_domain}")
    print(f"   Client ID: {auth0_client_id}")
    print(f"   Redirect URI: {redirect_uri}")
    print(f"   Audience: {auth0_audience}")
    print(f"   State: {state[:20]}...")
    print(f"   Code Challenge: {code_challenge[:20]}...")
    print()
    
    print("🔗 Full Authorization URL:")
    print(f"   {auth_url}")
    print()
    
    # Test the URL
    print("🧪 Testing Authorization URL...")
    print()
    
    try:
        # Make a request to the authorization endpoint
        response = requests.get(
            auth_url,
            allow_redirects=False,
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print()
        
        if response.status_code == 302:
            # Redirect means it's working
            location = response.headers.get('Location', '')
            print("✅ Authorization URL is valid (302 redirect)")
            print(f"   Redirect Location: {location[:100]}...")
            
            if 'error' in location:
                # Parse error from redirect
                parsed = urllib.parse.urlparse(location)
                params = urllib.parse.parse_qs(parsed.query)
                if 'error' in params:
                    error = params['error'][0]
                    error_description = params.get('error_description', [''])[0]
                    print()
                    print("❌ Auth0 Error Found:")
                    print(f"   Error: {error}")
                    print(f"   Description: {error_description}")
        elif response.status_code == 400:
            print("❌ Bad Request (400)")
            print("   This usually means:")
            print("   - Invalid client_id")
            print("   - Invalid redirect_uri (not in allowed list)")
            print("   - Missing required parameters")
        elif response.status_code == 403:
            print("❌ Forbidden (403)")
            print("   This usually means:")
            print("   - Callback URL not configured in Auth0")
            print("   - Application type mismatch")
            print("   - PKCE not enabled")
        elif response.status_code == 200:
            # HTML response - might be the error page
            if 'Oops' in response.text or 'something went wrong' in response.text.lower():
                print("❌ Auth0 Error Page Detected")
                print("   The 'Oops! Something went wrong' page was returned")
                print()
                print("   This typically means:")
                print("   1. Callback URL not in 'Allowed Callback URLs'")
                print("   2. Application Type is not 'Native'")
                print("   3. PKCE is not enabled")
                print("   4. Invalid client_id")
            else:
                print("✅ Authorization page returned (200)")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
        
        print()
        
        # Check response headers
        if 'Location' in response.headers:
            location = response.headers['Location']
            if 'error' in location:
                parsed = urllib.parse.urlparse(location)
                params = urllib.parse.parse_qs(parsed.query)
                print("📋 Error Details from Redirect:")
                for key, value in params.items():
                    print(f"   {key}: {value[0] if value else ''}")
        
    except Exception as e:
        print(f"❌ Error testing URL: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def check_callback_url_requirements():
    """Check callback URL requirements"""
    print("=" * 70)
    print("Callback URL Requirements")
    print("=" * 70)
    print()
    
    redirect_uri = "http://127.0.0.1:5000/callback"
    
    print(f"📋 Required Callback URL: {redirect_uri}")
    print()
    print("⚠️  CRITICAL: This EXACT URL must be in Auth0 'Allowed Callback URLs'")
    print()
    print("   Common mistakes:")
    print("   ❌ Missing 'http://' prefix")
    print("   ❌ Using 'https://' instead of 'http://'")
    print("   ❌ Trailing slash: 'http://127.0.0.1:5000/callback/'")
    print("   ❌ Wrong port: 'http://127.0.1:5000/callback'")
    print("   ❌ Wrong path: 'http://127.0.0.1:5000/callbacks'")
    print()
    print("   ✅ Correct format: http://127.0.0.1:5000/callback")
    print()

def check_application_settings():
    """Check required application settings"""
    print("=" * 70)
    print("Required Auth0 Application Settings")
    print("=" * 70)
    print()
    
    config = get_config()
    client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    
    print("📋 Application Settings Checklist:")
    print()
    print(f"   1. Application Client ID: {client_id}")
    print("      → Verify this matches in Auth0 Dashboard")
    print()
    print("   2. Application Type: Native")
    print("      → Required for PKCE flow")
    print("      → Does NOT require client secret")
    print()
    print("   3. Allowed Callback URLs:")
    print("      → http://127.0.0.1:5000/callback")
    print("      → http://localhost:5000/callback")
    print("      → Must match EXACTLY (case-sensitive, no trailing slash)")
    print()
    print("   4. Allowed Logout URLs:")
    print("      → http://127.0.0.1:5000")
    print("      → http://localhost:5000")
    print()
    print("   5. Allowed Web Origins:")
    print("      → http://127.0.0.1:5000")
    print("      → http://localhost:5000")
    print()
    print("   6. Grant Types (Enabled):")
    print("      ✅ Authorization Code")
    print("      ✅ Refresh Token")
    print()
    print("   7. Advanced Settings → OAuth:")
    print("      ✅ OIDC Conformant: Enabled")
    print("      ✅ PKCE: Required (or Optional)")
    print()
    print("   8. Advanced Settings → Grant Types:")
    print("      ✅ Allow Offline Access: Enabled (for refresh tokens)")
    print()

def provide_fix_instructions():
    """Provide step-by-step fix instructions"""
    print("=" * 70)
    print("Step-by-Step Fix Instructions")
    print("=" * 70)
    print()
    
    config = get_config()
    client_id = config.get("auth0_client_id") or config.get("auth_client_id")
    domain = config.get("auth0_domain") or config.get("auth_domain")
    
    print("🔧 How to Fix the 'Oops! Something went wrong' Error:")
    print()
    print("Step 1: Login to Auth0 Dashboard")
    print("   → Go to: https://manage.auth0.com/")
    print("   → Select tenant: dev-oczlciw58f2a4oei")
    print()
    print("Step 2: Navigate to Your Application")
    print(f"   → Applications → Applications → Find Client ID: {client_id}")
    print("   → Click on the application name")
    print()
    print("Step 3: Go to Settings Tab")
    print("   → Click 'Settings' tab at the top")
    print()
    print("Step 4: Configure Callback URL")
    print("   → Scroll to 'Allowed Callback URLs' section")
    print("   → Click in the text box")
    print("   → Type EXACTLY: http://127.0.0.1:5000/callback")
    print("   → Press Enter (or add comma and new line)")
    print("   → Also add: http://localhost:5000/callback")
    print("   → DO NOT add trailing slash")
    print()
    print("Step 5: Verify Application Type")
    print("   → Scroll to 'Application Type' dropdown")
    print("   → Should be: Native")
    print("   → If not, change it to 'Native'")
    print()
    print("Step 6: Verify Grant Types")
    print("   → Scroll to 'Application Properties' section")
    print("   → Under 'Grant Types', check:")
    print("      ✅ Authorization Code")
    print("      ✅ Refresh Token")
    print()
    print("Step 7: Configure Advanced Settings")
    print("   → Scroll to bottom, click 'Advanced Settings'")
    print("   → Click 'OAuth' tab")
    print("   → Verify:")
    print("      ✅ OIDC Conformant: Enabled")
    print("      ✅ PKCE: Required (or Optional)")
    print()
    print("Step 8: Save Changes")
    print("   → Click 'Save Changes' button at bottom")
    print("   → Wait for confirmation message")
    print()
    print("Step 9: Test Again")
    print("   → Run: python scripts/test_oauth_auto.py")
    print("   → Or open the authorization URL in browser")
    print()

def main():
    """Run all diagnostics"""
    print()
    print("🔍 Auth0 Error Debug Tool")
    print()
    
    # Test authorization URL
    test_authorization_url()
    
    # Check requirements
    check_callback_url_requirements()
    check_application_settings()
    provide_fix_instructions()
    
    print("=" * 70)
    print("✅ Diagnostic Complete")
    print("=" * 70)
    print()
    print("💡 Most Likely Cause:")
    print("   The callback URL 'http://127.0.0.1:5000/callback' is not")
    print("   configured in Auth0 Dashboard 'Allowed Callback URLs'.")
    print()
    print("   Follow the step-by-step instructions above to fix it.")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

