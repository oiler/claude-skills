# autonom — Changelog

## Unreleased

Fixes from the 2026-07-28 clean-room smoke run.

- **New `escalations` subcommand** — `uv run autonom.py escalations <slug> [--root DIR]` exits `0` when `escalations.md` is absent, empty, or whitespace-only and `1` when it has content, printing the contents to stdout. The escalation gate in steps 7 and 9 now calls it instead of describing a file check in prose, which puts "non-empty" in the script and removes the need for an `ls`/`test` tool permission the skill never granted.
- Ledger statuses documented: `complete` is the only status that advances the run, `escalated` is recorded *in addition to* it, and `failed` is recorded without it.
- SKILL.md now publishes the spec and plan validator contracts, including the warning that structural markers inside a code fence are invisible to the validator.
- `Bash(git worktree *)` added to `allowed-tools`; step 3 could not otherwise create the worktree it requires.
- Step 7 records why the reviewer prompt's paths are absolute — a dispatched subagent inherits the session's working directory, not the run's repository.

## v0.1.0 — 2026-07-28

Initial release.

- Runs superpowers steps 6–9 unattended from a single `/autonom` invocation.
- Authoring on the session model; both review passes pinned to `fable`.
- `scripts/autonom.py` owns artifact paths, the run ledger, artifact validation, and the reviewer dispatch prompts.
- Reviewer edits land as their own commit, so `git diff author..review` is the review record.
- Scope-changing findings are escalated to `escalations.md` and stop the run in both modes.
- Onboarding picks `checkpoint` (stop after the plan review) or `auto` (continue into subagent-driven-development); both create an isolated worktree first.
