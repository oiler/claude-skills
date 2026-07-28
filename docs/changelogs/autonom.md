# autonom — Changelog

## Unreleased

Fixes from the 2026-07-28 clean-room smoke run.

- **New `escalations` subcommand** — `uv run autonom.py escalations <slug> [--root DIR]` exits `0` when `escalations.md` is absent, empty, or whitespace-only and `1` when it has content, printing the contents to stdout. The escalation gate in steps 7 and 9 now calls it instead of describing a file check in prose, which puts "non-empty" in the script and removes the need for an `ls`/`test` tool permission the skill never granted.
- Ledger statuses documented: `complete` is the only status that advances the run, `escalated` is recorded *in addition to* it, and `failed` is recorded without it.
- SKILL.md now publishes the spec and plan validator contracts, including the warning that structural markers inside a code fence are invisible to the validator.
- `Bash(git worktree *)` added to `allowed-tools`; step 3 could not otherwise create the worktree it requires.
- Step 7 records why the reviewer prompt's paths are absolute — a dispatched subagent inherits the session's working directory, not the run's repository.
- **New `dispatched` ledger status** — `ledger <step> dispatched --slug <slug> --commit <base sha>` records the pre-dispatch HEAD so a compaction mid-Fable-dispatch cannot lose the review diff's first endpoint. Like `escalated` and `failed`, it never advances `next_step`.
- Startup sequence reordered: establish the run repository, `status`, onboarding question, `init`, *then* branch. The workspace is now named `autonom/<slug>` from the slug `init` mints, which did not exist yet under the old ordering.
- SKILL.md now states that the run operates on the repository the orchestrator's cwd is inside, and that the orchestrator confirms it with the human at onboarding.
- The branch is created directly in the run repository rather than through `superpowers:using-git-worktrees`, whose native `EnterWorktree` tool is bound to the session's repository. `Bash(git checkout *)` added to `allowed-tools`.
- `init`'s `.gitignore` line is now committed with the first authoring commit, so no run leaves a dirty tree for the reviewer.
- Step 6 no longer tells the orchestrator to follow `superpowers:brainstorming`, which cannot be invoked without starting the discovery gate autonom has already satisfied; the validator-contract section is the authority instead.
- An outstanding escalation now overrides both endings: no resume-into-implementation instruction is printed, because resuming is what the escalation blocks.
- Steps 7 and 9 now count the reviewer's commits with `git log --oneline <base sha>..HEAD` before recording. A reviewer that split its edits across several commits is not an error, but the ledger records the range rather than a single SHA so the record matches what the reviewer actually did.

## v0.1.0 — 2026-07-28

Initial release.

- Runs superpowers steps 6–9 unattended from a single `/autonom` invocation.
- Authoring on the session model; both review passes pinned to `fable`.
- `scripts/autonom.py` owns artifact paths, the run ledger, artifact validation, and the reviewer dispatch prompts.
- Reviewer edits land as their own commit, so `git diff author..review` is the review record.
- Scope-changing findings are escalated to `escalations.md` and stop the run in both modes.
- Onboarding picks `checkpoint` (stop after the plan review) or `auto` (continue into subagent-driven-development); both create an isolated worktree first.
