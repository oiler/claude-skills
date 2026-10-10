---
instrument: behavior
satisfies: [behavior]
skill_content_hash: 7e00e83c2936539b7935a4cb912104ef98817386d66e6dfb6de7b7563923a6c2
repo_commit: fd94efe1b59b0958aef1a974218188552837b2cd
date: 2026-10-10
verdict: pass
---

# orko-sdd v0.1.3 behavior comparison

## What ran

Two surfaces, each against v0.1.2 as the baseline arm.

- **Script surface.** `policy_compare.py` ran v0.1.2's `orko_sdd.py` (`master` at 42174c6) and v0.1.3's (fd94efe). It covers thirteen `log` dispatches, which must keep v0.1.2's answers because the role table didn't change, and `preflight` plus `log` at every orchestrator effort level. `eval_set.json` records both scripts' hashes, the comparison script's hash, and every result.
- **SKILL.md surface.** The v0.1.3 live engagement (`smoke-2026-10-10.md`, verdict pass, 26 of 26 mechanical checks, run at `--effort medium`) against v0.1.2's (`smoke-2026-09-25b.md`, at high), on the same textkit plan. The supporting medium run of a v0.1.2 copy with only the gate relaxed (`smoke-2026-10-10-medium.md`) is the evidence behind the change.

## Script scorecard

## log against MODELS.md (2026-10-10)

| Case | Dispatch | Policy | v0.1.2 | v0.1.3 | Condition |
|---|---|---|---|---|---|
| scoped implementer | `implementer-scoped` sonnet/medium | accept | accept | accept | met |
| scoped implementer at high | `implementer-scoped` sonnet/high | reject | reject | reject | met |
| ordinary review | `reviewer` opus/medium | accept | accept | accept | met |
| ordinary review at low | `reviewer` opus/low | reject | reject | reject | met |
| security review | `reviewer-security` opus/high | accept | accept | accept | met |
| security review at medium | `reviewer-security` opus/medium | reject | reject | reject | met |
| ordinary re-review | `re-reviewer` opus/medium | accept | accept | accept | met |
| security re-review | `re-reviewer-security` opus/high | accept | accept | accept | met |
| security re-review at medium | `re-reviewer-security` opus/medium | reject | reject | reject | met |
| gap implementer | `implementer-gap` opus/low | accept | accept | accept | met |
| multifile implementer | `implementer-multifile` opus/medium | accept | accept | accept | met |
| final reviewer | `final-reviewer` opus/high | accept | accept | accept | met |
| final fixer | `final-fixer` opus/medium | accept | accept | accept | met |

## Orchestrator effort

| Session effort | Policy | v0.1.2 preflight | v0.1.3 preflight | v0.1.3 preflight warns | v0.1.3 log warns | Condition |
|---|---|---|---|---|---|---|
| low | run with warning | blocked | ok | yes | yes | met |
| medium | run with warning | blocked | ok | yes | yes | met |
| high | run | ok | ok | no | no | met |
| xhigh | run | ok | ok | no | no | met |
| max | run | ok | ok | no | no | met |
| not set | run with warning | blocked | ok | yes | yes | met |

Pass condition: v0.1.3 matches the policy column on every row. Met on all 19 rows. v0.1.2 differs only on the three effort rows below high, where it blocks.

## SKILL.md comparison

| Question | v0.1.2 run (high) | v0.1.3 run (medium) |
|---|---|---|
| Orchestrator effort below high | Blocked in one turn (the v0.1.2 medium probe) | Preflight printed `orchestrator-effort: medium`, then the warning, then `STATUS: ok`. The run went on and wrote exactly one orchestrator-effort `Follow-up:` line, even though `log` warned on every dispatch. The report's Follow-up carries it |
| Fix-diff Minors from the final re-review | Guessed (A3) | Recorded as `Task final: minor (deferred)` lines, as the new text says. No guess reported |
| New final-review Minors marked drop or can-wait | v0.1.2-era medium run parked one without a documented basis (D1 of `smoke-2026-10-10-medium.md`) | Not exercised as a park. The orchestrator read re-raised Minors as deferred minors (ambiguity 1), which matches the existing "need no new line" rule, and sent one can-wait item to the fixer with a ruling |
| Worktree refusal note | Under-described (D1) | No refusal hit and no guess about the note. The operator combined some calls anyway (ambiguity 8) |
| Final-wave outcome | Fix introduced an Important regression; parked with a ruling | Fix introduced an Important regression; parked with a ruling. Same pattern at both efforts |

New findings from the v0.1.3 run go to the v0.1.4 backlog: re-raised deferred minors versus "new" Minors (1), no way to mark a deferred minor resolved, which is the existing D2 item (defect 1), no ledger format for ⚠️ resolutions (4), Write versus append for the ledger (7), and no security effort tier for the final fixer (6).

## Verdict

Pass. The script surface matches the policy on every case. On the SKILL.md surface, a medium-effort orchestrator ran the whole workflow with the warning recorded once, and the two wording fixes that came up were followed without guesses.
