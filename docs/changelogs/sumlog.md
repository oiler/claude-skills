# sumlog — Changelog

Entries before v0.6.1 live in the GitHub releases for `sumlog-v0.1.0` through `sumlog-v0.6.0`.

## v0.6.1 — 2026-09-22

### Security

- **`allowed-tools` no longer grants unrestricted `Bash`.** The bare `Bash` entry pre-approved every shell command during the `/sumlog` turn. The grant is now the bundled extractor (`uv run ${CLAUDE_SKILL_DIR}/scripts/extract_session.py`) and `mktemp`; `Read` and `Write` stay for the two temp files. Claude Code applies a skill's `allowed-tools` without a permission prompt, and workspace trust doesn't gate the grant, so each rule now names the exact command the skill runs.

### Changed

- **Extractor commands are written unquoted and on one line** so the text Claude runs matches the `allowed-tools` rule exactly; the quoted, backslash-continued form would not have matched it.
