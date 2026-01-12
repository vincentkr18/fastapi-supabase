# Supabase Setup Guide

This guide will help you set up Supabase Auth for your FastAPI application.

## Prerequisites

- A Supabase account (free tier available at [supabase.com](https://supabase.com))
- Python 3.9+ installed
- PostgreSQL knowledge (basic)

## Step 1: Create a Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Click "New Project"
3. Fill in:
   - **Project name**: Your app name
   - **Database password**: Strong password (save this!)
   - **Region**: Choose closest to your users
4. Click "Create new project"
5. Wait for project to be provisioned (1-2 minutes)

## Step 2: Get Your Credentials

From your Supabase project dashboard:

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY`

3. Go to **Settings** → **API** → **JWT Settings**
   - Copy **JWT Secret** → `SUPABASE_JWT_SECRET`

4. Go to **Settings** → **Database**
   - Copy **Connection string** → `DATABASE_URL`
   - Make sure to replace `[YOUR-PASSWORD]` with your actual database password

## Step 3: Configure Environment Variables

Update your `.env` file with the credentials from Step 2:

```env
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters-long

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

## Step 4: Enable Authentication Providers

### Email/Password Authentication

1. Go to **Authentication** → **Providers**
2. **Email** should be enabled by default
3. Configure email settings:
   - **Confirm email**: Toggle ON (recommended)
   - **Secure email change**: Toggle ON (recommended)

### Google OAuth (Optional)

1. Go to **Authentication** → **Providers**
2. Find **Google** and click to configure
3. Follow Supabase's guide to set up Google OAuth:
   - Create a Google Cloud project
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs
4. Enter your Google Client ID and Secret in Supabase

## Step 5: Configure Email Templates

1. Go to **Authentication** → **Email Templates**
2. Customize templates for:
   - **Confirm signup**: Welcome email with verification link
   - **Magic Link**: Passwordless login
   - **Change Email**: Confirm email change
   - **Reset Password**: Password recovery

## Step 6: Set Up Database Tables

Run the setup script to create all required tables:

```bash
python setup_db.py
```

This will create:
- `profiles` - User profile data
- `plans` - SaaS pricing plans
- `subscriptions` - User subscriptions
- `subscription_history` - Subscription audit log
- `api_keys` - User API keys
- `billing_events` - Webhook events

## Step 7: Enable Row Level Security (RLS)

For production, enable RLS policies in Supabase:

### Profiles Table

```sql
-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can view own profile"
ON profiles FOR SELECT
USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
ON profiles FOR UPDATE
USING (auth.uid() = id);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile"
ON profiles FOR INSERT
WITH CHECK (auth.uid() = id);
```

### Subscriptions Table

```sql
-- Enable RLS
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Users can read their own subscriptions
CREATE POLICY "Users can view own subscriptions"
ON subscriptions FOR SELECT
USING (auth.uid() = user_id);

-- Only service role can modify subscriptions
-- (handled via backend with service_role key)
```

### API Keys Table

```sql
-- Enable RLS
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Users can read their own API keys
CREATE POLICY "Users can view own api keys"
ON api_keys FOR SELECT
USING (auth.uid() = user_id);

-- Users can insert their own API keys
CREATE POLICY "Users can insert own api keys"
ON api_keys FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can delete their own API keys
CREATE POLICY "Users can delete own api keys"
ON api_keys FOR DELETE
USING (auth.uid() = user_id);
```

### Plans Table (Public Read)

```sql
-- Enable RLS
ALTER TABLE plans ENABLE ROW LEVEL SECURITY;

-- Anyone can read plans (public)
CREATE POLICY "Anyone can view plans"
ON plans FOR SELECT
TO PUBLIC
USING (active = true);
```

## Step 8: Test Your Setup

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

2. Visit `http://localhost:8000/docs`

3. Test authentication:
   - Sign up via Supabase JS SDK (frontend)
   - Get access token
   - Call FastAPI endpoints with `Authorization: Bearer <token>`

## Frontend Integration

### Example: Supabase JS SDK

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://xxxxxxxxxxxxx.supabase.co',
  'your-anon-key'
)

// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123'
})

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

// Get session
const { data: { session } } = await supabase.auth.getSession()
const accessToken = session.access_token

// Call FastAPI with token
const response = await fetch('http://localhost:8000/users/me', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})
```

## Security Best Practices

1. **Never expose service_role key** in frontend code
2. **Always use HTTPS** in production
3. **Enable RLS** on all tables
4. **Validate JWT** on every protected endpoint
5. **Use environment variables** for sensitive data
6. **Enable email confirmation** for new signups
7. **Implement rate limiting** on authentication endpoints
8. **Monitor authentication logs** in Supabase dashboard

## Troubleshooting

### "Invalid JWT" errors

- Check that `SUPABASE_JWT_SECRET` is correct
- Ensure token hasn't expired (default: 1 hour)
- Verify token is sent in `Authorization: Bearer <token>` format

### Database connection errors

- Verify `DATABASE_URL` is correct
- Check database password
- Ensure database allows connections from your IP

### RLS policy errors

- Verify RLS policies are created correctly
- Check that `auth.uid()` matches your user ID
- Use service role key for admin operations

## Next Steps

- Set up [Lemon Squeezy integration](LEMON_SQUEEZY_SETUP.md) for billing
- Configure CORS for your frontend domain
- Set up monitoring and logging
- Deploy to production (Railway, Render, Fly.io, etc.)

## Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
