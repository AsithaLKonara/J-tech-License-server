# Upload Bridge License Dashboard

Complete Laravel-based SaaS license management system for Upload Bridge.

## Features

- User authentication (email/password + magic link)
- Subscription management (monthly/annual/lifetime)
- Stripe payment integration
- License management
- Device tracking
- Admin panel
- Dark theme UI

## Installation

### Requirements

- PHP 8.1+
- MySQL 5.7+ or SQLite
- Composer
- mod_rewrite enabled

### Setup

1. Install dependencies:
```bash
composer install
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Generate application key:
```bash
php artisan key:generate
```

4. Configure database in `.env`:
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_DATABASE=dashboard
DB_USERNAME=root
DB_PASSWORD=
```

5. Run migrations:
```bash
php artisan migrate
```

6. Configure Stripe in `.env`:
```env
STRIPE_KEY=pk_test_...
STRIPE_SECRET=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_ANNUAL=price_...
STRIPE_PRICE_LIFETIME=price_...
```

7. Configure SMTP in `.env`:
```env
MAIL_MAILER=smtp
MAIL_HOST=smtp.yourhost.com
MAIL_PORT=587
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-password
MAIL_FROM_ADDRESS=noreply@yourdomain.com
```

## Docker Deployment

### Test Build Locally

Before deploying, test the Docker build locally:

**On Windows (PowerShell):**
```powershell
cd apps/web-dashboard
.\docker\test-build.ps1
```

**On Linux/Mac:**
```bash
cd apps/web-dashboard
chmod +x docker/test-build.sh
./docker/test-build.sh
```

### Run Container Locally

To run the container for testing:

**On Windows (PowerShell):**
```powershell
.\docker\test-run.ps1
```

**On Linux/Mac:**
```bash
chmod +x docker/test-run.sh
./docker/test-run.sh
```

The application will be available at `http://localhost:8080`

### Manual Docker Build

```bash
docker build -t upload-bridge-license-server .
docker run -p 8080:80 upload-bridge-license-server
```

## Deployment on Shared Hosting

1. Upload all files to your hosting
2. Set document root to `public/` directory
3. Set permissions:
   - `storage/` and `bootstrap/cache/` should be writable (755 or 775)
4. Configure `.env` with production values
5. Run migrations via SSH or hosting control panel

## License

MIT

