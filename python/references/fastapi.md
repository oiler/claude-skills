# FastAPI Development

Use this reference when the user is building or modifying a FastAPI service.

## When to choose FastAPI vs Flask

| Factor | Flask | FastAPI |
|---|---|---|
| Best for | Server-rendered HTML, simple APIs, prototypes | API-first backends, high-performance services |
| Async | Possible but not native (use Quart if needed) | Built-in, first-class async/await |
| Validation | Manual or with Flask-WTF / Marshmallow | Automatic via Pydantic models |
| Docs | Manual (add Swagger via flask-smorest) | Auto-generated OpenAPI/Swagger UI |
| Learning curve | Lower — minimal conventions | Moderate — requires Pydantic understanding |

If the user doesn't specify, ask. If they say "API", default to FastAPI. If they say "web app" or "website", default to Flask.

## Project Setup

```bash
uv init my-api && cd my-api
uv add fastapi uvicorn[standard]
```

Structure:

```
my-api/
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app instance + lifespan
│   ├── routers/
│   │   ├── __init__.py
│   │   └── items.py
│   ├── models.py           # Pydantic schemas
│   ├── db.py               # Database setup
│   └── dependencies.py     # Shared deps (auth, db session)
└── tests/
    └── test_items.py
```

## App Setup with Lifespan

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to DB, warm caches, etc.
    await init_db()
    yield
    # Shutdown: close connections
    await close_db()

app = FastAPI(title="My API", lifespan=lifespan)

# Register routers
from app.routers import items
app.include_router(items.router, prefix="/api")
```

Run with: `uv run uvicorn app.main:app --reload`

## Pydantic Models (Schemas)

Define request/response shapes with Pydantic:

```python
# app/models.py
from pydantic import BaseModel, Field
from datetime import datetime

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(gt=0)

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    created_at: datetime

    model_config = {"from_attributes": True}  # Enables ORM mode
```

## Routers

```python
# app/routers/items.py
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models import ItemCreate, ItemResponse
from app.dependencies import get_db_session

router = APIRouter(tags=["items"])

@router.get("/items", response_model=list[ItemResponse])
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db_session),
):
    return await db.fetch_items(skip=skip, limit=limit)

@router.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate, db=Depends(get_db_session)):
    return await db.create_item(item)

@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db=Depends(get_db_session)):
    item = await db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

## Dependency Injection

FastAPI's DI system is its superpower. Use it for database sessions, auth, config:

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, Header

async def get_db_session():
    session = await create_session()
    try:
        yield session
    finally:
        await session.close()

async def get_current_user(authorization: str = Header()):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid auth header")
    token = authorization.removeprefix("Bearer ")
    user = await verify_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user
```

## Error Handling

```python
# In app/main.py, on the FastAPI() instance:
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )
```

## Testing FastAPI

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.anyio
async def test_list_items(client):
    resp = await client.get("/api/items")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.anyio
async def test_create_item(client):
    resp = await client.post("/api/items", json={
        "name": "Widget",
        "price": 9.99,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Widget"
```

Use `anyio` for async test support (it ships its own pytest plugin — don't install `pytest-anyio`, which is a stub package). Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
anyio_backend = "asyncio"
```

## Key FastAPI Rules

- Use a lifespan context for startup/shutdown — never global state
- Separate routes into routers once you have more than ~5 endpoints
- Use Pydantic models for request validation, not manual parsing
- Use FastAPI's dependency injection for db sessions, auth, and config
- Return consistent error response shapes across all endpoints
- Use the framework test client (AsyncClient + ASGITransport), not a running server
- For production, use uvicorn with workers — never the dev server
