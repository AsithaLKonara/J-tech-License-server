# Railway Deployment Guide

Complete guide to deploy the Upload Bridge license system on Railway.

## Overview

Railway is an excellent platform for Laravel applications with:
- ✅ One-click deployment
- ✅ Automatic database provisioning
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Simple environment management

## Prerequisites

1. **Railway Account**: [Sign up](https://railway.app) (free tier available)
2. **GitHub Account**: For connecting your repository
3. **Stripe Account**: For payment processing
4. **SMTP Service**: For email delivery (Mailgun, SendGrid, etc.)

## Quick Start

### Option 1: Deploy from GitHub (Recommended)

1. **Connect Repository**
   - Go to [Railway Dashboard](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select `apps/web-dashboard` as the root directory

2. **Add Database**
   - Click "New" → "Database" → "Add PostgreSQL" (or MySQL)
   - Railway will automatically set `DATABASE_URL` environment variable

3. **Set Environment Variables**
   - Go to your service → "Variables"
   - Add all required variables (see below)

4. **Deploy**
   - Railway will automatically detect Laravel and deploy
   - First deployment may take 5-10 minutes

### Option 2: Deploy via CLI

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
cd apps/web-dashboard
railway init

# 4. Link to existing project (or create new)
railway link

# 5. Add PostgreSQL database
railway add postgresql

# 6. Set environment variables
railway variables set APP_ENV=production
railway variables set APP_DEBUG=false
railway variables set APP_URL=https://your-app.railway.app
# ... (see environment variables section)

# 7. Deploy
railway up
```

## Required Environment Variables

Set these in Railway Dashboard → Your Service → Variables:

### Application Configuration

```env
APP_NAME="Upload Bridge"
APP_ENV=production
APP_DEBUG=false
APP_KEY=                    # Will be generated automatically
APP_URL=https://your-app.railway.app
```

### Database Configuration

Railway automatically provides `DATABASE_URL`. Laravel will use it automatically.

**Optional:** If you need to override:
```env
DB_CONNECTION=pgsql
DB_HOST=your-db-host.railway.app
DB_PORT=5432
DB_DATABASE=railway
DB_USERNAME=postgres
DB_PASSWORD=your-password
```

### Cache Configuration

```env
CACHE_DRIVER=file            # Use 'redis' if you add Redis service
SESSION_DRIVER=database      # Recommended for production
```

### Mail Configuration

```env
MAIL_MAILER=smtp
MAIL_HOST=smtp.mailgun.org   # Or your SMTP provider
MAIL_PORT=587
MAIL_USERNAME=your-username
MAIL_PASSWORD=your-password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge"
```

### Stripe Configuration

```env
STRIPE_KEY=pk_live_...
STRIPE_SECRET=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_ANNUAL=price_...
STRIPE_PRICE_LIFETIME=price_...
```

### Admin User (for initial setup)

```env
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_NAME="Administrator"
ADMIN_PASSWORD=strong-password-here
```

### Optional: Redis (for better performance)

If you add Redis service:
```env
REDIS_HOST=your-redis-host.railway.app
REDIS_PASSWORD=your-redis-password
REDIS_PORT=6379
REDIS_DB=0
REDIS_CACHE_DB=1
CACHE_DRIVER=redis
SESSION_DRIVER=redis
```

## Deployment Steps

### Step 1: Initial Setup

1. **Create Railway Project**
   - Go to Railway Dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Service**
   - Set root directory to `apps/web-dashboard`
   - Railway will auto-detect Laravel

3. **Add Database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway creates database and sets `DATABASE_URL`

### Step 2: Configure Environment

1. **Set Environment Variables**
   - Go to your service → "Variables" tab
   - Add all required variables (see above)
   - **Important**: Set `APP_URL` to your Railway domain

2. **Generate Application Key**
   - Railway will auto-generate on first deploy
   - Or set manually: `APP_KEY=base64:...`
   - Generate locally: `php artisan key:generate`

### Step 3: Configure Build

Railway auto-detects Laravel, but you can customize:

**Build Command:**
```bash
composer install --optimize-autoloader --no-dev
```

**Start Command:**
```bash
php artisan serve --host=0.0.0.0 --port=$PORT
```

**Or use Nginx (recommended for production):**

Create `Procfile`:
```
web: vendor/bin/heroku-php-nginx -C nginx.conf public/
```

### Step 4: Run Migrations

**Option 1: Automatic (Recommended)**

Add to Railway build/start command or use Railway's post-deploy hook.

**Option 2: Manual via Railway CLI**

```bash
railway run php artisan migrate --force
```

**Option 3: Via Railway Dashboard**

- Go to your service
- Click "Deployments" → "View Logs"
- Use "Run Command" feature

### Step 5: Create Admin User

After first deployment:

```bash
railway run php artisan db:seed --class=AdminUserSeeder
```

Or set environment variables and run:
```bash
railway run php artisan tinker
>>> \App\Models\User::create([...])
```

### Step 6: Configure Custom Domain (Optional)

1. Go to your service → "Settings" → "Domains"
2. Click "Generate Domain" or "Add Custom Domain"
3. Update `APP_URL` environment variable
4. Configure DNS as instructed

## Post-Deployment

### 1. Verify Deployment

```bash
# Health check
curl https://your-app.railway.app/api/v2/health

# Should return:
# {"status":"ok","timestamp":"..."}
```

### 2. Test Authentication

```bash
curl -X POST https://your-app.railway.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "device_id": "TEST_DEVICE",
    "device_name": "Test Device"
  }'
```

### 3. Configure Stripe Webhook

1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-app.railway.app/webhook/stripe`
3. Select events to send
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

### 4. Test Email Delivery

```bash
railway run php artisan tinker
>>> Mail::raw('Test email', function($message) {
...     $message->to('your@email.com')->subject('Test');
... });
```

## Railway-Specific Configuration

### Nginx Configuration (Optional)

Create `nginx.conf` in `apps/web-dashboard/`:

```nginx
location / {
    try_files $uri $uri/ /index.php?$query_string;
}

location ~ \.php$ {
    fastcgi_pass 127.0.0.1:9000;
    fastcgi_index index.php;
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
}
```

### Procfile

Create `Procfile` in `apps/web-dashboard/`:

```
web: vendor/bin/heroku-php-nginx -C nginx.conf public/
```

Or for Apache:
```
web: vendor/bin/heroku-php-apache2 public/
```

### Buildpacks

Railway auto-detects PHP, but you can specify:

Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "php artisan serve --host=0.0.0.0 --port=$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Monitoring & Logs

### View Logs

**Via Dashboard:**
- Go to your service → "Deployments" → Click deployment → "View Logs"

**Via CLI:**
```bash
railway logs
```

### Monitor Metrics

- Railway Dashboard shows:
  - CPU usage
  - Memory usage
  - Network traffic
  - Request count

### Set Up Alerts

1. Go to your service → "Settings" → "Alerts"
2. Configure alerts for:
   - High CPU usage
   - High memory usage
   - Deployment failures

## Troubleshooting

### Deployment Fails

**Check logs:**
```bash
railway logs
```

**Common issues:**
1. **Missing environment variables**: Check all required vars are set
2. **Database connection**: Verify `DATABASE_URL` is set
3. **Build errors**: Check Composer dependencies
4. **Migration errors**: Run migrations manually

### Application Won't Start

**Check:**
1. Application logs: `railway logs`
2. Environment variables are set correctly
3. Database is accessible
4. Port is set correctly (`$PORT`)

### Database Connection Issues

**Verify:**
1. `DATABASE_URL` is set automatically by Railway
2. Database service is running
3. Network access is allowed

**Test connection:**
```bash
railway run php artisan tinker
>>> DB::connection()->getPdo();
```

### Migration Issues

**Run manually:**
```bash
railway run php artisan migrate:status
railway run php artisan migrate --force
```

### Cache Issues

**Clear cache:**
```bash
railway run php artisan cache:clear
railway run php artisan config:clear
railway run php artisan route:clear
railway run php artisan view:clear
```

## Scaling

### Horizontal Scaling

Railway supports multiple instances:
1. Go to service → "Settings" → "Scaling"
2. Set number of instances
3. Railway handles load balancing

### Vertical Scaling

Upgrade plan for more resources:
1. Go to "Settings" → "Billing"
2. Upgrade to Pro plan for:
   - More CPU
   - More RAM
   - Better performance

## Cost Optimization

### Free Tier Limits

- 500 hours/month compute time
- 5GB data transfer
- 1GB database storage

### Pro Plan ($20/month)

- Unlimited compute time
- 100GB data transfer
- 5GB database storage
- Better performance

### Tips to Reduce Costs

1. Use file-based cache (not Redis) on free tier
2. Optimize database queries
3. Use CDN for static assets
4. Monitor resource usage

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` to Git
   - Use Railway's secret management
   - Rotate secrets regularly

2. **HTTPS**
   - Railway provides automatic HTTPS
   - Use custom domain with SSL

3. **Database**
   - Use strong passwords
   - Restrict network access
   - Regular backups

4. **Application**
   - Set `APP_DEBUG=false` in production
   - Use secure session cookies
   - Enable rate limiting

## Backup & Recovery

### Database Backups

Railway provides automatic backups:
1. Go to database service → "Backups"
2. Configure backup schedule
3. Download backups as needed

### Manual Backup

```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

### Restore Backup

```bash
railway run psql $DATABASE_URL < backup.sql
```

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Laravel on Railway](https://docs.railway.app/guides/laravel)
- [Railway Discord](https://discord.gg/railway)

## Support

For Railway-specific issues:
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Support: support@railway.app

For application issues:
- See [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)
- See [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
