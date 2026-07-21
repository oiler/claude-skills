# Agent playbook — deciding whether to add an agent

Agents are the most expensive, least-used layer in a Cowork plugin. Across
22 surveyed Anthropic-shipped Cowork plugins, exactly 1 ships an agent
(`brand-voice`, three agents: `discover-brand`, `content-generation`,
`quality-assurance`). Read this before Phase 2/3 add an agent row to the
component table, and before Phase 4 scaffolds `agents/*.md`.

## 1. Default is no agent

The skill layer is the unit of capability in Cowork. A skill body — Trigger,
Inputs, Steps, Output Format, After — handles the overwhelming majority of
what a plugin needs to do, including multi-step work, tool calls through
connectors, and delegation to other skills. An agent is a separate
capability layer with its own frontmatter, its own context window, its own
tool-scoping surface — real cost to author, real cost to audit, real
surface for the standalone/supercharged split to break down on.

Start every component plan assuming zero agents. Adding one is a deliberate
deviation, not a default checkbox — the build menu marks it
`playbook-gated`, not `included by default`.

## 2. When-to-add gate

Add an agent only when the work is a **genuine autonomous multi-step job**
that shouldn't be inlined into a skill body. The tell is that the job needs
its own turn budget, its own tool scope, and produces a result the calling
skill consumes rather than narrates step-by-step. Three shapes qualify:

- **Heavy search/triage** — searching across many connected platforms,
  scoring and ranking results, deep-fetching a subset. (`discover-brand`:
  4-phase algorithm, 25 max turns, no tool restriction because it needs
  every connected MCP server.)
- **Long-form or batch generation** — content requiring simultaneous
  application of many constraints, or generating several variants at once.
  (`content-generation`: sonnet, 15 max turns, `Read`/`Glob`/`Grep` only.)
- **A QA sweep** — structured validation against a checklist, run as a
  distinct pass before the parent skill presents output. (`quality-assurance`:
  haiku, 10 max turns, `Read`/`Glob`/`Grep` only.)

**If the job is linear or short — a handful of steps, one tool, no
branching search — keep it a skill.** Inlining is cheaper to author, cheaper
to audit, and easier for the Cowork user's mental model: one skill, one
job, no invisible sub-agent turn budget running underneath it.

**State the justification out loud before emitting an agent.** Before
writing `agents/<name>.md`, write the one-line justification into the
Phase 2 component table (see `build-spine.md`) — which of the three shapes
this is, and why it can't be inlined. An agent with no stated justification
doesn't get scaffolded. This isn't a formality: writing the sentence is what
catches "this is actually just four Steps" before a needless agent ships.

## 3. Agent frontmatter fields

Every Cowork agent's frontmatter carries these fields, in this order. This
list is what Task 9's `agent.md` template fills in verbatim — treat it as
the field contract, not a suggestion.

| Field | Required | Shape |
|---|---|---|
| `name` | yes | kebab-case, matches the filename stem (`agents/content-generation.md` → `name: content-generation`) |
| `description` | yes | block scalar (`>` or `\|`), third person, embeds 2–3 `<example>` blocks |
| `model` | yes | cost-tuned — see below |
| `color` | yes | a distinct color per agent, for the operator's visual scan of `agents/` |
| `tools` | opt-in | present (pinned list) or absent (see §4) — never an empty list |
| `maxTurns` | yes | integer turn budget, sized to the job (see below) |

**`description` block-scalar shape.** The description is prose first —
what the agent does, when to use it — then 2–3 `<example>` blocks, each with
this exact structure:

```yaml
description: >
  One or two sentences: what this agent does, and the one-line "use this
  agent when..." trigger condition.

  <example>
  Context: The situation the calling skill or user is in.
  user: "The literal or representative user utterance"
  assistant: "The literal or representative assistant reply that leads to
  delegation"
  <commentary>
  Why this example justifies routing to the agent — tie it back to the
  when-to-add gate (heavy search, long-form/batch generation, or QA sweep).
  </commentary>
  </example>

  <example>
  ...second example, same shape...
  </example>
```

