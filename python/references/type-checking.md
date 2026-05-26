# Python Type Checking

Use this reference when adding or improving static type checking in a Python project. Covers tool choice, config, gradual adoption, and common patterns.

## Tool choice

| Tool | When | Notes |
|---|---|---|
| **mypy** | Default for established projects | Mature, exhaustive, slower. Use `--strict` mode. |
| **pyright / basedpyright** | Faster checks, richer inference, IDE-first workflows | Microsoft's checker (basedpyright is the community fork with looser defaults inverted). Run with `pyright .` or via Pylance in VS Code. |
| **ty** | Forward-looking only | Astral's checker, preview as of 2026 — not yet stable enough to default to. Worth tracking. |

Pick one tool per project. Running two leads to conflicting suppressions.

## Project config

### mypy

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true   # not included in strict; catches dead branches

# Per-module overrides when integrating with untyped libraries:
[[tool.mypy.overrides]]
module = "some_untyped_lib.*"
ignore_missing_imports = true
```

### pyright

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingImports = "error"
reportMissingTypeStubs = "warning"
# Per-path overrides:
exclude = ["legacy/", "build/"]
```

## Gradual typing

For an untyped codebase, don't try to type everything at once:

1. Start permissive: `strict = false`, then enable strictness flags one at a time
2. Mark currently-untyped modules with per-module overrides rather than scattering `# type: ignore` everywhere
3. When suppressing, always use error codes: `# type: ignore[arg-type]` not bare `# type: ignore`
4. Treat `Any` as a code smell — track usages with `grep -r ': Any' src/`; replace as you understand the code

## Patterns

### Protocols (structural typing)

```python
from typing import Protocol

class SupportsClose(Protocol):
    def close(self) -> None: ...

def shutdown(resource: SupportsClose) -> None:
    resource.close()
```

Use for "anything with this method" — duck typing made checkable.

### TypedDict (annotating dict shapes)

```python
from typing import TypedDict, NotRequired

class GitHubUser(TypedDict):
    login: str
    id: int
    bio: NotRequired[str | None]  # may be absent
```

Use when you're annotating data you don't control (JSON responses, config dicts).

### Literal (string enums without Enum)

```python
from typing import Literal

LogLevel = Literal["debug", "info", "warning", "error"]

def log(level: LogLevel, msg: str) -> None: ...
```

### Self (fluent APIs)

```python
from typing import Self

class Builder:
    def with_name(self, name: str) -> Self:
        self._name = name
        return self
```

### @override (3.12+)

Catches signature drift in subclasses when a parent method gets renamed:

```python
from typing import override

class JsonRenderer(BaseRenderer):
    @override
    def render(self, data: dict) -> str: ...
```

### TYPE_CHECKING (avoiding import cycles)

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .heavy_module import HeavyType  # only imported during type check

def process(x: "HeavyType") -> None: ...
```

## Top error triage

| Error | What it means | Fix |
|---|---|---|
| `Incompatible types in assignment` | Inferred type doesn't match annotation | Add a cast, widen the annotation, or fix the value |
| `Argument has incompatible type` | Passing wrong type to a function | Check function signature; convert at the boundary |
| `Missing type parameters for generic type` | Used `list` instead of `list[int]` | Add the parameter — `list[Any]` if you must |
| `Item "None" of "X \| None" has no attribute "..."` | Forgot None check | Add `if x is not None:` or use `assert x is not None` |
| `Module has no attribute "..."` | Attribute doesn't exist on the module, or stubs are missing/wrong | Check the attribute name first; if the module is untyped, install stubs (`types-<package>`) or add `ignore_missing_imports` for that module |
| `Returning Any from function declared to return X` | Function returns `Any` (often from untyped lib) | Add explicit cast or fix the upstream type |

## Key rules

- One type checker per project
- Always use error codes in `# type: ignore[code]` suppressions
- Treat `Any` as technical debt, not a target
- Add `@override` when you start a new subclass — costs nothing, catches real bugs
- For untyped third-party libs, prefer adding stubs (`types-<package>` or write a `.pyi`) over project-wide `ignore_missing_imports`
