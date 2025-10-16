# FastAPI Template - Development Operations
# Quick Start: make setup → cp .env.example .env → make infra-up → make db-migrate message="init" → make db-upgrade → make dev

# Load environment variables from .env file (similar to docker-compose env_file)
# The '-' prefix means don't fail if .env doesn't exist
-include .env
export

.PHONY: help setup dev celery celery-kill flower ngrok test lint format clean db-migrate db-upgrade db-downgrade db-reset db-seed infra-up infra-down infra-reset infra-logs app-build app-up app-down app-restart app-logs client-generate

help:
	@echo "FastAPI Template - Available Commands"
	@echo ""
	@echo "  make setup           - Create venv and install dependencies"
	@echo "  make dev             - Start development server (http://127.0.0.1:8000)"
	@echo "  make celery          - Start Celery worker locally (without Docker)"
	@echo "  make celery-kill     - Kill all Celery processes (local and Docker)"
	@echo "  make flower          - Start Flower monitoring UI locally (http://127.0.0.1:5555)"
	@echo "  make beat            - Start Celery Beat scheduler locally (without Docker)"
	@echo "  make ngrok           - Start ngrok tunnel (reads PORT from .env)"
	@echo ""
	@echo "  make infra-up        - Start infrastructure (Celery worker, Beat, Flower)"
	@echo "  make infra-down      - Stop infrastructure"
	@echo "  make infra-reset     - Destroy and recreate infrastructure"
	@echo "  make infra-logs      - View infrastructure logs"
	@echo ""
	@echo "  make app-build       - Build FastAPI Docker image"
	@echo "  make app-up          - Build and start FastAPI container"
	@echo "  make app-down        - Stop FastAPI container"
	@echo "  make app-restart     - Restart FastAPI container"
	@echo "  make app-logs        - View FastAPI container logs"
	@echo ""
	@echo "  make db-migrate message=\"msg\" - Generate migration"
	@echo "  make db-upgrade      - Apply migrations"
	@echo "  make db-downgrade    - Rollback migration"
	@echo "  make db-reset        - Reset database to fresh state (⚠️  deletes all data)"
	@echo "  make db-seed         - Seed database with test data"
	@echo ""
	@echo "  make test            - Run all tests"
	@echo "  make lint            - Run linter"
	@echo "  make format          - Format code"
	@echo ""
	@echo "  make client-generate [OUTPUT=path] - Generate TypeScript client (default: ./client)"
	@echo ""
	@echo "  make clean           - Remove cache and venv"

# ============================================================================
# Setup & Development
# ============================================================================

# Create virtual environment and install all dependencies (run once after clone)
setup:
	uv venv
	uv sync --extra dev

# Start uvicorn dev server with hot reload
# Server: http://127.0.0.1:8000 | API docs: http://127.0.0.1:8000/docs
dev:
	uv run python -m app.main

# Start Celery worker locally (without Docker)
# Processes background tasks from Redis Cloud queue
celery:
	uv run celery -A app.core.celery:celery_app worker --loglevel=info --concurrency=1 --pool=solo

# Kill all Celery processes (local and Docker)
# Use when switching between local and Docker celery workers
celery-kill:
	@pkill -9 -f "celery.*worker" 2>/dev/null || true
	@docker stop celery-worker celery-beat 2>/dev/null || true
	@echo "✓ All Celery processes stopped"

# Start Flower monitoring UI locally (without Docker)
# Dashboard: http://127.0.0.1:${FLOWER_PORT:-5555}
flower:
	uv run celery -A app.core.celery:celery_app flower --port=$${FLOWER_PORT:-5555}

# Start Celery Beat scheduler locally (without Docker)
# Schedules: View in Flower dashboard at http://127.0.0.1:${FLOWER_PORT:-5555}
beat:
	uv run celery -A app.core.celery:celery_app beat --scheduler redbeat.schedulers:RedBeatScheduler --loglevel=info

# Start ngrok tunnel to expose local server (reads PORT from .env)
ngrok:
	@if [ -z "$$PORT" ]; then \
		echo "Error: PORT not found in .env file"; \
		exit 1; \
	fi; \
	echo "Starting ngrok tunnel on port $$PORT..."; \
	ngrok http $$PORT

