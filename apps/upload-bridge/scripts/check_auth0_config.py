#!/usr/bin/env python3
"""
Check Auth0 Configuration and Diagnose Issues

This script checks:
1. Configuration files for mismatches
2. Auth0 application settings
3. Callback URL configuration
4. Application type
"""

import sys
import yaml
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config

def check_config_files():
    """Check configuration files for mismatches"""
    print("=" * 70)
    print("Checking Configuration Files")
    print("=" * 70)
    print()
    
    # Read auth_config.yaml
    auth_config_path = Path(__file__).parent.parent / "config" / "auth_config.yaml"
    app_config_path = Path(__file__).parent.parent / "config" / "app_config.yaml"
    
    auth_config = {}
    app_config = {}
    
    if auth_config_path.exists():
        with open(auth_config_path, 'r') as f:
            auth_config = yaml.safe_load(f) or {}
    
    if app_config_path.exists():
        with open(app_config_path, 'r') as f:
            app_config = yaml.safe_load(f) or {}
    
    print("📋 Configuration Files:")
    print()
    
    # Check auth_config.yaml
    print("1. auth_config.yaml:")
    auth0_auth = auth_config.get("auth0", {})
    print(f"   Domain: {auth0_auth.get('domain', 'NOT SET')}")
    print(f"   Client ID: {auth0_auth.get('client_id', 'NOT SET')}")
    print(f"   Audience: {auth0_auth.get('audience', 'NOT SET')}")
    print(f"   Server URL: {auth_config.get('auth_server_url', 'NOT SET')}")
    print()
    
    # Check app_config.yaml
    print("2. app_config.yaml:")
    auth_app = app_config.get("auth", {})
    print(f"   Domain: {auth_app.get('domain', 'NOT SET')}")
    print(f"   Client ID: {auth_app.get('client_id', 'NOT SET')}")
    print(f"   Audience: {auth_app.get('audience', 'NOT SET')}")
    print(f"   Server URL: {app_config.get('auth_server_url', 'NOT SET')}")
    print()
    
    # Check for mismatches
    print("⚠️  Configuration Mismatches:")
    print("-" * 70)
    
    domain_auth = auth0_auth.get('domain')
    domain_app = auth_app.get('domain')
    if domain_auth and domain_app and domain_auth != domain_app:
        print(f"   ❌ Domain mismatch:")
        print(f"      auth_config.yaml: {domain_auth}")
        print(f"      app_config.yaml: {domain_app}")
    else:
        print(f"   ✅ Domain: {domain_auth or domain_app}")
    
    client_id_auth = auth0_auth.get('client_id')
    client_id_app = auth_app.get('client_id')
    if client_id_auth and client_id_app and client_id_auth != client_id_app:
        print(f"   ❌ Client ID mismatch:")
        print(f"      auth_config.yaml: {client_id_auth}")
        print(f"      app_config.yaml: {client_id_app}")
    else:
        print(f"   ✅ Client ID: {client_id_auth or client_id_app}")
    
    print()
    
    # Check what's actually being used
    print("🔍 Active Configuration (from get_config()):")
    print("-" * 70)
    config = get_config()
    print(f"   Domain: {config.get('auth0_domain') or config.get('auth_domain')}")
    print(f"   Client ID: {config.get('auth0_client_id') or config.get('auth_client_id')}")
    print(f"   Audience: {config.get('auth0_audience') or config.get('auth_audience')}")
    print(f"   Server URL: {config.get('auth_server_url')}")
    print()
    
    return config

def check_auth0_endpoints(domain):
    """Check Auth0 endpoints accessibility"""
    print("=" * 70)
    print("Checking Auth0 Endpoints")
    print("=" * 70)
    print()
    
    endpoints = {
        "OpenID Configuration": f"https://{domain}/.well-known/openid-configuration",
        "JWKS": f"https://{domain}/.well-known/jwks.json",
        "Authorization": f"https://{domain}/authorize",
    }
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Accessible")
                if name == "OpenID Configuration":
                    data = response.json()
                    print(f"   Issuer: {data.get('issuer')}")
                    print(f"   Authorization: {data.get('authorization_endpoint')}")
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    print()

def check_callback_url_config():
    """Provide instructions for callback URL configuration"""
    print("=" * 70)
    print("Callback URL Configuration Check")
    print("=" * 70)
    print()
    
    callback_url = "http://127.0.0.1:5000/callback"
    
    print(f"📋 Required Callback URL: {callback_url}")
    print()
    print("⚠️  This URL MUST be configured in Auth0 Dashboard:")
    print()
    print("   Steps:")
    print("   1. Go to https://manage.auth0.com/")
    print("   2. Navigate to: Applications > Your Application")
    print("   3. Scroll to 'Allowed Callback URLs'")
    print(f"   4. Add: {callback_url}")
    print("   5. Also add: http://localhost:5000/callback (if different)")
    print("   6. Save changes")
    print()
    print("   Application Type should be: Native (for PKCE)")
    print()

def check_application_type():
    """Check if application type is correct"""
    print("=" * 70)
    print("Application Type Check")
    print("=" * 70)
    print()
    
    print("📋 Required Application Settings in Auth0:")
    print()
    print("   Application Type: Native")
    print("   (Required for PKCE flow without client secret)")
    print()
    print("   Grant Types Enabled:")
    print("   ✅ Authorization Code")
    print("   ✅ Refresh Token")
    print()
    print("   Advanced Settings > OAuth:")
    print("   ✅ OIDC Conformant: Enabled")
    print("   ✅ PKCE: Enabled (or 'Optional')")
    print()

def diagnose_error():
    """Provide diagnosis for common errors"""
    print("=" * 70)
    print("Error Diagnosis")
    print("=" * 70)
    print()
    
    print("🔍 Common Causes of 'Oops! Something went wrong':")
    print()
    print("   1. ❌ Callback URL not configured in Auth0")
    print("      → Add http://127.0.0.1:5000/callback to Allowed Callback URLs")
    print()
    print("   2. ❌ Wrong Application Type")
    print("      → Should be 'Native' for PKCE flow")
    print()
    print("   3. ❌ Client ID mismatch")
    print("      → Check config files use correct Client ID")
    print()
    print("   4. ❌ PKCE not enabled")
    print("      → Enable PKCE in Advanced Settings > OAuth")
    print()
    print("   5. ❌ Invalid redirect_uri")
    print("      → Must match exactly: http://127.0.0.1:5000/callback")
    print()
    print("   6. ❌ Port 5000 blocked")
    print("      → Check firewall allows port 5000")
    print()

def main():
    """Run all checks"""
    print()
    print("🔍 Auth0 Configuration Diagnostic Tool")
    print()
    
    # Check config files
    config = check_config_files()
    
    # Check Auth0 endpoints
    domain = config.get('auth0_domain') or config.get('auth_domain')
    if domain:
        check_auth0_endpoints(domain)
    
    # Check callback URL
    check_callback_url_config()
    
    # Check application type
    check_application_type()
    
    # Diagnose error
    diagnose_error()
    
    print("=" * 70)
    print("✅ Diagnostic Complete")
    print("=" * 70)
    print()
    print("💡 Next Steps:")
    print("   1. Fix any configuration mismatches")
    print("   2. Verify Auth0 application settings")
    print("   3. Ensure callback URL is configured")
    print("   4. Try OAuth login again")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

