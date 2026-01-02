# 🚀 SaaS License Server Implementation Plan

**Goal**: Transform the license server into a full SaaS platform similar to Cursor, with:
- User account creation and management
- Feature selection and subscription plans
- Stripe payment integration
- Admin panel for manual permissions (cash payments)
- Subscription-based licensing

---

## 📋 Current System Analysis

### What We Have:
- ✅ Auth0 OAuth integration
- ✅ Basic license management (in-memory database)
- ✅ User authentication flow
- ✅ Entitlement token system
- ✅ Device registration
- ✅ Express.js server on Railway

### What We Need:
- ❌ Real database (PostgreSQL/SQLite)
- ❌ User registration system
- ❌ Subscription plans and pricing
- ❌ Stripe payment integration
- ❌ Admin dashboard
- ❌ Feature selection UI
- ❌ Subscription management
- ❌ Webhook handling (Stripe)

---

## 🏗️ Architecture Design

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    SaaS License Server                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Auth0      │  │   Stripe     │  │   Database   │     │
│  │  (OAuth)     │  │  (Payments)  │  │ (PostgreSQL) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                │                    │            │
│         └────────────────┼────────────────────┘            │
│                          │                                 │
│  ┌──────────────────────────────────────────────────┐     │
│  │         Express.js API Server                    │     │
│  │  - Authentication                                │     │
│  │  - Subscription Management                       │     │
│  │  - License Management                            │     │
│  │  - Webhook Handlers                              │     │
│  └──────────────────────────────────────────────────┘     │
│                          │                                 │
│  ┌──────────────────────────────────────────────────┐     │
│  │         Admin Dashboard (React/Next.js)          │     │
│  │  - User Management                               │     │
│  │  - Subscription Management                       │     │
│  │  - Manual Permissions (Cash Payments)           │     │
│  │  - Analytics                                     │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │         Customer Portal (React/Next.js)           │     │
│  │  - Account Creation                               │     │
│  │  - Feature Selection                              │     │
│  │  - Payment (Stripe Checkout)                      │     │
│  │  - Subscription Management                        │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth0_sub VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  is_admin BOOLEAN DEFAULT FALSE,
  status VARCHAR(50) DEFAULT 'active' -- active, suspended, deleted
);
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES plans(id),
  stripe_subscription_id VARCHAR(255) UNIQUE,
  stripe_customer_id VARCHAR(255),
  status VARCHAR(50) NOT NULL, -- active, canceled, past_due, trialing
  current_period_start TIMESTAMP,
  current_period_end TIMESTAMP,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Plans Table
```sql
CREATE TABLE plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL, -- "Basic", "Pro", "Enterprise"
  description TEXT,
  price_monthly DECIMAL(10,2), -- in USD
  price_yearly DECIMAL(10,2), -- in USD
  stripe_price_id_monthly VARCHAR(255),
  stripe_price_id_yearly VARCHAR(255),
  features JSONB, -- Array of feature IDs
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Features Table
```sql
CREATE TABLE features (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key VARCHAR(255) UNIQUE NOT NULL, -- "pattern_upload", "wifi_upload", etc.
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(100), -- "upload", "advanced", "ai", etc.
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Licenses Table
```sql
CREATE TABLE licenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  subscription_id UUID REFERENCES subscriptions(id),
  plan VARCHAR(100) NOT NULL,
  features JSONB NOT NULL, -- Array of feature keys
  expires_at TIMESTAMP,
  payment_method VARCHAR(50), -- "stripe", "cash", "trial", "admin"
  payment_reference VARCHAR(255), -- Stripe subscription ID or cash payment reference
  is_active BOOLEAN DEFAULT TRUE,
  created_by_admin UUID REFERENCES users(id), -- For manual/cash payments
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Devices Table
```sql
CREATE TABLE devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  license_id UUID REFERENCES licenses(id) ON DELETE CASCADE,
  device_id VARCHAR(255) NOT NULL,
  device_name VARCHAR(255),
  last_seen TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(license_id, device_id)
);
```

### Payments Table (Cash/Manual)
```sql
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  subscription_id UUID REFERENCES subscriptions(id),
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',
  payment_method VARCHAR(50) NOT NULL, -- "cash", "bank_transfer", "check"
  reference VARCHAR(255), -- Payment reference number
  status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected
  approved_by UUID REFERENCES users(id), -- Admin who approved
  approved_at TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🎯 Implementation Phases

### Phase 1: Database Setup & Migration (Week 1)

**Tasks:**
1. Set up PostgreSQL database (Railway/Neon/Supabase)
2. Create database schema (migrations)
3. Migrate existing in-memory data
4. Set up database connection pooling
5. Create database models/ORM (Prisma or TypeORM)

