# Environment Setup Documentation

This document provides comprehensive information about all environment variables required for the Upload Bridge web dashboard.

## Overview

The application uses environment variables stored in a `.env` file for configuration. Never commit the `.env` file to version control.

## Creating .env File

Copy the example file:
```bash
cp .env.example .env
```

Generate application key:
```bash
php artisan key:generate
```

Secure the file:
```bash
chmod 600 .env
```

## Required Environment Variables

### Application Configuration

#### APP_NAME
- **Description**: Application name
- **Required**: Yes
- **Default**: `Upload Bridge`
- **Example**: `APP_NAME="Upload Bridge"`

#### APP_ENV
- **Description**: Application environment
- **Required**: Yes
- **Values**: `local`, `staging`, `production`
- **Production**: `APP_ENV=production`
- **Example**: `APP_ENV=production`

#### APP_KEY
- **Description**: Application encryption key
- **Required**: Yes
- **Generated**: Run `php artisan key:generate`
- **Example**: `APP_KEY=base64:xxxxxxxxxxxxx`

#### APP_DEBUG
- **Description**: Enable debug mode
- **Required**: Yes
- **Production**: `false`
- **Development**: `true`
- **Example**: `APP_DEBUG=false`

#### APP_URL
- **Description**: Application URL
- **Required**: Yes
- **Production**: Full HTTPS URL
- **Example**: `APP_URL=https://yourdomain.com`

#### ASSET_URL
- **Description**: Asset URL (for CDN)
- **Required**: No
- **Example**: `ASSET_URL=https://cdn.yourdomain.com`

## Database Configuration

### DB_CONNECTION
- **Description**: Database driver
- **Required**: Yes
- **Values**: `mysql`, `pgsql`, `sqlite`
- **Production**: `mysql` or `pgsql`
- **Example**: `DB_CONNECTION=mysql`

### MySQL Configuration

#### DB_HOST
- **Description**: Database host
- **Required**: Yes (for MySQL/PostgreSQL)
- **Default**: `127.0.0.1`
- **Example**: `DB_HOST=127.0.0.1`

#### DB_PORT
- **Description**: Database port
- **Required**: No
- **MySQL Default**: `3306`
- **PostgreSQL Default**: `5432`
- **Example**: `DB_PORT=3306`

#### DB_DATABASE
- **Description**: Database name
- **Required**: Yes (for MySQL/PostgreSQL)
- **Example**: `DB_DATABASE=upload_bridge`

#### DB_USERNAME
- **Description**: Database username
- **Required**: Yes (for MySQL/PostgreSQL)
- **Example**: `DB_USERNAME=upload_bridge_user`

#### DB_PASSWORD
- **Description**: Database password
- **Required**: Yes (for MySQL/PostgreSQL)
- **Example**: `DB_PASSWORD=strong_password_here`

#### DB_SOCKET
- **Description**: Database socket path
- **Required**: No
- **Example**: `DB_SOCKET=/var/run/mysqld/mysqld.sock`

#### MYSQL_ATTR_SSL_CA
- **Description**: MySQL SSL CA certificate path
- **Required**: No
- **Example**: `MYSQL_ATTR_SSL_CA=/path/to/ca.pem`

### SQLite Configuration

For development only:
```
DB_CONNECTION=sqlite
DB_DATABASE=/absolute/path/to/database.sqlite
```

## Redis Configuration (Optional)

### REDIS_CLIENT
- **Description**: Redis client
- **Required**: No
- **Default**: `phpredis`
- **Example**: `REDIS_CLIENT=phpredis`

### REDIS_HOST
- **Description**: Redis host
- **Required**: No
- **Default**: `127.0.0.1`
- **Example**: `REDIS_HOST=127.0.0.1`

### REDIS_PORT
- **Description**: Redis port
- **Required**: No
- **Default**: `6379`
- **Example**: `REDIS_PORT=6379`

### REDIS_PASSWORD
- **Description**: Redis password
- **Required**: No
- **Example**: `REDIS_PASSWORD=redis_password`

### REDIS_DB
- **Description**: Redis database number
- **Required**: No
- **Default**: `0`
- **Example**: `REDIS_DB=0`

### REDIS_CACHE_DB
- **Description**: Redis cache database number
- **Required**: No
- **Default**: `1`
- **Example**: `REDIS_CACHE_DB=1`

## Cache Configuration

### CACHE_DRIVER
- **Description**: Cache storage driver
- **Required**: No
- **Values**: `file`, `database`, `redis`, `memcached`, `array`
- **Default**: `file`
- **Production**: `redis` (recommended for performance)
- **Development**: `file` or `array`
- **Example**: `CACHE_DRIVER=redis`

### CACHE_PREFIX
- **Description**: Cache key prefix
- **Required**: No
- **Default**: Auto-generated from APP_NAME
- **Example**: `CACHE_PREFIX=upload_bridge_cache_`

**Note**: When using Redis for caching, ensure Redis is installed and running. See [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) for details.

## Session Configuration

