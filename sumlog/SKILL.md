---
name: sumlog
description: Generate an on-demand session log written to a dated Markdown file in the current project. Use ONLY when explicitly invoked as /sumlog, or when the user says "log this session", "summarize this session to a file", "create a session log", "session handoff", or "write a session log". Produces a three-part log — a 3-4 sentence human summary, every prompt the user typed verbatim and untruncated, and a YAML handoff-state block for resuming work in a future session.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
---

# sumlog — on-demand session log

Writes a deterministic three-part session log to `docs/session-logs/YYYY-MM-DD-<slug>.md` in the current project. Run the extractor, assemble the document, write it, report the path.

The script owns every prompt byte and the final file write. You author only the summary and the handoff judgment fields — you never copy prompts yourself, so the log is byte-exact by construction.

## Steps

1. **Read the session context.** Run:

   ```bash
   uv run "${CLAUDE_SKILL_DIR}/scripts/extract_session.py"
   ```

   It prints one JSON object: `{ "prompts_markdown": "...", "metadata": {...} }`.
   If it exits non-zero (no session id, or transcript missing), **STOP** and report the error.
   Read this to understand the session. Do **not** copy `prompts_markdown` — the script splices it verbatim in step 3.

2. **Write your two authored pieces to temp files.** From the prompts and metadata:

   - A **summary** — 3-4 sentences on what the session was about and where it stands. Write it to a temp file (e.g. `summary=$(mktemp)`).
   - The **handoff judgment fields** as YAML — write to a second temp file (e.g. `handoff=$(mktemp)`). Include only: `goal`, `work_completed`, `decisions`, `open_threads`, `next_steps`, `key_facts`. Do **not** include the deterministic fields (`session_id`, `date`, `cwd`, `git_branch`, `prompt_count`, `tools_used`, `files_touched`) — the script adds those.

   Also choose a short kebab-case `<slug>` describing the session topic.

3. **Assemble the log.** Run:

   ```bash
   uv run "${CLAUDE_SKILL_DIR}/scripts/extract_session.py" --assemble \
     --slug <slug> --summary-file "$summary" --handoff-file "$handoff"
   ```

   The script splices your verbatim prompts and deterministic metadata, injects your summary and handoff fields, writes `docs/session-logs/<date>-<slug>.md` (numeric suffix on same-day collision), and prints the path.

4. **Report only the printed path.** Do not dump the log contents into the chat.

## Notes

- Prompts come from the on-disk transcript, so they are complete even if the context window was compacted mid-session.
- Scope: the single current session only. Resumed sessions spanning multiple transcript files are out of scope.
