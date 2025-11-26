# Local Development Setup (Windows)

## Prerequisites

- Python 3.11+ installed
- PostgreSQL 15+ (local or cloud)
- Upstash Redis (free cloud account)

---

## Step 1: Setup Upstash Redis (Free)

### 1.1 Create Upstash Account
- Go to: https://upstash.com/
- Click "Sign Up" (free tier - no credit card required)
- Sign up with GitHub, Google, or Email

### 1.2 Create Redis Database
1. After signing in, click "Create Database"
2. Choose:
   - **Name**: csv-import-redis
   - **Region**: Choose closest to you (e.g., AWS US-East-1)
   - **Type**: Regional (free tier)
3. Click "Create"

### 1.3 Get Redis URL
1. Click on your database
2. Scroll down to "REST API" section
3. Copy the **Redis URL** that looks like:
   ```
   redis://default:YOUR_PASSWORD@lovely-snail-12345.upstash.io:6379
   ```
4. **Save this URL** - you'll need it for your `.env` file

---

## Step 2: Setup PostgreSQL

### Option A: Local PostgreSQL (Recommended if you have it)
1. Download from: https://www.postgresql.org/download/windows/
2. Install with defaults
3. Remember the password you set for `postgres` user
4. Your database URL will be:
   ```
   postgresql://postgres:YOUR_PASSWORD@localhost:5432/csvimport
   ```

### Option B: Free Cloud PostgreSQL (Neon - No installation needed)
1. Go to: https://neon.tech/
2. Sign up (free tier - no credit card)
3. Create a new project named "csv-import"
4. Copy the connection string (looks like):
   ```
   postgresql://user:password@ep-cool-cloud-123456.us-east-2.aws.neon.tech/neondb
   ```

---

## Step 3: Configure Environment

### 3.1 Update `.env` File

Open `d:\sde\csv-import-app\.env` and update:

```bash
# Database - Use your PostgreSQL connection string
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/csvimport
# OR if using Neon:
# DATABASE_URL=postgresql://user:password@ep-cool-cloud-123456.us-east-2.aws.neon.tech/neondb

# Redis - Use your Upstash Redis URL
REDIS_URL=redis://default:YOUR_PASSWORD@lovely-snail-12345.upstash.io:6379

# Security (already configured)
SECRET_KEY=<your-existing-secret-key>
AUTH_TOKEN=60Y_XquaW4TnJxUL70AjhJd_EUGANNqjeA_1XCZP5hI

# Application
ENVIRONMENT=development
DEBUG=true

# Import settings
BATCH_SIZE=1000
MAX_ERROR_SAMPLES=100

# Webhook settings
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=5

# File upload
MAX_UPLOAD_SIZE=524288000
UPLOAD_DIR=./uploads
```

### 3.2 Create Database (if using local PostgreSQL)

```powershell
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE csvimport;

# Exit
\q
```

---

## Step 4: Setup Python Environment

```powershell
# Navigate to project
cd d:\sde\csv-import-app

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Initialize Database

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Run migrations
alembic upgrade head
```

---

## Step 6: Create Upload Directory

```powershell
# Create uploads folder
New-Item -ItemType Directory -Force -Path uploads
```

---

## Step 7: Start the Application

### Terminal 1: Web Server
```powershell
# Activate venv
.\venv\Scripts\activate

# Start web server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Celery Worker
```powershell
# Activate venv
.\venv\Scripts\activate

# Start Celery worker
celery -A app.worker worker --loglevel=info --pool=solo
```

**Note**: `--pool=solo` is required for Windows since Celery doesn't support the default pool on Windows.

---

## Step 8: Access the Application

Open your browser to: **http://localhost:8000**

---

## Troubleshooting

### Issue: "psycopg2" installation fails
If you get errors installing psycopg2-binary, try:
```powershell
pip install psycopg2-binary --no-cache-dir
```

### Issue: Celery won't start on Windows
Make sure you're using `--pool=solo`:
```powershell
celery -A app.worker worker --loglevel=info --pool=solo
```

### Issue: Can't connect to database
- Check your DATABASE_URL in `.env`
- If using local PostgreSQL, make sure the service is running
- If using Neon, check your internet connection

### Issue: Can't connect to Redis
- Verify your Upstash Redis URL in `.env`
- Check that you copied the full URL including the password
- Ensure your internet connection is working

---

## Verification Steps

1. **Check web server**: http://localhost:8000 should show the UI
2. **Check API docs**: http://localhost:8000/docs
3. **Upload test CSV**: Use `sample_csvs\sample_10_rows.csv`
4. **Check Celery logs**: You should see the worker processing the import
5. **Check Upstash Dashboard**: You should see Redis commands being executed

---

## Quick Commands Reference

```powershell
# Activate environment
.\venv\Scripts\activate

# Start web server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start worker (in separate terminal)
celery -A app.worker worker --loglevel=info --pool=solo

# Run migrations
alembic upgrade head

# Run tests
pytest tests/ -v

# Deactivate environment
deactivate
```

---

## Next Steps

Once both the web server and worker are running:
1. Open http://localhost:8000
2. Go to "Upload CSV" tab
3. Upload `sample_csvs\sample_10_rows.csv`
4. Watch the Celery worker terminal for processing logs
5. See the imported products in the "Products" tab

🎉 **You're all set!**
