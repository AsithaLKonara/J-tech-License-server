#!/bin/bash
# Bash Deployment Script for Vercel
# Quick deploy script for Linux/Mac

echo "========================================"
echo "Upload Bridge License Server"
echo "Vercel Deployment Script"
echo "========================================"
echo ""

# Check Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found!"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi
echo "✅ Node.js found: $(node --version)"
echo ""

# Check npm
echo "Checking npm..."
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found!"
    exit 1
fi
echo "✅ npm found"
echo ""

# Check Vercel CLI
echo "Checking Vercel CLI..."
if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not found. Installing..."
    npm install -g vercel
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Vercel CLI"
        exit 1
    fi
    echo "✅ Vercel CLI installed"
else
    echo "✅ Vercel CLI found"
fi
echo ""

# Install dependencies
echo "Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"
echo ""

# Deploy
echo "Deploying to Vercel..."
echo "Follow the prompts:"
echo "  - Set up and deploy? → Y"
echo "  - Link to existing project? → N (first time)"
echo "  - Project name? → upload-bridge-license (or press Enter)"
echo "  - Directory? → . (press Enter)"
echo ""

vercel --prod

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "Next steps:"
    echo "  1. Copy the deployment URL from above"
    echo "  2. Update Upload Bridge config:"
    echo "     python ../apps/upload-bridge/scripts/update_vercel_url.py <URL>"
    echo ""
    echo "  3. Test the deployment:"
    echo "     curl https://your-project.vercel.app/api/health"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    exit 1
fi

