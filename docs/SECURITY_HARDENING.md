# Security Hardening Checklist

This document outlines security measures to implement before production deployment.

## Credentials and Secrets

### Production Checklist

- [ ] **Remove test credentials from codebase**
  - Database seeders use test data - acceptable for development
  - Production deployments should use `AdminUserSeeder` with unique credentials
  - No hardcoded passwords in code

- [ ] **Secure .env file**
  - File permissions: `chmod 600 .env`
  - Never commit to version control
  - Use different .env for each environment
  - Rotate secrets regularly

- [ ] **Secure license_keys.yaml (if exists)**
  - File is in `.gitignore` - verify it's not committed
  - Use environment variables for license keys in production
  - Restrict file permissions: `chmod 600`

- [ ] **Remove development data**
  - Database seeders include test users
  - Only use `AdminUserSeeder` in production
  - Clear test data after development

## Database Security

### Production Checklist

- [ ] **Use strong database credentials**
  - Unique username (not default)
  - Strong password (20+ characters)
  - Limited privileges (only required permissions)

- [ ] **Secure database connection**
  - Use SSL/TLS for database connections
  - Restrict database access to application server only
  - Use connection pooling

- [ ] **Remove test data**
  - Clear test users, subscriptions, licenses
  - Use production-ready seeders only
  - Verify no test data in production database

## Application Security

### Production Checklist

- [ ] **Environment configuration**
  - `APP_ENV=production`
  - `APP_DEBUG=false`
  - `APP_URL` set to production domain

- [ ] **Security headers enabled**
  - X-Frame-Options
  - X-Content-Type-Options
  - X-XSS-Protection
  - Strict-Transport-Security
  - Content-Security-Policy

- [ ] **Rate limiting configured**
  - API endpoints protected
  - Appropriate limits set
  - Monitoring enabled

- [ ] **CORS configured**
  - Restricted to known origins
  - Credentials handled securely
  - Methods/headers restricted

## Files and Permissions

### Production Checklist

- [ ] **File permissions**
  - Storage: `chmod -R 775 storage bootstrap/cache`
  - .env: `chmod 600 .env`
  - Application files: `chmod 644` (files), `chmod 755` (directories)

- [ ] **Remove development files**
  - Test files (if any)
  - Development scripts (if not needed)
  - Documentation drafts (if any)

## Monitoring and Logging

### Production Checklist

- [ ] **Logging configured**
  - Error logging enabled
  - Log rotation configured
  - Sensitive data not logged

- [ ] **Monitoring enabled**
  - Error tracking (Sentry, etc.)
  - Uptime monitoring
  - Performance monitoring

- [ ] **Alerting configured**
  - Critical error alerts
  - Security event alerts
  - Performance alerts

## SSL/TLS

### Production Checklist

- [ ] **SSL certificate installed**
  - Valid certificate
  - Certificate chain complete
  - Auto-renewal configured

- [ ] **HTTPS enforced**
  - HTTP redirects to HTTPS
  - Secure cookies enabled
  - HSTS header enabled

## External Services

### Production Checklist

- [ ] **Stripe configured**
  - Production API keys (not test keys)
  - Webhook secret configured
  - Webhook signature verification enabled

- [ ] **Email configured**
  - Production SMTP credentials
  - Verified sender address
  - SPF/DKIM/DMARC records set

## Testing

### Production Checklist

- [ ] **Security testing completed**
  - SQL injection tests
  - XSS tests
  - CSRF tests
  - Authentication tests
  - Authorization tests

- [ ] **Penetration testing**
  - Vulnerability scanning
  - Security audit
  - Code review

## Documentation

### Production Checklist

- [ ] **Security documentation**
  - Security configuration documented
  - Incident response plan
  - Security contacts

- [ ] **Operational documentation**
  - Deployment procedures
  - Backup procedures
  - Monitoring procedures

## Pre-Deployment Verification

Before deploying to production:

1. Review this checklist
2. Test in staging environment
3. Perform security scan
4. Review logs for sensitive data
5. Verify all secrets are in environment variables
6. Confirm test data is removed
7. Verify SSL/TLS is configured
8. Test all security features
9. Verify monitoring is working
10. Document deployment

## Post-Deployment

After deploying to production:

1. Verify application is accessible
2. Check logs for errors
3. Verify monitoring is working
4. Test critical functions
5. Verify SSL certificate is valid
6. Test security headers
7. Verify rate limiting is working
8. Test authentication flows
9. Verify external integrations (Stripe, email)
10. Document any issues

## Ongoing Security

### Regular Tasks

- [ ] **Regular updates**
  - Update dependencies monthly
  - Apply security patches promptly
  - Review security advisories

- [ ] **Regular audits**
  - Review logs weekly
  - Security scan monthly
  - Code review quarterly

- [ ] **Regular backups**
  - Daily database backups
  - Weekly full backups
  - Test restoration monthly

## Resources

- Laravel Security: https://laravel.com/docs/security
- OWASP: https://owasp.org
- CWE: https://cwe.mitre.org
- Security Headers: https://securityheaders.com
