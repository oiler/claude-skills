---
instrument: behavior
satisfies: [behavior]
skill_content_hash: 530bc6c5cf2360a80fc458c1fae5ec26e92ce651580ec1e471fa47aec9cedd12
repo_commit: f2da212f52a36017732c9f559d8ef2d056599430
date: 2026-09-25
verdict: pass
---

# orko-sdd v0.1.2 behavior comparison

## What ran

Two surfaces, each against v0.1.1 as the baseline arm.

- **Script surface.** `policy_compare.py` ran v0.1.1's `orko_sdd.py` (from `master` at 5d95114) and v0.1.2's (0242af6) on the same cases. The first set is twelve `log` dispatches that oiler's 2026-09-25 `MODELS.md` either requires or retires. The second is `preflight` and `log` at every orchestrator effort level (`CLAUDE_EFFORT` = low, medium, high, xhigh, max, and unset). `eval_set.json` records both scripts' hashes, the comparison script's hash, and every result.
- **SKILL.md surface.** The v0.1.2 live engagement (`smoke-2026-09-25b.md`, hash `530bc6c5…`, verdict pass, 25 of 25 mechanical checks) against v0.1.1's (`smoke-2026-09-25.md`, hash `a1b805b9…`), on the same textkit sample plan. A medium-effort probe of the real `/orko-sdd` invocation is recorded in the live-engagement report.

Before any edit, an independent reviewer checked what the policy change required, in a fresh context with empirical probes on Claude Code 2.1.283. It confirmed that `${CLAUDE_EFFORT}` is substituted into the injection line and that `CLAUDE_EFFORT` is set in Bash subprocesses. It found that a skill's `effort:` frontmatter lasts one turn and that pinned agent `effort:` holds. It also caught that a level typed after `/effort` becomes oiler's default. The shipped design follows its recommendations: split security roles, block at preflight, and warn mid-run.

## Script scorecard

## log against MODELS.md (2026-09-25)

| Case | Dispatch | Policy | v0.1.1 | v0.1.2 | Condition |
|---|---|---|---|---|---|
| scoped implementer, new policy | `implementer-scoped` sonnet/medium | accept | reject | accept | met |
| scoped implementer, old policy | `implementer-scoped` sonnet/high | reject | accept | reject | met |
| ordinary review, new policy | `reviewer` opus/medium | accept | reject | accept | met |
| ordinary review, old policy | `reviewer` opus/low | reject | accept | reject | met |
| security review, new policy | `reviewer-security` opus/high | accept | reject | accept | met |
| security review at medium | `reviewer-security` opus/medium | reject | reject | reject | met |
| ordinary re-review, mirrors reviewer | `re-reviewer` opus/medium | accept | reject | accept | met |
| security re-review, mirrors reviewer | `re-reviewer-security` opus/high | accept | reject | accept | met |
| gap implementer, unchanged | `implementer-gap` opus/low | accept | accept | accept | met |
| multifile implementer, unchanged | `implementer-multifile` opus/medium | accept | accept | accept | met |
| final reviewer, unchanged | `final-reviewer` opus/high | accept | accept | accept | met |
| final fixer, unchanged | `final-fixer` opus/medium | accept | accept | accept | met |

## Orchestrator effort

| Session effort | Policy | v0.1.1 preflight | v0.1.2 preflight | v0.1.2 log warns | Condition |
|---|---|---|---|---|---|
| low | block | ok | blocked | yes | met |
| medium | block | ok | blocked | yes | met |
| high | run | ok | ok | no | met |
| xhigh | run | ok | ok | no | met |
| max | run | ok | ok | no | met |
| not set | block | ok | blocked | yes | met |

Pass condition: v0.1.2 matches the policy column on every row. Met on all 18 rows. v0.1.1 disagrees with the policy on 7 of 12 `log` cases and on all 3 preflight cases that should block.

## SKILL.md comparison

| Question | v0.1.1 run | v0.1.2 run |
|---|---|---|
| Review roles and effort | Task reviews at opus/low (the policy then) | Task 1 (pure `slugify`) as `reviewer` opus/medium; Task 2 (stdin filter) and the final re-review as `reviewer-security` / `re-reviewer-security` opus/high, each citing the web-security trigger in `--why`. No review at opus/low |
| Scoped implementer effort | `implementer-scoped` sonnet/high | `implementer-scoped` sonnet/medium |
| Orchestrator effort | Unchecked | Preflight printed `orchestrator-effort: high` and passed at `--effort high`. It blocked the medium probe in one turn, before any worktree, with the session-only fix. `log` printed no warning during the run |
| D5: gap versus multifile boundary | Guessed (ambiguity 1): "this task sat between them. I guessed `implementer-gap`" | Applied the new criterion by name (ambiguity A9): the plan names the exports, so the files needn't agree "beyond what the plan states", so `implementer-gap`. The operator still calls it a judgment call, but it followed the rule's own test and converged without a fix round |
| D5: format for "record the assumption" | Guessed (ambiguity 2) | No guess. Each Task 2 open point went in as a `Ruling:` line and reached Decided (#1–#3) |

The v0.1.2 run's other findings are new, and none of them comes from this change's goals. They go to the v0.1.3 backlog:

- The Bash-refusal note is too narrow (A1/D1, the same as v0.1.1's D1, now with more refused shapes).
- The final re-review's role is only implied (A2/D2).
- Minor fix-diff breakage from the final re-review isn't routed (A3, the same as v0.1.1's D4).
- The rule against restating a parked finding conflicts with the rule to record what oiler must act on (A4/D3).
- The report's minors lead line doesn't depend on any must-fix marks (D4).

## Verdict

Pass. The script surface matches the new policy on every case. On the SKILL.md surface, the run used the split review roles as written, preflight enforced the orchestrator's effort in both directions, and neither D5 question came up again as a guess.
