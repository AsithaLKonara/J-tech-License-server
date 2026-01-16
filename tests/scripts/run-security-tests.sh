#!/bin/bash

# Security Testing Script
# Runs security tests to verify protection against common vulnerabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
BASE_URL="${BASE_URL:-$API_URL}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Security Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "API URL: $API_URL"
echo ""

# Check if API is accessible
echo -e "${YELLOW}Checking API accessibility...${NC}"
if curl -f -s "$API_URL/api/v2/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is accessible${NC}"
else
    echo -e "${RED}✗ API is not accessible at $API_URL${NC}"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    exit 1
fi

# Check if test file exists
if [ ! -f "tests/security/security-tests.test.js" ]; then
    echo -e "${RED}✗ Security test file not found${NC}"
    exit 1
fi

# Run security tests
echo ""
echo -e "${YELLOW}Running security tests...${NC}"
echo ""

cd "$(dirname "$0")/../.." || exit 1

if API_URL="$API_URL" BASE_URL="$BASE_URL" node tests/security/security-tests.test.js; then
    echo ""
    echo -e "${GREEN}Security tests completed successfully! ✓${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Security tests failed. Please review the output above.${NC}"
    exit 1
fi
