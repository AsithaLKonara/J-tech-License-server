# Error Tracking Setup Guide

This guide explains how to set up error tracking services (Sentry, Rollbar, etc.) for production monitoring.

## Overview

Error tracking services help you:
- Monitor application errors in real-time
- Get alerts for critical errors
- Track error trends and patterns
- Debug production issues quickly
- Improve application reliability

## Recommended Services

### 1. Sentry (Recommended)

- **Free tier**: 5,000 events/month
- **Features**: Error tracking, performance monitoring, release tracking
- **Integration**: Easy Laravel integration
- **URL**: https://sentry.io

### 2. Rollbar

- **Free tier**: 5,000 events/month
- **Features**: Error tracking, deployment tracking
- **Integration**: Good Laravel support
- **URL**: https://rollbar.com

### 3. Bugsnag

- **Free tier**: Limited
- **Features**: Error tracking, stability monitoring
- **Integration**: Laravel support
- **URL**: https://www.bugsnag.com

## Option 1: Sentry Setup

### Step 1: Create Sentry Account

1. Sign up at https://sentry.io
2. Create a new project
3. Select "Laravel" as the platform
4. Copy your DSN (Data Source Name)

### Step 2: Install Sentry SDK

```bash
cd apps/web-dashboard
composer require sentry/sentry-laravel
```

### Step 3: Publish Configuration

```bash
php artisan vendor:publish --provider="Sentry\Laravel\ServiceProvider"
```

### Step 4: Configure Environment

Add to `.env`:
```env
SENTRY_LARAVEL_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_ENVIRONMENT=production
```

### Step 5: Configure Exception Handler

Edit `app/Exceptions/Handler.php`:

```php
use Sentry\Laravel\Integration;

public function register(): void
{
    $this->reportable(function (Throwable $e) {
        if (app()->bound('sentry')) {
            app('sentry')->captureException($e);
        }
    });
}
```

### Step 6: Test Integration

```bash
php artisan tinker
>>> throw new \Exception('Test Sentry integration');
```

Check your Sentry dashboard to verify the error was captured.

## Option 2: Rollbar Setup

### Step 1: Create Rollbar Account

1. Sign up at https://rollbar.com
2. Create a new project
3. Select "Laravel" as the framework
4. Copy your access token

### Step 2: Install Rollbar SDK

```bash
cd apps/web-dashboard
composer require rollbar/rollbar-laravel
```

### Step 3: Publish Configuration

```bash
php artisan vendor:publish --provider="Rollbar\Laravel\RollbarServiceProvider"
```

### Step 4: Configure Environment

Add to `.env`:
```env
ROLLBAR_TOKEN=your_rollbar_access_token
ROLLBAR_ENVIRONMENT=production
```

### Step 5: Test Integration

```bash
php artisan tinker
>>> \Rollbar::error('Test Rollbar integration');
```

## Configuration Options

### Error Filtering

Filter out non-critical errors:

**Sentry:**
```php
// In AppServiceProvider
use Sentry\State\Scope;

\Sentry\configureScope(function (Scope $scope): void {
    $scope->setTag('environment', config('app.env'));
});
```

**Rollbar:**
```php
// In config/rollbar.php
'person_fn' => null,
'person' => [
    'id' => null,
    'username' => null,
    'email' => null,
],
```

### Release Tracking

Track errors by application version:

**Sentry:**
```env
SENTRY_RELEASE=1.0.0
```

**Rollbar:**
```env
ROLLBAR_VERSION=1.0.0
```

### Performance Monitoring

Enable performance monitoring:

**Sentry:**
```env
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
```

## Log Aggregation

### Laravel Log Channels

Configure logging to send to error tracking:

Edit `config/logging.php`:

```php
'channels' => [
    'sentry' => [
        'driver' => 'sentry',
    ],
    // or
    'rollbar' => [
        'driver' => 'rollbar',
    ],
],
```

### Log Levels

Set appropriate log levels:

```env
LOG_CHANNEL=sentry
LOG_LEVEL=error  # Only send errors and above
```

## Alerting

### Sentry Alerts

1. Go to Sentry Dashboard → Alerts
2. Create alert rules:
   - Error rate threshold
   - New issue alerts
   - Regression alerts
3. Configure notification channels (email, Slack, PagerDuty)

### Rollbar Alerts

1. Go to Rollbar Dashboard → Notifications
2. Configure alert rules:
   - Error count thresholds
   - New item alerts
   - Occurrence rate alerts
3. Set up notification channels

## Best Practices

### 1. Environment Tagging

Tag errors by environment:
```php
\Sentry\configureScope(function (Scope $scope): void {
    $scope->setTag('environment', config('app.env'));
    $scope->setTag('version', config('app.version'));
});
```

### 2. User Context

Add user information to errors:
```php
if (auth()->check()) {
    \Sentry\configureScope(function (Scope $scope): void {
        $scope->setUser([
            'id' => auth()->id(),
            'email' => auth()->user()->email,
        ]);
    });
}
```

### 3. Custom Context

Add custom context to errors:
```php
\Sentry\configureScope(function (Scope $scope): void {
    $scope->setContext('request', [
        'url' => request()->url(),
        'method' => request()->method(),
        'ip' => request()->ip(),
    ]);
});
```

### 4. Filter Sensitive Data

Don't send sensitive data:
```php
// In AppServiceProvider
\Sentry\configureScope(function (Scope $scope): void {
    $scope->setTag('sensitive', false);
});
```

### 5. Ignore Non-Critical Errors

Ignore certain error types:
```php
// In AppServiceProvider
\Sentry\configureScope(function (Scope $scope): void {
    $scope->setLevel(\Sentry\Severity::warning());
});
```

## Monitoring Dashboards

### Sentry Dashboard

- **Issues**: List of all errors
- **Performance**: Response time metrics
- **Releases**: Error rates by version
- **Users**: Affected users

### Rollbar Dashboard

- **Items**: List of errors
- **Occurrences**: Error frequency
- **Trends**: Error trends over time
- **Deploys**: Error rates by deployment

## Troubleshooting

### Errors Not Appearing

1. Check DSN/token is correct
2. Verify SDK is installed
3. Check firewall allows outbound connections
4. Review application logs
5. Test with manual error

### Too Many Errors

1. Adjust log levels
2. Filter out non-critical errors
3. Set up error rate limits
4. Review and fix common errors

### Performance Impact

1. Use async error reporting
2. Adjust sample rates
3. Filter errors before sending
4. Use queue for error reporting

## Integration with CI/CD

### Sentry Release Tracking

```bash
# In deployment script
export SENTRY_AUTH_TOKEN=your_token
export SENTRY_ORG=your_org
export SENTRY_PROJECT=your_project

sentry-cli releases new $VERSION
sentry-cli releases set-commits $VERSION --auto
sentry-cli releases finalize $VERSION
```

### Rollbar Deploy Tracking

```bash
# In deployment script
curl https://api.rollbar.com/api/1/deploy/ \
  -F access_token=$ROLLBAR_TOKEN \
  -F environment=production \
  -F revision=$GIT_COMMIT \
  -F local_username=$USER
```

## Support

- Sentry Documentation: https://docs.sentry.io/platforms/php/guides/laravel
- Rollbar Documentation: https://docs.rollbar.com/docs/laravel
- Laravel Logging: https://laravel.com/docs/logging
