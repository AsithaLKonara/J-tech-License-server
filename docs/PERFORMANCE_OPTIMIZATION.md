# Performance Optimization Guide

This guide covers performance optimization strategies for the Upload Bridge web dashboard.

## Overview

Performance optimization is crucial for production deployments. This guide covers caching, database optimization, and monitoring strategies.

## Caching

### Redis Caching Setup

Redis is recommended for production environments to improve application performance.

#### Installation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
Download from: https://github.com/microsoftarchive/redis/releases

#### Configuration

1. Update `.env` file:
```env
CACHE_DRIVER=redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=null
REDIS_DB=0
REDIS_CACHE_DB=1
```

2. Verify Redis connection:
```bash
php artisan tinker
>>> Cache::put('test', 'value', 60);
>>> Cache::get('test');
```

#### Cache Usage

**Basic Caching:**
```php
use Illuminate\Support\Facades\Cache;

// Store for 60 minutes
Cache::put('key', 'value', 60);

// Retrieve
$value = Cache::get('key');

// Store forever
Cache::forever('key', 'value');

// Check if exists
if (Cache::has('key')) {
    // ...
}

// Remove
Cache::forget('key');

// Clear all
Cache::flush();
```

**Cache Tags (Redis only):**
```php
// Tagged cache
Cache::tags(['users', 'admins'])->put('key', 'value', 60);

// Clear by tag
Cache::tags(['users'])->flush();
```

**Remember Pattern:**
```php
$value = Cache::remember('key', 60, function () {
    return expensiveOperation();
});
```

### File Caching

For development or small deployments, file caching is sufficient:

```env
CACHE_DRIVER=file
```

Cache files are stored in `storage/framework/cache/data/`.

### Array Caching

For testing, use array cache (in-memory only):

```env
CACHE_DRIVER=array
```

## Database Optimization

### Query Optimization

**Use Eager Loading:**
```php
// Bad: N+1 queries
$users = User::all();
foreach ($users as $user) {
    echo $user->devices->count();
}

// Good: Single query with eager loading
$users = User::with('devices')->get();
foreach ($users as $user) {
    echo $user->devices->count();
}
```

**Use Indexes:**
Ensure database indexes on frequently queried columns:
- `users.email` (unique)
- `devices.user_id`
- `devices.device_id`
- `entitlements.user_id`
- `entitlements.status`

**Limit Results:**
```php
// Use pagination
$devices = Device::paginate(20);

// Limit when not needed
$recent = Device::latest()->limit(10)->get();
```

### Database Connection Pooling

For high-traffic applications, configure connection pooling in `config/database.php`:

```php
'mysql' => [
    // ...
    'options' => [
        PDO::MYSQL_ATTR_INIT_COMMAND => 'SET sql_mode="STRICT_TRANS_TABLES"',
        PDO::ATTR_PERSISTENT => true, // Connection pooling
    ],
],
```

## Application Optimization

### Route Caching

Cache routes for production:

```bash
php artisan route:cache
```

Clear when routes change:
```bash
php artisan route:clear
```

### Config Caching

Cache configuration:

```bash
php artisan config:cache
```

Clear when config changes:
```bash
php artisan config:clear
```

### View Caching

Cache compiled views:

```bash
php artisan view:cache
```

Clear when views change:
```bash
php artisan view:clear
```

### Optimize Autoloader

```bash
composer install --optimize-autoloader --no-dev
```

## Monitoring Performance

### Query Logging

Enable query logging in development:

```php
// In AppServiceProvider
if (config('app.debug')) {
    DB::listen(function ($query) {
        Log::info($query->sql, [
            'bindings' => $query->bindings,
            'time' => $query->time,
        ]);
    });
}
```

### Performance Profiling

Use Laravel Debugbar or Telescope for profiling:

```bash
composer require barryvdh/laravel-debugbar --dev
```

### Cache Statistics

Monitor cache hit rates:

```php
// Check cache stats (Redis)
$redis = Redis::connection('cache');
$info = $redis->info('stats');
```

## Production Checklist

- [ ] Redis caching enabled
- [ ] Route caching enabled
- [ ] Config caching enabled
- [ ] View caching enabled
- [ ] Optimized autoloader
- [ ] Database indexes created
- [ ] Query optimization reviewed
- [ ] Eager loading used where needed
- [ ] Pagination implemented
- [ ] Performance monitoring set up

## Performance Scripts

### Benchmark Script

Measure endpoint performance:

```bash
bash scripts/performance-benchmark.sh
```

Options:
- `APP_URL`: Target URL (default: http://localhost:8000)
- `ITERATIONS`: Number of requests (default: 100)
- `CONCURRENT`: Concurrent requests (default: 10)

### Query Profiler

Enable slow query logging:

```bash
bash scripts/query-profiler.sh
```

Slow queries (>100ms) will be logged to `storage/logs/laravel.log`.

### Memory Profiler

Monitor PHP process memory usage:

```bash
bash scripts/memory-profiler.sh
```

For continuous monitoring:
```bash
watch -n 1 bash scripts/memory-profiler.sh
```

### Load Testing

See [tests/README_LOAD_TESTING.md](../../tests/README_LOAD_TESTING.md) for comprehensive load testing guide.

## Additional Resources

- [Laravel Caching Documentation](https://laravel.com/docs/cache)
- [Laravel Database Optimization](https://laravel.com/docs/queries#database-performance)
- [Redis Documentation](https://redis.io/documentation)
