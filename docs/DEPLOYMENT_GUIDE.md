# 🚀 J-Tech Pixel LED Upload Bridge - Deployment Guide

This document provides a unified set of instructions for deploying both the Web Dashboard and the Desktop App ecosystem.

---

## 🌐 1. Web Dashboard (Laravel)

### Environment Prerequisites
- PHP 8.1+
- MySQL or PostgreSQL
- Composer
- Stripe Account (Live Keys)

### Deployment Steps (Shared Hosting / cPanel)
1. **Prepare Package**: Run the root packager:
   ```powershell
   .\prepare_production_zip.ps1
   ```
2. **Upload Files**:
   - Upload `upload-bridge-core` to your user root (ABOVE `public_html`).
   - Upload the contents of the `public_html` folder to your server's `public_html`.
3. **Configure Environment**:
   - Create a `.env` file in the `upload-bridge-core` folder.
   - Use `apps/web-dashboard/.env.production` as a template.
4. **Initialize DB**:
   - Log in via SSH and run: `php artisan migrate --force`.

---

## 💻 2. Desktop Application

The desktop app is distributed as a single portable `.exe` for Windows.

### Build Process
1. Use the secure production builder:
   ```bash
   python apps/upload-bridge/build_prod_exe.py
   ```
2. The resulting `UploadBridge.exe` will be located in the `dist/` directory.

---

## 🛡️ 3. Security Hardening

### Mandatory Checks
- [ ] **HTTPS**: Verify the web portal forces SSL.
- [ ] **Secrets Audit**: Ensure `.env` files are not publicly accessible.
- [ ] **API Throttling**: Verify that rate limits are active in `config/cors.php`.

---

**Version**: 3.0.0  
**Release Date**: January 2026
