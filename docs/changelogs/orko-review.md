# orko-review — Changelog

## v0.1.1 — 2026-10-28

A few malformed findings no longer cost a whole lens. Across 39 recorded invalid reports, every failure was a missing or empty bullet, and retries drifted the same way.

### Added

- `lint --report <path>`: the reviewer checks its own report with `check`'s parser before replying. The brief carries the exact command.
- Malformed findings: a missing, out-of-order or empty bullet, or an unknown severity, marks only that finding. It stays in the index labeled `malformed: <reason>` and is decided like any other.
- A lens that fails twice is read leniently, so its findings still reach the apply step.
- Script-owned scratch folders, one per lens, outside the repo. A retry gets an empty one, and `summary` deletes them all once the run has a findings index.

### Changed

- The gap-free numbering rule is replaced by a duplicate-ID check.
- Severity matches case-insensitively.
- The failed-lens row in Needs you names what was read and from where; `failed-lenses:` names each lens's report.

### Known issues

- Whether a reviewer can run `lint` without a permission prompt depends on the session's permission settings. If it prompts, add `Bash(python3 <path to orko-review>/scripts/orko_review.py lint *)` to your allow list.

## v0.1.0 — 2026-09-26

First release: oiler's typed "dispatch independent reviewers on the spec/plan" prompt, as a slash-only skill.

### Added

- `/orko-review <doc-path> [--apply | --file-only]` runs a fixed battery of fresh-context Opus reviewers (spec: accuracy, completeness, design; plan: coverage, executability, verification; any other doc: accuracy, consistency, completeness), plus up to two specialists (security, frontend, data, performance, operations).
- Each reviewer gets a script-assembled brief and a one-sentence prompt, and writes a validated report to `<reviews-dir>/<doc-stem>/<timestamp>/`.
- `--apply` (the default) verifies every finding, records a disposition for each, edits the document, and prints a script-built summary. `--file-only` stops after the reports; `/orko-review --run <run-dir> --apply` applies them later.
- `--apply` blocks when the session effort is known and below `high`, per `MODELS.md`; an unknown session effort only warns. The reviewer agent pins `effort: high`.

### Known issues

- `run.json` and `decisions.md` are written with mode `0600` (the reports and briefs keep the umask default), and an empty `.lock` file stays in each run directory after `decide`.
