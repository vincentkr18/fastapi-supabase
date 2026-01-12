# FastAPI + Supabase Auth SaaS API

A production-ready FastAPI backend with Supabase Auth integration for SaaS applications.
cd D:\Projects\Backend\Fast-api\api-template; uvicorn main:app --reload

## 🏗️ Architecture

- **Authentication**: Delegated to Supabase Auth (email/password, Google OAuth, email verification)
- **Authorization**: JWT validation and resource access control in FastAPI
- **Database**: PostgreSQL via Supabase with Row Level Security (RLS)
- **Billing**: Lemon Squeezy webhook integration

## 🔐 Authentication Flow

1. Frontend uses Supabase JS SDK for login/signup/OAuth
2. Supabase issues JWT access tokens
3. Frontend sends JWT in `Authorization: Bearer <token>` header
4. FastAPI validates JWT and extracts user ID
5. FastAPI enforces authorization via RLS policies

## 📋 Features

- ✅ User profile management
- ✅ SaaS plan catalog
- ✅ Subscription management
- ✅ Subscription history tracking
- ✅ API key generation and management
- ✅ Lemon Squeezy webhook handling
- ✅ Row Level Security (RLS)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

### 3. Set Up Database

Run database migrations:

```bash
alembic upgrade head
```

Or use the setup script:

```bash
python setup_db.py
```

### 4. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## 📚 API Endpoints

### User Profiles (Authenticated)
- `GET /users/me` - Get current user profile
- `PATCH /users/me` - Update current user profile

### SaaS Plans (Public)
- `GET /plans` - List all plans
- `GET /plans/{plan_id}` - Get plan details

### Subscriptions (Authenticated)
- `POST /subscriptions` - Create subscription
- `GET /subscriptions/me` - Get current subscription
- `POST /subscriptions/me/cancel` - Cancel subscription
- `GET /subscriptions/me/history` - Get subscription history

### API Keys (Authenticated)
- `POST /api-keys` - Generate new API key
- `GET /api-keys` - List user's API keys
- `DELETE /api-keys/{id}` - Revoke API key

### Webhooks
- `POST /webhooks/lemon-squeezy` - Lemon Squeezy billing events

## 🗄️ Database Schema

### Tables

1. **profiles** - User profile data (supplements `auth.users`)
2. **plans** - SaaS pricing plans
3. **subscriptions** - User subscriptions
4. **subscription_history** - Subscription change log
5. **api_keys** - User API keys
6. **billing_events** - Webhook event log

All tables have RLS enabled with policies referencing `auth.uid()`.

## 🛡️ Security

- JWT validation using Supabase public keys
- Row Level Security (RLS) on all tables
- API key hashing
- Webhook signature verification
- CORS configuration

## 📖 Documentation

- [Supabase Setup Guide](SUPABASE_SETUP.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🧪 Testing

```bash
pytest
```

## 📦 Deployment

This application can be deployed to:
- Railway
- Render
- Fly.io
- Any platform supporting Python/FastAPI

Make sure to set environment variables in your deployment platform.

## 📄 License

MIT
