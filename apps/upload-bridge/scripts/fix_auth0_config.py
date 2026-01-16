#!/usr/bin/env python3
"""
Fix Auth0 Configuration Issues

This script:
1. Fixes Client ID mismatch between config files
2. Verifies Auth0 application settings
3. Provides instructions for callback URL configuration
"""

import sys
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def fix_config_files():
    """Fix configuration file mismatches"""
    print("=" * 70)
    print("Fixing Auth0 Configuration")
    print("=" * 70)
    print()
    
    config_dir = Path(__file__).parent.parent / "config"
    auth_config_path = config_dir / "auth_config.yaml"
    app_config_path = config_dir / "app_config.yaml"
    
    # Read app_config.yaml (source of truth)
    if app_config_path.exists():
        with open(app_config_path, 'r') as f:
            app_config = yaml.safe_load(f) or {}
        
        auth_app = app_config.get("auth", {})
        correct_client_id = auth_app.get("client_id")
        correct_domain = auth_app.get("domain")
        correct_audience = auth_app.get("audience")
        
        print(f"✅ Using correct values from app_config.yaml:")
        print(f"   Client ID: {correct_client_id}")
        print(f"   Domain: {correct_domain}")
        print(f"   Audience: {correct_audience}")
        print()
    else:
        print("❌ app_config.yaml not found!")
        return False
    
    # Update auth_config.yaml
    if auth_config_path.exists():
        with open(auth_config_path, 'r') as f:
            auth_config = yaml.safe_load(f) or {}
        
        auth0_section = auth_config.get("auth0", {})
        old_client_id = auth0_section.get("client_id")
        
        if old_client_id != correct_client_id:
            print(f"⚠️  Client ID mismatch found:")
            print(f"   Current: {old_client_id}")
            print(f"   Correct: {correct_client_id}")
            print()
            print("🔧 Updating auth_config.yaml...")
            
            # Update the config
            auth_config["auth0"]["client_id"] = correct_client_id
            auth_config["auth0"]["domain"] = correct_domain
            auth_config["auth0"]["audience"] = correct_audience
            
            # Write back
            with open(auth_config_path, 'w') as f:
                yaml.dump(auth_config, f, default_flow_style=False, sort_keys=False)
            
            print("✅ auth_config.yaml updated!")
        else:
            print("✅ Client IDs already match")
    else:
        print("⚠️  auth_config.yaml not found, creating it...")
        auth_config = {
            "auth0": {
                "domain": correct_domain,
                "client_id": correct_client_id,
                "audience": correct_audience,
                "client_secret": "${AUTH0_CLIENT_SECRET}"
            },
            "auth_server_url": "https://j-tech-license-server-production.up.railway.app",
            "token": {
                "lifetime_hours": 24,
                "refresh_threshold_hours": 1
            }
        }
        
        with open(auth_config_path, 'w') as f:
            yaml.dump(auth_config, f, default_flow_style=False, sort_keys=False)
        
        print("✅ auth_config.yaml created!")
    
    print()
    return True

def verify_auth0_settings():
    """Provide instructions for Auth0 settings"""
    print("=" * 70)
    print("Auth0 Application Settings Checklist")
    print("=" * 70)
    print()
    
    print("📋 Required Settings in Auth0 Dashboard:")
    print()
    print("1. Application Type: Native")
    print("   → Required for PKCE flow")
    print()
    print("2. Allowed Callback URLs:")
    print("   → http://127.0.0.1:5000/callback")
    print("   → http://localhost:5000/callback")
    print()
    print("3. Allowed Logout URLs:")
    print("   → http://127.0.0.1:5000")
    print("   → http://localhost:5000")
    print()
    print("4. Allowed Web Origins:")
    print("   → http://127.0.0.1:5000")
    print("   → http://localhost:5000")
    print()
    print("5. Grant Types (Enabled):")
    print("   ✅ Authorization Code")
    print("   ✅ Refresh Token")
    print()
    print("6. Advanced Settings → OAuth:")
    print("   ✅ OIDC Conformant: Enabled")
    print("   ✅ PKCE: Required (or Optional)")
    print()
    
    print("🔗 Quick Links:")
    print("   Dashboard: https://manage.auth0.com/")
    print("   Applications: https://manage.auth0.com/dashboard/us/dev-oczlciw58f2a4oei/applications")
    print()

def main():
    """Run fix"""
    print()
    print("🔧 Auth0 Configuration Fix Tool")
    print()
    
    if fix_config_files():
        verify_auth0_settings()
        
        print("=" * 70)
        print("✅ Configuration Fixed!")
        print("=" * 70)
        print()
        print("📝 Next Steps:")
        print("   1. Verify Auth0 application settings (see checklist above)")
        print("   2. Ensure callback URL is configured in Auth0")
        print("   3. Run OAuth test again: python scripts/test_oauth_auto.py")
        print()
    else:
        print("❌ Failed to fix configuration")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

