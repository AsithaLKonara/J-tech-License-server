#!/bin/bash

# Database Backup Script for Upload Bridge
# Usage: ./backup-database.sh [mysql|pgsql]

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/upload_bridge}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Determine database type
DB_TYPE="${1:-mysql}"

if [ "$DB_TYPE" = "mysql" ]; then
    # MySQL Configuration
    DB_HOST="${DB_HOST:-127.0.0.1}"
    DB_PORT="${DB_PORT:-3306}"
    DB_NAME="${DB_NAME:-upload_bridge}"
    DB_USER="${DB_USER:-upload_bridge_user}"
    DB_PASS="${DB_PASS:-}"

    # Perform backup
    BACKUP_FILE="$BACKUP_DIR/mysql_backup_$DATE.sql.gz"
    
    if [ -z "$DB_PASS" ]; then
        mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
    else
        mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$BACKUP_FILE"
    fi

    if [ $? -eq 0 ]; then
        echo "MySQL backup created successfully: $BACKUP_FILE"
    else
        echo "MySQL backup failed!"
        exit 1
    fi

elif [ "$DB_TYPE" = "pgsql" ]; then
    # PostgreSQL Configuration
    DB_HOST="${DB_HOST:-127.0.0.1}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-upload_bridge}"
    DB_USER="${DB_USER:-upload_bridge_user}"
    DB_PASS="${DB_PASS:-}"

    # Perform backup
    BACKUP_FILE="$BACKUP_DIR/pgsql_backup_$DATE.sql.gz"
    
    export PGPASSWORD="$DB_PASS"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        echo "PostgreSQL backup created successfully: $BACKUP_FILE"
    else
        echo "PostgreSQL backup failed!"
        exit 1
    fi

else
    echo "Invalid database type: $DB_TYPE"
    echo "Usage: $0 [mysql|pgsql]"
    exit 1
fi

# Cleanup old backups (keep only last N days)
find "$BACKUP_DIR" -name "*_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Old backups (older than $RETENTION_DAYS days) have been removed."
