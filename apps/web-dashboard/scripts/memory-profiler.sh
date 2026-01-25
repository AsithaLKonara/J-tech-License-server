#!/bin/bash

# Memory Profiler Script
# Monitors memory usage of PHP processes

set -e

echo "=========================================="
echo "Memory Profiler"
echo "=========================================="
echo ""

# Check if ps is available
if ! command -v ps &> /dev/null; then
    echo "Error: ps command not available"
    exit 1
fi

echo "PHP Process Memory Usage:"
echo "-------------------------"

# Find PHP processes
ps aux | grep -E "php|php-fpm|artisan" | grep -v grep | while read line; do
    PID=$(echo $line | awk '{print $2}')
    MEM=$(echo $line | awk '{print $6}')
    MEM_MB=$(echo "scale=2; $MEM / 1024" | bc)
    CMD=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
    
    echo "PID: $PID | Memory: ${MEM_MB}MB | $CMD"
done

echo ""
echo "Total PHP Memory Usage:"

# Calculate total
TOTAL=$(ps aux | grep -E "php|php-fpm|artisan" | grep -v grep | awk '{sum+=$6} END {print sum}')
TOTAL_MB=$(echo "scale=2; $TOTAL / 1024" | bc)

echo "Total: ${TOTAL_MB}MB"
echo ""

# Memory limits
echo "PHP Memory Limits:"
php -r "echo 'memory_limit: ' . ini_get('memory_limit') . PHP_EOL;"
php -r "echo 'max_execution_time: ' . ini_get('max_execution_time') . 's' . PHP_EOL;"

echo ""
echo "To monitor continuously, run:"
echo "  watch -n 1 bash scripts/memory-profiler.sh"
