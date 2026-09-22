# python — Changelog

Entries before v0.2.1 live in the GitHub release for `python-v0.2.0`.

## v0.2.1 — 2026-09-22

### Security

- **`allowed-tools` scoped to test, lint, and type-check commands.** `Bash(uv *)` pre-approved every uv subcommand, including `uv add`, `uv pip install`, and `uv run <any program>`, so a dependency could be added without a prompt. The grant now covers `pytest`, `ruff`, `mypy`, and `pyright`, bare or through `uv run`, plus `python -m pytest`. Dependency changes now ask first. Claude Code applies a skill's `allowed-tools` without a permission prompt, and workspace trust doesn't gate the grant, so each rule now names the exact command the skill runs.
