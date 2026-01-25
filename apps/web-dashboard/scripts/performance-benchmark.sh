#!/bin/bash

# Performance Benchmark Script
# Measures application performance metrics

set -e

APP_URL="${APP_URL:-http://localhost:8000}"
ITERATIONS="${ITERATIONS:-100}"
CONCURRENT="${CONCURRENT:-10}"

echo "=========================================="
echo "Performance Benchmark"
echo "=========================================="
echo "Target: $APP_URL"
echo "Iterations: $ITERATIONS"
echo "Concurrent: $CONCURRENT"
echo ""

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required"
    exit 1
fi

# Results
TOTAL_TIME=0
SUCCESS=0
FAILED=0
TIMES=()

# Benchmark function
benchmark_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    
    echo "Benchmarking: $method $endpoint"
    
    for i in $(seq 1 $ITERATIONS); do
        START=$(date +%s.%N)
        
        if [ "$method" = "GET" ]; then
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$APP_URL$endpoint" || echo "000")
        else
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" --max-time 10 "$APP_URL$endpoint" || echo "000")
        fi
        
        END=$(date +%s.%N)
        ELAPSED=$(echo "$END - $START" | bc)
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
            SUCCESS=$((SUCCESS + 1))
            TIMES+=($ELAPSED)
            TOTAL_TIME=$(echo "$TOTAL_TIME + $ELAPSED" | bc)
        else
            FAILED=$((FAILED + 1))
        fi
    done
    
    # Calculate statistics
    if [ ${#TIMES[@]} -gt 0 ]; then
        SORTED_TIMES=($(printf '%s\n' "${TIMES[@]}" | sort -n))
        MIN=${SORTED_TIMES[0]}
        MAX=${SORTED_TIMES[${#SORTED_TIMES[@]}-1]}
        AVG=$(echo "scale=3; $TOTAL_TIME / $SUCCESS" | bc)
        
        # Median
        MID=$(( ${#SORTED_TIMES[@]} / 2 ))
        if [ $((${#SORTED_TIMES[@]} % 2)) -eq 0 ]; then
            MEDIAN=$(echo "scale=3; (${SORTED_TIMES[$MID-1]} + ${SORTED_TIMES[$MID]}) / 2" | bc)
        else
            MEDIAN=${SORTED_TIMES[$MID]}
        fi
        
        echo "  Success: $SUCCESS"
        echo "  Failed: $FAILED"
        echo "  Min: ${MIN}s"
        echo "  Max: ${MAX}s"
        echo "  Avg: ${AVG}s"
        echo "  Median: ${MEDIAN}s"
        echo ""
    fi
}

# Health check endpoint
benchmark_endpoint "/api/v2/health" "GET"

# Reset counters
TOTAL_TIME=0
SUCCESS=0
FAILED=0
TIMES=()

echo "=========================================="
echo "Benchmark Complete"
echo "=========================================="
