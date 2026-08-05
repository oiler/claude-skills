# Distribution — install, visibility, packaging, versioning

Two decisions, locked in Phase 1 before component work starts (`build-spine.md`).
They determine what Phase 4 scaffolds and what Phase 5 packages.

Sources: manifest and marketplace schemas from https://code.claude.com/docs/en/plugins-reference and https://code.claude.com/docs/en/plugin-marketplaces (checked 2026-08-05); install surfaces from https://support.claude.com/en/articles/13837440 (updated 2026-05-29). Where this file states a stricter rule than the spec, it says so — those are house standards, and the validator enforces them as such.

## 1. The two decisions

| Decision | Options | Default lean | Tradeoff |
|---|---|---|---|
| **Install path** | Individual (app settings) ↔ Open marketplace | **Individual** | Marketplace adds `marketplace.json` + repo-layout obligations. |
| **Visibility** | Private/internal ↔ Public/shared | **Private** | Private → hardcode real tools/config (concrete). Public → switch on `~~category` placeholders + `CONNECTORS.md` + branding metadata (`license`/`homepage`/`repository`/`keywords`) + `CHANGELOG`. |

Confirm both decisions together, not independently — they're coupled (below), not four independent toggles.

## 2. The coupling

*Private → individual → concrete config* hangs together.
*Public → marketplace → `~~category` genericize + branding metadata + `marketplace.json` + `CHANGELOG`* hangs together.

Read "concrete" as a permission, not a prohibition: a private plugin *may* hardcode real product names, and `~~category` tokens in skill bodies stay legitimate at every profile — they're the standalone/supercharged mechanism (`skill-authoring.md`), not a public-only artifact, and the validator treats them as such. The one token rule that holds everywhere is that `~~` never appears in `description` frontmatter, where it fails at any visibility.

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

**Those four fields are a house floor, not the platform contract.** The manifest is optional entirely, and when present only `name` is required — everything else is optional. This builder emits all four because a plugin with no version and no author is unmaintainable, and the validator fails a manifest missing one; read that failure as "violates this builder's standard," not "violates the plugin spec."

Other manifest fields worth knowing, all optional: `displayName` (yes, it belongs on `plugin.json` too, not only on a marketplace entry), `$schema`, `defaultEnabled`, `userConfig` (the documented way to ask the plugin owner for a token or account id — every key under it needs a `title`, or the manifest fails validation outright; see `connectors-and-mcp.md` § Security), `channels`, `dependencies`, `workflows`, `outputStyles`, `lspServers`, `experimental.*`, and the component-path fields (`skills`, `commands`, `agents`, `hooks`, `mcpServers`) that let a component live somewhere other than its default directory. Use a component-path field only with a reason — the default layout is what every reader and every checklist assumes.

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
  "description": "One sentence: what this marketplace offers.",
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

`displayName` is what the Cowork UI shows; the entry's `description` is the
marketplace-listing copy and can match the plugin's own. A single-plugin
marketplace is fine — the repo just holds one plugin subdirectory.

**Four top-level fields, not three.** `name`, `owner`, and `plugins[]` are hard-required — omit one and `claude plugin validate` errors with or without `--strict`. Top-level `description` is a *warning* on its own, which `--strict` promotes to an error ("No marketplace description provided"), so a marketplace built without it passes a plain run and fails the strict run that §7 makes the default. Emit all four; the template does (verified against CLI 2.1.222, 2026-08-05). The gate is top-level only as far as the probe went: an entry omitting `displayName` and its own `description` passed `--strict` clean, so those two are genuinely optional. The other entry fields weren't tested — treat them as untested rather than proven safe.

**Name the marketplace carefully.** Sixteen marketplace names are reserved for Anthropic — including `knowledge-work-plugins`, `first-party-plugins`, and `anthropic-plugins` — and names that impersonate an official marketplace are blocked as well. A collision doesn't fail loudly at build time: the marketplace stops loading and is reported as registered from an untrusted source. Pick a name that is obviously yours.

