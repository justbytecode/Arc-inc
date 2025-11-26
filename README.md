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

*Stack selection and justification will be added in Step 1*

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
