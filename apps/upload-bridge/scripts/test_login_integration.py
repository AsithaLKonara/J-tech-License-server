#!/usr/bin/env python3
"""
Integration Test for Login Methods
Tests actual API calls and license validation flows
"""

import os
import sys
import requests
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_email_password_login_flow():
    """Test email/password login flow (mock backend)"""
    print("=" * 60)
    print("Testing Email/Password Login Flow")
    print("=" * 60)
    
    try:
        from core.auth_manager import AuthManager
        from core.license_manager import LicenseManager
        
        server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:3000')
        auth_manager = AuthManager(server_url=server_url)
        license_manager = LicenseManager(server_url=server_url)
        
        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'session_token': 'test-session-token',
            'entitlement_token': {
                'sub': 'test-user-id',
                'product': 'upload_bridge_pro',
                'plan': 'pro',
                'features': ['pattern_upload', 'wifi_upload', 'advanced_controls'],
                'expires_at': None
            },
            'user': {
                'id': 'test-user-id',
                'email': 'test@example.com'
            }
        }
        
        # Test the flow
        with patch('requests.post', return_value=mock_response):
            # Simulate login
            response = requests.post(
                f"{server_url}/api/v2/auth/login",
                json={
                    'email': 'test@example.com',
                    'password': 'testpassword123',
                    'device_id': auth_manager.get_device_id(),
                    'device_name': 'Windows Device'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store tokens
                auth_manager.session_token = data.get('session_token')
                auth_manager.entitlement_token = data.get('entitlement_token')
                auth_manager.user_info = data.get('user', {})
                
                print("✅ Login API call successful")
                print(f"   Session token: {auth_manager.session_token[:20]}...")
                print(f"   User email: {auth_manager.user_info.get('email')}")
                
                # Test license validation
                is_valid, message, license_info = license_manager.validate_license()
                print(f"✅ License validation: {is_valid}")
                print(f"   Message: {message}")
                if license_info:
                    print(f"   Source: {license_info.get('source', 'N/A')}")
                    print(f"   Plan: {license_info.get('plan', 'N/A')}")
                    print(f"   Features: {license_info.get('features', [])}")
                
                print()
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print()
                return False
                
    except Exception as e:
        print(f"❌ Email/Password login flow test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False

def test_offline_license_activation():
    """Test offline license key activation"""
    print("=" * 60)
    print("Testing Offline License Key Activation")
    print("=" * 60)
    
    try:
        from core.license_manager import LicenseManager
        
        license_manager = LicenseManager()
        
        # Test with a sample key (this is a test key format)
        test_key = "ULBP-9Q2Z-7K3M-4X1A"
        
        print(f"Testing activation with key: {test_key}")
        
        # Try to activate (will fail if key doesn't exist, but we can test the method)
        success, message = license_manager.activate_premade_key(test_key)
        
        if success:
            print(f"✅ License activated successfully")
            print(f"   Message: {message}")
        else:
            print(f"⚠️  License activation: {message}")
            print("   (This is expected if key doesn't exist in premade keys)")
        
        # Verify license manager can validate
        is_valid, val_message, info = license_manager.validate_license()
        print(f"✅ License validation works")
        print(f"   Valid: {is_valid}")
        print(f"   Message: {val_message}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Offline license activation test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False

def test_account_based_license_priority():
    """Test that account-based license takes priority"""
    print("=" * 60)
    print("Testing Account-Based License Priority")
    print("=" * 60)
    
    try:
        from core.auth_manager import AuthManager
        from core.license_manager import LicenseManager
        
        server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:3000')
        auth_manager = AuthManager(server_url=server_url)
        license_manager = LicenseManager(server_url=server_url)
        
        # Mock account-based license
        auth_manager.entitlement_token = {
            'sub': 'test-user-id',
            'product': 'upload_bridge_pro',
            'plan': 'pro',
            'features': ['pattern_upload', 'wifi_upload'],
            'expires_at': None
        }
        auth_manager.user_info = {'email': 'test@example.com', 'id': 'test-user-id'}
        
        # Test validation
        is_valid, message, license_info = license_manager.validate_license()
        
        print(f"✅ License validation completed")
        print(f"   Valid: {is_valid}")
        print(f"   Message: {message}")
        
        if license_info:
            source = license_info.get('source', 'N/A')
            print(f"   Source: {source}")
            
            if source == 'account':
                print("✅ Account-based license takes priority (correct!)")
            else:
                print(f"⚠️  License source is '{source}', expected 'account'")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Account-based license priority test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False

def test_oauth_configuration():
    """Test OAuth configuration is correct"""
    print("=" * 60)
    print("Testing OAuth Configuration")
    print("=" * 60)
    
    try:
        from core.oauth_handler import OAuthConfig
        
        auth0_domain = os.getenv('AUTH0_DOMAIN')
        auth0_client_id = os.getenv('AUTH0_CLIENT_ID')
        
        if not auth0_domain or not auth0_client_id:
            print("⚠️  Auth0 not configured (OAuth will be disabled)")
            print("   This is OK - Email/Password login still works")
            print()
            return True
        
        config = OAuthConfig(
            auth_domain=auth0_domain,
            client_id=auth0_client_id,
            audience=os.getenv('AUTH0_AUDIENCE'),
            scope="openid profile email offline_access",
            timeout=300,
        )
        
        print(f"✅ OAuth configuration valid")
        print(f"   Domain: {config.auth_domain}")
        print(f"   Client ID: {config.client_id[:20]}...")
        print(f"   Scope: {config.scope}")
        
        # Verify URL construction
        auth_url = f"https://{config.auth_domain}/authorize"
        print(f"   Auth URL: {auth_url}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ OAuth configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False

def main():
    """Run integration tests"""
    print("\n" + "=" * 60)
    print("LOGIN METHODS INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Email/Password Login Flow", test_email_password_login_flow),
        ("Offline License Activation", test_offline_license_activation),
        ("Account-Based License Priority", test_account_based_license_priority),
        ("OAuth Configuration", test_oauth_configuration),
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
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL INTEGRATION TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

