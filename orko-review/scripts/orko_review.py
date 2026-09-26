#!/usr/bin/env python3
"""orko-review helper: preflight, run setup, report checks, dispositions, and the summary.

Standard library only (Python 3.10+). SKILL.md says when each subcommand runs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
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


EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max")
MODE_FLAGS = ("--apply", "--file-only")
VALUE_OPTIONS = ("--effort", "--spec", "--run")
AGENT_NAME = "orko-review-reviewer"
AGENT_INSTALL = "ln -s ~/files/repo/claude-skills/orko-review/agents ~/.claude/agents/orko-review"
USAGE = "usage: /orko-review <doc-path> [--apply | --file-only]  or  /orko-review --run <run-dir> --apply"


@dataclass
class Resolution:
    doc: Path
    root: Path
    doc_type: str
    rule: str
    spec: Path | None
    lenses: tuple[str, ...]
    evergreen: list[Path]
    reviews: Path


def resolve(doc_arg: str, spec_arg: str | None, cwd: Path) -> tuple[Resolution | None, list[str], list[str]]:
    """Everything about the doc that preflight and start share: (resolution, problems, hints)."""
    doc = (cwd / Path(doc_arg).expanduser()).resolve()
    if not doc.is_file():
        return None, [f"doc not found: {doc}"], []
    if doc.suffix != ".md":
        return None, [f"not a Markdown doc: {doc}"], []
    root = repo_root(doc)
    doc_type, rule = detect_type(doc)
    problems: list[str] = []
    hints: list[str] = []
    spec = None
    if spec_arg is not None:
        if doc_type != "plan":
            problems.append("--spec applies only to plans")
        else:
            spec = (cwd / Path(spec_arg).expanduser()).resolve()
            if not spec.is_file():
                problems.append(f"spec not found: {spec}")
    elif doc_type == "plan":
        spec = resolve_spec(doc, root)
        if spec is None:
            problems.append("the plan's **Spec:** line is missing or doesn't resolve to a file")
            hints.append("pass --spec <path>")
    res = Resolution(doc, root, doc_type, rule, spec, CORE_LENSES[doc_type],
                     evergreen_docs(root), reviews_dir(doc, root))
    return res, problems, hints


def parse_preflight_args(argv: list[str]) -> tuple[dict[str, str | None], list[str], list[str], list[str]]:
    """Raw parsing: argparse exits 2 on an unknown flag, and preflight must always exit 0."""
    opts: dict[str, str | None] = {"effort": None, "spec": None, "run": None}
    flags: list[str] = []
    positionals: list[str] = []
    problems: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in VALUE_OPTIONS:
            if i + 1 < len(argv):
                opts[arg[2:]] = argv[i + 1]
            else:
                problems.append(f"{arg} needs a value")
            i += 2
            continue
        (flags if arg.startswith("--") else positionals).append(arg)
        i += 1
    return opts, flags, positionals, problems


def effort_lines(value: str | None, mode: str) -> tuple[list[str], list[str], list[str]]:
    if value not in EFFORT_ORDER:
        return (["effort: unknown",
                 "warning: session effort unknown; MODELS.md raises the session to high for spec and plan work"],
                [], [])
    out = [f"effort: {value}"]
    if EFFORT_ORDER.index(value) >= EFFORT_ORDER.index("high"):
        return out, [], []
    if mode == "apply":
        return (out,
                [f"session effort is {value}; --apply is a verification pass, which MODELS.md raises to high"],
                ["run /effort high, then rerun"])
    out.append(f"warning: session effort is {value}; MODELS.md raises the session to high for spec and plan work")
    return out, [], []


def agent_dirs(home: Path, cwd: Path) -> list[Path]:
    """Each .claude/agents from the cwd up to the cwd's repository root (closest first), then ~/.claude/agents.

    Matches Claude Code's precedence: project-level definitions shadow user-level ones.
    """
    start = cwd.resolve()
    top = git_out(start, "rev-parse", "--show-toplevel")
    stop = Path(top).resolve() if top else start
    dirs: list[Path] = []
    for directory in (start, *start.parents):
        dirs.append(directory / ".claude" / "agents")
        if directory == stop:
            break
    dirs.append(home / ".claude" / "agents")
    return dirs


def reviewer_effort(dirs: list[Path]) -> str | None:
    """The reviewer agent's effort field ('' if unset), or None if no agent file is found.

    Scans as Claude Code does: recursively, following symlinks, with loop protection.
    """
    seen: set[str] = set()
    for root in dirs:
        for dirpath, subdirs, files in os.walk(root, followlinks=True):
            real = os.path.realpath(dirpath)
            if real in seen:
                subdirs[:] = []
                continue
            seen.add(real)
            for name in files:
                if not name.endswith(".md"):
                    continue
                try:
                    text = (Path(dirpath) / name).read_text(encoding="utf-8")
                except OSError:
                    continue
                if not text.startswith("---\n"):
                    continue
                fields = dict(FIELD_RE.findall(text[4:].split("\n---", 1)[0]))
                if fields.get("name") == AGENT_NAME:
                    return fields.get("effort", "")
    return None


def finish(out: list[str], problems: list[str], hints: list[str]) -> list[str]:
    return (out + [f"problem: {p}" for p in problems] + [f"hint: {h}" for h in hints]
            + ["STATUS: blocked" if problems else "STATUS: ok"])


def preflight_lines(argv: list[str], home: Path, cwd: Path) -> list[str]:
    opts, flags, positionals, problems = parse_preflight_args(argv)
    hints: list[str] = []
    unknown = [f for f in flags if f not in MODE_FLAGS]
    if unknown:
        problems.append(f"unknown flag(s): {' '.join(unknown)}; {USAGE}")
    if "--apply" in flags and "--file-only" in flags:
        problems.append(f"--apply and --file-only together; {USAGE}")
    mode = "file-only" if "--file-only" in flags else "apply"
    out = [f"mode: {mode}"]
    e_out, e_problems, e_hints = effort_lines(opts["effort"], mode)
    out += e_out
    problems += e_problems
    hints += e_hints

    if len(positionals) != 1:
        problems.append(f"expected one doc path, got {len(positionals)} "
                        f"(wrap a path with spaces in quotes); {USAGE}")
    else:
        res, r_problems, r_hints = resolve(positionals[0], opts["spec"], cwd)
        problems += r_problems
        hints += r_hints
        if res is not None:
            out += [f"doc: {res.doc}", f"type: {res.doc_type} ({res.rule})"]
            if res.spec is not None:
                out.append(f"spec: {res.spec}")
            out += [f"lenses: {', '.join(res.lenses)}",
                    f"extras-available: {', '.join(EXTRA_LENSES)}",
                    f"evergreen: {', '.join(map(str, res.evergreen)) or 'none'}",
                    f"reviews-dir: {res.reviews}"]

    effort = reviewer_effort(agent_dirs(home, cwd))
    if effort is None:
        out.append("agent: missing")
        problems.append(f"{AGENT_NAME} agent not found")
        hints.append(f"install with: {AGENT_INSTALL}")
    elif effort != "high":
        out.append(f"agent: {AGENT_NAME} (effort {effort or 'unset'})")
        problems.append(f"{AGENT_NAME} must pin effort: high")
    else:
        out.append(f"agent: {AGENT_NAME}")
    return finish(out, problems, hints)


def cmd_preflight(argv: list[str]) -> int:
    try:
        lines = preflight_lines(argv, Path.home(), Path.cwd())
    except Exception as exc:  # the injection aborts the whole invocation on a nonzero exit
        lines = [f"problem: preflight crashed: {exc!r}", "STATUS: blocked"]
    print("\n".join(lines))
    return 0


RUN_STAMP = "%Y-%m-%d-%H%M%S"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(run: Path, manifest: dict) -> None:
    (run / "run.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def load_manifest(run: Path) -> dict | None:
    try:
        return json.loads((run / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def render_brief(lens: str, res: Resolution, run: Path) -> str:
    lines = ["# Review brief: " + lens, "", "## Paths", "",
             f"- Lens: {lens}", f"- Document under review: {res.doc}"]
    if res.spec is not None:
        lines.append(f"- Spec: {res.spec}")
    lines += [f"- Evergreen docs: {', '.join(map(str, res.evergreen)) or 'none'}",
              f"- Reviews directory (off limits except your report): {res.reviews}",
              f"- Write your report to: {run / f'{lens}.md'}", ""]
    return ("\n".join(lines) + "\n" + read_text(lens_file(res.doc_type, lens)) + "\n"
            + read_text(CONTRACT_PATH))


def dispatch_prompt(brief: Path) -> str:
    return f"Read {brief} and follow it."


def parse_start_args(argv: list[str]) -> tuple[dict[str, str | None], list[tuple[str, str]], list[str]]:
    """Each --extra must be followed immediately by its --why, so the pairing can't be ambiguous."""
    opts: dict[str, str | None] = {"doc": None, "mode": None, "spec": None}
    extras: list[tuple[str, str]] = []
    problems: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--extra":
            if i + 3 < len(argv) and argv[i + 2] == "--why":
                extras.append((argv[i + 1], argv[i + 3]))
                i += 4
                continue
            problems.append("each --extra <lens> must be followed immediately by --why <reason>")
            break
        if arg in ("--doc", "--mode", "--spec") and i + 1 < len(argv):
            opts[arg[2:]] = argv[i + 1]
            i += 2
            continue
        problems.append(f"unexpected argument: {arg}")
        break
    if opts["doc"] is None:
        problems.append("--doc is required")
    if opts["mode"] not in ("apply", "file-only"):
        problems.append("--mode must be apply or file-only")
    return opts, extras, problems


