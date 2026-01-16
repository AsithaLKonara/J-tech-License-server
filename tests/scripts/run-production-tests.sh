#!/bin/bash

# Production Readiness Test Suite
# This script runs all tests required for production readiness validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
BASE_URL="${BASE_URL:-$API_URL}"
TEST_TIMEOUT="${TEST_TIMEOUT:-30000}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Production Readiness Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if API is accessible
echo -e "${YELLOW}Checking API accessibility...${NC}"
if curl -f -s "$API_URL/api/v2/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is accessible${NC}"
else
    echo -e "${RED}✗ API is not accessible at $API_URL${NC}"
    echo "Please ensure the application is running before running tests."
    exit 1
fi

# Test results tracking
PASSED=0
FAILED=0

# Function to run a test file
run_test() {
    local test_file=$1
    local test_name=$2
    
    echo ""
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if node run-test.js "$test_file"; then
        echo -e "${GREEN}✓ $test_name PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ $test_name FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# Authentication Tests
echo ""
echo -e "${GREEN}=== Authentication Tests ===${NC}"
run_test "tests/api/auth-e2e.test.js" "Authentication E2E Tests"

# License Tests
echo ""
echo -e "${GREEN}=== License Tests ===${NC}"
run_test "tests/api/license-e2e.test.js" "License E2E Tests"

# Device Tests
echo ""
echo -e "${GREEN}=== Device Tests ===${NC}"
run_test "tests/api/device-e2e.test.js" "Device E2E Tests"

# Health Tests
echo ""
echo -e "${GREEN}=== Health Check Tests ===${NC}"
run_test "tests/api/health-e2e.test.js" "Health Check Tests"

# Security Tests
echo ""
echo -e "${GREEN}=== Security Tests ===${NC}"
if [ -f "tests/security/security-tests.test.js" ]; then
    run_test "tests/security/security-tests.test.js" "Security Tests"
else
    echo -e "${YELLOW}⚠ Security tests not found, skipping...${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
