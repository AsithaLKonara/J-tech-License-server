#!/bin/bash

# Load Testing Script
# Tests API endpoints under load

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
CONCURRENT_USERS="${CONCURRENT_USERS:-10}"
REQUESTS_PER_USER="${REQUESTS_PER_USER:-100}"
TEST_EMAIL="${TEST_EMAIL:-test@example.com}"
TEST_PASSWORD="${TEST_PASSWORD:-testpassword123}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Load Testing Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "API URL: $API_URL"
echo "Concurrent Users: $CONCURRENT_USERS"
echo "Requests per User: $REQUESTS_PER_USER"
echo ""

# Check if API is accessible
echo -e "${YELLOW}Checking API accessibility...${NC}"
if curl -f -s "$API_URL/api/v2/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is accessible${NC}"
else
    echo -e "${RED}✗ API is not accessible at $API_URL${NC}"
    exit 1
fi

# Create load test script
cat > /tmp/load-test.js << 'EOF'
const http = require('http');
const https = require('https');

const API_URL = process.env.API_URL || 'http://localhost:8000';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test@example.com';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'testpassword123';
const REQUESTS_PER_USER = parseInt(process.env.REQUESTS_PER_USER || '100');

const makeRequest = (options, data) => {
    return new Promise((resolve, reject) => {
        const protocol = API_URL.startsWith('https') ? https : http;
        const url = new URL(API_URL + options.path);
        
        const req = protocol.request({
            hostname: url.hostname,
            port: url.port || (url.protocol === 'https:' ? 443 : 80),
            path: url.pathname,
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            },
            timeout: 10000
        }, (res) => {
            let body = '';
            res.on('data', (chunk) => { body += chunk; });
            res.on('end', () => {
                resolve({
                    status: res.statusCode,
                    headers: res.headers,
                    body: body
                });
            });
        });
        
        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });
        
        if (data) {
            req.write(JSON.stringify(data));
        }
        req.end();
    });
};

async function runLoadTest() {
    const results = {
        total: 0,
        success: 0,
        failed: 0,
        errors: 0,
        times: []
    };
    
    const startTime = Date.now();
    
    // Login first to get token
    try {
        const loginResponse = await makeRequest({
            method: 'POST',
            path: '/api/v2/auth/login'
        }, {
            email: TEST_EMAIL,
            password: TEST_PASSWORD,
            device_id: 'load-test-device',
            device_name: 'Load Test Device'
        });
        
        if (loginResponse.status !== 200) {
            console.error('Login failed:', loginResponse.body);
            process.exit(1);
        }
        
        const loginData = JSON.parse(loginResponse.body);
        const token = loginData.session_token;
        
        // Run load test
        const promises = [];
        for (let i = 0; i < REQUESTS_PER_USER; i++) {
            const requestStart = Date.now();
            const promise = makeRequest({
                method: 'GET',
                path: '/api/v2/license/info',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }).then((response) => {
                const requestTime = Date.now() - requestStart;
                results.times.push(requestTime);
                results.total++;
                
                if (response.status === 200) {
                    results.success++;
                } else {
                    results.failed++;
                }
            }).catch((error) => {
                results.errors++;
                results.total++;
            });
            
            promises.push(promise);
            
            // Add small delay to avoid overwhelming
            if (i % 10 === 0) {
                await new Promise(resolve => setTimeout(resolve, 10));
            }
        }
        
        await Promise.all(promises);
        
        const endTime = Date.now();
        const totalTime = endTime - startTime;
        
        // Calculate statistics
        const sortedTimes = results.times.sort((a, b) => a - b);
        const avgTime = results.times.reduce((a, b) => a + b, 0) / results.times.length;
        const minTime = sortedTimes[0] || 0;
        const maxTime = sortedTimes[sortedTimes.length - 1] || 0;
        const medianTime = sortedTimes[Math.floor(sortedTimes.length / 2)] || 0;
        const p95Time = sortedTimes[Math.floor(sortedTimes.length * 0.95)] || 0;
        const p99Time = sortedTimes[Math.floor(sortedTimes.length * 0.99)] || 0;
        
        console.log(JSON.stringify({
            total: results.total,
            success: results.success,
            failed: results.failed,
            errors: results.errors,
            totalTime: totalTime,
            requestsPerSecond: (results.total / (totalTime / 1000)).toFixed(2),
            avgResponseTime: avgTime.toFixed(2),
            minResponseTime: minTime,
            maxResponseTime: maxTime,
            medianResponseTime: medianTime,
            p95ResponseTime: p95Time,
            p99ResponseTime: p99Time
        }));
        
    } catch (error) {
        console.error('Load test error:', error.message);
        process.exit(1);
    }
}

