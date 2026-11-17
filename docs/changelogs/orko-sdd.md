# orko-sdd — Changelog

## v0.1.5 — 2026-11-17

The skill no longer depends on the global `MODELS.md`, and orchestrator effort is a one-line note.

### Changed

- The role table's third column is "Use for" instead of "MODELS.md row", and a "Why these levels" list in SKILL.md carries the reasons from the old table rows the skill uses.
- Orchestrator effort below high, or unset, prints one `note:` line at preflight instead of a `warning:` with instructions for raising it. The note goes to oiler, not the ledger.

### Removed

- `log`'s per-dispatch orchestrator-effort warning on stderr. Preflight's note covers it.

## v0.1.4 — 2026-10-29

A regression the final fix wave introduces gets one more fix round, and the skill pins superpowers 7.0.0.

### Added

- `final-refixer` (opus/high): when the fix re-review lists a Critical or Important item under New Breakage in the Fix Diff, the orchestrator writes a superseding ruling if an earlier ruling prescribed the approach that regressed, dispatches one refixer, and runs one refix re-review. This overrides SDD's "There is no second fix wave" for that case only. Two clean-room runs had ended with such a regression parked (`smoke-2026-09-25b.md`, `smoke-2026-10-10.md`).
- `log` enforces the order and the cap: the refixer needs `--task final`, a `final-fixer` dispatch, and a re-review after it, and only one is allowed per ledger. `--override` doesn't lift these.
- A role rule for signature-only plans: exact signatures, test code and pinned values, with bodies left to the implementer, route to `implementer-scoped`.
- `report` labels the refixer `refix` on the final review row.

### Changed

- Pinned to superpowers 7.0.0. SDD's own text and templates are unchanged from 6.4.1. writing-plans now writes signature-and-test plans, which the new role rule covers.
- Finish keeps the workspace, as oiler's global CLAUDE.md asks, and copies it to the main checkout before `finishing-a-development-branch` can remove the worktree.
- Wording: the final fixer's NEEDS_CONTEXT and BLOCKED paths; rulings that depart from plan code; the final re-review's role; one home for a parked finding; the test-command gate; re-raised versus new minors; a ledger shape for resolved ⚠️ items; appending to the ledger inside a worktree.

## v0.1.3 — 2026-10-10

The orchestrator may run below high effort, with a warning, and the final-review wording covers the cases two clean-room runs had to guess at.

### Changed

- `preflight` warns instead of blocking when the orchestrator's effort is below high or isn't set, and keeps `STATUS: ok`. The warning carries the same session-only fix, and SKILL.md already copies preflight warnings into the ledger as `Follow-up:` lines. A medium-effort clean-room run passed all 25 mechanical checks (`evals/orko-sdd/smoke-2026-10-10-medium.md`). `log`'s mid-run warning is unchanged, and SKILL.md records it only when the ledger has no orchestrator-effort `Follow-up:` line yet.
- The role table cites MODELS.md's split per-task reviewer rows (2026-10-10): opus/medium when the diff isn't security-sensitive, opus/high when it is. The model and effort pairs are unchanged.
- SKILL.md lets the orchestrator park a new final-review Minor that the review marks drop or can-wait, instead of sending it to the single fix wave. Critical and Important findings still go to the fixer unless they conflict with the plan's text.
- SKILL.md records new Minor breakage that the final re-review finds in the fix diff as `Task final: minor (deferred)` lines, the same as out-of-scope observations.
- The worktree note lists everything the harness has refused: command substitution, loops with computed command names, chained heredocs, and `awk -v` pipelines, not only `cd` or `git -C` combined with git. It says to run each SDD script and git command as its own plain call.

## v0.1.2 — 2026-09-25

The role table follows oiler's 2026-09-25 effort policy, and the orchestrator's own effort is checked.

### Changed

