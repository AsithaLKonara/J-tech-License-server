#!/bin/bash
set -e

echo "🚀 VERSION: 2.1.1_FIXED_SED_AGAIN"

# ==============================================================================
# 1. SETUP FILESYSTEM
# ==============================================================================
mkdir -p /app/database /var/log/nginx /app/storage/framework/{sessions,views,cache} /app/storage/logs /app/bootstrap/cache
touch /app/database/database.sqlite
chmod -R 777 /app/database /var/log/nginx /app/storage /app/bootstrap/cache

# ==============================================================================
# 2. ENV
# ==============================================================================
if [ ! -f .env ]; then cp .env.example .env; fi
chmod 666 .env
php artisan key:generate --force
php artisan migrate --force --no-interaction || true
php artisan config:clear

# ==============================================================================
# 3. START SERVICES
# ==============================================================================
echo "✅ Starting PHP-FPM..."
mkdir -p /run/php
chmod 777 /run/php
php-fpm -D

# DYNAMIC PORT (Default 8080)
LISTENING_PORT=${PORT:-8080}
echo "📡 LISTENING ON: ${LISTENING_PORT}"

cp /app/docker/nginx.conf /etc/nginx/sites-available/default
sed -i "s/{{PORT}}/${LISTENING_PORT}/g" /etc/nginx/sites-available/default
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# LOGGING is already set to /dev/stdout in nginx.conf. DO NOT USE SED HERE.

# Verify Config
echo "✅ Validating Nginx Config..."
nginx -t

echo "🚀 Starting Nginx..."
exec nginx -g "daemon off;"
