#!/bin/bash
# Setup Test Environment Variables for Upload Bridge
# Shell script for Linux/macOS

echo "========================================"
echo "Upload Bridge - Test Environment Setup"
echo "========================================"
echo ""

# Test Auth0 Configuration (for OAuth/Social Login testing)
echo "Setting Auth0 test configuration..."

# Sample Auth0 values for testing (replace with your actual Auth0 credentials)
export AUTH0_DOMAIN="dev-test-123.us.auth0.com"
export AUTH0_CLIENT_ID="test-client-id-abc123"
export AUTH0_AUDIENCE="https://api.test.example.com"

# License Server URL (default: localhost:3000)
export LICENSE_SERVER_URL="http://localhost:3000"
export AUTH_SERVER_URL="http://localhost:3000"

echo "✅ Environment variables set:"
echo "   AUTH0_DOMAIN = $AUTH0_DOMAIN"
echo "   AUTH0_CLIENT_ID = $AUTH0_CLIENT_ID"
echo "   AUTH0_AUDIENCE = $AUTH0_AUDIENCE"
echo "   LICENSE_SERVER_URL = $LICENSE_SERVER_URL"
echo ""

echo "⚠️  NOTE: These are TEST values!"
echo "   Replace with your actual Auth0 credentials for production use."
echo ""

echo "To use these variables in this shell session:"
echo "   source scripts/setup_test_env.sh"
echo ""

echo "To set permanently (add to ~/.bashrc or ~/.zshrc):"
echo "   export AUTH0_DOMAIN=\"$AUTH0_DOMAIN\""
echo "   export AUTH0_CLIENT_ID=\"$AUTH0_CLIENT_ID\""
echo ""

echo "========================================"
echo "Environment setup complete!"
echo "========================================"

