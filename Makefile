.PHONY: build up down migrate test shell worker logs clean

# Build Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Run database migrations
migrate:
	docker-compose exec web alembic upgrade head

# Create a new migration
migration:
	docker-compose exec web alembic revision --autogenerate -m "$(MESSAGE)"

# Run tests
test:
	docker-compose exec web pytest tests/ -v

# Open shell in web container
shell:
	docker-compose exec web /bin/bash

# Start Celery worker (for debugging)
worker:
	docker-compose exec worker celery -A app.worker worker --loglevel=info

# View logs
logs:
	docker-compose logs -f

# View web logs only
logs-web:
	docker-compose logs -f web

# View worker logs only
logs-worker:
	docker-compose logs -f worker

# Clean up all containers and volumes
clean:
	docker-compose down -v
	rm -rf postgres-data/

# Full restart (down, build, up, migrate)
restart: down build up migrate

# Setup for first time (build, up, migrate)
setup: build up
	@echo "Waiting for services to be ready..."
	@sleep 5
	@make migrate
	@echo "Setup complete! Access the app at http://localhost:8000"

# Help
help:
	@echo "CSV Import Application - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup      - First-time setup (build, start, migrate)"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make migrate    - Run database migrations"
	@echo ""
	@echo "Development:"
	@echo "  make shell      - Open shell in web container"
	@echo "  make worker     - Start Celery worker"
	@echo "  make logs       - View all logs"
	@echo "  make logs-web   - View web server logs"
	@echo "  make logs-worker - View worker logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run tests"
	@echo ""
	@echo "Maintenance:"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Full restart"
	@echo "  make clean      - Stop and remove all containers/volumes"