# ============================================================================
# Infrastructure (Docker Compose)
# ============================================================================
# Services: Celery worker, Celery Beat scheduler, Flower monitoring
# Database: Using Supabase (configured in .env)
# Redis: Using Redis Cloud (configured in .env)
# All services run in Docker with health checks

# Start all infrastructure services in detached mode (excluding app)
# Services: celery-worker, celery-beat, flower
# Flower UI: http://127.0.0.1:5555
# Note: Always rebuilds images before starting
infra-up:
	@echo "Merging environment files..."
	@bash scripts/merge_env_files.sh
	docker compose up -d --build celery-worker celery-beat flower

# Stop and remove all containers
infra-down:
	docker compose down

# Destroy and recreate all infrastructure (Celery worker, Beat, Flower)
# Note: Database is on Supabase - use 'make db-reset' to reset database
# Note: Redis is on Redis Cloud - data persists externally
# Note: Always rebuilds images before starting
infra-reset:
	@echo "Destroying infrastructure and recreating..."
	docker compose down -v
	@echo "Merging environment files..."
	@bash scripts/merge_env_files.sh
	docker compose up -d --build celery-worker celery-beat flower
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Infrastructure reset complete!"

# View logs from all services (Ctrl+C to exit)
infra-logs:
	docker compose logs -f

# ============================================================================
# Application (Docker)
# ============================================================================
# FastAPI application in Docker container
# For local development without Docker, use: make dev

# Build FastAPI Docker image
app-build:
	docker compose build app

# Build and start FastAPI container
# Server: http://127.0.0.1:${PORT:-8000}
# Note: Always rebuilds image before starting
app-up:
	@echo "Merging environment files..."
	@bash scripts/merge_env_files.sh
	docker compose up -d --build app

# Stop FastAPI container
app-down:
	docker compose stop app

# Restart FastAPI container
app-restart:
	docker compose restart app

# View FastAPI container logs (Ctrl+C to exit)
app-logs:
	docker compose logs -f app

# ============================================================================
# Database Migrations (Alembic)
# ============================================================================

# Generate new migration with autogenerate (models auto-imported from app/models/)
# Usage: make db-migrate message="add users table"
db-migrate:
	uv run alembic revision --autogenerate -m "$(message)"

# Apply all pending migrations
db-upgrade:
	uv run alembic upgrade head

# Rollback last migration
db-downgrade:
	uv run alembic downgrade -1

# Reset database to fresh state (drops all tables, then recreates via migrations)
# WARNING: This will delete ALL data in the database!
# Uses force drop to handle cases where alembic_version is out of sync
db-reset:
	@echo "⚠️  WARNING: This will delete ALL tables and data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "Force dropping all tables..."
	@uv run python scripts/force_drop_all_tables.py --quiet
	@echo "Recreating all tables from migrations..."
	@uv run alembic upgrade head
	@echo "✓ Database reset complete!"

# Seed database with test data for development
db-seed:
	@echo "Seeding database with test data..."
	@PYTHONPATH=. uv run python scripts/seed_test_data.py

# ============================================================================
# Code Quality & Testing
# ============================================================================

# Run ruff linter (auto-fix fixable issues)
lint:
	uv run ruff check . --fix

# Format code with ruff (auto-fix)
format:
	uv run ruff format .

# Run all tests with pytest
# Specific test: uv run pytest path/to/test_file.py
# By name: uv run pytest -k test_name
test:
	uv run pytest

# ============================================================================
# Client Generation
# ============================================================================

# Generate TypeScript client using Hey API from OpenAPI schema
# Usage: make client-generate [OUTPUT=path]
# Default output: ./client directory with TypeScript SDK
OUTPUT ?= ./client

client-generate:
	@echo "Exporting OpenAPI schema..."
	@PYTHONPATH=. uv run python scripts/export_openapi.py
	@echo "Generating TypeScript client to $(OUTPUT)..."
	@npx @hey-api/openapi-ts -i openapi.json -o $(OUTPUT)
	@echo "✓ TypeScript client generated in $(OUTPUT)"

# ============================================================================
# Cleanup
# ============================================================================

# Remove cache files, compiled Python files, and virtual environment
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".venv" -exec rm -rf {} +
