-- Create Database for Upload Bridge Web Dashboard
-- Run this script to create the database before running migrations

-- Create database
CREATE DATABASE IF NOT EXISTS upload_bridge 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Use the database
USE upload_bridge;

-- Show success message (MySQL doesn't support PRINT, so this is just a comment)
-- Database created successfully!
-- Next step: Run migrations with: php artisan migrate
