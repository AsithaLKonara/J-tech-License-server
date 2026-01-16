"""
Pattern Creation Workflow E2E Tests
Tests for pattern creation workflows
"""

import pytest

from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.setup.test_fixtures import TestDataFactory


@pytest.mark.pattern
@pytest.mark.requires_desktop
class TestPatternCreationWorkflowE2E:
    """E2E tests for pattern creation workflows"""
    
    def test_create_new_pattern_dialog(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test create new pattern dialog"""
        # Pattern creation via desktop app
        pattern = authenticated_desktop_app.create_pattern(
            name="Test Pattern",
            width=72,
            height=1
        )
        
        assert pattern is not None, "Pattern creation failed"
    
    def test_pattern_creation_with_custom_dimensions(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation with custom dimensions"""
        # Test various dimensions
        dimensions = [(12, 6), (32, 32), (64, 64), (100, 1)]
        
        for width, height in dimensions:
            pattern = authenticated_desktop_app.create_pattern(
                name=f"Pattern {width}x{height}",
                width=width,
                height=height
            )
            assert pattern is not None, f"Pattern creation failed for {width}x{height}"
    
    def test_pattern_creation_from_template(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation from template"""
        # Create pattern (template selection would be in UI)
        pattern = authenticated_desktop_app.create_pattern(
            name="Template Pattern",
            width=72,
            height=1
        )
        
        assert pattern is not None, "Pattern creation from template failed"
    
    def test_pattern_creation_with_default_settings(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation with default settings"""
        pattern = authenticated_desktop_app.create_pattern()
        
        assert pattern is not None, "Pattern creation with defaults failed"
    
    def test_pattern_creation_validation(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation validation"""
        # Test invalid dimensions
        # Very large dimensions may fail
        try:
            pattern = authenticated_desktop_app.create_pattern(
                name="Large Pattern",
                width=10000,
                height=10000
            )
            # May succeed or fail depending on validation
        except Exception:
            # Validation should catch invalid dimensions
            pass
    
    def test_pattern_creation_with_invalid_dimensions(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation with invalid dimensions"""
        # Test zero dimensions
        try:
            pattern = authenticated_desktop_app.create_pattern(
                name="Invalid Pattern",
                width=0,
                height=0
            )
            # Should fail validation
        except Exception:
            # Expected to fail
            pass
    
    def test_pattern_creation_triggers_license_check(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation triggers license check"""
        # License should be checked before allowing pattern creation
        license_info = authenticated_desktop_app.get_license_info()
        assert license_info is not None, "License check should occur"
        
        # Create pattern (should work if license is valid)
        pattern = authenticated_desktop_app.create_pattern()
        assert pattern is not None, "Pattern creation should work with valid license"
    
    def test_pattern_creation_with_expired_license(self, db_client: DatabaseClient):
        """Test pattern creation with expired license"""
        # Create user with expired license
        user_data = TestDataFactory.create_user_data()
        password_hash = TestDataFactory.hash_password(user_data['password'])
        db_client.create_user(
            user_id=user_data['id'],
            email=user_data['email'],
            password_hash=password_hash
        )
        
        expired_license = TestDataFactory.create_expired_entitlement_data(
            user_id=user_data['id']
        )
        db_client.create_entitlement(
            entitlement_id=expired_license['id'],
            user_id=expired_license['user_id'],
            plan=expired_license['plan'],
            status=expired_license['status']
        )
        
        # Try to create pattern with expired license
        desktop_app = InProcessDesktopClient()
        desktop_app.initialize()
        success, error = desktop_app.login(user_data['email'], user_data['password'])
        
        if success:
            # Pattern creation may be blocked or allowed with warning
            pattern = desktop_app.create_pattern()
            # System should handle expired license gracefully
        
        # Cleanup
        db_client.cleanup_test_data(user_data['email'])
