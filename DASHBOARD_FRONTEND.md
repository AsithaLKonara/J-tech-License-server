# 🌐 License Server Dashboard Frontend

A simple web dashboard frontend for the Upload Bridge License Server.

## 📋 Overview

The dashboard provides a web interface for users to:
- Login with email/password
- View their account information
- See their license plan and features
- Manage their session

## 🚀 Deployment

The dashboard is automatically deployed with the license server to Vercel.

**URL**: `https://j-tech-license-server.vercel.app/`

## ✨ Features

### Login Page
- Email/password authentication
- Error handling
- Test account credentials displayed
- Responsive design

### Dashboard
- User information display
- License plan details
- Feature list with badges
- Session management
- Logout functionality

## 🎨 Design

- Modern gradient design
- Responsive layout
- Clean UI/UX
- Mobile-friendly

## 📁 Files

```
license-server/
├── public/
│   └── index.html          # Dashboard frontend
└── vercel.json             # Vercel config (includes rewrite rules)
```

## 🔧 Configuration

The dashboard automatically connects to the API endpoints:
- `/api/v2/auth/login` - User authentication
- Uses same domain as API (no CORS issues)

## 🧪 Testing

1. Navigate to: `https://j-tech-license-server.vercel.app/`
2. Login with test account:
   - Email: `test@example.com`
   - Password: `testpassword123`
3. View dashboard with user info and features

## 📝 Customization

To customize the dashboard:
1. Edit `public/index.html`
2. Modify styles in `<style>` section
3. Update JavaScript functions as needed
4. Redeploy to Vercel

## 🔒 Security

- Session tokens stored in localStorage
- Automatic logout on token expiration
- Secure API communication (HTTPS)

---

**Status**: ✅ Ready for use  
**Deployed**: ✅ Yes (with license server)