### SESSION_DRIVER
- **Description**: Session storage driver
- **Required**: No
- **Values**: `file`, `database`, `redis`, `memcached`
- **Default**: `file`
- **Production**: `database` or `redis`
- **Example**: `SESSION_DRIVER=file`

### SESSION_LIFETIME
- **Description**: Session lifetime in minutes
- **Required**: No
- **Default**: `120`
- **Example**: `SESSION_LIFETIME=120`

### SESSION_SECURE_COOKIE
- **Description**: Enable secure cookies (HTTPS only)
- **Required**: No
- **Production**: `true`
- **Default**: `false`
- **Example**: `SESSION_SECURE_COOKIE=true`

### SESSION_DOMAIN
- **Description**: Session cookie domain
- **Required**: No
- **Example**: `SESSION_DOMAIN=.yourdomain.com`

## Mail Configuration

### MAIL_MAILER
- **Description**: Mail driver
- **Required**: No
- **Values**: `smtp`, `sendmail`, `mailgun`, `ses`, `postmark`
- **Default**: `smtp`
- **Example**: `MAIL_MAILER=smtp`

### MAIL_HOST
- **Description**: SMTP host
- **Required**: Yes (for SMTP)
- **Example**: `MAIL_HOST=smtp.mailgun.org`

### MAIL_PORT
- **Description**: SMTP port
- **Required**: Yes (for SMTP)
- **Values**: `587` (TLS), `465` (SSL), `25`
- **Example**: `MAIL_PORT=587`

### MAIL_USERNAME
- **Description**: SMTP username
- **Required**: Yes (for SMTP)
- **Example**: `MAIL_USERNAME=postmaster@mg.yourdomain.com`

### MAIL_PASSWORD
- **Description**: SMTP password
- **Required**: Yes (for SMTP)
- **Example**: `MAIL_PASSWORD=your_smtp_password`

### MAIL_ENCRYPTION
- **Description**: SMTP encryption
- **Required**: Yes (for SMTP)
- **Values**: `tls`, `ssl`
- **Example**: `MAIL_ENCRYPTION=tls`

### MAIL_FROM_ADDRESS
- **Description**: Email sender address
- **Required**: No
- **Default**: `hello@example.com`
- **Example**: `MAIL_FROM_ADDRESS=noreply@yourdomain.com`

### MAIL_FROM_NAME
- **Description**: Email sender name
- **Required**: No
- **Default**: `Example`
- **Example**: `MAIL_FROM_NAME="Upload Bridge"`

### MAIL_EHLO_DOMAIN
- **Description**: SMTP EHLO domain
- **Required**: No
- **Example**: `MAIL_EHLO_DOMAIN=yourdomain.com`

## Stripe Configuration

### STRIPE_KEY
- **Description**: Stripe publishable key
- **Required**: Yes (for payments)
- **Test**: `pk_test_...`
- **Production**: `pk_live_...`
- **Example**: `STRIPE_KEY=pk_live_your_key`

### STRIPE_SECRET
- **Description**: Stripe secret key
- **Required**: Yes (for payments)
- **Test**: `sk_test_...`
- **Production**: `sk_live_...`
- **Example**: `STRIPE_SECRET=sk_live_your_secret`

### STRIPE_WEBHOOK_SECRET
- **Description**: Stripe webhook signing secret
- **Required**: Yes (for webhooks)
- **Format**: `whsec_...`
- **Example**: `STRIPE_WEBHOOK_SECRET=whsec_your_secret`

### STRIPE_PRICE_MONTHLY
- **Description**: Stripe price ID for monthly plan
- **Required**: Yes (for subscriptions)
- **Format**: `price_...`
- **Example**: `STRIPE_PRICE_MONTHLY=price_monthly_id`

### STRIPE_PRICE_ANNUAL
- **Description**: Stripe price ID for annual plan
- **Required**: Yes (for subscriptions)
- **Format**: `price_...`
- **Example**: `STRIPE_PRICE_ANNUAL=price_annual_id`

### STRIPE_PRICE_LIFETIME
- **Description**: Stripe price ID for lifetime plan
- **Required**: Yes (for subscriptions)
- **Format**: `price_...`
- **Example**: `STRIPE_PRICE_LIFETIME=price_lifetime_id`

## Logging Configuration

### LOG_CHANNEL
- **Description**: Default log channel
- **Required**: No
- **Values**: `stack`, `single`, `daily`, `slack`, `syslog`
- **Default**: `stack`
- **Example**: `LOG_CHANNEL=stack`

### LOG_LEVEL
- **Description**: Log level
- **Required**: No
- **Values**: `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`
- **Production**: `error`
- **Development**: `debug`
- **Example**: `LOG_LEVEL=error`

### LOG_SLACK_WEBHOOK_URL
- **Description**: Slack webhook URL for logging
- **Required**: No
- **Example**: `LOG_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`

## Filesystem Configuration

