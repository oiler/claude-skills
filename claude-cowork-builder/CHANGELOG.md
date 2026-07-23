# Changelog

## 0.2.0 — 2026-07-23

Lessons from the first production plugin built with this skill (sitecheck, v0.5.0–v0.8.0):

- Artifacts are Claude-authored — verbatim HTML publishing removed as a viable design; sanitized-payload boundary, link contract, update-in-place, truthful refresh disclosure (`live-artifacts.md`).
- Native-connector capability model: create-and-read-only surfaces, the append-only design rule (`connectors-and-mcp.md`); Drive production facts — Shared Drive limitation, sync trap (Drive recipe).
- State-home doctrine (`skill-authoring.md` § Where mutable state lives) + Phase 2 state question and Phase 3 Cowork gates (`build-spine.md`).
- Standalone fallback never silently replaces a configured connector; onboarding first-run pattern (`skill-authoring.md`).
- Probe the real path — capability checks run the plugin's actual code path (`cowork-runtime.md`).
- Audit: deviations doc honored (item 0), connector-safe state (item 14), truthful artifact disclosure (item 9); self-marketplace and git-archive packaging sanctioned as recognized alternatives (items 10/13, `distribution.md`).

## [0.1.0] - 2026-07-21
### Added
- Initial claude-cowork-builder: build menu, 6-phase spine, skill-authoring / connectors / agent-playbook / distribution / live-artifacts / audit references, plugin/skill/agent templates, and the Google Drive integration recipe.