**Optional entry fields**, beyond the four the template emits: `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, `strict`, `relevance`, `defaultEnabled`, plus per-entry component paths (`skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`). `category` and `homepage` are the two the corpus actually leans on. `strict` turns validation warnings into errors for that entry; `defaultEnabled` installs the plugin enabled rather than dormant.

**`source` is not only a relative string.** The `"./plugin-dir"` form is the local case. Four object forms cover remote plugins: `github` (`repo`, optional `ref`/`sha`), `url` (`url`, optional `ref`/`sha`), `git-subdir` (`url`, `path`, optional `ref`/`sha`), and `npm` (`package`, optional `version`/`registry`). Anthropic's own marketplace uses `url` and `git-subdir` heavily. Pin a `sha` when you care that the listing can't shift under you.

**`metadata.pluginRoot`** is an optional top-level field for a marketplace whose plugins don't sit one directory down — a per-plugin marketplace living beside the plugin it lists sets `"pluginRoot": "."`.

**Default for a private plugin that is its own repo — the self-marketplace.** A private plugin whose repo is *itself* a single-plugin marketplace: `.claude-plugin/marketplace.json` beside `plugin.json`, carrying `name`, `owner`, `description`, and a `plugins[]` entry that lists the plugin with `source: "./"` — the same four top-level fields a strict run demands of any marketplace, self or container. This is the default because `/plugin marketplace add <repo>` is the only stable local-install path in Claude Code, and restructuring into a container repo would move the manifest a directory above the packaging root. "marketplace.json is never a per-plugin file" holds for every *container* marketplace; the self-marketplace is the one sanctioned exception, proven over eight production releases. If the plugin later goes public, migrate into a real container marketplace.

The pattern has no name in the spec, but its mechanics are spec-sanctioned: a relative `source` *"must start with `./`"* and resolves against the marketplace root, and `"./"` is a documented marketplace-root source. Note the corollary — a per-plugin marketplace written as `"."` (no slash) is the deviant form even though Anthropic's own `brand-voice` uses it. Emit `"./"`.

**`CHANGELOG.md` — new file, plugin root.** Standard keep-a-changelog format: `## [0.1.0] - YYYY-MM-DD` sections, `Added`/`Changed`/`Fixed` subheads.

**Genericize.** Every product name a skill body references gets swapped for a `~~category` placeholder, and every product name in a `description` frontmatter field drops to plain category language (descriptions never carry `~~` tokens — see `connectors-and-mcp.md`), with `CONNECTORS.md` added at the plugin root as the translation table (category → placeholder → included servers → other options). See `connectors-and-mcp.md` for the full `~~category` system and the `CONNECTORS.md` table format — this is the same mechanism, triggered by the visibility flip.

## 5. Versioning

Semver (`MAJOR.MINOR.PATCH`). New plugins start at `0.1.0`. Bump `version` in `plugin.json` on every release; for public plugins, mirror the bump into `CHANGELOG.md`.

`version` isn't decoration — it's what update resolution keys on. Omit it and the client falls back to the git commit SHA, which means every push reads as a new version and a user can't pin anything. That is the real argument for the house floor above.

## 6. Packaging

Packaging produces a `.plugin` — a zip with `.claude-plugin/plugin.json` at the archive **root** (a wrapper directory like `my-plugin/.claude-plugin/plugin.json` fails). Anthropic documents that a custom plugin file can be uploaded but publishes no archive layout, so treat the root-manifest requirement as observed behavior rather than a documented format; it is consistent with how relative marketplace paths resolve, and it is what has worked in practice.

There are two install surfaces, differing by client, and both work offline for a private local-only plugin:

- **Claude Cowork (web/app):** upload the `.plugin` from the Plugins tab. Cowork validates the archive structure and installs it.
- **Claude Code (desktop/CLI):** `/plugin marketplace add <local-repo-path>` points at the working tree directly (§4) — no file to upload, and it picks up changes without a rebuild.

On the Cowork side, uploading the file is not the only route: a marketplace can also be added from the Plugins tab by *"Sync from GitHub repository or git URL"*. For a self-marketplace repo (§4) that is the smoothest hand-off — the recipient adds the repo URL once and gets updates by re-syncing — while the `.plugin` upload remains the right answer when the recipient can't reach the repo. Either way, plugins a user adds themselves are saved locally to that computer, so nothing follows them to a second machine (`cowork-runtime.md` § How plugins actually get installed).

