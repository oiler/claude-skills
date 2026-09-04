# Upgrades

The orko baseline is prompt-only: seats are defined inline in dispatch prompts, tiered per dispatch, and discarded after one turn. These are the paths past that baseline. Each buys something real and costs something real; none is assumed by the SKILL.md protocol.

## Curated expert cast (optional)

For seats you reuse across engagements, promote the inline persona to a static custom agent: define `.claude/agents/<seat>.md` with the persona in the body, a `tools` allowlist, and a `model` override. The conductor then dispatches the named agent instead of repacking the charter every time.

The cost is real and worth stating plainly. Custom agents do NOT load from `additionalDirectories` — they resolve only from the actual project's `.claude/agents/` or from `~/.claude/agents/`. So to use a cast member you must install its file into one of those two locations; a definition sitting in some other tracked directory will not be discovered. And once the agent file pins `model:`, that tier is FROZEN in the file: every dispatch of that seat runs at the pinned tier, so you lose the per-dispatch tiering the prompt-only baseline gives you (where the conductor picks Opus/Sonnet/Haiku per seat per engagement at the gate).

Install note: copy or symlink the agent files into `~/.claude/agents/` (machine-wide) or the project's `.claude/agents/` (per-project). Symlinking from a tracked source keeps one canonical copy; copying decouples them.

The tradeoff: a curated cast buys consistency and named experts you can reason about across engagements, at the price of upfront setup and frozen model tiers. Use it for the handful of seats you genuinely reuse; leave the long tail inline.

## Persistent peers (agent-teams)

By default orko seats are one-shot. A dispatch returns once and the seat is gone; following up does not resume that seat — it re-dispatches a cold one that rehydrates from the disk trail (`.orko/<slug>/`). The conductor↔expert relationship is fire-and-forget, not a conversation.

Setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` changes this. The flag enables `SendMessage`, which resumes an existing seat with its full context intact — the conductor can send a follow-up to a seat that still remembers everything it did, giving true multi-turn conductor↔expert dialogue instead of a cold rehydrate from files.

orko does NOT assume this flag. The entire protocol — one-shot dispatch, paper trail, rehydrate-from-disk on follow-up — is built to work without it. Agent-teams is a strict upgrade: turn it on for engagements that need live back-and-forth with a seat; everything still works with it off.

## Deterministic pipeline (Workflow)

Under ultracode, the engagement can be modeled as a Workflow DAG: stages wired as a directed graph with enforced structured output between them. This is the only path to data-level relay fidelity — a stage's findings come back as validated structured data the next stage consumes directly, rather than prose a model reads and relays. It closes the gap the baseline calls out under Limits ("relay fidelity is engineered, not byte-guaranteed").

Two constraints pin this as an upgrade, not the everyday baseline. The Workflow tool is ultracode-gated — it is not available in the standard harness. And a Workflow DAG is deterministic and non-conversational: stages execute along fixed edges with no conductor judgment mid-run, which is exactly what buys the fidelity but also removes the adaptive, conversational decomposition the prompt-only conductor provides. Reach for it when the engagement is stable enough to wire as a fixed graph and relay fidelity matters more than adaptability.

## Build engagement (shipped in v1.0.0)

The build engagement designed here on 2026-09-04 shipped as orko v1.0.0. The lifecycle lives in `build.md`, the Linear contract in `linear.md`, and the script surface in `scripts/orko.py --help`. Two design points worth keeping in view:

- **Linear is the record, git is for code.** Artifacts never commit. Every decision kicked up to the conductor is one issue with one of four outcomes; reviewer findings are decisions under that rule. Seats never write to Linear; the conductor posts, attributed by seat, from payloads the script emits.

## Not yet built

This is a design note from the 2026-09-04 session, not a shipped mechanism — nothing in `SKILL.md`, `build.md`, or the script implements it, so do not look for it during a run.

- **The judge is tuned per task.** Analysis gets a prose verifier. Code gets a judge that runs the tests: when the conductor dispatches competing implementations for one task, it keeps the candidate whose patch passes the suite and records the other as rejected.
