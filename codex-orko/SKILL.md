---
name: codex-orko
description: >-
  Retired. The brain/hands stance where Claude plans and Codex executes now
  runs inside orko as `/orko build <goal> --executor codex`. Triggers on
  "codex-orko", "orchestrate with Codex", "Claude plans Codex executes",
  "delegate implementation to Codex", "use Codex as the executor",
  "brain-hands split", "hand this to Codex and verify". It prints the redirect
  and does nothing else. For a plain one-off dispatch use /codex:rescue.
  Last full version: codex-orko-v0.1.0.
metadata:
  author: oiler
  version: 0.2.0
---

# codex-orko (retired)

The stance this skill provided (Claude as architect and reviewer with Codex as the executor) is now the Codex executor of the `orko` build engagement. Invoke `/orko build <goal> --executor codex`. The per-task loop, Codex defaults, and resume rules live in `orko/references/codex.md`.

For a single dispatch with no plan or record, use `/codex:rescue` directly.

Nothing else in this folder is live. The last full release is tagged `codex-orko-v0.1.0`.

Tell the user this skill is retired and name the replacement. Do not enter any stance.
