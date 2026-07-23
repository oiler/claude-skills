# claude-cowork-builder — Phase 5 smoke audit

Date: 2026-07-23
Plugin under audit: `/private/tmp/claude-501/-Users-jrf1039-files-projects-001-claude-skills-creator/85f2beea-78fc-4e71-9f99-ac67d65c84f6/scratchpad/smoke-fixture`
Reference material used: only `~/.claude/skills/claude-cowork-builder/` (SKILL.md + the reference files it routes to for the Phase 5 pre-package check — `references/audit-checklist.md`, `scripts/validate_plugin.py`, and, for grounding specific checklist items, `references/skill-authoring.md`, `references/connectors-and-mcp.md`, `references/distribution.md`, all cited inline by the checklist itself). No files outside this skill were consulted.

Procedure followed: SKILL.md's routing table row "Pre-package check" points to `scripts/validate_plugin.py` then `references/audit-checklist.md`. `audit-checklist.md` §"Run the validator first" gives the exact invocation: `uv run ${CLAUDE_SKILL_DIR}/scripts/validate_plugin.py <plugin-dir>`. I substituted the real skill path for `${CLAUDE_SKILL_DIR}` (see ambiguity #1 below) and ran it, then worked the 14-item checklist by hand for everything not tagged pure `[script]`.

## Validator run

```
uv run ~/.claude/skills/claude-cowork-builder/scripts/validate_plugin.py <plugin-dir>
```

Output:

```
profile: private-individual (no marketplace.json in plugin or parent)
FAIL item  2 [manifest-at-root] plugin.json found at the plugin root — the manifest lives at .claude-plugin/plugin.json
FAIL item  2 [manifest-field-description] manifest missing required field 'description'
FAIL item  2 [manifest-name-kebab] name 'Smoke_Fixture' is not kebab-case
FAIL item  2 [manifest-version-semver] version '1.0' is not MAJOR.MINOR.PATCH
FAIL item 10 [readme] README.md missing at the plugin root
FAIL item 10 [coupling] ~~ tokens in skill bodies (~~file-storage) but profile private-individual is private — private plugins use concrete tool names
FAIL item  6 [description-token] report-maker: raw ~~ token in description frontmatter — descriptions use plain category language
FAIL item  8 [hardcoded-path] skills/report-maker/SKILL.md:7: hardcoded absolute path — use ${CLAUDE_PLUGIN_ROOT} or the working folder
FAIL item  7 [open-command] skills/report-maker/SKILL.md: `open /` in a code block — never open files for the user, tell them the path
script checks: 9 failure(s)
exit code: 1
```

## 1. Defects found

### Surfaced by the bundled validator (`scripts/validate_plugin.py`)

| # | Checklist item | Finding |
|---|---|---|
| 1 | 2 [script] | `plugin.json` exists at the plugin root (byte-identical duplicate of `.claude-plugin/plugin.json`). Manifest is only valid at `.claude-plugin/plugin.json` per the skill's own Hard Rules; the root copy is a fail. |
| 2 | 2 [script] | Manifest `description` field is empty (`""`) — required field missing in substance. |
| 3 | 2 [script] | Manifest `name` is `"Smoke_Fixture"` — not kebab-case. |
| 4 | 2 [script] | Manifest `version` is `"1.0"` — not valid `MAJOR.MINOR.PATCH` semver. |
| 5 | 10 [script] | No `README.md` at the plugin root. |
| 6 | 10 [script] | Skill body uses a `~~file-storage` placeholder while the inferred profile is private — private plugins must use concrete tool names, not genericized placeholders (genericizing is a Public-only trigger). |
| 7 | 6 [script] | The `~~file-storage` token leaks into the skill's `description` frontmatter (`"Reads ~~file-storage to make reports."`) — descriptions must use plain category language, never raw `~~` tokens. |
| 8 | 8 [script] | `skills/report-maker/SKILL.md:7` hardcodes `/Users/oiler/report.html` — an absolute, machine-specific path where `${CLAUDE_PLUGIN_ROOT}` or a resolved working-folder path is required. |
| 9 | 7 [script] | `skills/report-maker/SKILL.md` contains `open /Users/oiler/report.html` inside a fenced code block — the skill body instructs opening a file for the user, which is banned outright. |

