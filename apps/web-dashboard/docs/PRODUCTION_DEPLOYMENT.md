# Production Deployment Guide

This guide provides step-by-step instructions for deploying the Upload Bridge web dashboard to production.

## Prerequisites

Before deploying, ensure you have:

- Server with PHP 8.2+ and required extensions
- Web server (Apache/Nginx)
- Database (MySQL 5.7+ or PostgreSQL 10+)
- SSL certificate
- Domain name configured
- Stripe account (production)
- SMTP email service

## Step 1: Server Preparation

### 1.1 Install Required Software

#### PHP 8.2+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install php8.2 php8.2-fpm php8.2-mysql php8.2-pgsql php8.2-curl \
    php8.2-mbstring php8.2-xml php8.2-zip php8.2-gd php8.2-bcmath

# CentOS/RHEL
sudo yum install php82 php82-php-fpm php82-php-mysqlnd php82-php-pgsql \
    php82-php-curl php82-php-mbstring php82-php-xml php82-php-zip
```

#### Composer
```bash
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
```

#### Web Server
- Apache 2.4+ or Nginx 1.18+

### 1.2 Configure PHP

Edit `php.ini`:
```ini
memory_limit = 256M
upload_max_filesize = 10M
post_max_size = 10M
max_execution_time = 300
```

## Step 2: Application Deployment

### 2.1 Clone Repository

```bash
cd /var/www
git clone <repository-url> upload-bridge
cd upload-bridge/apps/web-dashboard
```

### 2.2 Install Dependencies

```bash
composer install --optimize-autoloader --no-dev
```

### 2.3 Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/upload-bridge
sudo chmod -R 755 /var/www/upload-bridge
sudo chmod -R 775 storage bootstrap/cache
```

## Step 3: Environment Configuration

### 3.1 Create .env File

```bash
cp .env.example .env
```

### 3.2 Configure Environment Variables

Edit `.env` with production values:

```env
APP_NAME="Upload Bridge"
APP_ENV=production
APP_DEBUG=false
APP_URL=https://yourdomain.com
APP_KEY=

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge
DB_USERNAME=upload_bridge_user
DB_PASSWORD=strong_password_here

STRIPE_KEY=pk_live_your_key
STRIPE_SECRET=sk_live_your_secret
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_PRICE_MONTHLY=price_monthly_id
STRIPE_PRICE_ANNUAL=price_annual_id
STRIPE_PRICE_LIFETIME=price_lifetime_id

MAIL_MAILER=smtp
MAIL_HOST=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=your_username
MAIL_PASSWORD=your_password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge"

SESSION_SECURE_COOKIE=true
```

### 3.3 Generate Application Key

```bash
php artisan key:generate
```

### 3.4 Secure .env File

```bash
chmod 600 .env
```

## Step 4: Database Setup

### 4.1 Create Database

```sql
CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'upload_bridge_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON upload_bridge.* TO 'upload_bridge_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4.2 Run Migrations

```bash
php artisan migrate --force
```

### 4.3 Create Admin User

```bash
# Set admin credentials in .env
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_NAME="Administrator"
ADMIN_PASSWORD=strong_password_here

# Run seeder
php artisan db:seed --class=AdminUserSeeder
```

**IMPORTANT**: Change admin password immediately after first login!

## Step 5: SSL/TLS Configuration

### 5.1 Install SSL Certificate

See [SSL_SETUP.md](SSL_SETUP.md) for detailed instructions.

### 5.2 Configure Web Server

#### Apache Configuration

Create `/etc/apache2/sites-available/upload-bridge-ssl.conf`:

```apache
<VirtualHost *:443>
    ServerName yourdomain.com
    DocumentRoot /var/www/upload-bridge/apps/web-dashboard/public

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/yourdomain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/yourdomain.com/privkey.pem

    <Directory /var/www/upload-bridge/apps/web-dashboard/public>
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/upload-bridge-error.log
    CustomLog ${APACHE_LOG_DIR}/upload-bridge-access.log combined
