---
name: python
description: Expert guidance for Python programming. Use when user asks to write Python code, create scripts with uv, build web apps with Django/Flask/FastAPI, debug Python errors, set up type checking (mypy/pyright), configure ruff, manage packaging or dependencies, write tests with pytest, or asks about Python best practices, async patterns, or modern 3.12+ idioms. Covers uv-based scripting, uv project workflow, Django, Flask, FastAPI, type checking, testing, and supply-chain security. NOT for: Plotly Dash apps (use plotly-dash) or security reviews (use web-security).
allowed-tools: Bash(uv *) Bash(ruff *) Bash(pytest *) Bash(mypy *) Bash(pyright *)
---

# Python Expert

Expert Python guidance across scripting, web frameworks, type checking, and project tooling.

## Important — Read Reference Files First

Before writing code, load the reference file that matches the user's task:

| User wants to... | Read first |
|---|---|
| Run a quick script, one-off tool, CLI utility with inline deps | `references/uv-scripts.md` |
| Set up or manage a uv-based project (init/add/run/sync/lock, pyproject.toml) | `references/uv-projects.md` |
| Write idiomatic modern Python, async, or avoid common pitfalls | `references/style.md` |
| Add or improve type checking (mypy/pyright) | `references/type-checking.md` |
| Build or modify a Django project | `references/django.md` |
| Build or modify a Flask app | `references/flask.md` |
| Build or modify a FastAPI service | `references/fastapi.md` |

If none of those match, use the core principles below directly.

---

## Default Toolchain

When starting a new Python project, default to:

- **uv** — environment + dependency management (replaces `venv` + `pip` + `pip-tools` + `pipx`)
- **ruff** — lint + format (replaces `black`, `isort`, `flake8`, `pylint`, `pyupgrade`). One tool, fast, zero config to start.
- **pytest** — testing
- **mypy --strict** (or **pyright**) — static type checking

Python baseline: **3.12+** unless the user has a reason to target older. (3.10 reaches EOL October 2026; 3.12 unlocks the `type` statement, `@override`, and improved f-string parsing.)

## Project Structure Defaults

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

## Error Handling Principle

Be specific with exceptions. Never use bare `except:` or `except Exception:` that silently swallows errors. Catch the narrowest exception type that makes sense, log meaningfully, and re-raise or convert to a domain-specific exception when crossing a boundary.

```python
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    logger.error("Invalid JSON at line %d: %s", e.lineno, e.msg)
    raise ValueError(f"Could not parse config: {e}") from e
```

## Logging Principle

Use `logging.getLogger(__name__)`, never `print`, for anything beyond throwaway scripts. Configure once at the entry point:

```python
import logging

logger = logging.getLogger(__name__)

# At entry point only:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
```

## Supply Chain Security

For uv-based projects, always set `exclude-newer = "30 days"` in `pyproject.toml` and `~/.config/uv/uv.toml` to protect against fresh-package supply-chain attacks. See `references/uv-projects.md` for full setup, caveats, and the `exclude-newer-package` opt-out.

## Shared Rules for Web Frameworks

When building any web app (Django, Flask, or FastAPI):

- Use a factory pattern (Flask), lifespan context (FastAPI), or settings module split (Django) — never global state initialized at import time
- Separate routes into modules/blueprints/routers once you have more than ~5 endpoints
- Use environment variables for all configuration (secrets, database URLs, debug flags)
- Return consistent error response shapes across all endpoints
- Validate request input early — via forms or a schema library in Flask/Django, via Pydantic models in FastAPI
- Use the framework's test client, never hit a running server in tests
- For production, use gunicorn (Flask/Django WSGI) or uvicorn with workers (FastAPI/ASGI), never the dev server

## Troubleshooting Approach

When the user has an error or unexpected behavior:

1. Read the full traceback — Python errors are specific and descriptive
2. Identify the exception type and the failing line
3. Check types with `type()` / `isinstance()` if the error suggests a type mismatch
4. Reproduce minimally — strip away unrelated code
5. Verify Python version compatibility (`python --version`)
6. Check the virtual environment is activated and deps are installed
7. Use `python -m pytest -x --tb=short` for quick test feedback
8. Use `ruff check .` for lint issues (faster and more modern than pylint/flake8)
9. For type errors, run the project's configured checker (`mypy .` or `pyright .`) and see `references/type-checking.md` for top-error triage
