#!/bin/bash

# Database Restore Script for Upload Bridge
# Usage: ./restore-database.sh <backup_file> [mysql|pgsql]

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Error: Backup file not specified"
    echo "Usage: $0 <backup_file> [mysql|pgsql]"
    exit 1
fi

BACKUP_FILE="$1"
DB_TYPE="${2:-mysql}"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [ "$DB_TYPE" = "mysql" ]; then
    # MySQL Configuration
    DB_HOST="${DB_HOST:-127.0.0.1}"
    DB_PORT="${DB_PORT:-3306}"
    DB_NAME="${DB_NAME:-upload_bridge}"
    DB_USER="${DB_USER:-upload_bridge_user}"
    DB_PASS="${DB_PASS:-}"

    echo "Restoring MySQL database: $DB_NAME"
    echo "WARNING: This will overwrite the existing database!"
    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled."
        exit 0
    fi

    # Restore database
    if [ -z "$DB_PASS" ]; then
        gunzip < "$BACKUP_FILE" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$DB_NAME"
    else
        gunzip < "$BACKUP_FILE" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME"
    fi

    if [ $? -eq 0 ]; then
        echo "MySQL database restored successfully from: $BACKUP_FILE"
    else
        echo "MySQL database restore failed!"
        exit 1
    fi

elif [ "$DB_TYPE" = "pgsql" ]; then
    # PostgreSQL Configuration
    DB_HOST="${DB_HOST:-127.0.0.1}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-upload_bridge}"
    DB_USER="${DB_USER:-upload_bridge_user}"
    DB_PASS="${DB_PASS:-}"

    echo "Restoring PostgreSQL database: $DB_NAME"
    echo "WARNING: This will overwrite the existing database!"
    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled."
        exit 0
    fi

    # Restore database
    export PGPASSWORD="$DB_PASS"
    gunzip < "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

    if [ $? -eq 0 ]; then
        echo "PostgreSQL database restored successfully from: $BACKUP_FILE"
    else
        echo "PostgreSQL database restore failed!"
        exit 1
    fi

else
    echo "Invalid database type: $DB_TYPE"
    echo "Usage: $0 <backup_file> [mysql|pgsql]"
    exit 1
fi
