# FastAPI Template - Development Operations
# Quick Start: make setup → cp .env.example .env → make infra-up → make db-migrate message="init" → make db-upgrade → make dev

.PHONY: help setup dev test lint format clean db-migrate db-upgrade db-downgrade db-reset db-seed infra-up infra-down infra-reset infra-logs client-generate

help:
	@echo "FastAPI Template - Available Commands"
	@echo ""
	@echo "  make setup           - Create venv and install dependencies"
	@echo "  make dev             - Start development server (http://127.0.0.1:8000)"
	@echo ""
	@echo "  make infra-up        - Start infrastructure (Celery, Flower)"
	@echo "  make infra-down      - Stop infrastructure"
	@echo "  make infra-reset     - Destroy and recreate infrastructure"
	@echo "  make infra-logs      - View infrastructure logs"
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
	@echo "  make client-generate - Generate TypeScript client from OpenAPI schema"
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

# ============================================================================
# Infrastructure (Docker Compose)
# ============================================================================
# Services: Celery worker, Flower monitoring
# Database: Using Supabase (configured in .env)
# Redis: Using Redis Cloud (configured in .env)
# All services run in Docker with health checks

# Start all infrastructure services in detached mode (excluding app)
# Services: celery-worker, flower
# Flower UI: http://127.0.0.1:5555
infra-up:
	docker compose up -d celery-worker flower

# Stop and remove all containers
infra-down:
	docker compose down

# Destroy and recreate all infrastructure (Celery, Flower)
# Note: Database is on Supabase - use 'make db-reset' to reset database
# Note: Redis is on Redis Cloud - data persists externally
infra-reset:
	@echo "Destroying infrastructure and recreating..."
	docker compose down -v
	docker compose up -d celery-worker flower
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Infrastructure reset complete!"

# View logs from all services (Ctrl+C to exit)
infra-logs:
	docker compose logs -f

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

# Reset database to fresh state (drops all tables via Alembic, then recreates)
# WARNING: This will delete ALL data in the database!
db-reset:
	@echo "⚠️  WARNING: This will delete ALL tables and data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "Downgrading to base (removing all tables)..."
	uv run alembic downgrade base
	@echo "Upgrading to head (recreating all tables)..."
	uv run alembic upgrade head
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
# Output: ./client directory with TypeScript SDK
client-generate:
	@echo "Exporting OpenAPI schema..."
	@PYTHONPATH=. uv run python scripts/export_openapi.py
	@echo "Generating TypeScript client..."
	@npx @hey-api/openapi-ts -i openapi.json -o client
	@echo "✓ TypeScript client generated in ./client"

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
