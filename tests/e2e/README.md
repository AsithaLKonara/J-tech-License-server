# E2E Test Suite

Comprehensive end-to-end test suite for Upload Bridge system.

## Structure

```
tests/e2e/
├── conftest.py                    # Pytest fixtures and configuration
├── test_config.py                 # Test configuration
├── pytest.ini                    # Pytest settings
├── run_all_tests.py              # Test runner script
├── setup/                         # Test setup and fixtures
│   ├── test_environment.py       # Environment setup
│   └── test_fixtures.py          # Test data factories
├── helpers/                       # Helper utilities
│   ├── api_client.py             # API client wrapper
│   ├── database_client.py        # Database client
│   └── desktop_app_client.py     # Desktop app client
├── license-system/                # License system tests
├── authentication/                # Authentication tests
├── user-management/               # User management tests
├── pattern-creation/              # Pattern creation tests
├── user-journeys/                 # User journey tests
├── integration/                   # Integration tests
├── error-handling/                # Error handling tests
└── performance/                   # Performance tests
```

## Running Tests

### Run All Tests
```bash
pytest tests/e2e/ -v
```

### Run by Category
```bash
# License tests
pytest tests/e2e/license-system/ -v

# Authentication tests
pytest tests/e2e/authentication/ -v

# User management tests
pytest tests/e2e/user-management/ -v

# Pattern creation tests
pytest tests/e2e/pattern-creation/ -v

# User journey tests
pytest tests/e2e/user-journeys/ -v

# Integration tests
pytest tests/e2e/integration/ -v

# Error handling tests
pytest tests/e2e/error-handling/ -v

# Performance tests
pytest tests/e2e/performance/ -v
```

### Run by Marker
```bash
pytest tests/e2e/ -m license -v
pytest tests/e2e/ -m auth -v
pytest tests/e2e/ -m "license or auth" -v
```

### Run with Coverage
```bash
pytest tests/e2e/ --cov=apps/upload-bridge --cov=apps/web-dashboard -v
```

### Run in Parallel
```bash
pytest tests/e2e/ -n auto -v
```

## Configuration

Set environment variables for test configuration:

```bash
export WEB_DASHBOARD_URL=http://localhost:8000
export DB_HOST=127.0.0.1
export DB_PORT=3307
export DB_NAME=upload_bridge_test
export DB_USER=root
export DB_PASSWORD=your_password
```

## Prerequisites

1. MySQL server running
2. Web dashboard server running
3. Test database created and migrated
4. Python dependencies installed:
   - pytest
   - pytest-xdist (for parallel execution)
   - pytest-cov (for coverage)
   - requests
   - mysql-connector-python

## Test Categories

- **License System**: License validation, features, info
- **Authentication**: Email/password, magic link, tokens, sessions
- **User Management**: Registration, profile, devices
- **Pattern Creation**: Workflows, operations, design tools
- **User Journeys**: Complete user flows
- **Integration**: Cross-system integration
- **Error Handling**: Network, database, validation errors
- **Performance**: API, database, desktop app performance
