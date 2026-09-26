# claude-skills

A public mirror of the Claude Code skills I use day-to-day. Each folder is a self-contained skill (`SKILL.md` + supporting `references/`, `scripts/`, `assets/` as needed) that can be dropped into `~/.claude/skills/` or uploaded to Claude.ai.

## Index

| Skill | What it does |
|---|---|
| [front-end-engineer](front-end-engineer/) | Authority on HTML markup — semantically correct (MDN) HTML in a consistent personal style, with write + audit modes and routing to sibling front-end skills. |
| [sass](sass/) | Modern CSS (2020–2025) and advanced animations for developers with strong fundamentals. |
| [web-security](web-security/) | Application-level security for WordPress, Laravel, Django, FastAPI, and Dash. OWASP Top 10 (2021). |
| [python](python/) | Modern Python (3.12+) across `uv` scripting, Django, Flask, FastAPI, type checking, and pytest. |
| [plotly-dash](plotly-dash/) | Expert guidance for self-hosted, open-source Plotly Dash apps — callbacks, DataTable, deployment. |
| [cloud-run-functions](cloud-run-functions/) | Build, deploy, debug, and cost-tune Google Cloud Run functions in Python, with a fit gate that routes misfit workloads to Cloud Run services, jobs, or worker pools. |
| [wordpress-themes](wordpress-themes/) | VIP-standard custom theme development with modular structure and modern tooling. |
| [wordpress-blocks](wordpress-blocks/) | Custom Gutenberg blocks with server-side PHP rendering and clean editor/developer separation. |
| [wordpress-plugins](wordpress-plugins/) | Build, audit, extend, and release custom WordPress plugins to VIP standards — performant at scale, with a bundled scaffolder, security/performance/docs references, and a graded audit mode. |
| [orko](orko/) | Multi-expert engagements with the project's scaffold `docs/` repository as the record. `/orko <question>` decomposes an analysis, review, or research task into expert seats, verifies their findings, and commits an attributed review; `/orko build <goal> [--executor codex]` runs spec, spec review, plan, plan review, a human acceptance gate, execution by Claude or Codex, code review, and close, one committed record per decision. Replaces the retired `autonom` and `codex-orko` skills. |
| [orko-sdd](orko-sdd/) | Standing orchestrator overlay for `superpowers:subagent-driven-development`. `/orko-sdd <plan-path> [--release-critical]` runs a written plan under SDD with a model and effort policy per role, evergreen-conflict handling, safety stops, and a script-built final report. Its worker agents need a second symlink: `ln -s <repo>/orko-sdd/agents ~/.claude/agents/orko-sdd`. |
| [git-tagging](git-tagging/) | Semantic versioning, annotated git tags, GitHub Releases, and CHANGELOG maintenance. |
| [product-management](product-management/) | Generate-first product management artifacts — PRDs, problem statements, OKRs, strategy one-pagers, roadmaps, RACI, personas, and retrospectives. |
| [google-style](google-style/) | Writes and edits technical prose to the Google developer documentation style guide, with a bundled checker for the mechanically verifiable rules. |
| [sumlog](sumlog/) | On-demand session log: a dated Markdown file with a short summary and every prompt typed in the session, verbatim. |

## Installing a skill

```bash
cp -R <skill-name> ~/.claude/skills/
```

Or upload the matching `<skill-name>.zip` via Claude.ai → Settings → Capabilities → Skills.

## Archived

Archived on 26 Sep 2026. These folders stay in the repo for reference but are no longer maintained.

| Skill | What it does |
|---|---|
| [autonom](autonom/) | Retired redirect stub for the unattended spec-and-plan pipeline, which moved into `/orko build`. |
| [claude-cowork-builder](claude-cowork-builder/) | Builds Claude Cowork plugins — skills, agents, MCP connectors, and custom UI packaged into an installable `.plugin`. |
| [codex-orko](codex-orko/) | Retired redirect stub for the Claude-plans, Codex-executes stance, which moved into `/orko build --executor codex`. |
| [guardian-claude-code](guardian-claude-code/) | Audits Claude Code's third-party trust surface (MCP servers, plugins, hooks) for supply-chain risk. |
| [using-opencode](using-opencode/) | On-demand guide for using OpenCode, especially when coming from Claude Code. |
