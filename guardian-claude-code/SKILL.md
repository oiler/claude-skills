---
name: guardian-claude-code
description: Audits Claude Code's third-party trust surface for supply-chain risk — MCP servers, installed plugins/skills, and SessionStart/PreToolUse hooks. Use when the user asks to audit their Claude Code setup for security, check for compromised MCPs or plugins, scan for recent updates within the cooldown window, investigate "is it safe to install X", review what changed in their plugins or MCPs, or wants supply-chain protection for their dev environment. Also triggers on "guardian", "guardian-claude-code", "audit my claude code", "supply chain", "check my MCPs", "what changed in my plugins", "is this package safe", "review my third-party skills". Pairs with advisor-claude-code (config tuning) and web-security (application code) — this one is meta-tooling for the dev environment itself.
---

# guardian-claude-code

Audit the third-party trust surface that Claude Code depends on. Detects recently-updated packages, capability expansion in updates, source-URL inconsistencies, maintainer changes, and silent drift since the last session.

## When to use this skill

| Situation | Action |
|---|---|
| User asks to audit their setup for supply-chain risk | Run deep mode |
| SessionStart hook fires this skill's quick mode | Surface changes in 1-2 lines |
| User asks "is it safe to install X" | Run deep mode after install, before active use |
| User asks about a specific MCP or plugin | Run deep mode, narrate findings for that item |
| User wants CLAUDE.md / permission hygiene review | Use `advisor-claude-code` instead |
| User wants application-code security review | Use `web-security` instead |

## How to invoke

**Deep audit (on-demand):**

```bash
uv run ~/.claude/skills/guardian-claude-code/scripts/audit.py deep
```

Returns structured JSON findings. Takes <30s. Hits npm, PyPI, and GitHub APIs (cached 1h).

**Quick diff (SessionStart):**

```bash
uv run --quiet ~/.claude/skills/guardian-claude-code/scripts/audit.py quick
```

No network. Diffs against last snapshot. Takes <2s.

## How to interpret findings

Group findings by severity. Process **high** first, then **warn**, then **info**.

### High-severity categories (cannot be silenced by ordinary overrides)

- **`capability_diff`** — An update added new tools/hooks/permissions. This is the highest-signal hijack tell. Inspect the changelog. If the expansion isn't explained, revert or pin to the previous version.
- **`url_mismatch`** — The manifest's source URL doesn't match the registry's repository URL. Almost always typosquatting or repo hijack. Verify the package's true origin.
- **`maintainer_change`** — Publisher of the package changed since last snapshot. Could be legitimate (project handoff) or the "I sold my package" attack vector. Confirm.

### Warn / info categories (silenceable via overrides)

- **`cooldown`** — Item published within 7 days. Most are benign — official Anthropic plugins, packages the user actively tracks. Apply judgment: is this a package the user trusts and follows closely? If yes, offer to add `cooldown_exempt`. If no, suggest waiting until day 7.
- **`repo_health`** — Upstream repo archived. Soft signal. Note it; don't push hard.
- **`new_item` / `removed_item`** — Drift since last snapshot. Surface in 1 line. If the user didn't intend the change, it's a flag.

## How to offer fixes

For each finding, the JSON includes `fix_hint`. Translate to concrete action:

- "Remove from settings.json" → use `update-config` skill to edit settings
- "Pin to previous version" → propose the exact settings.json edit, ask for approval
- "Add trust override" → propose an override entry; require a `reason`; never silently disarm a high-signal category

Always ask before applying. Never auto-apply.

## Trust override discipline

When offering to write an override:

1. Propose the smallest possible override (prefer `silence_until_version` over `cooldown_exempt`).
2. Require a `reason` from the user — surface it in your proposal.
3. For `force_silence_all`: push back. Explain that it disables `capability_diff`, `url_mismatch`, and `maintainer_change` for this item, which are the categories that catch actual compromises. Ask if the user is sure.

## First-time setup

On first invocation, check whether the SessionStart hook is installed:

```bash
grep -q 'guardian-claude-code' ~/.claude/settings.json || echo "hook not installed"
```

If not installed, offer to add it (see `references/hook-install.md`). The skill works on-demand without it; the hook adds drift detection.

If `~/.claude/guardian/snapshot.json` doesn't exist, the first deep audit creates it. Quick mode before any baseline returns a "first run — no baseline" message.

## Reference docs

| Doc | When to read |
|---|---|
| `references/findings-schema.md` | Need exact field meanings or evidence shapes |
| `references/trust-overrides.md` | Writing or proposing an override entry |
| `references/hook-install.md` | Wiring or removing the SessionStart hook |
| `references/threat-model.md` | User asks what the skill protects against |

## Relationship to other skills

- **`advisor-claude-code`** — Adjacent meta-skill for Claude Code itself. Advisor tunes config quality (CLAUDE.md size, hook hygiene, permission breadth). Guardian audits third-party trust. Both can run from SessionStart; outputs are visually distinct.
- **`web-security`** — Unrelated. That covers application code; this covers the dev environment.
- **`update-config`** — Guardian delegates settings.json edits (removing an MCP, disabling a hook) to `update-config` when offering fixes.

## What this skill does NOT do

- Does not gate or sandbox tool execution at runtime.
- Does not scan application code for vulnerabilities (use `web-security`).
- Does not enumerate claude.ai account-level connectors — those aren't visible from local config. Print a reminder to review them via `/mcp`.
- Does not modify settings.json without explicit user approval.
