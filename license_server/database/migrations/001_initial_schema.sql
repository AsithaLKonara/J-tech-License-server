-- Migration: 001_initial_schema.sql
-- Description: Initial database schema for enterprise licensing system
-- Date: 2025-01-XX

-- This migration creates the initial schema
-- Run schema.sql first, then this migration adds any additional setup

-- Ensure UUID extension is enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Note: Main schema is in schema.sql
-- This file is for any post-schema setup or data migrations
