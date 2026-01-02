#!/bin/bash
# Setup Auth0 Configuration for Vercel
# This script configures Auth0 environment variables in Vercel

set -e

echo "🔐 Setting up Auth0 configuration for Vercel..."

# Auth0 Configuration
AUTH0_DOMAIN="dev-oczlciw58f2a4oei.us.auth0.com"
AUTH0_CLIENT_ID="7kciWD98RzUsktuzXtJkfSmLcr80Ix2X"
VERCEL_URL="https://j-tech-licensing.vercel.app"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed"
    echo "   Install it with: npm install -g vercel"
    exit 1
fi

# Check if logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "⚠️  Not logged in to Vercel"
    echo "   Run: vercel login"
    exit 1
fi

echo "✅ Vercel CLI is ready"
echo ""

# Set environment variables for production
echo "Setting environment variables for Production..."
vercel env add AUTH0_DOMAIN production <<< "$AUTH0_DOMAIN" || vercel env rm AUTH0_DOMAIN production --yes && vercel env add AUTH0_DOMAIN production <<< "$AUTH0_DOMAIN"
vercel env add AUTH0_CLIENT_ID production <<< "$AUTH0_CLIENT_ID" || vercel env rm AUTH0_CLIENT_ID production --yes && vercel env add AUTH0_CLIENT_ID production <<< "$AUTH0_CLIENT_ID"

# Set for preview environment
echo "Setting environment variables for Preview..."
vercel env add AUTH0_DOMAIN preview <<< "$AUTH0_DOMAIN" || vercel env rm AUTH0_DOMAIN preview --yes && vercel env add AUTH0_DOMAIN preview <<< "$AUTH0_DOMAIN"
vercel env add AUTH0_CLIENT_ID preview <<< "$AUTH0_CLIENT_ID" || vercel env rm AUTH0_CLIENT_ID preview --yes && vercel env add AUTH0_CLIENT_ID preview <<< "$AUTH0_CLIENT_ID"

# Set for development environment
echo "Setting environment variables for Development..."
vercel env add AUTH0_DOMAIN development <<< "$AUTH0_DOMAIN" || vercel env rm AUTH0_DOMAIN development --yes && vercel env add AUTH0_DOMAIN development <<< "$AUTH0_DOMAIN"
vercel env add AUTH0_CLIENT_ID development <<< "$AUTH0_CLIENT_ID" || vercel env rm AUTH0_CLIENT_ID development --yes && vercel env add AUTH0_CLIENT_ID development <<< "$AUTH0_CLIENT_ID"

echo ""
echo "✅ Environment variables configured!"
echo ""
echo "📋 Configuration Summary:"
echo "   AUTH0_DOMAIN: $AUTH0_DOMAIN"
echo "   AUTH0_CLIENT_ID: $AUTH0_CLIENT_ID"
echo "   Vercel URL: $VERCEL_URL"
echo ""
echo "🚀 Next steps:"
echo "   1. Redeploy to apply changes: vercel --prod"
echo "   2. Test the health endpoint: curl $VERCEL_URL/api/health"
echo "   3. See VERIFY_AUTH0_SETUP.md for testing instructions"

