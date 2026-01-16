# Manual Integration Test Checklist

**Upload Bridge License Server Integration**  
**Date**: 2025-01-27

---

## Prerequisites

- [ ] Web dashboard running locally or on staging
- [ ] Database migrations run
- [ ] Test user account created
- [ ] Upload-bridge application built/ready
- [ ] SMTP configured (for magic link testing)

---

## Test Scenarios

### 1. Complete Login Flow - Email/Password

**Steps:**
1. [ ] Start upload-bridge application
2. [ ] Verify login dialog appears
3. [ ] Go to "Email/Password" tab
4. [ ] Enter valid email and password
5. [ ] Click "Login"
6. [ ] Verify login succeeds
7. [ ] Verify license info displayed
8. [ ] Verify device registered automatically
9. [ ] Verify application continues normally
10. [ ] Check no console errors

**Expected Results:**
- Login successful
- Session token stored
- Entitlement token received
- License validated
- Device registered
- All tabs functional

---

### 2. Complete Login Flow - Magic Link

**Steps:**
1. [ ] Start upload-bridge application
2. [ ] Go to "Magic Link" tab
3. [ ] Enter email address
4. [ ] Click "Send Magic Link"
5. [ ] Verify success message
6. [ ] Check email for magic link
7. [ ] Click magic link in email (opens web dashboard)
8. [ ] Return to upload-bridge application
9. [ ] Verify automatic authentication
10. [ ] Verify license validated
11. [ ] Verify device registered

**Expected Results:**
- Magic link sent successfully
- Email received
- Clicking link authenticates user
- License validated
- Device registered

---

### 3. License Validation After Login

**Steps:**
1. [ ] Login successfully (email/password or magic link)
2. [ ] Verify entitlement token received
3. [ ] Check license info (plan, features, expiration)
4. [ ] Verify license is active
5. [ ] Test offline license caching (disconnect internet)
6. [ ] Verify license still works offline
7. [ ] Reconnect internet
8. [ ] Verify license refresh works

**Expected Results:**
- License info correct
- Offline caching works
- Token refresh works

---

### 4. Device Registration During Login

**Steps:**
1. [ ] Login with device_id provided
2. [ ] Verify device registered in database
3. [ ] Check device appears in web dashboard
4. [ ] Login from different device
5. [ ] Verify both devices registered
6. [ ] Check device limit enforcement
7. [ ] Try to register device beyond limit
8. [ ] Verify error message displayed

**Expected Results:**
- Devices registered correctly
- Device limit enforced
- Error messages clear

---

### 5. Offline License Caching

**Steps:**
1. [ ] Login successfully
2. [ ] Verify license cached locally
3. [ ] Disconnect from internet
4. [ ] Restart application
5. [ ] Verify license still valid
6. [ ] Check offline period matches plan type
7. [ ] Reconnect internet
8. [ ] Verify license refresh works

**Expected Results:**
- License cached correctly
- Offline validation works
- Offline period matches plan
- Refresh works when online

---

### 6. Token Refresh Flow

**Steps:**
1. [ ] Login successfully
2. [ ] Wait for token near expiration (or manually trigger)
3. [ ] Verify token refresh happens automatically
4. [ ] Check new tokens received
5. [ ] Verify old token revoked
6. [ ] Test with expired token
7. [ ] Verify re-authentication required

**Expected Results:**
- Token refresh automatic
- New tokens valid
- Old tokens revoked
- Expired tokens rejected

---

### 7. Error Scenarios

#### 7.1 Invalid Credentials

**Steps:**
1. [ ] Try login with wrong password
2. [ ] Verify error message displayed
3. [ ] Verify no tokens stored
4. [ ] Try login with non-existent email
5. [ ] Verify appropriate error message

**Expected Results:**
- Clear error messages
- No tokens stored
- User can retry

#### 7.2 Expired Tokens

**Steps:**
1. [ ] Use expired session token
2. [ ] Verify 401 error
3. [ ] Verify re-authentication required
4. [ ] Test with expired entitlement token
5. [ ] Verify license validation fails

**Expected Results:**
- Expired tokens rejected
- Clear error messages
- Re-authentication prompt

#### 7.3 Network Errors

**Steps:**
1. [ ] Disconnect internet
2. [ ] Try to login
3. [ ] Verify error message
4. [ ] Reconnect internet
5. [ ] Verify login works

**Expected Results:**
- Network errors handled gracefully
- Clear error messages
- Retry works when online

#### 7.4 Server Errors

**Steps:**
1. [ ] Stop web dashboard server
2. [ ] Try to login
3. [ ] Verify error message
4. [ ] Start server
5. [ ] Verify login works

**Expected Results:**
- Server errors handled
- Clear error messages
- Retry works when server available

---

### 8. Device Management

**Steps:**
1. [ ] Login successfully
2. [ ] Register multiple devices
3. [ ] Check device list in web dashboard
4. [ ] Delete device via web dashboard
5. [ ] Verify device removed
6. [ ] Try to login with deleted device
7. [ ] Verify device re-registered

**Expected Results:**
- Devices managed correctly
- Device deletion works
- Devices can be re-registered

---

### 9. License Plan Types

**Steps:**
1. [ ] Test with trial license
2. [ ] Verify trial features available
3. [ ] Test with monthly license
4. [ ] Verify monthly features available
5. [ ] Test with yearly license
6. [ ] Verify yearly features available
7. [ ] Test with perpetual license
8. [ ] Verify perpetual features available

**Expected Results:**
- Correct features for each plan
- Plan limits enforced
- Features match plan type

---

### 10. Complete User Journey

**Steps:**
1. [ ] New user registration (via web dashboard)
2. [ ] User receives trial license
3. [ ] User logs into upload-bridge
4. [ ] User creates pattern
5. [ ] User subscribes (via web dashboard)
6. [ ] License upgraded automatically
7. [ ] User gets new features
8. [ ] User uses advanced features
9. [ ] Subscription expires
10. [ ] User downgraded to trial

**Expected Results:**
- Complete flow works
- License updates automatically
- Features match subscription

---

## Test Results Template

### Test: [Test Name]
- **Date**: 
- **Tester**: 
- **Environment**: 
- **Status**: ✅ Pass / ❌ Fail / ⚠️ Partial
- **Issues Found**: 
- **Notes**: 

---

## Known Issues

Document any issues found during testing:

1. **Issue**: 
   - **Severity**: Critical / High / Medium / Low
   - **Steps to Reproduce**: 
   - **Expected**: 
   - **Actual**: 
   - **Workaround**: 

---

**Last Updated**: 2025-01-27
