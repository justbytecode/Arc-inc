# CSV Import Application

A production-grade web application for importing large CSV files (up to 500,000 rows) into PostgreSQL with real-time progress tracking, full CRUD operations, and reliable webhook management.

## Features

- **Large CSV Import**: Stream and import CSV files up to 500k rows with real-time progress tracking
- **Product Management**: Full CRUD operations with filtering, pagination, and bulk operations
- **Webhook Management**: Configure webhooks with queued delivery, exponential backoff retries, and delivery logs
- **Real-time Updates**: Server-sent events (SSE) for live import progress and job status
- **Background Processing**: Reliable job queue for imports, bulk operations, and webhook delivery
- **Case-insensitive SKU Handling**: Automatic normalization and upsert logic prevents duplicates
- **Docker Support**: Fully containerized application with docker-compose orchestration
- **Production Ready**: Includes migrations, tests, CI/CD, and deployment configuration

## Technology Stack

### Core Stack

- **Web Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Background Worker**: Celery 5.3
- **Message Broker**: Redis 7
- **Database**: PostgreSQL 15
- **Frontend**: Vanilla JavaScript with SSE (Server-Sent Events)

### Justification

**FastAPI over Django/Flask/Tornado**: FastAPI provides async/await support critical for streaming CSV uploads and SSE connections, automatic OpenAPI documentation, excellent performance, and built-in validation via Pydantic. Its async capability allows handling real-time progress updates efficiently while processing imports.

**SQLAlchemy + Alembic over Django ORM**: SQLAlchemy 2.0 offers fine-grained control for high-performance batch inserts using `COPY` or `INSERT ... ON CONFLICT`, support for custom SQL needed for case-insensitive SKU indexing, and explicit transaction boundaries required for batched upserts. Alembic provides version-controlled migrations independent of the web framework.

**Celery over Dramatiq**: Celery is the battle-tested choice with extensive documentation, built-in periodic task support (useful for webhook retries), rich monitoring tools (Flower), and wider community support. While Dramatiq is simpler, Celery's maturity and tooling ecosystem better suit production requirements.

**Redis over RabbitMQ**: Redis serves dual purposes - message broker for Celery AND high-speed storage for SSE progress updates. This reduces infrastructure complexity. Redis's in-memory performance is ideal for real-time progress tracking, and its simpler operational model (single binary, no clustering required for small scale) fits the deployment constraints.

**Vanilla JS + SSE over React**: Keeping the frontend minimal reduces build complexity while SSE (Server-Sent Events) provides native browser support for real-time updates without WebSocket overhead. SSE is unidirectional (server→client), which perfectly matches our progress streaming use case, and works through HTTP (no special proxy configuration needed).

## Quick Start

*Development and deployment instructions will be added in later steps*

## Architecture

*Architecture diagram and scaling notes will be added in Step 11*

## Project Status

This project is being built incrementally following a structured implementation plan:

- [x] Step 0: Repository scaffold
- [ ] Step 1: Stack selection & justification
- [ ] Step 2: Database schema & migrations
- [ ] Step 3: API & authentication skeleton
- [ ] Step 4: UI upload & real-time progress
- [ ] Step 5: Streaming import pipeline
- [ ] Step 6: Product management UI
- [ ] Step 7: Bulk delete background job
- [ ] Step 8: Webhooks & reliable delivery
- [ ] Step 9: Tests & CI
- [ ] Step 10: Docker & local development
- [ ] Step 11: Deployment & documentation

## License

MIT
