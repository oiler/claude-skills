# Trust Overrides

User-authored exemptions stored at `~/.claude/guardian/trust-overrides.json`.

## File format

```json
{
  "overrides": [
    {
      "surface": "mcp | plugin | skill | hook",
      "item": "name-of-the-thing",
      "rules": { ...rule... },
      "reason": "free-text explanation (required for force_silence_all)",
      "added": "YYYY-MM-DD"
    }
  ]
}
```

## Rule types

| Rule | Effect |
|---|---|
| `"cooldown_exempt": true` | Skips the 7-day recency check for this item |
| `"silence_until_version": "X.Y.Z"` | Silences findings until the item crosses this version |
| `"silence_until_date": "YYYY-MM-DD"` | Silences findings until the date passes |
| `"force_silence_all": true` | Silences every category, including high-signal ones. Requires `reason`. Use sparingly. |

## What overrides can silence

Overrides apply only to the noisy categories: `cooldown`, `repo_health`, `new_item`, `removed_item`.

The high-signal categories — `capability_diff`, `url_mismatch`, `maintainer_change` — fire regardless of overrides. The only escape is `force_silence_all`, which requires an explicit `reason` and is treated as a code smell by the skill (the model is instructed to push back when offering to write one).

## Example

```json
{
  "overrides": [
    {
      "surface": "mcp",
      "item": "courtlistener",
      "rules": {"cooldown_exempt": true},
      "reason": "Actively tracked project; recency isn't a concern",
      "added": "2026-05-24"
    },
    {
      "surface": "plugin",
      "item": "example-plugin",
      "rules": {"silence_until_version": "2.0.0"},
      "reason": "Known stable; re-evaluate at next major"
    }
  ]
}
```
