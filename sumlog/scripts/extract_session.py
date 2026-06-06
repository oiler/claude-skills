# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Extract verbatim typed prompts and metadata from the current Claude Code session transcript."""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)


def _prompt_text(content):
    """Return the human-typed text for a user record's content, or None if it is not a prompt."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        if not parts:
            return None  # tool_result-only or non-text content is not a prompt
        text = "\n".join(parts)
    else:
        return None
    text = SYSTEM_REMINDER_RE.sub("", text).strip()
    return text or None


FILE_TOOLS = {"Read", "Write", "Edit", "NotebookEdit"}


def tilde(path):
    """Replace a leading $HOME with ~ for portability/privacy; leave non-home paths absolute."""
    home = str(Path.home())
    if path == home:
        return "~"
    if path.startswith(home + "/"):
        return "~" + path[len(home):]
    return path


def build_metadata(records):
    """Tool-use counts and de-duplicated file paths touched, from assistant tool_use blocks."""
    tools = Counter()
    files = []
    for r in records:
        if r.get("type") != "assistant":
            continue
        for b in r.get("message", {}).get("content", []):
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            name = b.get("name", "")
            tools[name] += 1
            if name in FILE_TOOLS:
                fp = b.get("input", {}).get("file_path")
                if fp:
                    fp = tilde(fp)
                    if fp not in files:
                        files.append(fp)
    return {"tools_used": dict(tools), "files_touched": files}


def _tool_result_map(records):
    """Map each tool_use id to its structured toolUseResult (rides on the tool_result record)."""
    results = {}
    for r in records:
        result = r.get("toolUseResult")
        if not isinstance(result, dict):
            continue
        for b in r.get("message", {}).get("content", []) if isinstance(r.get("message"), dict) else []:
            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id"):
                results[b["tool_use_id"]] = result
    return results


def extract_agents(records):
    """Each Agent dispatch, joined with its result: label, type, model, status, and rollup stats."""
    results = _tool_result_map(records)
    agents = []
    for r in records:
        if r.get("type") != "assistant":
            continue
        for b in r.get("message", {}).get("content", []):
            if not isinstance(b, dict) or b.get("type") != "tool_use" or b.get("name") != "Agent":
                continue
            inp = b.get("input", {})
            res = results.get(b.get("id"), {})
            agents.append({
                "label": inp.get("description", "(no label)"),
                "agent_type": res.get("agentType") or inp.get("subagent_type", "?"),
                "model": inp.get("model") or "inherit",
                "status": res.get("status", "(no result)"),
                "tokens": res.get("totalTokens", 0),
                "tool_uses": res.get("totalToolUseCount", 0),
                "duration_ms": res.get("totalDurationMs", 0),
            })
    return agents


def build_agents_markdown(agents):
    """Render dispatched subagents as a table with a totals line, or '' if there were none."""
    if not agents:
        return ""
    lines = [
        "## Agents Dispatched",
        "",
        "| # | Label | Type | Model | Status | Tokens | Tools | Duration |",
        "|---|-------|------|-------|--------|--------|-------|----------|",
    ]
    total_tokens = 0
    for i, a in enumerate(agents, 1):
        label = str(a["label"]).replace("|", "\\|")
        total_tokens += a["tokens"]
        lines.append(
            f"| {i} | {label} | {a['agent_type']} | {a['model']} | {a['status']} | "
            f"{a['tokens']:,} | {a['tool_uses']} | {a['duration_ms'] / 1000:.1f}s |"
        )
    lines += ["", f"_{len(agents)} agents, {total_tokens:,} subagent tokens total._"]
    return "\n".join(lines)


def extract_tasks(records):
    """Reconstruct the session task list. Replays TaskCreate/TaskUpdate events in order;
    falls back to the last TodoWrite snapshot if the incremental task tools weren't used."""
    results = _tool_result_map(records)
    tasks = {}        # id -> {"id", "subject", "status"}
    order = []
    used_task_tools = False
    last_todos = None
    for r in records:
        if r.get("type") != "assistant":
            continue
        for b in r.get("message", {}).get("content", []):
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            name = b.get("name")
            inp = b.get("input", {})
            res = results.get(b.get("id"), {})
            if name == "TaskCreate":
                used_task_tools = True
                task = res.get("task") if isinstance(res, dict) else None
                tid = (task or {}).get("id") or str(len(order) + 1)
                subject = (task or {}).get("subject") or inp.get("subject", "(untitled)")
                if tid not in tasks:
                    tasks[tid] = {"id": tid, "subject": subject, "status": "pending"}
                    order.append(tid)
            elif name == "TaskUpdate":
                used_task_tools = True
                if isinstance(res, dict) and res.get("success"):
                    tid = res.get("taskId")
                    to = (res.get("statusChange") or {}).get("to") or inp.get("status")
                    if tid in tasks and to:
                        tasks[tid]["status"] = to
            elif name == "TodoWrite":
                todos = inp.get("todos")
                if isinstance(todos, list):
                    last_todos = todos
    if used_task_tools:
        return [tasks[t] for t in order]
    if last_todos is not None:
        # Best-effort: TodoWrite snapshots carry the whole list each call, with no stable ids.
        return [
            {"id": str(i), "subject": t.get("content") or t.get("subject") or "(untitled)",
             "status": t.get("status", "pending")}
            for i, t in enumerate(last_todos, 1) if isinstance(t, dict)
        ]
    return []


