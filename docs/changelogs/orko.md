# orko — Changelog

## v0.2.0 — 2026-07-13

Reliability pass. Every change below is a fix for a failure observed in a live smoke engagement (two seats, two verifiers, run against the `wordpress-plugins` scaffolder), not a speculative hardening.

### Fixed — dispatch correctness

- **Model tiers are now aliases (`opus` / `sonnet` / `haiku`), not pinned versions.** The tier table previously named `Sonnet 4.6` and `Opus 4.8`. Pinned names go stale as the lineup moves, and the dispatch tool takes aliases — a conductor following the table literally would have failed every dispatch.
- **Seat type is now specified as `general-purpose`.** Every seat must Write its findings file; dispatching a read-only agent type silently breaks the paper trail.
- **`allowed-tools` grants both `Agent` and `Task`, space-separated.** It previously listed only `Task`, comma-separated — off-spec syntax, and the wrong tool name in current builds, which meant a permission prompt on every dispatch.
- **Seats receive fully-qualified findings paths.** A subagent's working directory is not guaranteed to match the conductor's; relative paths are how findings files land where nobody looks.
- **"Cap seats per round" is now a concrete six.** An instruction a conductor cannot act on is not an instruction.

### Fixed — verification integrity

These are the important ones. The verify step is what orko sells; it had three ways to fail quietly.

- **The verifier template now ends with a numbered `When done: 1. Write… 2. Return…` close, matching the seat template.** Observed failure: a verifier given the write instruction mid-block did the analysis correctly, returned it as prose, and never wrote its verdict file. Both *seats* — which had the numbered close — complied first try. Restructuring produced immediate compliance.
- **A re-dispatched verifier must be as blind as the first.** Observed failure: the conductor's re-dispatch prompt summarized what the prior pass had concluded ("all items appear accurate — sanity-check that"). That is the answer key. The primed verifier confirmed a finding the unprimed one had correctly flagged as overstated. Fresh context is the entire mechanism of verification; anchoring the replacement destroys what you are paying for.
- **A slow dispatch is not a failed dispatch.** Observed near-miss: the correct verifier took four minutes and sixteen tool calls; the conductor assumed failure and replaced it with a fast, confidently-wrong one. Confirm a seat has actually returned before re-dispatching.
- **Verdicts now beat findings in synthesis.** Where a verifier corrects a seat, the conductor relays the corrected version and says the seat was corrected — never passes through a number a verdict has contradicted.
- **Verifiers are told to check severity, not just existence.** A seat reproduces a bug under conditions it chose and reports the severity those conditions imply. It is not motivated to ask whether the documented usage path reaches the bug at all.

### Fixed — delivery and failure handling

- **Delivery checks on both dispatch and verify.** Confirm the file exists, is non-empty, and follows the schema before treating a seat as done. Re-dispatch once on failure, naming what failed. A seat that fails twice is recorded as **failed** in the synthesis — never silently omitted.
- **`.gitignore` handling no longer assumes a git repo.** If the target is not a repo, skip the step rather than initializing one the user did not ask for.

### Changed — structure and framing

A second review pass caught the skill violating a rule it had just learned, plus a premise that had gone stale.

- **Steps 3–5 are now numbered sub-lists, not walls of prose.** Step 3 had grown into a single 120-word paragraph carrying six distinct rules, with the delivery check — the entire point of this release — buried at the end. That is precisely the buried-instruction failure the verifier fix diagnoses. A skill that teaches "the instruction a reader skips is the one that isn't structurally prominent" cannot bury its own most operationally critical rule.
- **Dropped the "mimics Fable" framing.** orko was conceived as a stand-in for a frontier model that wasn't available. The old top Limit told the conductor it was running a prompted imitation of something better, and pinned the six-seat cap to that as a fake causal link. Both wrong. orko's value is orthogonal to model tier: context isolation, cost tiering, an attributed paper trail, and adversarial verification. A frontier conductor still needed independent verifiers to catch a seat's arithmetic slip and its inflated severity — the smoke run proved it. Replaced with an explicit "what orko buys that a capable session alone does not."
- **`Limits` is limits again.** It had accumulated three bullets that restated protocol rules from steps 3–5 — duplicated recurring token cost that diluted both sections. Limits now says what orko *cannot do*; the rules live once, in the protocol.
- **Trimmed the war stories.** The four-minute/sixteen-tool-call anecdote is evidence, not rationale, and it belongs here in the changelog rather than in a skill body that reloads on every invocation. The rules kept their *why* and lost their transcript.
- **The conductor row in the tier table no longer names a model.** The conductor is the main thread, not a dispatch. A leftover line still said "keep Opus for the conductor," which contradicted it.
- **Description trimmed (~1,080 → ~700 chars) and `argument-hint` added.** `disable-model-invocation: true` prevents automatic loading, so the long list of auto-fire trigger phrases was sized for a job the skill does not do. Claude still sees name-and-description and can *suggest* orko; that needs far less. (Note this deliberately cuts against the usual "descriptions must be pushy" rule — that rule fights undertriggering, and a user-invoked skill has no triggering to under-do.)
- **`references/seats.md` no longer contradicts the tiering posture.** Its seat-design step said "judgment-heavy → Opus," inviting routine escalation; SKILL.md says default down, `opus` by justified exception. The reference now mirrors the stance instead of softening it.

## v0.1.0

Initial release. Conductor playbook, seat catalog, dispatch and verifier templates, upgrades reference.
