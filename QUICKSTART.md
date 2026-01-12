# Quick Start Guide

Get your FastAPI + Supabase Auth SaaS application running in minutes.

## Prerequisites

- Python 3.9 or higher
- A Supabase account (free tier available)
- pip or poetry for package management

## Step 1: Clone and Install

```bash
# Navigate to the project
cd api-template

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Set Up Supabase

1. **Create a Supabase project** at [https://app.supabase.com](https://app.supabase.com)

2. **Get your credentials** from Project Settings → API:
   - Project URL
   - anon (public) key
   - service_role key
   - JWT secret (from JWT Settings)

3. **Get database URL** from Project Settings → Database:
   - Connection string (replace `[YOUR-PASSWORD]` with your actual password)

## Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Supabase credentials
# Use your favorite text editor
```

Update these values in `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
API_KEY_SECRET_KEY=generate-a-random-secret-key
```

## Step 4: Set Up Database

```bash
# Run database setup script
python setup_db.py
```

This will:
- Create all necessary tables
- Seed initial SaaS plans (Free, Basic, Pro, Enterprise)

## Step 5: Enable Authentication in Supabase

1. Go to **Authentication** → **Providers** in Supabase dashboard
2. **Email** provider should be enabled by default
3. (Optional) Enable **Google OAuth** if needed
4. Configure email templates in **Authentication** → **Email Templates**

## Step 6: Run the Application

```bash
# Start the FastAPI server
uvicorn main:app --reload
```

The API is now running at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Step 7: Test the API

### Test Health Check
```bash
curl http://localhost:8000/health
```

### Test Plans Endpoint (Public)
```bash
curl http://localhost:8000/plans
```

### Test Authentication Flow

You'll need to use Supabase Auth from your frontend:

```javascript
// Example using Supabase JS SDK
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://your-project.supabase.co',
  'your-anon-key'
)

// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'test@example.com',
  password: 'SecurePassword123!'
})

// Get access token
const { data: { session } } = await supabase.auth.getSession()
const accessToken = session.access_token

// Call FastAPI endpoint
const response = await fetch('http://localhost:8000/users/me', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})
```

## Step 8: Enable Row Level Security (Optional but Recommended)

For production, enable RLS in Supabase:

1. Go to **SQL Editor** in Supabase dashboard
2. Run RLS policies from `SUPABASE_SETUP.md`

Example:
```sql
-- Enable RLS on profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Users can view own profile
CREATE POLICY "Users can view own profile"
ON profiles FOR SELECT
USING (auth.uid() = id);
```

## API Usage Examples

### Get Current User Profile
```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Profile
```bash
curl -X PATCH http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "display_name": "johndoe"
  }'
```

### Create Subscription
```bash
curl -X POST http://localhost:8000/subscriptions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "PLAN_UUID_HERE"
  }'
```

### Generate API Key
```bash
curl -X POST http://localhost:8000/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My API Key"
  }'
```

## Project Structure

```
api-template/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── database.py            # Database connection
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── requirements.txt       # Python dependencies
├── setup_db.py           # Database setup script
├── .env                  # Environment variables (create this)
├── .env.example          # Environment template
├── routers/
│   ├── users.py          # User profile endpoints
│   ├── plans.py          # SaaS plans endpoints
│   ├── subscriptions.py  # Subscription management
│   ├── api_keys.py       # API key management
│   └── webhooks.py       # Webhook handlers
├── utils/
│   ├── auth.py           # JWT validation
│   ├── security.py       # Security utilities
│   └── supabase_client.py # Supabase client
├── tests/
│   └── test_api.py       # Basic tests
└── docs/
    ├── README.md         # Main documentation
    ├── ARCHITECTURE.md   # Architecture overview
    └── SUPABASE_SETUP.md # Detailed Supabase guide
```

## Next Steps

1. **Frontend Integration**: Build a frontend with React/Vue/Next.js
2. **Billing Setup**: Configure Lemon Squeezy webhooks
3. **Custom Plans**: Modify plans in `setup_db.py`
4. **RLS Policies**: Add Row Level Security policies
5. **Testing**: Add more tests in `tests/`
6. **Deployment**: Deploy to Railway, Render, or Fly.io

## Troubleshooting

### "Import could not be resolved" errors in IDE
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`
- Configure your IDE to use the virtual environment

### Database connection errors
- Check `DATABASE_URL` in `.env`
- Verify database password
- Ensure database allows connections from your IP

### JWT validation errors
- Verify `SUPABASE_JWT_SECRET` is correct
- Check token hasn't expired
- Ensure token format is `Bearer <token>`

### "Table does not exist" errors
- Run `python setup_db.py`
- Check database connection

## Support

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Supabase Documentation](https://supabase.com/docs)
- [Architecture Guide](ARCHITECTURE.md)
- [Supabase Setup Guide](SUPABASE_SETUP.md)

## Development Tips

```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Format code
black .

# Check for errors
python -m pylint main.py
```

Happy coding! 🚀