**Org distribution (Team/Enterprise)** is a distribution mode this builder doesn't scaffold: an admin publishes a marketplace under Organization settings → Plugins, the backing repo must be private, and `npm` sources are not supported there. If a plugin is meant for a whole organization rather than a person, that path — not a `.plugin` hand-off — is the destination, and the plugin should be genericized as if public.

The versioned artifact name doubles as a rollback / portable hand-off key — keep a build to reinstall a known-good commit or share the plugin out-of-band.

Three default paths, by repo layout:

**Plugin-is-its-own-repo (default): the shipped Makefile.** Copy `assets/templates/Makefile` to the repo root at scaffold time. `make plugin` builds `dist/<name>-<version>-<sha>.plugin` from git-tracked content via `git archive`; `make verify` asserts the bundle carries the manifest and at least one skill layer — `skills/<name>/SKILL.md`, `commands/<name>.md`, or a root `SKILL.md`, all three of which the spec treats as valid — and that the denylist leaked nothing. Reproducible, cannot leak untracked files (a `zip -r` of the working tree honors nothing in `.gitignore`), and immune to the stale-zip-update hazard by construction — a fresh archive every build. The versioned artifact name is the rollback key. Use `.gitattributes` `export-ignore` to drop docs/evals/tests from the bundle.

**Plugin inside a container marketplace repo: the canonical zip command** — zip to `/tmp` first, then copy to the outputs directory (observed: writing directly into an outputs mount hits permission errors):

```bash
cd <plugin-dir> && zip -r /tmp/<name>.plugin . -x "*.DS_Store" && cp /tmp/<name>.plugin <outputs>/<name>.plugin
```

**Plugin directory that is neither its own repo nor inside a marketplace repo: the same canonical zip command.** A plugin folder living inside some unrelated project, or sitting in a working folder with no git around it at all, is the third real case — it comes up whenever an existing plugin gets handed over as a directory rather than a clone. It has no repo for `git archive` to read, so the Makefile path doesn't apply; run the zip command above verbatim from the plugin directory. Don't reach for it by fitting the layout to the container-marketplace branch — name the case and pick this one.

That path gives up what makes the Makefile the default: `zip -r` packages the working tree exactly as it stands, so untracked scratch files, editor backups, `.venv/`, and anything a `.gitignore` would have caught all ship. Sweep the directory before zipping, and prefer moving the plugin into its own repo if it's going to be packaged more than once.

The `.plugin` filename is the plugin's `name` field from `plugin.json` (kebab-case) — `<name>.plugin`, not the directory name if they've diverged.

Delete any stale `/tmp/<name>.plugin` from a previous run before zipping — `zip` updates an existing archive in place rather than replacing it, so a stale file can carry deleted entries into the "new" package.

## 7. Validation

If the `claude` CLI is available, run it against the **plugin directory**:

```bash
claude plugin validate ./my-plugin --strict
```

`--strict` promotes warnings to errors — that is what turns the missing marketplace `description` (§4) from advice into a failure. Run it strict by default and relax only when a warning is a recorded deviation.

**Know which manifest the directory form picked.** Given a directory, the CLI resolves one manifest and says which in its first line of output. A marketplace manifest wins when one is present, so on a self-marketplace layout (§4) `claude plugin validate ./my-plugin --strict` reads `Validating marketplace manifest` and reports plugin-side problems only as they surface through the `plugins[]` entry, prefixed `plugins[0] plugin.json → …`. A clean pass there is a statement about the marketplace file. To get a verdict addressed to the plugin manifest itself, point at it:

```bash
claude plugin validate ./my-plugin/.claude-plugin/plugin.json --strict
```

On a self-marketplace, run both — they answer different questions.

If the CLI isn't available, walk the manual structural checklist instead:

- `.claude-plugin/plugin.json` exists at exactly that path — a `plugin.json` sitting at the plugin root is a fail, not a variant.
- It parses as valid JSON; `name` is kebab-case.
- Every component directory referenced by `plugin.json` (skills, agents, MCP config) actually exists in the plugin tree, at the plugin root (not inside `.claude-plugin/`).
- Every skill directory contains a file named exactly `SKILL.md` — not `skill.md`, not `<name>-SKILL.md`.

Run this before packaging, not after — a bad zip is just a bad plugin directory with an archive extension.
