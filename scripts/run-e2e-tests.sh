#!/bin/bash
# E2E Test Runner Script for Linux/Mac
# Runs comprehensive E2E test suite

CATEGORY=${1:-all}
VERBOSE=${2:-false}
PARALLEL=${3:-false}
COVERAGE=${4:-false}

echo "========================================"
echo "E2E Test Suite Runner"
echo "========================================"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Build pytest command
PYTEST_CMD="pytest tests/e2e"

if [ "$VERBOSE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$CATEGORY" != "all" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $CATEGORY"
fi

if [ "$PARALLEL" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

if [ "$COVERAGE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=apps/upload-bridge --cov=apps/web-dashboard --cov-report=html --cov-report=term-missing"
fi

echo "Running: $PYTEST_CMD"
echo ""

# Run tests
eval $PYTEST_CMD

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "All tests passed!"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "Some tests failed!"
    echo "========================================"
fi

exit $EXIT_CODE
