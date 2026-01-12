# FastAPI + Supabase Auth - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Client                          │
│                     (React, Vue, Next.js, etc.)                  │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
                │ Auth Flows                  │ API Calls
                │ (signup, login,             │ (with JWT token)
                │  OAuth, etc.)               │
                ▼                             ▼
┌───────────────────────────┐    ┌──────────────────────────────┐
│     Supabase Auth         │    │      FastAPI Backend         │
│  (Authentication Only)    │    │   (Authorization + Logic)    │
├───────────────────────────┤    ├──────────────────────────────┤
│ • Email/Password          │    │ • JWT Validation             │
│ • Google OAuth            │    │ • User Profiles              │
│ • Email Verification      │    │ • Subscription Management    │
│ • Token Issuance          │    │ • API Key Management         │
│ • Session Management      │    │ • Billing Webhooks           │
└───────────────┬───────────┘    └──────────┬───────────────────┘
                │                           │
                │ Issues JWT                │ Validates JWT
                │ References auth.users.id  │ Uses user_id
                │                           │
                └───────────┬───────────────┘
                            ▼
                ┌───────────────────────────┐
                │   Supabase PostgreSQL     │
                │                           │
                │ • auth.users (managed)    │
                │ • profiles (custom)       │
                │ • plans                   │
                │ • subscriptions           │
                │ • subscription_history    │
                │ • api_keys                │
                │ • billing_events          │
                │                           │
                │ Row Level Security (RLS)  │
                └───────────────────────────┘
```

## Authentication Flow

### 1. User Signup (Supabase)
```
User → Frontend → Supabase Auth
                     ↓
                  Creates user in auth.users
                     ↓
                  Sends verification email
                     ↓
                  Returns session + JWT
                     ↓
Frontend → FastAPI → Creates profile in profiles table
```

### 2. User Login (Supabase)
```
User → Frontend → Supabase Auth
                     ↓
                  Validates credentials
                     ↓
                  Returns session + JWT
                     ↓
Frontend stores JWT for API calls
```

### 3. API Request (FastAPI)
```
Frontend → FastAPI endpoint
    with Authorization: Bearer <jwt>
            ↓
    JWT Validation (utils/auth.py)
            ↓
    Extract user_id from JWT
            ↓
    Query database with user_id
            ↓
    Return user-specific data
