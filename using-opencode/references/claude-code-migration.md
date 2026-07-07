> Verified 2026-07-06 against https://opencode.ai/docs/rules and /docs/agents. Re-check if OpenCode has shipped changes.

# Claude Code → OpenCode migration

## Concept mapping

| Claude Code | OpenCode | Notes |
|---|---|---|
| `CLAUDE.md` (project) | `AGENTS.md` (project) | OpenCode reads `CLAUDE.md` as fallback if no `AGENTS.md`. First match per category wins. |
| `~/.claude/CLAUDE.md` (global) | `~/.config/opencode/AGENTS.md` | `~/.claude/CLAUDE.md` used as fallback. |
| `settings.json` / `.claude/settings.json` | `opencode.json` / `opencode.jsonc` | Schema: `https://opencode.ai/config.json`. |
| `.claude/` project dir | `.opencode/` | Holds agents, commands, etc. |
| `~/.claude/skills/<name>/SKILL.md` | read natively | Also `.opencode/`. Disable via `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`. |
| Subagents (`.claude/agents/*.md`) | agents: `opencode.json` `agent{}` block or `.opencode/agents/*.md` or `~/.config/opencode/agents/*.md` | Markdown filename = agent name. `mode: primary \| subagent \| all`. |
| Slash commands | commands | See /docs/commands. |
| Hooks | plugins | See /docs/plugins. |
| Permissions in settings | `permission` field | Values `ask`/`allow`/`deny`, glob-matched, per-agent overrides. |
| `/init` → CLAUDE.md | `/init` → AGENTS.md | Scans repo, may ask questions, writes/updates AGENTS.md. |
| MCP servers | MCP servers | See /docs/mcp-servers. |

## Compatibility opt-out

- `OPENCODE_DISABLE_CLAUDE_CODE=1` — disable all `.claude` support
- `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` — disable only `~/.claude/CLAUDE.md`
- `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` — disable only `.claude/skills`

## Rule-file precedence

OpenCode looks for rule files in this order, and the first match per category wins:

1. Local files, walking up from the current directory (`AGENTS.md`, then `CLAUDE.md`)
2. Global `~/.config/opencode/AGENTS.md`
3. `~/.claude/CLAUDE.md` (unless disabled via env var)

If both `AGENTS.md` and `CLAUDE.md` exist locally, only `AGENTS.md` is used.