### Surfaced by my own judgment / manual inspection (not caught by the script)

| # | Checklist item | Finding |
|---|---|---|
| 10 | 5 [judgment] | No standalone path at all. `skill-authoring.md`'s command-skill template requires `## Without connected sources` / `## With ~~category connected` sections, and the Hard Rule in SKILL.md states every command skill must work with zero connectors. `report-maker`'s entire body is a one-line `open` command hard-wired to a `~~file-storage` connector — there is no way to run this skill without that connector, and no degrade path is offered. This directly violates a Hard Rule, not just a style item. |
| 11 | 6 [judgment, four-way sync] | The `~~file-storage` token is completely orphaned. Per `connectors-and-mcp.md`, a category token needs three siblings — a `CONNECTORS.md` "Placeholder" row, a `README.md` "connectors this plugin uses" section, and a matching `.mcp.json` server entry. None of `CONNECTORS.md`, `README.md`, or `.mcp.json` exist anywhere in the plugin. The connector this skill depends on is undeclared and unconfigurable by the plugin owner. |
| 12 | 3 [judgment] | Description (`"Reads ~~file-storage to make reports."`) is not pushy: single generic sentence, no concrete trigger phrasing a user would type, no closing `Use when…` clause, and (separately from the raw-token fail above) leans on internal category jargon rather than plain language. Per the checklist this is "the most common skill defect" and this description fails on every sub-criterion at once. |
| 13 | 7 [judgment, remainder] | Beyond the flagged `open` call: the skill never writes to the user's working folder, never resolves or states an output path, and never tells the user where a file landed — the entire hygiene contract in `skill-authoring.md` § Cowork output hygiene is unaddressed. There's also no `## MANDATORY FIRST STEP` working-folder guard and no acknowledgment of the no-working-folder/session-deliverable mode, so the skill's schedulability status is undefined. |
| 14 | skill-authoring.md two-tier model | The skill fits neither shape the reference defines. Frontmatter has no `argument-hint` (needed for a command skill) and no `user-invocable: false` (needed for a knowledge skill), and the body has none of the seven mandated command-skill sections (`## Trigger`, `## Inputs`, `## Steps`, `## Without connected sources`, `## With ~~category connected`, `## Output Format`, `## After`) or the CONNECTORS.md banner line required of any skill that references a `~~category` token. This is effectively an unauthored skill stub, not a defect the checklist has a single numbered slot for — closest fit is item 4 (progressive disclosure / SKILL.md quality), but the real problem is structural: it isn't a command or knowledge skill at all as the reference defines those terms. |
| 15 | 13 [judgment] | Phase 5 packaging cannot proceed as scaffolded. `audit-checklist.md` item 13 and `distribution.md` §6 document exactly two packaging paths: (a) plugin-is-its-own-repo → copy `assets/templates/Makefile`, build via `git archive`; (b) plugin-inside-a-container-marketplace-repo → the canonical `zip` command. This fixture is neither: it is not a git repository at all (`git status` fails with "not a git repository"), it has no `Makefile`, and it has no `.claude-plugin/marketplace.json` (self- or container-). `distribution.md` states the self-marketplace layout is "the default" for a private plugin that is its own repo — none of that scaffolding is present. There is no packaging path this plugin can currently take without further scaffolding work, regardless of whether the other 14 items were fixed. |

Items I checked and found **no defect** for, given how little the plugin actually contains: item 0 (no deviations doc present, nothing to reconcile), item 9 remainder (no secrets, no remote MCP entries, no agents, no artifact-generation instructions to check), item 11 (only one skill, nothing to dedup), item 12 (not a finance/legal/health-domain skill, disclaimer not applicable), item 14 (no in-place connector writes instructed — though this is a pass mostly because the skill does almost nothing, not because it demonstrates correct state handling).

## 2. Ambiguities / gaps in the skill's own instructions

1. **`${CLAUDE_SKILL_DIR}` is never defined anywhere in the skill.** Both `audit-checklist.md:5` and `build-spine.md:118` give the validator invocation as `uv run ${CLAUDE_SKILL_DIR}/scripts/validate_plugin.py <plugin-dir>`, but no file in the skill (`SKILL.md`, any `references/*.md`) explains what sets `CLAUDE_SKILL_DIR`, when it's populated, or what to do if it's unset. In my actual shell it was unset, and I had to infer/substitute the real filesystem path (`~/.claude/skills/claude-cowork-builder`) to run the check at all. A user or agent running this outside a context that happens to export that variable has no documented fallback.

