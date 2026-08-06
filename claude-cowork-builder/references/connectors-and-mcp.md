# Connectors and MCP — wiring external tools

This reference covers the `~~category` placeholder system, the `CONNECTORS.md`
table format, and the five `.mcp.json` server shapes. Read it whenever Phase 2
or Phase 3 of the build spine includes an MCP connector, or when adding an
integration to an existing plugin (menu entry 2).

Sources: `${VAR}` / `${user_config.KEY}` substitution, the supported `.mcp.json` keys, and MCP tool scope-renaming come from https://code.claude.com/docs/en/plugins-reference (checked 2026-08-05); shape frequencies and the `~~category` vocabulary come from Anthropic's knowledge-work plugin corpus.

## The `~~category` system

Skills reference external tools by **category**, never by product name. A
skill body never says "check Slack" or "pull from Google Drive" — it says
`~~chat` or `~~cloud storage`. The category is the stable name; the
product behind it can change without touching skill prose.

Why category and not product:

- A plugin author who wires in a different Slack-alternative MCP server
  shouldn't have to grep every skill file for the string "Slack."
- A Cowork end user's connected tool is a runtime fact, not a build-time one —
  the skill can't assume which product is live.
- Standalone/supercharged fallback (see `skill-authoring.md`) reads cleanest
  when the "with connector" branch names a category, not a brand.

**Prefer corpus vocabulary when one fits.** Anthropic's own plugins converge on a small set of category names — counted at mirror `2099f2c`, the most-used are `~~chat` (77), `~~project tracker` (54), `~~email` (50), `~~knowledge base` (46), `~~cloud storage` (42), and `~~CRM` (18). Reach for one of those before coining a synonym, and check the count rather than guessing: plausible-sounding tokens like `~~messaging` and `~~document store` appear **zero** times in the corpus. Category names are per-plugin, so a plugin-specific name is still legitimate (this builder's Drive recipe ships `~~file storage`, and the illustrative tables below use names of their own); just pick one name deliberately and hold it across all four sync locations. Tokens are routinely multi-word and may be acronym-cased (`~~CRM`, `~~HRIS`, `~~ATS`) — that is corpus-normal, not a violation.

**`~~` tokens live in skill bodies only — never in `description` frontmatter.**
The description is the trigger surface, matched against what a user actually
types, and no user types `~~file storage`. Descriptions use plain language
for the category ("the user's connected file storage"). While the plugin is
private, a description may also name the concrete product ("Google Drive",
"search my Drive for…") for trigger accuracy — private plugins are allowed
concrete names everywhere (`distribution.md` §3). Going Public genericizes
descriptions along with bodies: product phrasing drops to category language
in the same pass (`distribution.md` §4).

**The four places a category placeholder must stay in sync.** Every
`~~category` token that appears in a skill body has three siblings, and all
four must agree on spelling and casing:

| Where it lives | What it looks like |
|---|---|
| `SKILL.md` (skill body prose) | `~~document store connected` |
| `CONNECTORS.md` (the lookup table) | `Placeholder` column: `~~document store` |
| `README.md` (setup instructions for the plugin owner) | Same token, in the "connectors this plugin uses" section |
| `.mcp.json` (server key name) | The server key doesn't have to equal the token literally, but it must map to the same category — see the table's "Included servers" column |

If you rename a category (e.g. `~~document store` → `~~file storage`),
rename it everywhere in the same pass. A stale token in one file and a
renamed one in another is the single most common Phase 5 audit failure —
Claude reading the skill mid-conversation has no way to reconcile "I was told
`~~file storage` is connected but the skill body asks about `~~document
store`."

## CONNECTORS.md — the lookup table

`CONNECTORS.md` lives at the plugin root. It is the single place that maps
every `~~category` token used anywhere in the plugin to what's actually
wired up in `.mcp.json`, plus what else could be wired up instead. Skills
point here (via the CONNECTORS banner in `skill-authoring.md`) rather than
explaining connector state inline.

Open the file with this preamble, verbatim in intent (adapt the specific
categories to the plugin, keep the framing):

```markdown
## How tool references work

Plugin files use `~~category` as a placeholder for whatever tool the user connects in that category. For example, `~~cloud storage` might mean Google Drive, Dropbox, or any other storage service with an MCP server.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (cloud storage, chat, email, etc.) rather than specific products. The `.mcp.json` pre-configures specific MCP servers, but any MCP server in that category works.
```

That is the corpus's own two-paragraph preamble, and `assets/templates/CONNECTORS.md` reproduces it. Adapt the example and the category list to the plugin; keep both paragraphs.

