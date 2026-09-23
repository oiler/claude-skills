---
name: orko-sdd
description: >-
  oiler's standing orchestrator overlay for superpowers:subagent-driven-development.
  Runs a written implementation plan under SDD with oiler's model and effort policy
  (MODELS.md), evergreen-conflict handling, safety stops, turn-ending rules, and a
  script-built final report. Invoke only as /orko-sdd <plan-path> [--release-critical].
argument-hint: "<plan-path> [--release-critical]"
disable-model-invocation: true
allowed-tools: >-
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py preflight *)
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py log *)
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py verify *)
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py report *)
---

# orko-sdd

Execute the plan with `superpowers:subagent-driven-development` (SDD). You are the orchestrator: you dispatch, review, and decide. You do not implement.

This file changes SDD; it doesn't restate it. Where the two conflict, this file wins, because oiler's instructions outrank plugins. Everything not mentioned here runs as SDD says: the ledger, task briefs, review packages, the single task reviewer, the fix loop and its breaker, and the final review. Written against SDD 6.4.1.

Below, `<workspace>` is the directory SDD's `sdd-workspace` script prints, and `<ledger>` is the `progress.md` inside it. The `allowed-tools` grant covers the script's four subcommands only until oiler's next message; after that, a call may ask for permission.

## Preflight

!`python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py preflight $ARGUMENTS`

If that block ends in `STATUS: blocked`, report its `problem:` lines and stop. On `STATUS: ok`, invoke SDD for the `plan:` path. Once SDD has created the ledger:

- If the `flags:` line shows `--release-critical`, append the line `orko-sdd: release-critical` to the ledger. `log` reads it when you dispatch the final review.
- Copy each `warning:` line into the ledger as `Follow-up: <warning>`, so the report carries it.

## Authority

- The plan is the controlling doc for this run. CLAUDE.md and other evergreen docs constrain it.
- A task that conflicts with an evergreen doc is skipped, not ruled on. Append `Task <N>: skipped — evergreen conflict — <doc>:<line> — <what conflicts>` to the ledger, then `Task <M>: skipped — depends on Task <N>` for every task that builds on it, and continue with independent work. In this run, the skip is CLAUDE.md's "halt", and the report's Follow-up line is its "ask".
- You own every other decision the plan leaves open. Make it, record it as an SDD ruling on its own ledger line, and keep going; a ruling carried only in a `log --why` never reaches the report. Ask oiler only for the actions under Stops, or when nothing else can proceed without the answer.
- Material product, behavior, or architecture ambiguity is a ruling for you, not a reason to pick a bigger model.
- Record anything oiler must act on after the run as a `Follow-up: <item>` ledger line, so the report carries it.

## Models and effort

