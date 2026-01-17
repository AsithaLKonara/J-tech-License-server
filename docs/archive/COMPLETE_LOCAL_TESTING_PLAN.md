# 🧪 Complete Local Testing Plan

**Date**: January 16, 2026  
**Environment**: Windows 11 (Local Development)  
**Version**: 3.0.0  
**Status**: Ready to Execute

---

## 📋 Table of Contents

1. [Environment Setup](#environment-setup)
2. [Testing Phases](#testing-phases)
3. [Test Execution](#test-execution)
4. [Verification Checklists](#verification-checklists)
5. [Troubleshooting](#troubleshooting)

---

## 🔧 Environment Setup

### Step 1: Verify System Requirements

```powershell
# Check Python version
python --version  # Should be 3.8+

# Check Node.js version
node --version  # Should be 16+

# Check npm version
npm --version  # Should be 8+

# Check Composer (for PHP)
composer --version  # Should be 2.0+
```

### Step 2: Install Desktop App Dependencies

```powershell
cd apps/upload-bridge

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Install Web Dashboard Dependencies

```powershell
cd apps/web-dashboard

# Install PHP dependencies
composer install

# Install Node.js dependencies
npm install

# Configure environment
copy .env.example .env
php artisan key:generate
```

### Step 4: Database Setup

```powershell
# Start MySQL (if using XAMPP/WAMP)
.\scripts\mysql-start.ps1

# Create database
mysql -u root -p -e "CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
php artisan migrate --force

# Seed test data
php artisan db:seed --class=TestDataSeeder
```

### Step 5: Environment Variables

**`apps/web-dashboard/.env`**:
```env
APP_NAME="Upload Bridge"
APP_ENV=local
APP_KEY=base64:xxxxx...
APP_DEBUG=true
APP_URL=http://localhost:8000

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge
DB_USERNAME=root
DB_PASSWORD=

JWT_SECRET=your-secret-key
UPLOAD_BRIDGE_API_URL=http://localhost:5000
```

**`apps/upload-bridge/.env`**:
```env
API_URL=http://localhost:8000
JWT_TOKEN=test-token
DEVICE_ID=test-device-001
OFFLINE_MODE=false
```

---

## 🧪 Testing Phases

### Phase 1: Unit Tests (2-3 hours)

#### 1.1 Core Module Tests

```powershell
# Python unit tests
cd apps/upload-bridge
pytest tests/unit/test_auth_manager.py -v
pytest tests/unit/test_gradient.py -v
pytest tests/unit/test_rate_limiter.py -v
pytest tests/unit/test_retry_utils.py -v
pytest tests/unit/test_network_validation.py -v
```

**Expected Results**:
- ✅ 40+ tests passing
- ✅ 95%+ code coverage
- ✅ No warnings or errors

#### 1.2 UI Component Tests

```powershell
# Canvas and widget tests
pytest tests/unit/test_matrix_design_canvas.py -v
pytest tests/unit/test_gradient_widget.py -v
pytest tests/unit/test_color_picker.py -v
```

**Expected Results**:
- ✅ 25+ tests passing
- ✅ All drawing modes functional
- ✅ Event handling correct

#### 1.3 Parser Tests

```powershell
# Pattern parser tests
pytest tests/unit/test_standard_format_parser.py -v
pytest tests/unit/test_preset_parser.py -v
```

**Expected Results**:
- ✅ 20+ tests passing
- ✅ JSON parsing correct
- ✅ Error handling robust

---

### Phase 2: Integration Tests (3-4 hours)

#### 2.1 Desktop ↔ Backend API

```powershell
# Start web server in background
cd apps/web-dashboard
npm run dev  # or php artisan serve

# In separate terminal
cd apps/upload-bridge
pytest tests/integration/test_api_communication.py -v
```

**Test Coverage**:
- User authentication endpoint
- Device registration endpoint
- License validation endpoint
- Token refresh mechanism
- Error response handling

**Expected Results**:
- ✅ Device successfully registers
- ✅ License validation returns correct status
- ✅ Tokens refresh properly
- ✅ Error codes are correct

#### 2.2 Pattern Upload Workflow

```powershell
pytest tests/integration/test_upload_workflow.py -v
```

**Test Coverage**:
- Pattern validation
- Binary encoding
- Network transmission
- Retry on failure
- Cleanup on completion

**Expected Results**:
- ✅ Pattern uploads successfully
- ✅ Progress callbacks fire
- ✅ Temp files cleaned up
- ✅ Rate limiting enforced

#### 2.3 License Management

```powershell
pytest tests/integration/test_license_workflow.py -v
```

**Test Coverage**:
- License key validation
- Device seat management
- Offline grace period
- Subscription tier enforcement
- Feature entitlement checking

**Expected Results**:
- ✅ License activates correctly
- ✅ Device seat limits enforced
- ✅ Offline mode works
- ✅ Grace period countdown accurate

---

### Phase 3: End-to-End Tests (4-5 hours)

#### 3.1 Complete User Workflow

```powershell
# Start all services
.\scripts\start-local-testing.ps1

# In separate terminal
cd tests
npm test -- tests/e2e/complete-workflow.test.js
```

**Workflow 1: New User Registration**
```
1. User registers at dashboard
2. User logs in
3. User activates license key
4. System binds device
5. Device becomes active
```

**Workflow 2: Pattern Design & Upload**
```
1. Open desktop app
2. Create new pattern (500x500 pixels)
3. Design with multiple shapes and gradients
4. Simulate pattern
5. Verify simulation matches design
6. Upload to test device
7. Verify device receives pattern
```

**Workflow 3: Offline & Resync**
```
1. Desktop app loses connection
2. App enters offline mode
3. User creates new pattern
4. App stores pattern locally
5. Connection restored
6. Patterns sync to server
7. Verify sync completes successfully
```

#### 3.2 Error Recovery Scenarios

```powershell
npm test -- tests/e2e/error-recovery.test.js
```

**Scenarios**:
- Network interruption during upload
- Invalid pattern data
- License expiration
- Device disconnection
- Server errors (500, 503)
- Timeout handling

---

### Phase 4: Performance Tests (2-3 hours)

#### 4.1 Canvas Performance

```powershell
pytest tests/performance/test_canvas_performance.py -v
```

**Metrics**:
- Rendering speed with 10k+ pixels
- Memory usage (target: <500 MB)
- Undo/redo speed
- Gradient computation time

#### 4.2 Network Performance

```powershell
pytest tests/performance/test_upload_performance.py -v
```

**Metrics**:
- Upload speed (target: >5 MB/s over LAN)
- Connection pooling efficiency
- Rate limiter overhead
- Retry logic impact

#### 4.3 Load Testing

```powershell
cd tests/load
node load-test-dashboard.js
node load-test-api.js
```

**Scenarios**:
- 10 concurrent users registering
- 5 concurrent uploads
- 100+ API requests/second
- Memory/CPU usage monitoring

---

## 🏃 Test Execution

### Quick Test (15 minutes)

```powershell
# All unit tests
cd apps/upload-bridge
pytest tests/unit -v --tb=short
```

### Standard Test (2-3 hours)

```powershell
# Unit + Integration tests
cd apps/upload-bridge
pytest tests/unit tests/integration -v

# E2E sample
cd ../../tests
npm test -- tests/e2e/basic-auth.test.js
```

### Complete Test (8-10 hours)

```powershell
# Run everything
.\run_complete_e2e_tests.ps1
```

### Continuous Integration Mode

```powershell
# Watch mode - reruns on file changes
pytest-watch tests/unit

# Or in Node.js
npm test -- --watch
```

---

## ✅ Verification Checklists

### Pre-Testing Checklist

- [ ] Python virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Database created and migrated
- [ ] Test data seeded
- [ ] Environment variables configured
- [ ] MySQL/PostgreSQL running
- [ ] No uncommitted changes in git
- [ ] `.env` files are correct

### Unit Test Verification

- [ ] All 40+ core module tests pass
- [ ] All 25+ UI component tests pass
- [ ] All 20+ parser tests pass
- [ ] Code coverage ≥95%
- [ ] No warnings in test output
- [ ] Execution time <30 seconds total

### Integration Test Verification

- [ ] API communication tests pass
- [ ] Pattern upload workflow tests pass
- [ ] License management tests pass
- [ ] All 15+ integration tests pass
- [ ] No flaky tests (run twice, both pass)
- [ ] Execution time <15 minutes total

### E2E Test Verification

- [ ] User registration workflow passes
- [ ] Pattern design workflow passes
- [ ] Upload workflow passes
- [ ] Offline/resync workflow passes
- [ ] Error recovery scenarios pass
- [ ] All 12+ E2E tests pass
- [ ] Execution time <30 minutes total

### Performance Test Verification

- [ ] Canvas renders 10k pixels in <500ms
- [ ] Memory usage stays <500 MB
- [ ] Upload speed >5 MB/s on LAN
- [ ] Connection pooling reduces overhead by >30%
- [ ] Rate limiter adds <5% latency
- [ ] Load test handles 10 concurrent users

### Security Test Verification

- [ ] Invalid tokens rejected
- [ ] SQL injection attempts blocked
- [ ] Invalid patterns rejected
- [ ] Rate limits enforced
- [ ] Offline license expiration respected
- [ ] Device binding validates correctly

---

## 🔍 Detailed Test Scenarios

### Scenario 1: Complete User Journey

**Duration**: 30 minutes

```
1. [SETUP] Start web dashboard and API
   - Verify dashboard loads at http://localhost:8000
   - Verify API responds at http://localhost:8000/api/v2/health

2. [REGISTRATION] Create new user account
   - Navigate to registration page
   - Fill in email: testuser@example.com
   - Fill in password: TestPassword123!
   - Submit and verify email confirmation
   - Confirm email (check database or mock)
   - Verify user account created

3. [ACTIVATION] Activate first license
   - Log in with testuser@example.com
   - Request trial license key
   - Click "Activate License"
   - System binds device ID
   - Verify "License Active" status shown

4. [DESKTOP APP] Launch desktop application
   - Run: python apps/upload-bridge/main.py
   - Verify app launches without errors
   - Verify license shows as valid
   - Verify device ID matches

5. [DESIGN] Create simple pattern
   - New project: 16x16 LED grid
   - Select rectangle tool
   - Draw 4x4 red square at (2,2)
   - Draw 4x4 blue square at (10,10)
   - Save pattern as "test-pattern-1.json"

6. [SIMULATE] Run simulation
   - Click "Simulate" button
   - Preview should show 2 colored squares
   - Frame rate display should show 30 FPS
   - Animation should be smooth
   - Stop simulation

7. [UPLOAD] Upload to test device (if available)
   - Click "Upload to Device"
   - Select device from list
   - Verify upload progress bar
   - Verify "Upload Complete" message
   - Device should display pattern

8. [VERIFY] Check dashboard
   - Refresh web dashboard
   - Navigate to "My Uploads"
   - Verify pattern appears in list
   - Verify upload timestamp correct
   - Verify file size shown
```

### Scenario 2: Offline Mode & Resync

**Duration**: 20 minutes

```
1. [SETUP] Desktop app with internet
   - Verify "Online" indicator
   - Verify license valid

2. [DISCONNECT] Simulate network failure
   - Disconnect from internet
   - Wait 5 seconds
   - Verify "Offline" indicator appears
   - Verify "Grace Period: 30 days" shown

3. [OFFLINE WORK] Continue designing offline
   - Create new pattern: "offline-pattern.json"
   - Simulate pattern (should work)
   - Try to upload (should show offline message)
   - Verify pattern saved locally

4. [RECONNECT] Restore internet connection
   - Reconnect to internet
   - Wait for auto-reconnect (should be <10 seconds)
   - Verify "Online" indicator returns
   - Verify grace period resets

5. [SYNC] Verify offline changes sync
   - Dashboard shows pending sync
   - Click "Sync Now"
   - Verify upload queue processes
   - Verify "offline-pattern.json" uploaded
   - Verify local sync marker cleared
```

### Scenario 3: Error Recovery

**Duration**: 15 minutes

```
1. [NETWORK ERROR] Simulate network timeout
   - Upload pattern
   - Interrupt network (pull network cable)
   - Verify "Connection Error" dialog
   - Verify "Retry" button available
   - Restore network
   - Click "Retry"
   - Verify upload resumes and completes

2. [INVALID DATA] Upload corrupted pattern
   - Manually edit pattern JSON (break structure)
   - Try to load pattern
   - Verify error message: "Invalid pattern format"
   - Verify graceful error dialog
   - Verify no crash

3. [RATE LIMIT] Exceed rate limit
   - Upload 10 patterns in sequence
   - 11th upload should show: "Upload limit exceeded (10/hour)"
   - Verify helpful message with wait time
   - Wait for cooldown period
   - Verify upload succeeds

4. [LICENSE EXPIRATION] Simulate expired license
   - (Manual test in database) Set license to expired
   - Try to upload pattern
   - Verify "License Expired" error
   - Verify link to renew license
   - Verify no pattern uploaded
```

---

## 🐛 Troubleshooting

### Common Issues

#### Python Virtual Environment Not Activated

**Problem**: `pip install` fails or `python` not found

**Solution**:
```powershell
# Navigate to desktop app
cd apps/upload-bridge

# Create venv
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Verify
python --version
```

#### MySQL Connection Refused

**Problem**: `mysql: [ERROR] Can't connect to MySQL server`

**Solution**:
```powershell
# Start MySQL service
.\scripts\mysql-start.ps1

# Or if using XAMPP
# Open XAMPP and start MySQL manually

# Verify connection
mysql -u root -p
```

#### Database Migration Errors

**Problem**: `SQLSTATE[42000]: Syntax error or access violation`

**Solution**:
```powershell
cd apps/web-dashboard

# Fresh database
php artisan migrate:refresh --force
php artisan db:seed --class=TestDataSeeder

# Or manually
mysql -u root -p upload_bridge < database/schema.sql
```

#### Port Already in Use

**Problem**: `Address already in use` when starting server

**Solution**:
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or use different port
php artisan serve --port=8001
```

#### Test Failures

**Problem**: Tests fail with timeout or assertion errors

**Solution**:
```powershell
# Run with more verbose output
pytest tests/ -v --tb=long

# Run single test file
pytest tests/unit/test_auth_manager.py -v

# Run with print statements
pytest tests/ -v -s

# Check test logs
cat logs/test.log
```

---

## 📊 Success Criteria

### Phase Completion Requirements

| Phase | Tests | Pass Rate | Duration | Status |
|-------|-------|-----------|----------|--------|
| Unit | 85+ | ≥99% | <1 hour | ✅ |
| Integration | 50+ | ≥98% | <2 hours | ✅ |
| E2E | 25+ | ≥95% | <3 hours | ✅ |
| Performance | 15+ | ≥90% | <1 hour | ✅ |
| **Total** | **175+** | **≥96%** | **<7 hours** | **✅** |

### Coverage Requirements

- **Unit Test Coverage**: ≥95%
- **Integration Test Coverage**: ≥85%
- **E2E Test Coverage**: ≥80%
- **Overall Code Coverage**: ≥90%

### Performance Requirements

- Canvas rendering: <500ms for 10k pixels
- API response time: <200ms average
- Upload speed: >5 MB/s on LAN
- Memory usage: <500 MB sustained
- Database queries: <100ms average

### Security Requirements

- All authentication flows validated
- No SQL injection vulnerabilities
- No XSS vulnerabilities
- Rate limiting enforced
- License validation secure
- Token handling correct

---

## 📈 Reporting

### Test Report Template

**File**: `test-results-{DATE}.md`

```markdown
# Test Execution Report - {DATE}

## Summary
- Total Tests: {count}
- Passed: {count}
- Failed: {count}
- Skipped: {count}
- Duration: {time}

## Results by Phase
- Unit Tests: {count} passed, {count} failed
- Integration Tests: {count} passed, {count} failed
- E2E Tests: {count} passed, {count} failed

## Coverage
- Lines: {percentage}%
- Branches: {percentage}%
- Functions: {percentage}%

## Issues Found
{list of failures}

## Performance Results
- Canvas rendering: {time}ms
- API response: {time}ms
- Upload speed: {speed} MB/s
- Memory peak: {memory} MB

## Recommendations
{any follow-up items}
```

---

## 🎯 Next Steps After Testing

1. **Create Build Artifacts**
   - Windows EXE
   - macOS DMG
   - Linux AppImage

2. **Deploy to Staging**
   - Upload to staging server
   - Run smoke tests
   - Verify all features

3. **Production Deployment**
   - Backup production database
   - Deploy web dashboard
   - Deploy API
   - Monitor for errors

4. **Post-Deployment**
   - Verify all endpoints
   - Check license system
   - Monitor performance
   - Gather user feedback

---

**Status**: Ready to execute complete local testing  
**Last Updated**: January 16, 2026  
**Next Review**: After testing completion
