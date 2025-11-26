# 🚀 Hosting on Render.com (From Scratch)

This guide will take you from your local code to a fully deployed application on Render.com with a Database and Background Worker.

## Prerequisites
- A [GitHub](https://github.com) account.
- A [Render.com](https://render.com) account.

---

## Step 1: Push Code to GitHub
Render needs to pull your code from a GitHub repository.

1. **Create a New Repository** on GitHub (e.g., `csv-import-app`).
2. **Push your local code** to this repository.
   *(If you haven't done this yet, run these commands in your terminal)*:
   ```bash
   # Initialize git if not already done
   git init
   git add .
   git commit -m "Ready for deployment"
   
   # Link to your new GitHub repo (replace URL with YOUR repo URL)
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/csv-import-app.git
   git push -u origin main
   ```

---

## Step 2: Deploy using Blueprint (The Easy Way)
We have created a `render.yaml` file in your project. This file tells Render exactly what to build (Web API, Worker, Database, Redis).

1. **Login to Render Dashboard**: [https://dashboard.render.com](https://dashboard.render.com)
2. Click **New +** and select **Blueprint**.
3. Connect your **GitHub account** and select the repository you just pushed (`csv-import-app`).
4. **Service Group Name**: Enter a name like `csv-import-production`.
5. **Apply**: Click "Apply Blueprint".

Render will now automatically:
- ✅ Create a PostgreSQL Database (`csv-import-db`)
- ✅ Create a Redis instance (`csv-import-redis`)
- ✅ Build and Deploy the Web API (`csv-import-api`)
- ✅ Build and Deploy the Celery Worker (`csv-import-worker`)

---

## Step 3: Verify Deployment
Once the deployment finishes (it may take 2-3 minutes):

1. Go to the **Dashboard**.
2. Click on the **csv-import-api** service.
3. Find the **URL** (e.g., `https://csv-import-api.onrender.com`).
4. Open that URL in your browser. You should see the CSV Import App!

---

## Step 4: Troubleshooting
If something goes wrong:

- **Logs**: Click on the specific service (e.g., `csv-import-worker`) and click "Logs" to see what's happening.
- **Database Migrations**: Render usually runs the app, but if tables are missing, you might need to run migrations.
  - In the Render Dashboard, go to `csv-import-api` -> **Shell**.
  - Run: `alembic upgrade head`

---

## 🧹 Cleanup (Optional)
Since you are deploying to the cloud, you can delete these local development files from your computer if you wish:
- `setup_git.bat`
- `deploy_to_github.bat`
- `fix_redis_ssl.py`
- `start_worker.bat`
- `start_web.bat`
