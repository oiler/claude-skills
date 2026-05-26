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

## Choosing Between Data Containers

Pick by purpose, not preference:

| Need | Use | Why |
|---|---|---|
| Internal data container (no external input) | `@dataclass` | Stdlib, zero deps, good IDE support |
| Validate external input (API requests, config files, CLI args) | Pydantic v2 model | Runtime validation, coerces types, generates JSON schema |
| Type an existing dict shape (e.g., parsed JSON response) | `TypedDict` | Annotates without restructuring data |
| Need slots + validation without Pydantic | `attrs` | Rare — only when Pydantic is overkill |

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

async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r.json() for r in responses
            if not isinstance(r, Exception)
        ]
```

Prefer `httpx` over `aiohttp` — it has sync and async APIs with the same interface.

## Common Pitfalls to Catch

When reviewing or writing Python code, watch for:

- Mutable default arguments (`def f(items=[])` — use `None` + conditional)
- Late binding closures in loops (use `functools.partial` or default args)
- Missing `if __name__ == "__main__":` guard in scripts
- Using `datetime.now()` without timezone (use `datetime.now(timezone.utc)`)
- Bare `except:` or `except Exception:` swallowing errors silently
- `os.path` when `pathlib` would be clearer
- `requests` in async contexts (use `httpx` instead)
