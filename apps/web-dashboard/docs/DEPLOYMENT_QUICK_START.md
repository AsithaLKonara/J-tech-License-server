# Deployment Quick Start Guide

Quick reference for deploying Upload Bridge to production.

## Prerequisites

- PHP 8.2+, MySQL/PostgreSQL, Web Server (Apache/Nginx)
- SSL certificate, Domain name, Stripe account, SMTP service

## Quick Deployment Steps

### 1. Pre-Deployment Check

```bash
cd apps/web-dashboard
bash scripts/pre-deployment-check.sh
```

### 2. Deploy Code

```bash
cd /var/www/upload-bridge
git pull origin main
cd apps/web-dashboard
composer install --optimize-autoloader --no-dev
```

### 3. Configure Environment

```bash
cp .env.production.example .env
nano .env  # Edit with production values
php artisan key:generate
chmod 600 .env
```

### 4. Database Setup

```bash
php artisan migrate --force
php artisan db:seed --class=AdminUserSeeder
```

### 5. Optimize

```bash
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

### 6. Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/upload-bridge
sudo chmod -R 775 storage bootstrap/cache
```

### 7. Reload Web Server

```bash
# Apache
sudo systemctl reload apache2

# Nginx
sudo systemctl reload nginx
```

### 8. Verify

```bash
curl -f https://yourdomain.com/api/v2/health
```

## Common Commands

### Clear Caches

```bash
php artisan optimize:clear
```

### Rebuild Caches

```bash
php artisan optimize
```

### Check Migration Status

```bash
php artisan migrate:status
```

### View Logs

```bash
tail -f storage/logs/laravel.log
```

### Test Database Connection

```bash
php artisan tinker
>>> DB::connection()->getPdo();
```

## Quick Troubleshooting

### 500 Error

```bash
# Check logs
tail -f storage/logs/laravel.log

# Clear caches
php artisan optimize:clear

# Check permissions
ls -la storage bootstrap/cache
```

### Database Error

```bash
# Test connection
php artisan db:show

# Check credentials in .env
grep DB_ .env
```

### Cache Issues

```bash
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
```

## Rollback

```bash
cd /var/www/upload-bridge
git checkout <previous-commit>
cd apps/web-dashboard
php artisan optimize:clear
sudo systemctl reload apache2  # or nginx
```

## Emergency Contacts

- System Admin: [contact]
- Database Admin: [contact]
- Hosting Provider: [contact]

## Platform-Specific Guides

- [Railway Deployment](RAILWAY_DEPLOYMENT.md) - Deploy on Railway (Recommended)
- [Vercel Deployment](VERCEL_DEPLOYMENT.md) - Vercel considerations (Not recommended)

## Full Documentation

- [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md) - Detailed procedures
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Complete guide
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) - Operations procedures
