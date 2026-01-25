#!/bin/bash

# Pre-Deployment Check Script
# Verifies all requirements before deployment

set -e

echo "=========================================="
echo "Pre-Deployment Checklist"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# Check if .env file exists
echo "1. Environment Configuration"
if [ -f ".env" ]; then
    check_pass ".env file exists"
else
    check_fail ".env file not found"
    exit 1
fi

# Check required environment variables
REQUIRED_VARS=(
    "APP_NAME"
    "APP_ENV"
    "APP_KEY"
    "APP_URL"
    "DB_CONNECTION"
)

for var in "${REQUIRED_VARS[@]}"; do
    if grep -q "^${var}=" .env && ! grep -q "^${var}=$" .env && ! grep -q "^${var}=\s*$" .env; then
        check_pass "${var} is set"
    else
        check_fail "${var} is not set or empty"
    fi
done

# Check production-specific variables
if grep -q "^APP_ENV=production" .env; then
    if grep -q "^APP_DEBUG=false" .env; then
        check_pass "APP_DEBUG is false (production)"
    else
        check_warn "APP_DEBUG should be false in production"
    fi
    
    if grep -q "^APP_URL=https://" .env; then
        check_pass "APP_URL uses HTTPS"
    else
        check_warn "APP_URL should use HTTPS in production"
    fi
fi

# Database configuration
echo ""
echo "2. Database Configuration"
DB_CONNECTION=$(grep "^DB_CONNECTION=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")

if [ "$DB_CONNECTION" = "mysql" ] || [ "$DB_CONNECTION" = "pgsql" ]; then
    DB_VARS=("DB_HOST" "DB_DATABASE" "DB_USERNAME" "DB_PASSWORD")
    for var in "${DB_VARS[@]}"; do
        if grep -q "^${var}=" .env && ! grep -q "^${var}=$" .env; then
            check_pass "${var} is set"
        else
            check_fail "${var} is not set or empty"
        fi
    done
    
    # Test database connection
    echo "   Testing database connection..."
    if php artisan db:show &>/dev/null; then
        check_pass "Database connection successful"
    else
        check_fail "Database connection failed"
    fi
elif [ "$DB_CONNECTION" = "sqlite" ]; then
    DB_PATH=$(grep "^DB_DATABASE=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    if [ -f "$DB_PATH" ]; then
        check_pass "SQLite database file exists"
    else
        check_fail "SQLite database file not found: $DB_PATH"
    fi
fi

# Check migrations
echo ""
echo "3. Database Migrations"
if php artisan migrate:status &>/dev/null; then
    PENDING=$(php artisan migrate:status 2>/dev/null | grep -c "Pending" || echo "0")
    if [ "$PENDING" -eq 0 ]; then
        check_pass "All migrations are up to date"
    else
        check_warn "$PENDING pending migration(s)"
    fi
else
    check_fail "Could not check migration status"
fi

# SSL Certificate (if HTTPS)
echo ""
echo "4. SSL/TLS Configuration"
if grep -q "^APP_URL=https://" .env; then
    APP_URL=$(grep "^APP_URL=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    DOMAIN=$(echo "$APP_URL" | sed -e 's|https\?://||' -e 's|/.*$||')
    
    if command -v openssl &> /dev/null; then
        if echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | grep -q "Verify return code: 0"; then
            check_pass "SSL certificate is valid"
        else
            check_warn "Could not verify SSL certificate (may need manual check)"
        fi
    else
        check_warn "openssl not available, skipping SSL check"
    fi
else
    check_pass "HTTPS not required (development)"
fi

# File permissions
echo ""
echo "5. File Permissions"
if [ -w "storage" ] && [ -w "bootstrap/cache" ]; then
    check_pass "Storage and cache directories are writable"
else
    check_fail "Storage or cache directories are not writable"
    echo "   Run: chmod -R 775 storage bootstrap/cache"
fi

# Check configuration cache
echo ""
echo "6. Configuration"
if php artisan config:cache &>/dev/null; then
    check_pass "Configuration cache created successfully"
    php artisan config:clear &>/dev/null
else
    check_fail "Configuration cache failed"
fi

# Check route cache
if php artisan route:cache &>/dev/null; then
    check_pass "Route cache created successfully"
    php artisan route:clear &>/dev/null
else
    check_warn "Route cache failed (may have closure routes)"
fi

# Check view cache
if php artisan view:cache &>/dev/null; then
    check_pass "View cache created successfully"
    php artisan view:clear &>/dev/null
else
    check_fail "View cache failed"
fi

# Smoke tests
echo ""
echo "7. Smoke Tests"
if php artisan tinker --execute="echo 'OK';" &>/dev/null; then
    check_pass "Application can boot"
else
    check_fail "Application failed to boot"
fi

# Check for common issues
echo ""
echo "8. Common Issues"
if grep -q "password123\|changeme\|secret" .env; then
    check_warn "Default passwords detected in .env - change them!"
fi

if [ -f "composer.lock" ]; then
    check_pass "composer.lock exists"
else
    check_warn "composer.lock not found - run: composer install"
fi

# Summary
echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $(($(echo "$(grep -c '✓' <<< "$(cat)")" || echo "0")))"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Errors:${NC} $ERRORS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Deployment check failed with $ERRORS error(s)${NC}"
    exit 1
fi
