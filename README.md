# claude-skills

A public mirror of the Claude Code skills I use day-to-day. Each folder is a self-contained skill (`SKILL.md` + supporting `references/`, `scripts/`, `assets/` as needed) that can be dropped into `~/.claude/skills/` or uploaded to Claude.ai.

## Index

| Skill | What it does |
|---|---|
| [front-end-engineer](front-end-engineer/) | Authority on HTML markup — semantically correct (MDN) HTML in a consistent personal style, with write + audit modes and routing to sibling front-end skills. |
| [git-tagging](git-tagging/) | Semantic versioning, annotated git tags, GitHub Releases, and CHANGELOG maintenance. |
| [guardian-claude-code](guardian-claude-code/) | Audits Claude Code's third-party trust surface (MCP servers, plugins, hooks) for supply-chain risk. |
| [orko](orko/) | PM-run multi-expert engagements — decomposes a review, audit, or research task into role-specialized expert seats, dispatches each to a tier-appropriate model, and reports verified, attributed findings. |
| [plotly-dash](plotly-dash/) | Expert guidance for self-hosted, open-source Plotly Dash apps — callbacks, DataTable, deployment. |
| [python](python/) | Modern Python (3.12+) across `uv` scripting, Django, Flask, FastAPI, type checking, and pytest. |
| [sass](sass/) | Modern CSS (2020–2025) and advanced animations for developers with strong fundamentals. |
| [web-security](web-security/) | Application-level security for WordPress, Laravel, Django, FastAPI, and Dash. OWASP Top 10 (2021). |
| [wordpress-blocks](wordpress-blocks/) | Custom Gutenberg blocks with server-side PHP rendering and clean editor/developer separation. |
| [wordpress-themes](wordpress-themes/) | VIP-standard custom theme development with modular structure and modern tooling. |

## Installing a skill

```bash
cp -R <skill-name> ~/.claude/skills/
```

Or upload the matching `<skill-name>.zip` via Claude.ai → Settings → Capabilities → Skills.