**Deliverables:**
- ✅ Database schema
- ✅ Migration scripts
- ✅ Database connection module
- ✅ Model definitions

---

### Phase 2: User Registration & Account Management (Week 1-2)

**Tasks:**
1. Create user registration endpoint
2. Email verification system
3. User profile management
4. Password reset flow
5. Account deletion/deactivation

**API Endpoints:**
```
POST   /api/v2/users/register          - Register new user
POST   /api/v2/users/verify-email      - Verify email
POST   /api/v2/users/reset-password    - Request password reset
GET    /api/v2/users/profile           - Get user profile
PUT    /api/v2/users/profile           - Update profile
DELETE /api/v2/users/account           - Delete account
```

**Deliverables:**
- ✅ User registration API
- ✅ Email verification
- ✅ Profile management

---

### Phase 3: Subscription Plans & Features (Week 2)

**Tasks:**
1. Create plans management system
2. Feature definition system
3. Plan-feature mapping
4. Plan pricing configuration
5. Plan comparison API

**API Endpoints:**
```
GET    /api/v2/plans                   - List all plans
GET    /api/v2/plans/:id               - Get plan details
GET    /api/v2/features                - List all features
POST   /api/v2/admin/plans             - Create plan (admin)
PUT    /api/v2/admin/plans/:id         - Update plan (admin)
```

**Default Plans:**
- **Free**: Basic features, limited usage
- **Basic**: $9/month - Core features
- **Pro**: $29/month - All features + priority support
- **Enterprise**: Custom pricing - All features + dedicated support

**Deliverables:**
- ✅ Plans management system
- ✅ Features catalog
- ✅ Plan-feature mapping

---

### Phase 4: Stripe Integration (Week 2-3)

**Tasks:**
1. Set up Stripe account and API keys
2. Create Stripe products and prices
3. Implement Stripe Checkout
4. Handle Stripe webhooks
5. Subscription management (upgrade/downgrade/cancel)
6. Payment method management

**API Endpoints:**
```
POST   /api/v2/subscriptions/create-checkout    - Create Stripe checkout session
POST   /api/v2/subscriptions/create-portal       - Create customer portal session
GET    /api/v2/subscriptions                    - Get user subscriptions
POST   /api/v2/subscriptions/cancel             - Cancel subscription
POST   /api/v2/webhooks/stripe                  - Stripe webhook handler
```

**Stripe Webhooks:**
- `checkout.session.completed` - New subscription
- `customer.subscription.updated` - Subscription changed
- `customer.subscription.deleted` - Subscription canceled
- `invoice.payment_succeeded` - Payment successful
- `invoice.payment_failed` - Payment failed

**Deliverables:**
- ✅ Stripe integration
- ✅ Checkout flow
- ✅ Webhook handlers
- ✅ Subscription management

---

### Phase 5: Admin Dashboard (Week 3-4)

**Tasks:**
1. Admin authentication and authorization
2. User management interface
3. Subscription management
4. Manual permission assignment (cash payments)
5. Analytics and reporting
6. Payment approval system

**Features:**
- User list with search/filter
- User details and subscription history
- Manual subscription creation
- Cash payment approval workflow
- Feature assignment
- Usage analytics
- Revenue reports

**Tech Stack:**
- Frontend: React + Next.js or Vue.js
- UI Library: Tailwind CSS + shadcn/ui or Ant Design
- Charts: Recharts or Chart.js

**Deliverables:**
- ✅ Admin dashboard UI
- ✅ User management
- ✅ Manual permission system
- ✅ Analytics dashboard

---

### Phase 6: Customer Portal (Week 4-5)

**Tasks:**
1. Customer-facing dashboard
2. Plan selection and comparison
3. Stripe Checkout integration
4. Subscription management UI
5. Feature usage display
6. Billing history

**Features:**
- Account overview
- Plan selection with feature comparison
- Payment method management
- Subscription status
- Usage statistics
- Invoice history
- Support/help section

**Deliverables:**
- ✅ Customer portal UI
- ✅ Plan selection flow
- ✅ Payment integration
- ✅ Subscription management

---

### Phase 7: License Server Updates (Week 5)

**Tasks:**
1. Update login endpoint to use database
2. Update license generation from subscriptions
3. Real-time license validation
4. Subscription status checking
5. Feature entitlement from subscriptions

**API Updates:**
```
POST /api/v2/auth/login
  - Now reads from database
  - Creates license from active subscription
  - Handles trial periods
  - Checks subscription status
```

**Deliverables:**
- ✅ Updated license server
- ✅ Subscription-based licensing
- ✅ Real-time validation

