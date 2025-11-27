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

**pyproject.toml**

**Test Database:**
- Name: `{POSTGRES_DB}_test` (e.g., `postgres_test` on Supabase)
- Tables: Created once per session, dropped at end
- Isolation: Each test runs in transaction that rolls back
- Uses same Supabase connection as development (configured in `.env`)

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
tests/                              # Core application tests
├── conftest.py                     # Fixtures (db_session, client, sync_client)
├── test_*.py                       # Test modules (one per API module or model)
└── README.md                       # This file

app/integrations/*/tests/           # Integration-specific tests (co-located)
├── conftest.py                     # Integration-specific fixtures
└── test_*.py                       # Integration tests

app/extensions/*/tests/             # Extension tests (co-located)
├── conftest.py                     # Extension-specific fixtures
├── test_*.py                       # Pytest tests
└── bruno/                          # Bruno API test collections
```

**Conventions:**
- Files: `test_*.py`
- Functions: `test_*()` or `async def test_*()`
- Core tests in `tests/`, co-located tests in `app/integrations/*/tests/` and `app/extensions/*/tests/`
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
- Ensure `.env` has valid Supabase and Redis Cloud credentials
- Test database `{POSTGRES_DB}_test` is auto-created on Supabase
- Start infrastructure: `make infra-up` (Celery/Flower only - Redis on Redis Cloud)

**Async errors:**
- Use `async def` for async fixtures
- Remember to `await` async calls

**Isolation issues:**
- Use `db_session` fixture (auto-rollback)
- Don't commit in production code during tests

## Test Database Management

The test database (`{POSTGRES_DB}_test`) is automatically created on Supabase when tests run. No manual setup required.

To manually reset test database:
```bash
# Via Supabase SQL Editor or psql
DROP DATABASE IF EXISTS postgres_test;
CREATE DATABASE postgres_test;
```

## Best Practices

1. Use `db_session` for database tests
2. No `@pytest.mark.asyncio` needed (auto-detected)
3. Keep tests isolated (no shared state)
4. Descriptive test names
5. One assertion concept per test
6. Let transaction rollback handle cleanup

---

## Manual API Testing with REST Client

For manual testing of Messenger integration endpoints, use the provided HTTP file.

**File:** `tests/messenger.http`

### Setup

1. **Install REST Client extension** (VS Code):
   - Name: REST Client
   - Author: Huachao Mao
   - [Marketplace Link](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)

2. **Update recipient ID**:
   ```http
   @recipientId = YOUR_RECIPIENT_PSID_HERE
   ```
   Get PSID from Messenger webhook logs when a user messages your page.

3. **Start server**:
   ```bash
   make dev
   ```

### Usage

**Execute requests:**
- Click "Send Request" link above any request
- Keyboard shortcuts:
  - `Ctrl+Alt+R` (Mac: `Cmd+Alt+R`) - Send request
  - `Ctrl+Alt+C` (Mac: `Cmd+Alt+C`) - Cancel request

**Results:** Response appears in a separate tab with formatted JSON.

### Test Categories

The file includes comprehensive test cases:

1. **Text Messages** - Simple and long text messages
2. **Quick Replies** - Choice buttons, icons, user phone/email
3. **Generic Template (Single)** - Product cards, articles, events
4. **Generic Template (Carousel)** - Product catalogs, destinations, menus
5. **Edge Cases** - Maximum limits (13 quick replies, 10 carousel elements)
6. **Real World Scenarios** - E-commerce, support, restaurant flows
7. **Error Tests** - Validation failures (intentionally invalid)

### Local Variations

Create a local copy with your test data (ignored by git):

```bash
cp tests/messenger.http tests/messenger.local.http
# Edit messenger.local.http with your actual recipient_id
```

Pattern `*.local.http` is in `.gitignore` - safe for personal test data.

### Tips

- **Real images**: All examples use Unsplash images (free, no attribution needed)
- **Postback events**: Check Celery logs to see payload data from button clicks
- **Validation**: Section 7 tests validation errors (expected to fail)
- **API docs**: View all schemas at http://localhost:8000/scalar
