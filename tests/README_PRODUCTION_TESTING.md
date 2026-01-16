# Production Testing Guide

This guide explains how to run the production readiness test suite.

## Prerequisites

1. **Running Application**
   - Application must be running and accessible
   - Database must be set up with migrations
   - Test data should be seeded (optional but recommended)

2. **Node.js**
   - Node.js 16+ required
   - npm or yarn package manager

3. **Dependencies**
   ```bash
   cd tests
   npm install
   ```

## Test Suites

### 1. Authentication Tests

Tests all authentication methods:
- Email/password login
- Magic link authentication
- Token refresh
- Token revocation (logout)

**Run:**
```bash
cd tests
API_URL=http://localhost:8000 node run-test.js tests/api/auth-e2e.test.js
```

### 2. License Tests

Tests license management:
- License validation
- License info retrieval
- Entitlement token generation

**Run:**
```bash
cd tests
API_URL=http://localhost:8000 node run-test.js tests/api/license-e2e.test.js
```

### 3. Device Tests

Tests device management:
- Device registration
- Device listing
- Device deletion
- Device limit enforcement

**Run:**
```bash
cd tests
API_URL=http://localhost:8000 node run-test.js tests/api/device-e2e.test.js
```

### 4. Security Tests

Tests security vulnerabilities:
- SQL Injection protection
- XSS protection
- Rate limiting
- Authentication bypass attempts
- Security headers
- Input validation

**Run:**
```bash
cd tests
API_URL=http://localhost:8000 bash scripts/run-security-tests.sh
```

Or directly:
```bash
cd tests
API_URL=http://localhost:8000 node tests/security/security-tests.test.js
```

### 5. Load Tests

Tests API performance under load:
- Concurrent user simulation
- Request rate measurement
- Response time statistics
- Error rate tracking

**Run:**
```bash
cd tests
API_URL=http://localhost:8000 \
CONCURRENT_USERS=10 \
REQUESTS_PER_USER=100 \
TEST_EMAIL=test@example.com \
TEST_PASSWORD=testpassword123 \
bash scripts/run-load-tests.sh
```

**Parameters:**
- `API_URL`: Base URL of the API (default: http://localhost:8000)
- `CONCURRENT_USERS`: Number of concurrent users (default: 10)
- `REQUESTS_PER_USER`: Number of requests per user (default: 100)
- `TEST_EMAIL`: Test user email for authentication
- `TEST_PASSWORD`: Test user password

### 6. Complete Production Test Suite

Runs all production readiness tests:

**Run:**
```bash
cd tests
API_URL=http://localhost:8000 bash scripts/run-production-tests.sh
```

## Test Data

### Generating Test Data

Generate test users for load testing:

```bash
cd tests
API_URL=http://localhost:8000 node scripts/generate-test-data.js 20
```

This will:
- Generate test users with random emails/passwords
- Attempt to register them (if registration endpoint exists)
- Save test data to `tests/fixtures/load-test-users.json`

### Using Test Data

Test data is saved in JSON format:
```json
[
  {
    "email": "loadtest_abc123@example.com",
    "password": "TestPassword123!xyz",
    "id": "user_id",
    "session_token": "token"
  }
]
```

Use this data in your tests or load testing scripts.

## Configuration

### Environment Variables

- `API_URL`: Base URL of the API (default: http://localhost:8000)
- `BASE_URL`: Alias for API_URL
- `TEST_EMAIL`: Test user email
- `TEST_PASSWORD`: Test user password
- `TEST_TIMEOUT`: Test timeout in milliseconds (default: 30000)

### Test Configuration

Edit test files to customize:
- Test endpoints
- Test data
- Assertions
- Timeouts

## Running Tests in Different Environments

### Local Development

```bash
API_URL=http://localhost:8000 bash scripts/run-production-tests.sh
```

### Staging Environment

```bash
API_URL=https://staging.yourdomain.com bash scripts/run-production-tests.sh
```

### Production Environment

**Warning**: Only run read-only tests in production!

```bash
# Health check only
API_URL=https://yourdomain.com node run-test.js tests/api/health-e2e.test.js

# Full test suite (use with caution)
API_URL=https://yourdomain.com bash scripts/run-production-tests.sh
```

## Expected Results

### Authentication Tests
- All login methods should work
- Tokens should be generated correctly
- Token refresh should work
- Logout should invalidate tokens

### License Tests
- License validation should work
- License info should be accurate
- Entitlement tokens should be valid

### Device Tests
- Device registration should work
- Device limits should be enforced
- Device deletion should work

### Security Tests
- SQL Injection attempts should be blocked
- XSS attempts should be sanitized
- Rate limiting should be enforced
- Authentication should be required for protected endpoints
- Security headers should be present

### Load Tests
- API should handle concurrent requests
- Response times should be acceptable (< 500ms average)
- Error rate should be low (< 1%)
- Requests per second should meet requirements

## Troubleshooting

### Tests Fail to Connect

**Error**: `API is not accessible`

**Solutions**:
1. Verify application is running
2. Check API_URL is correct
3. Check firewall/network settings
4. Verify port is accessible

### Authentication Tests Fail

**Error**: `Invalid email or password`

**Solutions**:
1. Verify test user exists in database
2. Check credentials in test files
3. Run database seeder if needed
4. Check authentication endpoint is working

### Security Tests Fail

**Error**: `Vulnerability detected`

**Solutions**:
1. Review security test output
2. Check application logs
3. Verify security middleware is enabled
4. Review security configuration

### Load Tests Show Poor Performance

**Issues**: High response times, many errors

**Solutions**:
1. Check server resources (CPU, memory)
2. Review database query performance
3. Check for bottlenecks
4. Optimize slow queries
5. Scale resources if needed

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/tests.yml
- name: Run Production Tests
  run: |
    cd tests
    npm install
    API_URL=http://localhost:8000 bash scripts/run-production-tests.sh
```

## Next Steps

After running tests:

1. **Review Results**: Check all tests pass
2. **Fix Issues**: Address any failures
3. **Optimize**: Improve performance if needed
4. **Document**: Update documentation with findings
5. **Monitor**: Set up monitoring based on test results

## Support

For issues or questions:
- Check test output and logs
- Review application logs
- Check API documentation
- Review test file source code
