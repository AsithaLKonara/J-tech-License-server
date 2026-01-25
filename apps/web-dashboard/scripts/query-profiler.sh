#!/bin/bash

# Database Query Profiler
# Analyzes slow queries and database performance

set -e

echo "=========================================="
echo "Database Query Profiler"
echo "=========================================="
echo ""

# Check if we're in Laravel directory
if [ ! -f "artisan" ]; then
    echo "Error: Must run from Laravel root directory"
    exit 1
fi

# Enable query logging
echo "Enabling query logging..."
php artisan tinker <<EOF
DB::listen(function(\$query) {
    if (\$query->time > 100) { // Log queries > 100ms
        Log::info('Slow Query', [
            'sql' => \$query->sql,
            'bindings' => \$query->bindings,
            'time' => \$query->time . 'ms'
        ]);
    }
});
echo "Query logging enabled. Run your application and check storage/logs/laravel.log\n";
EOF

echo ""
echo "Query profiling enabled."
echo "Slow queries (>100ms) will be logged to storage/logs/laravel.log"
echo ""
echo "To view recent slow queries:"
echo "  tail -f storage/logs/laravel.log | grep 'Slow Query'"
echo ""
echo "To analyze all queries, use Laravel Debugbar or Telescope"
