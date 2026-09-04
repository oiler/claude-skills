# Upgrades

The orko baseline is prompt-only: seats are defined inline in dispatch prompts, tiered per dispatch, and discarded after one turn. These are the paths past that baseline. Each buys something real and costs something real; none is assumed by the SKILL.md protocol.

## Curated expert cast (optional)

For seats you reuse across engagements, promote the inline persona to a static custom agent: define `.claude/agents/<seat>.md` with the persona in the body, a `tools` allowlist, and a `model` override. The conductor then dispatches the named agent instead of repacking the charter every time.

The cost is real and worth stating plainly. Custom agents do NOT load from `additionalDirectories` — they resolve only from the actual project's `.claude/agents/` or from `~/.claude/agents/`. So to use a cast member you must install its file into one of those two locations; a definition sitting in some other tracked directory will not be discovered. And once the agent file pins `model:`, that tier is FROZEN in the file: every dispatch of that seat runs at the pinned tier, so you lose the per-dispatch tiering the prompt-only baseline gives you (where the conductor picks Opus/Sonnet/Haiku per seat per engagement at the gate).

Install note: copy or symlink the agent files into `~/.claude/agents/` (machine-wide) or the project's `.claude/agents/` (per-project). Symlinking from a tracked source keeps one canonical copy; copying decouples them.

The tradeoff: a curated cast buys consistency and named experts you can reason about across engagements, at the price of upfront setup and frozen model tiers. Use it for the handful of seats you genuinely reuse; leave the long tail inline.

## Persistent peers (agent-teams)

By default orko seats are one-shot. A dispatch returns once and the seat is gone; following up does not resume that seat — it re-dispatches a cold one that rehydrates from the disk trail (`docs/sessions/<slug>/`). The conductor↔expert relationship is fire-and-forget, not a conversation.

Setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` changes this. The flag enables `SendMessage`, which resumes an existing seat with its full context intact — the conductor can send a follow-up to a seat that still remembers everything it did, giving true multi-turn conductor↔expert dialogue instead of a cold rehydrate from files.

orko does NOT assume this flag. The entire protocol — one-shot dispatch, paper trail, rehydrate-from-disk on follow-up — is built to work without it. Agent-teams is a strict upgrade: turn it on for engagements that need live back-and-forth with a seat; everything still works with it off.

## Deterministic pipeline (Workflow)

Under ultracode, the engagement can be modeled as a Workflow DAG: stages wired as a directed graph with enforced structured output between them. This is the only path to data-level relay fidelity — a stage's findings come back as validated structured data the next stage consumes directly, rather than prose a model reads and relays. It closes the gap the baseline calls out under Limits ("relay fidelity is engineered, not byte-guaranteed").

Two constraints pin this as an upgrade, not the everyday baseline. The Workflow tool is ultracode-gated — it is not available in the standard harness. And a Workflow DAG is deterministic and non-conversational: stages execute along fixed edges with no conductor judgment mid-run, which is exactly what buys the fidelity but also removes the adaptive, conversational decomposition the prompt-only conductor provides. Reach for it when the engagement is stable enough to wire as a fixed graph and relay fidelity matters more than adaptability.

## Build engagement (v2, agreed design — not yet built)

orko v1 is an analysis instrument. v2 adds a build engagement type under the same conductor, and folds the `autonom` skill into orko so there is one skill, one persona, and one paper trail. This section records the design agreed on 2026-09-04; the implementation follows it.

### One skill, two engagement types

| Engagement | Invoked as | Lifecycle | Seats |
|---|---|---|---|
| Analysis (v1) | `/orko <question>` | brief, dispatch, verify, synthesize | analysts + verifiers |
| Build (v2) | `/orko build <goal> [init docs]` | intake, spec, plan, execute, code review | analysts as reviewers, one plan-writer, implementers via `superpowers:subagent-driven-development` |

The skill stays `disable-model-invocation: true`. It is never the default; a project that runs this way declares it up front (a line in the project CLAUDE.md naming `/orko build`) and the human still invokes it.

### What is kept and what is dropped

| From | Keep | Drop |
|---|---|---|
| orko v1 | conductor role, gate-before-dispatch, seat/verifier templates, model tiering, delivery checks, FINDINGS schema | `docs/sessions/` as the primary record |
| autonom | ledger and resume logic, spec and plan validators, escalation gate, one-onboarding-question discipline, cwd and `git -C` hazards | committed artifacts, `docs/superpowers/` paths, reviewer write authority, pinned-Fable in-place review |

### Build lifecycle

| Step | Conductor does | Dispatches | Linear |
|---|---|---|---|
| 0 Intake | reads goal and init docs, asks one round of clarifying questions, confirms repo, branch, and boundaries | none | creates Project; records goal, boundaries, branch |
| 1 Spec | writes spec to run dir, validates | none | Project document "Spec" |
| 2 Spec review | folds in, decides per finding | 2–4 reviewer seats, parallel, report-only | one issue per finding |
| 3 Plan | edits the draft, validates | one plan-writer seat | Project document "Plan" |
| 4 Plan review | as step 2 | reviewer seats | as step 2 |
| 5 Execute | orchestrates `subagent-driven-development` | implementers | issue per escalation only, never per task |
| 6 Code review | folds in, fixes or backlogs | review seats (incl. `code-review`, `security-review`) | one issue per finding |
| 7 Close | summary, links PR | none | Project done; backlog remains |

After intake the conductor is in charge within the declared boundaries. autonom's pre-authorized skipping of the brainstorming User Review Gate and the writing-plans Execution Handoff carries over to build engagements only, and only after intake.

### Linear is the record, git is for code

- Artifacts never commit. The spec and plan live in the git-ignored run directory as working copies (validators and seats read them by absolute path) and in Linear Project documents as the record. Project repos stay clean of product docs; only documentation that supports the code itself is committed.
- **Every decision kicked up to the conductor becomes a Linear issue.** Reviewer findings are decisions by this rule, so they get one issue each, not one per seat. Four outcomes: handled now (Done, with reasoning, action, and resolving commit), deferred (Backlog, with enough context to pick up cold), rejected (Canceled, with why), or outside boundaries (Blocked; the run stops and asks the human — this is autonom's escalation gate with a home).
- **The conductor posts to Linear, attributed by seat.** Seats report back and never write to Linear. This replaces autonom's separate-review-commit safeguard, which existed only because reviewers had write authority.
- Analysis engagements move to Linear too: a Project with one issue per verified finding, so the skill has one trail convention. The run dir is scratch in both modes.
- The ledger records the Linear Project and document IDs at init so a resumed session can re-fetch; the Project description carries enough to rebuild state if the run dir is lost.
- The script (`autonom.py` becomes `orko.py`) owns structure: paths, ledger, validators, seat prompts. It cannot call the Linear connector, so it emits what to post and the conductor posts it — the bright-line contract from autonom, with side effects visible in the transcript.

### The judge is tuned per task

v1's verifier is a *prose* judge, the right referee for analysis. Code is different: when build seats produce competing implementations, the judge runs the test suite and keeps the candidate whose patch passes. Prose work gets a synthesizing judge; code work gets a judge that runs the tests.
