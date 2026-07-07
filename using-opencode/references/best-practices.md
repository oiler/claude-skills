> Digest verified 2026-07-06 against https://opencode.ai/docs. Version-sensitive items carry inline verify pointers.

# OpenCode usage best practices

## Modes & flow

- Plan mode (toggle with Tab) disables the agent's ability to make changes and instead proposes HOW it will implement.
- Build mode executes changes.
- Recommend plan-then-build for non-trivial features; use direct Build for straightforward changes.
- (verify: /docs/agents)

## /init & AGENTS.md discipline

- Run `/init` per project; it scans the repo, may ask a couple targeted questions, and writes/updates `AGENTS.md`. Commit `AGENTS.md` to git.
- Keep AGENTS.md concise: build/lint/test commands, architecture/structure not obvious from filenames, project conventions, setup quirks/gotchas.
- Reuse existing rule files via the `instructions` field in `opencode.json` (supports globs like `packages/*/AGENTS.md` and remote URLs, fetched with a 5s timeout) rather than duplicating into AGENTS.md.
- (verify: /docs/rules)

## Sessions & subagents

- Built-in subagents: General (full tool access, multi-step work / parallel units), Explore (fast, read-only, code search), Scout (read-only, external docs & dependency research).
- Invoke subagents by `@mention`; primary agents can also invoke them automatically based on descriptions.
- Navigate child sessions with the session child/parent keybinds.
- (verify: /docs/agents)

## Undo / redo & sharing

- `/undo` reverts the last change and restores your prompt to edit and retry; `/redo` reapplies. Both are repeatable.
- `/share` creates a shareable conversation link; conversations are NOT shared by default.
- (verify: /docs/share)

## Permissions posture

- Permission values are `ask` / `allow` / `deny`, matched as glob/wildcard patterns; per-agent overrides supported.
- Last matching rule wins — put the `*` wildcard first and specific rules after.
- Favor default-deny for destructive bash and edits on planning/review agents.
- (verify: /docs/permissions)

## Providers & models hygiene

- `/connect` to add provider credentials, `/models` to switch model, `opencode models` to list available models.
- Set a sensible global default via the `model` key in `opencode.json`.
- For WHICH model to use and how to wire per-agent/parallel models, see multi-model.md. For EDITING config, use the customize-opencode skill.
- (verify: /docs/models, /docs/providers)
