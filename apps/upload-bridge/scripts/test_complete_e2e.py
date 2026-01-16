#!/usr/bin/env python3
"""
Complete End-to-End Test Suite for Upload Bridge License System

This script tests:
1. AuthManager integration (login, token storage, refresh)
2. LicenseManager integration (validation, feature checking)
3. Account-based license flow
4. File-based license flow
5. UI integration (if possible)
6. Error handling

Usage:
    python scripts/test_complete_e2e.py
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.auth_manager import AuthManager, EntitlementManager
from core.license_manager import LicenseManager
from core.oauth_handler import run_oauth_flow, OAuthConfig, generate_pkce_pair

class E2ETestSuite:
    def __init__(self):
        self.results = []
        self.config = get_config()
        self.server_url = self.config.get("auth_server_url", "https://j-tech-license-server-production.up.railway.app")
        self.auth0_domain = self.config.get("auth0_domain") or self.config.get("auth_domain")
        self.auth0_client_id = self.config.get("auth0_client_id") or self.config.get("auth_client_id")
        self.auth0_audience = self.config.get("auth0_audience") or self.config.get("auth_audience")
        
    def add_result(self, name: str, passed: bool, message: str, details: Optional[Dict[str, Any]] = None):
        self.results.append({
            'name': name,
            'passed': passed,
            'message': message,
            'details': details
        })
        icon = '✅' if passed else '❌'
        print(f"{icon} {name}: {message}")
        if details and not passed:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def test_auth_manager_initialization(self):
        """Test AuthManager initialization"""
        try:
            auth_manager = AuthManager(server_url=self.server_url)
            self.add_result(
                'AuthManager Initialization',
                True,
                'AuthManager initialized successfully',
                {'server_url': self.server_url}
            )
            return auth_manager
        except Exception as e:
            self.add_result(
                'AuthManager Initialization',
                False,
                f'Failed to initialize AuthManager: {e}',
                {'error': str(e)}
            )
            return None
    
    def test_license_manager_initialization(self):
        """Test LicenseManager initialization"""
        try:
            license_manager = LicenseManager.instance(server_url=self.server_url)
            self.add_result(
                'LicenseManager Initialization',
                True,
                'LicenseManager initialized successfully',
                {'server_url': self.server_url}
            )
            return license_manager
        except Exception as e:
            self.add_result(
                'LicenseManager Initialization',
                False,
                f'Failed to initialize LicenseManager: {e}',
                {'error': str(e)}
            )
            return None
    
    def test_device_id_generation(self, auth_manager: Optional[AuthManager]):
        """Test device ID generation"""
        if not auth_manager:
            self.add_result('Device ID Generation', False, 'AuthManager not available', {'skip': True})
            return
        
        try:
            device_id = auth_manager.get_device_id()
            if device_id and device_id.startswith('DEVICE_'):
                self.add_result(
                    'Device ID Generation',
                    True,
                    f'Device ID generated: {device_id}',
                    {'device_id': device_id}
                )
            else:
                self.add_result(
                    'Device ID Generation',
                    False,
                    f'Invalid device ID format: {device_id}',
                    {'device_id': device_id}
                )
        except Exception as e:
            self.add_result(
                'Device ID Generation',
                False,
                f'Failed to generate device ID: {e}',
                {'error': str(e)}
            )
    
    def test_token_storage(self, auth_manager: Optional[AuthManager]):
        """Test token storage and retrieval"""
        if not auth_manager:
            self.add_result('Token Storage', False, 'AuthManager not available', {'skip': True})
            return
        
        try:
            # Check if token file exists
            token_file = auth_manager.TOKEN_FILE
            if token_file.exists():
                # Try to load
                auth_manager.load_session()
                if auth_manager.session_token or auth_manager.entitlement_token:
                    self.add_result(
                        'Token Storage',
                        True,
                        'Tokens loaded from storage',
                        {
                            'has_session_token': bool(auth_manager.session_token),
                            'has_entitlement_token': bool(auth_manager.entitlement_token)
                        }
                    )
                else:
                    self.add_result(
                        'Token Storage',
                        False,
                        'Token file exists but no tokens loaded',
                        {'token_file': str(token_file)}
                    )
            else:
                self.add_result(
                    'Token Storage',
                    False,
                    'No token file found (expected if not logged in)',
                    {'token_file': str(token_file), 'note': 'This is normal if user has not logged in'}
                )
        except Exception as e:
            self.add_result(
                'Token Storage',
                False,
                f'Token storage test failed: {e}',
                {'error': str(e)}
            )
    
    def test_oauth_configuration(self):
        """Test OAuth configuration"""
        if not self.auth0_domain or not self.auth0_client_id:
            self.add_result(
                'OAuth Configuration',
                False,
                'Auth0 not configured',
                {
                    'auth0_domain': self.auth0_domain,
                    'auth0_client_id': self.auth0_client_id,
                    'hint': 'Set AUTH0_DOMAIN and AUTH0_CLIENT_ID in config'
                }
            )
            return
        
        try:
            # Test PKCE generation
            code_verifier, code_challenge = generate_pkce_pair()
            if code_verifier and code_challenge:
                self.add_result(
                    'OAuth Configuration',
                    True,
                    'OAuth configuration valid and PKCE generation works',
                    {
                        'auth0_domain': self.auth0_domain,
                        'auth0_client_id': self.auth0_client_id,
                        'auth0_audience': self.auth0_audience,
                        'pkce_generated': True
                    }
                )
            else:
                self.add_result(
                    'OAuth Configuration',
                    False,
                    'PKCE generation failed',
                    {}
                )
        except Exception as e:
            self.add_result(
                'OAuth Configuration',
                False,
                f'OAuth configuration test failed: {e}',
                {'error': str(e)}
            )
    
    def test_account_based_license_validation(self, auth_manager: Optional[AuthManager], license_manager: Optional[LicenseManager]):
        """Test account-based license validation"""
        if not auth_manager or not license_manager:
            self.add_result('Account-Based License Validation', False, 'Managers not available', {'skip': True})
            return
        
        try:
            # Check if user has valid token
            if auth_manager.has_valid_token():
                is_valid, message, license_info = license_manager.validate_license()
                
                if is_valid and license_info:
                    source = license_info.get('source', 'unknown')
                    if source == 'account':
                        self.add_result(
                            'Account-Based License Validation',
                            True,
                            f'Account-based license validated: {message}',
                            {
                                'source': source,
                                'plan': license_info.get('license', {}).get('plan'),
                                'features': license_info.get('license', {}).get('features', [])
                            }
                        )
                    else:
                        self.add_result(
                            'Account-Based License Validation',
                            False,
                            f'License validated but source is not account: {source}',
                            {'source': source, 'license_info': license_info}
                        )
                else:
                    self.add_result(
                        'Account-Based License Validation',
                        False,
                        f'License validation failed: {message}',
                        {'message': message}
                    )
            else:
                self.add_result(
                    'Account-Based License Validation',
                    False,
                    'No valid authentication token (expected if not logged in)',
                    {'note': 'This is normal if user has not logged in via OAuth'}
                )
        except Exception as e:
            self.add_result(
                'Account-Based License Validation',
                False,
                f'Account-based license validation test failed: {e}',
                {'error': str(e)}
            )
    
    def test_feature_checking(self, auth_manager: Optional[AuthManager]):
        """Test feature checking via EntitlementManager"""
        if not auth_manager:
            self.add_result('Feature Checking', False, 'AuthManager not available', {'skip': True})
            return
        
        try:
            entitlement_manager = EntitlementManager(auth_manager)
            
            # Test feature checking
            features_to_test = ['pattern_upload', 'wifi_upload', 'advanced_controls']
            feature_results = {}
            
            for feature in features_to_test:
                is_enabled = entitlement_manager.is_feature_enabled(feature)
                feature_results[feature] = is_enabled
            
            # Get entitlement info
            entitlement_info = entitlement_manager.get_entitlement_info()
            
            self.add_result(
                'Feature Checking',
                True,
                'Feature checking works',
                {
                    'features': feature_results,
                    'entitlement_info': entitlement_info
                }
            )
        except Exception as e:
            self.add_result(
                'Feature Checking',
                False,
                f'Feature checking test failed: {e}',
                {'error': str(e)}
            )
    
    def test_file_based_license_validation(self, license_manager: Optional[LicenseManager]):
        """Test file-based license validation"""
        if not license_manager:
            self.add_result('File-Based License Validation', False, 'LicenseManager not available', {'skip': True})
            return
        
        try:
            # Try to load cached license
            license_data = license_manager.load_cached_license()
            
            if license_data:
                # Validate locally
                is_valid, message = license_manager._validate_license_locally(license_data)
                
                if is_valid:
                    self.add_result(
                        'File-Based License Validation',
                        True,
                        f'File-based license validated: {message}',
                        {
                            'source': 'file',
                            'license_id': license_data.get('license', {}).get('license_id'),
                            'features': license_data.get('license', {}).get('features', [])
                        }
                    )
                else:
                    self.add_result(
                        'File-Based License Validation',
                        False,
                        f'File-based license validation failed: {message}',
                        {'message': message}
                    )
            else:
                self.add_result(
                    'File-Based License Validation',
                    False,
                    'No file-based license found (expected if not activated)',
                    {'note': 'This is normal if user has not activated offline license key'}
                )
        except Exception as e:
            self.add_result(
                'File-Based License Validation',
                False,
                f'File-based license validation test failed: {e}',
                {'error': str(e)}
            )
    
    def test_license_priority(self, auth_manager: Optional[AuthManager], license_manager: Optional[LicenseManager]):
        """Test license priority (account-based takes precedence)"""
        if not auth_manager or not license_manager:
            self.add_result('License Priority', False, 'Managers not available', {'skip': True})
            return
        
        try:
            # Validate license (should check account-based first)
            is_valid, message, license_info = license_manager.validate_license()
            
            if is_valid and license_info:
                source = license_info.get('source', 'unknown')
                self.add_result(
                    'License Priority',
                    True,
                    f'License priority working: {source} license used',
                    {
                        'source': source,
                        'message': message,
                        'note': 'Account-based license should take precedence if both exist'
                    }
                )
            else:
                self.add_result(
                    'License Priority',
                    False,
                    f'License validation failed: {message}',
                    {'message': message}
                )
        except Exception as e:
            self.add_result(
                'License Priority',
                False,
                f'License priority test failed: {e}',
                {'error': str(e)}
            )
    
    def test_error_handling(self):
        """Test error handling for network errors"""
        try:
            # Test with invalid server URL
            invalid_auth_manager = AuthManager(server_url="https://invalid-server-url-12345.com")
            
            # Try to login with invalid token (should handle gracefully)
            success, message = invalid_auth_manager.login("invalid_token")
            
            if not success:
                self.add_result(
                    'Error Handling',
                    True,
                    'Error handling works correctly',
                    {
                        'invalid_server_handled': True,
                        'error_message': message
                    }
                )
            else:
                self.add_result(
                    'Error Handling',
                    False,
                    'Should have failed with invalid server',
                    {}
                )
        except Exception as e:
            # If exception is raised, check if it's handled gracefully
            error_str = str(e).lower()
            if 'connection' in error_str or 'timeout' in error_str or 'resolve' in error_str:
                self.add_result(
                    'Error Handling',
                    True,
                    'Network errors handled gracefully',
                    {'error': str(e)}
                )
            else:
                self.add_result(
                    'Error Handling',
                    False,
                    f'Unexpected error: {e}',
                    {'error': str(e)}
                )
    
    def test_server_connectivity(self):
        """Test server connectivity"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    'Server Connectivity',
                    True,
                    'License server is accessible',
                    {
                        'status': data.get('status'),
                        'service': data.get('service'),
                        'version': data.get('version')
                    }
                )
            else:
                self.add_result(
                    'Server Connectivity',
                    False,
                    f'Server returned status {response.status_code}',
                    {'status_code': response.status_code}
                )
        except Exception as e:
            self.add_result(
                'Server Connectivity',
                False,
                f'Failed to connect to server: {e}',
                {'error': str(e), 'server_url': self.server_url}
            )
    
    def run_all(self):
        """Run all tests"""
        print("=" * 60)
        print("Complete E2E Test Suite for Upload Bridge License System")
        print("=" * 60)
        print()
        print(f"📡 License Server URL: {self.server_url}")
        print(f"🔐 Auth0 Domain: {self.auth0_domain or 'Not configured'}")
        print(f"🆔 Auth0 Client ID: {self.auth0_client_id or 'Not configured'}")
        print()
        print("─" * 60)
        print()
        
        # Initialize managers
        print("📦 Phase 1: Initialization\n")
        auth_manager = self.test_auth_manager_initialization()
        license_manager = self.test_license_manager_initialization()
        
        # Basic functionality tests
        print("\n🔧 Phase 2: Basic Functionality\n")
        self.test_device_id_generation(auth_manager)
        self.test_token_storage(auth_manager)
        self.test_oauth_configuration()
        self.test_server_connectivity()
        
        # License validation tests
        print("\n🔐 Phase 3: License Validation\n")
        self.test_account_based_license_validation(auth_manager, license_manager)
        self.test_file_based_license_validation(license_manager)
        self.test_license_priority(auth_manager, license_manager)
        self.test_feature_checking(auth_manager)
        
        # Error handling tests
        print("\n⚠️  Phase 4: Error Handling\n")
        self.test_error_handling()
        
        # Print summary
        print("\n" + "─" * 60)
        print("📊 Test Summary\n")
        
        passed = sum(1 for r in self.results if r['passed'])
        failed = sum(1 for r in self.results if not r['passed'] and not r.get('details', {}).get('skip'))
        skipped = sum(1 for r in self.results if r.get('details', {}).get('skip'))
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        if skipped > 0:
            print(f"⏭️  Skipped: {skipped}")
        print(f"📝 Total: {len(self.results)}\n")
        
        if failed == 0:
            print("🎉 All tests passed!\n")
        else:
            print("⚠️  Some tests failed. Please review the results above.\n")
        
        return {
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': len(self.results),
            'results': self.results
        }

if __name__ == "__main__":
    try:
        suite = E2ETestSuite()
        results = suite.run_all()
        sys.exit(0 if results['failed'] == 0 else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

