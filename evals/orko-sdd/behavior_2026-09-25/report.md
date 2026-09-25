---
instrument: behavior
satisfies: [behavior]
skill_content_hash: a1b805b967a2ed5cf4ab42eb5031683d9d4688e57362a97b24b1e897d99e21fd
repo_commit: e3f154f4319fea137a77836c75f264ac8c957588
date: 2026-09-25
verdict: pass
---

# orko-sdd v0.1.1 behavior comparison

## What ran

Two surfaces, each against a v0.1.0 baseline arm.

- **Report surface.** v0.1.0's `orko_sdd.py` (from `master`) and v0.1.1's (branch head, unchanged since 6d672e9) each ran `report` on the same four committed ledgers: `ledger-orko-v2-build.md`, `ledger-orko-sdd-run1.md`, `ledger-orko-sdd-run2.md`, and `ledger-orko-sdd-run3.md`. Each ledger was copied into a `.superpowers/sdd/plan/progress.md` shape in scratch, with `--plan /nonexistent/plan.md` and `--repo` set to that scratch directory, so titles are bare numbers and commit counts are `?` in both arms. `eval_set.json` records each ledger's SHA-256 and both outputs' hashes, taken after the scratch path is replaced with `<out>`.
- **SKILL.md surface.** The v0.1.1 live engagement (`smoke-2026-09-25.md`, hash `a1b805b9…`, verdict pass, 20 of 20 mechanical checks) against its baseline arm, v0.1.0's run 3 (`smoke-2026-09-23c.md`, hash `4a6164af…`). Both ran the same textkit sample plan; the scratch `CLAUDE.md`, `pyproject.toml`, and `docs/plan.md` are byte-identical to run 3's.

## Report scorecard

| Ledger | Metric | v0.1.0 | v0.1.1 |
|---|---|---|---|
| ledger-orko-v2-build | decided rows | 18 | 18 |
| ledger-orko-v2-build | done tasks | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| ledger-orko-v2-build | parked findings repeated in Follow-up | 1 | 0 |
| ledger-orko-v2-build | script-written skip lines in Follow-up | 0 | 0 |
| ledger-orko-v2-build | Follow-up pointers to the ledger for minors | 1 | 0 |
| ledger-orko-v2-build | minor texts missing | 19 | 0 |
| ledger-orko-v2-build | ruling warnings | none | shape #2, #13; unmatched #11 |
| ledger-orko-v2-build | Models items without a role label | 0 | 0 |
| ledger-orko-sdd-run1 | decided rows | 17 | 17 |
| ledger-orko-sdd-run1 | done tasks | 1, 2, 3, 4, final review | 1, 2, 3, 4, final review |
| ledger-orko-sdd-run1 | parked findings repeated in Follow-up | 0 | 0 |
| ledger-orko-sdd-run1 | script-written skip lines in Follow-up | 2 | 1 |
| ledger-orko-sdd-run1 | Follow-up pointers to the ledger for minors | 1 | 0 |
| ledger-orko-sdd-run1 | minor texts missing | 6 | 0 |
| ledger-orko-sdd-run1 | ruling warnings | none | shape #3, #11, #12, #13, #14, #15, #16; reversal #4, #6 |
| ledger-orko-sdd-run1 | Models items without a role label | 3 | 0 |
| ledger-orko-sdd-run2 | decided rows | 10 | 10 |
| ledger-orko-sdd-run2 | done tasks | 1, 2, 3, 4, final review | 1, 2, 3, 4, final review |
| ledger-orko-sdd-run2 | parked findings repeated in Follow-up | 4 | 0 |
| ledger-orko-sdd-run2 | script-written skip lines in Follow-up | 2 | 1 |
| ledger-orko-sdd-run2 | Follow-up pointers to the ledger for minors | 1 | 0 |
| ledger-orko-sdd-run2 | minor texts missing | 5 | 0 |
| ledger-orko-sdd-run2 | ruling warnings | none | none |
| ledger-orko-sdd-run2 | Models items without a role label | 3 | 0 |
| ledger-orko-sdd-run3 | decided rows | 11 | 11 |
| ledger-orko-sdd-run3 | done tasks | 1, 2, 3, 4, final review | 1, 2, 3, 4, final review |
| ledger-orko-sdd-run3 | parked findings repeated in Follow-up | 4 | 0 |
| ledger-orko-sdd-run3 | script-written skip lines in Follow-up | 2 | 1 |
| ledger-orko-sdd-run3 | Follow-up pointers to the ledger for minors | 1 | 0 |
| ledger-orko-sdd-run3 | minor texts missing | 6 | 0 |
| ledger-orko-sdd-run3 | ruling warnings | none | shape #2; reversal #5, #6 |
| ledger-orko-sdd-run3 | Models items without a role label | 3 | 0 |