```

## Database Schema

### Managed by Supabase (DO NOT MODIFY)
- **auth.users**: User identities, emails, passwords
- **auth.sessions**: Active sessions
- **auth.identities**: OAuth provider identities

### Managed by FastAPI (CUSTOM TABLES)

#### profiles
```sql
id          UUID PRIMARY KEY (FK → auth.users.id)
first_name  VARCHAR(100)
last_name   VARCHAR(100)
display_name VARCHAR(150)
avatar_url  VARCHAR(500)
extra_meta  JSON
created_at  TIMESTAMP
updated_at  TIMESTAMP
```

#### plans
```sql
id                        UUID PRIMARY KEY
name                      VARCHAR(100) UNIQUE
description               TEXT
lemon_squeezy_product_id  VARCHAR(255)
price_monthly             DECIMAL(10,2)
price_annually            DECIMAL(10,2)
features                  JSON
active                    BOOLEAN
created_at                TIMESTAMP
updated_at                TIMESTAMP
```

#### subscriptions
```sql
id                           UUID PRIMARY KEY
user_id                      UUID (FK → profiles.id)
plan_id                      UUID (FK → plans.id)
status                       VARCHAR(50)
start_date                   TIMESTAMP
end_date                     TIMESTAMP
lemon_squeezy_subscription_id VARCHAR(255)
price_id                     VARCHAR(255)
auto_renew                   BOOLEAN
canceled_at                  TIMESTAMP
created_at                   TIMESTAMP
updated_at                   TIMESTAMP
```

#### subscription_history
```sql
id              UUID PRIMARY KEY
subscription_id UUID (FK → subscriptions.id)
event           VARCHAR(100)
amount          DECIMAL(10,2)
event_date      TIMESTAMP
metadata        JSON
```

#### api_keys
```sql
id          UUID PRIMARY KEY
user_id     UUID (FK → profiles.id)
key_hash    VARCHAR(255) UNIQUE
key_prefix  VARCHAR(20)
name        VARCHAR(100)
created_at  TIMESTAMP
expires_at  TIMESTAMP
revoked     BOOLEAN
last_used   TIMESTAMP
```

#### billing_events
```sql
id            UUID PRIMARY KEY
user_id       UUID (FK → profiles.id)
event_type    VARCHAR(100)
payload       JSON
received_at   TIMESTAMP
processed     BOOLEAN
error_message TEXT
```

## Security Model

### Row Level Security (RLS)

All custom tables have RLS enabled with policies that use `auth.uid()`:

```sql
-- Example: Users can only see their own profile
CREATE POLICY "Users can view own profile"
ON profiles FOR SELECT
USING (auth.uid() = id);
```

### JWT Validation

FastAPI validates every request:
1. Extract token from `Authorization: Bearer <token>`
2. Verify signature using `SUPABASE_JWT_SECRET`
3. Check expiration
4. Extract user ID from `sub` claim
5. Use user ID for authorization

### API Key Security

- Generated using cryptographically secure random
- Hashed with bcrypt before storage
- Only shown once upon creation
- Can be revoked by user

## API Endpoints

### Public (No Auth)
- `GET /` - Health check
- `GET /health` - Detailed health
- `GET /plans` - List plans
- `GET /plans/{id}` - Get plan

### Protected (Requires JWT)
- `GET /users/me` - Get profile
- `PATCH /users/me` - Update profile
- `POST /subscriptions` - Create subscription
- `GET /subscriptions/me` - Get subscription
- `POST /subscriptions/me/cancel` - Cancel subscription
- `GET /subscriptions/me/history` - Subscription history
- `POST /api-keys` - Generate API key
- `GET /api-keys` - List API keys
- `DELETE /api-keys/{id}` - Revoke API key

### Server-Only (Webhook)
- `POST /webhooks/lemon-squeezy` - Billing webhooks

## Data Flow Examples

### Example 1: User Profile Update
```
1. User updates profile in frontend
2. Frontend sends PATCH to /users/me with JWT
3. FastAPI validates JWT → extracts user_id
4. FastAPI updates profiles table where id = user_id
5. RLS policy ensures user can only update own row
6. Returns updated profile
```

### Example 2: Subscription Creation
```
1. User selects plan and pays via Lemon Squeezy
2. Lemon Squeezy sends webhook to /webhooks/lemon-squeezy
3. FastAPI validates webhook signature
4. FastAPI creates subscription record
5. FastAPI creates subscription_history entry
6. User can now access subscription via /subscriptions/me
```

### Example 3: API Key Generation
```
1. User requests new API key via frontend
2. Frontend sends POST to /api-keys with JWT
3. FastAPI validates JWT → extracts user_id
4. FastAPI generates secure random key
5. FastAPI hashes key and stores in api_keys table
6. Returns full key (only time it's shown)
7. User stores key for future API calls
```

## Environment Configuration

### Required Environment Variables
```
SUPABASE_URL              - Supabase project URL
SUPABASE_ANON_KEY         - Anon/public key
SUPABASE_SERVICE_ROLE_KEY - Service role key
SUPABASE_JWT_SECRET       - JWT signing secret
DATABASE_URL              - PostgreSQL connection string
API_KEY_SECRET_KEY        - Secret for API key hashing
LEMON_SQUEEZY_WEBHOOK_SECRET - Webhook signature secret
```

## Deployment Checklist

- [ ] Set all environment variables
- [ ] Enable RLS on all tables
- [ ] Create RLS policies
- [ ] Configure CORS for production domain
- [ ] Set up Supabase Auth providers
- [ ] Configure email templates
- [ ] Set up Lemon Squeezy webhooks
- [ ] Enable HTTPS
- [ ] Set up monitoring/logging
- [ ] Test authentication flow
- [ ] Test webhook processing

## Best Practices

1. **Never store passwords** - Supabase handles this
2. **Never expose service_role key** to frontend
3. **Always validate JWT** on protected endpoints
4. **Use RLS policies** for defense in depth
5. **Hash API keys** before storage
6. **Verify webhook signatures**
7. **Use environment variables** for secrets
8. **Enable email confirmation** for signups
9. **Implement rate limiting** for production
10. **Monitor auth logs** regularly
