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
- A task that conflicts with an evergreen doc is skipped, not ruled on. Append `Task <N>: skipped — evergreen conflict — <doc>:<line> — <what conflicts>` to the ledger, then `Task <M>: skipped — depends on Task <N>` for every task that builds on it, and continue with independent work. In this run, the skip is CLAUDE.md's "halt", and the report's Follow-up line is its "ask": `report` writes one line per skipped chain on its own. For the decision oiler must make, append the ledger line `Task <N>: skip decision — <options>` for the chain's first task, and `report` puts it on that chain's line. Don't write a separate `Follow-up:` line for it.
- You own every other decision the plan leaves open. Make it, record it as an SDD ruling on its own ledger line, and keep going; a ruling carried only in a `log --why` never reaches the report. Write each ruling as `Ruling: <what> — <why> — cost if wrong: <cost>`. When a ruling replaces an earlier one, write it as `Ruling (supersedes "<words>"): …`, quoting words from the earlier ruling, so the report marks that row superseded; the report flags a plain ruling that reads as a reversal. Don't restate a parked finding or a ruling in a `Follow-up:` line, because Decided already carries it. Ask oiler only for the actions under Stops, or when nothing else can proceed without the answer.
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
- Downgrade on a fresh re-dispatch (NEEDS_CONTEXT, or a fix round 1-3 when the implementer can't be resumed) when the work left is transcription from the plan or a single-file mechanical fix: log it as `implementer-scoped`, whatever the task's first role was.
- A batch of small same-shape tasks (SDD's batching rule) is one dispatch: log it with `--task 3,4,5`. Record its completion as one `Task <N>: complete (…)` line per task, because SDD's resume check reads per-task lines.
- SDD's BLOCKED re-dispatch "with a more capable model": `fix-tier-up`. Any other fresh re-dispatch (NEEDS_CONTEXT, or a fix round 1-3 when the implementer can't be resumed) logs again under the task's original role, unless the downgrade rule applies.
- Scoped re-reviews log as `re-reviewer`. The final whole-branch review logs as `--task final --role final-reviewer`; for an unusually large branch, `--override` to fable/high with the reason. Its single fix dispatch logs as `--task final --role final-fixer`.

## Fix loop

Rounds 1-3 run as SDD says: resume the original implementer. It keeps its model, so those rounds need no new log line. At round 4, decide why the loop hasn't converged and log the fresh implementer under the matching role:

| Why the loop hasn't converged | Role |
|---|---|
| Incomplete execution: skipped files, missing verification, work not followed through | `fix-incomplete` |
| Thorough investigation produced a confident but wrong diagnosis | `fix-wrong-diagnosis` |
| Neither, or the script rejects `fix-incomplete` | `fix-tier-up` |

`fix-tier-up` means at least one step above the stuck implementer, where a step is a stronger model or a higher effort on the same model: opus/medium to opus/high counts. SDD asks for "one tier above"; this is looser on purpose, because xhigh is reserved and Fable is kept for `fix-wrong-diagnosis`. If the script rejects `fix-tier-up` too (the stuck implementer already ran at opus/high or above), rerun it with `--override` and the reason.

Round 5 logs the same way as round 4, and `log` checks it against round 4's dispatch. After a fable/high round 4, `fix-incomplete` and `fix-tier-up` both reject, so round 5 is `fix-wrong-diagnosis` again or an `--override` with the reason.

At SDD's breaker, add a cost to both of its formats, because the report's Decided table needs one for every ruling: `Task <N>: parked — <finding> — Ruling: <why the code stands> — cost if wrong: <cost>`, and `Task <N>: Ruling: <finding> — <what you decided and why> — cost if wrong: <cost>`.

Resuming the implementer before its first review, over its own DONE_WITH_CONCERNS, isn't a fix round, so it needs no ledger line.

Send the final fixer every finding from the final review, as SDD says, including the deferred minors the final review marks must-fix. The one exception is a finding that conflicts with the plan's text: rule on it first, as SDD's plan-mandated rule says, and when the ruling keeps the plan, park the finding instead of sending it. Record each final-review finding you park, before the fix wave or after the re-review, as `Task final: parked — <finding> — Ruling: <why> — cost if wrong: <cost>`; that line is the ruling, so don't write a separate `Ruling:` line for it. `<K>` below counts every `Task final: parked` line, from before the fix wave and after it. Record the final re-review's out-of-scope observations as `Task final: minor (deferred): <one-liner>`. Deferred minors the final review marks drop or can-wait need no new line. After the final re-review, append `Task final: complete (commits <fix-base7>..<head7>, review clean)`, with `<K> parked` in place of `review clean` when you parked any and `<fix-base7>` the commit the final fixer started from; when the final review comes back clean with no fix wave, append `Task final: complete (commits <merge-base7>..<head7>, review clean)`, the branch range that review saw.

## Dispatch lines

Add each of these sentences verbatim where it applies:

- Every implementer and fixer dispatch, including the final fixer: "Use red/green TDD for any logic in this task: write the failing test, run it and watch it fail, then implement."
- Every implementer, fixer, and reviewer dispatch whose code touches request handling, auth, user input, output encoding, or secrets: "Invoke the web-security skill before writing or reviewing code for this task." User input is anything the program reads from outside itself at runtime: HTTP requests, command-line arguments, stdin, files, environment variables, and responses from other services. A library function's string arguments count when the function builds paths, shell commands, SQL, HTML, or URLs from them, or parses an untrusted format; a pure transform such as a slug function doesn't, but a command-line filter that reads stdin does. The final reviewer gets the line when any task on the branch did; the final fixer and a re-reviewer get it when the code they touch qualifies.

## Branch

oiler's standing preference, which is the consent SDD and `superpowers:using-git-worktrees` ask for: create an isolated worktree without asking, unless the session already runs in a feature worktree, in which case use it. Don't create it with the built-in `EnterWorktree(name=…)`: it picks its own branch name and directory under `.claude/worktrees/`, and with the default `worktree.baseRef: fresh` it branches from `origin/<default>`, which a repository with no remote doesn't have. Instead:

1. Run `git worktree add <repo-root>/.worktrees/<plan-slug> -b feat/<plan-slug> <base-branch>`, with preflight's `base-branch` (or `<repo-root>`'s, see below).
2. If `.worktrees/` isn't ignored, add it to `.git/info/exclude`.
3. Work from that directory: enter it with `EnterWorktree(path=…)`, loading the tool with ToolSearch first if it's deferred. Use absolute paths instead when the tool is unavailable or you decline it, or when the session is already in a worktree, where `EnterWorktree(path=…)` accepts only targets under `.claude/worktrees/`.

