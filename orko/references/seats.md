# Seats

## Catalog

These are example seats, not a fixed cast. The conductor picks from them or synthesizes a novel seat (with an inline charter) when an engagement needs one not listed.

- **security-reviewer** — hunts for vulnerabilities and unsafe handling: injection, auth/session flaws, secret exposure, insecure config, OWASP-class risks.
- **performance-analyst** — finds hot paths, N+1 queries, allocation and memory pressure, and scaling bottlenecks under realistic load.
- **accessibility-auditor** — checks semantics, keyboard operability, focus management, color contrast, and screen-reader behavior against WCAG.
- **test-strategist** — assesses coverage, missing edge cases, brittle or flaky tests, and where the suite gives false confidence.
- **data-modeler** — examines schema shape, normalization, constraints, indexing, and migration safety for the data the system stores.
- **api-designer** — reviews interface contracts: resource naming, versioning, error shapes, idempotency, and backward compatibility.
- **dependency/supply-chain auditor** — inventories third-party packages for known CVEs, abandoned or unmaintained deps, license conflicts, and install-time risk.
- **researcher** — gathers and synthesizes external evidence (docs, prior art, comparisons) on a focused question the team needs answered.

## Designing a seat

1. **One question it owns.** Give the seat a single, clearly scoped question; do not bundle multiple investigations into one seat.
2. **Pack all context.** The seat inherits no conversation history — include every path, constraint, and artifact it needs to work from a cold start.
3. **Prime with intent.** State the larger goal and who the work is for, so the seat optimizes for the actual outcome rather than the literal prompt.
4. **Assign a model tier by difficulty.** Match the seat to the tier table in SKILL.md (judgment-heavy → Opus, moderate → Sonnet, mechanical → Haiku).
5. **Require evidence and explicit gaps.** Every claim must tie to a tool result, and the seat must state what it did NOT check.

## FINDINGS schema (expert-authored)

```markdown
### FINDINGS — Seat: <name>
- Verdict: <one line>
- Evidence: <each point tied to a file:line or tool result>
- Recommendations: <ordered>
- Confidence & gaps: <what is uncertain or unchecked>
```

## Dispatch-prompt template

The conductor fills the `<...>` slots per seat.

```markdown
You are the <seat-role> on an orko engagement. Investigate ONLY: <scoped question>.

Context (you inherit no prior conversation — everything you need is here):
<paths, constraints, the larger goal and who it is for>

Rules:
- Substantiate every claim against a tool result (cite file:line or command output). State explicitly what you did NOT check.
- Do not change anything. Report findings only.
- Stay within your seat's scope; flag adjacent issues in one line, don't chase them.

When done:
1. Write your full findings to docs/sessions/<slug>/findings/<seat>.md using the FINDINGS schema exactly.
2. Return to the conductor ONLY: the file path, your one-line verdict, and your confidence (high/medium/low). Do not paste the findings into your return.
```

## Verifier-prompt template

Runs fresh-context, one per seat by default.

```markdown
You are an independent verifier on an orko engagement. You did not author these findings and have no stake in them.

Read ONLY:
- The findings file: docs/sessions/<slug>/findings/<seat>.md
- The same source material it cites: <paths / how to access>

For EACH finding, re-check it against the actual evidence and label it:
- confirmed — evidence supports it as stated
- overstated — real but exaggerated (give the accurate version)
- unsubstantiated — evidence does not support it
- missing-context — true but omits something that changes the conclusion

Write your verdicts to docs/sessions/<slug>/findings/<seat>.verdict.md:

### VERDICTS — Seat: <seat> (verifier: <model>)
- <finding> -> <label>: <one-line reason, cite evidence>

Do not rewrite the findings or investigate beyond checking the claims. Return to the conductor only a one-line tally (e.g. "3 confirmed, 1 overstated, 0 unsubstantiated").
```
