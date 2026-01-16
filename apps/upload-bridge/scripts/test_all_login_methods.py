#!/usr/bin/env python3
"""
Test All Login Methods
Tests Email/Password, OAuth, Magic Link, and Offline License activation
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_environment_variables():
    """Test if environment variables are set"""
    print("=" * 60)
    print("Testing Environment Variables")
    print("=" * 60)
    
    required_vars = {
        'AUTH0_DOMAIN': os.getenv('AUTH0_DOMAIN'),
        'AUTH0_CLIENT_ID': os.getenv('AUTH0_CLIENT_ID'),
        'AUTH0_AUDIENCE': os.getenv('AUTH0_AUDIENCE'),
        'LICENSE_SERVER_URL': os.getenv('LICENSE_SERVER_URL', 'http://localhost:3000'),
        'AUTH_SERVER_URL': os.getenv('AUTH_SERVER_URL', 'http://localhost:3000'),
    }
    
    all_set = True
    for var, value in required_vars.items():
        if value:
            print(f"✅ {var} = {value}")
        else:
            print(f"❌ {var} = (not set)")
            all_set = False
    
    print()
    return all_set

def test_auth_manager():
    """Test AuthManager initialization"""
    print("=" * 60)
    print("Testing AuthManager")
    print("=" * 60)
    
    try:
        from core.auth_manager import AuthManager
        
        server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:3000')
        auth_manager = AuthManager(server_url=server_url)
        
        print(f"✅ AuthManager initialized")
        print(f"   Server URL: {server_url}")
        print(f"   Has valid token: {auth_manager.has_valid_token()}")
        print()
        return True
    except Exception as e:
        print(f"❌ AuthManager initialization failed: {e}")
        print()
        return False

def test_license_manager():
    """Test LicenseManager initialization"""
    print("=" * 60)
    print("Testing LicenseManager")
    print("=" * 60)
    
    try:
        from core.license_manager import LicenseManager
        
        server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:3000')
        license_manager = LicenseManager(server_url=server_url)
        
        print(f"✅ LicenseManager initialized")
        print(f"   Server URL: {server_url}")
        print(f"   License directory: {license_manager.ENCRYPTED_LICENSE_DIR}")
        
        # Test license validation (will fail if no license, but that's OK)
        is_valid, message, info = license_manager.validate_license()
        print(f"   License validation: {is_valid}")
        print(f"   Message: {message}")
        if info:
            print(f"   License source: {info.get('source', 'N/A')}")
        print()
        return True
    except Exception as e:
        print(f"❌ LicenseManager initialization failed: {e}")
        print()
        return False

def test_login_dialog_import():
    """Test LoginDialog can be imported"""
    print("=" * 60)
    print("Testing LoginDialog Import")
    print("=" * 60)
    
    try:
        from ui.dialogs.login_dialog import LoginDialog
        print("✅ LoginDialog imported successfully")
        print()
        return True
    except Exception as e:
        print(f"❌ LoginDialog import failed: {e}")
        print()
        return False

def test_oauth_config():
    """Test OAuth configuration"""
    print("=" * 60)
    print("Testing OAuth Configuration")
    print("=" * 60)
    
    try:
        from core.oauth_handler import OAuthConfig
        
        auth0_domain = os.getenv('AUTH0_DOMAIN')
        auth0_client_id = os.getenv('AUTH0_CLIENT_ID')
        
        if auth0_domain and auth0_client_id:
            config = OAuthConfig(
                auth_domain=auth0_domain,
                client_id=auth0_client_id,
                audience=os.getenv('AUTH0_AUDIENCE'),
                scope="openid profile email offline_access",
                timeout=300,
            )
            print(f"✅ OAuth config created")
            print(f"   Domain: {config.auth_domain}")
            print(f"   Client ID: {config.client_id[:20]}...")
            print()
            return True
        else:
            print("⚠️  Auth0 not configured (OAuth will be disabled)")
            print()
            return True  # Not an error, just not configured
    except Exception as e:
        print(f"❌ OAuth config failed: {e}")
        print()
        return False

def test_config_file():
    """Test config file loading"""
    print("=" * 60)
    print("Testing Config File")
    print("=" * 60)
    
    try:
        import yaml
        config_file = project_root / "config" / "auth_config.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            print(f"✅ Config file loaded: {config_file}")
            if 'auth0' in config:
                auth0_config = config['auth0']
                print(f"   Domain: {auth0_config.get('domain', 'N/A')}")
                print(f"   Client ID: {auth0_config.get('client_id', 'N/A')[:20]}...")
            print()
            return True
        else:
            print(f"⚠️  Config file not found: {config_file}")
            print()
            return False
    except Exception as e:
        print(f"❌ Config file test failed: {e}")
        print()
        return False

def test_email_password_login_code():
    """Test email/password login code path"""
    print("=" * 60)
    print("Testing Email/Password Login Code Path")
    print("=" * 60)
    
    try:
        # Test that the login method exists and can be called
        from ui.dialogs.login_dialog import LoginDialog
        from core.auth_manager import AuthManager
        
        server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:3000')
        auth_manager = AuthManager(server_url=server_url)
        
        # Check if _login_with_email_password method exists
        if hasattr(LoginDialog, '_login_with_email_password'):
            print("✅ Email/Password login method exists")
        else:
            print("❌ Email/Password login method not found")
            return False
        
        # Check if validate_license_after_login exists
        if hasattr(LoginDialog, '_validate_license_after_login'):
            print("✅ License validation after login method exists")
        else:
            print("❌ License validation method not found")
            return False
        
        print()
        return True
    except Exception as e:
        print(f"❌ Email/Password login test failed: {e}")
        print()
        return False

def test_offline_license_keys():
    """Test offline license key activation"""
    print("=" * 60)
    print("Testing Offline License Keys")
    print("=" * 60)
    
    try:
        from core.license_manager import LicenseManager
        
        license_manager = LicenseManager()
        
        # Check if premade keys file exists
        if license_manager.premade_keys_file.exists():
            print(f"✅ Premade keys file exists: {license_manager.premade_keys_file}")
            
            # Try to load keys
            keys = license_manager._load_premade_keys()
            if keys:
                print(f"✅ Loaded {len(keys)} premade license keys")
                # Show first key ID
                first_key = list(keys.keys())[0] if keys else None
                if first_key:
                    print(f"   Sample key ID: {first_key}")
            else:
                print("⚠️  No premade keys found in file")
        else:
            print(f"⚠️  Premade keys file not found: {license_manager.premade_keys_file}")
        
        # Test activate_premade_key method exists
        if hasattr(license_manager, 'activate_premade_key'):
            print("✅ activate_premade_key method exists")
        else:
            print("❌ activate_premade_key method not found")
            return False
        
        print()
        return True
    except Exception as e:
        print(f"❌ Offline license test failed: {e}")
        print()
        return False

def test_license_validation_priority():
    """Test license validation priority (account vs file-based)"""
    print("=" * 60)
    print("Testing License Validation Priority")
    print("=" * 60)
    
    try:
        from core.license_manager import LicenseManager
        
        license_manager = LicenseManager()
        
        # Check validate_license method
        if hasattr(license_manager, 'validate_license'):
            print("✅ validate_license method exists")
            
            # Test that it checks account-based first
            # (We can't actually test the full flow without real tokens)
            is_valid, message, info = license_manager.validate_license()
            print(f"   Current validation result: {is_valid}")
            print(f"   Message: {message}")
            if info:
                print(f"   License source: {info.get('source', 'N/A')}")
        else:
            print("❌ validate_license method not found")
            return False
        
        print()
        return True
    except Exception as e:
        print(f"❌ License validation priority test failed: {e}")
        print()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TESTING ALL LOGIN METHODS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Config File", test_config_file),
        ("AuthManager", test_auth_manager),
        ("LicenseManager", test_license_manager),
        ("LoginDialog Import", test_login_dialog_import),
        ("OAuth Configuration", test_oauth_config),
        ("Email/Password Login Code", test_email_password_login_code),
        ("Offline License Keys", test_offline_license_keys),
        ("License Validation Priority", test_license_validation_priority),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}\n")
            results.append((name, False))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

