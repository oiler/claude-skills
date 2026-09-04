# autonom — Changelog

## v0.2.0 — 2026-09-04

Retired. The skill is now a redirect stub pointing at `/orko build`. Scripts, references, and tests moved to `orko/` (see orko v1.0.0). Evidence reports under `evals/autonom/` are kept as history.

## v0.1.0 — 2026-07-28

Initial release. Runs superpowers steps 6–9 — author spec, review spec, author plan, review plan — as one unattended relay from a single `/autonom` invocation.

**The relay**

- Authoring runs on the session model; both review passes are pinned to `fable`, because escalating to a more capable reviewer is the point of the two passes.
- Each review lands as its own commit, so `git diff <author sha>..<review sha>` is the complete record of what a reviewer changed and either pass can be reverted alone.
- Onboarding asks one question — `checkpoint` (stop after the plan review) or `auto` (continue into `subagent-driven-development`) — and confirms the run repository. The run then moves to an isolated branch, `autonom/<slug>`, in both modes.
- Scope-changing findings are escalated to `escalations.md` and stop the run in both modes. Emptying that file is the human act that resolves an escalation; nothing in autonom clears it.

**The script**

`scripts/autonom.py` owns every deterministic surface — artifact paths, the run ledger, artifact validation, and the two reviewer dispatch prompts. Exit codes are `0` success, `1` validation findings, `2` usage or IO error.

- `init` mints the run's slug, derives every artifact path from it, and refuses a topic that collides with an existing run or that carries a newline or control character.
- `status` prints every run as JSON: its resume point, its last ledger status, and the base SHA of a dispatch that may not have been recorded complete — enough for a resumed session to reconcile the ledger against the branch without reading the ledger itself.
- `ledger` records `dispatched`, `complete`, `escalated`, and `failed`. Only `complete` advances the run; `dispatched` carries the pre-dispatch base SHA so a compaction mid-review cannot lose the diff range.
- `prompt` emits a reviewer's entire dispatch text, with the run's absolute paths substituted in and its git commands anchored with `git -C <root>`, so a subagent that inherits the wrong working directory still edits and commits in the run repository.
- `escalations` exits `0` when nothing is escalated and `1` with the contents when something is, so "non-empty" is decided in code rather than in prose.
- `validate spec` and `validate plan` check the artifact contracts SKILL.md publishes, reporting one finding per line with its line number.