Inside a worktree entered this way, the harness has refused (observed in Claude Code 2.1.280–2.1.281) a Bash call that combines `cd` or `git -C` with git work, so split those into separate calls.

`<plan-slug>` is the plan file's basename without `.md`, and `<worktree>` is the worktree the run uses. Once in the worktree, pass SDD's scripts (`sdd-workspace`, `task-brief`, `review-package`) the plan's path inside the worktree, so the workspace and ledger live there. `<repo-root>` is the repository the plan changes, which the plan names when it isn't the one you started in; when it differs, take `<base-branch>` (`master`, else `main`) and the `.worktrees/` exclusion from `<repo-root>`, not from preflight. When the plan file lives outside that repository, pass SDD's scripts its absolute path and run them from the worktree; the workspace still lands in the worktree.

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

While a subagent you dispatched is running and nothing local remains, ending the turn with one status line is fine, because its completion notification resumes you.

## Finish

SDD deletes its workspace as soon as the final review is clean. Hold that deletion: the ledger feeds the report. Instead, after the final review and its fix wave:

1. Run each of the project's test and lint commands with its output redirected into the workspace, and record the result in the same Bash call:

   ```bash
   <command> > <workspace>/verify-<n>.log 2>&1; python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py verify --ledger <ledger> --exit $? --output <workspace>/verify-<n>.log -- '<command>'
   ```

   The command runs under normal permission rules. The script only records its exit code and last output line. Don't pipe `<command>` into another program: `$?` would be the last program's exit code, so a failing suite could record exit 0. If the project has no lint command, record only its test commands.

2. Build the report:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py report --ledger <ledger> --repo <worktree>
   ```

   If Follow-up flags Decided rows or lists lines not read as rulings, fix those ledger lines and run `report` once more. Paste that output, with any flags that remain.

3. Invoke `superpowers:finishing-a-development-branch`. In the message that presents its options, put the report first; a one-line announcement before it is fine. Paste the script's output unchanged, from `## Done` through the Verified table, then write the Recommended items under `## Recommended` in place of the HTML comment: at most three, and only ones that would change what oiler does next. The report's Decided table is SDD's "Rulings I made" list, so don't repeat it. Merging and pushing are stops.

4. Only after `finishing-a-development-branch` has completed, delete the workspace as SDD does: `rm -rf <workspace>`.
