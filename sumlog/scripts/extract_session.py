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


def assemble_document(slug, summary, prompts_markdown, meta, handoff_text):
    """Build the complete session-log markdown. prompts_markdown is spliced byte-exact."""
    return (
        f"# Session Log — {meta['date']} — {slug}\n\n"
        f"## Summary\n\n{summary.strip()}\n\n"
        f"{prompts_markdown.rstrip(chr(10))}\n\n"
        f"## Handoff State\n\n"
        f"```yaml\n{render_metadata_yaml(meta)}\n{handoff_text.strip()}\n```\n"
    )


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
    meta = build_metadata(records)
    meta.update({
        "session_id": session_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "cwd": tilde(os.getcwd()),
        "git_branch": _git_branch(),
        "prompt_count": len(prompts),
    })
    return build_prompts_markdown(prompts), meta


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

    prompts_markdown, meta = load_session()

    if not args.assemble:
        print(json.dumps({"prompts_markdown": prompts_markdown, "metadata": meta}, indent=2))
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
    doc = assemble_document(args.slug, summary, prompts_markdown, meta, handoff_text)
    out = Path(args.out) if args.out else resolve_output_path(args.slug, meta["date"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc)
    print(out)


if __name__ == "__main__":
    main()
