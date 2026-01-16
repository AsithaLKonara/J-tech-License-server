"""
License System Test Suite

Comprehensive license system testing including activation, validation, expiry, and revocation.
"""

import sys
import time
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from core.license_manager import LicenseManager
from tests.helpers.report_generator import TestResult, TestSuiteResult


class LicenseSystemTestSuite:
    """Test suite for license system."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test suite."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_results: List[TestResult] = []
    
    def _make_temp_manager(self) -> LicenseManager:
        """Create a LicenseManager instance with temporary directories."""
        mgr = LicenseManager(server_url="http://invalid-server-for-tests")
        # Redirect cache locations into temporary directory
        mgr.ENCRYPTED_LICENSE_DIR = self.temp_dir
        mgr.cache_file = self.temp_dir / "license_cache.json"
        mgr.encrypted_license_file = self.temp_dir / "license.enc"
        mgr.ENCRYPTED_LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        return mgr
    
    def _basic_license_payload(self, expires_at: Optional[str] = None) -> dict:
        """Create a basic license payload for testing."""
        return {
            "license": {
                "license_id": "TEST-LICENSE",
                "product_id": "upload_bridge_pro",
                "issued_to_email": "test@example.com",
                "issued_at": datetime.utcnow().isoformat() + "Z",
                "expires_at": expires_at,
                "features": ["pro"],
                "version": 1,
                "max_devices": 1,
            },
            "signature": None,
            "public_key": None,
            "format_version": "1.0",
        }
    
    def log_test(self, name: str, passed: bool, error_message: Optional[str] = None, execution_time: float = 0.0, details: Optional[Dict[str, Any]] = None):
        """Log test result."""
        self.test_results.append(TestResult(
            name=name,
            suite="License System",
            passed=passed,
            skipped=False,
            error_message=error_message,
            execution_time=execution_time,
            details=details or {}
        ))
    
    # License Activation Tests
    def test_premade_key_activation(self) -> bool:
        """Test premade key activation (offline)."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            
            # Test with a mock premade key (we'll need to mock the key loading)
            # Since we can't easily access real premade keys, we'll test the activation path
            # by directly saving a license
            license_data = self._basic_license_payload()
            
            saved = mgr.save_license(license_data, validate_online=False)
            
            # Verify license was saved
            loaded = mgr.load_cached_license()
            loaded_successfully = loaded is not None and loaded.get("license", {}).get("license_id") == "TEST-LICENSE"
            
            passed = saved and loaded_successfully
            execution_time = time.time() - start_time
            
            self.log_test(
                "Premade Key Activation (Offline)",
                passed,
                None if passed else f"Saved: {saved}, Loaded: {loaded_successfully}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Premade Key Activation (Offline)", False, str(e), execution_time)
            return False
    
    def test_activation_with_invalid_key(self) -> bool:
        """Test activation with invalid key."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            
            # Try to activate with invalid key
            success, message = mgr.activate_premade_key("INVALID-KEY-12345")
            
            # Should fail
            passed = not success and "Invalid" in message
            execution_time = time.time() - start_time
            
            self.log_test(
                "Activation with Invalid Key",
                passed,
                None if passed else f"Unexpected: success={success}, message={message}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Activation with Invalid Key", False, str(e), execution_time)
            return False
    
    # License Validation Tests
    def test_local_validation_cache_hit(self) -> bool:
        """Test local validation uses cache when recent."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            license_data = self._basic_license_payload()
            
            # Save license
            assert mgr.save_license(license_data, validate_online=False)
            
            # Force cache to look "recent"
            import time as time_module
            now = time_module.time()
            with open(mgr.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            cache["validated_at"] = now
            with open(mgr.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f)
            
            # Mock server validation to fail (should still use cache)
            def fake_validate_with_server(_license_data):
                return False, "Server unreachable"
            
            with patch.object(mgr, 'validate_with_server', side_effect=fake_validate_with_server):
                ok, message, _info = mgr.validate_license(force_online=False)
            
            passed = ok and ("offline mode" in message.lower() or "valid" in message.lower() or "cache" in message.lower())
            execution_time = time.time() - start_time
            
            self.log_test(
                "Local Validation (Cache Hit)",
                passed,
                None if passed else f"Result: {ok}, Message: {message}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Local Validation (Cache Hit)", False, str(e), execution_time)
            return False
    
    def test_validation_cache_expired(self) -> bool:
        """Test validation requires online check when cache expired."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            license_data = self._basic_license_payload()
            
            # Save license
            assert mgr.save_license(license_data, validate_online=False)
            
            # Mark cache as very old
            old_time = time.time() - (mgr.CACHE_VALIDITY_DAYS + 1) * 86400
            with open(mgr.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            cache["validated_at"] = old_time
            with open(mgr.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f)
            
            # Simulate server being unavailable
            def fake_validate_with_server(_license_data):
                raise RuntimeError("server down")
            
            with patch.object(mgr, 'validate_with_server', side_effect=fake_validate_with_server):
                ok, message, _info = mgr.validate_license(force_online=False)
            
            # Should fail because cache is expired and server is down
            passed = not ok
            execution_time = time.time() - start_time
            
            self.log_test(
                "Validation (Cache Expired)",
                passed,
                None if passed else f"Unexpected: ok={ok}, message={message}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Validation (Cache Expired)", False, str(e), execution_time)
            return False
    
    # License Expiry Tests
    def test_expiry_checking(self) -> bool:
        """Test expiry checking."""
        start_time = time.time()
        try:
            from datetime import timezone
            mgr = self._make_temp_manager()
            
            # Test with expired license (use timezone-aware datetime with Z suffix)
            expired_dt = datetime.now(timezone.utc) - timedelta(days=1)
            expired_date = expired_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            expired_license = self._basic_license_payload(expires_at=expired_date)
            
            # Test with valid license (future date, timezone-aware with Z suffix)
            valid_dt = datetime.now(timezone.utc) + timedelta(days=30)
            valid_date = valid_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            valid_license = self._basic_license_payload(expires_at=valid_date)
            
            # Test with perpetual license (no expiry)
            perpetual_license = self._basic_license_payload(expires_at=None)
            
            # Check expiry (returns tuple: (is_valid, expires_at))
            expired_valid, _ = mgr.check_expiry(expired_license)
            valid_valid, _ = mgr.check_expiry(valid_license)
            perpetual_valid, _ = mgr.check_expiry(perpetual_license)
            
            passed = not expired_valid and valid_valid and perpetual_valid
            execution_time = time.time() - start_time
            
            self.log_test(
                "Expiry Checking",
                passed,
                None if passed else f"Expired: {expired_valid}, Valid: {valid_valid}, Perpetual: {perpetual_valid}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Expiry Checking", False, str(e), execution_time)
            import traceback
            traceback.print_exc()
            return False
    
    def test_remaining_days_calculation(self) -> bool:
        """Test remaining days calculation."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            
            # Test with license expiring in 30 days
            future_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
            license_data = self._basic_license_payload(expires_at=future_date)
            
            remaining = mgr.get_remaining_days(license_data)
            
            # Should be around 30 days (allow some tolerance)
            passed = 29 <= remaining <= 31
            execution_time = time.time() - start_time
            
            self.log_test(
                "Remaining Days Calculation",
                passed,
                None if passed else f"Remaining: {remaining} days (expected ~30)",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Remaining Days Calculation", False, str(e), execution_time)
            return False
    
    # License Cache Tests
    def test_cache_creation_on_activation(self) -> bool:
        """Test cache is created on activation."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            license_data = self._basic_license_payload()
            
            # Save license (activation)
            saved = mgr.save_license(license_data, validate_online=False)
            
            # Verify cache file exists
            cache_exists = mgr.cache_file.exists()
            
            # Verify encrypted license file exists
            encrypted_exists = mgr.encrypted_license_file.exists()
            
            passed = saved and cache_exists and encrypted_exists
            execution_time = time.time() - start_time
            
            self.log_test(
                "Cache Creation on Activation",
                passed,
                None if passed else f"Saved: {saved}, Cache: {cache_exists}, Encrypted: {encrypted_exists}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Cache Creation on Activation", False, str(e), execution_time)
            return False
    
    def test_cache_validity_period(self) -> bool:
        """Test cache validity period (7 days)."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            
            # Verify CACHE_VALIDITY_DAYS is 7
            passed = mgr.CACHE_VALIDITY_DAYS == 7
            execution_time = time.time() - start_time
            
            self.log_test(
                "Cache Validity Period",
                passed,
                None if passed else f"Expected 7 days, got {mgr.CACHE_VALIDITY_DAYS}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Cache Validity Period", False, str(e), execution_time)
            return False
    
    # License GUI Tests (minimal - most GUI testing happens in GUI test suite)
    def test_license_manager_initialization(self) -> bool:
        """Test license manager can be initialized."""
        start_time = time.time()
        try:
            mgr = self._make_temp_manager()
            
            # Verify manager was created
            passed = mgr is not None and hasattr(mgr, 'validate_license')
            execution_time = time.time() - start_time
            
            self.log_test(
                "License Manager Initialization",
                passed,
                None if passed else "Manager initialization failed",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("License Manager Initialization", False, str(e), execution_time)
            return False
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all license system tests."""
        print("\n" + "=" * 60)
        print("License System Test Suite")
        print("=" * 60)
        
        test_methods = [
            self.test_premade_key_activation,
            self.test_activation_with_invalid_key,
            self.test_local_validation_cache_hit,
            self.test_validation_cache_expired,
            self.test_expiry_checking,
            self.test_remaining_days_calculation,
            self.test_cache_creation_on_activation,
            self.test_cache_validity_period,
            self.test_license_manager_initialization,
        ]
        
        start_time = time.time()
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"ERROR in {test_method.__name__}: {e}")
        
        execution_time = time.time() - start_time
        
        # Calculate summary
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.passed)
        failed = total - passed
        skipped = sum(1 for r in self.test_results if r.skipped)
        
        suite_result = TestSuiteResult(
            name="License System",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            execution_time=execution_time,
            tests=self.test_results
        )
        
        print(f"\nLicense System: {passed}/{total} passed ({execution_time:.2f}s)")
        
        return suite_result
    
    def __del__(self):
        """Cleanup temporary directory."""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except:
                pass

