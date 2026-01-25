# Email Configuration Guide

This guide explains how to configure SMTP email delivery for production.

## Supported Mail Drivers

- **SMTP** (recommended for production)
- **Mailgun** (recommended for production)
- **Postmark** (recommended for production)
- **SES** (AWS Simple Email Service)
- **Sendmail** (for local servers)
- **Mailtrap** (development/testing only)

## Step 1: Choose Email Service

### Recommended Services

1. **Mailgun** (https://www.mailgun.com)
   - Free tier: 5,000 emails/month
   - Good deliverability
   - Easy setup

2. **Postmark** (https://postmarkapp.com)
   - Free tier: 100 emails/month
   - Excellent deliverability
   - Transactional email focused

3. **Amazon SES** (https://aws.amazon.com/ses/)
   - Pay per email (very cheap)
   - High deliverability
   - Requires AWS account

4. **SendGrid** (https://sendgrid.com)
   - Free tier: 100 emails/day
   - Good deliverability
   - Popular choice

## Step 2: Configure SMTP Settings

### Example: Mailgun Configuration

1. Sign up at https://www.mailgun.com
2. Verify your domain
3. Get SMTP credentials:
   - Go to **Sending** → **Domain settings**
   - Copy SMTP credentials

Update `.env`:
```env
MAIL_MAILER=smtp
MAIL_HOST=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=postmaster@mg.yourdomain.com
MAIL_PASSWORD=your_smtp_password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge"
```

### Example: Postmark Configuration

1. Sign up at https://postmarkapp.com
2. Create a server
3. Get SMTP credentials from server settings

Update `.env`:
```env
MAIL_MAILER=smtp
MAIL_HOST=smtp.postmarkapp.com
MAIL_PORT=587
MAIL_USERNAME=your_server_token
MAIL_PASSWORD=your_server_token
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge"
```

### Example: AWS SES Configuration

1. Set up AWS SES account
2. Verify your email/domain
3. Get SMTP credentials from SES console

Update `.env`:
```env
MAIL_MAILER=smtp
MAIL_HOST=email-smtp.us-east-1.amazonaws.com
MAIL_PORT=587
MAIL_USERNAME=your_ses_smtp_username
MAIL_PASSWORD=your_ses_smtp_password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge"
```

### Example: SendGrid Configuration

1. Sign up at https://sendgrid.com
2. Create API key or use SMTP
3. Get SMTP credentials

Update `.env`:
```env
MAIL_MAILER=smtp
MAIL_HOST=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME="Upload Bridge"
```

## Step 3: Configure From Address

The `MAIL_FROM_ADDRESS` must be:
- Verified with your email service provider
- Match your domain (for better deliverability)
- Not use generic addresses like "no-reply" (may affect deliverability)

Best practices:
- Use `noreply@yourdomain.com` or `notifications@yourdomain.com`
- Verify the domain with your email provider
- Use SPF/DKIM/DMARC records for authentication

## Step 4: Test Email Delivery

### Test Magic Link Email

1. Navigate to login page
2. Click "Magic Link" option
3. Enter your email address
4. Check email inbox (and spam folder)
5. Verify email was received

### Test Password Reset Email

1. Navigate to login page
2. Click "Forgot Password"
3. Enter your email address
4. Check email inbox
5. Verify reset link works

### Test Notification Email

Test other notification emails:
- Subscription confirmations
- Payment receipts
- Account notifications

### Manual Test via Tinker

```bash
php artisan tinker
>>> Mail::raw('Test email', function($message) {
...     $message->to('your@email.com')
...             ->subject('Test Email');
... });
```

## Step 5: Email Templates

The application uses Laravel's mail system with blade templates.

### Magic Link Email

Located at: `resources/views/emails/magic-link.blade.php`

Customize:
- Email subject
- Email body
- Link styling
- Branding

### Password Reset Email

Laravel's default password reset email can be customized by publishing:
```bash
php artisan vendor:publish --tag=laravel-notifications
```

## Step 6: Email Queue (Recommended)

For better performance, use queue for sending emails:

1. Configure queue driver in `.env`:
```env
QUEUE_CONNECTION=database
```

2. Create queue table:
```bash
php artisan queue:table
php artisan migrate
```

3. Start queue worker:
```bash
php artisan queue:work
```

4. Or use supervisor/systemd to keep worker running

## Troubleshooting

### Emails Not Sending

1. **Check SMTP credentials**
   - Verify username/password
   - Check host/port
   - Verify encryption (tls/ssl)

2. **Check email service status**
   - Mailgun: https://status.mailgun.com
   - Postmark: https://status.postmarkapp.com
   - AWS SES: https://status.aws.amazon.com

3. **Check application logs**
   ```bash
   tail -f storage/logs/laravel.log
   ```

4. **Test SMTP connection**
   ```bash
   php artisan tinker
   >>> config('mail')
   ```

### Emails Going to Spam

1. **Verify domain**
   - Set up SPF record
   - Set up DKIM record
   - Set up DMARC record

2. **Use verified sender address**
   - Verify domain with email provider
   - Use professional email address

3. **Avoid spam triggers**
   - Don't use all caps
   - Avoid spam words
   - Include unsubscribe link
   - Use proper HTML formatting

### Connection Timeout

1. Check firewall rules
2. Verify SMTP port is open (587, 465, 25)
3. Check server can reach SMTP server
4. Try different port (587 vs 465)

### Authentication Failed

1. Verify username and password
2. Check if account is active
3. Verify IP is whitelisted (if required)
4. Check if 2FA is enabled (may need app password)

## Security Best Practices

1. **Never commit credentials to version control**
   - Use `.env` file (in `.gitignore`)
   - Use environment variables in production

2. **Use TLS/SSL encryption**
   - Always use `MAIL_ENCRYPTION=tls` or `ssl`
   - Never send credentials over plain text

3. **Limit email sending rate**
   - Configure rate limiting
   - Use queue for bulk emails
   - Respect email service limits

4. **Monitor email delivery**
   - Track bounce rates
   - Monitor spam reports
   - Review delivery logs

## Email Service Limits

### Mailgun
- Free: 5,000 emails/month
- Foundation: $35/month for 50,000 emails

### Postmark
- Free: 100 emails/month
- Paid: Starts at $15/month for 10,000 emails

### AWS SES
- $0.10 per 1,000 emails
- Free tier: 62,000 emails/month (for EC2)

### SendGrid
- Free: 100 emails/day
- Essentials: $19.95/month for 50,000 emails

## Support

- Laravel Mail Documentation: https://laravel.com/docs/mail
- Mailgun Documentation: https://documentation.mailgun.com
- Postmark Documentation: https://postmarkapp.com/developer
- AWS SES Documentation: https://docs.aws.amazon.com/ses
