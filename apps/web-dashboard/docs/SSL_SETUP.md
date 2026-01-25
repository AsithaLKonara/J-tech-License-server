# SSL/TLS Certificate Setup Guide

This guide explains how to set up SSL/TLS certificates for production deployment.

## Overview

SSL/TLS certificates are required for:
- HTTPS encryption
- Secure cookie transmission
- Webhook security (Stripe, etc.)
- Browser trust
- SEO benefits

## Options for SSL Certificates

### 1. Let's Encrypt (Free, Recommended)

- **Free** SSL certificates
- **Automatic renewal**
- **90-day validity** (auto-renewed)
- **Trusted by all browsers**
- **Requires server access**

### 2. Cloud Provider SSL

- **AWS Certificate Manager (ACM)**
- **Google Cloud SSL**
- **Azure App Service Certificates**
- **Usually free** with cloud hosting
- **Automatic management**

### 3. Commercial SSL Certificates

- **DigiCert**
- **GlobalSign**
- **Comodo**
- **Paid** but includes support
- **Longer validity periods**

## Option 1: Let's Encrypt with Certbot (Recommended)

### Prerequisites

- Server with root/sudo access
- Domain name pointing to server
- Port 80 and 443 open
- Apache or Nginx web server

### Installation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install certbot python3-certbot-apache
# Or for Nginx:
sudo apt install certbot python3-certbot-nginx
```

#### CentOS/RHEL
```bash
sudo yum install epel-release
sudo yum install certbot python3-certbot-apache
# Or for Nginx:
sudo yum install certbot python3-certbot-nginx
```

### Obtain Certificate

#### With Apache
```bash
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com
```

#### With Nginx
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### Standalone (if not using Apache/Nginx)
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts:
1. Enter email address
2. Agree to terms
3. Choose whether to redirect HTTP to HTTPS (recommended: Yes)

### Automatic Renewal

Certbot sets up automatic renewal via cron. Test renewal:
```bash
sudo certbot renew --dry-run
```

Certificates are stored at:
- Certificate: `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/yourdomain.com/privkey.pem`

## Option 2: Cloud Provider SSL

### AWS Certificate Manager (ACM)

1. Go to AWS Certificate Manager
2. Request a public certificate
3. Enter domain name
4. Choose DNS validation or email validation
5. Add CNAME record (for DNS validation) or verify email
6. Certificate is issued automatically
7. Attach to:
   - Load Balancer
   - CloudFront distribution
   - API Gateway

**Note**: ACM certificates can only be used with AWS services.

### Google Cloud SSL

1. Go to Cloud Console → SSL Certificates
2. Create SSL certificate
3. Enter domain name
4. Create Google-managed certificate
5. Attach to Load Balancer
6. Certificate is automatically provisioned

### Azure App Service

1. Go to App Service → TLS/SSL settings
2. Add private key certificate (upload or import from Key Vault)
3. Or use App Service Managed Certificate (free)
4. Enable HTTPS Only

## Option 3: Manual Certificate Installation

If you have a certificate from a commercial provider:

### 1. Upload Certificate Files

Upload to secure location (e.g., `/etc/ssl/certs/`):
- Certificate file (`.crt` or `.pem`)
- Private key file (`.key`)
- Certificate chain file (`.ca-bundle` or `.chain.pem`)

### 2. Configure Web Server

#### Apache Configuration

Edit `/etc/apache2/sites-available/yourdomain-ssl.conf`:
```apache
<VirtualHost *:443>
    ServerName yourdomain.com
    DocumentRoot /var/www/your-app/public

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/yourdomain.crt
    SSLCertificateKeyFile /etc/ssl/private/yourdomain.key
    SSLCertificateChainFile /etc/ssl/certs/yourdomain.chain.crt

    # SSL Configuration
    SSLProtocol all -SSLv2 -SSLv3
    SSLCipherSuite HIGH:!aNULL:!MD5
    SSLHonorCipherOrder on

    # HSTS
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
</VirtualHost>
```

Enable site:
```bash
sudo a2ensite yourdomain-ssl
sudo systemctl reload apache2
```

#### Nginx Configuration

Edit `/etc/nginx/sites-available/yourdomain`:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_trusted_certificate /etc/ssl/certs/yourdomain.chain.crt;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    root /var/www/your-app/public;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.2-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

Test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Configure Laravel for HTTPS

### 1. Update .env

```env
APP_URL=https://yourdomain.com
SESSION_SECURE_COOKIE=true
```

### 2. Update Trusted Proxies (if behind load balancer)

Edit `app/Http/Middleware/TrustProxies.php`:
```php
protected $proxies = '*'; // Or specific IPs
protected $headers = Request::HEADER_X_FORWARDED_FOR |
                     Request::HEADER_X_FORWARDED_HOST |
                     Request::HEADER_X_FORWARDED_PORT |
                     Request::HEADER_X_FORWARDED_PROTO;
```

### 3. Force HTTPS in AppServiceProvider (if needed)

Edit `app/Providers/AppServiceProvider.php`:
```php
public function boot(): void
{
    if (config('app.env') === 'production') {
        URL::forceScheme('https');
    }
}
```

## Verify SSL Setup

### 1. Test in Browser

- Navigate to `https://yourdomain.com`
- Check for padlock icon
- Verify no SSL warnings

### 2. Test with SSL Labs

Visit https://www.ssllabs.com/ssltest/
- Enter your domain
- Review SSL rating (aim for A or A+)
- Check for vulnerabilities

### 3. Test Certificate Validity

```bash
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### 4. Check Certificate Expiry

```bash
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

## Security Best Practices

### 1. Use Strong Ciphers

- Disable SSLv2, SSLv3, TLSv1.0, TLSv1.1
- Use TLSv1.2 or TLSv1.3
- Prefer strong cipher suites

### 2. Enable HSTS

Add Strict-Transport-Security header:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### 3. Redirect HTTP to HTTPS

Always redirect HTTP traffic to HTTPS

### 4. Use Secure Cookies

Set `SESSION_SECURE_COOKIE=true` in `.env`

### 5. OCSP Stapling

Enable OCSP stapling for better performance:
- Apache: `SSLUseStapling on`
- Nginx: `ssl_stapling on`

## Troubleshooting

### Certificate Not Trusted

1. Verify certificate chain is complete
2. Check intermediate certificates are included
3. Verify domain name matches certificate
4. Check certificate hasn't expired

### Mixed Content Warnings

1. Ensure all resources (CSS, JS, images) use HTTPS
2. Use protocol-relative URLs or force HTTPS
3. Check browser console for mixed content errors

### Certificate Expired

1. **Let's Encrypt**: Renew automatically with `certbot renew`
2. **Manual**: Request new certificate and update configuration
3. Set up monitoring for certificate expiry

### Connection Refused on Port 443

1. Check firewall allows port 443
2. Verify web server is listening on port 443
3. Check SSL configuration in web server
4. Review web server error logs

## Certificate Renewal Monitoring

Set up monitoring to alert before expiration:

### Check Certificate Expiry

```bash
#!/bin/bash
DOMAIN="yourdomain.com"
EXPIRY_DATE=$(echo | openssl s_client -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
    echo "WARNING: SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
    # Send alert
fi
```

## Support

- Let's Encrypt: https://letsencrypt.org/docs
- Certbot: https://certbot.eff.org/docs
- SSL Labs: https://www.ssllabs.com/ssltest
- Mozilla SSL Config Generator: https://ssl-config.mozilla.org
