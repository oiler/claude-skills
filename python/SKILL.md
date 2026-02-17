---
name: python-expert
description: Expert guidance for Python programming. Use when user asks to write Python code, create scripts, build web apps with Django/Flask/FastAPI, run one-off tools with uv, debug Python errors, optimize performance, or asks about Python best practices, packaging, testing, or async patterns. Covers modern Python 3.10+ idioms, uv-based scripting, Django, Flask, FastAPI, data science, testing, and production deployment.
---

# Python Expert

Expert Python guidance across scripting, web frameworks, and production systems.

## Important — Read Reference Files First

Before writing code, load the reference file that matches the user's task:

| User wants to... | Read first |
|---|---|
| Run a quick script, one-off tool, CLI utility, or use inline dependencies | `references/uv-scripts.md` |
| Build or modify a Django project (models, views, admin, DRF APIs) | `references/django.md` |
| Build or modify a Flask or FastAPI project (routes, middleware, APIs) | `references/flask-fastapi.md` |

If none of those match, use the core principles below directly.

---

## Core Principles (Always Apply)

### Modern Python Style (3.10+)

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

### Project Structure Defaults

When creating a new Python project (not a uv one-off script), use this layout:

```
project-name/
├── pyproject.toml          # Single source of truth for metadata + deps
├── src/
│   └── project_name/       # Importable package
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── conftest.py
│   └── test_main.py
└── README.md
```

Use `pyproject.toml` as the single config file. Do not create `setup.py`, `setup.cfg`, or `requirements.txt` unless the user specifically asks for them.

### Error Handling

Be specific with exceptions. Never use bare `except:`.

```python
# Good — specific exceptions, useful messages
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    logger.error("Invalid JSON at line %d: %s", e.lineno, e.msg)
    raise ValueError(f"Could not parse config: {e}") from e

# Good — custom exceptions for domain logic
class InsufficientFundsError(Exception):
    def __init__(self, balance: Decimal, amount: Decimal):
        self.balance = balance
        self.amount = amount
        super().__init__(f"Cannot withdraw {amount}: balance is {balance}")
```

### Testing with pytest

Default to pytest for all testing. Structure tests to mirror source layout.

```python
# Use fixtures for shared setup
import pytest

@pytest.fixture
def db_session():
    session = create_test_session()
    yield session
    session.rollback()

# Parametrize for multiple cases
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("", ""),
    ("café", "CAFÉ"),
])
def test_uppercase(input, expected):
    assert to_upper(input) == expected

# Use tmp_path for file operations
def test_export(tmp_path):
    out = tmp_path / "report.csv"
    export_report(out)
    assert out.read_text().startswith("id,name")
```

### Async Programming

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

### Dependencies and Packaging

For full projects, use `pyproject.toml`:

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff"]

[tool.ruff]
line-length = 100
```

For quick scripts, use uv inline metadata — see `references/uv-scripts.md`.

### Logging (not print)

Use structured logging for anything beyond throwaway scripts:

```python
import logging

logger = logging.getLogger(__name__)

# Configure once at entry point
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
```

### Common Pitfalls to Catch

When reviewing or writing Python code, watch for:

- Mutable default arguments (`def f(items=[])` — use `None` + conditional)
- Late binding closures in loops (use `functools.partial` or default args)
- Missing `if __name__ == "__main__":` guard in scripts
- Using `datetime.now()` without timezone (use `datetime.now(timezone.utc)`)
- Bare `except:` or `except Exception:` swallowing errors silently
- `os.path` when `pathlib` would be clearer
- `requests` in async contexts (use `httpx` instead)

## Troubleshooting Approach

When the user has an error or unexpected behavior:

1. Read the full traceback — Python errors are specific and descriptive
2. Identify the exception type and the failing line
3. Check types with `type()` / `isinstance()` if the error suggests a type mismatch
4. Reproduce minimally — strip away unrelated code
5. Verify Python version compatibility (`python --version`)
6. Check the virtual environment is activated and deps are installed
7. Use `python -m pytest -x --tb=short` for quick test feedback
8. Use `ruff check .` for lint issues instead of pylint/flake8 (faster, more modern)
