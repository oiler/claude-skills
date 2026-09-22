# orko-sdd — Changelog

## v0.1.0 — 2026-09-22

First release: oiler's standing SDD orchestrator prompt, as a slash-only overlay on `superpowers:subagent-driven-development` 6.4.1.

### Added

- `/orko-sdd <plan-path> [--release-critical]`, which runs a written plan under SDD with oiler's model and effort policy, evergreen-conflict skips, safety stops, and turn-ending rules.
- `orko-sdd-low`, `orko-sdd-medium`, and `orko-sdd-high` agents, which carry per-role effort because the Agent tool has no effort parameter.
- `scripts/orko_sdd.py`: `preflight` (injected at invocation), `log` (validates each dispatch against the role table), `verify` (records test and lint results), and `report` (builds the final report from the SDD ledger and git).
