# Shared Hosting Deployment Guide

**Upload Bridge Web Dashboard**  
**Version**: 3.0.0  
**Last Updated**: 2025-01-27

---

## Overview

This guide covers deploying the Upload Bridge Web Dashboard on shared hosting. The application is designed to be lightweight and compatible with standard shared hosting environments.

---

## Prerequisites

### Hosting Requirements

- **PHP**: 8.1 or higher
- **Database**: MySQL 5.7+ or MariaDB 10.3+
- **Web Server**: Apache with mod_rewrite enabled (or Nginx)
- **Disk Space**: Minimum 100MB (500MB recommended)
- **Memory**: PHP memory_limit of at least 128MB (256MB recommended)

### Required PHP Extensions

- `pdo_mysql` - Database connectivity
- `mbstring` - String handling
- `openssl` - Encryption
- `json` - JSON processing
- `curl` - HTTP requests (for Stripe)
- `fileinfo` - File type detection
- `zip` - Archive handling

### Optional Extensions

- `redis` - For caching (if using Redis)
- `imagick` - For image processing (if needed)

---

## Step 1: Upload Files

### 1.1 File Structure

Upload all files to your hosting account. The structure should be:

```
public_html/
├── public/          # Document root (set this in hosting control panel)
│   ├── index.php
│   └── ...
├── app/
├── bootstrap/
├── config/
├── database/
├── resources/
├── routes/
├── storage/
├── vendor/
├── .env
├── artisan
└── composer.json
```

### 1.2 Set Document Root

**Important**: Set your hosting's document root to the `public/` directory, NOT the root directory.

**cPanel:**
1. Go to "Subdomains" or "Addon Domains"
2. Set document root to `public_html/public` or `public_html/yourdomain/public`

**Other Hosting:**
- Check your hosting control panel for "Document Root" or "Web Root" settings
- Point it to the `public/` directory

---

## Step 2: Database Setup

### 2.1 Create Database

1. Log into your hosting control panel (cPanel, Plesk, etc.)
2. Go to "MySQL Databases" or "Database Management"
3. Create a new database (e.g., `upload_bridge_db`)
4. Create a database user
5. Grant all privileges to the user on the database
6. Note down:
   - Database name
   - Database username
   - Database password
   - Database host (usually `localhost`)

### 2.2 Import Schema (Optional)

If you have access to phpMyAdmin or command line:

1. Open phpMyAdmin
2. Select your database
3. Go to "Import" tab
4. Upload `database/schema.sql` (if you have it)
5. Or run migrations via command line (see Step 4)

---

## Step 3: Environment Configuration

### 3.1 Create .env File

1. Copy `.env.example` to `.env` (if available)
2. Or create a new `.env` file in the root directory

### 3.2 Configure .env File

Edit `.env` with your production values:

```env
APP_NAME="Upload Bridge Dashboard"
APP_ENV=production
APP_KEY=base64:your_generated_key_here
APP_DEBUG=false
APP_URL=https://yourdomain.com

# Database Configuration
DB_CONNECTION=mysql
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=your_database_name
DB_USERNAME=your_database_user
DB_PASSWORD=your_database_password

# License Server URL (your own domain)
LICENSE_SERVER_URL=https://yourdomain.com

# Mail/SMTP Configuration
MAIL_MAILER=smtp
MAIL_HOST=smtp.yourhost.com
MAIL_PORT=587
MAIL_USERNAME=your_smtp_username
MAIL_PASSWORD=your_smtp_password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="${APP_NAME}"

# Stripe Configuration
STRIPE_KEY=pk_live_your_stripe_publishable_key
STRIPE_SECRET=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_MONTHLY=price_monthly_id
STRIPE_PRICE_ANNUAL=price_annual_id
STRIPE_PRICE_LIFETIME=price_lifetime_id

# Session Configuration
SESSION_DRIVER=file
SESSION_LIFETIME=120

# Cache Configuration
CACHE_DRIVER=file
```

### 3.3 Generate Application Key

If you have SSH access:

```bash
php artisan key:generate
```

If you don't have SSH access:
1. Use an online Laravel key generator
2. Or contact support for assistance
3. Set `APP_KEY` in `.env` file

---

## Step 4: Run Migrations

### 4.1 Via SSH (If Available)

```bash
cd /path/to/your/application
php artisan migrate --force
```

### 4.2 Via phpMyAdmin

1. Open phpMyAdmin
2. Select your database
3. Go to "SQL" tab
4. Copy contents of each migration file from `database/migrations/`
5. Run them in order (by date prefix)

### 4.3 Via Hosting Control Panel

Some hosting providers offer "Run PHP Script" or similar features. Create a temporary file:

```php
<?php
require __DIR__.'/vendor/autoload.php';
$app = require_once __DIR__.'/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->call('migrate', ['--force' => true]);
echo "Migrations completed!";
```

**Important**: Delete this file after running migrations!

---

## Step 5: File Permissions

### 5.1 Set Permissions

Set the following permissions (via FTP or File Manager):

- `storage/` - 755 (or 775 if needed)
- `storage/framework/` - 755
- `storage/framework/cache/` - 755
- `storage/framework/sessions/` - 755
- `storage/framework/views/` - 755
- `storage/logs/` - 755
- `bootstrap/cache/` - 755

**Via cPanel File Manager:**
1. Right-click folder → "Change Permissions"
2. Set to 755 (or 775)

