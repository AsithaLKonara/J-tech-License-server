"""
Test Environment Setup
Handles database setup, service health checks, and test data preparation
"""

import logging
import time
import requests
from typing import Tuple, Optional
from pathlib import Path

from tests.e2e.test_config import (
    WEB_DASHBOARD_URL,
    API_BASE_URL,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    USE_TEST_DATABASE
)
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.helpers.api_client import APIClient

logger = logging.getLogger(__name__)


class TestEnvironment:
    """Manages test environment setup and teardown"""
    
    def __init__(self):
        self.db_client = DatabaseClient()
        self.api_client = APIClient()
        self.is_setup = False
    
    def check_api_health(self) -> Tuple[bool, Optional[str]]:
        """Check if API server is running and healthy"""
        try:
            success, error = self.api_client.health_check()
            if success:
                logger.info("API server is healthy")
                return True, None
            else:
                return False, error or "API health check failed"
        except Exception as e:
            return False, f"API health check error: {str(e)}"
    
    def check_database_connection(self) -> Tuple[bool, Optional[str]]:
        """Check if database is accessible"""
        try:
            with self.db_client.get_connection() as conn:
                if conn.is_connected():
                    logger.info("Database connection successful")
                    return True, None
                else:
                    return False, "Database connection failed"
        except Exception as e:
            return False, f"Database connection error: {str(e)}"
    
    def setup_database(self) -> Tuple[bool, Optional[str]]:
        """Setup test database (run migrations if needed)"""
        try:
            # Check if database exists
            with self.db_client.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"USE {DB_NAME}")
                cursor.close()
            
            logger.info("Database setup complete")
            return True, None
        except Exception as e:
            return False, f"Database setup error: {str(e)}"
    
    def wait_for_services(self, max_wait: int = 30) -> Tuple[bool, Optional[str]]:
        """Wait for all services to be ready"""
        logger.info("Waiting for services to be ready...")
        
        start_time = time.time()
        api_ready = False
        db_ready = False
        
        while time.time() - start_time < max_wait:
            # Check API
            if not api_ready:
                api_ready, _ = self.check_api_health()
            
            # Check database
            if not db_ready:
                db_ready, _ = self.check_database_connection()
            
            if api_ready and db_ready:
                logger.info("All services are ready")
                return True, None
            
            time.sleep(1)
        
        issues = []
        if not api_ready:
            issues.append("API server not ready")
        if not db_ready:
            issues.append("Database not ready")
        
        return False, "; ".join(issues)
    
    def setup(self) -> Tuple[bool, Optional[str]]:
        """Complete environment setup"""
        if self.is_setup:
            return True, None
        
        logger.info("Setting up test environment...")
        
        # Wait for services
        success, error = self.wait_for_services()
        if not success:
            return False, error
        
        # Setup database
        success, error = self.setup_database()
        if not success:
            return False, error
        
        self.is_setup = True
        logger.info("Test environment setup complete")
        return True, None
    
    def teardown(self):
        """Cleanup test environment"""
        logger.info("Tearing down test environment...")
        self.is_setup = False
        logger.info("Test environment teardown complete")
    
    def verify_environment(self) -> Tuple[bool, list]:
        """Verify environment is ready for testing"""
        issues = []
        
        # Check API
        api_ready, api_error = self.check_api_health()
        if not api_ready:
            issues.append(f"API: {api_error}")
        
        # Check database
        db_ready, db_error = self.check_database_connection()
        if not db_ready:
            issues.append(f"Database: {db_error}")
        
        return len(issues) == 0, issues


# Global test environment instance
_test_env: Optional[TestEnvironment] = None


def get_test_environment() -> TestEnvironment:
    """Get global test environment instance"""
    global _test_env
    if _test_env is None:
        _test_env = TestEnvironment()
    return _test_env
