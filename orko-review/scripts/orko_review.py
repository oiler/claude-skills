#!/usr/bin/env python3
"""orko-review helper: preflight, run setup, report checks, dispositions, and the summary.

Standard library only (Python 3.10+). SKILL.md says when each subcommand runs.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
LENS_DIR = SKILL_DIR / "references" / "lenses"
CONTRACT_PATH = SKILL_DIR / "references" / "reviewer-contract.md"
SUBCOMMANDS = ("preflight", "start", "check", "decide", "summary")
CORE_LENSES: dict[str, tuple[str, ...]] = {
    "spec": ("accuracy", "completeness", "design"),
    "plan": ("coverage", "executability", "verification"),
    "generic": ("accuracy", "consistency", "completeness"),
}
EXTRA_LENSES = ("security", "frontend", "data", "performance", "operations")
MAX_EXTRAS = 2
EVERGREEN_NAMES = ("CLAUDE.md", "AGENTS.md", "PROJECT.md", "OBJECTIVE.md", "DESIGN.md", "ARCHITECTURE.md")
TYPE_SCAN_LINES = 40
SPEC_LINE_RE = re.compile(r"^\s*(?:- )?\*\*Spec:\*\*(.*)$")
FIELD_RE = re.compile(r"^([\w-]+):[ \t]*(.*?)[ \t]*$", re.M)


def git_out(cwd: Path, *args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def repo_root(doc: Path) -> Path:
    """The doc's repository, not the cwd's; the doc's directory when it isn't in one."""
    top = git_out(doc.parent, "rev-parse", "--show-toplevel")
    return Path(top).resolve() if top else doc.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def one_line(text: str) -> str:
    return " ".join(text.split())


def spec_line_value(lines: Iterable[str]) -> str | None:
    """The value after the first line that starts with **Spec:** (a mid-line mention doesn't count)."""
    for line in lines:
        match = SPEC_LINE_RE.match(line)
        if match:
            return match.group(1)
    return None


def detect_type(doc: Path) -> tuple[str, str]:
    """(type, the rule that matched), first match wins."""
    if doc.parent.name == "specs":
        return "spec", "parent directory specs/"
    if doc.parent.name == "plans":
        return "plan", "parent directory plans/"
    if doc.name.endswith("-design.md"):
        return "spec", "filename *-design.md"
    if spec_line_value(read_text(doc).splitlines()[:TYPE_SCAN_LINES]) is not None:
        return "plan", "**Spec:** header line"
    return "generic", "no rule matched"


def spec_token(value: str) -> str | None:
    quoted = re.search(r"`([^`]+)`", value)
    if quoted:
        token = quoted.group(1).strip()
    else:
        parts = value.split()
        token = parts[0].rstrip(".,)") if parts else ""
    if not token or token.startswith("http"):
        return None
    return token


def resolve_spec(plan: Path, root: Path) -> Path | None:
    value = spec_line_value(read_text(plan).splitlines())
    token = spec_token(value) if value is not None else None
    if token is None:
        return None
    try:
        path = Path(token).expanduser()
        candidates = [path] if path.is_absolute() else [root / path, plan.parent / path]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
    except (RuntimeError, OSError):
        return None
    return None


def reviews_dir(doc: Path, root: Path) -> Path:
    for directory in doc.parents:
        if directory.name == "superpowers":
            return directory / "reviews"
        if directory == root:
            break
    if doc.parent.name in ("specs", "plans"):
        return doc.parent.parent / "reviews"
    return doc.parent / "reviews"


def evergreen_docs(root: Path) -> list[Path]:
    return [base / name for base in (root, root / "docs") for name in EVERGREEN_NAMES
            if (base / name).is_file()]


def lens_file(doc_type: str, lens: str) -> Path:
    prefix = "extra" if lens in EXTRA_LENSES else doc_type
    return LENS_DIR / f"{prefix}-{lens}.md"
