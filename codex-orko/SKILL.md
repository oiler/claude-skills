---
name: codex-orko
description: >-
  Orchestration stance where THIS Claude session stays the architect and
  reviewer while Codex does the heavy implementation, dispatched through the
  openai-codex plugin's /codex:rescue. Use when you want a brain/hands split:
  Claude plans, decomposes, and verifies; Codex executes. Triggers on "codex-orko",
  "orchestrate with Codex", "you are the orchestrator", "Claude plans Codex executes",
  "delegate implementation to Codex", "use Codex as the executor", "brain-hands split",
  "hand this to Codex and verify", "be the orchestrator and let Codex build".
  Enter with /codex-orko (bare = enter stance; with a task = run one plan→delegate→verify
  cycle then stay in stance; "stop" = exit). NOT for a plain one-off dispatch to Codex
  (use /codex:rescue directly) and NOT for parallel fan-out across independent tasks
  (use superpowers:dispatching-parallel-agents). Requires the openai-codex plugin
  installed and authenticated.
---
