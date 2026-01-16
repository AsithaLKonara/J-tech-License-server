# Load Testing Guide

This guide explains how to perform load testing on the Upload Bridge license server.

## Overview

Load testing helps identify:
- Maximum concurrent users
- Response time under load
- Breaking points
- Performance bottlenecks
- Resource usage patterns

## Prerequisites

1. Node.js 18+ installed
2. Application running and accessible
3. Test user account created
4. Sufficient system resources

## Quick Start

### Basic Load Test

```bash
cd tests
export LICENSE_SERVER_URL=http://localhost:8000
node load/load-test-scenarios.js steady 10 60
```

This runs a steady load test with 10 concurrent users for 60 seconds.

## Available Scenarios

### 1. Steady Load

Constant number of concurrent users.

```bash
node load/load-test-scenarios.js steady <users> <duration>
```

**Example:**
```bash
node load/load-test-scenarios.js steady 20 120
# 20 concurrent users for 2 minutes
```

### 2. Ramp Up

Gradually increase load over time.

```bash
node load/load-test-scenarios.js ramp <maxUsers> <duration> <stepDuration>
```

**Example:**
```bash
node load/load-test-scenarios.js ramp 50 300 10
# Ramp from 0 to 50 users over 5 minutes, 10s per step
```

### 3. Spike Test

Sudden increase in load to test recovery.

```bash
node load/load-test-scenarios.js spike <baseUsers> <spikeUsers> <spikeDuration>
```

**Example:**
```bash
node load/load-test-scenarios.js spike 5 100 30
# Baseline 5 users, spike to 100 for 30s, then recover
```

### 4. Stress Test

Find the breaking point by gradually increasing load.

```bash
node load/load-test-scenarios.js stress <startUsers> <maxUsers> <increment>
```

**Example:**
```bash
node load/load-test-scenarios.js stress 10 500 10
# Start at 10, increase by 10 until failure or 500 max
```

### 5. Endurance Test

Sustained load over extended period.

```bash
node load/load-test-scenarios.js endurance <users> <duration>
```

**Example:**
```bash
node load/load-test-scenarios.js endurance 20 600
# 20 users for 10 minutes
```

### 6. Mixed Workload

Different types of requests (health, login, license).

```bash
node load/load-test-scenarios.js mixed <users> <duration>
```

**Example:**
```bash
node load/load-test-scenarios.js mixed 15 180
# 15 users, mixed requests, 3 minutes
```

## Using the Load Test Script

The `run-load-tests.sh` script provides a convenient wrapper:

```bash
cd tests/scripts
bash run-load-tests.sh
```

Or with custom parameters:

```bash
LICENSE_SERVER_URL=http://localhost:8000 \
CONCURRENT_USERS=20 \
DURATION=120 \
bash run-load-tests.sh
```

## Interpreting Results

### Success Metrics

- **Success Rate**: Should be > 95% under normal load
- **Response Time**: Should be < 500ms for most requests
- **Error Rate**: Should be < 1%

### Warning Signs

- Success rate drops below 90%
- Response times exceed 1 second
- Error rate exceeds 5%
- Memory usage continuously increases
- Database connections exhausted

## Performance Baselines

Recommended baselines for production:

- **Normal Load**: 50-100 concurrent users
- **Peak Load**: 200-500 concurrent users
- **Response Time**: < 200ms (p95)
- **Error Rate**: < 0.1%

## Monitoring During Tests

### Application Logs

```bash
tail -f apps/web-dashboard/storage/logs/laravel.log
```

### System Resources

```bash
# CPU and Memory
top

# Network
iftop

# Database connections
mysql -u root -p -e "SHOW PROCESSLIST;"
```

### Application Metrics

Use Laravel Telescope or Debugbar to monitor:
- Query execution times
- Cache hit rates
- Memory usage
- Request/response times

## Best Practices

1. **Start Small**: Begin with low concurrency and gradually increase
2. **Monitor Resources**: Watch CPU, memory, and database during tests
3. **Test Realistic Scenarios**: Use mixed workloads that match production
4. **Run During Off-Peak**: Avoid impacting real users
5. **Document Results**: Keep records of test results for comparison
6. **Test Recovery**: Verify system recovers after load spikes
7. **Test Different Endpoints**: Don't just test health checks

## Troubleshooting

### Tests Fail Immediately

- Check application is running
- Verify `LICENSE_SERVER_URL` is correct
- Check network connectivity
- Review application logs

### High Error Rate

- Check database connection pool
- Verify Redis is running (if using)
- Check application memory limits
- Review slow query log

### Slow Response Times

- Check database indexes
- Verify cache is working
- Check for N+1 queries
- Review application logs for bottlenecks

## Advanced Configuration

### Custom Test Scenarios

Create custom scenarios in `tests/load/load-test-scenarios.js`:

```javascript
async function customScenario() {
    // Your custom load test logic
}
```

### Integration with CI/CD

Add load tests to CI pipeline:

```yaml
- name: Load Test
  run: |
    cd tests
    node load/load-test-scenarios.js steady 10 30
```

## Additional Resources

- [Performance Optimization Guide](../../apps/web-dashboard/docs/PERFORMANCE_OPTIMIZATION.md)
- [Laravel Performance](https://laravel.com/docs/queries#database-performance)
- [Load Testing Best Practices](https://k6.io/docs/test-types/load-testing/)
