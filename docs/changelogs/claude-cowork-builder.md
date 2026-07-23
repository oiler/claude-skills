# claude-cowork-builder — Changelog

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
