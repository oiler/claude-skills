# Audit checklist — Phase 5

Run before every package (Phase 5). Every item is pass/fail; fix before zipping.

1. **SKILL.md filename exact.** Every skill directory in the plugin contains a file named exactly `SKILL.md` — not `skill.md`, not `<name>-SKILL.md`. Wrong filename fails silently, no error surfaces. Check: `find skills -mindepth 2 -maxdepth 2 -iname 'skill.md'` and confirm every result is spelled `SKILL.md` exactly, and that every skill subdirectory has one.

2. **`plugin.json` valid.** `name` is kebab-case, `version` is valid semver (`MAJOR.MINOR.PATCH`), `description` is present and non-empty. If the `claude` CLI is available, run `claude plugin validate <path-to-plugin.json>` and require a clean pass. If it isn't available, do the manual structural check instead: `plugin.json` parses as valid JSON; every component directory it references (skills, agents, MCP config) actually exists in the tree; every skill directory has a `SKILL.md`. See `distribution.md` §7.

3. **Descriptions are pushy.** Every skill's `description` field is third person (describes the skill, doesn't instruct it), is trigger-phrase-rich (packs in concrete phrasing a user would actually type), and closes with a `Use when…` clause. A thin or generic description is a fail — undertriggering is the most common skill defect. See `skill-authoring.md`.

4. **Progressive disclosure held.** Each `SKILL.md` stays lean — routing/summary content only — with real detail pushed into `references/`. A `SKILL.md` that reads like a full manual instead of a router is a fail.

5. **Standalone + supercharged confirmed.** Every command skill has a working zero-connector path: the `## Without connected sources` section covers the zero-connector path explicitly, and that path never hard-fails just because a connector isn't wired. The "with `~~category` connected" path is additive, never a substitute. See `skill-authoring.md` § Standalone + Supercharged.

6. **`~~category` sync verified.** Every `~~category` placeholder used in a skill body appears, spelled and cased identically, in all of: the skill body itself, `CONNECTORS.md`'s `Placeholder` column (4-column table: Category / Placeholder / Included servers / Other options), the "connectors this plugin uses" section of `README.md`, and a matching server entry in `.mcp.json`. Grep each token across all four locations and confirm no orphans in either direction. Every empty-`url: ""` stub in `.mcp.json` is marked with `*` next to its row in `CONNECTORS.md` or `README.md`, with the footnote `` `*` — Placeholder — MCP URL not yet configured `` defined once. See `connectors-and-mcp.md`.

7. **Cowork output hygiene held.** For every skill that writes files: output goes to the user's working folder, never the plugin's own install directory or an arbitrary temp path; no relative paths — only a real, resolved path rooted in the working folder; no `open` or `xdg-open` call, and no language implying the file opened itself; the skill's last move on that path is telling the user exactly where the file landed. See `skill-authoring.md` § Cowork output hygiene and `live-artifacts.md` § Ship + wire for the Live Artifact case.

8. **`${CLAUDE_PLUGIN_ROOT}` used everywhere.** Every intra-plugin path reference — copying `dashboard.html`, pointing at a template, referencing another skill's file — uses `${CLAUDE_PLUGIN_ROOT}`. Grep the plugin tree for hardcoded absolute paths (`/Users/`, `/home/`, `/tmp/`, etc.) or bare relative paths standing in for a plugin-root reference; any hit is a fail.

9. **Security checks pass.** No literal secret, API key, or bearer token appears anywhere in `.mcp.json` or skill bodies — every credential is a `${VAR}` environment-variable substitution, and each referenced `${VAR}` is documented in `README.md` (what it is, where to get it). Every remote `.mcp.json` entry (`http` or `sse` type) uses `https://` — no plaintext remotes. Every agent's `tools:` field is either a pinned least-privilege list or deliberately omitted with the mandatory `# tools not restricted — …` comment explaining why; never present-but-empty, never silently omitted. See `connectors-and-mcp.md` § Security and `agent-playbook.md` §4.

10. **Distribution artifacts match the declared path.** Private/individual: minimal `plugin.json` (`name`, `version`, `description`, `author`) — no `marketplace.json`, no `CHANGELOG.md` required, concrete product names allowed. Public/marketplace: `plugin.json` also carries `license`, `homepage`, `repository`, `keywords`; a `marketplace.json` exists at the plugin root; a `CHANGELOG.md` exists at the plugin root in keep-a-changelog format; every skill body is genericized to `~~category` placeholders with `CONNECTORS.md` present. A plugin shipping public artifacts while still visibility-private (or vice versa) is a fail. See `distribution.md` §3–4.

11. **Dedup lint clean.** No two skills in the plugin cover overlapping trigger territory, and no stray experimental/scratch skill directory survived into the packaged tree (e.g. a `-v2`, `-draft`, `-old`, or `-copy` suffixed skill left over from iteration). Every shipped skill has a distinct, non-overlapping `description` scope from every other shipped skill.

12. **Sensitive-domain disclaimer present where applicable.** If any skill's function touches finance, legal, or health/medical topics, that skill's body carries an explicit disclaimer to the Cowork end user (not investment/legal/medical advice, consult a professional, etc.) in its user-facing output — not buried only in authoring material. Skills outside these domains are exempt; don't add a disclaimer where the subject matter doesn't call for one.

13. **Package with the canonical zip command.** Build the `.plugin` artifact with, verbatim:

   ```bash
   cd <plugin-dir> && zip -r /tmp/<name>.plugin . -x "*.DS_Store" && cp /tmp/<name>.plugin <outputs>/<name>.plugin
   ```

   `<name>` is `plugin.json`'s `name` field (kebab-case), not the directory name if they've diverged. Zip to `/tmp` first, then copy to the outputs directory — never zip directly into an outputs mount. See `distribution.md` §6.
