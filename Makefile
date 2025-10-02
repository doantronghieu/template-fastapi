# FastAPI Template - Development Operations
# Quick Start: make setup → cp .env.example .env → make infra-up → make db-migrate message="init" → make db-upgrade → make dev

.PHONY: help setup dev test lint format clean db-migrate db-upgrade db-downgrade infra-up infra-down infra-reset infra-logs

help:
	@echo "FastAPI Template - Available Commands"
	@echo ""
	@echo "  make setup           - Create venv and install dependencies"
	@echo "  make dev             - Start development server (http://127.0.0.1:8000)"
	@echo ""
	@echo "  make infra-up        - Start infrastructure (PostgreSQL)"
	@echo "  make infra-down      - Stop infrastructure"
	@echo "  make infra-reset     - Destroy and recreate infrastructure"
	@echo "  make infra-logs      - View infrastructure logs"
	@echo ""
	@echo "  make db-migrate message=\"msg\" - Generate migration"
	@echo "  make db-upgrade      - Apply migrations"
	@echo "  make db-downgrade    - Rollback migration"
	@echo ""
	@echo "  make test            - Run all tests"
	@echo "  make lint            - Run linter"
	@echo "  make format          - Format code"
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
	uv run uvicorn app.main:app --reload

# ============================================================================
# Infrastructure (Docker Compose)
# ============================================================================
# Services: PostgreSQL 17 (Alpine) with health checks and persistent volumes
# Configure via .env file (see .env.example)

# Start all services in detached mode
infra-up:
	docker compose up -d

# Stop and remove all containers (data persists in volumes)
infra-down:
	docker compose down

# Destroy volumes and recreate infrastructure with migrations
infra-reset:
	@echo "Destroying infrastructure and recreating..."
	docker compose down -v
	docker compose up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	uv run alembic upgrade head
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
# Cleanup
# ============================================================================

# Remove cache files, compiled Python files, and virtual environment
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".venv" -exec rm -rf {} +
