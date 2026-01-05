# Operations Runbook

This runbook provides procedures for common operations, maintenance tasks, troubleshooting, and incident response for the Upload Bridge web dashboard.

## Table of Contents

1. [Common Operations](#common-operations)
2. [Maintenance Procedures](#maintenance-procedures)
3. [Backup and Restore](#backup-and-restore)
4. [Monitoring Procedures](#monitoring-procedures)
5. [Incident Response](#incident-response)
6. [Troubleshooting](#troubleshooting)

## Common Operations

### Application Status Check

Check if the application is running:

```bash
# Check web server status
sudo systemctl status apache2
# or
sudo systemctl status nginx

# Check PHP-FPM status
sudo systemctl status php8.2-fpm

# Check application health endpoint
curl https://yourdomain.com/api/v2/health
```

### View Application Logs

```bash
# Laravel logs
tail -f /var/www/upload-bridge/apps/web-dashboard/storage/logs/laravel.log

# Web server error logs
sudo tail -f /var/log/apache2/error.log
# or
sudo tail -f /var/log/nginx/error.log

# PHP-FPM logs
sudo tail -f /var/log/php8.2-fpm.log
```

### Clear Application Cache

```bash
cd /var/www/upload-bridge/apps/web-dashboard

# Clear all caches
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear

# Rebuild caches (production)
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

### Restart Application

```bash
# Restart web server
sudo systemctl restart apache2
# or
sudo systemctl restart nginx

# Restart PHP-FPM
sudo systemctl restart php8.2-fpm

# Restart queue worker (if using)
php artisan queue:restart
```

### Check Database Connection

```bash
cd /var/www/upload-bridge/apps/web-dashboard
php artisan tinker

# In tinker:
>>> DB::connection()->getPdo();
>>> DB::table('users')->count();
```

### View Queued Jobs

```bash
# View queue status
php artisan queue:work --help

# Process queue manually
php artisan queue:work

# View failed jobs
php artisan queue:failed
```

## Maintenance Procedures

### Daily Tasks

1. **Check Application Logs**
   ```bash
   tail -n 100 storage/logs/laravel.log | grep -i error
   ```

2. **Check Disk Space**
   ```bash
   df -h
   ```

3. **Check Application Health**
   ```bash
   curl https://yourdomain.com/api/v2/health
   ```

### Weekly Tasks

1. **Review Error Logs**
   - Check for recurring errors
   - Review error tracking service (Sentry, etc.)
   - Investigate critical errors

2. **Check Backup Status**
   - Verify backups completed successfully
   - Test backup restoration (monthly)

3. **Review Performance Metrics**
   - Check response times
   - Review database query performance
   - Check resource usage

### Monthly Tasks

1. **Update Dependencies**
   ```bash
   composer update
   composer audit  # Check for security vulnerabilities
   ```

2. **Review Security Logs**
   - Check for suspicious activity
   - Review failed login attempts
   - Check rate limiting violations

3. **Database Maintenance**
   ```sql
   -- Optimize tables (MySQL)
   OPTIMIZE TABLE users, subscriptions, licenses, devices;

   -- Vacuum database (PostgreSQL)
   VACUUM ANALYZE;
   ```

4. **Test Backup Restoration**
   - Restore backup to test environment
   - Verify data integrity
   - Document restoration time

### Quarterly Tasks

1. **Security Audit**
   - Review security patches
   - Update SSL certificates
   - Review access logs

2. **Performance Review**
   - Analyze slow queries
   - Review caching strategy
   - Optimize database indexes

3. **Documentation Review**
   - Update runbook with new procedures
   - Document known issues and solutions
   - Review incident reports

## Backup and Restore

### Database Backup

#### MySQL Backup

```bash
#!/bin/bash
BACKUP_DIR="/backups/upload_bridge"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="upload_bridge"
DB_USER="upload_bridge_user"
DB_PASS="your_password"

mkdir -p $BACKUP_DIR
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

#### PostgreSQL Backup

```bash
#!/bin/bash
BACKUP_DIR="/backups/upload_bridge"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="upload_bridge"
DB_USER="upload_bridge_user"

mkdir -p $BACKUP_DIR
PGPASSWORD=your_password pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Automated Backups

Set up cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/backup-script.sh
```

### Restore Database

#### MySQL Restore

```bash
# Restore from backup
gunzip < backup_20250127_020000.sql.gz | mysql -u upload_bridge_user -p upload_bridge
```

#### PostgreSQL Restore

```bash
# Restore from backup
gunzip < backup_20250127_020000.sql.gz | PGPASSWORD=your_password psql -U upload_bridge_user upload_bridge
```

### Application Files Backup

```bash
# Backup application files
tar -czf backup_app_$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='vendor' \
  --exclude='storage/logs/*' \
  /var/www/upload-bridge/apps/web-dashboard

# Backup .env file separately (important!)
cp /var/www/upload-bridge/apps/web-dashboard/.env /backups/env_$(date +%Y%m%d).env
```

## Monitoring Procedures

### Health Checks

#### Application Health

```bash
# Check health endpoint
curl https://yourdomain.com/api/v2/health

# Expected response:
# {"status":"ok","timestamp":"...","version":"2.0"}
```

#### Database Health

```bash
# MySQL
mysqladmin -u upload_bridge_user -p status

# PostgreSQL
psql -U upload_bridge_user -d upload_bridge -c "SELECT version();"
```

#### Disk Space

```bash
# Check disk usage
df -h

# Check specific directory
du -sh /var/www/upload-bridge
du -sh /backups
```

#### Memory Usage

```bash
# Check memory usage
free -h

# Check process memory
ps aux | grep php
```

### Log Monitoring

#### Error Monitoring

```bash
# Watch for errors in real-time
tail -f storage/logs/laravel.log | grep -i error

# Count errors in last hour
grep "$(date +%Y-%m-%d)" storage/logs/laravel.log | grep -i error | wc -l
```

#### Failed Login Attempts

```bash
# Check failed login attempts
grep "Invalid email or password" storage/logs/laravel.log | tail -20
```

#### Rate Limiting Violations

```bash
# Check rate limit violations
grep "429" storage/logs/laravel.log | tail -20
```

### Performance Monitoring

#### Response Time

```bash
# Check API response time
time curl -s https://yourdomain.com/api/v2/health
```

#### Database Query Performance

```bash
# Enable query logging
php artisan tinker
>>> DB::enableQueryLog();
>>> // Run your queries
>>> DB::getQueryLog();
```

## Incident Response

### Incident Severity Levels

- **Critical**: Application down, data loss, security breach
- **High**: Major functionality broken, performance degradation
- **Medium**: Minor functionality broken, non-critical errors
- **Low**: Cosmetic issues, warnings

### Incident Response Process

1. **Identify and Assess**
   - Check application status
   - Review error logs
   - Check monitoring alerts
   - Determine severity

2. **Contain**
   - Isolate affected systems if needed
   - Implement temporary workarounds
   - Prevent further damage

3. **Diagnose**
   - Gather information
   - Review logs
   - Reproduce issue
   - Identify root cause

4. **Remediate**
   - Fix the issue
   - Test the fix
   - Deploy fix
   - Verify resolution

5. **Document**
   - Record incident details
   - Document root cause
   - Update procedures if needed
   - Review and learn

### Common Incidents

#### Application Down

**Symptoms**: HTTP 500 errors, blank pages, timeouts

**Steps**:
1. Check web server status
2. Check PHP-FPM status
3. Check application logs
4. Check database connection
5. Check disk space
6. Restart services if needed

#### Database Connection Failed

**Symptoms**: Database connection errors in logs

**Steps**:
1. Check database server is running
2. Verify credentials in `.env`
3. Check network connectivity
4. Check database user permissions
5. Review database logs

#### High Error Rate

**Symptoms**: Many errors in logs, error tracking alerts

**Steps**:
1. Identify error pattern
2. Review recent code changes
3. Check dependencies
4. Review configuration
5. Check for external service issues

#### Performance Degradation

**Symptoms**: Slow response times, timeouts

**Steps**:
1. Check server resources (CPU, memory, disk)
2. Review slow query log
3. Check database connection pool
4. Review caching effectiveness
5. Check for external service issues

#### Security Incident

**Symptoms**: Unauthorized access, suspicious activity

**Steps**:
1. Isolate affected systems
2. Review access logs
3. Check for unauthorized changes
4. Review user accounts
5. Change compromised credentials
6. Notify security team
7. Document incident

## Troubleshooting

### Application Won't Start

**Possible Causes**:
- Configuration errors
- Missing dependencies
- File permission issues
- Database connection failed

**Solutions**:
1. Check `.env` configuration
2. Verify file permissions
3. Check application logs
4. Test database connection
5. Clear caches
6. Reinstall dependencies

### Database Connection Errors

**Possible Causes**:
- Wrong credentials
- Database server down
- Network issues
- User permissions

**Solutions**:
1. Verify credentials in `.env`
2. Check database server status
3. Test connection manually
4. Review user permissions
5. Check firewall rules

### Email Not Sending

**Possible Causes**:
- SMTP configuration wrong
- Email service down
- Firewall blocking SMTP port
- Invalid credentials

**Solutions**:
1. Verify SMTP credentials
2. Test SMTP connection
3. Check email service status
4. Review firewall rules
5. Check email service logs

### Stripe Webhook Not Working

**Possible Causes**:
- Webhook URL incorrect
- Webhook secret mismatch
- SSL certificate issues
- Firewall blocking requests

**Solutions**:
1. Verify webhook URL in Stripe Dashboard
2. Check webhook secret matches `.env`
3. Review webhook logs in Stripe Dashboard
4. Check application logs
5. Test webhook manually

### High Memory Usage

**Possible Causes**:
- Memory leaks
- Too many concurrent requests
- Large data sets
- Inefficient queries

**Solutions**:
1. Check for memory leaks
2. Review application logs
3. Optimize database queries
4. Increase PHP memory limit
5. Scale horizontally

### Slow Response Times

**Possible Causes**:
- Database queries slow
- External service delays
- Network issues
- Server resource constraints

**Solutions**:
1. Review slow query log
2. Optimize database queries
3. Add database indexes
4. Implement caching
5. Check external services
6. Scale resources

## Support Contacts

- **Technical Support**: support@yourdomain.com
- **Emergency**: emergency@yourdomain.com
- **Security**: security@yourdomain.com

## Additional Resources

- [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Database Setup Guide](DATABASE_SETUP.md)
- [Stripe Setup Guide](STRIPE_SETUP.md)
- [Email Setup Guide](EMAIL_SETUP.md)
- [Security Configuration](SECURITY_CONFIGURATION.md)
- [API Documentation](API.md)
