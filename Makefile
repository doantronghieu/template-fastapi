# FastAPI Template - Development Operations
# Quick Start: make setup → cp .env.example .env → make infra-up → make db-migrate message="init" → make db-upgrade → make dev

# Load environment variables from .env file (similar to docker-compose env_file)
# The '-' prefix means don't fail if .env doesn't exist
-include .env
export

.PHONY: help setup dev celery celery-kill flower ngrok test lint format clean db-migrate db-upgrade db-downgrade db-reset db-seed infra-up infra-down infra-reset infra-logs docker-build app-build app-up app-down app-restart app-logs client-generate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | sed 's/:.*##/ /' | awk '{cmd=$$1; $$1=""; printf "  make %-25s%s\n", cmd, $$0}'

# ============================================================================
# Setup & Development
# ============================================================================

setup: ## Create venv and install all dependencies (run once after clone)
	uv venv
	uv sync --extra dev

dev: ## Start uvicorn dev server with hot reload (http://127.0.0.1:8000)
	uv run python -m app.main

celery: ## Start Celery worker locally (without Docker)
	uv run celery -A app.core.celery:celery_app worker --loglevel=info --concurrency=1 --pool=solo

celery-kill: ## Kill all Celery processes (local and Docker)
	@pkill -9 -f "celery.*worker" 2>/dev/null || true
	@docker stop celery-worker celery-beat 2>/dev/null || true
	@echo "✓ All Celery processes stopped"

flower: ## Start Flower monitoring UI locally (http://127.0.0.1:5555)
	uv run celery -A app.core.celery:celery_app flower --port=$${FLOWER_PORT:-5555}

beat: ## Start Celery Beat scheduler locally (without Docker)
	uv run celery -A app.core.celery:celery_app beat --scheduler redbeat.schedulers:RedBeatScheduler --loglevel=info

ngrok: ## Start ngrok tunnel to expose local server (reads PORT from .env)
	@if [ -z "$$PORT" ]; then \
		echo "Error: PORT not found in .env file"; \
		exit 1; \
	fi; \
	echo "Starting ngrok tunnel on port $$PORT..."; \
	ngrok http $$PORT

# ============================================================================
# Infrastructure (Docker Compose)
# ============================================================================

infra-up: ## Start all infrastructure services (Celery worker, Beat, Flower)
	@echo "Merging environment files..."
	@bash scripts/merge_env_files.sh
	docker compose up -d --build celery-worker celery-beat flower

infra-down: ## Stop and remove all containers
	docker compose down

infra-reset: ## Destroy and recreate all infrastructure (Celery worker, Beat, Flower)
	@echo "Destroying infrastructure and recreating..."
	docker compose down -v
	@echo "Merging environment files..."
	@bash scripts/merge_env_files.sh
	docker compose up -d --build celery-worker celery-beat flower
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Infrastructure reset complete!"

infra-logs: ## View logs from all services (Ctrl+C to exit)
	docker compose logs -f

# ============================================================================
# Application (Docker)
# ============================================================================

docker-build: ## Build all Docker images (API + Celery) for linux/amd64
	@echo "Building API image..."
	DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --target api -t backend-ai:api -f docker/Dockerfile .
	@echo "Building Celery image..."
	DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --target celery -t backend-ai:celery -f docker/Dockerfile .
	@echo "✓ All images built"

app-build: ## Build FastAPI Docker image
	docker compose build app

app-up: ## Build and start FastAPI container
	@echo "Merging environment files..."
	@bash scripts/merge_env_files.sh
	docker compose up -d --build app

app-down: ## Stop FastAPI container
	docker compose stop app

app-restart: ## Restart FastAPI container
	docker compose restart app

app-logs: ## View FastAPI container logs (Ctrl+C to exit)
	docker compose logs -f app

# ============================================================================
# Database Migrations (Alembic)
# ============================================================================

db-migrate: ## Generate new migration with autogenerate (message="msg")
	uv run alembic revision --autogenerate -m "$(message)"

db-upgrade: ## Apply all pending migrations
	uv run alembic upgrade head

db-downgrade: ## Rollback last migration
	uv run alembic downgrade -1

db-reset: ## Reset database to fresh state (⚠️ deletes all data)
	@echo "⚠️  WARNING: This will delete ALL tables and data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "Force dropping all tables..."
	@uv run python scripts/force_drop_all_tables.py --quiet
	@echo "Recreating all tables from migrations..."
	@uv run alembic upgrade head
	@echo "✓ Database reset complete!"

db-seed: ## Seed database with test data for development
	@echo "Seeding database with test data..."
	@PYTHONPATH=. uv run python scripts/seed_test_data.py

# ============================================================================
# Code Quality & Testing
# ============================================================================

lint: ## Run ruff linter (auto-fix fixable issues)
	uv run ruff check . --fix

format: ## Format code with ruff
	uv run ruff format .

test: ## Run all tests with pytest
	uv run pytest

# ============================================================================
# Client Generation
# ============================================================================

OUTPUT ?= ./client

client-generate: ## Generate TypeScript client using Hey API from OpenAPI schema [OUTPUT=path]
	@echo "Exporting OpenAPI schema..."
	@PYTHONPATH=. uv run python scripts/export_openapi.py
	@echo "Generating TypeScript client to $(OUTPUT)..."
	@npx @hey-api/openapi-ts -i openapi.json -o $(OUTPUT)
	@echo "✓ TypeScript client generated in $(OUTPUT)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove cache files, compiled Python files, and venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".venv" -exec rm -rf {} +
