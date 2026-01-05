#!/bin/bash

# Railway Setup Script
# Helps set up the application for Railway deployment

set -e

echo "=========================================="
echo "Railway Setup Script"
echo "=========================================="
echo ""

# Check if we're in Laravel directory
if [ ! -f "artisan" ]; then
    echo "Error: Must run from Laravel root directory"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "1. Checking Railway configuration..."
if [ -f "railway.json" ]; then
    echo -e "${GREEN}✓${NC} railway.json exists"
else
    echo -e "${YELLOW}⚠${NC} railway.json not found (will be created)"
fi

if [ -f "Procfile" ]; then
    echo -e "${GREEN}✓${NC} Procfile exists"
else
    echo -e "${YELLOW}⚠${NC} Procfile not found (will be created)"
fi

echo ""
echo "2. Checking environment variables..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} Created .env file"
    else
        echo -e "${YELLOW}⚠${NC} .env.example not found"
    fi
fi

echo ""
echo "3. Required Railway environment variables:"
echo "   - APP_ENV=production"
echo "   - APP_DEBUG=false"
echo "   - APP_URL=https://your-app.railway.app"
echo "   - DATABASE_URL (automatically set by Railway)"
echo "   - MAIL_* (SMTP configuration)"
echo "   - STRIPE_* (Stripe keys)"
echo ""
echo "   Set these in Railway Dashboard → Your Service → Variables"
echo ""

echo "4. Next steps:"
echo "   1. Install Railway CLI: npm i -g @railway/cli"
echo "   2. Login: railway login"
echo "   3. Initialize: railway init"
echo "   4. Add database: railway add postgresql"
echo "   5. Set variables: railway variables set KEY=value"
echo "   6. Deploy: railway up"
echo ""
echo "   Or use Railway Dashboard:"
echo "   1. Connect GitHub repository"
echo "   2. Set root directory to apps/web-dashboard"
echo "   3. Add PostgreSQL database"
echo "   4. Set environment variables"
echo "   5. Deploy"
echo ""

echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "See docs/RAILWAY_DEPLOYMENT.md for detailed instructions"
