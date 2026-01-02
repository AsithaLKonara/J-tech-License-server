#!/bin/bash
# Auth0 CLI Setup Script for Upload Bridge License Server
# 
# This script uses Auth0 CLI to configure Auth0 settings programmatically.
# It automates the setup process similar to how Vercel CLI works.

set -e

AUTH0_DOMAIN="${AUTH0_DOMAIN:-}"
VERCEL_URL="${VERCEL_URL:-https://j-tech-licensing.vercel.app}"
APP_NAME="${APP_NAME:-Upload Bridge License Server}"
API_NAME="${API_NAME:-Upload Bridge License API}"
API_IDENTIFIER="${API_IDENTIFIER:-https://j-tech-licensing.vercel.app}"

echo "🔐 Auth0 CLI Setup for Upload Bridge License Server"
echo "=================================================="
echo ""

# Check if Auth0 CLI is installed
if ! command -v auth0 &> /dev/null; then
    echo "❌ Auth0 CLI not found!"
    echo ""
    echo "Please install Auth0 CLI first:"
    echo "  Option 1 (Homebrew - macOS):"
    echo "    brew tap auth0/auth0-cli"
    echo "    brew install auth0"
    echo ""
    echo "  Option 2 (npm):"
    echo "    npm install -g @auth0/auth0-cli"
    echo ""
    echo "  Option 3 (Linux):"
    echo "    curl -sSfL https://raw.githubusercontent.com/auth0/auth0-cli/main/install.sh | sh -s -- -b ."
    echo ""
    exit 1
fi

AUTH0_VERSION=$(auth0 --version 2>&1 || echo "unknown")
echo "✅ Auth0 CLI found: $AUTH0_VERSION"

# Check if logged in
echo ""
echo "Checking Auth0 authentication..."
if ! auth0 tenants list &> /dev/null; then
    echo "⚠️  Not authenticated. Please login:"
    echo "   auth0 login"
    echo ""
    read -p "Would you like to login now? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        auth0 login
        if [ $? -ne 0 ]; then
            echo "❌ Login failed"
            exit 1
        fi
    else
        exit 1
    fi
else
    echo "✅ Authenticated with Auth0"
fi

# Get Auth0 domain if not provided
if [ -z "$AUTH0_DOMAIN" ]; then
    echo ""
    echo "Auth0 Domain (e.g., your-tenant.auth0.com):"
    read -r AUTH0_DOMAIN
    
    if [ -z "$AUTH0_DOMAIN" ]; then
        echo "❌ Auth0 domain is required"
        exit 1
    fi
fi

echo ""
echo "Configuration:"
echo "  Auth0 Domain: $AUTH0_DOMAIN"
echo "  Vercel URL: $VERCEL_URL"
echo "  App Name: $APP_NAME"
echo "  API Name: $API_NAME"
echo "  API Identifier: $API_IDENTIFIER"
echo ""

# Check if Auth0 Deploy CLI is installed (optional but recommended)
HAS_DEPLOY_CLI=false
if command -v auth0-deploy &> /dev/null; then
    DEPLOY_VERSION=$(auth0-deploy --version 2>&1 || echo "unknown")
    echo "✅ Auth0 Deploy CLI found: $DEPLOY_VERSION"
    HAS_DEPLOY_CLI=true
else
    echo "⚠️  Auth0 Deploy CLI not found (optional)"
    echo "   Install with: npm install -g auth0-deploy-cli"
fi

echo ""
echo "📋 Setup Steps:"
echo ""

# Step 1: List existing applications
echo "1. Checking existing applications..."
if auth0 apps list --json &> /dev/null; then
    APP_COUNT=$(auth0 apps list --json 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
    echo "   Found $APP_COUNT existing application(s)"
    
    EXISTING_APP=$(auth0 apps list --json 2>/dev/null | jq -r ".[] | select(.name==\"$APP_NAME\") | .client_id" 2>/dev/null || echo "")
    if [ -n "$EXISTING_APP" ]; then
        echo "   ✅ Application '$APP_NAME' already exists (ID: $EXISTING_APP)"
        APP_ID=$EXISTING_APP
    else
        echo "   ℹ️  Application '$APP_NAME' not found - will need to be created manually or via Deploy CLI"
        echo "   (Auth0 CLI doesn't support creating apps with full config - use Dashboard or Deploy CLI)"
    fi
else
    echo "   ⚠️  Could not list applications (may need Management API access)"
fi

# Step 2: Provide configuration instructions
echo ""
echo "2. Configuration Instructions:"
echo ""
echo "   Since Auth0 CLI has limitations for application creation, here's what to configure:"
echo ""
echo "   📝 Application Settings (in Auth0 Dashboard):"
echo "      Application Type: Native"
echo "      Allowed Callback URLs:"
echo "        - http://localhost:3000/callback"
echo "        - $VERCEL_URL/callback"
echo "      Allowed Logout URLs:"
echo "        - http://localhost:3000"
echo "        - $VERCEL_URL"
echo "      Allowed Web Origins:"
echo "        - http://localhost:3000"
echo "        - $VERCEL_URL"
echo "      Grant Types:"
echo "        - Authorization Code"
echo "        - Refresh Token"
echo ""

# Step 3: Use Deploy CLI if available
if [ "$HAS_DEPLOY_CLI" = true ]; then
    echo "3. Using Auth0 Deploy CLI for configuration..."
    
    CONFIG_DIR="$(dirname "$0")/auth0-config"
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        echo "   Created config directory: $CONFIG_DIR"
    fi
    
    echo "   ⚠️  Configuration files need to be created manually"
    echo "   See AUTH0_CLI_SETUP.md for example configuration"
    echo ""
else
    echo "3. Skipping Deploy CLI configuration (not installed)"
    echo ""
fi

# Step 4: Test authentication
echo "4. Testing authentication flow..."
echo "   Run 'auth0 test login' to test the authentication flow"
echo ""

# Summary
echo "=================================================="
echo "✅ Setup Complete!"
echo ""
echo "Next Steps:"
echo "  1. Configure application in Auth0 Dashboard (see instructions above)"
echo "  2. Set environment variables:"
echo "     export AUTH0_DOMAIN='$AUTH0_DOMAIN'"
echo "     export AUTH0_CLIENT_ID='<your-client-id>'"
echo "  3. Test authentication: auth0 test login"
echo "  4. Run tests: npm run test:auth0"
echo ""
echo "For more details, see AUTH0_CLI_SETUP.md"
echo ""

