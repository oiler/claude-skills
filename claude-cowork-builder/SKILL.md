---
name: claude-cowork-builder
description: Build full-featured Claude Cowork plugins the opinionated way — skills, agents, MCP connectors, and custom UI packaged into an installable .plugin. Use when building, creating, scaffolding, or packaging a Cowork plugin, adding a Cowork integration or connector, wiring Google Drive into Cowork, converting a workflow into a Cowork plugin, or auditing a Cowork plugin. Triggers on "Cowork plugin", "build a Cowork plugin", "create a Cowork plugin", "Cowork integration", "package a .plugin", "Cowork Google Drive", "knowledge-work plugin". NOT for WordPress plugins (use wordpress-plugins) or generic non-Cowork Claude Code plugin questions.
---

# claude-cowork-builder

Opinionated builder for Claude Cowork plugins. It encodes the Cowork plugin format directly — frontmatter fields, layer types, packaging rules — rather than delegating to Anthropic's Cowork-only skill, so it works standalone in Claude Code. It is operated here by oiler, a technical user; this SKILL.md and its references speak in terse, decision-dense engineering language. The plugins it emits are a different audience: nontechnical Cowork end users. That distinction matters everywhere except this file.

## The build menu

```
╭─ claude-cowork-builder ─────────────────────────────────────────────╮
│  START                                                              │
│   1) New plugin from scratch     2) Add an integration              │
│   3) Add a component             4) Audit + package                 │
│                                                                     │
│  DISTRIBUTION                                                       │
│   Install:     (•) Individual      ( ) Marketplace                  │
│   Visibility:  (•) Private         ( ) Public → genericize + meta   │
│                                                                     │
│  SKILLS  (primary layer — pick per skill)                           │
│   [x] Command skill   (argument-hint, /slash, $1 args, user-facing) │
│   [ ] Knowledge skill (auto-trigger; user-invocable:false to hide)  │
│   [ ] Router skill    (intent→skill dispatch; for big plugins)      │
│       standalone+supercharged fallback copy: emitted by default     │
│                                                                     │
│  OPTIONAL LAYERS                                                    │
│   [ ] Agent           (playbook-gated; builder justifies + scopes)  │
│   [ ] Custom UI       (static HTML deliverable / Live Artifact)     │
│   [ ] MCP connector   (http / sse / stdio / bearer)                 │
│                                                                     │
│  SPECIALTY INTEGRATIONS                                             │
│   [ ] Google Drive    ( curated, correct building block )           │
╰─────────────────────────────────────────────────────────────────────╯
```

Pick a START option, then walk the checkboxes top to bottom. Every decision has a pre-selected default — the board shows what "just build it" looks like. Deviate deliberately, not by omission.

## The spine at a glance

| Phase | What happens | Output |
|---|---|---|
| 0 · Charter | Problem, Cowork audience, external tools. One-paragraph charter. | Scope statement |
| 1 · Distribution | Install + visibility decisions, each with a default + tradeoff. | Install + visibility locked |
| 2 · Component plan | Skills (primary) + MCP; agents only if playbook justifies; router if large; custom UI (deliverable or Live Artifact) only if warranted. | Confirmed components |
| 3 · Component design | Per component: triggers, references, tool scoping, standalone/supercharged, agent contracts. | Specs |
| 4 · Scaffold | .claude-plugin/plugin.json, skills, CONNECTORS.md, .mcp.json, README, optional agents/static-UI asset. | Plugin directory |
| 5 · Audit + package | Run the audit checklist → package .plugin. | Installable artifact |

Full walkthrough of every phase: `references/build-spine.md`.

## Routing table

| When you're… | Read |
|---|---|
| Running the full build | references/build-spine.md |
| Authoring skills (command/knowledge/router) | references/skill-authoring.md |
| Wiring external tools | references/connectors-and-mcp.md |
| Deciding whether to add an agent | references/agent-playbook.md |
| Choosing install/visibility & packaging | references/distribution.md |
| Custom UI (static deliverable / Live Artifacts) | references/live-artifacts.md |
| Pre-package check | references/audit-checklist.md |
| Adding Google Drive | integrations/google-drive/recipe.md |

## The two first-class defaults

Default lean: Private + Individual install; switch to Public → genericize + add marketplace metadata.

## Hard rules

- Every skill file is named exactly `SKILL.md` — wrong filename fails silently, no error surfaces.
- The manifest lives at `.claude-plugin/plugin.json` — at the plugin root it isn't found. Components (`skills/`, `agents/`, `.mcp.json`) live at the root, never inside `.claude-plugin/`.
- Every command skill works with zero connectors — the user can paste, upload, or describe the input instead. The connected `~~category` path is additive, never required.
- Cowork output hygiene: outputs go to the user's working folder; no relative paths; no `open`/`xdg-open` (the skill runs in a VM); always tell the user the exact path that was written.
- What the plugin says to Cowork users stays nontechnical — no schema-speak, raw `~~` tokens, or plugin-internal file names in user-facing copy.
- Reference the plugin root as `${CLAUDE_PLUGIN_ROOT}`, never a hardcoded or relative path — plugins install into locations the author doesn't control.
- Agents are exceptional, not default: add one only when a playbook justifies it, and scope it as tightly as that playbook allows.