Log every dispatch before you make it:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py log --ledger <ledger> --task <N|N,M,…|final> --role <role> --model <model> --effort <effort> --why '<one line>'
```

Single-quote the `--why` text here and the command after `--` in Finish's `verify` call, and write `'\''` for a literal single quote: double quotes let `$` and backticks run, and an unquoted command splits at `&&`.

On success, the script prints `subagent_type` and `model`: dispatch with exactly those. SDD's templates say `general-purpose`; use the printed `subagent_type` instead. Exit 2 means the combination is off-policy or the call was refused; stderr says which. For an off-policy combination, choose again, or rerun with `--override` and put the reason in `--why`.

| Role | Model/effort | MODELS.md row |
|---|---|---|
| `implementer-scoped` | sonnet/high | Implementer: tightly scoped task from the approved plan |
| `implementer-gap` | opus/low | Implementer: minor local gap with one conventional reading |
| `implementer-multifile` | opus/medium, opus/high | Implementer: multi-file feature or substantial refactor |
| `implementer-ui` | sonnet/high | Implementer: frontend/UI from clear art direction |
| `implementer-ui-replication` | opus/medium | Implementer: high-fidelity UI replication or difficult visual debugging |
| `reviewer` | opus/low | Per-task code reviewer |
| `re-reviewer` | opus/low | Scoped re-review (CLAUDE.md: opus for scoped re-reviews) |
| `fix-incomplete` | same model as the task's last implementer or fix dispatch, next effort up (low → medium → high) | Fix failure caused by skipped files, incomplete execution or missing verification (xhigh is reserved, so a high-effort failure goes to fix-tier-up) |
| `fix-wrong-diagnosis` | fable/high | Fix failure after thorough investigation produced a confident but wrong diagnosis |
| `fix-tier-up` | opus/medium, opus/high; only above the task's last implementer or fix dispatch | SDD fix rounds 4-5: at least one step above the stuck implementer |
| `final-reviewer` | opus/high; fable/high when the ledger carries `orko-sdd: release-critical` | Final review: ordinary / release-critical whole-branch review |
| `final-fixer` | opus/medium | SDD's single final-review fix dispatch |

Choosing a role:

- The task's plan text contains the complete code: `implementer-scoped`.
- One small local gap with one conventional reading: `implementer-gap`. Record the assumption in the ledger.
- Several files with integration concerns: `implementer-multifile`, at opus/high only when the task is unusually difficult.
- Downgrade when a task turns out to be mechanical.
- A batch of small same-shape tasks (SDD's batching rule) is one dispatch: log it with `--task 3,4,5`. Record its completion as one `Task <N>: complete (…)` line per task, because SDD's resume check reads per-task lines.
- SDD's BLOCKED re-dispatch "with a more capable model": `fix-tier-up`. Any other fresh re-dispatch (NEEDS_CONTEXT, or a fix round 1-3 when the implementer can't be resumed) logs again under the task's original role.
- Scoped re-reviews log as `re-reviewer`. The final whole-branch review logs as `--task final --role final-reviewer`; for an unusually large branch, `--override` to fable/high with the reason. Its single fix dispatch logs as `--task final --role final-fixer`.

## Fix loop

Rounds 1-3 run as SDD says: resume the original implementer. It keeps its model, so those rounds need no new log line. At round 4, decide why the loop hasn't converged and log the fresh implementer under the matching role:

| Why the loop hasn't converged | Role |
|---|---|
| Incomplete execution: skipped files, missing verification, work not followed through | `fix-incomplete` |
| Thorough investigation produced a confident but wrong diagnosis | `fix-wrong-diagnosis` |
| Neither, or the script rejects `fix-incomplete` | `fix-tier-up` |

If the script also rejects `fix-tier-up` (the stuck implementer already ran at opus/high), rerun it with `--override` and the reason.

## Dispatch lines

Add each of these sentences verbatim where it applies:

- Every implementer dispatch: "Use red/green TDD for any logic in this task: write the failing test, run it and watch it fail, then implement."
- Implementer and reviewer dispatches for a task that touches request handling, auth, user input, output encoding, or secrets: "Invoke the web-security skill before writing or reviewing code for this task."

## Branch

oiler's standing preference, which is the consent SDD and `superpowers:using-git-worktrees` ask for: create an isolated worktree without asking, on a new `feat/<plan-slug>` branch off preflight's `base-branch`, unless the session already runs in a feature worktree, in which case use it. `<plan-slug>` is the plan file's basename without `.md`, and `<worktree>` is the worktree the run uses.

## Speed

Time matters: the earlier a correct result lands, the better. The levers are SDD's: batch small same-shape tasks into one dispatch, pick the cheapest role the table allows, hand artifacts over as files, and never ask a reviewer to re-run tests the implementer already ran.

## Stops

Confirm with oiler before pushing, merging, force-pushing, deleting branches, running migrations against anything non-local, or touching secrets or credentials. These add to SDD's four stop conditions.

## How your turns end

In oiler's words:

A message with no tool call ends your turn, and work stops until I return. Don't end a turn in any of these ways:

- A summary that announces the next step instead of taking it.
- An offer to continue unless I'd prefer otherwise.
- A list of decisions for me when none of them blocks the remaining work.
- Stopping to report because a milestone finished or the turn got long.

Put status notes and recommendations in the same message as your next tool call, and keep going on anything that doesn't depend on me. Stop only when nothing can advance without me, or when an action needs confirmation under the rules above.

## Finish

SDD deletes its workspace as soon as the final review is clean. Hold that deletion: the ledger feeds the report. Instead, after the final review and its fix wave:

1. Run each of the project's test and lint commands with its output redirected into the workspace, and record the result in the same Bash call:

   ```bash
   <command> > <workspace>/verify-<n>.log 2>&1; python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py verify --ledger <ledger> --exit $? --output <workspace>/verify-<n>.log -- '<command>'
   ```

   The command runs under normal permission rules. The script only records its exit code and last output line.

2. Build the report:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py report --ledger <ledger> --repo <worktree>
   ```

3. Invoke `superpowers:finishing-a-development-branch`. In the message that presents its options, put the report first, verbatim, with only the Recommended section filled in: at most three items, and only ones that would change what oiler does next. The report's Decided table is SDD's "Rulings I made" list, so don't repeat it. Merging and pushing are stops.

4. Only after `finishing-a-development-branch` has completed, delete everything in the workspace except `progress.md`, which the report's "see <ledger>" pointers still name: `find <workspace> -mindepth 1 ! -name progress.md -delete`.
