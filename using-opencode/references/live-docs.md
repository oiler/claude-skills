# Finding & verifying current OpenCode docs

## Canonical URL map

Base: `https://opencode.ai/docs/`. Each URL is base + slug + `/`.

| Page | URL | What's here |
|------|-----|-------------|
| `config` | https://opencode.ai/docs/config/ | The opencode.json/.jsonc config file: schema, top-level keys |
| `providers` | https://opencode.ai/docs/providers/ | Provider setup, credentials, custom providers |
| `rules` | https://opencode.ai/docs/rules/ | AGENTS.md, precedence, Claude Code compatibility fallbacks |
| `agents` | https://opencode.ai/docs/agents/ | Primary agents & subagents, per-agent model/permission/mode |
| `models` | https://opencode.ai/docs/models/ | Selecting models, recommended list, model IDs, variants |
| `commands` | https://opencode.ai/docs/commands/ | Custom slash commands |
| `permissions` | https://opencode.ai/docs/permissions/ | The ask/allow/deny permission system |
| `mcp-servers` | https://opencode.ai/docs/mcp-servers/ | Configuring MCP servers |
| `skills` | https://opencode.ai/docs/skills/ | Agent Skills (SKILL.md) support in OpenCode |
| `plugins` | https://opencode.ai/docs/plugins/ | Plugin API (the hooks analog) |
| `tools` | https://opencode.ai/docs/tools/ | Built-in tools and enabling/disabling them |
| `keybinds` | https://opencode.ai/docs/keybinds/ | Keybindings |
| `zen` | https://opencode.ai/docs/zen/ | OpenCode Zen curated model gateway |
| `share` | https://opencode.ai/docs/share/ | Sharing conversations |
| `cli` | https://opencode.ai/docs/cli/ | Command-line flags and usage |
| `tui` | https://opencode.ai/docs/tui/ | Terminal UI |
| `references` | https://opencode.ai/docs/references/ | Config schema reference |
| `troubleshooting` | https://opencode.ai/docs/troubleshooting/ | Diagnosing issues |

## When to fetch

OpenCode ships fast, so some facts go stale. Fetch the live docs before answering when the question touches any version-sensitive area:

- **Model IDs or the recommended-model list** — the curated set and its IDs change.
- **The provider count** — the number of supported providers grows over time.
- **Newly shipped features** — anything the user frames as recent, or that you don't recognize.
- **Config field names or shapes** — key names, nesting, and accepted values drift.
- **Anything the embedded best-practices digest flags with a verify pointer** — treat that pointer as an instruction to fetch.

## How to fetch

Try these in order and stop at the first that works:

1. `webfetch` the mapped URL directly.
2. If `webfetch` is permission-denied in OpenCode, either dispatch the read-only `scout` subagent to research the external docs, OR ask the user to approve webfetch.
3. If neither is available, answer from the embedded digest and EXPLICITLY flag the claim as possibly stale, citing the relevant verify URL from the map above.

## Staleness triage

If a digest fact conflicts with the live docs, the live docs win. Note the discrepancy — including which page it came from — so the embedded digest can be refreshed later.
