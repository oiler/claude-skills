> Verified 2026-07-06 against https://opencode.ai/docs/models and /docs/agents. The recommended-model list is volatile — always verify at /docs/models.

# Multi-model: which model, and how to wire it

## Decision framework — which model for which task

Match the task's dominant demand to model traits, then pick a current example. All examples are volatile — the recommended list changes and is non-exhaustive.

| Task type | Traits to favor | Example(s) |
|---|---|---|
| Deep reasoning / architecture | Strong chain-of-thought, high reasoning-effort budget | Claude Opus 4.5 `(verify at /docs/models — list changes)`; GPT 5.2 `(verify at /docs/models — list changes)` |
| Fast & cheap planning / triage | Low latency, low cost, decent instruction-following | Claude Sonnet 4.5 `(verify at /docs/models — list changes)`; Minimax M2.1 `(verify at /docs/models — list changes)` |
| Long-context synthesis | Large context window, stable recall across the window | Gemini 3 Pro `(verify at /docs/models — list changes)`; Claude Opus 4.5 `(verify at /docs/models — list changes)` |
| Strong tool-calling / codegen | Reliable structured tool calls + code quality | GPT 5.1 Codex `(verify at /docs/models — list changes)`; GPT 5.2 `(verify at /docs/models — list changes)` |

Only a subset of models are strong at BOTH codegen AND tool-calling at once — do not assume a good coder calls tools reliably. Prefer the docs' recommended list over guessing.

Recommended examples as of 2026-07-06 (VOLATILE — verify at /docs/models): GPT 5.2, GPT 5.1 Codex, Claude Opus 4.5, Claude Sonnet 4.5, Minimax M2.1, Gemini 3 Pro.

## Wiring — how to run different models

Model IDs use the format `provider/model-id`. Examples:

- `anthropic/claude-sonnet-4-5`
- `openai/gpt-5`
- `opencode/gpt-5.1-codex` (via OpenCode Zen)

OpenCode reaches 75+ providers via the AI SDK + models.dev. Use `/connect` to add credentials, `/models` to switch interactively, and `opencode models` to list what's available.

Ways to set the model, from broadest to narrowest scope:

- **Global default** — the `model` key in `opencode.json`.
- **Per-agent override** — the `model` field, set either in a JSON `agent{}` block or in a markdown-agent's frontmatter (`~/.config/opencode/agents/*.md` or `.opencode/agents/*.md`).
- **Subagent inheritance** — subagents inherit the invoking primary agent's model unless they set their own `model`.

Provider-specific options pass through the config. OpenAI reasoning models take `reasoningEffort` and `textVerbosity`; Anthropic takes `thinking.budgetTokens`. Variants exist per option (e.g. `high` / `max` / `low`).

Concrete example — two subagents pinned to DIFFERENT providers, each scoped to read-appropriate work, ready for parallel dispatch:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "agent": {
    "researcher": {
      "description": "Long-context doc synthesis, read-only",
      "mode": "subagent",
      "model": "google/gemini-3-pro",
      "tools": { "write": false, "edit": false }
    },
    "codegen": {
      "description": "Tool-calling + code generation",
      "mode": "subagent",
      "model": "openai/gpt-5.1-codex",
      "reasoningEffort": "high"
    }
  }
}
```

Editing this config is the `customize-opencode` skill's job.

## Running the streams in parallel (handoff)

Parallel work streams = define subagents on different providers (as above), then dispatch them concurrently via the Task tool or `@mention`.

Do NOT reimplement fan-out logic here:

- Orchestrated fan-out WITH synthesis → hand off to the `orko` skill.
- Simpler independent parallel dispatch → hand off to `dispatching-parallel-agents`.
