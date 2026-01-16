"""
E2E Test Configuration
Configuration for end-to-end tests including URLs, credentials, and test settings
"""

import os
from pathlib import Path

# Base URLs
WEB_DASHBOARD_URL = os.environ.get('WEB_DASHBOARD_URL', 'http://localhost:8000')
API_BASE_URL = f"{WEB_DASHBOARD_URL}/api/v2"

# Database Configuration
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))  # Changed from 3307 to match MySQL default port
DB_NAME = os.environ.get('DB_NAME', 'upload_bridge_test')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

# Test User Credentials
TEST_USER_EMAIL = os.environ.get('TEST_USER_EMAIL', 'test@example.com')
TEST_USER_PASSWORD = os.environ.get('TEST_USER_PASSWORD', 'testpassword123')
TEST_ADMIN_EMAIL = os.environ.get('TEST_ADMIN_EMAIL', 'admin@example.com')
TEST_ADMIN_PASSWORD = os.environ.get('TEST_ADMIN_PASSWORD', 'adminpassword123')

# Test Settings
TEST_TIMEOUT = int(os.environ.get('TEST_TIMEOUT', '30'))  # seconds
API_RETRY_ATTEMPTS = int(os.environ.get('API_RETRY_ATTEMPTS', '3'))
API_RETRY_DELAY = float(os.environ.get('API_RETRY_DELAY', '1.0'))

# Test Data Directories
TEST_DATA_DIR = Path(__file__).parent.parent / 'data'
TEST_PATTERNS_DIR = TEST_DATA_DIR / 'patterns'
TEST_EXPORTS_DIR = TEST_DATA_DIR / 'exports'

# Desktop App Configuration
DESKTOP_APP_PATH = os.environ.get('DESKTOP_APP_PATH', None)  # Path to desktop app executable
DESKTOP_APP_TIMEOUT = int(os.environ.get('DESKTOP_APP_TIMEOUT', '60'))  # seconds

# Test Isolation
USE_TEST_DATABASE = os.environ.get('USE_TEST_DATABASE', 'true').lower() == 'true'
CLEANUP_AFTER_TESTS = os.environ.get('CLEANUP_AFTER_TESTS', 'true').lower() == 'true'

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', None)  # None = console only

# Performance Test Thresholds
API_RESPONSE_TIME_THRESHOLD = float(os.environ.get('API_RESPONSE_TIME_THRESHOLD', '1.0'))  # seconds
DB_QUERY_TIME_THRESHOLD = float(os.environ.get('DB_QUERY_TIME_THRESHOLD', '0.5'))  # seconds

# License Test Settings
TEST_LICENSE_PLANS = ['trial', 'monthly', 'yearly', 'perpetual']
TEST_LICENSE_STATUSES = ['active', 'inactive', 'cancelled', 'expired']

# Pattern Test Settings
TEST_PATTERN_DIMENSIONS = [
    (72, 1),   # Standard LED strip
    (12, 6),   # Small matrix
    (32, 32),  # Medium matrix
    (64, 64),  # Large matrix
]

# Ensure test directories exist
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
TEST_PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
TEST_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
