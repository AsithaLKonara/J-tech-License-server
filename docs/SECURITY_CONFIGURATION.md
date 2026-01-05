# Security Configuration Guide

This guide explains security hardening measures implemented for production.

## Security Headers

Security headers are automatically added to all HTTP responses via `SecurityHeaders` middleware.

### Headers Added

1. **X-Frame-Options: DENY**
   - Prevents page from being displayed in frames
   - Protects against clickjacking attacks

2. **X-Content-Type-Options: nosniff**
   - Prevents browsers from MIME-sniffing responses
   - Forces browsers to respect Content-Type header

3. **X-XSS-Protection: 1; mode=block**
   - Enables XSS filter in older browsers
   - Legacy support (modern browsers use CSP)

4. **Strict-Transport-Security**
   - Enforces HTTPS connections
   - Prevents protocol downgrade attacks
   - Only enabled when using HTTPS

5. **Content-Security-Policy**
   - Controls which resources can be loaded
   - Prevents XSS attacks
   - Customized for Stripe integration

6. **Referrer-Policy: strict-origin-when-cross-origin**
   - Controls referrer information sent
   - Balances privacy and functionality

7. **Permissions-Policy**
   - Controls browser features (geolocation, camera, etc.)
   - Disables unnecessary features by default

### Customizing Security Headers

Edit `app/Http/Middleware/SecurityHeaders.php` to adjust headers based on your needs.

**Important**: If you customize CSP, ensure it allows:
- Stripe scripts: `https://js.stripe.com`
- Stripe API: `https://api.stripe.com`
- Stripe webhooks: `https://hooks.stripe.com`

## Rate Limiting

Rate limiting is configured on API endpoints to prevent abuse.

### Current Configuration

- **API endpoints**: 60 requests per minute per IP
- Configured in `app/Providers/RouteServiceProvider.php`

### Adjusting Rate Limits

Edit `app/Providers/RouteServiceProvider.php`:

```php
RateLimiter::for('api', function (Request $request) {
    return Limit::perMinute(60)->by($request->user()?->id ?: $request->ip());
});
```

Options:
- `perMinute(60)`: Change number of requests
- `perHour(1000)`: Use hourly limit
- `by($identifier)`: Change how limits are tracked

### Rate Limit Headers

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `Retry-After`: Seconds to wait before retrying

## CORS Configuration

CORS (Cross-Origin Resource Sharing) is configured in `config/cors.php`.

### Current Configuration

- **Allowed origins**: `*` (all origins) - suitable for desktop app
- **Allowed methods**: All methods
- **Allowed headers**: All headers
- **Supports credentials**: `false` (for security)

### Production CORS Configuration

For production, restrict allowed origins:

```php
'allowed_origins' => [
    'https://yourdomain.com',
    'https://app.yourdomain.com',
],
```

Or use patterns:
```php
'allowed_origins_patterns' => [
    '/^https:\/\/.*\.yourdomain\.com$/',
],
```

**Note**: Current configuration allows all origins for desktop app compatibility. Adjust based on your deployment.

## SQL Injection Protection

Laravel provides built-in protection against SQL injection:

1. **Query Builder**: Uses parameter binding
2. **Eloquent ORM**: Uses parameter binding
3. **Prepared Statements**: All database queries use prepared statements

### Best Practices

- Always use Eloquent or Query Builder
- Never use raw SQL with user input
- Validate and sanitize user input
- Use type casting in models

### Example (Safe)
```php
User::where('email', $email)->first(); // Safe
```

### Example (Unsafe - Don't do this)
```php
DB::select("SELECT * FROM users WHERE email = '{$email}'"); // Unsafe!
```

## XSS Protection

Laravel provides built-in XSS protection:

1. **Blade templating**: Automatically escapes output
2. **{{ }} syntax**: Escapes HTML
3. **{!! !!} syntax**: Raw output (use with caution)

### Best Practices

- Use `{{ }}` for all user-generated content
- Only use `{!! !!}` for trusted content
- Sanitize input before storing
- Use HTML Purifier for rich text

### Content Security Policy

CSP further protects against XSS by controlling resource loading. Current policy:
- Allows scripts only from self and Stripe
- Prevents inline scripts (with exceptions for Stripe)
- Restricts resource loading

## CSRF Protection

CSRF protection is enabled for all web routes via `VerifyCsrfToken` middleware.

### Excluded Routes

Webhook endpoints are excluded from CSRF verification:
- `/webhook/stripe` (uses signature verification instead)

### CSRF Tokens

Include CSRF token in forms:
```blade
@csrf
```

Or in AJAX requests:
```javascript
headers: {
    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
}
```

## Secure Cookies

Secure cookies are configured in `config/session.php`.

### Configuration

Set in `.env`:
```env
SESSION_SECURE_COOKIE=true
SESSION_DOMAIN=yourdomain.com
```

This ensures:
- Cookies only sent over HTTPS
- Cookies scoped to your domain
- HttpOnly flag enabled (prevents JavaScript access)

## Authentication Security

### Password Hashing

Passwords are hashed using bcrypt (Laravel default):
- Salted hashing
- High cost factor
- One-way hashing

### Session Security

- Session IDs are randomly generated
- Session data is encrypted
- Sessions expire after inactivity
- HttpOnly cookies prevent XSS

### Token Security

API tokens are:
- Randomly generated
- Hashed before storage
- Expire after inactivity
- Revocable

## File Upload Security

### Validation

- File type validation
- File size limits
- Filename sanitization

### Storage

- Uploads stored outside web root
- Direct access prevented
- Access via application logic only

## Environment Security

### .env File

- Never commit `.env` to version control
- Use different `.env` for each environment
- Restrict file permissions: `chmod 600 .env`

### Secrets Management

- Store secrets in environment variables
- Use secret management services in production
- Rotate secrets regularly

## Security Checklist

- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] CORS configured for production
- [ ] HTTPS enabled
- [ ] Secure cookies enabled
- [ ] SQL injection protection verified
- [ ] XSS protection verified
- [ ] CSRF protection enabled
- [ ] File uploads secured
- [ ] Environment variables secured
- [ ] Logs don't contain sensitive data
- [ ] Error messages don't reveal sensitive information
- [ ] Regular security updates applied
- [ ] Firewall configured
- [ ] Intrusion detection enabled

## Monitoring Security

### Logs

Monitor application logs for:
- Authentication failures
- Rate limit violations
- Suspicious requests
- Error patterns

### Tools

- Security headers: https://securityheaders.com
- SSL test: https://www.ssllabs.com/ssltest
- CSP evaluator: https://csp-evaluator.withgoogle.com
- OWASP ZAP: https://www.zaproxy.org

## Incident Response

If security incident occurs:

1. **Isolate**: Take affected systems offline
2. **Assess**: Determine scope of breach
3. **Contain**: Prevent further damage
4. **Remediate**: Fix vulnerabilities
5. **Notify**: Inform affected users if required
6. **Document**: Record incident and response
7. **Review**: Learn from incident

## Resources

- Laravel Security: https://laravel.com/docs/security
- OWASP Top 10: https://owasp.org/www-project-top-ten
- CWE Top 25: https://cwe.mitre.org/top25
- Security Headers: https://securityheaders.com
