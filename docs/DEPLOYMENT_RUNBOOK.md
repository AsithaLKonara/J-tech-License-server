# Deployment Runbook

This runbook provides step-by-step procedures for deploying the Upload Bridge web dashboard to production.

## Pre-Deployment Checklist

Before starting deployment, complete the pre-deployment check:

```bash
cd apps/web-dashboard
bash scripts/pre-deployment-check.sh
```

Resolve any errors before proceeding.

## Deployment Steps

### Step 1: Pre-Deployment Preparation

#### 1.1 Backup Current Deployment (if upgrading)

```bash
# Backup database
mysqldump -u username -p database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup application files
tar -czf backup_app_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/upload-bridge
```

#### 1.2 Verify Prerequisites

- [ ] Server has PHP 8.2+ installed
- [ ] Database server is running
- [ ] SSL certificate is valid
- [ ] Domain DNS is configured
- [ ] Stripe account is configured
- [ ] SMTP credentials are ready

### Step 2: Code Deployment

#### 2.1 Pull Latest Code

```bash
cd /var/www/upload-bridge
git fetch origin
git checkout main  # or your deployment branch
git pull origin main
```

#### 2.2 Install Dependencies

```bash
cd apps/web-dashboard
composer install --optimize-autoloader --no-dev
```

#### 2.3 Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/upload-bridge
sudo chmod -R 755 /var/www/upload-bridge
sudo chmod -R 775 storage bootstrap/cache
```

### Step 3: Environment Configuration

#### 3.1 Update .env File

```bash
# Copy production template if needed
cp .env.production.example .env

# Edit .env with production values
nano .env  # or use your preferred editor
```

**Required Variables:**
- `APP_ENV=production`
- `APP_DEBUG=false`
- `APP_URL=https://yourdomain.com`
- `APP_KEY` (generate if new deployment)
- Database credentials
- Stripe keys
- SMTP credentials

#### 3.2 Generate Application Key (if new deployment)

```bash
php artisan key:generate
```

#### 3.3 Secure .env File

```bash
chmod 600 .env
```

### Step 4: Database Operations

#### 4.1 Run Migrations

```bash
# Check migration status
php artisan migrate:status

# Run pending migrations
php artisan migrate --force
```

#### 4.2 Seed Database (if new deployment)

```bash
# Create admin user
php artisan db:seed --class=AdminUserSeeder

# Or seed test data (development only)
# php artisan db:seed --class=DatabaseSeeder
```

#### 4.3 Verify Database

```bash
php artisan tinker
>>> DB::connection()->getPdo();
>>> exit
```

### Step 5: Cache Optimization

#### 5.1 Clear Old Caches

```bash
php artisan config:clear
php artisan route:clear
php artisan view:clear
php artisan cache:clear
```

#### 5.2 Build Production Caches

```bash
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

### Step 6: Web Server Configuration

#### 6.1 Verify Web Server Configuration

**Apache:**
```bash
sudo apache2ctl configtest
```

**Nginx:**
```bash
sudo nginx -t
```

#### 6.2 Reload Web Server

**Apache:**
```bash
sudo systemctl reload apache2
```

**Nginx:**
```bash
sudo systemctl reload nginx
```

### Step 7: Post-Deployment Verification

#### 7.1 Health Check

```bash
curl -f https://yourdomain.com/api/v2/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 7.2 Smoke Tests

1. **Homepage loads:**
   ```bash
   curl -I https://yourdomain.com
   ```

2. **API endpoints respond:**
   ```bash
   curl https://yourdomain.com/api/v2/health
   ```

3. **SSL certificate is valid:**
   ```bash
   openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
   ```

#### 7.3 Functional Tests

- [ ] Login page loads
- [ ] User can register/login
- [ ] License validation works
- [ ] Device registration works
- [ ] Stripe checkout works (test mode)
- [ ] Email delivery works

### Step 8: Monitoring Setup

#### 8.1 Verify Error Tracking

- [ ] Sentry/Rollbar is configured
- [ ] Test error is logged

#### 8.2 Verify Uptime Monitoring

