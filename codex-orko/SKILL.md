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

## Codex defaults

Dispatch every Codex task with these defaults, stated explicitly (`/codex:rescue` leaves model/effort unset otherwise):

```
/codex:rescue --model gpt-5.5 --effort xhigh --write <focused task>
```

- **Foreground** by default. Add `--background` for long runs, then check back.
- **Model slugs** (all support effort `low|medium|high|xhigh`; verified against the local Codex model cache — do not invent others):

  | `--model` | When |
  |---|---|
  | `gpt-5.5` | **Default** — frontier coding/research. |
  | `gpt-5.4` | Prior frontier tier. |
  | `gpt-5.4-mini` | Cheap/fast mechanical tasks. |
  | `spark` | Speed (plugin maps it to `gpt-5.3-codex-spark`). |

- **Effort:** `xhigh` by default. Drop to `high`/`medium` for cheap mechanical work.
- **Write posture:** `--write` (Codex edits files) by default, matching real implementation. For diagnosis/review only, omit `--write` and say "read-only".
- **Thread continuity:** `--resume` to continue the current Codex thread, `--fresh` to start clean.

### Dependency

This skill requires the **openai-codex** plugin, installed and authenticated. If a dispatch reports Codex missing or unauthenticated, stop and tell the user to run **`/codex:setup`** — do not improvise a workaround.

## The cycle (run this every task)

1. **Scope** — one clear objective, self-contained. Give Codex the files, the goal, and the acceptance check. See the task template below.
2. **Dispatch** — `/codex:rescue` with the current defaults/overrides.
3. **Inspect** — read the actual diff/output yourself. **Non-negotiable: do not blindly trust Codex output.**
4. **Verify** — run tests / typecheck / lint where relevant before declaring done.
5. **Accept or re-scope** — if Codex went sideways, tighten the task and re-delegate (`--resume`) rather than silently hand-patching.

## How to write a good Codex task

Keep it focused and specific. Include:
- **Objective** — one outcome, stated plainly.
- **Context** — the exact files/functions in play and any constraint (style, framework, version).
- **Acceptance** — how Codex (and you) will know it's done: the test that must pass, the behavior to see.

Prefer several tight tasks over one sprawling one. A task Codex can hold in context is a task Codex gets right.

## When NOT to use this skill

- **A plain one-off "just send this to Codex"** → call `/codex:rescue` directly. You don't need the stance for a single dispatch.
- **Parallel fan-out across independent tasks** → use `superpowers:dispatching-parallel-agents`. This skill is the *serial* brain-hands stance, not a parallel dispatcher.
- **Analysis / PM orchestration** → that's the `orko` skill, a different domain.
