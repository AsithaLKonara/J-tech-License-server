# E2E Test Suite for Upload Bridge License System

Complete end-to-end testing suite covering web dashboard, license server API, integration flows, security, and user journeys.

## Test Structure

```
tests/
├── api/                    # API E2E tests
│   ├── auth-e2e.test.js
│   ├── license-e2e.test.js
│   ├── device-e2e.test.js
│   └── ...
├── integration/            # Integration tests
│   ├── auth-integration.test.js
│   ├── license-db.test.js
│   ├── database-e2e.test.js
│   ├── desktop-app-api.test.js
│   ├── stripe-webhook.test.js
│   ├── email-service.test.js
│   └── database-consistency.test.js
├── desktop-app/            # Desktop app integration tests
│   ├── login-flow.test.js
│   ├── license-validation.test.js
│   └── offline-mode.test.js
├── security/               # Security tests
│   └── api-security.test.js
├── e2e/                    # User journey tests
│   ├── complete-user-journey.test.js
│   ├── license-renewal-journey.test.js
│   └── error-handling.test.js
├── helpers/                # Test utilities
│   ├── api-client.js       # Enhanced with retry, logging, parallel
│   ├── db-helpers.js
│   ├── test-data.js        # Enhanced with factories
│   ├── test-environment.js # NEW: Environment utilities
│   └── test-runner.js
├── orchestration/          # Test orchestration
│   └── test-suite-runner.js # NEW: Parallel execution, discovery
├── reporting/             # Test reporting
│   ├── html-reporter.js    # NEW: HTML reports
│   ├── json-reporter.js    # NEW: JSON reports
│   └── junit-reporter.js   # NEW: JUnit XML
├── monitoring/             # Test monitoring
│   ├── performance-monitor.js    # NEW: Performance tracking
│   ├── flaky-test-detector.js    # NEW: Flaky test detection
│   └── test-trend-analyzer.js    # NEW: Trend analysis
├── setup/                  # Test setup
│   ├── setup-database.js   # NEW: Database setup
│   ├── setup-services.js   # NEW: Service health checks
│   ├── setup-test-data.js  # NEW: Test data preparation
│   └── teardown.js         # NEW: Cleanup utilities
├── seeders/                # Database seeders
│   ├── database-seeder.js  # NEW: Database seeding
│   └── cleanup-seeder.js   # NEW: Test data cleanup
├── fixtures/               # Test fixtures
│   ├── users.json          # NEW: Test user data
│   ├── subscriptions.json  # NEW: Test subscription data
│   ├── licenses.json       # NEW: Test license data
│   └── devices.json        # NEW: Test device data
├── run-test.js            # Test runner wrapper
├── run-automated-tests.js # Automated test runner
├── run-complete-test-suite.js # NEW: Complete suite runner
└── package.json
```

## Prerequisites

- Node.js 18+ (for built-in fetch API)
- PHP 8.1+ and Composer (for web dashboard tests)
- Chrome/Chromium (for Laravel Dusk tests)

## Running Tests

### Run All Tests

**Option 1: Complete Test Suite (Recommended)**
```bash
cd tests
npm run test:complete
```

**Option 2: PowerShell Orchestration**
```powershell
.\run_complete_e2e_tests.ps1
```

**Option 3: Test Suite Runner**
```bash
cd tests
node orchestration/test-suite-runner.js
```

### Run Individual Test Suites

#### API Tests
```bash
cd tests
npm run test:api:all
# Or individual files:
node run-test.js tests/api/auth-e2e.test.js
node run-test.js tests/api/license-e2e.test.js
node run-test.js tests/api/device-e2e.test.js
```

#### Integration Tests
```bash
cd tests
npm run test:integration
```

#### Desktop App Tests
```bash
cd tests
npm run test:desktop-app
```

#### Parallel Execution
```bash
cd tests
npm run test:parallel
```

#### Integration Tests

```bash
node tests/run-test.js tests/integration/auth-integration.test.js
node tests/run-test.js tests/integration/license-db.test.js
node tests/run-test.js tests/integration/database-e2e.test.js
```

#### Security Tests

```bash
node tests/run-test.js tests/security/api-security.test.js
```

#### User Journey Tests

```bash
node tests/run-test.js tests/e2e/complete-user-journey.test.js
node tests/run-test.js tests/e2e/license-renewal-journey.test.js
node tests/run-test.js tests/e2e/error-handling.test.js
```

### Web Dashboard Tests (Laravel Dusk)

```bash
cd web-dashboard
php artisan dusk
```

## Configuration

### Environment Variables

