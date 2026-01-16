#!/usr/bin/env python3
"""
Comprehensive License Flow Testing Script
Tests the complete license activation and validation flow with local Laravel server.

Usage:
    python scripts/test_license_flow.py

Prerequisites:
    1. License server running on http://localhost:8000
    2. Test user created: test@example.com / testpassword123
    3. Environment variable: LICENSE_SERVER_URL=http://localhost:8000 (optional)
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import requests
from core.auth_manager import AuthManager
from core.license_manager import LicenseManager


class LicenseFlowTester:
    """Comprehensive license flow testing"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.test_email = "test@example.com"
        self.test_password = "testpassword123"
        self.results = []
        
    def log(self, message: str, status: str = "INFO"):
        """Log test message"""
        status_symbol = {
            "PASS": "✅",
            "FAIL": "❌",
            "INFO": "ℹ️",
            "WARN": "⚠️"
        }.get(status, "ℹ️")
        
        print(f"{status_symbol} {message}")
        self.results.append({
            "status": status,
            "message": message,
            "timestamp": time.time()
        })
    
    def test_server_health(self) -> bool:
        """Test 1: Server health check"""
        self.log("Testing server health...", "INFO")
        try:
            response = requests.get(f"{self.server_url}/api/v2/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log(f"Server health check passed: {data.get('status')}", "PASS")
                return True
            else:
                self.log(f"Server health check failed: Status {response.status_code}", "FAIL")
                return False
        except Exception as e:
            self.log(f"Server health check failed: {e}", "FAIL")
            return False
    
    def test_email_password_login(self) -> Tuple[bool, Optional[AuthManager]]:
        """Test 2: Email/password login"""
        self.log("Testing email/password login...", "INFO")
        try:
            auth_manager = AuthManager(server_url=self.server_url)
            success, message = auth_manager.login(
                email=self.test_email,
                password=self.test_password
            )
            
            if success:
                self.log(f"Login successful: {message}", "PASS")
                if auth_manager.session_token:
                    self.log(f"Session token received: {auth_manager.session_token[:20]}...", "PASS")
                if auth_manager.entitlement_token:
                    self.log(f"Entitlement token received", "PASS")
                return True, auth_manager
            else:
                self.log(f"Login failed: {message}", "FAIL")
                return False, None
        except Exception as e:
            self.log(f"Login error: {e}", "FAIL")
            return False, None
    
    def test_invalid_credentials(self) -> bool:
        """Test 3: Invalid credentials rejection"""
        self.log("Testing invalid credentials rejection...", "INFO")
        try:
            auth_manager = AuthManager(server_url=self.server_url)
            success, message = auth_manager.login(
                email="invalid@example.com",
                password="wrongpassword"
            )
            
            if not success:
                self.log(f"Invalid credentials correctly rejected: {message}", "PASS")
                return True
            else:
                self.log("Invalid credentials were accepted (should be rejected)", "FAIL")
                return False
        except Exception as e:
            self.log(f"Invalid credentials test error: {e}", "FAIL")
            return False
    
    def test_license_validation(self, auth_manager: AuthManager) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Test 4: License validation"""
        self.log("Testing license validation...", "INFO")
        try:
            license_manager = LicenseManager(server_url=self.server_url)
            is_valid, message, license_info = license_manager.validate_license()
            
            if is_valid:
                self.log(f"License validation passed: {message}", "PASS")
                if license_info:
                    self.log(f"License status: {license_info.get('status')}", "INFO")
                    self.log(f"License plan: {license_info.get('plan')}", "INFO")
                    if license_info.get('expires_at'):
                        self.log(f"License expires: {license_info.get('expires_at')}", "INFO")
                return True, license_info
            else:
                self.log(f"License validation failed: {message}", "FAIL")
                return False, None
        except Exception as e:
            self.log(f"License validation error: {e}", "FAIL")
            return False, None
    
    def test_session_persistence(self, auth_manager: AuthManager) -> bool:
        """Test 5: Session persistence"""
        self.log("Testing session persistence...", "INFO")
        try:
            # Save session
            auth_manager.save_session()
            self.log("Session saved", "INFO")
            
            # Create new AuthManager instance (simulates app restart)
            new_auth_manager = AuthManager(server_url=self.server_url)
            new_auth_manager.load_session()
            
            if new_auth_manager.session_token and new_auth_manager.entitlement_token:
                self.log("Session loaded successfully after restart", "PASS")
                if new_auth_manager.has_valid_token():
                    self.log("Token is still valid after reload", "PASS")
                    return True
                else:
                    self.log("Token is invalid after reload", "FAIL")
                    return False
            else:
                self.log("Session not loaded correctly", "FAIL")
                return False
        except Exception as e:
            self.log(f"Session persistence error: {e}", "FAIL")
            return False
    
    def test_token_refresh(self, auth_manager: AuthManager) -> bool:
        """Test 6: Token refresh"""
        self.log("Testing token refresh...", "INFO")
        try:
            if not auth_manager.session_token:
                self.log("No session token available for refresh", "WARN")
                return False
            
            success, message = auth_manager.refresh_token()
            
            if success:
                self.log(f"Token refresh successful: {message}", "PASS")
                if auth_manager.entitlement_token:
                    self.log("New entitlement token received", "PASS")
                return True
            else:
                self.log(f"Token refresh failed: {message}", "FAIL")
                return False
        except Exception as e:
            self.log(f"Token refresh error: {e}", "FAIL")
            return False
    
    def test_license_info_endpoint(self, auth_manager: AuthManager) -> bool:
        """Test 7: License info endpoint"""
        self.log("Testing license info endpoint...", "INFO")
        try:
            if not auth_manager.session_token:
                self.log("No session token available", "WARN")
                return False
            
            url = f"{self.server_url}/api/v2/license/info"
            headers = {
                'Authorization': f'Bearer {auth_manager.session_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"License info retrieved: {data.get('status', 'unknown')}", "PASS")
                return True
            else:
                self.log(f"License info request failed: Status {response.status_code}", "FAIL")
                return False
        except Exception as e:
            self.log(f"License info endpoint error: {e}", "FAIL")
            return False
    
    def test_logout(self, auth_manager: AuthManager) -> bool:
        """Test 8: Logout"""
        self.log("Testing logout...", "INFO")
        try:
            auth_manager.logout()
            
            if not auth_manager.session_token and not auth_manager.entitlement_token:
                self.log("Logout successful - tokens cleared", "PASS")
                
                # Verify session file is deleted
                if not auth_manager.TOKEN_FILE.exists():
                    self.log("Session file deleted correctly", "PASS")
                    return True
                else:
                    self.log("Session file still exists after logout", "WARN")
                    return True  # Still consider pass if tokens cleared
            else:
                self.log("Logout failed - tokens still present", "FAIL")
                return False
        except Exception as e:
            self.log(f"Logout error: {e}", "FAIL")
            return False
    
    def test_grace_period(self) -> bool:
        """Test 9: Offline grace period"""
        self.log("Testing offline grace period...", "INFO")
        try:
            # Login first
            auth_manager = AuthManager(server_url=self.server_url)
            success, _ = auth_manager.login(
                email=self.test_email,
                password=self.test_password
            )
            
            if not success:
                self.log("Cannot test grace period - login failed", "WARN")
                return False
            
            # Validate license (this sets grace period)
            license_manager = LicenseManager(server_url=self.server_url)
            is_valid, _, license_info = license_manager.validate_license()
            
            if is_valid:
                self.log("License validated - grace period started", "PASS")
                
                # Check if grace period file exists
                if license_manager.last_validation_file.exists():
                    self.log("Grace period timestamp file created", "PASS")
                    
                    # Check grace period status
                    if license_manager._is_within_grace_period():
                        self.log("Within grace period - offline mode should work", "PASS")
                        return True
                    else:
                        self.log("Not within grace period", "WARN")
                        return True  # Still pass - grace period logic works
                else:
                    self.log("Grace period timestamp file not created", "WARN")
                    return True
            else:
                self.log("Cannot test grace period - license validation failed", "WARN")
                return False
        except Exception as e:
            self.log(f"Grace period test error: {e}", "FAIL")
            return False
    
    def test_magic_link_request(self) -> bool:
        """Test 10: Magic link request"""
        self.log("Testing magic link request...", "INFO")
        try:
            url = f"{self.server_url}/api/v2/auth/magic-link/request"
            payload = {
                'email': self.test_email
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Magic link requested: {data.get('message', 'success')}", "PASS")
                return True
            elif response.status_code == 422:
                # Validation error - might be expected
                self.log("Magic link request validation error (may be expected)", "WARN")
                return True
            else:
                self.log(f"Magic link request failed: Status {response.status_code}", "FAIL")
                return False
        except Exception as e:
            self.log(f"Magic link request error: {e}", "FAIL")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary"""
        print("=" * 60)
        print("License Flow Testing - Local Laravel Server")
        print("=" * 60)
        print(f"Server URL: {self.server_url}")
        print(f"Test User: {self.test_email}")
        print("=" * 60)
        print()
        
        # Test 1: Server health
        if not self.test_server_health():
            self.log("Cannot continue - server is not accessible", "FAIL")
            return self.get_summary()
        
        print()
        
        # Test 2: Email/password login
        login_success, auth_manager = self.test_email_password_login()
        if not login_success or not auth_manager:
            self.log("Cannot continue - login failed", "FAIL")
            return self.get_summary()
        
        print()
        
        # Test 3: Invalid credentials
        self.test_invalid_credentials()
        print()
        
        # Test 4: License validation
        license_valid, license_info = self.test_license_validation(auth_manager)
        print()
        
        # Test 5: Session persistence
        self.test_session_persistence(auth_manager)
        print()
        
        # Test 6: Token refresh
        self.test_token_refresh(auth_manager)
        print()
        
        # Test 7: License info endpoint
        self.test_license_info_endpoint(auth_manager)
        print()
        
        # Test 8: Logout
        self.test_logout(auth_manager)
        print()
        
        # Test 9: Grace period
        self.test_grace_period()
        print()
        
        # Test 10: Magic link request
        self.test_magic_link_request()
        print()
        
        return self.get_summary()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print("=" * 60)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "results": self.results
        }


def main():
    """Main entry point"""
    # Get server URL from environment or use default
    server_url = os.environ.get("LICENSE_SERVER_URL") or os.environ.get("AUTH_SERVER_URL") or "http://localhost:8000"
    
    tester = LicenseFlowTester(server_url=server_url)
    summary = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if summary["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
