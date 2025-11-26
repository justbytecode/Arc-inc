# Environment Configuration Guide

## Quick Setup

To get started with your local development environment, follow these steps:

### 1. Copy the example file
```bash
cp .env.example .env
```

### 2. Edit the `.env` file with your settings

**Important fields you MUST customize:**

```bash
# 🔐 SECURITY - CHANGE THESE!
SECRET_KEY=your-random-secret-key-here-min-32-chars
AUTH_TOKEN=your-auth-token-for-api-access
```

**How to generate secure keys:**

```bash
# For SECRET_KEY (32+ random characters)
# Option 1: Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -base64 32

# For AUTH_TOKEN (demo token for testing)
# Use anything memorable for local dev, e.g.: my-local-dev-token-12345
```

### 3. Database Configuration (for local development with Docker)

The default values work with docker-compose, **no changes needed** for local dev:

```bash
DATABASE_URL=postgresql://csvuser:csvpassword@postgres:5432/csvimport
REDIS_URL=redis://redis:6379/0
```

**⚠️ For production deployment**, change these to your actual database credentials!

### 4. Upload Directory

Create the upload directory (Docker will auto-create, but for local testing):

```bash
mkdir -p uploads
```

Or on Windows:
```powershell
New-Item -ItemType Directory -Force -Path uploads
```

---

## Complete `.env` File Template

Here's a fully annotated template:

```bash
# ============================================
# DATABASE CONFIGURATION
# ============================================
# For Docker: use service name "postgres"
# For local: use "localhost"
DATABASE_URL=postgresql://csvuser:csvpassword@postgres:5432/csvimport

# ============================================
# REDIS CONFIGURATION
# ============================================
# For Docker: use service name "redis"
# For local: use "localhost"
REDIS_URL=redis://redis:6379/0

# ============================================
# SECURITY (⚠️ CHANGE FOR PRODUCTION!)
# ============================================
# SECRET_KEY: Used for session encryption and security
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=change-this-in-production-to-a-random-secret

# AUTH_TOKEN: Simple bearer token for API authentication
# Use a strong random token for production
# For local dev, use something memorable
AUTH_TOKEN=demo-auth-token-12345

# ============================================
# APPLICATION SETTINGS
# ============================================
ENVIRONMENT=development
DEBUG=true

# ============================================
# CSV IMPORT SETTINGS
# ============================================
# BATCH_SIZE: Rows processed per database transaction
# Larger = faster but more memory. 1000 is a good balance.
# For 500k rows: 1000 batch → ~500 transactions
BATCH_SIZE=1000

# MAX_ERROR_SAMPLES: How many errors to store in import log
# Prevents huge error logs from filling database
MAX_ERROR_SAMPLES=100

# ============================================
# WEBHOOK SETTINGS
# ============================================
# WEBHOOK_TIMEOUT: HTTP request timeout in seconds
WEBHOOK_TIMEOUT=30

# WEBHOOK_MAX_RETRIES: Number of delivery attempts before giving up
WEBHOOK_MAX_RETRIES=5

# Retry delays are hardcoded in config.py as exponential backoff:
# [60s, 5min, 15min, 1hour, 2hours]

# ============================================
# FILE UPLOAD SETTINGS
# ============================================
# MAX_UPLOAD_SIZE: Maximum file size in bytes (500MB default)
MAX_UPLOAD_SIZE=524288000

# UPLOAD_DIR: Where uploaded CSV files are temporarily stored
# Docker: use /app/uploads
# Local: use ./uploads
UPLOAD_DIR=/app/uploads
```

---

## Using Your `.env` File

### With Docker (Recommended)

```bash
# 1. Make sure .env exists in the project root
# 2. Start services
docker-compose up -d

# 3. Run migrations
docker-compose exec web alembic upgrade head

# 4. Access the app
# http://localhost:8000
```

### Without Docker (Local Development)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Update .env for localhost
# Change "postgres" → "localhost" in DATABASE_URL
# Change "redis" → "localhost" in REDIS_URL

# 4. Make sure PostgreSQL and Redis are running locally

# 5. Run migrations
alembic upgrade head

# 6. Start web server
uvicorn app.main:app --reload

# 7. In another terminal, start Celery worker
celery -A app.worker worker --loglevel=info
```

---

## Frontend Configuration

The frontend needs to know the API URL. Update `/static/js/config.js`:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',  // Change for production
    AUTH_TOKEN: 'demo-auth-token-12345',     // Must match .env AUTH_TOKEN
    SSE_RECONNECT_INTERVAL: 3000
};
```

**⚠️ Important:** The `AUTH_TOKEN` in `config.js` **must match** the `AUTH_TOKEN` in your `.env` file!

---

## Production Deployment Notes

When deploying to production (Render, Railway, Heroku, etc.):

1. **Generate strong secrets:**
   ```bash
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
   python -c "import secrets; print('AUTH_TOKEN=' + secrets.token_urlsafe(32))"
   ```

2. **Use environment variables** provided by your hosting platform for DATABASE_URL

3. **Set ENVIRONMENT=production** and **DEBUG=false**

4. **Update frontend config.js** to point to your production API URL

5. **Enable HTTPS** (most platforms do this automatically)

---

## Troubleshooting

**Q: "Connection refused" errors?**
- Check if PostgreSQL and Redis are running
- Verify DATABASE_URL and REDIS_URL are correct for your setup (localhost vs service names)

**Q: "401 Unauthorized" errors?**
- Make sure AUTH_TOKEN in `.env` matches `config.js`
- Check if Authorization header is being sent

**Q: Celery worker not processing jobs?**
- Ensure Celery worker is running: `celery -A app.worker worker --loglevel=info`
- Check Redis connection
- Look for errors in worker logs

**Q: Upload directory errors?**
- Create the directory: `mkdir -p uploads` or `New-Item -ItemType Directory -Force -Path uploads`
- Check UPLOAD_DIR path in `.env` matches your system
