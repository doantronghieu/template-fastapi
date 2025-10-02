# Testing Guide

## Quick Start

```bash
make test                                              # Run all tests
uv run pytest tests/test_example.py                   # Specific file
uv run pytest tests/test_example.py::test_create_example  # Specific test
uv run pytest -v                                       # Verbose
uv run pytest -s                                       # Show prints
```

## Configuration

**pyproject.toml:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"  # Auto-detect async tests, no decorators needed
```

**Test Database:**
- Name: `{POSTGRES_DB}_test` (e.g., `db_test`)
- Tables: Created once per session, dropped at end
- Isolation: Each test runs in transaction that rolls back

## Fixtures

See `conftest.py` for implementation. All fixtures are function-scoped except `test_engine`.

**`test_engine`** (session) - Database engine, auto-used by `db_session`

**`db_session`** - Async session with transaction rollback
```python
async def test_create(db_session: AsyncSession):
    record = MyModel(name="test")
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)
    assert record.id is not None
```

**`client`** - Async HTTP client with database override
```python
async def test_api(client: AsyncClient):
    response = await client.post("/api/users", json={"email": "test@example.com"})
    assert response.status_code == 201
```

**`sync_client`** - Synchronous client for non-async tests
```python
def test_health(sync_client: TestClient):
    response = sync_client.get("/api/health")
    assert response.status_code == 200
```

## Writing Tests

### Database Operations

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def test_query(db_session: AsyncSession):
    # Create
    user = User(email="test@example.com")
    db_session.add(user)
    await db_session.commit()

    # Query
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    found = result.scalar_one()
    assert found.email == "test@example.com"
```

### API Endpoints

```python
from httpx import AsyncClient

async def test_endpoint(client: AsyncClient):
    response = await client.get("/api/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Test Organization

```
tests/
├── conftest.py       # Fixtures
├── test_*.py         # Test modules (one per API module or model)
└── README.md         # This file
```

**Conventions:**
- Files: `test_*.py`
- Functions: `test_*()` or `async def test_*()`
- One test file per API module or model
- Group related tests together

## Debugging

```bash
uv run pytest --pdb        # Debug on failure
uv run pytest --lf         # Run last failed
uv run pytest -l           # Show local variables
uv run pytest -s           # Disable capture (see prints)
uv run pytest -v -s tests/test_example.py::test_create  # Specific test verbose
```

## Common Issues

**Database connection:**
- Start PostgreSQL: `make infra-up`
- Check database: `docker exec postgres psql -U postgres -l`

**Async errors:**
- Use `async def` for async fixtures
- Remember to `await` async calls

**Isolation issues:**
- Use `db_session` fixture (auto-rollback)
- Don't commit in production code during tests

## Manual Database

```bash
# Create test database
docker exec postgres psql -U postgres -c "CREATE DATABASE db_test;"

# Drop test database
docker exec postgres psql -U postgres -c "DROP DATABASE db_test;"
```

## Best Practices

1. Use `db_session` for database tests
2. No `@pytest.mark.asyncio` needed (auto-detected)
3. Keep tests isolated (no shared state)
4. Descriptive test names
5. One assertion concept per test
6. Let transaction rollback handle cleanup