- `implementer-scoped` runs at sonnet/medium instead of sonnet/high. A stalled scoped implementer now steps up to `fix-incomplete` at sonnet/high.
- The per-task review splits into `reviewer` (opus/medium) and `reviewer-security` (opus/high), and the scoped re-review into `re-reviewer` (opus/medium) and `re-reviewer-security` (opus/high). A review whose dispatch gets the web-security line takes the security role, so `log` refuses a medium review of a security diff, and the Speed rule no longer trades that level away. Both security roles keep the `rev` and `re-rev` labels in the report.
- `preflight` reads `CLAUDE_EFFORT`, prints `orchestrator-effort:`, and blocks below high, including when it isn't set. Its fix names the session-only path (`/effort`, choose high, press `s`, or `claude --effort high`), because a level typed after `/effort` becomes oiler's default. xhigh and max pass.
- `log` warns on stderr, without refusing the dispatch, when the orchestrator's effort has dropped below high mid-run. SKILL.md has the orchestrator relay the fix to oiler and record the warning once as a `Follow-up:` line.
- SKILL.md draws the line between `implementer-gap` and `implementer-multifile` by whether the files have to agree with each other, not by file count, and records each open point of a gap task as a `Ruling:` line.

## v0.1.1 — 2026-09-25

Report fidelity and instruction gaps, from the v0.1.0 clean-room runs.

### Changed

- The report states each fact once. Parked findings with a ruling appear only in Decided. Done names the kind of skip, and Follow-up gives each skipped chain one line with its dependents and the decision oiler must make, written as `Task <N>: skip decision — <options>`. `Follow-up:` ledger lines render without their prefix.
- Deferred minors are listed in full in Follow-up, one line per task, instead of as a count and a path to a ledger that Finish deletes. `Task <N,M>:` and `Task final:` minor lines are read too, and SKILL.md has the orchestrator write the final re-review's out-of-scope observations as `Task final: minor (deferred)` lines. Follow-up is no longer truncated, and the 40-line cap is gone.
- Decided numbers its rows. A `Ruling (supersedes "<words>"):` line marks the row it replaces, and both rows show the link.
- Follow-up flags Decided rows that lack the `Ruling: <what> — <why> — cost if wrong: <cost>` shape, supersedes notes that match nothing, plain rulings that read as reversals, and rulings an unindented line may continue. It also flags a parked line with no finding, and lists lines that look like rulings but didn't parse. The reversal warning says to add a supersedes note only if the ruling does reverse one. Finish has the orchestrator fix those ledger lines and run `report` once more.
- The ruling parser keeps empty rulings, joins indented continuation lines, reads `**Ruling:**`, `**Ruling**:`, and table-cell rulings cleanly, reads every ruling in a multi-cell table row, ends an annotation at its own closing parenthesis, and reads `Final: parked` lines with their findings. A bold or backticked line after a ruling starts its own entry instead of joining the ruling. A ruling quoted in a `Follow-up:` line is no longer a decision. `minor (deferred) — <text>` drops its leading dash, and `Depends on Task <N>` folds into its chain in any case.
- The Models column labels each model with its role: `impl`, `rev`, `re-rev`, or `fix`.
- SKILL.md defines user input for the web-security line and says when the final-review roles get it. It sends every final-review finding to the fixer except plan conflicts, adds a cost to SDD's breaker formats, defines `fix-tier-up`'s step and round 5, gives the downgrade rule a target and a time, corrects the `EnterWorktree` notes, and covers plans that live outside the repository.

## v0.1.0 — 2026-09-23

First release: oiler's standing SDD orchestrator prompt, as a slash-only overlay on `superpowers:subagent-driven-development` 6.4.1.

### Added

- `/orko-sdd <plan-path> [--release-critical]`, which runs a written plan under SDD with oiler's model and effort policy, evergreen-conflict skips, safety stops, and turn-ending rules.
- `orko-sdd-low`, `orko-sdd-medium`, and `orko-sdd-high` agents, which carry per-role effort because the Agent tool has no effort parameter.
- `scripts/orko_sdd.py`: `preflight` (injected at invocation), `log` (validates each dispatch against the role table), `verify` (records test and lint results), and `report` (builds the final report from the SDD ledger and git).
- The report puts Recommended, the one section the orchestrator writes, last, and reads `Task final: complete (…)` and `Task final: parked — …` lines: the final review row shows completion, and each parked residual names its finding in Decided and Follow-up.
