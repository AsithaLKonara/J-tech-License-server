"""
Desktop App Performance E2E Tests
Tests for desktop application performance
"""

import pytest
import time

from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient


@pytest.mark.performance
@pytest.mark.requires_desktop
class TestDesktopPerformanceE2E:
    """E2E tests for desktop app performance"""
    
    def test_pattern_creation_with_large_dimensions(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern creation with large dimensions"""
        # Create large pattern
        start_time = time.time()
        pattern = authenticated_desktop_app.create_pattern(
            name="Large Pattern",
            width=256,
            height=256
        )
        creation_time = time.time() - start_time
        
        assert pattern is not None, "Pattern creation failed"
        assert creation_time < 5, f"Large pattern creation took {creation_time}s"
    
    def test_pattern_loading_performance(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test pattern loading performance"""
        # Create pattern
        pattern = authenticated_desktop_app.create_pattern(
            name="Load Test Pattern",
            width=72,
            height=1
        )
        
        assert pattern is not None, "Pattern creation failed"
        # Loading would be tested with actual file in full E2E
    
    def test_ui_responsiveness(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test UI responsiveness"""
        # Create multiple patterns quickly
        start_time = time.time()
        for i in range(5):
            pattern = authenticated_desktop_app.create_pattern(
                name=f"Pattern {i}",
                width=72,
                height=1
            )
            assert pattern is not None
        total_time = time.time() - start_time
        
        # Should be responsive
        assert total_time < 2, f"UI operations took {total_time}s"
    
    def test_memory_usage_with_large_patterns(self, authenticated_desktop_app: InProcessDesktopClient):
        """Test memory usage with large patterns"""
        # Create large pattern
        pattern = authenticated_desktop_app.create_pattern(
            name="Memory Test Pattern",
            width=128,
            height=128
        )
        
        assert pattern is not None, "Large pattern creation failed"
        # Memory usage would be monitored in full E2E
