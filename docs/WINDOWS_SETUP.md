# Windows Quick Start Guide

Since you're on Windows without `make`, use these Docker Compose commands directly:

## 🚀 Quick Setup (Windows)

### 1. Build and Start Services

```powershell
# Build images
docker-compose build

# Start all services (web, worker, postgres, redis)
docker-compose up -d

# Wait a few seconds for services to be ready
Start-Sleep -Seconds 10

# Run database migrations
docker-compose exec web alembic upgrade head
```

### 2. Access the Application

Open your browser to: **http://localhost:8000**

### 3. Common Commands

```powershell
# View logs (all services)
docker-compose logs -f

# View web server logs only
docker-compose logs -f web

# View worker logs only
docker-compose logs -f worker

# Stop services
docker-compose down

# Restart everything
docker-compose down
docker-compose build
docker-compose up -d
Start-Sleep -Seconds 10
docker-compose exec web alembic upgrade head

# Run tests
docker-compose exec web pytest tests/ -v

# Open shell in web container
docker-compose exec web /bin/bash

# Clean up (remove containers and volumes)
docker-compose down -v
```

## 🔧 Troubleshooting

### Issue: Services won't start
```powershell
# Check if ports are already in use
netstat -ano | findstr :8000
netstat -ano | findstr :5432
netstat -ano | findstr :6379

# Stop any conflicting services
docker-compose down
```

### Issue: "Connection refused" errors
```powershell
# Make sure services are healthy
docker-compose ps

# Check logs for errors
docker-compose logs web
docker-compose logs postgres
docker-compose logs redis
```

### Issue: Database migration fails
```powershell
# Wait longer for postgres to be ready
Start-Sleep -Seconds 15
docker-compose exec web alembic upgrade head
```

## 📊 Verify Everything Works

```powershell
# 1. Check all services are running
docker-compose ps
# Expected: All services should be "Up" and healthy

# 2. Check web server is responding
# Open http://localhost:8000 in browser

# 3. Check API docs
# Open http://localhost:8000/docs in browser

# 4. Run tests
docker-compose exec web pytest tests/ -v
```

## 🎯 First Upload Test

1. Open http://localhost:8000
2. Go to "Upload CSV" tab
3. Click "Choose File" and select `sample_csvs\sample_10_rows.csv`
4. Click "Upload and Import"
5. Watch the progress bars!
6. Go to "Products" tab to see imported products

## 📝 Your Configuration

Your `.env` file should have:
```
AUTH_TOKEN=60Y_XquaW4TnJxUL70AjhJd_EUGANNqjeA_1XCZP5hI
SECRET_KEY=<your-generated-secret-key>
```

Your `app/static/js/config.js` has:
```javascript
AUTH_TOKEN: '60Y_XquaW4TnJxUL70AjhJd_EUGANNqjeA_1XCZP5hI'
```

✅ These match - perfect!

## 🆘 Need Help?

Check logs for errors:
```powershell
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f postgres
```