2. **The validator's inferred "private-individual" profile has no corresponding documented shape.** `distribution.md` §6 and `audit-checklist.md` item 10 describe exactly two repo layouts for a private plugin: "its own repo" (self-marketplace is stated as *the default*, requiring `marketplace.json` + the shipped Makefile) or "inside a container marketplace repo." Nowhere in the reference docs is there a third, bare "private-individual — no marketplace.json anywhere, not necessarily even a git repo" layout described as legitimate. Yet `validate_plugin.py`'s `infer_profile()` treats "no marketplace.json in plugin or parent" as sufficient to call the profile `private-individual` and pass it through cleanly — it never checks whether the directory is a git repo, never requires `marketplace.json` for this case, and item 10's script check only validates `marketplace.json` *if one already exists*, rather than requiring one for a would-be self-marketplace. Net effect: a plugin that is missing the "default" self-marketplace scaffolding entirely (as this fixture is) sails through the profile check with zero flags on that gap, and the disagreement between validator code and reference prose about what "private-individual" even means is never called out anywhere in the skill.

3. **Audit checklist item 13 doesn't address the profile the validator actually inferred.** Item 13's two packaging paths ("plugin-is-its-own-repo" / "container marketplace repo") don't mention what to do for a `private-individual`-profiled directory that is neither — which is exactly this fixture's state. I had to conclude on my own that packaging is blocked pending further scaffolding; the skill doesn't say this explicitly anywhere I found.

4. **The Phase-5 routing table entry names only two files, but full execution of the checklist depends on several more.** SKILL.md's routing row says "Pre-package check → run scripts/validate_plugin.py, then references/audit-checklist.md." In practice, checklist items 5, 6, 7, 9, 12, and 14 each cite a *different* reference file inline (`skill-authoring.md`, `connectors-and-mcp.md`, `cowork-runtime.md`, `live-artifacts.md`, `agent-playbook.md`) for the substance of what to check. All of those are within the skill, so I followed them, but the routing table itself doesn't surface this — someone following only the two named files would miss the detail behind roughly half the judgment items.

5. **No guidance on a duplicated manifest.** Two byte-identical `plugin.json` files exist (root and `.claude-plugin/`). The Hard Rules and item 2 make clear the root one is invalid, but nothing in the skill says whether the fix is "delete the root copy" (my assumption) versus some other reconciliation — a minor gap, but a real one given the file was clearly duplicated, not just misplaced.

6. **`--profile` CLI override is undocumented.** `validate_plugin.py` accepts `--profile {private-individual,self-marketplace,container-marketplace,public}` and will fail loudly if it disagrees with the inferred profile, but neither `SKILL.md` nor `audit-checklist.md` mentions when or why an operator would pass it.

## 3. Verdict

**Do not ship.** The validator alone returns exit code 1 with 9 hard failures, and the plugin fails several Hard Rules the skill treats as non-negotiable (manifest location, `${CLAUDE_PLUGIN_ROOT}`/no-hardcoded-paths, zero-connector standalone path, no `open`/`xdg-open`). Beyond the mechanical failures, the single skill in this plugin (`report-maker`) is not really an authored skill at all — it has no argument-hint or user-invocable flag, none of the mandated command-skill body sections, no CONNECTORS.md banner, and its only "instruction" is a shell command that opens a hardcoded path on one specific person's machine using a connector that is declared nowhere else in the plugin. And structurally, Phase 5 packaging (item 13) has no path forward as currently scaffolded — the directory is neither a git repo with a Makefile nor part of a container marketplace, so even after fixing every content-level failure there is no documented way to produce the `.plugin` artifact without first doing scaffolding work (git init, add Makefile or marketplace.json, or move it into a container marketplace repo) that the skill's Phase 4 is supposed to have already done. This reads as a deliberately seeded smoke-test fixture rather than a near-complete plugin — every numbered defect above is exactly the kind of thing the checklist exists to catch, and the validator did catch the mechanical majority of them correctly.
