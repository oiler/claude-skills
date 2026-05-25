# Findings Schema

`scripts/audit.py` emits a JSON object to stdout. The shape:

```json
{
  "mode": "quick | deep",
  "baseline_established": true,
  "message": "human-readable summary (quick mode only)",
  "notices": ["optional list of skipped checks"],
  "findings": [ { ...finding... } ]
}
```

## Finding record

```json
{
  "severity": "high | warn | info",
  "category": "cooldown | capability_diff | url_mismatch | maintainer_change | repo_health | new_item | removed_item",
  "surface": "mcp | plugin | skill | hook | connector",
  "item": "name-of-the-thing",
  "signal": "one-line human description",
  "evidence": { ...category-specific fields... },
  "fix_hint": "short suggested remediation"
}
```

## Categories and what they mean

| Category | Severity | Fires when | Silenceable |
|---|---|---|---|
| `cooldown` | warn | Item published less than 7 days ago | Yes |
| `capability_diff` | high | Existing item updated and declares new tools/hooks/permissions | **No** |
| `url_mismatch` | high | Manifest source URL doesn't match registry repository URL | **No** |
| `maintainer_change` | high | Registry publisher differs from snapshot's recorded publisher | **No** |
| `repo_health` | info | Upstream GitHub repo is archived | Yes |
| `malformed_manifest` | warn | An enumeration target's manifest file (plugin.json, hooks.json, etc.) couldn't be parsed | Yes |
| `new_item` | info | Item present in current scan, absent in last snapshot | Yes |
| `removed_item` | info | Item present in last snapshot, absent in current scan | Yes |

High-signal categories (`capability_diff`, `url_mismatch`, `maintainer_change`) cannot be silenced by ordinary overrides — only by `force_silence_all`, which requires an explicit reason.

## Evidence fields by category

| Category | Evidence fields |
|---|---|
| `cooldown` | `current_version`, `publish_date`, `days_ago` |
| `capability_diff` | `added` (list of capability strings), `previous_version`, `current_version` |
| `url_mismatch` | `manifest_url`, `registry_url` |
| `maintainer_change` | `previous_publisher`, `current_publisher`, `previous_version`, `current_version` |
| `repo_health` | `repository`, `archived`, `last_push_date` |
| `malformed_manifest` | (none — see `signal` field for parse error message) |
| `new_item`, `removed_item` | `source`, `version` |

## How the skill uses these

The SKILL.md teaches the model to:

1. Group findings by severity (`high` first, then `warn`, then `info`).
2. Apply contextual judgment — official Anthropic plugins updating, etc.
3. Offer to act on `fix_hint` interactively.
4. Offer to add a trust override for benign findings the user dismisses.
