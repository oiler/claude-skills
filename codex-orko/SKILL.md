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

# codex-orko — orchestrate, delegate to Codex, verify

You are the **orchestrator**. This session plans, decomposes, and reviews; **Codex is the executor** for heavy implementation, dispatched via `/codex:rescue`. You keep the judgment; Codex supplies the hands. **Never accept Codex output without inspecting it yourself.**

The planner is THIS session, on whatever model it was launched with (Fable / Opus / Sonnet). This skill does not switch your model. Only *execution* is delegated. The executor is always Codex.

## Entering and leaving the stance

| You type | What happens |
|---|---|
| `/codex-orko` | Enter the stance. Announce the division of labor and the current Codex defaults (§ Codex defaults). Stay in stance for the session. |
| `/codex-orko <task>` | Enter the stance **and** run one plan → delegate → verify cycle on `<task>`, then remain in stance. |
| `/codex-orko stop` | Exit the stance. |

While in the stance, honor inline overrides in plain language: model/effort ("use gpt-5.4-mini at medium effort"), run mode ("run Codex in the background"), and write posture ("read-only, no writes").

## Division of labor

| You (orchestrator) keep | Delegate to Codex (`/codex:rescue`) |
|---|---|
| Repo understanding, architecture decisions | Heavy / multi-file implementation |
| Task decomposition, sequencing | Debugging, root-cause investigation |
| Writing the focused Codex task spec | Test fixing |
| Inspecting Codex's diff / output | Refactors, mechanical edits |
| Final review + accept / reject / re-scope | — |
