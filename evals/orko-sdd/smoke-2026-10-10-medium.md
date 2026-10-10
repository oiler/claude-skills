---
instrument: supporting
satisfies: []
date: 2026-10-10
verdict: pass
---

> **Supporting evidence, not a release instrument.** This run tested whether the orchestrator can run at medium effort. The candidate was a scratch copy of released v0.1.2 (`skill_content_hash` 530bc6c5…), renamed `orko-sdd-candidate` so it couldn't collide with the installed skill, with one change: `medium` added to `ORCHESTRATOR_EFFORTS`. It ran as `claude -p "/orko-sdd-candidate docs/plan.md" --model opus --effort medium` on a fresh clone of the v0.1.2 textkit fixture. The self-review below came from resuming that session at `--effort high`, with the v0.1.2 resume prompt. Cost $3.70, 6.9 min, 23 turns, against the high baseline (`smoke-2026-09-25b.md`) at $4.14, 11.5 min, 50 turns. D2 below is expected: the candidate accepts medium, so `log` has nothing to warn about. D3 led to the 2026-10-10 MODELS.md reviewer-row split. It informed v0.1.3's change from a preflight block to a warning.

# Smoke test: orko-sdd-candidate, medium orchestrator effort

## Task given (verbatim)

```
/orko-sdd-candidate docs/plan.md
```

Preflight block as rendered: `plan: …/orko-sdd-medium-smoke/docs/plan.md`, `flags: none`, `sdd: 6.4.1`, `agents: orko-sdd-low, orko-sdd-medium, orko-sdd-high`, `base-branch: master`, `orchestrator-effort: medium`, `final-review: opus/high`, `STATUS: ok`.

The skill files under review (`orko-sdd-candidate/SKILL.md`, `agents/orko-sdd-{low,medium,high}.md`, `scripts/orko_sdd.py`) are byte-identical to the copies the run loaded from `orko-sdd-medium-smoke/.claude/skills/orko-sdd-candidate/`; I checked this with `diff`.

## What happened (step by step)

1. **Preflight.** It returned `STATUS: ok` with no `warning:` lines and no `--release-critical`, so I added no ledger lines for either.
2. **SDD invoked** on the plan path, as the skill says.
3. **Branch.**
   - Ran `git worktree add <repo>/.worktrees/plan -b feat/plan master`. `<plan-slug>` is `plan`, from `docs/plan.md`.
   - Appended `.worktrees/` to `.git/info/exclude`.
   - Loaded `EnterWorktree` through ToolSearch and entered with `path=`.
4. **Workspace and ledger.**
   - Ran `sdd-workspace` with the plan path inside the worktree, which gave `<worktree>/.superpowers/sdd/plan`.
   - Created the ledger with the identity line and a note that the plan names no spec.
5. **Preflight conflict scan.** I wrote the SDD table to the ledger: one row per task and one per shared file or interface.
   - Task 3 conflicts with `CLAUDE.md:3`, since it adds `requests` and `beautifulsoup4` to `pyproject.toml`. I logged `Task 3: skipped — evergreen conflict — CLAUDE.md:3 — …`, `Task 4: skipped — depends on Task 3`, and `Task 3: skip decision — (a)/(b)/(c)` in the formats the Authority section gives.
   - Task 2 had three open points. I recorded each as a `Ruling: … — … — cost if wrong: …` line before dispatch, as the `implementer-gap` rule requires.
6. **Task 1 (slugify).**
   - `log` with `implementer-scoped sonnet/medium`, because the plan text has the complete code. Dispatched `orko-sdd-medium`/`sonnet`. It returned DONE with RED and GREEN evidence.
   - Built the review package with BASE `42737fc`. `log` with `reviewer opus/medium` and no web-security line, because slugify is a pure transform. Dispatched `orko-sdd-medium`/`opus`.
   - The reviewer found spec ✅, approved, 3 Minors and one ⚠️ item (RED/GREEN not re-run). I resolved the ⚠️ by grepping the report for the evidence.
   - Ledgered the Minors as `minor (deferred)`, then `Task 1: complete (…, review clean)`.