Pass conditions, v0.1.1 column:

| Condition | Result |
|---|---|
| `decided rows` at least v0.1.0's on every ledger | met: 18, 17, 10, 11 in both arms |
| `done tasks` identical to v0.1.0's | met on all four |
| `parked findings repeated in Follow-up` is 0 | met on all four (v0.1.0: 1, 0, 4, 4) |
| `Follow-up pointers to the ledger for minors` is 0 | met on all four (v0.1.0: 1 each) |
| `minor texts missing` is 0 | met on all four (v0.1.0: 19, 6, 5, 6) |
| `Models items without a role label` is 0 | met on all four (v0.1.0: 0, 3, 3, 3) |
| `script-written skip lines in Follow-up` is 0 for orko-v2 and 1 for each run | met: 0, 1, 1, 1 (v0.1.0: 0, 2, 2, 2) |
| `ruling warnings` exactly as specified | met: `shape #2, #13; unmatched #11` / `shape #3, #11, #12, #13, #14, #15, #16; reversal #4, #6` / `none` / `shape #2; reversal #5, #6` |

## SKILL.md comparison

For each of the seven P2 questions: did run 3's operator guess on it, and did the v0.1.1 operator?

| P2 question | Run 3 (v0.1.0) | v0.1.1 run | Exercised by the sample plan |
|---|---|---|---|
| Scope of the web-security line | Guessed (ambiguity 4): stdin CLI counts, `slugify` doesn't, "both calls were guesses" | No guess. Task 1 got no line because `slugify` "is the skill's own example of a pure transform"; Task 2, its reviewer, and the final-review roles got it because the code is a stdin filter | Yes: no repeat |
| Final-review findings declined before the fix wave | Guessed (ambiguity 13): what to record for minors the final review triaged drop or can-wait | No guess on parking or on drop/can-wait minors. Every finding went to the fixer and nothing was parked. New adjacent guess (ambiguity 5): whether a ruling may depart from plan code when there's no spec, since the plan-conflict exception spells out only the ruling-keeps-the-plan branch | Yes: no repeat. The new guess is about the departing branch of the plan-conflict rule, which v0.1.1 didn't address; it goes to the v0.1.2 backlog |
| Fix round 5 | Not reached | Not reached | No: the fix loop never ran |
| `fix-tier-up`'s step | Not reached | Not reached | No |
| The downgrade rule | Not reached | Not reached | No |
| Compound `cd`/`git -C` Bash inside a worktree | Not listed as a guess (run 3 used `cd` with absolute paths and didn't enter the worktree) | No guess. Found a defect (D1): the harness refused a compound call with neither `cd` nor `git -C` (`bash <sdd script>` plus `git rev-parse` plus `log`), so the note's description is too narrow | Yes: no repeat guess. D1 goes to the v0.1.2 backlog |
| `EnterWorktree` facts | Guessed (ambiguity 5): whether a deferred tool counts as available; fell back to `cd` | No guess. Loaded `EnterWorktree` through ToolSearch and entered with `path=`, "That matches the skill" | Yes: no repeat |

Round 5, `fix-tier-up`'s step, and the downgrade rule aren't exercised by this plan, so their wording rests on review and the dogfood run, as the spec's eval plan says.

The v0.1.1 run's other findings (D2 stale deferred minors after supersession, D3 final-fixer NEEDS_CONTEXT path, D4 Minor new breakage from the final re-review, D5 gap versus multifile boundary) are new, not P2 repeats. They go to the v0.1.2 backlog.

## Verdict

Pass. Every report-surface pass condition is met on all four ledgers. On the SKILL.md surface, none of the four exercised P2 questions came up again as a guess, and the three unexercised ones are recorded as such.
