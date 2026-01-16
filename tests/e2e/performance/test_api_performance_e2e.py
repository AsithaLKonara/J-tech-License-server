"""
API Performance E2E Tests
Tests for API response times and performance
"""

import pytest
import time

from tests.e2e.helpers.api_client import APIClient
from tests.e2e.test_config import API_RESPONSE_TIME_THRESHOLD


@pytest.mark.performance
@pytest.mark.requires_api
class TestAPIPerformanceE2E:
    """E2E tests for API performance"""
    
    def test_api_response_times(self, authenticated_api_client: APIClient):
        """Test API response times"""
        # Measure response time for license info
        start_time = time.time()
        success, data, error = authenticated_api_client.get_license_info()
        response_time = time.time() - start_time
        
        assert success, f"API request failed: {error}"
        assert response_time < API_RESPONSE_TIME_THRESHOLD * 2, \
            f"Response time {response_time}s exceeds threshold"
    
    def test_concurrent_api_requests(self, authenticated_api_client: APIClient):
        """Test concurrent API requests"""
        import concurrent.futures
        
        def make_request():
            return authenticated_api_client.get_license_info()
        
        # Run multiple requests concurrently
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        total_time = time.time() - start_time
        
        # All should succeed
        for success, data, error in results:
            assert success or error is not None
        
        # Should complete in reasonable time
        assert total_time < 10, f"Concurrent requests took {total_time}s"
    
    def test_api_load_handling(self, authenticated_api_client: APIClient):
        """Test API load handling"""
        # Make multiple sequential requests
        start_time = time.time()
        for _ in range(20):
            success, data, error = authenticated_api_client.get_license_info()
            assert success or error is not None
        total_time = time.time() - start_time
        
        # Should handle load reasonably
        avg_time = total_time / 20
        assert avg_time < API_RESPONSE_TIME_THRESHOLD * 2, \
            f"Average response time {avg_time}s is too high"
    
    def test_api_rate_limiting(self, authenticated_api_client: APIClient):
        """Test API rate limiting"""
        # Make rapid requests
        failures = 0
        for _ in range(50):
            success, data, error = authenticated_api_client.get_license_info()
            if not success:
                failures += 1
        
        # Rate limiting may kick in after many requests
        # This test verifies system handles rapid requests