**Via SSH:**
```bash
chmod -R 755 storage bootstrap/cache
```

### 5.2 Verify Writable

Ensure `storage/` and `bootstrap/cache/` are writable by the web server.

---

## Step 6: SMTP Configuration

### 6.1 Get SMTP Credentials

Most shared hosting providers offer SMTP. Common options:

- **cPanel Email**: Use your hosting's email server
- **Third-party**: Gmail, SendGrid, Mailgun, etc.

### 6.2 Configure in .env

```env
MAIL_MAILER=smtp
MAIL_HOST=smtp.yourhost.com
MAIL_PORT=587
MAIL_USERNAME=your_email@yourdomain.com
MAIL_PASSWORD=your_email_password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge Dashboard"
```

### 6.3 Test Email

Create a test script (delete after testing):

```php
<?php
require __DIR__.'/vendor/autoload.php';
$app = require_once __DIR__.'/bootstrap/app.php';

use Illuminate\Support\Facades\Mail;

Mail::raw('Test email', function($message) {
    $message->to('your@email.com')
            ->subject('Test Email');
});

echo "Email sent!";
```

---

## Step 7: Stripe Configuration

### 7.1 Get Stripe Keys

1. Log into Stripe Dashboard
2. Go to "Developers" → "API keys"
3. Copy your Live keys (not test keys for production)
4. Set up webhook endpoint (see Step 8)

### 7.2 Configure in .env

```env
STRIPE_KEY=pk_live_...
STRIPE_SECRET=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_ANNUAL=price_...
STRIPE_PRICE_LIFETIME=price_...
```

---

## Step 8: Stripe Webhook Setup

### 8.1 Create Webhook Endpoint

1. In Stripe Dashboard, go to "Developers" → "Webhooks"
2. Click "Add endpoint"
3. Endpoint URL: `https://yourdomain.com/webhook/stripe`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the webhook signing secret
6. Add to `.env` as `STRIPE_WEBHOOK_SECRET`

---

## Step 9: Testing Deployment

### 9.1 Health Check

Visit: `https://yourdomain.com/api/v2/health`

Should return:
```json
{
  "status": "ok",
  "timestamp": "...",
  "version": "2.0"
}
```

### 9.2 Test Registration

1. Visit: `https://yourdomain.com/register`
2. Create a test account
3. Verify email (if email verification enabled)

### 9.3 Test Login

1. Visit: `https://yourdomain.com/login`
2. Login with test account
3. Verify dashboard loads

### 9.4 Test API

```bash
curl -X POST https://yourdomain.com/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password","device_id":"TEST"}'
```

---

## Step 10: Security Configuration

### 10.1 Hide .env File

Ensure `.env` is not publicly accessible. It should be in `.gitignore` and not in `public/`.

### 10.2 Enable HTTPS

1. Install SSL certificate (Let's Encrypt is free)
2. Force HTTPS in `.env`:
   ```env
   APP_URL=https://yourdomain.com
   ```
3. Update `config/app.php` if needed to force HTTPS

### 10.3 Set Secure Cookies

In `config/session.php`, ensure:
```php
'secure' => env('SESSION_SECURE_COOKIE', true),
'http_only' => true,
'same_site' => 'lax',
```

---

## Troubleshooting

### Issue: 500 Internal Server Error

**Solutions:**
1. Check `storage/logs/laravel.log` for errors
2. Verify file permissions (Step 5)
3. Check `.env` file exists and is configured
4. Verify `APP_KEY` is set
5. Check PHP version (must be 8.1+)
6. Check PHP extensions are installed

### Issue: Database Connection Error

**Solutions:**
1. Verify database credentials in `.env`
2. Check database host (try `127.0.0.1` instead of `localhost`)
3. Verify database user has permissions
4. Check database exists

### Issue: Migration Errors

**Solutions:**
1. Check database user has CREATE TABLE permissions
2. Verify all migrations are present
3. Check for conflicting table names
4. Try running migrations one at a time

### Issue: Email Not Sending

**Solutions:**
1. Verify SMTP credentials
2. Check firewall allows outbound SMTP (port 587/465)
3. Test with a simple PHP mail script
4. Check spam folder
5. Verify `MAIL_FROM_ADDRESS` is valid

### Issue: API Returns 404

**Solutions:**
1. Verify document root is set to `public/`
2. Check `.htaccess` file exists in `public/`
3. Verify mod_rewrite is enabled
4. Check `routes/api.php` exists

### Issue: Storage Not Writable

**Solutions:**
1. Set permissions: `chmod -R 755 storage`
2. Check ownership (should be web server user)
3. Verify disk space available
4. Check `storage/` directory exists

---

## Performance Optimization

### Enable Caching

```bash
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

### Optimize Autoloader

```bash
composer install --optimize-autoloader --no-dev
```

### Use Redis (If Available)

Update `.env`:
```env
CACHE_DRIVER=redis
SESSION_DRIVER=redis
QUEUE_CONNECTION=redis
```

---

## Maintenance

### Clear Cache

```bash
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
```

### View Logs

Check `storage/logs/laravel.log` for errors and debugging information.

### Backup Database

Regularly backup your database via:
- cPanel → phpMyAdmin → Export
- Hosting backup tools
- Automated backup scripts

---

## Support

For deployment assistance:
- Check Laravel documentation: https://laravel.com/docs
- Review hosting provider documentation
- Contact support with specific error messages

---

**Last Updated**: 2025-01-27
