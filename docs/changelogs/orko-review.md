# orko-review — Changelog

## v0.1.0 — 2026-09-26

First release: oiler's typed "dispatch independent reviewers on the spec/plan" prompt, as a slash-only skill.

### Added

- `/orko-review <doc-path> [--apply | --file-only]` runs a fixed battery of fresh-context Opus reviewers (spec: accuracy, completeness, design; plan: coverage, executability, verification; any other doc: accuracy, consistency, completeness), plus up to two specialists (security, frontend, data, performance, operations).
- Each reviewer gets a script-assembled brief and a one-sentence prompt, and writes a validated report to `<reviews-dir>/<doc-stem>/<timestamp>/`.
- `--apply` (the default) verifies every finding, records a disposition for each, edits the document, and prints a script-built summary. `--file-only` stops after the reports; `/orko-review --run <run-dir> --apply` applies them later.
- `--apply` blocks when the session effort is known and below `high`, per `MODELS.md`; an unknown session effort only warns. The reviewer agent pins `effort: high`.

### Known issues

- `run.json` and `decisions.md` are written with mode `0600` (the reports and briefs keep the umask default), and an empty `.lock` file stays in each run directory after `decide`.
