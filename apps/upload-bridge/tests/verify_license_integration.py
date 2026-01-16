#!/usr/bin/env python3
"""
Upload Bridge License Integration Verification Script

This script verifies that the license server integration is working correctly.
It checks:
- Application startup
- Configuration loading
- API endpoint accessibility
- Basic authentication flow
"""

import sys
import os
import json
import requests
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.auth_manager import AuthManager
    from core.license_manager import LicenseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the upload-bridge directory")
    sys.exit(1)


def check_application_startup():
    """Check if application can start without errors"""
    print("\n📱 Checking Application Startup...")
    try:
        # Try importing main modules
        from ui.main_window import MainWindow
        from ui.dialogs.login_dialog import LoginDialog
        print("✅ Application modules import successfully")
        return True
    except Exception as e:
        print(f"❌ Application startup error: {e}")
        return False


def check_configuration_loading():
    """Check if configuration loads correctly"""
    print("\n⚙️  Checking Configuration Loading...")
    try:
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "auth_config.yaml"
        
        if not config_path.exists():
            print(f"⚠️  Config file not found: {config_path}")
            print("   Using default configuration")
            return True
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        server_url = config.get('auth_server_url') or config.get('license_server_url') or 'http://localhost:8000'
        print(f"✅ Configuration loaded")
        print(f"   Server URL: {server_url}")
        return True
    except Exception as e:
        print(f"❌ Configuration loading error: {e}")
        return False


def check_api_endpoints(server_url):
    """Check if API endpoints are accessible"""
    print(f"\n🌐 Checking API Endpoints (Server: {server_url})...")
    
    endpoints = [
        ('/api/v2/health', 'GET'),
        ('/api/v2/auth/login', 'POST'),
    ]
    
    results = []
    for endpoint, method in endpoints:
        try:
            url = f"{server_url}{endpoint}"
            if method == 'GET':
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json={}, timeout=5)
            
            if response.status_code in [200, 400, 401]:  # 400/401 are expected for POST without data
                print(f"✅ {method} {endpoint} - Accessible (Status: {response.status_code})")
                results.append(True)
            else:
                print(f"⚠️  {method} {endpoint} - Unexpected status: {response.status_code}")
                results.append(False)
        except requests.exceptions.ConnectionError:
            print(f"❌ {method} {endpoint} - Connection failed (server not running?)")
            results.append(False)
        except requests.exceptions.Timeout:
            print(f"❌ {method} {endpoint} - Request timeout")
            results.append(False)
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)


def check_auth_manager():
    """Check if AuthManager initializes correctly"""
    print("\n🔐 Checking AuthManager...")
    try:
        server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:8000')
        auth_manager = AuthManager(server_url=server_url)
        print(f"✅ AuthManager initialized")
        print(f"   Server URL: {auth_manager.server_url}")
        return True
    except Exception as e:
        print(f"❌ AuthManager initialization error: {e}")
        return False


def check_license_manager():
    """Check if LicenseManager initializes correctly"""
    print("\n📜 Checking LicenseManager...")
    try:
        server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:8000')
        license_manager = LicenseManager(server_url=server_url)
        print(f"✅ LicenseManager initialized")
        print(f"   Server URL: {license_manager.server_url}")
        return True
    except Exception as e:
        print(f"❌ LicenseManager initialization error: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Upload Bridge License Integration Verification")
    print("=" * 60)
    
    results = []
    
    # Check application startup
    results.append(check_application_startup())
    
    # Check configuration
    results.append(check_configuration_loading())
    
    # Get server URL
    server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:8000')
    print(f"\n🔗 Using Server URL: {server_url}")
    
    # Check API endpoints
    results.append(check_api_endpoints(server_url))
    
    # Check managers
    results.append(check_auth_manager())
    results.append(check_license_manager())
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  Some checks failed ({passed}/{total} passed)")
        print("\nNote: Some failures may be expected if:")
        print("  - Server is not running")
        print("  - Configuration needs to be set up")
        print("  - Network connectivity issues")
        return 1


if __name__ == '__main__':
    sys.exit(main())
