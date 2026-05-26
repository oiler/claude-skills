# uv Projects — Full Project Lifecycle

Use this reference when the user is setting up or managing a uv-based Python project (anything with a `pyproject.toml`). For one-off scripts with inline metadata, see `uv-scripts.md` instead.

## When to use this reference

- User is starting a new Python project with multiple files
- User wants to add or remove dependencies from a project
- User is configuring `pyproject.toml`, `uv.lock`, or CI for a uv project
- User is migrating from pip / poetry / pipenv to uv

## Project structure

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

## pyproject.toml — Dependencies and Packaging

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

[tool.uv]
exclude-newer = "30 days"
```

For quick scripts, use uv inline metadata — see `uv-scripts.md`.

## Supply Chain Security

**Always include `exclude-newer = "30 days"` in every uv project.** This is a rolling window that tells uv to ignore any package version published within the last 30 days, protecting against supply chain attacks like the March 2026 litellm compromise (malicious versions were caught and yanked within hours).

Two places to set this — both should be in place:

**`pyproject.toml`** (per-project, committed to git):
```toml
[tool.uv]
exclude-newer = "30 days"
```

**`~/.config/uv/uv.toml`** (machine-wide fallback, top-level key — no `[tool.uv]` section):
```toml
exclude-newer = "30 days"
```

Important caveats:
- This only applies to registry packages (PyPI). Git and local path dependencies are not affected.
- The timestamp is written into `uv.lock` at resolution time. The window doesn't move until you run `uv lock --upgrade` or `uv sync --upgrade`.
- If a project genuinely needs a package released within the last 30 days, use `exclude-newer-package` to opt that specific package out: `exclude-newer-package = { some-package = false }`.

## Lifecycle commands

[Placeholder — Task 8 adds this section]

## Dev dependencies and groups (PEP 735)

[Placeholder — Task 8 adds this section]

## Migrating from pip / poetry / pipenv

[Placeholder — Task 8 adds this section]
