# Upload Bridge License Integration Verification

**Version**: 3.0.0  
**Date**: 2025-01-27

---

## Overview

This document provides a comprehensive checklist for verifying that the license server integration works correctly in the Upload Bridge desktop application.

---

## Pre-Verification Setup

### 1. Web Dashboard Setup
- [ ] Web dashboard running (local or remote)
- [ ] Database migrations completed
- [ ] Test user account created
- [ ] SMTP configured (for magic link testing)

### 2. Upload Bridge Configuration
- [ ] Update `config/auth_config.yaml` with web dashboard URL
- [ ] Or set `LICENSE_SERVER_URL` environment variable
- [ ] Verify configuration loads correctly

---

## Verification Checklist

### Application Startup
- [ ] Application starts without errors
- [ ] No import errors
- [ ] No configuration errors
- [ ] Login dialog appears (if not authenticated)
- [ ] All tabs load correctly

### Login Dialog Functionality
- [ ] Login dialog displays correctly
- [ ] All tabs visible (Email/Password, Magic Link, Social Login)
- [ ] Email/Password tab functional
- [ ] Magic Link tab functional
- [ ] Social Login tab shows (optional, requires Auth0)
- [ ] Create Account button works
- [ ] Cancel button works

### Email/Password Login
- [ ] Enter email and password
- [ ] Click Login button
- [ ] Loading indicator shows
- [ ] Login succeeds
- [ ] Session token stored
- [ ] Entitlement token received
- [ ] License info displayed
- [ ] Device registered automatically
- [ ] Application continues normally
- [ ] No error messages

### Magic Link Request
- [ ] Go to Magic Link tab
- [ ] Enter email address
- [ ] Click "Send Magic Link"
- [ ] Success message displayed
- [ ] Email received (check inbox)
- [ ] Magic link URL in email is correct

### Magic Link Authentication
- [ ] Click magic link in email
- [ ] Web dashboard opens
- [ ] User authenticated in web dashboard
- [ ] Return to upload-bridge application
- [ ] Application detects authentication
- [ ] License validated automatically
- [ ] Device registered
- [ ] Application continues normally

### License Validation
- [ ] License validated after login
- [ ] License info displayed correctly
- [ ] Plan type correct
- [ ] Features list correct
- [ ] Expiration date correct (if applicable)
- [ ] License status is "active"

### Device Registration
- [ ] Device registered during login
- [ ] Device ID generated correctly
- [ ] Device name stored correctly
- [ ] Device appears in web dashboard
- [ ] Multiple devices can be registered
- [ ] Device limit enforced correctly

### Offline License Caching
- [ ] Login successfully
- [ ] License cached locally
- [ ] Disconnect from internet
- [ ] Restart application
- [ ] License still valid
- [ ] Offline period matches plan type:
  - Trial: 0 days (no offline)
  - Monthly: 3 days
  - Yearly: 14 days
  - Perpetual: 30 days
- [ ] Reconnect internet
- [ ] License refresh works

### Token Refresh
- [ ] Login successfully
- [ ] Token refresh happens automatically
- [ ] New tokens received
- [ ] Old token revoked
- [ ] License info updated
- [ ] No interruption to user

### All Tabs Functional
- [ ] Media Upload tab works
- [ ] Design Tools tab works
- [ ] Preview tab works
- [ ] Flash tab works
- [ ] Batch Flash tab works
- [ ] Pattern Library tab works
- [ ] Audio Reactive tab works
- [ ] WiFi Upload tab works
- [ ] Arduino IDE tab works

### Error Handling
- [ ] Invalid credentials show error
- [ ] Network errors show error
- [ ] Server errors show error
- [ ] Expired tokens show error
- [ ] Device limit errors show error
- [ ] Error messages are clear and helpful
- [ ] User can retry after errors

### Console Errors
- [ ] No Python errors in console
- [ ] No Qt errors in console
- [ ] No API errors in console
- [ ] No import errors
- [ ] No configuration errors

### Performance
- [ ] Login completes within 5 seconds
- [ ] License validation completes within 2 seconds
- [ ] Token refresh completes within 2 seconds
- [ ] No UI freezing during authentication
- [ ] Application remains responsive

---

## Test Scenarios

### Scenario 1: New User First Login
1. [ ] User registers via web dashboard
2. [ ] User receives trial license
3. [ ] User opens upload-bridge
4. [ ] Login dialog appears
5. [ ] User logs in with email/password
6. [ ] License validated (trial)
7. [ ] Device registered
8. [ ] User can use application

### Scenario 2: Existing User Login
1. [ ] User opens upload-bridge
2. [ ] Cached license checked
3. [ ] If valid, no login required
4. [ ] If expired, login dialog appears
5. [ ] User logs in
6. [ ] License refreshed
7. [ ] Application continues

### Scenario 3: Magic Link Flow
1. [ ] User requests magic link
2. [ ] Email received
3. [ ] User clicks link
4. [ ] Web dashboard authenticates
5. [ ] Upload-bridge detects authentication
6. [ ] License validated
7. [ ] Application ready

### Scenario 4: Device Limit Reached
1. [ ] User has max devices registered
2. [ ] User tries to login from new device
3. [ ] Error message displayed
4. [ ] User can remove old device
5. [ ] User can register new device

### Scenario 5: License Expired
1. [ ] User has expired license
2. [ ] User tries to login
3. [ ] License validation fails
4. [ ] User prompted to renew
5. [ ] After renewal, license works

---

## Verification Results

### Test Environment
- **Date**: 
- **Tester**: 
- **Web Dashboard URL**: 
- **Upload Bridge Version**: 
- **Operating System**: 

### Results Summary
- **Total Checks**: 
- **Passed**: 
- **Failed**: 
- **Skipped**: 

### Issues Found
1. **Issue**: 
   - **Severity**: 
   - **Description**: 
   - **Steps to Reproduce**: 
   - **Workaround**: 

---

## Next Steps

After verification:
- [ ] Fix any issues found
- [ ] Re-test fixed issues
- [ ] Update documentation if needed
- [ ] Proceed to production deployment

---

**Last Updated**: 2025-01-27