- `LICENSE_SERVER_URL` - License server API URL (default: https://j-tech-license-server.vercel.app)

### Test Accounts

Default test account for API tests:
- Email: `test@example.com`
- Password: `testpassword123`

## Test Coverage

### Authentication
- ✅ Login with valid/invalid credentials
- ✅ Token refresh
- ✅ Session management
- ✅ CORS headers
- ✅ Rate limiting

### License Management
- ✅ License validation
- ✅ License creation
- ✅ License expiration
- ✅ Feature access control

### Device Management
- ✅ Device registration
- ✅ Device limit enforcement
- ✅ Device ownership verification

### Security
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Token validation
- ✅ Input validation

### Integration
- ✅ Cross-system authentication
- ✅ Database operations
- ✅ License-database integration

### User Journeys
- ✅ New user onboarding
- ✅ License renewal
- ✅ Error handling

## Writing Tests

### API Test Example

```javascript
const ApiClient = require('../helpers/api-client');

describe('My Test Suite', () => {
    let apiClient;

    beforeEach(() => {
        apiClient = new ApiClient();
    });

    it('should test something', async () => {
        const response = await apiClient.login('test@example.com', 'password123');
        expect(response.status).toBe(200);
    });
});
```

### Web Dashboard Test Example (Laravel Dusk)

```php
use Tests\Browser\BrowserTestCase;
use Laravel\Dusk\Browser;

class MyTest extends BrowserTestCase
{
    public function test_something(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/dashboard')
                ->assertSee('Dashboard');
        });
    }
}
```

## Test Helpers

### ApiClient

Enhanced API client with retry logic, logging, and parallel support:
- `get(endpoint, headers)` - GET request with retry
- `post(endpoint, body, headers)` - POST request with retry
- `delete(endpoint, headers)` - DELETE request
- `put(endpoint, body, headers)` - PUT request
- `parallel(requests)` - Execute multiple requests in parallel
- `login(email, password, deviceId, deviceName)` - Login and store session
- `refresh(deviceId)` - Refresh session token
- `health()` - Health check
- **Options**: `timeout`, `retries`, `retryDelay`, `logging`

### TestData

Enhanced test data generators with factories:
- `generateEmail(prefix)` - Generate unique email
- `generateDeviceId(prefix)` - Generate unique device ID
- `generateUser(overrides)` - Generate user data
- `userFactory(count, overrides)` - Generate multiple users
- `subscriptionFactory(count, overrides)` - Generate subscriptions
- `licenseFactory(count, overrides)` - Generate licenses
- `deviceFactory(count, overrides)` - Generate devices
- `paymentFactory(count, overrides)` - Generate payments
- `generateUserScenario(overrides)` - Complete user scenario
- `generateSqlInjectionPayloads()` - SQL injection test payloads
- `generateXssPayloads()` - XSS test payloads

### TestEnvironment

Environment detection and service management:
- `isCI()` - Detect CI environment
- `isLocal()` - Detect local environment
- `getBaseURL()` - Get API base URL
- `checkServiceHealth(baseUrl)` - Check service health
- `waitForService(baseUrl, maxAttempts, delay)` - Wait for service
- `setupIsolation()` - Setup test isolation
- `getConfig()` - Get test configuration

### Test Suite Runner

Orchestrates test execution:
- Automatic test discovery
- Test grouping by category
- Parallel execution with concurrency control
- Result aggregation
- Performance tracking

## Troubleshooting

### Tests fail with "fetch is not available"

Install node-fetch or use Node.js 18+:
```bash
npm install node-fetch
```

### Web dashboard tests fail

Ensure:
1. PHP and Composer are installed
2. Dependencies are installed: `composer install`
3. Database is set up: `php artisan migrate`
4. ChromeDriver is installed: `php artisan dusk:install`

### API tests fail to connect

Check:
1. License server URL is correct
2. Server is running and accessible
3. Network connectivity

## Test Reports

Test reports are automatically generated in `test-results/` directory:

- **HTML Report** - Visual test report with pass/fail statistics, performance metrics, and error details
- **JSON Report** - Machine-readable test results
- **JUnit XML** - CI/CD compatible format for test result integration

Reports include:
- Test execution timeline
- Pass/fail statistics
- Performance metrics (duration, slow tests)
- Error stack traces
- Flaky test detection
- Test trend analysis

### Viewing Reports

```bash
# HTML reports are generated automatically
open test-results/test-report-*.html

# JSON reports for programmatic access
cat test-results/test-report-*.json

# JUnit XML for CI/CD
cat test-results/junit.xml
```

## Continuous Integration

### GitHub Actions

Tests run automatically on PR and push via `.github/workflows/e2e-tests.yml`:
- Sets up MySQL service
- Configures PHP and Node.js
- Runs Laravel migrations
- Starts Laravel server
- Executes all test suites
- Generates and uploads test reports

### Exit Codes

All test runners return appropriate exit codes:
- `0`: All tests passed
- `1`: Some tests failed

### CI/CD Integration

The test suite is designed for CI/CD:
- JUnit XML reports for test result integration
- Artifact uploads for test reports
- Parallel execution for faster feedback
- Service health checks before test execution