runLoadTest();
EOF

# Run load test for each concurrent user
echo -e "${YELLOW}Running load tests...${NC}"
echo ""

TOTAL_REQUESTS=0
TOTAL_SUCCESS=0
TOTAL_FAILED=0
TOTAL_ERRORS=0
TOTAL_TIME=0

for ((i=1; i<=CONCURRENT_USERS; i++)); do
    echo -e "${YELLOW}User $i/$CONCURRENT_USERS...${NC}"
    
    USER_START=$(date +%s%N)
    RESULT=$(API_URL="$API_URL" TEST_EMAIL="$TEST_EMAIL" TEST_PASSWORD="$TEST_PASSWORD" REQUESTS_PER_USER="$REQUESTS_PER_USER" node /tmp/load-test.js 2>&1)
    USER_END=$(date +%s%N)
    USER_TIME=$(( (USER_END - USER_START) / 1000000 ))
    
    if [ $? -eq 0 ]; then
        STATS=$(echo "$RESULT" | tail -1)
        echo "$STATS" | jq -r '"User \($i): \(.success)/\(.total) requests, \(.requestsPerSecond) req/s, avg: \(.avgResponseTime)ms"'
        
        REQUESTS=$(echo "$STATS" | jq -r '.total')
        SUCCESS=$(echo "$STATS" | jq -r '.success')
        FAILED=$(echo "$STATS" | jq -r '.failed')
        ERRORS=$(echo "$STATS" | jq -r '.errors')
        
        TOTAL_REQUESTS=$((TOTAL_REQUESTS + REQUESTS))
        TOTAL_SUCCESS=$((TOTAL_SUCCESS + SUCCESS))
        TOTAL_FAILED=$((TOTAL_FAILED + FAILED))
        TOTAL_ERRORS=$((TOTAL_ERRORS + ERRORS))
        TOTAL_TIME=$((TOTAL_TIME + USER_TIME))
    else
        echo -e "${RED}User $i failed${NC}"
        echo "$RESULT"
    fi
    
    # Small delay between users
    sleep 1
done

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Load Test Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Total Requests: $TOTAL_REQUESTS"
echo -e "Successful: ${GREEN}$TOTAL_SUCCESS${NC}"
echo -e "Failed: ${RED}$TOTAL_FAILED${NC}"
echo -e "Errors: ${RED}$TOTAL_ERRORS${NC}"
echo "Total Time: ${TOTAL_TIME}ms"
if [ $TOTAL_TIME -gt 0 ]; then
    RPS=$(echo "scale=2; $TOTAL_REQUESTS * 1000 / $TOTAL_TIME" | bc)
    echo "Average Requests/Second: $RPS"
fi
echo ""

# Cleanup
rm -f /tmp/load-test.js

if [ $TOTAL_FAILED -eq 0 ] && [ $TOTAL_ERRORS -eq 0 ]; then
    echo -e "${GREEN}Load test completed successfully! ✓${NC}"
    exit 0
else
    echo -e "${RED}Load test completed with failures.${NC}"
    exit 1
fi
