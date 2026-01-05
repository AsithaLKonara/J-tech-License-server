# Monitoring and Dashboards Setup Guide

This guide explains how to set up monitoring, dashboards, and alerts for production.

## Overview

Monitoring helps you:
- Track application uptime
- Monitor performance metrics
- Get alerts for issues
- Analyze trends
- Make data-driven decisions

## Monitoring Services

### 1. Uptime Monitoring

#### UptimeRobot (Free)

- **Free tier**: 50 monitors
- **Features**: HTTP(S) monitoring, keyword monitoring
- **URL**: https://uptimerobot.com

**Setup:**
1. Sign up at UptimeRobot
2. Add new monitor
3. Configure:
   - Type: HTTP(s)
   - URL: https://yourdomain.com/api/v2/health
   - Interval: 5 minutes
   - Alert contacts: Email/SMS
4. Save monitor

#### Pingdom

- **Free tier**: Limited
- **Features**: Uptime monitoring, performance monitoring
- **URL**: https://www.pingdom.com

#### StatusCake

- **Free tier**: 10 tests
- **Features**: Uptime monitoring, SSL monitoring
- **URL**: https://www.statuscake.com

### 2. Application Performance Monitoring (APM)

#### New Relic

- **Free tier**: Limited
- **Features**: APM, error tracking, infrastructure monitoring
- **URL**: https://newrelic.com

#### Datadog

- **Free tier**: Limited
- **Features**: APM, logs, infrastructure
- **URL**: https://www.datadog.com

#### Sentry Performance

- **Features**: Performance monitoring, error tracking
- **URL**: https://sentry.io

### 3. Log Aggregation

#### Papertrail

- **Free tier**: 16MB/month
- **Features**: Log aggregation, search
- **URL**: https://www.papertrail.com

#### Loggly

- **Free tier**: 200MB/day
- **Features**: Log aggregation, analytics
- **URL**: https://www.loggly.com

## Setting Up Uptime Monitoring

### Step 1: Health Check Endpoint

Ensure health endpoint is working:
```bash
curl https://yourdomain.com/api/v2/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-01-27T12:00:00Z",
  "version": "2.0"
}
```

### Step 2: Configure Monitor

**UptimeRobot:**
1. Monitor Type: HTTP(s)
2. Friendly Name: Upload Bridge API
3. URL: https://yourdomain.com/api/v2/health
4. Monitoring Interval: 5 minutes
5. Alert When: Down for 1 check

**Pingdom:**
1. Check Type: HTTP
2. URL: https://yourdomain.com/api/v2/health
3. Check Interval: 5 minutes
4. Alert Threshold: 1 failure

### Step 3: Set Up Alerts

Configure alert contacts:
- Email notifications
- SMS notifications (optional)
- Slack/Teams integration (optional)
- PagerDuty (for critical alerts)

## Creating Dashboards

### Key Metrics to Monitor

1. **Uptime**
   - Availability percentage
   - Downtime incidents
   - Response time

2. **Performance**
   - API response times
   - Database query times
   - Error rates

3. **Usage**
   - Request volume
   - Active users
   - API endpoint usage

4. **Errors**
   - Error rate
   - Error types
   - Affected users

### Dashboard Tools

#### Grafana (Self-hosted)

1. Install Grafana
2. Configure data sources (Prometheus, InfluxDB, etc.)
3. Create dashboards
4. Set up alerts

#### Datadog Dashboards

1. Sign up for Datadog
2. Install agent
3. Create custom dashboards
4. Configure widgets

#### New Relic Dashboards

1. Sign up for New Relic
2. Install agent
3. Create dashboards
4. Add widgets

## Custom Metrics

### Laravel Metrics

Create custom metrics endpoint:

```php
// routes/api.php
Route::get('/metrics', function () {
    return response()->json([
        'users' => \App\Models\User::count(),
        'active_subscriptions' => \App\Models\Subscription::where('status', 'active')->count(),
        'total_devices' => \App\Models\Device::count(),
        'api_requests_today' => cache()->get('api_requests_today', 0),
    ]);
})->middleware('api.auth');
```

### Prometheus Integration

Install Prometheus exporter:

```bash
composer require promphp/prometheus_client_php
```