7. **Task 2 (CLI filter).**
   - `log` with `implementer-gap opus/low` and dispatched `orko-sdd-low`/`opus`. The dispatch included the TDD line, the web-security line (stdin) and the three rulings.
   - It returned DONE_WITH_CONCERNS: the RED run failed on an import error, not on the assertions.
   - I resumed it through SendMessage to break the code one assertion at a time and record which test went red. Per the skill, this is not a fix round, so it got no ledger line. It returned DONE with the mutation evidence.
   - `log` with `reviewer-security opus/high` and dispatched `orko-sdd-high`/`opus`. Spec ✅, approved, 6 Minors (one was "output clean", which isn't a defect).
   - Ledgered 5 deferred Minors, `Task 2: complete (…, review clean)`, and a `Follow-up:` for the missing `.gitignore`.
8. **Final review.**
   - `log` with `--task final --role final-reviewer opus/high` and dispatched `orko-sdd-high`/`opus` with the web-security line, because Task 2 qualified.
   - It found 1 Important (no `python3 -m textkit` entry point) and 2 new Minors (BrokenPipe traceback; `--sep -x` is rejected by argparse). It also triaged every deferred Minor (none must-fix) and endorsed the Task 3 skip.
9. **Final fix wave.**
   - Recorded two `Ruling:` lines for how to fix: `__main__.py` only, no `[project.scripts]`; the Python-docs BrokenPipe pattern.
   - Parked `--sep -x` as `Task final: parked — … — Ruling: … — cost if wrong: …`.
   - Added one free-form line, `Task final: minor triage — …`.
   - `log` with `final-fixer opus/medium` and dispatched once with both remaining findings, the TDD line and the web-security line. It returned DONE in commit `5e994e5`, with 7 tests.
10. **Final re-review.**
    - Built the package for `d5ea660..5e994e5`. `log` with `re-reviewer-security opus/high` and dispatched. Both findings ADDRESSED. It also reported 3 new Minor breakages in the fix diff and 2 out-of-scope observations.
    - Ledgered 4 of those 5 as `Task final: minor (deferred)`. The fifth, `__pycache__`, was already a Follow-up.
    - Appended `Task final: complete (commits d5ea660..5e994e5, 1 parked)`.
11. **Finish.**
    - Ran `verify` for the test command with the output redirected and `$?` passed in, and no pipe. Exit 0, `OK`.
    - Ran `report`. It flagged nothing.
    - Invoked `finishing-a-development-branch` and posted the report verbatim from `## Done` through `## Verified`, then 3 Recommended items, then the 3-option menu.
    - The workspace is not deleted yet. The skill says to delete it only after `finishing-a-development-branch` completes, and that is waiting on oiler's choice.

Dispatch tally: 8 subagent dispatches plus 1 resume. Every one was logged beforehand, and every `log` call exited 0.

## Ambiguities and guesses

| # | Where | What was unclear | What I did |
|---|---|---|---|
| A1 | Fix loop, final-review paragraph | It says "send the final fixer every finding", with the plan-text conflict as the only exception. It doesn't cover a *new* final-review Minor that the reviewer itself marks "drop". "Deferred minors the final review marks drop … need no new line" covers only earlier deferred Minors. | I parked `--sep -x` with a ruling instead of sending it. This was a guess, and it departs from the literal rule because that finding doesn't conflict with the plan text. See D1. |
| A2 | Fix loop, final re-review | The skill says how to record the re-review's *out-of-scope observations*, but not *new Minor breakage in the fix diff*. SDD adds only new Critical/Important findings to the open list. | I recorded the new Minor breakages as `Task final: minor (deferred)` alongside the out-of-scope ones. |
| A3 | Fix loop, final review | No ledger format for the final reviewer's triage of earlier deferred Minors (can-wait/drop). The skill says only that drop/can-wait "need no new line". | I wrote a free-form `Task final: minor triage — …` line anyway. `report` silently ignored it. It does no harm, but it isn't documented. |
| A4 | Preflight / Models and effort | Preflight showed `orchestrator-effort: medium`, and MODELS.md runs the orchestrator at high. The skill says the mismatch shows up as a `warning:` from `log`. No `log` call printed one, so I appended no Follow-up and told oiler nothing. It's unclear whether `log` is supposed to warn here. | I followed the script's output. See D2. |
| A5 | Branch | The caveat names only `cd` or `git -C` combined with git work. The worktree guard also refused a `cd && heredoc && git rev-parse` call and an `awk -v …` pipeline with no git in it, saying it was "too complex to verify". | I split the calls and used Write for the ledger. For the final reviewer, I pointed it at `code-reviewer.md` and told it to follow the prompt block, instead of extracting the block to a file. |
| A6 | Dispatch construction | The skill says to use SDD's templates with the printed `subagent_type`, but doesn't say whether to paste the template or hand it over as a file. Its Speed section says "hand artifacts over as files". | I extracted the task-reviewer prompt block into `<workspace>/task-reviewer-rubric.md` once and pointed both task reviewers at it. I pointed the final reviewer and the re-reviewer at the template files directly. |
| A7 | Choosing a role | The table says nothing on whether a Task 2 resume over DONE_WITH_CONCERNS needs a `log` call. The skill says only "isn't a fix round, so it needs no ledger line". | No `log` call. The resumed agent kept its model, so this seemed consistent. |
| A8 | Finish step 3 | "A one-line announcement before it is fine". My lead-in was two sentences, a status line plus the skip notice. `finishing-a-development-branch` Step 1 also wants a test run, and the skill's Finish step 1 `verify` had just run on the same tree. | I treated the `verify` run as the skill's Step 1 test run and didn't run it again. My lead-in was slightly longer than one line. |
| A9 | Finish step 3 vs. global CLAUDE.md | The skill caps Recommended at 3 items that change what oiler does next. Global CLAUDE.md says every output ends with a decisions list. | I used Recommended as the decisions list and ended the message with the finishing menu, which the finishing skill requires. |
| A10 | Models table vs. MODELS.md | The skill's `reviewer` row is opus/medium and cites MODELS.md's "Per-task code reviewer" row. That row says Opus 5.5 at **high**. | I followed the skill: opus/medium for Task 1's non-security review. This contradicts an evergreen-weighted doc. See D3. |

### What I did because of global CLAUDE.md or MODELS.md rather than the skill

- **Likelihood and impact tags.** Every reviewer dispatch said "Report every finding … tag each with realistic likelihood and impact", from CLAUDE.md's Orchestration section.
- **Task 2 resume.** I resumed Task 2 to get assertion-level RED evidence because of CLAUDE.md's "every test goes red before it goes green". SDD's DONE_WITH_CONCERNS handling allowed it; neither skill demanded it.
- **Missing `.gitignore`.** I recorded it as a Follow-up because of CLAUDE.md's Scope section ("list other edge cases … instead of implementing").
- **Commit attribution.** I told implementers to use the system-reminder attribution line in commits.
- **Response style.** I wrote prose in the concise style and avoided emoji. That comes from CLAUDE.md and the output style, not the skill.

## Defects found

| # | Severity | Where | Defect | Owner |
|---|---|---|---|---|
| D1 | Minor | My execution, against SKILL.md's Fix loop final-review paragraph | I parked a new final-review Minor (`--sep -x`) without sending it to the final fixer. The finding doesn't conflict with the plan's text, and that's the only documented reason to park before the fix wave. The skill text also leaves this case open (A1). | Orchestrator, with a skill gap |
| D2 | Minor, unconfirmed | `orko_sdd.py log` or preflight | Preflight reported `orchestrator-effort: medium`, but no `log` call printed `warning: orchestrator effort is …`. If the warning should fire at medium, the policy mismatch never reached the ledger or oiler. I didn't read the script source to confirm which way it's meant to work. | Script, or skill wording |
| D3 | Minor | SKILL.md Models and effort table | The `reviewer` row (opus/medium) cites MODELS.md's per-task reviewer row, which says high. Either the row should say high or the citation should explain the downgrade. Under global CLAUDE.md's document authority, this contradicts an evergreen doc and should be a stop sign. | Skill |
| D4 | Minor | SKILL.md Branch caveat | The caveat understates what the worktree guard refuses. Heredoc-plus-`cd` calls and `awk -v` pipelines are refused too, and the refusal message talks about git. | Skill |
| D5 | Cosmetic | SKILL.md Fix loop | No ledger format for final-review triage of deferred Minors, or for new Minor breakage in the final fix diff (A2, A3). | Skill |

No step was blocked.

## Verdict rationale

**Pass.** Every documented step completed as SKILL.md describes:

- preflight
- the SDD hand-off
- the worktree branch
- the ledger with the scan table
- the evergreen skip chain, including the `skip decision` line, which `report` rendered on the chain's Follow-up line
- rulings in the documented format
- `log` before every dispatch, using the printed `subagent_type` and `model`
- role selection: `implementer-scoped`, `implementer-gap`, `reviewer`, `reviewer-security`, `final-reviewer`, `final-fixer`, `re-reviewer-security`
- the dispatch lines
- one final fix wave and one scoped re-review
- the `Task final: complete (…, 1 parked)` line
- `verify` without a pipe
- `report` with no flags
- the finishing skill with the report pasted verbatim
- holding the workspace deletion

The defects are wording gaps, one possible script check that never fired, a contradiction with MODELS.md, and one orchestrator deviation (D1). None of them stopped the workflow. The only step still open, deleting the workspace, is by design waiting on oiler's answer to the finishing menu.

## Mechanical checks (unchanged v0.1.2 scripts; the v0.1.2 effort check expects medium)

## Mechanical checks (orchestrator)

Orchestrator model (init): `claude-opus-5-5`. Subagent effort isn't recorded in `claude -p` transcripts; it rests on the agent files' `effort` field.

| Check | Result | Detail |
|---|---|---|
| ledger found | pass | /Users/jrf1039/files/scratch/orko-sdd-medium-smoke/.worktrees/plan/.superpowers/sdd/plan/progress.md |
| T1 dispatched on-table as implementer-scoped | pass |  |
| T2 dispatched with an on-table implementer role | pass |  |
| T3 skipped for the evergreen conflict | pass |  |
| T4 skipped as T3's dependent | pass |  |
| final review opus/high | pass |  |
| no override used | pass |  |
| at least one Verify line | pass |  |
| init lists the three agents | pass |  |
| at least one Agent dispatch | pass | 7 calls |
| every Agent call matches its log line in order | pass | 7 calls, 7 log lines |
| no git push | pass |  |
| report has all five sections | pass |  |

| Agent type | Resolved model |
|---|---|
| orko-sdd-high | claude-opus-5-5 |
| orko-sdd-low | claude-opus-5-5 |
| orko-sdd-medium | claude-opus-5-5 |
| orko-sdd-medium | claude-sonnet-5-5 |

| Check (v0.1.1) | Result |
|---|---|
| every orko_sdd.py call ran the candidate skill | pass |
| every Models item carries a role label | pass |
| no Follow-up pointer to the ledger for minors | pass |
| Decided header is numbered | pass |
| no parked finding repeated in Follow-up | pass |
| no ruling warning left after the Finish rerun | pass |
| the skipped chain has one script line, carrying the decision | pass |

| Check (v0.1.2) | Result |
|---|---|
| preflight reported orchestrator-effort: medium and STATUS: ok | pass |
| Task 1 (pure slugify) reviewed as reviewer opus/medium | pass |
| Task 2 (stdin filter) reviewed as reviewer-security opus/high | pass |
| no reviewer or re-reviewer dispatch at opus/low | pass |
| no orchestrator-effort warning from log | pass |

Review dispatches in the ledger:

- `Task 1: dispatch reviewer opus/medium — Task 1 slugify is a pure transform, no security line`
- `Task 2: dispatch reviewer-security opus/high — Task 2 CLI reads stdin and argv, so review gets the web-security line`
- `Task final: dispatch re-reviewer-security opus/high — Scoped re-review of the final fix wave; cli.py stdin/stdout handling qualifies for the security line`