### FILESYSTEM_DISK
- **Description**: Default filesystem disk
- **Required**: No
- **Values**: `local`, `public`, `s3`
- **Default**: `local`
- **Example**: `FILESYSTEM_DISK=local`

## Admin User Seeder Configuration

### ADMIN_EMAIL
- **Description**: Admin user email
- **Required**: No (for AdminUserSeeder)
- **Default**: `admin@example.com`
- **Example**: `ADMIN_EMAIL=admin@yourdomain.com`

### ADMIN_NAME
- **Description**: Admin user name
- **Required**: No (for AdminUserSeeder)
- **Default**: `Administrator`
- **Example**: `ADMIN_NAME="Administrator"`

### ADMIN_PASSWORD
- **Description**: Admin user password
- **Required**: No (for AdminUserSeeder)
- **Default**: `changeme`
- **Example**: `ADMIN_PASSWORD=strong_password_here`

**IMPORTANT**: Change admin password immediately after first login!

## License Server Configuration

### LICENSE_SERVER_URL
- **Description**: License server URL (for desktop app)
- **Required**: No
- **Default**: Same as `APP_URL`
- **Example**: `LICENSE_SERVER_URL=https://yourdomain.com`

## Configuration Examples

### Production Configuration

```env
APP_NAME="Upload Bridge"
APP_ENV=production
APP_DEBUG=false
APP_URL=https://yourdomain.com
APP_KEY=base64:xxxxxxxxxxxxx

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge
DB_USERNAME=upload_bridge_user
DB_PASSWORD=strong_password_here

SESSION_DRIVER=database
SESSION_SECURE_COOKIE=true

MAIL_MAILER=smtp
MAIL_HOST=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=postmaster@mg.yourdomain.com
MAIL_PASSWORD=your_smtp_password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge"

STRIPE_KEY=pk_live_your_key
STRIPE_SECRET=sk_live_your_secret
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_PRICE_MONTHLY=price_monthly_id
STRIPE_PRICE_ANNUAL=price_annual_id
STRIPE_PRICE_LIFETIME=price_lifetime_id

LOG_CHANNEL=daily
LOG_LEVEL=error

ADMIN_EMAIL=admin@yourdomain.com
ADMIN_NAME="Administrator"
ADMIN_PASSWORD=strong_password_here
```

### Development Configuration

```env
APP_NAME="Upload Bridge"
APP_ENV=local
APP_DEBUG=true
APP_URL=http://localhost:8000
APP_KEY=base64:xxxxxxxxxxxxx

DB_CONNECTION=sqlite
DB_DATABASE=/absolute/path/to/database.sqlite

SESSION_DRIVER=file
SESSION_SECURE_COOKIE=false

MAIL_MAILER=smtp
MAIL_HOST=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=test
MAIL_PASSWORD=test
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=test@example.com
MAIL_FROM_NAME="Upload Bridge"

STRIPE_KEY=pk_test_your_key
STRIPE_SECRET=sk_test_your_secret
STRIPE_WEBHOOK_SECRET=whsec_test_secret
STRIPE_PRICE_MONTHLY=price_test_monthly
STRIPE_PRICE_ANNUAL=price_test_annual
STRIPE_PRICE_LIFETIME=price_test_lifetime

LOG_CHANNEL=stack
LOG_LEVEL=debug
```

## Troubleshooting

### Configuration Not Loading

1. Clear config cache: `php artisan config:clear`
2. Verify `.env` file exists
3. Check file permissions
4. Verify syntax (no spaces around `=`)
5. Check for quotes where needed

### Database Connection Failed

1. Verify database credentials
2. Check database server is running
3. Verify user has permissions
4. Check host/port are correct
5. Test connection manually

### Mail Not Sending

1. Verify SMTP credentials
2. Check host/port are correct
3. Verify encryption matches port
4. Check firewall allows SMTP port
5. Test connection manually

### Stripe Not Working

1. Verify API keys are correct
2. Check keys match environment (test vs live)
3. Verify webhook secret matches Stripe Dashboard
4. Check webhook endpoint is accessible
5. Review Stripe Dashboard logs

## Security Best Practices

1. **Never commit `.env` to version control**
   - File is in `.gitignore`
   - Use `.env.example` as template

2. **Use different `.env` for each environment**
   - Development: `.env`
   - Staging: `.env.staging`
   - Production: `.env.production`

3. **Secure `.env` file permissions**
   - `chmod 600 .env` (read/write for owner only)

4. **Use strong passwords**
   - Database passwords: 20+ characters
   - Admin passwords: 12+ characters with complexity

5. **Rotate secrets regularly**
   - Change passwords periodically
   - Rotate API keys after security incidents
   - Update secrets after team member changes

6. **Use environment-specific values**
   - Test keys for development
   - Live keys for production only
   - Never use production keys in development

## Support

For additional help, see:
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- [DATABASE_SETUP.md](DATABASE_SETUP.md)
- [STRIPE_SETUP.md](STRIPE_SETUP.md)
- [EMAIL_SETUP.md](EMAIL_SETUP.md)