- [ ] UptimeRobot/Pingdom is configured
- [ ] Alerts are set up

## Rollback Procedure

If deployment fails, follow these steps:

### Step 1: Stop Web Server (if needed)

```bash
sudo systemctl stop apache2  # or nginx
```

### Step 2: Restore Code

```bash
cd /var/www/upload-bridge
git checkout <previous-commit-hash>
# or
git reset --hard <previous-tag>
```

### Step 3: Restore Database (if migrations were run)

```bash
mysql -u username -p database_name < backup_YYYYMMDD_HHMMSS.sql
```

### Step 4: Restore Application Files (if needed)

```bash
tar -xzf backup_app_YYYYMMDD_HHMMSS.tar.gz -C /
```

### Step 5: Clear Caches

```bash
cd apps/web-dashboard
php artisan config:clear
php artisan route:clear
php artisan view:clear
php artisan cache:clear
```

### Step 6: Restart Web Server

```bash
sudo systemctl start apache2  # or nginx
```

### Step 7: Verify Rollback

```bash
curl -f https://yourdomain.com/api/v2/health
```

## Troubleshooting

### Issue: Application won't boot

**Symptoms:**
- 500 Internal Server Error
- Blank page

**Solutions:**
1. Check Laravel logs: `tail -f storage/logs/laravel.log`
2. Verify `.env` file exists and is readable
3. Check file permissions: `ls -la storage bootstrap/cache`
4. Verify PHP version: `php -v`
5. Check web server error logs

### Issue: Database connection failed

**Symptoms:**
- "SQLSTATE[HY000] [2002] Connection refused"

**Solutions:**
1. Verify database server is running: `sudo systemctl status mysql`
2. Check database credentials in `.env`
3. Test connection: `mysql -u username -p -h host database`
4. Verify firewall allows database port

### Issue: Migrations fail

**Symptoms:**
- "Migration failed" error

**Solutions:**
1. Check migration status: `php artisan migrate:status`
2. Review migration files for errors
3. Check database permissions
4. Verify database exists

### Issue: Cache issues

**Symptoms:**
- Old configuration persists
- Routes not updating

**Solutions:**
1. Clear all caches: `php artisan optimize:clear`
2. Rebuild caches: `php artisan optimize`
3. Check cache driver in `.env`
4. Verify Redis is running (if using Redis)

### Issue: SSL certificate errors

**Symptoms:**
- Browser shows "Not Secure"
- Certificate expired warning

**Solutions:**
1. Check certificate expiry: `openssl x509 -in cert.pem -noout -dates`
2. Renew certificate (Let's Encrypt): `sudo certbot renew`
3. Verify web server configuration
4. Check certificate path in web server config

### Issue: Email not sending

**Symptoms:**
- Emails not received
- SMTP errors in logs

**Solutions:**
1. Verify SMTP credentials in `.env`
2. Test SMTP connection: `telnet smtp.host 587`
3. Check firewall allows SMTP port
4. Review mail logs: `tail -f storage/logs/laravel.log`
5. Test email sending: `php artisan tinker` → `Mail::raw(...)`

## Maintenance Procedures

### Daily

- [ ] Check application logs for errors
- [ ] Verify uptime monitoring status
- [ ] Review error tracking dashboard

### Weekly

- [ ] Review database size and performance
- [ ] Check disk space usage
- [ ] Review security logs
- [ ] Update dependencies (if needed)

### Monthly

- [ ] Review and rotate secrets
- [ ] Update SSL certificates (if needed)
- [ ] Review and optimize database
- [ ] Review performance metrics
- [ ] Update application dependencies

## Emergency Contacts

- **System Administrator:** [contact info]
- **Database Administrator:** [contact info]
- **Stripe Support:** [contact info]
- **Hosting Provider:** [contact info]

## Additional Resources

- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Detailed deployment guide
- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) - Operations procedures
- [SSL_SETUP.md](SSL_SETUP.md) - SSL certificate setup
- [STRIPE_SETUP.md](STRIPE_SETUP.md) - Stripe configuration
- [EMAIL_SETUP.md](EMAIL_SETUP.md) - Email configuration
