# Python Style and Idioms

Use this reference when writing or reviewing Python code for idiomatic patterns, async correctness, or common pitfalls.

## Modern Python Style (3.12+)

Write Python that uses current idioms. Avoid legacy patterns.

```python
# Type hints on all public functions
def fetch_users(limit: int = 50, active: bool = True) -> list[dict[str, Any]]:
    ...

# Dataclasses over manual __init__
from dataclasses import dataclass, field

@dataclass
class Config:
    host: str = "localhost"
    port: int = 8000
    tags: list[str] = field(default_factory=list)

# match-case for dispatch
match command:
    case "start":
        start_server()
    case "stop" | "quit":
        shutdown()
    case _:
        print(f"Unknown: {command}")

# f-strings, never .format() or %
msg = f"Processing {count:,} items in {elapsed:.2f}s"

# pathlib, never os.path
from pathlib import Path
config_path = Path.home() / ".config" / "app" / "settings.toml"
```

### New in 3.11–3.12

```python
# datetime.UTC (3.11+) — cleaner than timezone.utc
from datetime import datetime, UTC
now = datetime.now(UTC)

# type statement (PEP 695, 3.12+) — for type aliases
type UserId = int
type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]

# @override decorator (3.12+) — catches signature drift in subclasses
from typing import override

class JsonRenderer(BaseRenderer):
    @override
    def render(self, data: dict) -> str:
        return json.dumps(data)

```

## Choosing Between Data Containers

Pick by purpose, not preference:

| Need | Use | Why |
|---|---|---|
| Internal data container (no external input) | `@dataclass` | Stdlib, zero deps, good IDE support |
| Validate external input (API requests, config files, CLI args) | Pydantic v2 model | Runtime validation, coerces types, generates JSON schema |
| Type an existing dict shape (e.g., parsed JSON response) | `TypedDict` | Annotates without restructuring data |
| Need slots + validators + converters with less runtime overhead than Pydantic | `attrs` | Rare in new code; pick it when you specifically need attrs's converter hooks or slots+inheritance |

Default to `@dataclass`. Reach for Pydantic at trust boundaries. Use TypedDict when you're documenting a dict shape you don't control. `attrs` is rarely the right answer in new code.

```python
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import TypedDict

# Internal: dataclass
@dataclass
class CacheEntry:
    key: str
    value: bytes
    expires_at: float

# Boundary: Pydantic
class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[^@]+@[^@]+$")
    age: int = Field(ge=13, le=120)

# Shape annotation: TypedDict
class GitHubUser(TypedDict):
    login: str
    id: int
    followers: int
```

## Async Programming

Use async for I/O-bound work. Never use it for CPU-bound work (use multiprocessing instead).

```python
import asyncio
import httpx

# TaskGroup (3.11+) — structured concurrency, cancels siblings on first error
async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(client.get(url)) for url in urls]
        return [t.result().json() for t in tasks]

# asyncio.timeout (3.11+) — context-manager timeouts replace wait_for boilerplate
async def fetch_with_timeout(url: str) -> dict:
    async with asyncio.timeout(5.0):
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            return r.json()
```

Prefer `TaskGroup` over `asyncio.gather` in new code — it propagates exceptions properly and cancels siblings cleanly.

Prefer `httpx` over `aiohttp` — same interface for sync and async, easier to test.

## Common Pitfalls to Catch

When reviewing or writing Python code, watch for:

- Mutable default arguments (`def f(items=[])` — use `None` + conditional)
- Late binding closures in loops (use `functools.partial` or default args)
- Missing `if __name__ == "__main__":` guard in scripts
- Using `datetime.now()` without timezone (use `datetime.now(UTC)`)
- Bare `except:` or `except Exception:` swallowing errors silently
- `os.path` when `pathlib` would be clearer
- `requests` in async contexts (use `httpx` instead)
- Forgetting `await` on a coroutine (silently produces a `RuntimeWarning: coroutine was never awaited`)
- Mixing sync DB drivers inside async handlers (psycopg2 in an async FastAPI route blocks the event loop — use asyncpg or psycopg3 async)
- Using `datetime.utcnow()` (deprecated in 3.12 — use `datetime.now(UTC)`)