</VirtualHost>

<VirtualHost *:80>
    ServerName yourdomain.com
    Redirect permanent / https://yourdomain.com/
</VirtualHost>
```

Enable site:
```bash
sudo a2ensite upload-bridge-ssl
sudo systemctl reload apache2
```

#### Nginx Configuration

Create `/etc/nginx/sites-available/upload-bridge`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    root /var/www/upload-bridge/apps/web-dashboard/public;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.2-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/upload-bridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 6: Stripe Configuration

### 6.1 Configure Stripe Keys

See [STRIPE_SETUP.md](STRIPE_SETUP.md) for detailed instructions.

### 6.2 Set Up Webhook

1. Log into Stripe Dashboard
2. Go to Developers → Webhooks
3. Add endpoint: `https://yourdomain.com/webhook/stripe`
4. Select events to send
5. Copy webhook secret to `.env`

## Step 7: Email Configuration

### 7.1 Configure SMTP

See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed instructions.

### 7.2 Test Email Delivery

```bash
php artisan tinker
>>> Mail::raw('Test email', function($message) {
...     $message->to('your@email.com')->subject('Test');
... });
```

## Step 8: Final Configuration

### 8.1 Clear Caches

```bash
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

### 8.2 Set Up Queue (Optional)

For better performance:

```bash
php artisan queue:table
php artisan migrate
```

Start queue worker:
```bash
php artisan queue:work --daemon
```

Or use supervisor/systemd to keep it running.

### 8.3 Set Up Log Rotation

Create `/etc/logrotate.d/upload-bridge`:

```
/var/www/upload-bridge/apps/web-dashboard/storage/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

## Step 9: Testing

### 9.1 Verify Application

1. Visit `https://yourdomain.com`
2. Check for SSL certificate (padlock icon)
3. Test login functionality
4. Test subscription flow
5. Verify email delivery

### 9.2 Check Logs

```bash
tail -f storage/logs/laravel.log
```

## Step 10: Monitoring

### 10.1 Set Up Error Tracking

Integrate error tracking service (Sentry, Rollbar, etc.)

### 10.2 Set Up Uptime Monitoring

Configure uptime monitoring service (UptimeRobot, Pingdom, etc.)

### 10.3 Set Up Backups

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for backup procedures.

## Rollback Procedures

If issues occur after deployment:

### 1. Revert Code

```bash
git checkout <previous-commit>
composer install --optimize-autoloader --no-dev
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

### 2. Restore Database

```bash
mysql -u upload_bridge_user -p upload_bridge < backup.sql
```

### 3. Restore .env

If `.env` was changed, restore from backup.

## Post-Deployment Checklist

- [ ] Application accessible via HTTPS
- [ ] SSL certificate valid
- [ ] All pages load correctly
- [ ] Login works
- [ ] Subscription flow works
- [ ] Email delivery works
- [ ] Stripe webhook works
- [ ] Error tracking configured
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] Logs rotating
- [ ] Admin password changed
- [ ] Test data removed (if any)

## Troubleshooting

### Application Not Loading

1. Check web server is running
2. Check PHP-FPM is running
3. Check file permissions
4. Check `.env` configuration
5. Check logs: `storage/logs/laravel.log`

### Database Connection Error

1. Verify database credentials in `.env`
2. Check database server is running
3. Check user has permissions
4. Check firewall rules

### SSL Certificate Issues

1. Verify certificate is valid
2. Check certificate chain is complete
3. Verify domain matches certificate
4. Check certificate hasn't expired

### Email Not Sending

1. Check SMTP credentials
2. Verify email service is accessible
3. Check firewall allows SMTP port
4. Review email service logs

## Support

For additional help, see:
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)
- [DATABASE_SETUP.md](DATABASE_SETUP.md)
- [STRIPE_SETUP.md](STRIPE_SETUP.md)
- [EMAIL_SETUP.md](EMAIL_SETUP.md)
- [SSL_SETUP.md](SSL_SETUP.md)
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
