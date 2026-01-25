#!/bin/bash
set -e
# Ensure we catch any errors in background processes
set -o pipefail

echo "🚀 VERSION: 2.1.1_FIXED_SED_AGAIN"

# ==============================================================================
# 1. SETUP FILESYSTEM
# ==============================================================================
mkdir -p /app/database /var/log/nginx /app/storage/framework/{sessions,views,cache} /app/storage/logs /app/bootstrap/cache
touch /app/database/database.sqlite
chmod -R 777 /app/database /var/log/nginx /app/storage /app/bootstrap/cache

# ==============================================================================
# 2. ENV & PREPARE APP
# ==============================================================================
if [ ! -f .env ]; then 
    echo "📄 Creating .env from example..."
    cp .env.example .env
fi
chmod 666 .env

if [ -z "$APP_KEY" ]; then
    echo "🔑 No APP_KEY in environment, generating one..."
    php artisan key:generate --force --no-interaction
else
    echo "✅ Using APP_KEY from environment"
fi

echo "🗄️ Running Migrations..."
# Run migrations and capture output
if php artisan migrate --force --no-interaction; then
    echo "✅ Migrations complete"
else
    echo "⚠️ Migrations failed or already up to date"
fi

echo "🌱 Seeding Database..."
php artisan db:seed --force --no-interaction || echo "⚠️ Seeding failed"

echo "🧹 Formatting Storage & Permissions..."
mkdir -p /app/storage/framework/{sessions,views,cache} /app/storage/logs /app/bootstrap/cache
chmod -R 777 /app/storage /app/bootstrap/cache /app/database

echo "✨ Clearing Cache & Optimizing..."
php artisan config:clear
php artisan cache:clear
php artisan view:clear
composer dump-autoload --optimize

# ==============================================================================
# 3. START SERVICES
# ==============================================================================
echo "✅ Starting PHP-FPM..."
php-fpm -D

# Verify FPM is listening
sleep 2
echo "|-- PHP-FPM started"


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

# Diagnostics
echo "📊 PROCESS CHECK:"
ps aux | grep -E "php|nginx"
echo "🌐 PORT CHECK:"
ss -tulpn || netstat -tulpn || true

# Pre-touch logs to ensure tail works
touch /var/log/nginx/error.log /var/log/nginx/access.log

# Tail Nginx logs to stdout in background
tail -f /var/log/nginx/error.log &
tail -f /var/log/nginx/access.log &

echo "🚀 Starting Nginx..."
# Use -g "daemon off;" to keep container alive
exec nginx -g "daemon off;"
