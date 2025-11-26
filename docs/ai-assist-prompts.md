# AI-Assisted Development Prompts

This document tracks the AI assistance used during the development of this project.

## Initial Project Setup

### Prompt 1: Project Scaffold (Step 0)
**Date**: 2025-11-26

**Prompt Summary**: Build a complete production-minded web application that imports large CSV files (up to ~500,000 rows) into PostgreSQL, with real-time upload/import progress in the UI, full product CRUD, bulk delete, webhook management with queued reliable delivery and retries, Dockerized setup, tests and migrations, and public deployment.

**Context**: This is a comprehensive assignment-style project with 11 defined implementation steps, requiring specific technology choices (FastAPI/Django, SQLAlchemy/Alembic, Celery/Dramatiq, Redis/RabbitMQ, PostgreSQL) and explicit acceptance criteria.

**AI Tool**: Claude (Antigravity)

**Outcome**: Repository skeleton created with:
- Project structure (/app, /tests, /docs)
- README.md with project overview
- .gitignore for Python/Docker/Node.js
- Dockerfile with multi-stage build
- docker-compose.yml with postgres, redis, web, worker services
- Basic FastAPI application entry point
- Test configuration with fixtures
- This documentation file

## Technology Stack Decisions (Step 1)

### Decision Rationale
**Date**: 2025-11-26

**Selected Stack**:
- Web Framework: FastAPI 0.104+
- ORM: SQLAlchemy 2.0 + Alembic
- Background Worker: Celery 5.3
- Message Broker & Cache: Redis 7
- Database: PostgreSQL 15
- Frontend: Vanilla JavaScript with SSE (Server-Sent Events)

**Key Justifications**:

1. **FastAPI**: Chosen for async/await support essential for streaming CSV uploads and SSE connections. The async capability allows concurrent handling of file uploads while sending real-time progress updates to the UI.

2. **SQLAlchemy + Alembic**: Selected for fine-grained control over batch inserts (using `COPY` to temp table + `INSERT ... ON CONFLICT` for upsert). SQLAlchemy 2.0's explicit transaction control is critical for batched commits (1000 rows per batch) to avoid long-running transactions.

3. **Celery**: Preferred over Dramatiq for its mature ecosystem, built-in task scheduling (needed for webhook retry backoff), and monitoring tools (Flower). Production-grade reliability is prioritized over simplicity.

4. **Redis**: Serves dual purpose - Celery broker AND real-time progress cache for SSE updates. This architectural choice reduces infrastructure complexity while providing in-memory performance for progress tracking.

5. **Vanilla JS + SSE**: Avoided React/build tooling to keep frontend simple. SSE is ideal for unidirectional server→client progress updates, works over HTTP (no proxy issues), and has native browser support.

**Tradeoffs Considered**:
- WebSocket vs SSE: SSE chosen because it's simpler, HTTP-based, and sufficient for one-way progress streaming
- Celery vs Dramatiq: Celery chosen for production tooling despite higher complexity
- React vs Vanilla JS: Vanilla chosen to match "minimal frontend" requirement and avoid build step

---

**Note**: This file serves as a transparent record of AI assistance in this project, documenting prompts, decisions, and outcomes to maintain clarity and reproducibility.