---

### Phase 8: Testing & Deployment (Week 6)

**Tasks:**
1. End-to-end testing
2. Payment flow testing
3. Webhook testing
4. Admin dashboard testing
5. Customer portal testing
6. Security audit
7. Performance optimization
8. Production deployment

**Deliverables:**
- ✅ Test suite
- ✅ Documentation
- ✅ Deployment guide
- ✅ Production-ready system

---

## 🛠️ Technology Stack

### Backend
- **Runtime**: Node.js + Express.js
- **Database**: PostgreSQL (Railway/Neon/Supabase)
- **ORM**: Prisma or TypeORM
- **Payment**: Stripe API
- **Auth**: Auth0 (existing)

### Frontend (Admin & Customer Portal)
- **Framework**: Next.js 14+ (React)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui or Ant Design
- **Charts**: Recharts
- **State Management**: Zustand or React Query

### Infrastructure
- **Hosting**: Railway (existing)
- **Database**: Railway PostgreSQL or Neon
- **CDN**: Vercel (for frontend)
- **Email**: SendGrid or Resend
- **Monitoring**: Sentry

---

## 📦 Required Packages

### Backend Dependencies
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "stripe": "^14.0.0",
    "@prisma/client": "^5.7.0",
    "prisma": "^5.7.0",
    "jsonwebtoken": "^9.0.2",
    "bcrypt": "^5.1.1",
    "zod": "^3.22.4",
    "dotenv": "^16.3.1",
    "cors": "^2.8.5"
  }
}
```

### Frontend Dependencies
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@stripe/stripe-js": "^2.2.0",
    "@stripe/react-stripe-js": "^2.4.0",
    "tailwindcss": "^3.3.6",
    "zustand": "^4.4.7",
    "@tanstack/react-query": "^5.17.0",
    "recharts": "^2.10.3"
  }
}
```

---

## 🔐 Security Considerations

1. **API Authentication**: JWT tokens with refresh mechanism
2. **Admin Authorization**: Role-based access control (RBAC)
3. **Payment Security**: Stripe handles all payment data
4. **Webhook Security**: Verify Stripe webhook signatures
5. **Rate Limiting**: Prevent abuse
6. **Input Validation**: Zod schemas for all inputs
7. **SQL Injection**: Use parameterized queries (ORM)
8. **CORS**: Configure properly for production
9. **HTTPS**: Enforce HTTPS only
10. **Secrets Management**: Use environment variables

---

## 💰 Pricing Strategy (Example)

### Free Plan
- Price: $0/month
- Features: Basic pattern upload, limited devices
- Usage: 10 patterns/month

### Basic Plan
- Price: $9/month or $90/year (save 17%)
- Features: All upload methods, 5 devices
- Usage: Unlimited patterns

### Pro Plan
- Price: $29/month or $290/year (save 17%)
- Features: All features, priority support, 20 devices
- Usage: Unlimited patterns + AI features

### Enterprise Plan
- Price: Custom
- Features: Everything + dedicated support, unlimited devices
- Usage: Custom limits

---

## 📋 Admin Workflow for Cash Payments

1. **Customer contacts admin** (email/phone)
2. **Admin creates manual payment record**:
   - User email
   - Amount
   - Payment method (cash/bank transfer)
   - Reference number
3. **Admin assigns subscription**:
   - Select plan
   - Set duration
   - Assign features
4. **Admin approves payment**:
   - Mark payment as approved
   - Subscription activated
   - User notified via email
5. **License generated automatically** from subscription

---

## 🚀 Quick Start Implementation Order

1. **Database Setup** (Day 1-2)
   - Set up PostgreSQL
   - Create schema
   - Set up Prisma

2. **Basic APIs** (Day 3-5)
   - User registration
   - Plans/features API
   - Updated login endpoint

3. **Stripe Integration** (Day 6-8)
   - Stripe setup
   - Checkout flow
   - Webhooks

4. **Admin Dashboard** (Day 9-12)
   - Basic UI
   - User management
   - Manual permissions

5. **Customer Portal** (Day 13-15)
   - Plan selection
   - Payment flow
   - Account management

6. **Testing & Polish** (Day 16-20)
   - E2E testing
   - Bug fixes
   - Documentation

---

## 📝 Next Steps

1. **Review and approve this plan**
2. **Set up database** (PostgreSQL)
3. **Create project structure**
4. **Start with Phase 1** (Database setup)
5. **Iterate through phases**

---

**Estimated Timeline**: 6 weeks for full implementation  
**Priority**: Start with database and basic APIs, then Stripe, then dashboards

---

**Last Updated**: 2025-01-02