Create metrics endpoint:

```php
use Prometheus\CollectorRegistry;
use Prometheus\Storage\InMemory;

$registry = new CollectorRegistry(new InMemory());

$counter = $registry->getOrRegisterCounter(
    'app',
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
);

$counter->inc(['GET', '/api/v2/health', '200']);
```

## Alert Configuration

### Critical Alerts

1. **Application Down**
   - Condition: Health check fails
   - Action: Immediate notification
   - Escalation: PagerDuty/SMS

2. **High Error Rate**
   - Condition: Error rate > 5%
   - Action: Email notification
   - Review: Check error logs

3. **Slow Response Times**
   - Condition: P95 response time > 1s
   - Action: Email notification
   - Review: Check performance

4. **Database Issues**
   - Condition: Database connection failures
   - Action: Immediate notification
   - Escalation: On-call engineer

### Warning Alerts

1. **High CPU Usage**
   - Condition: CPU > 80%
   - Action: Email notification

2. **High Memory Usage**
   - Condition: Memory > 80%
   - Action: Email notification

3. **Disk Space Low**
   - Condition: Disk < 20% free
   - Action: Email notification

## Log Monitoring

### Set Up Log Aggregation

**Papertrail:**
1. Sign up at Papertrail
2. Add system
3. Configure log forwarding:
   ```bash
   # rsyslog configuration
   *.* @logs.papertrailapp.com:PORT
   ```

**Loggly:**
1. Sign up at Loggly
2. Install token
3. Configure Laravel:
   ```env
   LOG_CHANNEL=loggly
   LOGGLY_TOKEN=your_token
   ```

### Log Analysis

Monitor for:
- Error patterns
- Security events
- Performance issues
- User activity

## Performance Monitoring

### Response Time Tracking

Track API response times:

```php
// Middleware
public function handle($request, Closure $next)
{
    $start = microtime(true);
    $response = $next($request);
    $duration = (microtime(true) - $start) * 1000;
    
    // Log or send to monitoring service
    \Log::info('API Request', [
        'endpoint' => $request->path(),
        'method' => $request->method(),
        'duration_ms' => $duration,
    ]);
    
    return $response;
}
```

### Database Query Monitoring

Enable query logging:

```php
// In AppServiceProvider
DB::listen(function ($query) {
    if ($query->time > 100) { // Log slow queries
        \Log::warning('Slow Query', [
            'sql' => $query->sql,
            'time' => $query->time,
        ]);
    }
});
```

## Dashboard Examples

### Uptime Dashboard

- **Widget 1**: Uptime percentage (last 30 days)
- **Widget 2**: Response time graph
- **Widget 3**: Incident timeline
- **Widget 4**: Status by endpoint

### Performance Dashboard

- **Widget 1**: Average response time
- **Widget 2**: P95/P99 response times
- **Widget 3**: Requests per second
- **Widget 4**: Error rate

### Error Dashboard

- **Widget 1**: Error rate over time
- **Widget 2**: Top errors
- **Widget 3**: Errors by endpoint
- **Widget 4**: Affected users

## Best Practices

### 1. Set Appropriate Thresholds

- Don't alert on every minor issue
- Use different thresholds for different environments
- Review and adjust thresholds regularly

### 2. Use Multiple Alert Channels

- Email for non-critical
- SMS for critical
- Slack for team notifications
- PagerDuty for on-call

### 3. Regular Review

- Review alerts weekly
- Adjust thresholds based on patterns
- Remove false positives
- Document alert procedures

### 4. Dashboard Organization

- Group related metrics
- Use consistent colors
- Include time ranges
- Make dashboards actionable

## Troubleshooting

### Alerts Not Firing

1. Check alert configuration
2. Verify thresholds are correct
3. Test alert channels
4. Review monitoring service status

### Too Many Alerts

1. Increase thresholds
2. Add alert cooldown periods
3. Group related alerts
4. Filter out noise

### Missing Metrics

1. Verify data collection
2. Check data source connections
3. Review metric definitions
4. Test metric endpoints

## Support

- UptimeRobot: https://uptimerobot.com/help
- Pingdom: https://www.pingdom.com/support
- Grafana: https://grafana.com/docs
- Datadog: https://docs.datadoghq.com
