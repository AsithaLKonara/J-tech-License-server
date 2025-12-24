# ⚡ Quick Deploy to Vercel

## 🚀 3-Step Deployment

### Step 1: Install & Login

```bash
cd license-server
npm install
vercel login
```

### Step 2: Deploy

```bash
vercel --prod
```

When prompted:
- **Set up and deploy?** → `Y`
- **Link to existing project?** → `N` (first time)
- **Project name?** → `upload-bridge-license` (or press Enter)
- **Directory?** → `.` (press Enter)

### Step 3: Copy URL & Configure

After deployment, you'll see:
```
✅ Production: https://your-project-name.vercel.app
```

**Update Upload Bridge config:**

```bash
# Windows PowerShell
python apps\upload-bridge\scripts\update_vercel_url.py https://your-project-name.vercel.app

# Or manually edit:
# apps/upload-bridge/config/auth_config.yaml
# Set: auth_server_url: https://your-project-name.vercel.app
```

## ✅ Test It

```bash
# Test health endpoint
curl https://your-project-name.vercel.app/api/health

# Test login
curl -X POST https://your-project-name.vercel.app/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword123","device_id":"DEVICE_123","device_name":"Test"}'
```

## 🎯 Test Accounts

- **Email**: `test@example.com`
- **Password**: `testpassword123`
- **Plan**: Pro (all features)

## 📝 That's It!

Your license server is now live on Vercel! 🎉

For detailed instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

