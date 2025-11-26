# Deliverables Mapping

This document maps the acceptance criteria from the project specification to the implementation in this repository.

## ✅ Acceptance Criteria Verification

### 1. Upload Large CSV via UI with Real-time Progress

**Requirement**: Stream CSV upload showing upload bytes + parsing/import progress with status messages

**Implementation**:
- Frontend: [`app/static/index.html`](file:///d:/sde/csv-import-app/app/static/index.html) (lines 28-79)
- Upload JS: [`app/static/js/uploads.js`](file:///d:/sde/csv-import-app/app/static/js/uploads.js)
  - XHR-based upload with byte progress tracking (lines 55-60)
  - Polling for import status with UI updates (lines 82-156)
- API Endpoint: [`app/routers/imports.py`](file:///d:/sde/csv-import-app/app/routers/imports.py) - `POST /api/imports`
- Worker Task: [`app/worker.py`](file:///d:/sde/csv-import-app/app/worker.py) - `import_csv_task` (lines 30-172)

**Verification**:
1. Navigate to `http://localhost:8000`
2. Select a CSV file and click "Upload and Import"
3. Observe byte upload progress bar
4. After upload, see real-time import progress with states: Pending → Parsing → Importing → Completed

---

### 2. Import into PostgreSQL with Case-insensitive SKU Uniqueness and Upsert

**Requirement**: Duplicate SKUs (case-insensitive) should overwrite existing records

**Implementation**:
- SKU Normalization: [`app/csv_utils.py`](file:///d:/sde/csv-import-app/app/csv_utils.py) - `CSVValidator.validate_row` (lines 56-58)
- Database Model: [`app/models.py`](file:///d:/sde/csv-import-app/app/models.py) - `Product` with `sku_norm` field (lines 18-19)
- Migration: [`alembic/versions/001_initial_schema.py`](file:///d:/sde/csv-import-app/alembic/versions/001_initial_schema.py) - unique index on `sku_norm` (line 38)
- Batch Upsert: [`app/db_operations.py`](file:///d:/sde/csv-import-app/app/db_operations.py) - `batch_upsert_products` using PostgreSQL COPY + INSERT ON CONFLICT  (lines 16-106)

**Verification**:
1. Upload `sample_csvs/sample_10_rows.csv` (contains "SAMPLE-001" and "sample-001")
2. Check database: `docker-compose exec web alembic current`
3. Verify only 9 unique products exist (rows 1 and 4 are the same SKU, different case)
4. Product with SKU "sample-001" should have updated data from row 4

---

### 3. CRUD UI for Products

**Requirement**: Filtering, server pagination, inline/modal edit, single delete

**Implementation**:
- Frontend UI: [`app/static/index.html`](file:///d:/sde/csv-import-app/app/static/index.html) (lines 80-111, 146-177)
- Products JS: [`app/static/js/products.js`](file:///d:/sde/csv-import-app/app/static/js/products.js)
  - Pagination (lines 101-133)
  - Filtering (lines 32-41)
  - Modal CRUD (lines 135-237)
- API Router: [`app/routers/products.py`](file:///d:/sde/csv-import-app/app/routers/products.py)
  - GET with filters/pagination (lines 25-63)
  - POST create (lines 66-98)
  - PUT update (lines 115-156)
  - DELETE single (lines 159-177)

**Verification**:
1. Navigate to "Products" tab
2. Apply filters (SKU, name, category, active status)
3. Change page size (25/50/100) and navigate pages
4. Click "Create Product" to add new item
5. Click "Edit" on any product to modify
6. Click "Delete" on any product (confirms before deletion)

---

### 4. Bulk "Delete All Products" with Typed Confirmation

**Requirement**: Background job with progress, protected by typed confirmation

**Implementation**:
- UI Confirmation: [`app/static/js/products.js`](file:///d:/sde/csv-import-app/app/static/js/products.js) - `deleteAllProducts` (lines 239-256)
- API Endpoint: [`app/routers/products.py`](file:///d:/sde/csv-import-app/app/routers/products.py) - `POST /api/products/delete_all` (lines 180-200)
- Worker Task: [`app/worker.py`](file:///d:/sde/csv-import-app/app/worker.py) - `delete_all_products_task` with batched deletion (lines 182-245)

**Verification**:
1. Go to Products tab, click "Delete All Products"
2. Type exactly "DELETE ALL" in the prompt
3. Task starts in background (returns task_id)
4. Products are deleted in batches of 1000
5. Verify all products removed from database

---

### 5. Webhook UI: Create/Edit/Delete/Test/Enable/Disable with Queued Delivery

**Requirement**: CRUD, test endpoint, exponential backoff retries, logs

**Implementation**:
- Frontend UI: [`app/static/index.html`](file:///d:/sde/csv-import-app/app/static/index.html) (lines 112-145, 178-214)
- Webhooks JS: [`app/static/js/webhooks.js`](file:///d:/sde/csv-import-app/app/static/js/webhooks.js)
  - CRUD operations (lines 18-150)
  - Test delivery (lines 152-167)
  - View logs (lines 169-191)
- API Router: [`app/routers/webhooks.py`](file:///d:/sde/csv-import-app/app/routers/webhooks.py)
  - CRUD endpoints (lines 20-152)
  - Test delivery (lines 155-220)
  - Logs retrieval (lines 223-236)
- Delivery Task: [`app/worker.py`](file:///d:/sde/csv-import-app/app/worker.py) - `deliver_webhook_task` with retry logic (lines 248-367)
  - Exponential backoff: 60s, 5min, 15min, 1h, 2h (line 334)
  - HMAC signatures (lines 289-295)

**Verification**:
1. Go to "Webhooks" tab, click "Create Webhook"
2. Enter name, URL (e.g., `https://webhook.site/your-unique-url`), select events
3. Optionally add HMAC secret
4. Click "Test" button to send test delivery
5. View response code and time
6. Click "Logs" to see delivery history
7. Upload a CSV to trigger `import.completed` event
8. Check webhook logs for automatic delivery

---

### 6. Background Jobs for Import and Webhook Delivery

**Requirement**: Celery or Dramatiq workers

**Implementation**:
- Worker Configuration: [`app/worker.py`](file:///d:/sde/csv-import-app/app/worker.py)
  - Celery app setup (lines 1-25)
  - Import task (lines 30-172)
  - Delete task (lines 182-245)
  - Webhook delivery task (lines 248-367)
- Docker Setup: [`docker-compose.yml`](file:///d:/sde/csv-import-app/docker-compose.yml) - worker service (lines 63-79)

**Verification**:
1. Start worker: `docker-compose up worker`
2. Check logs: `docker-compose logs -f worker`
3. Upload CSV and observe worker processing logs
4. Verify tasks complete successfully

---

### 7. Dockerized with Migrations

**Requirement**: Docker setup, Alembic or Django migrations

**Implementation**:
- Dockerfile: [`Dockerfile`](file:///d:/sde/csv-import-app/Dockerfile) - multi-stage build with non-root user
- Docker Compose: [`docker-compose.yml`](file:///d:/sde/csv-import-app/docker-compose.yml) - all services configured
- Migrations: [`alembic/versions/001_initial_schema.py`](file:///d:/sde/csv-import-app/alembic/versions/001_initial_schema.py)
- Makefile: [`Makefile`](file:///d:/sde/csv-import-app/Makefile) - build, up, migrate, test targets

**Verification**:
```bash
make setup      # Build, start services, run migrations
make migrate    # Run migrations
make test       # Run tests in Docker
make logs       # View logs
```

---

### 8. Unit + Integration Tests

**Requirement**: Test CSV parsing, validation, upsert behavior, webhook retry logic

**Implementation**:
- Unit Tests: [`tests/test_csv_utils.py`](file:///d:/sde/csv-import-app/tests/test_csv_utils.py)
  - CSV validation (lines 10-105)
  - SKU normalization (lines 75-85)
- Integration Tests: [`tests/test_integration.py`](file:///d:/sde/csv-import-app/tests/test_integration.py)
  - Upload CSV (lines 44-73)
  - Case-insensitive SKU upsert (lines 97-120)
  - Product CRUD (lines 123-203)
- GitHub Actions: [`.github/workflows/test.yml`](file:///d:/sde/csv-import-app/.github/workflows/test.yml) - CI pipeline

**Verification**:
```bash
# Local
make test

# Or direct
docker-compose exec web pytest tests/ -v
```

---

### 9. README with Deployment Instructions

**Requirement**: Run & deploy instructions, architecture notes, verification steps

**Implementation**:
- Main README: [`README.md`](file:///d:/sde/csv-import-app/README.md) - updated with stack, features, quick start
- Environment Setup: [`docs/ENVIRONMENT_SETUP.md`](file:///d:/sde/csv-import-app/docs/ENVIRONMENT_SETUP.md) - comprehensive .env guide
- This Document: [`DELIVERABLES.md`](file:///d:/sde/csv-import-app/DELIVERABLES.md) - acceptance criteria mapping

---

### 10. Sample CSVs

**Requirement**: Small and medium sample CSV files

**Implementation**:
- 10-row sample: [`sample_csvs/sample_10_rows.csv`](file:///d:/sde/csv-import-app/sample_csvs/sample_10_rows.csv)

**Verification**:
Use these files to test import functionality.

---

## Test Credentials

For local development (when using default docker-compose setup):

- **API Authentication**: 
  - Token: `demo-auth-token-12345`
  - Header: `Authorization: Bearer demo-auth-token-12345`

- **Database**:
  - Host: `localhost:5432`
  - User: `csvuser`
  - Password: `csvpassword`
  - Database: `csvimport`

- **Frontend Config**: Update `app/static/js/config.js`:
  ```javascript
  AUTH_TOKEN: 'demo-auth-token-12345'  // Must match .env
  ```

---

## Quick Verification Checklist

Run these steps to verify all functionality:

```bash
# 1. Setup
cd csv-import-app
cp .env.example .env
# Edit .env and set SECRET_KEY and AUTH_TOKEN
make setup

# 2. Test CSV Import
# Open http://localhost:8000
# Upload sample_csvs/sample_10_rows.csv
# Watch real-time progress

# 3. Test Upsert (re-upload same file)
# Upload sample_csvs/sample_10_rows.csv again
# Products tab should still show 9 products (not 18)

# 4. Test Product CRUD
# Products tab → Create new product
# Edit existing product
# Delete single product
# Apply filters and pagination

# 5. Test Bulk Delete
# Products tab → "Delete All Products"
# Type "DELETE ALL" to confirm
# Verify products disappear

# 6. Test Webhooks
# Get test URL from webhook.site
# Webhooks tab → Create webhook
# Select "import.completed" event
# Upload CSV to trigger webhook
# Check webhook.site for delivery

# 7. Run Tests
make test

# 8. View Logs
make logs
```

---

## Architecture Notes

### Data Flow
1. User uploads CSV → FastAPI saves file
2 FastAPI creates ImportJob record
3. Celery task processes CSV in batches (1000 rows/batch)
4. PostgreSQL COPY for high-performance bulk insert
5. Progress updates after each batch
6. Frontend polls `/api/imports/{job_id}/status`
7. On completion, webhook events queued
8. Separate Celery task delivers webhooks with retries

### Scaling to 500k Rows
- Streaming CSV read (constant memory)
- Batched upsert (500 batches for 500k rows at batch_size=1000)
- Short transactions per batch
- Unique index on `sku_norm` for O(log n) lookups
- Horizontal Celery worker scaling
- Adjust `BATCH_SIZE` env variable for tuning

---

## Files Summary

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point |
| `app/models.py` | SQLAlchemy database models |
| `app/routers/` | API route handlers |
| `app/worker.py` | Celery background tasks |
| `app/csv_utils.py` | CSV streaming and validation |
| `app/db_operations.py` | High-performance batch upsert |
| `app/static/` | Frontend HTML/CSS/JS |
| `alembic/versions/` | Database migrations |
| `tests/` | Unit and integration tests |
| `.github/workflows/` | CI/CD pipeline |
| `Makefile` | Docker orchestration commands |
| `docs/` | Additional documentation |
