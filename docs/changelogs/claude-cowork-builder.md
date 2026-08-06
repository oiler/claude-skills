# claude-cowork-builder — Changelog

## v0.4.0 — 2026-08-05

Full upgrade pass through the executable release gate (structural change class). Spec/plan: workshop `docs/superpowers/{specs,plans}/2026-08-05-cowork-builder-v0.4.0-upgrade*`.

- **Source re-sweep, all 25 tracked files.** Every format-bearing fact verified against the refreshed knowledge-work-plugins mirror (`2099f2c`), the live plugins-reference/plugin-marketplaces docs, and the Cowork support collection; 54 DRIFT rows corrected (survey: workshop workspace). Newly cited authorities: `code.claude.com/docs/en/plugins-reference`, `/plugin-marketplaces`, support article 13837440. Runtime facts updated (cloud-by-default wording, computer-use matrix rows); Live Artifacts consent sentence completed ("can only use the connectors you approved during creation or update").
- **Validator upgraded (45 → 64 tests), fixing three empirically-reproduced defects:** the `~~` token regex was blind to acronyms and multi-word categories (`~~CRM` matched nothing — audit item 6's determinism guarantee silently no-opped); the coupling rule made the default scaffold fail the default profile (bundled Drive recipe failed the bundled validator) — removed: `~~` tokens in skill bodies now pass every profile (the standalone+supercharged mechanism), while `~~` in description frontmatter fails everywhere; only `skills/*/SKILL.md` was accepted — all three spec layouts now validate (`skills/`, `commands/`, root `SKILL.md` exactly). Also new: manifest component-path resolution, house-vs-spec manifest-field split, self-marketplace top-level `description` enforcement.
- **Gate blocker fixed: test suite relocated** to `tests/` with a `pyproject.toml` (pytest+pyyaml, `pythonpath`), so the gate's `uv run --with pytest pytest -q` invocation resolves dependencies (pytest never reads PEP-723). Lock committed per the guardian model.
- **Behavior evals vs v0.3.2** (bundle: `evals/claude-cowork-builder/behavior_2026-08-05/`): six opus runs, all assertions passing both configs; transcript-level differences favored the candidate (validator caught 4/4 vs 3/4 planted script defects; no coupling workaround needed; `userConfig` keychain install flow vs hand-edit-JSON instructions). Committed fixtures: `fixtures/base-plugin`, `fixtures/imperfect-plugin` + defects manifest.
- **Live-probed corrections from the eval runs** (CLI 2.1.222): marketplace template gains the strict-required top-level `description`; `userConfig.<KEY>.title` documented as a hard schema requirement; audit item 2 clarifies `--strict` scope on self-marketplace layouts; multi-category `## With ~~category connected` pattern sanctioned; packaging path added for a plugin directory that is neither its own repo nor inside a container marketplace; false "`--strict` flags `color`" claim removed (validation reads manifests, not component frontmatter).
- **Trigger scope tightened to explicit-only (owner direction).** The description now auto-triggers only on requests that explicitly name Cowork plugin work, with a word-gate NOT-for (any Cowork request that never says "plugin" suggests the skill by name instead). Eval set expanded 8 → 22 queries (10 pos / 12 neg, four `boundary: wordpress-plugins` rows); three description rounds measured in the sibling arena. Gate artifact (`trigger_eval_results_2026-08-05.json`, 5 runs/query, opus, 600s timeout, zero error runs): positives 10/10 at 1.00, negatives 12/12 at 0.00 including all boundary rows. No waivers. Watch item: the "review this cowork plugin folder" phrasing showed 0.33–0.80 variance in 3-run development measurements before settling at 1.00 in the gate run.
- **Google Drive endpoint research concluded: the empty-`url: ""` stub is correct, not pending.** The native Drive connector has no MCP URL to fill (Anthropic's own plugins ship the same stub; verified against the corpus and support articles); the recipe's known-URL branch now names its real referent, a self-run Google MCP server. Recipe step-4 fork reworded accordingly.
- **Clean-room smoke: pass** (`smoke-report-2026-08-05.md`, bound to the release hash). Every phase completed from a cold read; validator, Makefile, and both `--strict` forms clean on first attempt. **Deferred documentation findings** (each cost a decision, none cost a step; deferred rather than re-running all evidence): D1 CONNECTORS-banner placement contradiction between `skill-authoring.md` and the command template; D2 Phase 4 scaffold order omits `marketplace.json` on the default layout; D4 audit item 4 cannot express the paired-knowledge-skill idiom the skill itself recommends. (`${CLAUDE_SKILL_DIR}` ambiguity re-noted; standing accept/no-fix adjudication from v0.3.2.)
- Frontmatter gains `metadata.version`. Backlog carried: native-connector "declare nothing" scaffolding path; eval-prompt domains from the operator's own work areas.

## v0.3.2 — 2026-07-23

- Corrected the install framing again (v0.3.1 over-corrected). A `.plugin` **is** a valid install artifact for Claude Cowork: you upload it, and Cowork validates its structure (`.claude-plugin/plugin.json` at the archive root — a wrapper directory fails). The two install surfaces are now named accurately in the Makefile template header and `distribution.md` §6: **Cowork** installs by uploading the `.plugin`; **Claude Code desktop/CLI** installs by `/plugin marketplace add <local-repo-path>`. The rollback / portable-hand-off role stays, but no longer at the expense of denying the upload path.

## v0.3.1 — 2026-07-23

- Corrected stale install framing: the Makefile template header and `distribution.md` §6 said the `.plugin` bundle was "the shape Cowork installs when you upload a plugin package." It isn't — the stable local-install path is `/plugin marketplace add <repo>` from the self-marketplace repo (§4). The `.plugin` is a reproducible `git archive` snapshot for rollback and portable hand-off, not an upload-to-install artifact. Both docs now say so.

## v0.3.0 — 2026-07-23

Determinism pass (workshop determinism ladder, first application):

- `scripts/validate_plugin.py` — deterministic validator for the audit checklist's mechanical items (manifest, profile/distribution coherence, skill filenames + frontmatter, `~~`-in-description, hardcoded paths, open/xdg-open in code blocks, `.mcp.json` parse). Profile inference: private-individual / self-marketplace / container-marketplace / public. `--json`, exit 0/1/2. Tier 3 on the ladder; tests via `uv run --with pytest --with pyyaml`.
- `assets/templates/Makefile` — git-archive packaging template (from sitecheck production), emitted at scaffold for plugin-is-own-repo layouts. Tier 1: the script owns the artifact write.
- Audit checklist partitioned: every item tagged `[script]` / `[script-assisted]` / `[judgment]`; Phase 5 is validator-first.
- Promotions from deviation to default (eight sitecheck releases of evidence): self-marketplace layout for private plugin-is-own-repo (`distribution.md` §4, item 10) and git-archive packaging (`distribution.md` §6, item 13). `Exception:` clauses removed.
- Gate: validator runs clean (exit 0) against sitecheck-claude v0.8.0, read-only.

## v0.2.0 — 2026-07-23

Lessons from the first production plugin built with this skill (sitecheck, v0.5.0–v0.8.0):

- Artifacts are Claude-authored — verbatim HTML publishing removed as a viable design; sanitized-payload boundary, link contract, update-in-place, truthful refresh disclosure (`live-artifacts.md`).
- Native-connector capability model: create-and-read-only surfaces, the append-only design rule (`connectors-and-mcp.md`); Drive production facts — Shared Drive limitation, sync trap (Drive recipe).
- State-home doctrine (`skill-authoring.md` § Where mutable state lives) + Phase 2 state question and Phase 3 Cowork gates (`build-spine.md`).
- Standalone fallback never silently replaces a configured connector; onboarding first-run pattern (`skill-authoring.md`).
- Probe the real path — capability checks run the plugin's actual code path (`cowork-runtime.md`).
- Audit: deviations doc honored (item 0), connector-safe state (item 14), truthful artifact disclosure (item 9); self-marketplace and git-archive packaging sanctioned as recognized alternatives (items 10/13, `distribution.md`).

## v0.1.0 — 2026-07-21
### Added
- Initial claude-cowork-builder: build menu, 6-phase spine, skill-authoring / connectors / agent-playbook / distribution / live-artifacts / audit references, plugin/skill/agent templates, and the Google Drive integration recipe.
