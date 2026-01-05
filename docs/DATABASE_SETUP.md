# Database Setup Guide

This guide explains how to set up the database for production deployment.

## Supported Databases

- **MySQL 5.7+** (recommended for production)
- **PostgreSQL 10+** (recommended for production)
- **SQLite** (development only)

## Production Database Setup

### Step 1: Create Database

#### MySQL
```sql
CREATE DATABASE upload_bridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'upload_bridge_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON upload_bridge.* TO 'upload_bridge_user'@'localhost';
FLUSH PRIVILEGES;
```

#### PostgreSQL
```sql
CREATE DATABASE upload_bridge;
CREATE USER upload_bridge_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE upload_bridge TO upload_bridge_user;
```

### Step 2: Configure Environment

Update `.env` file with database credentials:

```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=upload_bridge
DB_USERNAME=upload_bridge_user
DB_PASSWORD=strong_password_here
```

For PostgreSQL:
```env
DB_CONNECTION=pgsql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=upload_bridge
DB_USERNAME=upload_bridge_user
DB_PASSWORD=strong_password_here
```

### Step 3: Run Migrations

```bash
cd apps/web-dashboard
php artisan migrate --force
```

### Step 4: Create Admin User

```bash
# Set admin credentials in .env (optional, or use defaults)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_NAME="Administrator"
ADMIN_PASSWORD=changeme

# Run seeder
php artisan db:seed --class=AdminUserSeeder
```

**IMPORTANT**: Change the admin password immediately after first login!

### Step 5: (Optional) Seed Test Data

For development/testing only:
```bash
php artisan db:seed --class=DatabaseSeeder
```

## Database Connection Pooling

### MySQL (using PDO connection pooling)

Laravel handles connection pooling automatically. Configure pool size in your database server settings:

```ini
# MySQL my.cnf
max_connections = 200
```

### PostgreSQL (using pgBouncer)

1. Install pgBouncer
2. Configure connection pooling
3. Update `.env` to use pgBouncer port (usually 6432)

## Performance Optimization

### Indexes

All necessary indexes are created via migrations. Key indexes include:
- `users.email` (unique)
- `subscriptions.user_id`
- `licenses.user_id`
- `devices.user_id`
- `devices.entitlement_id`

### Query Optimization

Monitor slow queries:
```sql
-- MySQL
SHOW FULL PROCESSLIST;
SELECT * FROM information_schema.PROCESSLIST WHERE TIME > 5;

-- PostgreSQL
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

### Connection Limits

Adjust connection limits based on your server capacity:
- Small deployment: 50-100 connections
- Medium deployment: 100-200 connections
- Large deployment: 200+ connections

## Backup Strategy

### Automated Backups

Set up automated backups using:

1. **MySQL**: `mysqldump` with cron
2. **PostgreSQL**: `pg_dump` with cron
3. **Cloud services**: AWS RDS, Google Cloud SQL, Azure Database

### Backup Script Example (MySQL)

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

### Backup Script Example (PostgreSQL)

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

## Testing Database Performance

### Connection Test

```bash
php artisan tinker
>>> DB::connection()->getPdo();
```

### Query Performance Test

```bash
php artisan tinker
>>> DB::enableQueryLog();
>>> // Run your queries
>>> DB::getQueryLog();
```

## Troubleshooting

### Connection Refused

- Verify database server is running
- Check firewall rules
- Verify host/port in `.env`

### Access Denied

- Verify username and password
- Check user permissions
- Verify host restrictions (localhost vs %)

### Migration Errors

- Ensure database exists
- Check user has CREATE/DROP permissions
- Review migration files for syntax errors

### Performance Issues

- Enable query logging
- Review slow query log
- Check database server resources
- Optimize indexes
- Use connection pooling
