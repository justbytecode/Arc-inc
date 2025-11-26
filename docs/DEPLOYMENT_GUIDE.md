# Deployment Guide

This application consists of two main components:
1. **Web API** (FastAPI)
2. **Background Worker** (Celery)

To fully function (especially for CSV imports and bulk deletes), **BOTH** components must be running.

---

## ⚠️ Important Note on Vercel

**Vercel is NOT recommended for this full application.**

Vercel is a "Serverless" platform. It shuts down processes immediately after a request finishes.
- **What works:** The API endpoints (listing products, viewing webhooks).
- **What FAILS:** The Background Worker.
  - When you upload a CSV, the API queues a job.
  - **No worker is running** to pick up that job.
  - The import will stay "Pending" forever.

### If you must use Vercel:
You can deploy the **API** to Vercel, but you must host the **Worker** somewhere else (like a VPS, Heroku, or Render) and connect them to the same Redis/Database.

---

## ✅ Recommended: Render.com (Free Tier Available)

Render allows you to run both the Web Service and the Background Worker in the same project.

### 1. Create a `render.yaml` (Blueprint)
Create a file named `render.yaml` in your repository root:

```yaml
services:
  # 1. The Web API
  - type: web
    name: csv-import-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: csv-import-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: csv-import-redis
          property: connectionString

  # 2. The Celery Worker
  - type: worker
    name: csv-import-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.worker.celery_app worker --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: csv-import-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: csv-import-redis
          property: connectionString

databases:
  - name: csv-import-db
    databaseName: csv_db
    user: csv_user

services:
  - type: redis
    name: csv-import-redis
    ipAllowList: [] # Allow internal connections
```

### 2. Deploy
1. Push your code to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Connect your repository.
5. Render will automatically create the Web Service, Worker, Database, and Redis.

---

## 🚀 How to Deploy to Vercel (API Only)

If you only want to show the UI/API (without working imports):

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```
   - Follow the prompts (link to existing project? No. Project name? csv-import-app).
   - It will detect `vercel.json` and deploy.

4. **Environment Variables**:
   - Go to the Vercel Dashboard -> Settings -> Environment Variables.
   - Add `DATABASE_URL` (from Neon/Postgres).
   - Add `REDIS_URL` (from Upstash/Redis).

**Result**: The site will load, you can view products, but **Uploads will hang** because no worker is processing them.