def build_tasks_markdown(tasks):
    """Render the session task list as a table with a totals line, or '' if there were none."""
    if not tasks:
        return ""
    lines = ["## Task List", "", "| ID | Task | Status |", "|----|------|--------|"]
    completed = 0
    for t in tasks:
        subject = str(t["subject"]).replace("|", "\\|")
        if t["status"] == "completed":
            completed += 1
        lines.append(f"| {t['id']} | {subject} | {t['status']} |")
    lines += ["", f"_{len(tasks)} tasks, {completed} completed._"]
    return "\n".join(lines)


def extract_prompts(records):
    """Genuine human-typed prompts, in order, verbatim (system-reminders stripped)."""
    prompts = []
    for r in records:
        # isMeta is True or absent in practice; any falsy value (absent/False) is treated as not-meta
        if r.get("type") != "user" or r.get("isMeta"):
            continue
        text = _prompt_text(r.get("message", {}).get("content"))
        if text is not None:
            prompts.append(text)
    return prompts


def locate_transcript():
    """Resolve (session_id, transcript_path) for the current session, or exit with a clear error."""
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        sys.exit("error: CLAUDE_CODE_SESSION_ID is not set; cannot locate the session transcript")
    # Claude Code encodes cwd as /path/to/dir -> -path-to-dir (each '/' -> '-').
    # Lossy for paths containing '-', but matches Claude Code's actual directory naming.
    encoded = os.getcwd().replace("/", "-")
    path = Path.home() / ".claude" / "projects" / encoded / f"{session_id}.jsonl"
    if not path.is_file():
        sys.exit(f"error: transcript not found at {path}")
    return session_id, path


def _git_branch():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def build_prompts_markdown(prompts):
    """Render the verbatim prompts section. Prompt text is emitted untruncated and unmodified."""
    if not prompts:
        return "## Prompts (chronological)\n\n_No typed prompts found in this session._\n"
    lines = ["## Prompts (chronological)", ""]
    for i, p in enumerate(prompts, 1):
        lines += [f"### Prompt {i}", "", p, ""]
    return "\n".join(lines)


