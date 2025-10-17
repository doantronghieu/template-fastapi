# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation Principle

**Every piece of information lives in exactly one place.**

**Three-tier hierarchy:**

1. **Code files** (`.py`): Minimal docstrings (3-5 lines) with references to docs
   - What the module does + where to find details
   - Example: `app/core/database.py` → "See docs/tech-stack.md for database details"

2. **Documentation files** (`docs/*.md`): Complete technical details and guides
   - `tech-stack.md` - Database, Celery, FastAPI, testing (all tech details)
   - `architecture.md` - Application structure and component interactions
   - `guides/development.md` - How to add features
   - `patterns/*.md` - Schema, library, and logging patterns
   - `extensions/*.md` - Extension system guides

3. **CLAUDE.md** (this file): Quick reference with file pointers
   - Tech stack list → implementation files
   - Commands and workflows
   - Navigation to detailed docs

**Rationale**: Detailed explanations belong in documentation files, not code. Developers find comprehensive guides in `docs/`, concise pointers in code, and quick reference in CLAUDE.md.

## Project Overview

FastAPI template with SQLModel (async SQLAlchemy), Supabase (PostgreSQL), Redis Cloud, Celery task queue, API documentation via Scalar, and modular extension system for specific customizations. Uses `uv` for dependency management and Docker Compose for infrastructure.

**Tech Stack:**
- **FastAPI** 0.118+ - Modern, fast web framework → See `app/main.py`
- **SQLModel** 0.0.22+ - SQL databases with Python type hints → See `app/core/database.py`, `app/models/*.py`
- **Alembic** 1.14+ - Database migrations with async support → See `alembic/env.py`
- **SQLAdmin** 0.20+ - Admin interface for database management → See `app/core/admin.py`
- **Jinja2** 3.1+ - Server-side templating engine → See `app/core/templates.py`
- **Supabase** - Cloud PostgreSQL database with Session Pooler → See `app/core/database.py`, `app/core/config.py`
- **Redis Cloud** - Managed Redis for Celery broker/backend → See `app/core/celery.py`, `app/core/config.py`
- **Celery** 5.5+ - Distributed task queue → See `app/core/celery.py`, `app/tasks/*.py`
- **Flower** 2.0+ - Celery monitoring UI → See `app/core/celery.py`
- **pytest** - Testing framework → See `tests/conftest.py`, `tests/README.md`
- **Python** 3.10+ - Uses modern union syntax (`int | None`)
- **uv** - Fast Python package manager

## Quick Start

```bash
# Initial setup (one-time)
make setup                                    # Create venv and install dependencies
cp .env.example .env                          # Configure environment variables (add Supabase and Redis Cloud credentials)
make infra-up                                 # Start Celery worker, Beat scheduler, Flower
make db-upgrade                               # Apply migrations to Supabase

# Development workflow
make dev                                      # Start FastAPI server at http://127.0.0.1:8000
```

## Common Commands

### Development
- `make dev` - Start uvicorn with hot reload (http://127.0.0.1:8000)
- `make format` - Format code with ruff
- `make lint` - Run ruff linter with auto-fix
- `make test` - Run pytest suite

### Infrastructure (Docker Compose)
- `make infra-up` - Start Celery worker, Beat scheduler, Flower (http://127.0.0.1:5555)
- `make infra-down` - Stop all containers
- `make infra-reset` - Destroy and recreate infrastructure
- `make infra-logs` - Follow logs from all services
- `make beat` - Start Beat scheduler locally (for development/testing)

### Database Migrations (Alembic)
- `make db-migrate message="description"` - Generate migration (auto-detects model changes)
- `make db-upgrade` - Apply pending migrations to Supabase
- `make db-downgrade` - Rollback last migration
- `make db-reset` - Reset Supabase database to fresh state (⚠️ deletes all data, handles out-of-sync migrations)
- `make db-seed` - Seed database with test data
- Direct: `uv run alembic revision --autogenerate -m "message"` or `uv run alembic upgrade head`

### Testing
- `make test` - Run all tests
- `uv run pytest tests/test_file.py` - Run specific file
- `uv run pytest tests/test_file.py::test_name` - Run specific test
- `uv run pytest -v` - Verbose output
- `uv run pytest -s` - Show print statements
- `uv run pytest -m integration` - Run integration tests only
- Tests use `{POSTGRES_DB}_test` database with transaction rollback isolation

### Client Generation
- `make client-generate` - Generate TypeScript client from OpenAPI schema using Hey API

## Architecture & Tech Stack

**See `docs/tech-stack.md` for:**
- Database (SQLModel + Supabase)
- Task Queue (Celery + Redis Cloud)
- Migrations (Alembic)
- API Framework (FastAPI)
- Admin Interface (SQLAdmin)
- Templates (Jinja2)
- Testing (pytest)

**See `docs/architecture.md` for:**
- Application structure and file organization
- Configuration system
- Dependency injection patterns
- Component interactions

## Extension System

Modular architecture for custom features without affecting core codebase.

**See `docs/extensions/` for:**
- `README.md` - Extension system guide (template, workflow, architecture rules)
- `message-handlers.md` - Custom channel message handlers
- `messenger.md` - Messenger integration guide

**Quick**: `cp -r app/extensions/_example app/extensions/my_extension` → Enable in `.env`

## Patterns & Guides

**See `docs/patterns/` for:**
- `schemas.md` - Schema location, TypedDict vs Pydantic, composition, validation
- `libraries.md` - Library architecture pattern, provider implementation
- `logging.md` - Logging strategy, task ID context, error handling

**See `docs/guides/` for:**
- `development.md` - File naming, adding models/services/endpoints, integrations

## Environment Configuration

Required variables in `.env` (see `.env.example` for complete list)

## Key Implementation Details

- **Package manager**: `uv` (not pip/poetry) - use `uv run` prefix for all Python commands
- **Database**: Supabase (PostgreSQL) - dual engines async (asyncpg) for API, sync (psycopg2) for admin
- **Supabase setup**: Uses Session Pooler for pgbouncer compatibility with statement cache disabled
- **Redis**: Redis Cloud free tier (30MB, 30 max connections) - optimized for minimal connection usage
- **API responses**: Scalar docs preferred over default Swagger UI
- **Admin interface**: SQLAdmin at `/admin` with auto-discovery of ModelView classes
- **Environment**: Required `.env` file with Supabase and Redis Cloud credentials (see `.env.example`)
- **Docker**: Only for Celery and Flower - database is on Supabase cloud, Redis on Redis Cloud
- **Celery worker**: Runs in Docker with concurrency=1 and pool=solo, aggressively optimized connection pooling
