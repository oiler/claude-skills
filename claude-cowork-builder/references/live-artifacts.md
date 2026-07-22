# Custom UI — static HTML deliverables vs. Live Artifacts

Two genuinely different surfaces get called "custom UI" in Cowork work, and they are easy to conflate (the original plugin-corpus survey did exactly that, under the name "Live Artifacts"). They share nothing operationally:

- A **static HTML deliverable** is a file the plugin ships and copies into the user's working folder. Corpus-verified pattern — observed in official plugins.
- A **Live Artifact** is a managed Cowork feature: a persistent, connector-refreshed page in the Artifacts view. Facts below are from Anthropic's support article ("Use live artifacts in Claude Cowork", https://support.claude.com/en/articles/14729249, checked 2026-07-22).

The default for a new component is still *neither* (`build-spine.md`, Phase 2). Pick a surface only when chat turns genuinely can't carry the interaction, then pick which surface using §3.

## 1. Static HTML deliverable — the ship-and-copy pattern

A single static HTML file — no build step, no server, no framework runtime — shipped inside the plugin and copied out into the user's working folder at run time. Once copied it's a plain local file the user opens in a browser: frozen at copy time, fully offline, no connection back to Claude or to connectors. Useful for a snapshot dashboard, a formatted reference, a portable report shell.

**Placement.** The file — `dashboard.html` — lives directly under the plugin's `skills/` directory, as a sibling of the skill subfolders, **not** nested inside any individual skill's own directory:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── agents/
├── skills/
│   ├── dashboard.html          ← here, not inside a skill subfolder
│   ├── start/
│   │   └── SKILL.md
│   └── some-other-skill/
│       └── SKILL.md
└── CONNECTORS.md
```

It sits at that level because more than one skill may need to hand it out, and because a skill subfolder is scoped to one skill's own frontmatter and body — the file is a plugin-level asset, not owned by any single skill.

**Wiring.** A `start`-style command skill delivers it: copy the file into the user's working folder, then tell the user where it landed. The copy source is always the plugin-root-relative path:

```
${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html
```

Never a hardcoded or relative path — same rule as everywhere else in this builder (`SKILL.md` → Hard rules), and it matters more here because the plugin's install location is genuinely unknown at authoring time.

This is the Cowork output-hygiene rule (`skill-authoring.md` → "Cowork output hygiene") applied to one artifact type, not a separate rule set:

- Copy destination is the user's **working folder** — never the plugin's own install directory, never an arbitrary temp path.
- The path told back to the user is a **real, resolved path**, not a relative one.
- The skill **never** calls `open` or `xdg-open`, and never implies the file opened itself — it runs in a VM with no ability to pop a window on the user's machine.
- The skill's last move is to **tell the user the path** — "I've copied the dashboard to your working folder as `dashboard.html` — open it in your browser to get started."

Worked shape, inside the `start` skill's `## Steps`:

```markdown
### 1. Copy the dashboard

Copy `${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html` into the user's working
folder. Tell the user the resulting path and that they can open it in a
browser — never attempt to open it directly.
```

Any skill may re-run the same copy step (a "reset dashboard" path, a deleted copy) — the rule is about the copy mechanics and messaging, not which skill performs it.

**Branding.** Default neutral and brandable:

- **Inline SVG favicon** — data URI or inline `<svg>`, never a second shipped asset file (one more placement and relative-path failure mode).
- **Self-contained CSS** — all styling in a `<style>` block; no external stylesheet, CDN font, or icon-font link.
- **No external fetches of any kind** — no CDN scripts, no remote `fetch()`, no analytics beacons. The file must render and function fully offline, from disk, exactly as shipped.

Theming (brand colors, a logo) is an enhancement layered onto a working self-contained file, never a prerequisite for shipping one.

## 2. Live Artifacts — the Cowork feature

What the feature actually is, per the support article:

- A **persistent, interactive HTML page** Claude creates in Cowork, living in the **Artifacts view** on Claude Desktop — not in the working folder, not opened from disk by the user.
- It **refreshes with current data from connected apps**: a short cache makes it load fast, it re-queries connectors on its own, and a manual refresh button sits in its header.
- **Version history**: every iteration with Claude saves the previous version; users can compare and restore.
- Created by **asking Claude during a Cowork task** ("build me a tracker that pulls from…") or via Artifacts view → New artifact → Create Cowork artifact.
- **Constraints**: desktop-only (macOS/Windows/Linux beta), paid plans, stored locally per device (doesn't follow the user across devices). Team/Enterprise sharing opens the artifact with the **viewer's** connectors, not the author's.
- **Security property that matters to plugin authors**: Live Artifacts *use connectors without asking* — no approval prompt, even in session modes that normally require one.

**The plugin's role is prompt-level only.** There is no documented packaging surface for Live Artifacts: no manifest field, no file format, no `${CLAUDE_PLUGIN_ROOT}` mechanism, no way to ship one inside a `.plugin`. Do not invent one. The only path a plugin has is instructional — a skill's `## Steps` can direct Claude to create or update a Live Artifact during the Cowork task:

```markdown
### 3. Build the tracker

Create a live artifact: a tracker for [the thing], pulling current data
from ~~project tracker and ~~messaging. Keep it to one screen; the user
will iterate on layout in follow-ups.
```

Rules when a skill does this:

- **Name data sources by `~~category`**, same as everywhere else (`connectors-and-mcp.md`) — the live artifact will bind to whatever the user actually has connected.
- **Disclose the auto-refresh behavior in user-facing copy.** Because live artifacts read connectors without approval prompts, a skill that spawns one quietly widens what the plugin touches. The skill's user-facing output says, in plain language, that the artifact keeps itself current from their connected tools. This is an audit item (`audit-checklist.md` item 9).
- **The standalone floor still applies.** With zero connectors, the skill either builds the artifact from pasted/uploaded data (static content, no refresh) or falls back to a §1 static deliverable — it never hard-fails for want of a connector.
- **Desktop/plan caveats are the user's reality, not yours to detect.** Don't try to sniff the environment; if artifact creation isn't available, Claude will surface that in-task, and the skill's fallback path covers it.

## 3. Choosing a surface

| Actual need | Use |
|---|---|
| One-off report or summary | Neither — a skill writes the file and tells the user where it is |
| A form or a few inputs | Neither — ask conversationally, turn by turn |
| Snapshot dashboard: offline, portable, frozen at generation time | §1 static deliverable |
| Persistent tracker/dashboard the user revisits and that must stay current with connector data | §2 Live Artifact (accepting desktop-only + paid-plan constraints) |
| "It would look nicer as a UI" with no persistence or interactivity requirement | Neither — chat is the default surface; don't dress up what chat already handles |

Per `build-spine.md` Phase 2, the default answer to "does this plugin need custom UI" is no. Add a surface only when the need is real, and be able to say in one sentence what interaction it supports that chat turns don't.
