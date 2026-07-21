# Live Artifacts — shipping a custom UI

A Live Artifact is the only Cowork-specific custom-UI surface. Everything
else in a plugin is conversational — skills, agents, connectors all resolve
to Claude talking with the user in chat. A Live Artifact is the one layer
that puts a persistent, interactive HTML surface in front of the user
instead. Reach for it deliberately; the default for a new component is
still "no Live Artifact" (`build-spine.md`, Phase 2).

## 1. What it is

A Live Artifact is a static HTML file — no build step, no server, no
framework runtime — shipped inside the plugin and copied out into the
user's working folder at run time. There's no live connection back to the
plugin, no Cowork-specific JS API, no MCP bridge baked into the page: once
copied, it's a plain file the user's browser opens like any other local
HTML file. "Live" describes the fact that the user keeps it open and
interacts with it across a session, not that it has a live channel back
into Claude.

Because it's just HTML, all the constraints below are about *how a single
static file has to behave* to be trustworthy and portable, not about a
Cowork-specific API surface to learn.

## 2. Ship + wire

**Placement.** The file — `dashboard.html` — lives directly under the
plugin's `skills/` directory, as a sibling of the skill subfolders. It is
**not** nested inside any individual skill's own directory:

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

It sits at that level because more than one skill may need to hand it out
or refer to it, and because a skill subfolder is scoped to one skill's own
frontmatter and body — the artifact isn't owned by any single skill, it's
a plugin-level asset.

**Wiring.** A `start`-style command skill is what actually delivers the
artifact to the user. Its job, at the relevant step, is exactly two things:
copy the file into the user's working folder, then tell the user where it
landed. The copy source is always the plugin-root-relative path:

```
${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html
```

Never a hardcoded or relative path — same rule as everywhere else in this
builder (`SKILL.md` → Hard rules), and it matters more here because the
plugin's install location is genuinely unknown at authoring time.

This is the Cowork output-hygiene rule (`skill-authoring.md` → "Cowork
output hygiene") applied to one specific artifact type, not a separate set
of rules:

- The copy destination is the user's **working folder** — never the
  plugin's own install directory, never an arbitrary temp path.
- The path told back to the user is a **real, resolved path**, not a
  relative one.
- The skill **never** calls `open` or `xdg-open` on the file, and never
  writes or implies language suggesting the file opened itself. The skill
  runs in a VM with no ability to pop a window on the user's machine.
- The skill's last move here is to **tell the user the path** — e.g. "I've
  copied the dashboard to your working folder as `dashboard.html` — open it
  in your browser to get started." — so the user can find and open it
  themselves.

Worked shape, inside the `start` skill's `## Steps`:

```markdown
### 1. Copy the dashboard

Copy `${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html` into the user's working
folder. Tell the user the resulting path and that they can open it in a
browser — never attempt to open it directly.
```

If the plugin needs the artifact re-copied later (e.g. a "reset dashboard"
path, or the user deleted their copy), any skill can perform the same copy
step — the rule is about the copy mechanics and messaging, not about which
skill is allowed to do it. `start` is just the conventional first place a
user encounters it.

## 3. Branding

Default the artifact to neutral and brandable, not to a specific product
identity:

- **Inline SVG favicon** — embed the favicon as a data URI or inline
  `<svg>`, not a linked `.ico`/`.png` file. A second shipped asset file is
  one more thing to place correctly and one more relative-path failure
  mode; an inline favicon has neither problem.
- **Self-contained CSS** — all styling lives in a `<style>` block in the
  same file. No external stylesheet, no CDN font, no icon-font link.
- **No external fetches of any kind** — no CDN script tags, no remote
  `fetch()` calls to third-party services, no analytics beacons. The
  artifact has no server behind it and no reliable network assumptions; it
  has to render and function fully offline, from disk, exactly as shipped.

This isn't a permanent restriction — a plugin author who wants a themed
dashboard (specific brand colors, a logo, custom typography) can absolutely
build that in. The point of the neutral default is that an unthemed
plugin still ships something that looks intentional, not a bare unstyled
HTML page — theming is an enhancement layered onto a working self-contained
file, never a prerequisite for shipping one.

## 4. When to use

Add a Live Artifact only when the plugin genuinely needs a **persistent,
interactive surface** that a conversational skill can't provide — a
dashboard the user keeps open and glances back at, a visualization that
updates shape as the user interacts with it, a layout too spatial for chat
turns to represent well. That's a narrow bar.

Skip it when the actual need is any of:

- A one-off report or summary → a skill just writes the file and tells the
  user where it is.
- A form or a few inputs → a skill can ask for them conversationally, turn
  by turn.
- "It would look nicer as a UI" without a persistence or interactivity
  requirement → conversational output is the default surface in Cowork;
  don't add a UI layer to dress up something chat already handles.

Per `build-spine.md` Phase 2, the default answer to "does this plugin need
a Live Artifact" is no. Add one only when the persistent-surface need is
real, and be able to say in one sentence what interaction the dashboard
supports that chat turns don't.
