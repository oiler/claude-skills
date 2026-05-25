# SessionStart Hook Installation

Wire the quick-mode audit into your SessionStart hook so drift gets surfaced on every session.

## Add to `~/.claude/settings.json`

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{
        "type": "command",
        "command": "uv run --quiet ~/.claude/skills/guardian-claude-code/scripts/audit.py quick"
      }]
    }]
  }
}
```

If you already have other SessionStart hooks, append this hook block to the existing `SessionStart` entry rather than replacing it.

## What it does

On every session start, the hook runs `audit.py quick`. Quick mode:

- Makes no network calls
- Compares the current enumeration against `~/.claude/guardian/snapshot.json`
- Prints a JSON payload of changes since the last snapshot
- Always exits 0 — it never blocks session start

The skill's SKILL.md teaches Claude to read this output, surface anything interesting in 1-2 lines, and remind you that a deep audit will explain why.

## Removing the hook

Delete the entry from `~/.claude/settings.json`. The skill continues to work on-demand without it.
