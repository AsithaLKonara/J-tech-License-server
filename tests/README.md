# E2E Testing Guide

This directory contains end-to-end tests for the Upload Bridge License Dashboard using Laravel Dusk.

## Test Structure

```
tests/
├── Browser/
│   └── TestCase.php          # Base Dusk test case
├── E2E/
│   ├── AuthenticationTest.php
│   ├── UserDashboardTest.php
│   ├── SubscriptionTest.php
│   ├── LicenseTest.php
│   ├── DeviceTest.php
│   ├── BillingTest.php
│   ├── AccountTest.php
│   ├── AdminTest.php
│   ├── MagicLinkTest.php
│   └── StripeIntegrationTest.php
└── Helpers/
    └── TestHelpers.php       # Test utility functions
```

## Prerequisites

1. **PHP 8.1+** installed
2. **Composer** installed
3. **Chrome/Chromium** browser installed
4. **ChromeDriver** (installed automatically via `php artisan dusk:install`)

## Setup

1. Install dependencies:
```bash
cd web-dashboard
composer install
```

2. Install Dusk and ChromeDriver:
```bash
php artisan dusk:install
```

3. Create test environment file:
```bash
cp .env.dusk.local .env
php artisan key:generate
```

4. Create SQLite database:
```bash
touch database/database.sqlite
```

5. Run migrations:
```bash
php artisan migrate
```

## Running Tests

### Run All Tests
```bash
php artisan dusk
```

### Run Specific Test Class
```bash
php artisan dusk --filter AuthenticationTest
```

### Run Specific Test Method
```bash
php artisan dusk --filter test_user_can_register_with_valid_data
```

### Run Tests with Screenshots on Failure
```bash
php artisan dusk --screenshots
```

### Run Tests in Non-Headless Mode (See Browser)
```bash
php artisan dusk --no-headless
```

## Test Coverage

### Authentication Flow
- User registration (valid/invalid data)
- User login (valid/invalid credentials)
- Logout functionality
- Session management
- Remember me functionality

### Magic Link Flow
- Request magic link
- Magic link verification
- Token expiration
- One-time use validation

### User Dashboard
- Dashboard access
- Subscription status display
- License information display
- Device count display
- Payment history display

### Subscription Management
- View subscription page
- Display available plans
- Initiate checkout
- Cancel subscription
- Subscription status updates

### License Management
- View licenses
- Display license status
- Show subscription association
- Empty state handling

### Device Management
- View devices
- Delete devices
- Ownership verification
- Empty state handling

### Billing
- View billing history
- Display payments
- Payment amounts and dates

### Account Settings
- Update profile
- Update email
- Update password
- Validation errors

### Admin Panel
- Admin access control
- User management
- Subscription management
- Manual subscription creation

### Stripe Integration
- Webhook endpoint validation
- Event handling structure

## Test Helpers

The `TestHelpers` class provides utility methods:

- `createUser()` - Create test user
- `createAdmin()` - Create admin user
- `createSubscription()` - Create test subscription
- `createLicense()` - Create test license
- `createDevice()` - Create test device
- `createPayment()` - Create test payment
- `createMagicLink()` - Create magic link
- `loginAs()` - Login user via browser

## Troubleshooting

### ChromeDriver Issues
```bash
php artisan dusk:chrome-driver
```

### Database Issues
```bash
php artisan migrate:fresh
```

### Clear Cache
```bash
php artisan config:clear
php artisan cache:clear
```

### View Screenshots
Screenshots are saved to `tests/Browser/screenshots/` on test failures.

### View Console Logs
Console logs are saved to `tests/Browser/console/` on test failures.

## CI/CD Integration

Tests run automatically on push/PR via GitHub Actions (`.github/workflows/dusk.yml`).

## Best Practices

1. Each test should be independent
2. Use unique email addresses for each test
3. Clean up test data in `setUp()` or `tearDown()`
4. Use descriptive test method names
5. Test both success and failure paths
6. Test edge cases and empty states

## Notes

- Tests use SQLite for speed
- Database is reset before each test
- Tests run in headless mode by default
- Screenshots are captured on failures
- External services (Stripe, Email) are mocked where possible
