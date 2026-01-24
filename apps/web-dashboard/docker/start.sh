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
    echo "📦 Setting up SQLite database..."
    mkdir -p /app/database
    touch /app/database/database.sqlite
    chmod 664 /app/database/database.sqlite
    chown www-data:www-data /app/database/database.sqlite
    
    # Run migrations if database is empty
    echo "🔄 Running database migrations..."
    php artisan migrate --force || echo "⚠️  Migration failed or already up to date"
fi

# Clear and cache config
echo "🧹 Clearing Laravel caches..."
php artisan config:clear || true
php artisan cache:clear || true
php artisan route:clear || true

# Ensure permissions
echo "🔐 Setting permissions..."
chown -R www-data:www-data /app/storage /app/bootstrap/cache /app/database 2>/dev/null || true
chmod -R 775 /app/storage /app/bootstrap/cache 2>/dev/null || true

# Test Laravel bootstrap
echo "🧪 Testing Laravel bootstrap..."
if php artisan --version > /dev/null 2>&1; then
    echo "✅ Laravel is working"
else
    echo "⚠️  Laravel artisan command failed, but continuing..."
    # Try to see what the error is
    php artisan --version 2>&1 | head -5 || true
fi

# Start PHP-FPM
echo "✅ Starting PHP-FPM..."
php-fpm -D

# Wait for PHP-FPM to be ready
echo "⏳ Waiting for PHP-FPM to start..."
for i in {1..10}; do
    if pgrep -x php-fpm > /dev/null; then
        echo "✅ PHP-FPM process is running (attempt $i)"
        break
    fi
    sleep 1
done

# Wait a bit more for socket to be ready
sleep 2

# Check if PHP-FPM is listening on port 9000
if command -v ss >/dev/null 2>&1 && ss -tlnp 2>/dev/null | grep -q ':9000'; then
    echo "✅ PHP-FPM is listening on port 9000"
elif [ -S /var/run/php/php8.2-fpm.sock ] || [ -S /run/php/php8.2-fpm.sock ]; then
    echo "✅ PHP-FPM socket exists"
else
    echo "⚠️  PHP-FPM socket/port check inconclusive, but process is running"
fi

# Handle PORT environment variable (Railway sets this dynamically)
if [ -n "$PORT" ] && [ "$PORT" != "80" ]; then
    echo "🔧 Updating Nginx to listen on port $PORT (Railway dynamic port)..."
    # Replace all 'listen 80' variants with the dynamic port
    sed -i "s/listen 80/listen ${PORT}/g" /etc/nginx/sites-available/default
    # Also update any symlinked version to be sure
    if [ -f /etc/nginx/sites-enabled/default ]; then
        sed -i "s/listen 80/listen ${PORT}/g" /etc/nginx/sites-enabled/default
    fi
    echo "📝 Nginx will listen on port $PORT"
else
    echo "📝 Nginx will listen on default port 80"
fi

# Test nginx configuration
echo "✅ Testing Nginx configuration..."
if ! nginx -t; then
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

# Create nginx log directory
mkdir -p /var/log/nginx
chown www-data:www-data /var/log/nginx

# Start Nginx
echo "✅ Starting Nginx..."
echo "📋 Nginx and PHP-FPM are starting. Check logs if healthcheck fails:"
echo "   - Nginx: /var/log/nginx/error.log"
echo "   - PHP-FPM: Check container logs"
echo ""
echo "🌐 Health check endpoints available:"
echo "   - http://localhost:${PORT:-80}/health (simple, no Laravel)"
echo "   - http://localhost:${PORT:-80}/health.php (PHP, no Laravel)"
echo "   - http://localhost:${PORT:-80}/api/v2/health (Laravel endpoint)"

# Start Nginx in foreground (this keeps container alive)
exec nginx -g 'daemon off;'