def render_metadata_yaml(meta):
    """Render the deterministic metadata fields as a YAML block, fixed key order."""
    lines = [
        f"session_id: {meta['session_id']}",
        f"date: {meta['date']}",
        f"cwd: {meta['cwd']}",
        f"git_branch: {meta['git_branch'] if meta['git_branch'] is not None else 'null'}",
        f"prompt_count: {meta['prompt_count']}",
    ]
    tools = meta["tools_used"]
    if tools:
        lines.append("tools_used:")
        lines += [f"  {name}: {count}" for name, count in tools.items()]
    else:
        lines.append("tools_used: {}")
    files = meta["files_touched"]
    if files:
        lines.append("files_touched:")
        lines += [f"  - {f}" for f in files]
    else:
        lines.append("files_touched: []")
    return "\n".join(lines)


def assemble_document(slug, summary, prompts_markdown, meta, handoff_text,
                      agents_markdown="", tasks_markdown=""):
    """Build the complete session-log markdown. prompts_markdown is spliced byte-exact."""
    parts = [
        f"# Session Log — {meta['date']} — {slug}",
        "",
        "## Summary",
        "",
        summary.strip(),
        "",
        prompts_markdown.rstrip("\n"),
        "",
    ]
    if tasks_markdown.strip():
        parts += [tasks_markdown.rstrip("\n"), ""]
    if agents_markdown.strip():
        parts += [agents_markdown.rstrip("\n"), ""]
    parts += [
        "## Handoff State",
        "",
        "```yaml",
        render_metadata_yaml(meta),
        handoff_text.strip(),
        "```",
    ]
    return "\n".join(parts) + "\n"


def resolve_output_path(slug, date, base_dir=Path("docs/session-logs")):
    """Dated path under base_dir, with a numeric suffix on same-day-same-slug collision."""
    base = Path(base_dir)
    candidate = base / f"{date}-{slug}.md"
    n = 2
    while candidate.exists():
        candidate = base / f"{date}-{slug}-{n}.md"
        n += 1
    return candidate


def load_session():
    """Locate the current transcript and return (prompts_markdown, metadata)."""
    session_id, path = locate_transcript()
    try:
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except json.JSONDecodeError as e:
        sys.exit(f"error: malformed JSONL in transcript: {e}")
    prompts = extract_prompts(records)
    agents = extract_agents(records)
    tasks = extract_tasks(records)
    meta = build_metadata(records)
    meta.update({
        "session_id": session_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "cwd": tilde(os.getcwd()),
        "git_branch": _git_branch(),
        "prompt_count": len(prompts),
    })
    return (build_prompts_markdown(prompts), build_agents_markdown(agents),
            build_tasks_markdown(tasks), meta)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extract session prompts/metadata as JSON, or assemble the full log file."
    )
    parser.add_argument("--assemble", action="store_true",
                        help="Write the full session-log file instead of emitting JSON.")
    parser.add_argument("--slug", help="kebab-case slug for the filename and title (with --assemble).")
    parser.add_argument("--summary-file", help="File holding the model-written summary prose.")
    parser.add_argument("--handoff-file", help="File holding the model-written handoff YAML fields.")
    parser.add_argument("--out", help="Explicit output path (overrides docs/session-logs/<date>-<slug>.md).")
    args = parser.parse_args(argv)

    prompts_markdown, agents_markdown, tasks_markdown, meta = load_session()

    if not args.assemble:
        print(json.dumps({
            "prompts_markdown": prompts_markdown,
            "agents_markdown": agents_markdown,
            "tasks_markdown": tasks_markdown,
            "metadata": meta,
        }, indent=2))
        return

    missing = [flag for flag, value in (
        ("--slug", args.slug),
        ("--summary-file", args.summary_file),
        ("--handoff-file", args.handoff_file),
    ) if not value]
    if missing:
        sys.exit(f"error: --assemble requires {', '.join(missing)}")

    summary = Path(args.summary_file).read_text()
    handoff_text = Path(args.handoff_file).read_text()
    doc = assemble_document(args.slug, summary, prompts_markdown, meta, handoff_text,
                            agents_markdown, tasks_markdown)
    out = Path(args.out) if args.out else resolve_output_path(args.slug, meta["date"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc)
    print(out)


if __name__ == "__main__":
    main()
