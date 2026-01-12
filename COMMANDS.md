# Development Commands Reference

This file contains common commands for development and deployment.

## Setup Commands

### Initial Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Supabase credentials
# (Use your favorite text editor)

# Run setup checks
python check_setup.py

# Initialize database
python setup_db.py
```

## Development Commands

### Run Application
```bash
# Development mode (with auto-reload)
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# With custom port
uvicorn main:app --reload --port 8080
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_root_endpoint

# Verbose output
pytest -v
```

### Database Management
```bash
# Initialize database tables
python setup_db.py

# Test database connection
python test_connection.py

# Alembic migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1
```

### Code Quality
```bash
# Format code with black
black .

# Lint code
pylint main.py
pylint routers/
pylint utils/

# Type checking (if mypy installed)
mypy .
```

## Docker Commands

### Build and Run
```bash
# Build image
docker build -t fastapi-supabase-app .

# Run container
docker run -p 8000:8000 --env-file .env fastapi-supabase-app

# Run with volume mount (for development)
docker run -p 8000:8000 -v ${PWD}:/app --env-file .env fastapi-supabase-app
```

### Docker Compose (if using)
```bash
# Start services
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f
```

## Deployment Commands

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Set environment variables
railway variables set SUPABASE_URL=your-url
railway variables set SUPABASE_ANON_KEY=your-key
# ... (set all variables)

# Deploy
railway up

# View logs
railway logs

# Open in browser
railway open
```

### Render
```bash
# Deploy via dashboard or:
render deploy

# View logs
render logs
```

### Fly.io
```bash
# Install Fly CLI (Windows PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Login
fly auth login

# Launch app
fly launch

# Set secrets
fly secrets set SUPABASE_URL=your-url
fly secrets set SUPABASE_ANON_KEY=your-key
# ... (set all secrets)

# Deploy
fly deploy

# View logs
fly logs

# SSH into instance
fly ssh console
```

## Database Commands (Supabase)

### SQL Editor Queries
```sql
-- View all profiles
SELECT * FROM profiles;

-- View active subscriptions
SELECT * FROM subscriptions WHERE status = 'active';

-- View plans
SELECT * FROM plans;

-- View API keys (hashed)
SELECT id, user_id, key_prefix, name, created_at FROM api_keys;

-- View subscription history
SELECT * FROM subscription_history ORDER BY event_date DESC;

-- View recent billing events
SELECT * FROM billing_events ORDER BY received_at DESC LIMIT 10;
```

## Maintenance Commands

### Update Dependencies
```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Generate new requirements.txt
pip freeze > requirements.txt
```

### Backup Database
```bash
# From Supabase Dashboard → Database → Backups
# Or use pg_dump:
pg_dump -h db.xxxxxxxxxxxxx.supabase.co -U postgres -d postgres > backup.sql
```

### Clean Up
```bash
# Remove Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Remove virtual environment
rm -rf venv/

# Remove logs
rm -rf logs/
```

## Debugging Commands

### Check Configuration
```bash
# Run pre-flight checks
python check_setup.py

# Test Supabase connection
python test_connection.py

# Print environment variables (be careful with secrets!)
python -c "from config import get_settings; print(get_settings())"
```

### Interactive Python Shell
```bash
# Start Python shell with app context
python

# Then in Python:
from database import engine, SessionLocal
from models import *
from config import get_settings

db = SessionLocal()
# Now you can query models
users = db.query(Profile).all()
```

### View Logs
```bash
# Application logs (if configured)
tail -f logs/app.log

# Uvicorn logs
# (displayed in terminal when running)

# Docker logs
docker logs -f container-name
```

## Useful One-Liners

### Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Count Lines of Code
```bash
find . -name "*.py" -not -path "./venv/*" | xargs wc -l
```

### Find TODO Comments
```bash
grep -r "TODO" --include="*.py" .
```

### Check Python Version
```bash
python --version
```

### List Installed Packages
```bash
pip list
```

### Create Requirements from Current Environment
```bash
pip freeze > requirements.txt
```

## Environment-Specific Commands

### Development
```bash
export DEBUG=True
export ENVIRONMENT=development
uvicorn main:app --reload
```

### Staging
```bash
export DEBUG=False
export ENVIRONMENT=staging
uvicorn main:app --workers 2
```

### Production
```bash
export DEBUG=False
export ENVIRONMENT=production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Quick Reference URLs

### Local Development
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

### Supabase Dashboard
- Project: https://app.supabase.com/project/your-project-id
- SQL Editor: https://app.supabase.com/project/your-project-id/sql
- Auth: https://app.supabase.com/project/your-project-id/auth
- Database: https://app.supabase.com/project/your-project-id/database

## Tips

- Always activate virtual environment before running commands
- Use `.env` for local development, never commit it
- Use environment variables on deployment platforms
- Run `check_setup.py` before starting development
- Run tests before deploying
- Check logs regularly for errors
- Keep dependencies updated
- Back up database regularly

For more detailed information, see the documentation files in this directory.
