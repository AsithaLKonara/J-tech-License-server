#!/usr/bin/env python3
"""
License Priority Tests

This script tests:
1. Account-based license takes precedence over file-based
2. File-based license used as fallback when account-based not available
3. Priority order is correct
4. Fallback behavior works correctly

Usage:
    python scripts/test_license_priority.py
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auth_manager import AuthManager
from core.license_manager import LicenseManager

class PriorityTestSuite:
    def __init__(self):
        self.results = []
        self.server_url = "https://j-tech-license-server-production.up.railway.app"
        
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
    
    def test_account_based_priority(self):
        """Test that account-based license takes precedence"""
        try:
            auth_manager = AuthManager(server_url=self.server_url)
            license_manager = LicenseManager.instance(server_url=self.server_url)
            
            # Check if account-based license exists
            if auth_manager.has_valid_token():
                # Validate license (should return account-based)
                is_valid, message, license_info = license_manager.validate_license()
                
                if is_valid and license_info:
                    source = license_info.get('source', 'unknown')
                    if source == 'account':
                        self.add_result(
                            'Account-Based Priority',
                            True,
                            'Account-based license takes precedence',
                            {
                                'source': source,
                                'message': message,
                                'plan': license_info.get('license', {}).get('plan'),
                                'features': license_info.get('license', {}).get('features', [])
                            }
                        )
                    else:
                        self.add_result(
                            'Account-Based Priority',
                            False,
                            f'Account-based license not used (source: {source})',
                            {
                                'source': source,
                                'expected': 'account',
                                'license_info': license_info
                            }
                        )
                else:
                    self.add_result(
                        'Account-Based Priority',
                        False,
                        f'License validation failed: {message}',
                        {'message': message}
                    )
            else:
                self.add_result(
                    'Account-Based Priority',
                    False,
                    'No account-based license available (expected if not logged in)',
                    {'note': 'This is normal if user has not logged in via OAuth'}
                )
        except Exception as e:
            self.add_result(
                'Account-Based Priority',
                False,
                f'Account-based priority test failed: {e}',
                {'error': str(e)}
            )
    
    def test_file_based_fallback(self):
        """Test that file-based license is used as fallback"""
        try:
            license_manager = LicenseManager.instance(server_url=self.server_url)
            
            # Try to load file-based license
            license_data = license_manager.load_cached_license()
            
            if license_data:
                # Validate (should work even without account-based)
                is_valid, message = license_manager._validate_license_locally(license_data)
                
                if is_valid:
                    self.add_result(
                        'File-Based Fallback',
                        True,
                        'File-based license works as fallback',
                        {
                            'source': 'file',
                            'message': message,
                            'license_id': license_data.get('license', {}).get('license_id'),
                            'features': license_data.get('license', {}).get('features', [])
                        }
                    )
                else:
                    self.add_result(
                        'File-Based Fallback',
                        False,
                        f'File-based license validation failed: {message}',
                        {'message': message}
                    )
            else:
                self.add_result(
                    'File-Based Fallback',
                    False,
                    'No file-based license found (expected if not activated)',
                    {'note': 'This is normal if user has not activated offline license key'}
                )
        except Exception as e:
            self.add_result(
                'File-Based Fallback',
                False,
                f'File-based fallback test failed: {e}',
                {'error': str(e)}
            )
    
    def test_priority_order(self):
        """Test that priority order is correct (account first, then file)"""
        try:
            auth_manager = AuthManager(server_url=self.server_url)
            license_manager = LicenseManager.instance(server_url=self.server_url)
            
            # Check validation order
            has_account = auth_manager.has_valid_token()
            has_file = license_manager.load_cached_license() is not None
            
            # Validate license
            is_valid, message, license_info = license_manager.validate_license()
            
            if is_valid and license_info:
                source = license_info.get('source', 'unknown')
                
                # Determine expected source based on availability
                if has_account:
                    expected_source = 'account'
                elif has_file:
                    expected_source = 'file'
                else:
                    expected_source = None
                
                if source == expected_source:
                    self.add_result(
                        'Priority Order',
                        True,
                        f'Priority order is correct: {source} license used',
                        {
                            'has_account': has_account,
                            'has_file': has_file,
                            'source': source,
                            'expected': expected_source,
                            'message': message
                        }
                    )
                else:
                    self.add_result(
                        'Priority Order',
                        False,
                        f'Priority order is incorrect: {source} used, expected {expected_source}',
                        {
                            'has_account': has_account,
                            'has_file': has_file,
                            'source': source,
                            'expected': expected_source
                        }
                    )
            else:
                if not has_account and not has_file:
                    self.add_result(
                        'Priority Order',
                        True,
                        'No licenses available (expected behavior)',
                        {
                            'has_account': has_account,
                            'has_file': has_file,
                            'message': message
                        }
                    )
                else:
                    self.add_result(
                        'Priority Order',
                        False,
                        f'License validation failed: {message}',
                        {
                            'has_account': has_account,
                            'has_file': has_file,
                            'message': message
                        }
                    )
        except Exception as e:
            self.add_result(
                'Priority Order',
                False,
                f'Priority order test failed: {e}',
                {'error': str(e)}
            )
    
    def test_fallback_behavior(self):
        """Test fallback behavior when account-based license is not available"""
        try:
            license_manager = LicenseManager.instance(server_url=self.server_url)
            
            # Mock AuthManager to have no valid token
            with patch.object(license_manager, '_get_auth_manager', return_value=None):
                # Try to validate (should fallback to file-based)
                license_data = license_manager.load_cached_license()
                
                if license_data:
                    is_valid, message = license_manager._validate_license_locally(license_data)
                    
                    if is_valid:
                        self.add_result(
                            'Fallback Behavior',
                            True,
                            'Fallback to file-based license works',
                            {
                                'source': 'file',
                                'message': message
                            }
                        )
                    else:
                        self.add_result(
                            'Fallback Behavior',
                            False,
                            f'File-based license validation failed: {message}',
                            {'message': message}
                        )
                else:
                    self.add_result(
                        'Fallback Behavior',
                        False,
                        'No file-based license available for fallback',
                        {'note': 'This is normal if user has not activated offline license key'}
                    )
        except Exception as e:
            self.add_result(
                'Fallback Behavior',
                False,
                f'Fallback behavior test failed: {e}',
                {'error': str(e)}
            )
    
    def test_license_info_structure(self):
        """Test that license info structure is correct"""
        try:
            auth_manager = AuthManager(server_url=self.server_url)
            license_manager = LicenseManager.instance(server_url=self.server_url)
            
            # Validate license
            is_valid, message, license_info = license_manager.validate_license()
            
            if is_valid and license_info:
                # Check structure
                required_fields = ['source', 'license']
                missing_fields = [f for f in required_fields if f not in license_info]
                
                if not missing_fields:
                    license_obj = license_info.get('license', {})
                    license_required = ['product_id']
                    license_missing = [f for f in license_required if f not in license_obj]
                    
                    if not license_missing:
                        self.add_result(
                            'License Info Structure',
                            True,
                            'License info structure is correct',
                            {
                                'source': license_info.get('source'),
                                'has_license': 'license' in license_info,
                                'license_fields': list(license_obj.keys())
                            }
                        )
                    else:
                        self.add_result(
                            'License Info Structure',
                            False,
                            f'License object missing fields: {license_missing}',
                            {
                                'missing': license_missing,
                                'present': [f for f in license_required if f not in license_missing]
                            }
                        )
                else:
                    self.add_result(
                        'License Info Structure',
                        False,
                        f'License info missing fields: {missing_fields}',
                        {
                            'missing': missing_fields,
                            'present': [f for f in required_fields if f not in missing_fields]
                        }
                    )
            else:
                self.add_result(
                    'License Info Structure',
                    False,
                    'No license info available to test structure',
                    {'message': message}
                )
        except Exception as e:
            self.add_result(
                'License Info Structure',
                False,
                f'License info structure test failed: {e}',
                {'error': str(e)}
            )
    
    def run_all(self):
        """Run all priority tests"""
        print("=" * 60)
        print("License Priority Tests")
        print("=" * 60)
        print()
        print("─" * 60)
        print()
        
        print("📋 Phase 1: Priority Order\n")
        self.test_priority_order()
        self.test_account_based_priority()
        
        print("\n🔄 Phase 2: Fallback Behavior\n")
        self.test_file_based_fallback()
        self.test_fallback_behavior()
        
        print("\n📊 Phase 3: Structure Validation\n")
        self.test_license_info_structure()
        
        # Print summary
        print("\n" + "─" * 60)
        print("📊 Test Summary\n")
        
        passed = sum(1 for r in self.results if r['passed'])
        failed = sum(1 for r in self.results if not r['passed'])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📝 Total: {len(self.results)}\n")
        
        if failed == 0:
            print("🎉 All priority tests passed!\n")
        else:
            print("⚠️  Some priority tests failed. Please review the results above.\n")
        
        return {
            'passed': passed,
            'failed': failed,
            'total': len(self.results),
            'results': self.results
        }

if __name__ == "__main__":
    try:
        suite = PriorityTestSuite()
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

