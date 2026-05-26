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
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

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
- If a project genuinely needs a package released within the last 30 days, use `exclude-newer-package` to set a per-package cutoff that overrides the global window — set it to a future date to effectively opt the package out: `exclude-newer-package = { some-package = "2099-01-01" }`.

## Lifecycle commands

| Command | Use |
|---|---|
| `uv init <name>` | Scaffold a new project with `pyproject.toml`, `src/`, `.python-version` |
| `uv add <pkg>` | Add a runtime dependency; updates `pyproject.toml` and `uv.lock` |
| `uv add --dev <pkg>` | Add a development dependency (goes to `[dependency-groups].dev`) |
| `uv remove <pkg>` | Remove a dependency from both pyproject.toml and lockfile |
| `uv run <cmd>` | Run a command in the project's venv (creates/syncs the venv if needed) |
| `uv sync` | Install everything in `uv.lock` into the venv |
| `uv sync --frozen` | Like `sync` but fail if `uv.lock` is out of date (use in CI) |
| `uv lock` | Regenerate the lockfile from `pyproject.toml` constraints |
| `uv lock --upgrade` | Bump all dependencies to latest allowed versions |
| `uv lock --upgrade-package <pkg>` | Bump a single package |
| `uv tree` | Show the resolved dependency tree |
| `uv python install 3.12` | Install a managed Python interpreter |

**Lockfile commit policy:** Always commit `uv.lock` for applications. For libraries, the recommendation is evolving — committing is fine for reproducibility but consumers ignore your lockfile.

## Dev dependencies and groups (PEP 735)

uv uses `[dependency-groups]` (PEP 735) — the modern replacement for `[project.optional-dependencies]` for dev/test/docs deps that aren't part of your package's installable extras:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.6",
    "mypy>=1.11",
]
docs = [
    "mkdocs-material>=9.5",
]
```

Install a specific group: `uv sync --group docs`. Install all groups: `uv sync --all-groups`.

Keep `[project.optional-dependencies]` only for actual installable extras (e.g., `pip install mypackage[postgres]`).

## Migrating from pip / poetry / pipenv

| You used to... | With uv... |
|---|---|
| `python -m venv .venv && source .venv/bin/activate` | `uv venv` (or just let `uv run` create it implicitly) |
| `pip install -r requirements.txt` | `uv sync` (after `uv add` for each dep, or `uv pip install -r requirements.txt` as a transition) |
| `pip install <pkg>` | `uv add <pkg>` |
| `pip-compile requirements.in` | `uv lock` |
| `poetry add <pkg>` | `uv add <pkg>` |
| `poetry install` | `uv sync` |
| `poetry shell` | `uv run <cmd>` (no shell activation needed) |
| `pipenv install <pkg>` | `uv add <pkg>` |
| `pipenv install --dev <pkg>` | `uv add --dev <pkg>` |

For a one-shot migration from a `requirements.txt` codebase: `uv init`, then `uv add $(cat requirements.txt | grep -v '^#')`.
