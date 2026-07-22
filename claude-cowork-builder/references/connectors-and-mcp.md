# Connectors and MCP — wiring external tools

This reference covers the `~~category` placeholder system, the `CONNECTORS.md`
table format, and the four `.mcp.json` server shapes. Read it whenever Phase 2
or Phase 3 of the build spine includes an MCP connector, or when adding an
integration to an existing plugin (menu entry 2).

## The `~~category` system

Skills reference external tools by **category**, never by product name. A
skill body never says "check Slack" or "pull from Google Drive" — it says
`~~messaging` or `~~document store`. The category is the stable name; the
product behind it can change without touching skill prose.

Why category and not product:

- A plugin author who wires in a different Slack-alternative MCP server
  shouldn't have to grep every skill file for the string "Slack."
- A Cowork end user's connected tool is a runtime fact, not a build-time one —
  the skill can't assume which product is live.
- Standalone/supercharged fallback (see `skill-authoring.md`) reads cleanest
  when the "with connector" branch names a category, not a brand.

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

Skills in this plugin refer to external tools by category, never by
product name — you'll see placeholders like `~~document store` or
`~~messaging` in skill bodies instead of a specific product. This table
maps each placeholder to what's actually connected in `.mcp.json` for
this plugin, and what else you could swap in instead.
```

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

`.mcp.json` lives at the plugin root, alongside `CONNECTORS.md`. It declares
`mcpServers`, one entry per connector. Four shapes cover everything this
builder wires up. Reproduce these verbatim — don't invent a fifth shape.

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

## Security

- **Secrets go through environment variables, never literals.** `${SERVICE_TOKEN}`, `${SLACK_CLIENT_ID}` — every credential in `.mcp.json` is a `${VAR}` substitution. A literal API key or bearer token committed into `.mcp.json` is a Phase 5 audit failure, not a style nit.
- **HTTPS only for remote servers.** Every `http` and `sse` entry's `url` is `https://` — no plaintext remotes, no exceptions for "internal" or "trusted" endpoints.
- **Document every required env var in `README.md`.** If `.mcp.json` references `${SERVICE_TOKEN}`, the plugin's `README.md` says what it is, where the plugin owner gets it, and that it must be set before the connector will work. A plugin that ships a `${VAR}` reference with no corresponding README entry leaves the owner guessing what to configure.
- **Remote sessions may not reach your remote server.** Remote-session egress goes through a mandatory allow-list proxy, and Enterprise defaults to no network (`cowork-runtime.md`). Treat "connector unreachable" as an expected runtime state, not an error — it's another reason the standalone path is mandatory.