def validate_extras(extras: list[tuple[str, str]]) -> list[str]:
    names = [name for name, _ in extras]
    problems = [f"unknown specialist lens: {n} (catalog: {', '.join(EXTRA_LENSES)})"
                for n in names if n not in EXTRA_LENSES]
    if len(set(names)) != len(names):
        problems.append("a specialist lens is listed twice")
    if len(names) > MAX_EXTRAS:
        problems.append(f"at most {MAX_EXTRAS} specialist lenses")
    problems += [f"--why for {n} is empty" for n, why in extras if not one_line(why)]
    return problems


def cmd_start(argv: list[str], cwd: Path | None = None, now: datetime | None = None) -> int:
    cwd = cwd or Path.cwd()
    opts, extras, problems = parse_start_args(argv)
    res = None
    if not problems:
        res, r_problems, _hints = resolve(opts["doc"], opts["spec"], cwd)
        problems += r_problems + validate_extras(extras)
    run = None
    if not problems:
        run = res.reviews / res.doc.stem / (now or datetime.now()).strftime(RUN_STAMP)
        if run.exists():
            problems.append(f"run directory already exists: {run}")
    if problems:
        print("\n".join(f"problem: {p}" for p in problems))
        return 2
    (run / "briefs").mkdir(parents=True)
    shutil.copyfile(res.doc, run / "doc.orig.md")
    lenses = [*res.lenses, *(name for name, _ in extras)]
    write_manifest(run, {
        "doc": str(res.doc), "doc_sha256": sha256(res.doc), "type": res.doc_type,
        "spec": str(res.spec) if res.spec else None, "mode": opts["mode"], "lenses": lenses,
        "extras": {name: one_line(why) for name, why in extras},
        "evergreen": [str(p) for p in res.evergreen], "reviews_dir": str(res.reviews),
        "status": {lens: "pending" for lens in lenses}, "attempts": {}, "failures": {},
        "index": None, "dispositions": {},
    })
    print(f"run: {run}")
    for lens in lenses:
        brief = run / "briefs" / f"{lens}.md"
        brief.write_text(render_brief(lens, res, run), encoding="utf-8")
        print(f"{lens}: {dispatch_prompt(brief)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["preflight"]:
        return cmd_preflight(argv[1:])
    if argv[:1] == ["start"]:
        return cmd_start(argv[1:])
    print(f"usage: orko_review.py {{{','.join(SUBCOMMANDS)}}} ...", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