Below the preamble, one table, four columns, one row per category:

```markdown
| Category | Placeholder | Included servers | Other options |
|---|---|---|---|
| Document store | `~~document store` | Google Drive | Dropbox, Box, SharePoint |
| Messaging | `~~messaging` | Slack | Microsoft Teams |
| Email | `~~email` | Gmail | Outlook |
```

Column rules:

- **Category** — plain English, the thing being connected. Sentence case, no `~~`.
- **Placeholder** — the exact `~~category` token used in skill bodies. Must match character-for-character.
- **Included servers** — what this plugin actually ships in `.mcp.json` for this category, by product name. This is the only column where a product name is allowed — the table is the translation layer between category-speak (skills) and product-speak (the plugin owner configuring `.mcp.json`).
- **Other options** — products the plugin doesn't ship a server for but that fit the same category, so the plugin owner knows what they could swap in without editing skill bodies.

A category with no server configured yet still gets a row — its "Included
servers" cell points at the empty-url stub (below), so the plugin owner
knows exactly what to fill in.

## `.mcp.json` shapes

`.mcp.json` lives at the plugin root, alongside `CONNECTORS.md`. It declares `mcpServers`, one entry per connector. Five shapes cover what this builder wires up — the four below plus the `oauth` block (Slack, further down). Reproduce them verbatim rather than improvising a new one.

**HTTP remote:**

```json
{ "mcpServers": { "example-http": { "type": "http", "url": "https://…" } } }
```

**SSE remote:**

```json
{ "mcpServers": { "example-sse": { "type": "sse", "url": "https://…" } } }
```

**stdio, local process via `npx`:**

```json
{ "mcpServers": { "example-stdio": { "command": "npx", "args": ["-y", "@scope/server", "--stdio"] } } }
```

**HTTP remote with a bearer token:**

```json
{ "mcpServers": { "example-bearer": { "type": "http", "url": "https://…", "headers": { "Authorization": "Bearer ${SERVICE_TOKEN}" } } } }
```

Picking a shape:

| Shape | When |
|---|---|
| `http` | Remote MCP server, no auth header needed (rare — most remotes need a token) |
| `sse` | Remote MCP server that streams over SSE instead of plain HTTP |
| `command`/`npx` stdio | Server runs as a local process the plugin spawns — no remote URL at all. **Local sessions only:** local MCP servers don't run in remote sessions or scheduled tasks (`cowork-runtime.md`), so a stdio-only connector silently disappears there — pair it with a remote shape or make sure the standalone path carries the skill |
| `http` + `headers` (bearer) | Remote MCP server gated by a bearer token — the common case for anything requiring auth |
| `http` + `oauth` | Remote MCP server behind an OAuth handshake — Slack is the corpus example; see § Slack — shared OAuth block |

`type`, `url`, `command`, `args`, `headers`, and `oauth` are not the whole key set — `env` (environment variables for a stdio server) and `headersHelper` (a command that emits headers at connect time) are also supported. Use them when the connector genuinely needs them; don't add them decoratively.

Never hardcode a secret into the `url` or `headers` value. `${SERVICE_TOKEN}`
is an environment-variable substitution, not a literal string to fill in —
see Security, below.

## Empty-url stub — connector not yet configured

When a category is planned but the real server URL isn't known yet (common
during Phase 4 scaffolding, before the plugin owner has an account/token to
point at), ship the stub verbatim:

```json
{ "mcpServers": { "gmail": { "type": "http", "url": "" } } }
```

