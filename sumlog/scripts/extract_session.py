# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Extract verbatim typed prompts and metadata from the current Claude Code session transcript."""

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
                if fp and fp not in files:
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


def main():
    session_id, path = locate_transcript()
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    prompts = extract_prompts(records)
    meta = build_metadata(records)
    meta.update({
        "session_id": session_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "cwd": os.getcwd(),
        "git_branch": _git_branch(),
        "prompt_count": len(prompts),
    })
    print(json.dumps(
        {"prompts_markdown": build_prompts_markdown(prompts), "metadata": meta},
        indent=2,
    ))


if __name__ == "__main__":
    main()
