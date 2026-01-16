"""
Pytest Configuration and Fixtures for E2E Tests
Provides shared fixtures for all E2E tests
"""

import pytest
import logging
from typing import Generator, Optional

from tests.e2e.test_config import (
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    CLEANUP_AFTER_TESTS
)
from tests.e2e.setup.test_environment import get_test_environment
from tests.e2e.helpers.api_client import APIClient
from tests.e2e.helpers.database_client import DatabaseClient
from tests.e2e.helpers.desktop_app_client import InProcessDesktopClient
from tests.e2e.setup.test_fixtures import TestDataFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_environment():
    """Setup test environment for entire test session"""
    env = get_test_environment()
    success, error = env.setup()
    if not success:
        pytest.fail(f"Test environment setup failed: {error}")
    
    yield env
    
    if CLEANUP_AFTER_TESTS:
        env.teardown()


@pytest.fixture(scope="session")
def api_client(test_environment) -> APIClient:
    """API client fixture"""
    return APIClient()


@pytest.fixture(scope="session")
def db_client(test_environment) -> DatabaseClient:
    """Database client fixture"""
    return DatabaseClient()


@pytest.fixture(scope="function")
def authenticated_api_client(api_client: APIClient, test_user_data) -> APIClient:
    """API client with authentication"""
    email = test_user_data['email']
    password = test_user_data['password']
    
    success, data, error = api_client.login(email, password)
    if not success:
        pytest.fail(f"Login failed: {error}")
    
    yield api_client
    
    # Cleanup: logout
    api_client.logout()


@pytest.fixture(scope="function")
def test_user_data() -> dict:
    """Create test user data"""
    return TestDataFactory.create_user_data()


@pytest.fixture(scope="function")
def test_user_in_db(db_client: DatabaseClient, test_user_data: dict) -> Generator[dict, None, None]:
    """Create test user in database"""
    user_data = test_user_data.copy()
    password_hash = TestDataFactory.hash_password(user_data['password'])
    
    # Create user in database
    success = db_client.create_user(
        user_id=user_data['id'],
        email=user_data['email'],
        password_hash=password_hash,
        name=user_data['name'],
        is_admin=user_data['is_admin']
    )
    
    if not success:
        pytest.fail("Failed to create test user in database")
    
    yield user_data
    
    # Cleanup: delete user and all related data
    if CLEANUP_AFTER_TESTS:
        db_client.cleanup_test_data(user_data['email'])


@pytest.fixture(scope="function")
def test_user_with_entitlement(test_user_in_db: dict, db_client: DatabaseClient) -> Generator[dict, None, None]:
    """Create test user with active entitlement"""
    user_data = test_user_in_db
    
    # Create trial entitlement
    entitlement_data = TestDataFactory.create_entitlement_data(
        user_id=user_data['id'],
        plan='trial',
        status='active'
    )
    
    success = db_client.create_entitlement(
        entitlement_id=entitlement_data['id'],
        user_id=entitlement_data['user_id'],
        plan=entitlement_data['plan'],
        status=entitlement_data['status'],
        max_devices=entitlement_data['max_devices']
    )
    
    if not success:
        pytest.fail("Failed to create test entitlement")
    
    user_data['entitlement'] = entitlement_data
    
    yield user_data
    
    # Cleanup handled by test_user_in_db fixture


@pytest.fixture(scope="function")
def desktop_app_client() -> InProcessDesktopClient:
    """Desktop app client fixture (in-process)"""
    client = InProcessDesktopClient()
    success = client.initialize()
    if not success:
        pytest.skip("Desktop app components not available")
    return client


@pytest.fixture(scope="function")
def authenticated_desktop_app(desktop_app_client: InProcessDesktopClient, 
                              test_user_with_entitlement: dict) -> InProcessDesktopClient:
    """Desktop app client with authentication"""
    user_data = test_user_with_entitlement
    
    success, error = desktop_app_client.login(
        email=user_data['email'],
        password=user_data['password']
    )
    
    if not success:
        pytest.fail(f"Desktop app login failed: {error}")
    
    return desktop_app_client


@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test(db_client: DatabaseClient):
    """Auto-cleanup fixture (runs after each test)"""
    yield
    
    # Additional cleanup if needed
    # This runs after each test function


@pytest.fixture(scope="function")
def isolated_test_data(db_client: DatabaseClient) -> Generator[dict, None, None]:
    """Create isolated test data that will be cleaned up"""
    test_data = {
        'users': [],
        'entitlements': [],
        'devices': []
    }
    
    yield test_data
    
    # Cleanup all created test data
    if CLEANUP_AFTER_TESTS:
        for email in test_data['users']:
            db_client.cleanup_test_data(email)


# Pytest hooks
def pytest_configure(config):
    """Configure pytest"""
    # Register custom markers
    config.addinivalue_line("markers", "license: License system tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "user: User management tests")
    config.addinivalue_line("markers", "pattern: Pattern creation tests")
    config.addinivalue_line("markers", "journey: User journey tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "error: Error handling tests")
    config.addinivalue_line("markers", "performance: Performance tests")


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    # Add markers based on test file location
    for item in items:
        test_path = str(item.fspath)
        
        if 'license-system' in test_path:
            item.add_marker(pytest.mark.license)
        elif 'authentication' in test_path:
            item.add_marker(pytest.mark.auth)
        elif 'user-management' in test_path:
            item.add_marker(pytest.mark.user)
        elif 'pattern-creation' in test_path:
            item.add_marker(pytest.mark.pattern)
        elif 'user-journeys' in test_path:
            item.add_marker(pytest.mark.journey)
        elif 'integration' in test_path:
            item.add_marker(pytest.mark.integration)
        elif 'error-handling' in test_path:
            item.add_marker(pytest.mark.error)
        elif 'performance' in test_path:
            item.add_marker(pytest.mark.performance)