Two examples is the floor; three when the agent covers genuinely distinct
trigger situations (e.g., one example from direct user request, one from a
skill delegating). Don't pad to three with a near-duplicate of example one.

**`model:` — cost-tuned, not defaulted.**

| Job shape | Model | Why |
|---|---|---|
| Generation (long-form, batch, creative) | `sonnet` | Needs real generation quality |
| Heavy search/triage | `sonnet` | Multi-phase reasoning over ranked, conflicting sources |
| QA / validation sweep | `haiku` | Structured checklist against known criteria — cheap model, cheap job |

Don't default every agent to `sonnet` out of caution. A QA agent running a
fixed checklist doesn't need generation-grade reasoning; pin `haiku` and let
the turn budget, not the model, be the safety margin.

**`maxTurns:`** — set from the job's real shape, not a round number pulled
from nowhere. Search/triage jobs that fan out across platforms run longest
(20–25). Generation jobs sit in the middle (12–15). QA sweeps are shortest
(8–10) — a validation pass against a fixed checklist doesn't need deep
exploration.

**`tools:`** — see §4, it's load-bearing enough to get its own section.

## 4. Tool scoping is load-bearing, and opt-in

`tools:` is not a formality field — it's the actual authorization boundary
for what the agent can touch once dispatched. Two shapes, chosen
deliberately per agent:

**Read/analysis agents — pin the list.**

```yaml
tools:
  - Read
  - Glob
  - Grep
```

Anything that generates, validates, or triages content the calling skill
already handed it — not searching live external platforms — gets this
pinned triad. It can read what it's given and scan for patterns; it can't
reach out to a connector, write a file, or run a command. Both
`content-generation` and `quality-assurance` use exactly this list.

**Broad-search agents — omit `tools`, with a comment.**

```yaml
model: sonnet
color: cyan
maxTurns: 25
# tools not restricted — this agent needs all available MCP tools to search platforms
---
```

An agent whose entire job is searching across whatever platforms the user
has connected (Notion, Slack, Drive, Confluence, Box, ...) can't be scoped
to a fixed tool list at authoring time — the set of live connectors is a
runtime fact of the specific Cowork install, not something the plugin author
can enumerate in advance. Omitting `tools` grants the full available set;
the trailing comment is mandatory, not decorative — it's the difference
between "we forgot to scope this" and "we considered scoping and this is
why it's open."

**Never leave `tools:` present but empty, and never omit it silently.**
Absence must be explained inline. A reviewer scanning `agents/*.md` should
never have to guess whether an unscoped agent was a deliberate call or an
oversight.

## 5. Skill → agent delegation shape

An agent is never invoked directly by the Cowork end user — it's dispatched
by a skill, for the one heavy step that skill can't do inline. The skill
stays the thin orchestrator: it owns the Trigger, the Inputs, the
conversation with the user, and it hands off the expensive middle step to
the agent by name, then resumes for Output Format and After.

Concretely, inside the skill's `## Steps`:

```markdown
### 4. Generate Content

Create content that matches brand voice attributes and follows tone
guidelines for this content type.

For complex or long-form content, delegate to the content-generation
agent (defined in `agents/content-generation.md`).
For high-stakes content, delegate to the quality-assurance agent
(defined in `agents/quality-assurance.md`) for validation.
```

That's the whole shape: a sentence naming the agent and pointing at its
file, placed at the exact step where the heavy work happens. The skill body
doesn't restate the agent's algorithm or its output format — that's the
agent's own file. The skill doesn't narrate the agent's internal turns to
the user either; it receives the agent's result and continues its own
Output Format / After sections as if that step were any other.

If a skill needs to delegate to more than one agent, each delegation gets
its own named pointer at its own step — don't collapse "call agent A, then
agent B" into a single vague sentence. The reader (you, auditing this later,
or Claude re-reading its own instructions mid-conversation) needs to resolve
each delegation to a specific file without re-deriving intent.
