# autonom — Changelog

## v0.1.0 — 2026-07-28

Initial release.

- Runs superpowers steps 6–9 unattended from a single `/autonom` invocation.
- Authoring on the session model; both review passes pinned to `fable`.
- `scripts/autonom.py` owns artifact paths, the run ledger, artifact validation, and the reviewer dispatch prompts.
- Reviewer edits land as their own commit, so `git diff author..review` is the review record.
- Scope-changing findings are escalated to `escalations.md` and stop the run in both modes.
- Onboarding picks `checkpoint` (stop after the plan review) or `auto` (continue into subagent-driven-development); both create an isolated worktree first.
