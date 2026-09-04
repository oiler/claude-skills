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
4. **Assign a model tier by difficulty, defaulting down.** Per the tier table in SKILL.md: `sonnet` for analyst seats and verifiers, `haiku` for mechanical ones, `opus` only when a seat's question genuinely needs frontier judgment — and say why at the gate. The cheapest model that clears the bar is the resting state, not the floor you escalate from by habit.
5. **Require evidence and explicit gaps.** Every claim must tie to a tool result, and the seat must state what it did NOT check.

## FINDINGS schema (expert-authored)

```markdown
### FINDINGS — Seat: <name>
- Verdict: <one line>
- Evidence: <each point tied to a file:line or tool result>
- Recommendations: <ordered>
- Confidence & gaps: <what is uncertain or unchecked>
```

## Dispatch and verifier prompts

Both prompts are emitted by the script, never composed by hand:

    uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt seat <slug> --seat <name> --question "<one question>" --context-file <run_dir>/context/<name>.md
    uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt verifier <slug> --seat <name> --question "<same question>" --context-file <run_dir>/context/<name>.md

The context file is the conductor's one authored input per seat: paths, constraints, the larger goal, and who the work is for. The templates live in `seat-prompt.md` and `verifier-prompt.md` beside this file. Both end with a numbered write-then-return close, because a subagent treats its returned message as the answer and a file instruction buried mid-prompt gets skipped. Keep any new template structurally parallel.