Mark every empty-url entry with a `*` in `.mcp.json`'s surrounding
documentation (a comment isn't valid JSON, so the marker lives in
`CONNECTORS.md` or `README.md` instead, next to that server's row) and
define the footnote once in each file that carries a `*` marker — a `*`
in a file whose footnote lives elsewhere is a dangling reference:

```markdown
`*` — Placeholder — MCP URL not yet configured
```

An empty-url stub is not a broken connector — it's a deliberately
unconfigured one. The plugin still packages and installs; the skill that
depends on it just runs its standalone (no-connector) path until the plugin
owner fills the URL in.

## Slack — shared OAuth block

Slack's MCP server (when included) uses an `oauth` block shape that shows up
identically across plugins. Copy it as-is when Slack is a connector —
`clientId` and `callbackPort` don't vary by plugin, only the token value
resolved through env vars does:

```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://…",
      "oauth": {
        "clientId": "${SLACK_CLIENT_ID}",
        "callbackPort": 3118
      }
    }
  }
}
```

`callbackPort: 3118` is the observed convention across Slack MCP configs —
treat it as a fixed value, not a per-plugin choice, unless something else on
the host machine is already bound to that port.

## Native connectors — capability model

The `~~category` a skill names may resolve at runtime to an **Anthropic-managed native connector** (Drive, Gmail, …) rather than an MCP server from `.mcp.json`. For a nontechnical Cowork audience the native connector is the default reality — it's what an org can approve without OAuth-token custody — and it is **narrower than the product's API**:

- Observed native tool surfaces can be **create-and-read only**: no update-in-place, no delete, no cell-level writes to spreadsheets. "Overwriting" a file by creating it again does not overwrite — it **duplicates**, and whichever skill later reads "the" file has an undefined pick. A flow that mutates a connector-hosted file in place corrupts silently; it does not fail loudly.
- **Design rule: be a read-mostly, append-only citizen of the user's connected storage.** Read what the user owns (config they edit), create immutable dated files (reports, exports), and never update a file or cell in place through a native connector. Mutable state belongs in the working folder — or, when it genuinely must be shared and durable, in immutable versioned snapshots (`state-<timestamp>`, read newest, write a new one on change), which a create-only surface supports. See `skill-authoring.md` § Where mutable state lives.
- **Probe capability from the tool surface, never by writing.** To learn what a connection can do this session, read which tools are actually available; do not create a probe file in the user's storage.
- The exact tool surface is live Cowork behavior — treat it as a **Cowork gate** (`build-spine.md` Phase 3): verify in a real session, and record a designed fallback for the narrower outcome.

## Security

- **Secrets go through environment variables, never literals.** `${SERVICE_TOKEN}`, `${SLACK_CLIENT_ID}` — every credential in `.mcp.json` is a `${VAR}` substitution. A literal API key or bearer token committed into `.mcp.json` is a Phase 5 audit failure, not a style nit.
- **`userConfig` is the better ask for anything the plugin owner must supply.** A bare `${VAR}` assumes the owner already exported an env var and read the README. Declaring the value in the manifest's `userConfig` block instead makes Claude prompt for it when the plugin is enabled, substitute it as `${user_config.KEY}` into `.mcp.json` and hook commands, and export it as `CLAUDE_PLUGIN_OPTION_<KEY>`; marking it `sensitive: true` routes it to the OS keychain rather than a config file. Prefer it for tokens and account identifiers; keep raw `${VAR}` for values that genuinely come from the surrounding environment. Note the guardrail that comes with it: shell-form hook commands **reject** `${user_config.*}` substitution outright, so a value can never be interpolated into a shell string.
- **Every `userConfig` key carries a `title`.** Alongside `type`, `description`, and any `sensitive: true`, each key needs a short human-readable label — it's what the prompt shows the plugin owner instead of a bare `SERVICE_TOKEN`. It is not optional and not a strict-only nicety: `claude plugin validate` errors with `userConfig.<KEY>.title: Invalid input: expected string, received undefined` whether or not `--strict` is passed, so a `userConfig` block written without it fails the first validation run. A minimal key reads `{ "type": "string", "title": "Service API token", "description": "…", "sensitive": true }`.
- **HTTPS only for remote servers.** Every `http` and `sse` entry's `url` is `https://` — no plaintext remotes, no exceptions for "internal" or "trusted" endpoints. The rule governs urls that have a value. An empty `url: ""` is the declared-but-unconfigured stub above, not a plaintext remote — it names a category the plugin intends to serve and points nowhere at all, which is why it carries the `*` footnote rather than a scheme. Anthropic's own plugins ship it, and for a native connector (§ Native connectors, above) it is the finished state, since there is no endpoint to fill in.
- **Document every required env var in `README.md`.** If `.mcp.json` references `${SERVICE_TOKEN}`, the plugin's `README.md` says what it is, where the plugin owner gets it, and that it must be set before the connector will work. A plugin that ships a `${VAR}` reference with no corresponding README entry leaves the owner guessing what to configure.
- **Remote sessions may not reach your remote server.** Remote-session egress goes through a mandatory allow-list proxy, and Enterprise defaults to no network (`cowork-runtime.md`). Treat "connector unreachable" as an expected runtime state, not an error — it's another reason the standalone path is mandatory.

## Tool names are scope-renamed once installed

A plugin's MCP tools do not surface under the bare name the server advertises. They are renamed to `mcp__plugin_<plugin>_<server>__<tool>` — plugin name and `.mcp.json` server key both baked in. This only matters when something names a tool explicitly (an agent's `tools:`/`disallowedTools:` list, a hook matcher, a skill body that pins a tool by name): the bare name will not match. Naming categories rather than tools, the default everywhere else in this builder, sidesteps the problem entirely.
