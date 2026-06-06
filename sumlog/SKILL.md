---
name: sumlog
description: Generate an on-demand session log written to a dated Markdown file in the current project. Use ONLY when explicitly invoked as /sumlog, or when the user says "log this session", "summarize this session to a file", "create a session log", "session handoff", or "write a session log". Produces a three-part log — a 3-4 sentence human summary, every prompt the user typed verbatim and untruncated, and a YAML handoff-state block for resuming work in a future session.
disable-model-invocation: true
allowed-tools: Bash, Read, Write
---

# sumlog — on-demand session log

Writes a deterministic three-part session log to `docs/session-logs/YYYY-MM-DD-<slug>.md` in the current project. Run the extractor, assemble the document, write it, report the path.

## Steps

1. **Extract the session data.** Run:

   ```bash
   uv run "${CLAUDE_SKILL_DIR}/scripts/extract_session.py"
   ```

   It prints one JSON object: `{ "prompts_markdown": "...", "metadata": {...} }`.
   If it exits non-zero (no session id, or transcript missing), **STOP** and report the error. Do not write a partial log.

2. **Assemble the document.** Title: `# Session Log — <date> — <slug>`. Then exactly three sections:

   - `## Summary` — write 3-4 sentences: what this session was about and where it stands. Human-readable.
   - Splice `prompts_markdown` in **byte-exact**. Do not reformat, renumber, truncate, or paraphrase it.
   - `## Handoff State` — a single ```yaml code block. First copy the deterministic fields from `metadata` verbatim: `session_id`, `date`, `cwd`, `git_branch`, `prompt_count`, `tools_used`, `files_touched`. Then add your judgment fields: `goal`, `work_completed`, `decisions`, `open_threads`, `next_steps`, `key_facts`.

3. **Choose the path.** `<slug>` is a short kebab-case summary of the session topic (derive it from the goal / first prompt). Path: `docs/session-logs/<date>-<slug>.md` using the `date` from `metadata`. If that file already exists, append `-2`, `-3`, etc.

4. **Write the file** with the Write tool. Create `docs/session-logs/` if needed.

5. **Report only the written path.** Do not dump the log contents into the chat.

## Notes

- Prompts come from the on-disk transcript, so they are complete even if the context window was compacted mid-session.
- Scope: the single current session only. Resumed sessions spanning multiple transcript files are out of scope.
