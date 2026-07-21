# Distribution — install, visibility, packaging, versioning

Two decisions, locked in Phase 1 before component work starts (`build-spine.md`).
They determine what Phase 4 scaffolds and what Phase 5 packages.

## 1. The two decisions

| Decision | Options | Default lean | Tradeoff |
|---|---|---|---|
| **Install path** | Individual (app settings) ↔ Open marketplace | **Individual** | Marketplace adds `marketplace.json` + repo-layout obligations. |
| **Visibility** | Private/internal ↔ Public/shared | **Private** | Private → hardcode real tools/config (concrete). Public → switch on `~~category` placeholders + `CONNECTORS.md` + branding metadata (`license`/`homepage`/`repository`/`keywords`) + `CHANGELOG`. |

Confirm both decisions together, not independently — they're coupled (below), not four independent toggles.

## 2. The coupling

*Private → individual → concrete config* hangs together.
*Public → marketplace → `~~category` genericize + branding metadata + `marketplace.json` + `CHANGELOG`* hangs together.

**"Going public" is the trigger to genericize.** A plugin doesn't drift into public with product names still hardcoded — the moment visibility flips to Public, every concrete tool name in skill bodies gets swapped for a `~~category` placeholder (see `connectors-and-mcp.md`), and the artifact set below expands to match. Don't scaffold public artifacts for a plugin that's staying private, and don't ship a public plugin with concrete product names still in the skill bodies.

## 3. Private artifacts

What a private, individually-installed plugin ships. Minimal `plugin.json`:

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "One sentence: what this plugin does.",
  "author": {
    "name": "oiler"
  }
}
```

Concrete tool names and config are allowed and expected — skill bodies can say "Google Drive," `.mcp.json` can point at a real endpoint, `CONNECTORS.md` can be skipped entirely if there's nothing to translate. No `marketplace.json`, no `CHANGELOG.md` requirement.

## 4. Public artifacts

Everything in §3, plus:

**`plugin.json` gains:**
```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "One sentence: what this plugin does.",
  "author": {
    "name": "oiler"
  },
  "license": "MIT",
  "homepage": "https://github.com/oiler/my-plugin",
  "repository": "https://github.com/oiler/my-plugin",
  "keywords": ["cowork", "plugin"]
}
```

**`marketplace.json` — new file, plugin root:**
```json
{
  "owner": "oiler",
  "metadata": {
    "pluginRoot": "."
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./my-plugin"
    }
  ]
}
```

**`CHANGELOG.md` — new file, plugin root.** Standard keep-a-changelog format: `## [0.1.0] - YYYY-MM-DD` sections, `Added`/`Changed`/`Fixed` subheads.

**Genericize.** Every product name a skill body references gets swapped for a `~~category` placeholder, with `CONNECTORS.md` added at the plugin root as the translation table (category → placeholder → included servers → other options). See `connectors-and-mcp.md` for the full `~~category` system and the `CONNECTORS.md` table format — this is the same mechanism, triggered by the visibility flip.

## 5. Versioning

Semver (`MAJOR.MINOR.PATCH`). New plugins start at `0.1.0`. Bump `version` in `plugin.json` on every release; for public plugins, mirror the bump into `CHANGELOG.md`.

## 6. Packaging

Canonical zip command — zip to `/tmp` first, then copy to the outputs directory (avoids permission issues writing directly into an outputs mount):

```bash
cd <plugin-dir> && zip -r /tmp/<name>.plugin . -x "*.DS_Store" && cp /tmp/<name>.plugin <outputs>/<name>.plugin
```

The `.plugin` filename is the plugin's `name` field from `plugin.json` (kebab-case) — `<name>.plugin`, not the directory name if they've diverged.

## 7. Validation

If the `claude` CLI is available, run it against the packaged artifact:

```bash
claude plugin validate <path-to-plugin.json>
```

If it isn't available, walk the manual structural checklist instead:

- `plugin.json` is valid JSON; `name` is kebab-case.
- Every component directory referenced by `plugin.json` (skills, agents, MCP config) actually exists in the plugin tree.
- Every skill directory contains a file named exactly `SKILL.md` — not `skill.md`, not `<name>-SKILL.md`.

Run this before packaging, not after — a bad zip is just a bad plugin directory with an archive extension.
