---
instrument: behavior
satisfies: [behavior]
skill_content_hash: 42b5a49531f34ace7203d56a643c84bdd9d6a51551ab1f4906797124925779cc
repo_commit: 51e9ed3f58310f08c8587a2995417f35ae985da4
date: 2026-10-29
verdict: pass
---

# orko-sdd v0.1.4 behavior comparison: the final refix decision

The question: given a fix re-review's report, does the orchestrator under v0.1.4 dispatch one refixer exactly when the fix wave introduced Critical or Important breakage, and park everything else, where v0.1.3 parks it all?

## Method

`decision_compare.py` gives `claude -p --model opus --effort high --tools ""` superpowers 7.0.0's SDD `SKILL.md` and `re-review-prompt.md`, the orko-sdd `SKILL.md` under test, a ledger, and a re-review report, and asks for the next ledger lines and `log` command. The cases come from the real fix re-review of the 2026-10-10 v0.1.3 clean-room run (`build_cases.py`), with the grading edited per case. Three runs per case per arm, graded by line prefix. `eval_set.json` holds the cases and the pass rule.

## Result: pass

| Case | v0.1.4 (final) | v0.1.3 | v0.1.4 before the case-5 fix |
|---|---|---|---|
| 1-important | 3/3 | 3/3 | 3/3 |
| 2-minor | 3/3 | 3/3 | 3/3 |
| 3-not-addressed | 3/3 | 3/3 | 3/3 |
| 4-after-refix | 3/3 | — | 3/3 |
| 5-mixed | 3/3 | 3/3 | 1/3 |

Cost: $2.9 for this run, $3.92 for the first.

The first run missed case 5. In 2 of 3 runs the orchestrator dispatched the refixer correctly but wrote no `parked` line for the NOT ADDRESSED finding, because it expected the refix to resolve it (same root cause), so the finding left the ledger. Following the spec's on-a-miss rule, SKILL.md now says to park each NOT ADDRESSED finding with its own line even then (commit 51e9ed3), and every case was rerun. `results-run1-before-fix.json` keeps the first run.

## Deciding lines

- **1-important** (v0.1.4, run 1): `LOG: python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py log --ledger <workspace>/progress.md --task final --role final-refixer --model opus --effort high --why 'fix re-review found Important new breakage: ASCII-fold in text`
- **2-minor** (v0.1.4, run 1): `LEDGER: Task final: minor (deferred): slugify's ASCII fold (`.encode("ascii", "ignore")`, textkit/slug.py:7) deletes characters that don't decompose to ASCII, where the regex used to turn them into separators: "Paris–Lon`
- **3-not-addressed** (v0.1.4, run 1): `LEDGER: Task final: parked — Invalid UTF-8 on stdin: the crash is fixed and good lines still slug, but bad bytes are stripped instead of acting as separators (`foo\xffbar` -> `foobar`, not `foo-bar`) — Ruling: real and d`
- **4-after-refix** (v0.1.4, run 1): `LEDGER: Task final: parked — refix re-review Important: NFKD runs before lowercase in textkit/slug.py:7, said to split the one-to-one mapping (ﬁle -> file, Ⅻ -> xii) — Ruling: the refix diff only changed which characters`
- **5-mixed** (v0.1.4, run 1): `LOG: python3 ${CLAUDE_SKILL_DIR}/scripts/orko_sdd.py log --ledger /Users/jrf1039/files/scratch/orko-sdd-v014-probe/.worktrees/plan/.superpowers/sdd/plan/progress.md --task final --role final-refixer --model opus --effort`
