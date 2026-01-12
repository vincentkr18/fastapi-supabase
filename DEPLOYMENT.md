# Deployment Guide

This guide covers deploying your FastAPI + Supabase Auth application to production.

## Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Supabase project set up and configured
- [ ] Row Level Security (RLS) enabled on all tables
- [ ] RLS policies created
- [ ] CORS origins updated for production domain
- [ ] Email templates customized
- [ ] Webhook endpoints configured
- [ ] Tests passing (`pytest`)
- [ ] Dependencies up to date
- [ ] `.env` file not committed to git

## Deployment Options

### Option 1: Railway

[Railway](https://railway.app) is recommended for FastAPI applications.

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login to Railway**
```bash
railway login
```

3. **Initialize Project**
```bash
railway init
```

4. **Set Environment Variables**
```bash
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_ANON_KEY=your-anon-key
railway variables set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
railway variables set SUPABASE_JWT_SECRET=your-jwt-secret
railway variables set DATABASE_URL=your-database-url
railway variables set API_KEY_SECRET_KEY=your-secret-key
railway variables set LEMON_SQUEEZY_WEBHOOK_SECRET=your-webhook-secret
railway variables set ENVIRONMENT=production
railway variables set DEBUG=False
```

5. **Deploy**
```bash
railway up
```

6. **Get URL**
```bash
railway domain
```

### Option 2: Render

[Render](https://render.com) offers free tier for hobby projects.

1. **Create New Web Service** on Render dashboard

2. **Connect Repository**
   - Connect your GitHub/GitLab repository
   - Or deploy from Docker image

3. **Configure Service**
   - **Name**: Your app name
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - Add all variables from `.env`
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=False`

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy on git push

### Option 3: Fly.io

[Fly.io](https://fly.io) is great for global distribution.

1. **Install Fly CLI**
```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows
iwr https://fly.io/install.ps1 -useb | iex
```

2. **Login**
```bash
fly auth login
```

3. **Create fly.toml**
```toml
app = "your-app-name"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

4. **Deploy**
```bash
fly launch
fly secrets set SUPABASE_URL=your-url
fly secrets set SUPABASE_ANON_KEY=your-key
# ... set all other secrets
fly deploy
```

### Option 4: Docker (Any Platform)

Use the included Dockerfile for any Docker-compatible platform.

1. **Build Image**
```bash
docker build -t fastapi-supabase-app .
```

2. **Run Locally**
```bash
docker run -p 8000:8000 \
  -e SUPABASE_URL=your-url \
  -e SUPABASE_ANON_KEY=your-key \
  # ... other env vars
  fastapi-supabase-app
```

3. **Deploy to Platform**
   - Push to Docker Hub: `docker push`
   - Deploy to AWS ECS, Google Cloud Run, Azure Container Apps, etc.

## Post-Deployment Configuration

### 1. Update CORS Origins

In your `.env` or environment variables:
```env
CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

### 2. Configure Supabase Auth

In Supabase Dashboard → Authentication → URL Configuration:

- **Site URL**: `https://your-frontend.com`
- **Redirect URLs**: Add your production URLs

### 3. Set Up Webhooks

#### Lemon Squeezy
1. Go to Lemon Squeezy Dashboard → Settings → Webhooks
2. Add webhook URL: `https://your-api.com/webhooks/lemon-squeezy`
3. Select events to receive
4. Copy webhook secret to `LEMON_SQUEEZY_WEBHOOK_SECRET`

### 4. Enable HTTPS

Most platforms (Railway, Render, Fly.io) provide HTTPS automatically.

For custom domains:
- Add CNAME record pointing to your deployment
- Platform will provision SSL certificate automatically

### 5. Set Up Monitoring

#### Supabase Monitoring
- Go to Supabase Dashboard → Reports
- Monitor database performance, API usage

#### Application Monitoring

Add Sentry for error tracking:

```bash
pip install sentry-sdk[fastapi]
```

```python
# In main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    environment=settings.ENVIRONMENT
)
```

### 6. Set Up Logging

For production logging, consider:
- [LogDNA](https://logdna.com)
- [Papertrail](https://papertrailapp.com)
- [Datadog](https://www.datadoghq.com)

### 7. Database Backups

Supabase provides automatic backups, but for extra safety:

1. Go to Supabase Dashboard → Database → Backups
2. Enable daily backups
3. Set retention period

## Performance Optimization

### 1. Database Connection Pooling

Already configured in `database.py`:
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
```

### 2. Enable Caching

Add Redis for caching:
```bash
pip install redis fastapi-cache2
```

### 3. Use CDN

For static assets, use a CDN:
- Cloudflare
- AWS CloudFront
- Fastly

### 4. Rate Limiting

Add rate limiting:
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## Security Checklist

- [ ] HTTPS enabled
- [ ] Environment variables secured (not in code)
- [ ] Service role key never exposed to frontend
- [ ] RLS enabled on all tables
- [ ] JWT validation on all protected endpoints
- [ ] Webhook signatures verified
- [ ] API keys hashed in database
- [ ] CORS configured for specific origins
- [ ] Rate limiting enabled
- [ ] Email confirmation required for signups
- [ ] Password requirements enforced (Supabase)
- [ ] Regular dependency updates
- [ ] Error messages don't leak sensitive info

## Scaling Considerations

### Horizontal Scaling

Most platforms auto-scale:
- Railway: Automatic
- Render: Manual scaling in dashboard
- Fly.io: `fly scale count 3`

### Database Scaling

Supabase offers:
- Free tier: 500MB database, 2 concurrent connections
- Pro tier: 8GB database, 60 concurrent connections
- Custom: Contact Supabase for enterprise

### Caching Strategy

1. **Application-level**: Use Redis for frequently accessed data
2. **Database-level**: Supabase has built-in caching
3. **CDN-level**: Cache API responses at edge

## Monitoring Checklist

- [ ] Uptime monitoring (UptimeRobot, Pingdom)
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (New Relic, Datadog)
- [ ] Log aggregation (LogDNA, Papertrail)
- [ ] Database monitoring (Supabase Dashboard)
- [ ] API usage tracking
- [ ] Webhook delivery monitoring

## Troubleshooting Production Issues

### Database Connection Issues
```python
# Check connection pool status
from database import engine
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
```

### Memory Issues
- Increase instance size
- Check for memory leaks
- Enable garbage collection logging

### Slow Response Times
- Check database query performance
- Add database indexes
- Enable caching
- Use connection pooling

## Rollback Strategy

### Railway/Render
- Dashboard → Deployments → Rollback to previous deployment

### Fly.io
```bash
fly releases
fly rollback <version>
```

### Docker
```bash
# Keep previous image tags
docker tag app:latest app:v1.0.0
docker tag app:latest app:v1.0.1

# Rollback
docker-compose down
docker-compose up -d app:v1.0.0
```

## Cost Optimization

### Supabase
- Free tier: Good for development and small apps
- Pro tier ($25/mo): Production apps
- Pay-as-you-go: Scale only what you need

### Hosting Platform
- Railway: Free tier → $5/mo
- Render: Free tier → $7/mo
- Fly.io: Pay per resource usage

### Tips
1. Use free tier for development
2. Enable auto-pause for inactive apps
3. Monitor resource usage
4. Optimize database queries
5. Use caching to reduce database calls

## Support Resources

- [Railway Discord](https://discord.gg/railway)
- [Render Community](https://community.render.com)
- [Fly.io Community](https://community.fly.io)
- [Supabase Discord](https://discord.supabase.com)
- [FastAPI Discord](https://discord.com/invite/VQjSZaeJmf)

Good luck with your deployment! 🚀
