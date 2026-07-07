---
name: using-opencode
description: >-
  On-demand guide for using OpenCode well, especially when coming from Claude Code.
  Use when the user explicitly asks for help WITH OpenCode itself: "help me with OpenCode",
  "how do I do X in OpenCode", "OpenCode best practice", "what's the OpenCode equivalent of",
  "coming from Claude Code", "migrate from Claude Code to OpenCode", "CLAUDE.md vs AGENTS.md",
  "settings.json vs opencode.json", "set up multi-model in OpenCode", "run different models
  in parallel", "use OpenAI/Gemini/Anthropic side by side in OpenCode", or names this skill
  ("using-opencode"). Also covers finding current OpenCode docs. Do NOT trigger merely because
  a session is running inside OpenCode. Routes config-file EDITING to customize-opencode and
  parallel fan-out EXECUTION to orko / dispatching-parallel-agents.
---

# Using OpenCode

On-demand reference for using OpenCode effectively — especially for users migrating from Claude Code.

## When to use / When NOT to use

Use this skill when the user explicitly asks for help with OpenCode itself:

- "help me with OpenCode"
- "how do I do X in OpenCode"
- "OpenCode best practice"
- "what's the OpenCode equivalent of ..."
- "coming from Claude Code" / "migrate from Claude Code to OpenCode"
- "CLAUDE.md vs AGENTS.md"
- "settings.json vs opencode.json"
- "set up multi-model in OpenCode" / "run different models in parallel"
- "use OpenAI/Gemini/Anthropic side by side in OpenCode"
- names this skill ("using-opencode")
- needs to find or verify current OpenCode docs

Do NOT trigger this skill merely because the current session happens to be running inside OpenCode. It fires on explicit questions ABOUT OpenCode, not on ambient use of it.

## Routing

| If the user wants... | Go to |
|---|---|
| Claude Code → OpenCode concept mapping | references/claude-code-migration.md |
| OpenCode usage best practices (modes, /init, sessions, permissions posture) | references/best-practices.md |
| Which model for which task + how to wire per-agent/parallel models | references/multi-model.md |
| To find/verify current official docs | references/live-docs.md |
| To EDIT opencode.json / agents / plugins / MCP / permissions | invoke the customize-opencode skill |
| To actually RUN a parallel multi-agent fan-out | invoke orko or dispatching-parallel-agents |

## Claude Code → OpenCode quick reference

| Claude Code | OpenCode |
|---|---|
| `CLAUDE.md` (project) | `AGENTS.md` (project); `CLAUDE.md` read as fallback |
| `~/.claude/CLAUDE.md` (global) | `~/.config/opencode/AGENTS.md`; `~/.claude/CLAUDE.md` fallback |
| `settings.json` / `.claude/settings.json` | `opencode.json` / `opencode.jsonc` |
| `.claude/` | `.opencode/` |
| `~/.claude/skills/` | read natively by OpenCode (compat) |
| subagents (`.claude/agents/`) | agents: `opencode.json` `agent{}` or `.opencode/agents/*.md` |
| hooks | plugins |
| `/init` → CLAUDE.md | `/init` → AGENTS.md |

## Live-fetch rule

OpenCode moves fast; several answers are version-sensitive. Treat the following as version-sensitive: model IDs, the provider list, newly added features, and config field names.

When a question is version-sensitive:

1. Fetch the page mapped in `references/live-docs.md` before answering — do not answer from memory.
2. If `webfetch` is permission-denied in OpenCode, either ask the user to approve it or dispatch the read-only `scout` subagent to read the page.
3. If neither is available, answer from the digest in the reference files and explicitly flag the answer as possibly stale, citing the verify URL so the user can confirm.

## References

- **references/claude-code-migration.md** — read when the user is coming from Claude Code and needs the concept-by-concept mapping (config files, agents, hooks/plugins, skills compat).
- **references/best-practices.md** — read for OpenCode usage guidance: modes, `/init`, session hygiene, and permissions posture.
- **references/multi-model.md** — read for which model to pick for which task and how to wire per-agent or parallel models.
- **references/live-docs.md** — read to find or verify current official docs, especially for version-sensitive answers (see the Live-fetch rule above).
