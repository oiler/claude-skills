---
instrument: behavior
satisfies: [behavior]
skill_content_hash: 4c25f2c64090efdde3bd6e435a1f040e479db8706546d16e44071f463baafd53
repo_commit: 40d4b81be3cd6f5b481f3e736e998e06d8b6f4f8
date: 2026-10-28
verdict: pass
---

# orko-review v0.1.1 behavior comparison: corpus replay

The question: across every report orko-review has ever rejected, does v0.1.1 keep the findings v0.1.0 threw away, and does it mark exactly the malformed ones?

## Method

`replay.py` runs v0.1.0's `parse_report` (tag `orko-review-v0.1.0`) and v0.1.1's (`40d4b81`) over every `*.invalid-*.md` under `~/files/**/reviews/`. Each report is checked against its own front matter. The reports belong to private projects, so `results.json` records counts, project folder names, run stamps, and lens names only, never report text. `eval_set.json` holds the pass rule.

## Result: pass

39 reports, 744 finding headings. v0.1.0 failed all 39. v0.1.1 found no report-level error in any of them, indexed all 744 findings, and marked 160 malformed: in every report, exactly the findings v0.1.0 named in its errors.

| Project folder | Reports | Findings | Indexed by v0.1.1 | Malformed |
|---|---|---|---|---|
| afactory | 23 | 523 | 523 | 110 |
| ajp | 9 | 130 | 130 | 26 |
| nhl | 6 | 85 | 85 | 23 |
| scratch | 1 | 6 | 6 | 1 |
| **Total** | **39** | **744** | **744** | **160** |

The spec's evidence run, comms-briefer `2026-10-20-110919`: `accuracy.invalid-2.md` indexes 19 findings with 3 malformed, and `design.invalid-2.md` indexes 18 with 3 malformed, as the spec predicted. Under v0.1.0 both lenses were dropped for the run.

## What this doesn't cover

The replay measures the parser. The reviewer side of the change (the contract's four-bullet rule and the `lint` self-check) and the orchestrator's handling of malformed entries are covered by the live engagement, `smoke-2026-10-28.md`.
