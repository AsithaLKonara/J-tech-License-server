FROM php:8.2-fpm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libsqlite3-dev \
    zip \
    unzip \
    nginx \
    sqlite3 \
    procps \
    iproute2 \
    && docker-php-ext-install pdo_mysql pdo_sqlite mbstring exif pcntl bcmath gd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /app

# Copy composer files
COPY composer.json composer.lock ./

# Create necessary directories BEFORE composer install
RUN mkdir -p bootstrap/cache storage/framework/cache storage/framework/sessions storage/framework/views storage/logs \
    && chmod -R 775 bootstrap/cache storage

# Install dependencies without running scripts (artisan doesn't exist yet)
RUN composer install --ignore-platform-reqs --no-scripts --no-autoloader

# Copy application files (now artisan exists)
COPY . .

# Complete autoloader generation and run Laravel scripts
RUN composer dump-autoload --optimize \
    && php artisan package:discover --ansi || true

# Set permissions
RUN chown -R www-data:www-data /app \
    && chmod -R 775 storage bootstrap/cache

# Configure nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Create nginx log directory
RUN mkdir -p /var/log/nginx && chown www-data:www-data /var/log/nginx

# Create PHP-FPM pool configuration
RUN mkdir -p /var/run/php /run/php && \
    { \
        echo '[www]'; \
        echo 'user = www-data'; \
        echo 'group = www-data'; \
        echo 'listen = 127.0.0.1:9000'; \
        echo 'pm = dynamic'; \
        echo 'pm.max_children = 5'; \
        echo 'pm.start_servers = 2'; \
        echo 'pm.min_spare_servers = 1'; \
        echo 'pm.max_spare_servers = 3'; \
        echo 'pm.max_requests = 500'; \
    } > /usr/local/etc/php-fpm.d/www.conf

# Expose port (Railway will set PORT env var)
EXPOSE 80
ENV PORT=80

# Start script
COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

CMD ["/usr/local/bin/start.sh"]
