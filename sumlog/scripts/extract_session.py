# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Extract verbatim typed prompts and metadata from the current Claude Code session transcript."""

import re

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
