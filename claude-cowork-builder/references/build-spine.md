# Build spine — full phase-by-phase walkthrough

Six phases, Phase 0 through Phase 5. Run them in order for a new plugin (menu
option 1). Other menu entries jump in partway — see **Menu shortcuts** below.

## Phase 0 · Charter

**Goal:** Pin down what plugin you're building before touching any files.

**Resolve:**
- The problem this plugin solves, in one sentence.
- The Cowork audience — who runs this inside Cowork, and how technical they are (default: nontechnical/light-technical).
- External tools the plugin touches (Drive, Slack, a REST API, none).
- How it will be invoked — interactive tasks, scheduled tasks, or both. Scheduled use changes the output and guard rules (`cowork-runtime.md` § Scheduled tasks).

Skip questions the request already answers. If oiler's prompt states the
problem, audience, and tools up front, don't re-ask — restate them back and
move on.

**Output:** A one-paragraph charter: problem + audience + tools touched.

## Phase 1 · Distribution

**Goal:** Lock the two first-class distribution decisions before any
component work starts, because they determine what Phase 4 emits.

**Resolve:**
- **Install path** — Individual (app settings) vs. Marketplace. Default: Individual.
- **Visibility** — Private/internal vs. Public/shared. Default: Private.

**The coupling rule (verbatim):** *Private→individual→concrete config;
Public→marketplace→`~~category` genericize + branding metadata +
`marketplace.json` + `CHANGELOG`.*

"Going public" is the trigger to genericize — it's not a standalone toggle.
Confirm both decisions together, not independently.

Full detail — private vs. public artifact sets, versioning, packaging,
validation: `distribution.md`.

**Output:** Install + visibility locked.

## Phase 2 · Component plan

**Goal:** Decide what layers this plugin ships, and write down what it
declines and why — not just what it includes.

**Resolve:**
- Which skills (command / knowledge / router) this plugin needs, primary layer.
- Whether MCP connectors are needed, and which categories.
- Whether an agent is justified — only if the `agent-playbook.md` gate passes. Default is no agent.
- Whether custom UI is needed — a static HTML deliverable (shipped + copied), an authored artifact from a sanitized payload (a prominent snapshot in the Artifacts view), or a Live Artifact (connector-refreshed); three surfaces, chosen per `live-artifacts.md` §3. Default is none.
- Where mutable state lives, if the plugin remembers between runs — working folder vs. versioned snapshots in connected storage. This decision couples to schedulability; resolve it here per `skill-authoring.md` § Where mutable state lives.
- Whether a router skill is needed — default heuristic: only when skill count ≥ 8.

**Output:** A component table, one row per component type considered —
**including declined types**, each with a one-line reason:

| Component | Included? | Reason |
|---|---|---|
| Command skill(s) | Yes | Primary layer — user-facing actions |
| Knowledge skill(s) | Yes/No | … |
| Router skill | No | Skill count < 8 |
| Agent | No | No autonomous multi-step job — `agent-playbook.md` gate fails |
| MCP connector | Yes/No | … |
| Custom UI (deliverable / authored artifact / Live Artifact) | No | No persistent UI need |

Don't skip the "No" rows — the table's value is showing what was considered
and declined, not just what shipped.

## Phase 3 · Component design

**Goal:** Turn the Phase 2 plan into concrete specs for each included
component — enough detail that Phase 4 is pure scaffolding, no more decisions.

**Resolve, per component:**
- Triggers — what phrasing fires this skill (command) or auto-triggers it (knowledge).
- `references/` needs — does this component need its own detail file.
- Tool scoping — for agents, which tools are pinned vs. omitted.
- Standalone/supercharged fallback — the zero-connector path and the connected path.
- Agent contracts — if an agent is in the plan, its frontmatter fields and the skill→agent delegation shape.
- Cowork gates — list every design fact that can only be verified in a live Cowork session (a connector's actual tool surface, artifact behavior, egress/proxy quirks), each with a designed fallback for the unfavorable outcome. The list carries into Phase 5 and gets re-verified after the first real session; a gate without a recorded fallback is an unresolved design decision.

Route to the detail reference for each component type:
- Skills (command/knowledge/router) → `skill-authoring.md`
- Agents → `agent-playbook.md`
- MCP connectors → `connectors-and-mcp.md`

**Output:** Per-component specs, ready to scaffold.

## Phase 4 · Scaffold

**Goal:** Emit the real plugin directory. This phase writes files — no more
open decisions should surface here; anything unresolved sends you back to
Phase 2 or 3.

**Order of operations:**
1. Directory tree — including `.claude-plugin/` at the plugin root.
2. `.claude-plugin/plugin.json` — the manifest lives inside `.claude-plugin/`, never at the plugin root; everything else lives at the plugin root, never inside `.claude-plugin/`.
3. Each component, from its template (`assets/templates/`).
4. `CONNECTORS.md` + `.mcp.json` (plugin root).
5. `README.md`.
6. Plugin-is-its-own-repo: copy `assets/templates/Makefile` to the repo root — it is the default packaging path (`distribution.md` §6).

**Rules while scaffolding:**
- Every intra-plugin path reference uses `${CLAUDE_PLUGIN_ROOT}` — never a hardcoded or relative path.
- All names (plugin, skills, files) are kebab-case.

**Output:** A complete plugin directory, ready for audit.

## Phase 5 · Audit + package

**Goal:** Catch defects before they ship — wrong filenames, missing
fallback paths, out-of-sync placeholders — then produce the installable
artifact.

**Resolve, in order:**
1. Run the validator — `uv run ${CLAUDE_SKILL_DIR}/scripts/validate_plugin.py <plugin-dir>`. It is the authority for every `[script]`-tagged item in `audit-checklist.md`; fix failures and re-run until it exits 0. Don't re-derive its checks by hand.
2. Walk the `[judgment]` items and the model-owned halves of the `[script-assisted]` items in `audit-checklist.md`.
3. Don't package a plugin that fails either half.

**Output:** An installable `.plugin` — `make plugin && make verify` for a plugin-is-its-own-repo layout, the canonical zip command inside a container repo (`distribution.md` §6).

---

## Menu shortcuts

Not every session starts at Phase 0. From the build menu:

- **Entry 2 (Add an integration)** → jumps to **Phase 3**. Distribution is
  already locked for an existing plugin; go straight to designing the new
  component.
- **Entry 3 (Add a component)** → jumps to **Phase 3**. Same reasoning —
  no need to re-charter or re-decide distribution for an addition.
- **Entry 4 (Audit + package)** → jumps to **Phase 5**. The plugin is
  already built; just verify and ship.

Only **Entry 1 (New plugin from scratch)** runs the full Phase 0→5 spine.
