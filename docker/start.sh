#!/bin/bash
set -e

echo "🚀 Starting Upload Bridge License Server..."

# Create .env if it doesn't exist
if [ ! -f /app/.env ]; then
    echo "📝 Creating .env file from .env.example..."
    if [ -f /app/.env.example ]; then
        cp /app/.env.example /app/.env
    else
        # Create minimal .env
        cat > /app/.env <<EOF
APP_NAME="Upload Bridge"
APP_ENV=production
APP_KEY=
APP_DEBUG=false
APP_URL=http://localhost

LOG_CHANNEL=stderr
LOG_LEVEL=error

DB_CONNECTION=sqlite
DB_DATABASE=/app/database/database.sqlite

CACHE_DRIVER=file
SESSION_DRIVER=file
QUEUE_CONNECTION=sync

MAIL_MAILER=log
EOF
    fi
fi

# Generate APP_KEY if not set
if ! grep -q "APP_KEY=base64:" /app/.env; then
    echo "🔑 Generating APP_KEY..."
    php artisan key:generate --force || echo "Warning: Could not generate APP_KEY"
fi

# Ensure database exists (for SQLite)
if grep -q "DB_CONNECTION=sqlite" /app/.env; then
    mkdir -p /app/database
    touch /app/database/database.sqlite
    chmod 664 /app/database/database.sqlite
    chown www-data:www-data /app/database/database.sqlite
fi

# Clear and cache config
php artisan config:clear || true
php artisan cache:clear || true

# Ensure permissions
chown -R www-data:www-data /app/storage /app/bootstrap/cache
chmod -R 775 /app/storage /app/bootstrap/cache

echo "✅ Starting PHP-FPM..."
# Start PHP-FPM in background
php-fpm -D

# Wait for PHP-FPM to be ready
echo "⏳ Waiting for PHP-FPM to start..."
sleep 3

# Check if PHP-FPM is running
if ! pgrep -x php-fpm > /dev/null; then
    echo "⚠️  PHP-FPM not running, trying foreground mode..."
    php-fpm -F &
    sleep 2
fi

echo "✅ Starting Nginx..."
# Test nginx configuration
nginx -t || echo "⚠️  Nginx config test failed, continuing anyway..."

# Start Nginx in foreground (this keeps container alive)
exec nginx -g 'daemon off;'
