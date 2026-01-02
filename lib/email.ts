/**
 * Email Service - SMTP Email Sending
 * Uses nodemailer with SMTP configuration
 */

import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: parseInt(process.env.SMTP_PORT || '587'),
  secure: false, // true for 465, false for other ports
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

/**
 * Send magic link email
 */
export async function sendMagicLink(email: string, token: string): Promise<void> {
  const url = `${process.env.APP_URL}/api/v2/auth/verify-magic-link?token=${token}`;
  
  await transporter.sendMail({
    from: process.env.SMTP_FROM,
    to: email,
    subject: 'Login to Upload Bridge',
    html: `
      <h2>Login to Upload Bridge</h2>
      <p>Click the link below to login:</p>
      <p><a href="${url}">${url}</a></p>
      <p>This link will expire in 15 minutes.</p>
    `,
    text: `Login to Upload Bridge: ${url}`,
  });
}

