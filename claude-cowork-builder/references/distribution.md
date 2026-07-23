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

What a private, individually-installed plugin ships. The manifest lives at
`.claude-plugin/plugin.json` — inside a `.claude-plugin/` directory at the
plugin root, never at the root itself. Only the manifest goes in
`.claude-plugin/`; component directories (`skills/`, `agents/`) and the
root-level files (`.mcp.json`, `CONNECTORS.md`, `README.md`) stay at the
plugin root:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      ← manifest, always exactly here
├── skills/
├── .mcp.json
└── README.md
```

Minimal `plugin.json`:

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

This bare shape is the validator's `private-individual` profile — the minimal private layout, legitimate for a plugin installed directly through app settings (individual install), which needs no `marketplace.json` at all. The self-marketplace below (§4) is the default only when the plugin is distributed as *its own git repo* for `/plugin marketplace add` local install — the two are different install mechanisms, both valid for a private plugin, and the validator names whichever the repo shape implies.

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

**`marketplace.json` — lives in the marketplace repo, not the plugin.** A
marketplace is a container repository holding one or more plugins as
subdirectories; its manifest sits at the *repo's* `.claude-plugin/marketplace.json`
and lists each plugin by relative `source`. It is never a per-plugin file —
"going marketplace" means the plugin moves into (or becomes) such a repo:

```
my-marketplace/                      ← the marketplace repo
├── .claude-plugin/
│   └── marketplace.json             ← one manifest for the whole marketplace
├── my-plugin/                       ← a plugin, with its own .claude-plugin/plugin.json
└── another-plugin/
```

```json
{
  "name": "my-marketplace",
  "owner": { "name": "oiler" },
  "plugins": [
    {
      "name": "my-plugin",
      "displayName": "My Plugin",
      "source": "./my-plugin",
      "description": "One sentence: what this plugin does."
    }
  ]
}
```

`displayName` is what the Cowork UI shows; `description` here is the
marketplace-listing copy and can match the plugin's own. A single-plugin
marketplace is fine — the repo just holds one plugin subdirectory.

**Default for a private plugin that is its own repo — the self-marketplace.** A private plugin whose repo is *itself* a single-plugin marketplace: `.claude-plugin/marketplace.json` beside `plugin.json`, listing the plugin with `source: "./"`. This is the default because `/plugin marketplace add <repo>` is the only stable local-install path in Claude Code, and restructuring into a container repo would move the manifest a directory above the packaging root. "marketplace.json is never a per-plugin file" holds for every *container* marketplace; the self-marketplace is the one sanctioned exception, proven over eight production releases. If the plugin later goes public, migrate into a real container marketplace.

**`CHANGELOG.md` — new file, plugin root.** Standard keep-a-changelog format: `## [0.1.0] - YYYY-MM-DD` sections, `Added`/`Changed`/`Fixed` subheads.

**Genericize.** Every product name a skill body references gets swapped for a `~~category` placeholder, and every product name in a `description` frontmatter field drops to plain category language (descriptions never carry `~~` tokens — see `connectors-and-mcp.md`), with `CONNECTORS.md` added at the plugin root as the translation table (category → placeholder → included servers → other options). See `connectors-and-mcp.md` for the full `~~category` system and the `CONNECTORS.md` table format — this is the same mechanism, triggered by the visibility flip.

## 5. Versioning

Semver (`MAJOR.MINOR.PATCH`). New plugins start at `0.1.0`. Bump `version` in `plugin.json` on every release; for public plugins, mirror the bump into `CHANGELOG.md`.

## 6. Packaging

Two default paths, by repo layout:

**Plugin-is-its-own-repo (default): the shipped Makefile.** Copy `assets/templates/Makefile` to the repo root at scaffold time. `make plugin` builds `dist/<name>-<version>-<sha>.plugin` from git-tracked content via `git archive`; `make verify` asserts the bundle carries the manifest and at least one skill and that the denylist leaked nothing. Reproducible, cannot leak untracked files (a `zip -r` of the working tree honors nothing in `.gitignore`), and immune to the stale-zip-update hazard by construction — a fresh archive every build. The versioned artifact name is the rollback key. Use `.gitattributes` `export-ignore` to drop docs/evals/tests from the bundle.

**Plugin inside a container marketplace repo: the canonical zip command** — zip to `/tmp` first, then copy to the outputs directory (avoids permission issues writing directly into an outputs mount):

```bash
cd <plugin-dir> && zip -r /tmp/<name>.plugin . -x "*.DS_Store" && cp /tmp/<name>.plugin <outputs>/<name>.plugin
```

The `.plugin` filename is the plugin's `name` field from `plugin.json` (kebab-case) — `<name>.plugin`, not the directory name if they've diverged.

Delete any stale `/tmp/<name>.plugin` from a previous run before zipping — `zip` updates an existing archive in place rather than replacing it, so a stale file can carry deleted entries into the "new" package.

## 7. Validation

If the `claude` CLI is available, run it against the packaged artifact:

```bash
claude plugin validate <plugin-dir>/.claude-plugin/plugin.json
```

If it isn't available, walk the manual structural checklist instead:

- `.claude-plugin/plugin.json` exists at exactly that path — a `plugin.json` sitting at the plugin root is a fail, not a variant.
- It parses as valid JSON; `name` is kebab-case.
- Every component directory referenced by `plugin.json` (skills, agents, MCP config) actually exists in the plugin tree, at the plugin root (not inside `.claude-plugin/`).
- Every skill directory contains a file named exactly `SKILL.md` — not `skill.md`, not `<name>-SKILL.md`.

Run this before packaging, not after — a bad zip is just a bad plugin directory with an archive extension.
