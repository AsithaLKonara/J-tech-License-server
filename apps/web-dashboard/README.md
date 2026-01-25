# Upload Bridge Web Dashboard

A comprehensive SaaS License Management Dashboard built with Laravel 10, Stripe and SQLite.

## Table of Contents
1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Quick Setup (Windows)](#quick-setup-windows)
4. [Manual Installation](#manual-installation)
5. [Configuration](#configuration)
6. [Core Modules](#core-modules)
7. [Common Commands](#common-commands)
8. [Troubleshooting](#troubleshooting)

---

## Features

- **Authentication**: Secure login, registration, and magic link authentication.
- **SaaS Subscriptions**: Full Stripe integration for billing and subscriptions.
- **License Management**: Generate and manage software licenses for devices.
- **Device Tracking**: Monitor activate devices and hardware identifiers.
- **Admin Panel**: Dedicated administrative interface for managing users and subscriptions.
- **Responsive Design**: Modern dashboard interface accessible on all devices.

---

## Prerequisites

- **PHP**: 8.1 or higher
- **Composer**: Dependency manager for PHP
- **SQLite**: Database (enabled by default in PHP)
- **Stripe Account**: For processing payments

---

## Quick Setup (Windows)

The project includes a PowerShell script to automate the setup process.

1. Open PowerShell in the project root.
2. Run the setup script:
   ```powershell
   ./setup.ps1
   ```
3. Follow the prompts in the script.

---

## Manual Installation

If you prefer manual setup, follow these steps:

1. **Install Dependencies**:
   ```bash
   composer install
   ```
2. **Setup Environment**:
   ```bash
   cp .env.example .env
   php artisan key:generate
   ```
3. **Database Setup**:
   - Create an empty file at `database/database.sqlite`.
   - Run migrations:
     ```bash
     php artisan migrate
     ```
4. **Create Folders**:
   Ensure the following directories exist and are writable:
   - `storage/framework/sessions`
   - `storage/framework/views`
   - `storage/framework/cache/data`
   - `bootstrap/cache`

---

## Configuration

Edit the `.env` file to configure your application:

- `APP_URL`: Set to your production URL or `http://localhost:8000` for local development.
- `DB_DATABASE`: Path to your SQLite database.
- `STRIPE_KEY` / `STRIPE_SECRET`: Your Stripe API keys.
- `MAIL_*`: Configure SMTP settings for magic links and notifications.

---

## Core Modules

### 1. License Management
Users can view and manage their licenses in the `/licenses` section. Licenses are tied to subscriptions.

### 2. Device Management
The system tracks hardware identifiers (HWID) to prevent license sharing. Users can manage their active devices under `/devices`.

### 3. Billing & Subscriptions
Integration with Stripe for subscription lifecycle management (Subscribe, Upgrade, Cancel).

### 4. Admin Dashboard
Accessible at `/admin` for users with the admin role. Allows management of all users and manual subscription creation.

---

## Common Commands

- **Start Dev Server**: `php artisan serve`
- **Run Migrations**: `php artisan migrate`
- **Database Tinker**: `php artisan tinker`
- **Clear Cache**: `php artisan optimize:clear`
- **Generate Admin User**:
  ```php
  // via php artisan tinker
  \App\Models\User::create([
      'name' => 'Admin User',
      'email' => 'admin@example.com',
      'password' => Hash::make('password'),
      'is_admin' => true,
  ]);
  ```

---

## Troubleshooting

### "Failed to open stream" error in storage
If you encounter errors related to `storage/framework/...`, ensure the directory structure exists:
```powershell
New-Item -ItemType Directory -Force -Path "storage/framework/sessions", "storage/framework/views", "storage/framework/cache/data"
```

### Missing SQLite Extension
Ensure `extension=sqlite3` and `extension=pdo_sqlite` are uncommented in your `php.ini`.

### Stripe Webhook Issues
For local development, use the Stripe CLI to forward webhooks:
```bash
stripe listen --forward-to localhost:8000/webhook/stripe
```
