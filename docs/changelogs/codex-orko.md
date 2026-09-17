# codex-orko — Changelog

## v0.2.0 — 2026-09-08

Retired. The skill is now a redirect stub pointing at `/orko build <goal> --executor codex`. The stance it provided (Claude as architect and reviewer with Codex as the executor) is the Codex executor of the orko build engagement (see orko v2.0.0); the per-task loop, Codex defaults, and resume rules live in `orko/references/codex.md`. A plain one-off dispatch with no plan or record still goes to `/codex:rescue`.

## v0.1.0 — 2026-07-11

Initial release. An orchestration stance: this Claude session stays the architect and reviewer while Codex does the implementation, dispatched through the openai-codex plugin's `/codex:rescue`. `/codex-orko` bare enters the stance, with a task runs one plan-delegate-verify cycle and stays in stance, and `stop` exits.
