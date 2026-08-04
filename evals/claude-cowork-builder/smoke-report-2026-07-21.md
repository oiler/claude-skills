# drive-helper smoke report — claude-cowork-builder fidelity test

Date: 2026-07-21
Skill under test: /Users/jrf1039/files/repo/claude-skills/claude-cowork-builder/ (read-only)
Build path: menu entry 1 (New plugin from scratch), full Phase 0→5 spine, Google Drive recipe.

## (a) Scaffolded plugin tree

`find . -type f | sort` from the plugin root (/private/tmp/claude-501/-Users-jrf1039-files-projects-001-claude-skills-creator/f7ff07c6-197f-404f-a1ea-9111312e8edb/scratchpad/cowork-smoke/drive-helper/):

```
./.claude-plugin/plugin.json
./.mcp.json
./CONNECTORS.md
./README.md
./skills/find-in-drive/SKILL.md
./skills/read-drive-file/SKILL.md
```

## (b) Audit checklist results (references/audit-checklist.md)

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | SKILL.md filename exact | PASS | `find skills -mindepth 2 -maxdepth 2 -iname 'skill.md'` returned exactly `skills/find-in-drive/SKILL.md` and `skills/read-drive-file/SKILL.md`, both spelled `SKILL.md`; every skill subdirectory has one. |
| 2 | plugin.json valid, at the right path | PASS | `claude plugin validate <plugin-dir>/.claude-plugin/plugin.json` → "✔ Validation passed", exit 0. Manifest is at exactly `.claude-plugin/plugin.json`; `name` = `drive-helper` (kebab-case); `version` = `0.1.0` (semver); `description` non-empty. |
| 3 | Descriptions are pushy | PASS | Both skills ship the recipe's descriptions: third person, trigger-phrase-rich ("find that file in Drive", "search my Google Drive for…", "that doc", "the spreadsheet"), each closing with a `Use when…` clause. |
| 4 | Progressive disclosure held | PASS | Both SKILL.md files are lean (~55 lines each): section-templated process/rules, no manual-length content. No `references/` needed at this size. |
| 5 | Standalone + supercharged confirmed | PASS | The one command skill (`find-in-drive`) has `## Without connected sources` (upload/paste fallback, never hard-fails) and `## With ~~file storage connected` as an additive path. The knowledge skill also carries both paths in its Rules. |
| 6 | `~~category` sync verified | PASS | `~~file storage` spelled/cased identically in: both skill bodies, CONNECTORS.md `Placeholder` column (4-column table), README.md "Connectors this plugin uses" section, and `.mcp.json` has the matching `google-drive` server (mapped via the table's "Included servers" cell). No `~~` token in any `description` frontmatter (grep: none). Empty-`url:""` stub marked `*` in CONNECTORS.md and README.md with the footnote `` `*` — Placeholder — MCP URL not yet configured `` defined. |
| 7 | Cowork output hygiene held | PASS | `find-in-drive` `## Output Format`: file output only on request, goes to the user's working folder, exact path told to the user, explicit "never use a relative path" and no `open`/`xdg-open`. `read-drive-file` writes no files. |
| 8 | `${CLAUDE_PLUGIN_ROOT}` used everywhere | PASS | No intra-plugin path references requiring it exist (no Live Artifact copy steps, no template pointers). Grep for `/Users/`, `/home/`, `/tmp/` in the tree: no hits. The only relative path is the CONNECTORS banner `../../CONNECTORS.md`, which skill-authoring.md mandates verbatim (see ambiguity 2). |
| 9 | Security checks pass | PASS | No literal secrets/keys/tokens anywhere (grep clean). No `${VAR}` references, so nothing to document in README. No `http://` remotes; the only server entry is the recipe's sanctioned empty-url stub. No agents, so no `tools:` field to check. |
| 10 | Distribution artifacts match declared path | PASS | Private/individual as declared: minimal `plugin.json` (name/version/description/author only), no `marketplace.json`, no `CHANGELOG.md`, no marketplace repo. Concrete product names ("Google Drive") present in descriptions/README, allowed for private (distribution.md §3). |
| 11 | Dedup lint clean | PASS | Two skills with distinct, non-overlapping scopes (locate vs. read/interpret; find-in-drive explicitly delegates reading to read-drive-file). No `-v2`/`-draft`/`-old`/`-copy` stray directories. |
| 12 | Sensitive-domain disclaimer | PASS (exempt) | No finance, legal, or health function anywhere in the plugin; per the item, no disclaimer added where the domain doesn't call for one. |
| 13 | Package with the canonical zip command | PASS | Ran the canonical command verbatim (see (c)). `<name>` taken from plugin.json's `name` field (`drive-helper`). |

Result: 13/13 pass. No fixes required before packaging.

## (c) Packaging command and result

Command (canonical form from audit-checklist.md item 13 / distribution.md §6, with `<plugin-dir>`, `<name>`, `<outputs>` substituted):

```bash
cd /private/tmp/claude-501/-Users-jrf1039-files-projects-001-claude-skills-creator/f7ff07c6-197f-404f-a1ea-9111312e8edb/scratchpad/cowork-smoke/drive-helper && zip -r /tmp/drive-helper.plugin . -x "*.DS_Store" && cp /tmp/drive-helper.plugin /private/tmp/claude-501/-Users-jrf1039-files-projects-001-claude-skills-creator/f7ff07c6-197f-404f-a1ea-9111312e8edb/scratchpad/cowork-smoke/drive-helper.plugin
```

Result: success. `unzip -l` on the copied artifact lists exactly the 6 scaffolded files (plus directory entries), 7,763 bytes total. Note: a stale `/tmp/drive-helper.plugin` existed from a prior run, so `zip` reported "updating:" rather than "adding:"; the archive listing was verified to contain only the current tree — no stale entries. The canonical command does not delete a pre-existing `/tmp/<name>.plugin` first, which could in principle retain stale entries; verifying the listing closed that gap.

## (d) Ambiguities, contradictions, and forced guesses

1. **Recipe is written for menu entry 2, used from entry 1.** `integrations/google-drive/recipe.md` says "Use this from menu entry 2 (Add an integration)" and phrases its steps as merges into an *existing* plugin ("copy the entry into the target plugin's `.mcp.json`", "under the existing table"). For a from-scratch build there is nothing to merge into. Resolution: build-spine Phase 4 step 4 scaffolds `CONNECTORS.md` + `.mcp.json` from `assets/templates/`, and the CONNECTORS.md template already contains the exact Google Drive file-storage row, so the two sources converge — but the docs never state that entry 1 + Drive means "template already equals recipe output." Mild overlap/redundancy, resolved without guessing beyond that.
2. **Hard rule vs. mandated banner.** SKILL.md hard rules say every intra-plugin path reference uses `${CLAUDE_PLUGIN_ROOT}`, "never a hardcoded or relative path." But skill-authoring.md mandates the CONNECTORS banner verbatim with a relative markdown link (`../../CONNECTORS.md`), and both shipped starter skills contain it. Resolution: followed the more specific, verbatim-mandated banner; treated audit item 8 as targeting hardcoded absolute paths and bare relative paths "standing in for a plugin-root reference," which the banner is not. Still a doc-level contradiction worth tightening.
3. **`*` footnote — "or" vs. "defined once".** connectors-and-mcp.md says the stub marker lives "in `CONNECTORS.md` or `README.md`"; audit item 6 says the footnote is "defined once." The recipe's connectors-row.md puts it in CONNECTORS.md, and the README template's MCP section references the same category. I placed the `*` + footnote in both files (a `*` in README with no footnote there would dangle). Guess: "defined once" means once per file where a `*` appears, not once per plugin. Docs don't settle it.
4. **Private lean vs. `~~category` tokens.** distribution.md §3 says a private plugin may hardcode concrete names and "CONNECTORS.md can be skipped entirely." The Drive recipe nonetheless ships skills written to `~~file storage` with a CONNECTORS.md row, even at the private default lean. Not a contradiction the build had to resolve (the recipe says "no renaming is needed"), but the private-plugin allowance and the recipe's category-first skills pull in opposite directions; I followed the recipe as shipped.
5. **README template gaps.** `assets/templates/README.md` has placeholders but no fill guidance: the "Settings" section ("Optional `.claude/settings.local.json`…") for a plugin with no settings (kept it, added "None required"), and no defined "connectors this plugin uses" heading text even though audit item 6 and connectors-and-mcp.md's four-places-in-sync table require such a section in README by that description. I used the template's "## MCP Integrations" heading with a "Connectors this plugin uses:" lead-in to satisfy both. Also, the template's install line mentions a marketplace option, which I trimmed for a private/individual plugin — the docs don't say whether to.
6. **Audit item 2's manual-check clause is partly vacuous.** "Every component directory referenced by `plugin.json` … exists" — the minimal private manifest has no fields referencing components at all, so nothing to check. Moot here since the CLI was available and passed, but the manual path as written can't fail on a minimal manifest.
7. **Canonical zip uses `/tmp` staging.** The command hardcodes `/tmp/<name>.plugin` as the staging path. Followed verbatim per the fidelity rules; note the stale-archive "updating" behavior described in (c).

## Phase outputs (for completeness)

- Phase 0 charter: drive-helper helps oiler find and read files in Google Drive from Cowork; audience = single private nontechnical-tolerant user (oiler); external tool = Google Drive.
- Phase 1: Individual install + Private visibility (locked together; concrete config path).
- Phase 2 component table: command skill find-in-drive (Yes — primary layer), knowledge skill read-drive-file (Yes — format handling, hidden from slash menu), router (No — declined, count < 8), agent (No — declined, playbook gate fails), MCP connector (Yes — `~~file storage`, empty-url Google Drive stub), Live Artifact (No — declined, no persistent UI).
- Phase 3: recipe starter skills used as shipped, no category renaming; endpoint decision = URL not known → stub + `*` footnote.
- Phase 4: tree above.
- Phase 5: audit 13/13 pass; packaged.
