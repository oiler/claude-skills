#!/usr/bin/env python3
"""orko-review helper: preflight, run setup, report checks, dispositions, and the summary.

Standard library only (Python 3.10+). SKILL.md says when each subcommand runs.
"""
from __future__ import annotations

import argparse
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

    if opts["run"] is not None:
        if "--apply" not in flags:
            problems.append(f"--run needs --apply; {USAGE}")
        if positionals:
            problems.append(f"--run takes no doc path; {USAGE}")
        if "--file-only" in flags:
            problems.append("--run applies an earlier file-only run; it can't be combined with --file-only")
        if not problems:
            out += resume((cwd / Path(opts["run"]).expanduser()).resolve(), problems)
        return finish(out, problems, hints)

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
    hints: list[str] = []
    res = None
    if not problems:
        res, r_problems, hints = resolve(opts["doc"], opts["spec"], cwd)
        problems += r_problems + validate_extras(extras)
    run = None
    if not problems:
        run = res.reviews / res.doc.stem / (now or datetime.now()).strftime(RUN_STAMP)
        if run.exists():
            problems.append(f"run directory already exists: {run}")
    if problems:
        print("\n".join([f"problem: {p}" for p in problems] + [f"hint: {h}" for h in hints]))
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


SEVERITIES = ("blocker", "major", "minor", "nit")
VERDICTS = ("ready", "ready with changes", "not ready")
BULLETS = ("Where", "Evidence", "Problem", "Fix")
SECTIONS = ("## Verdict", "## Findings", "## Checked and sound")
FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FINDING_RE = re.compile(r"^### F-(\d+) \[([^\]]*)\] (\S.*)$")
BULLET_RE = re.compile(r"^- (Where|Evidence|Problem|Fix):(.*)$")


def parse_findings(block: list[str]) -> tuple[list[dict], list[str]]:
    content = [line for line in block if line.strip()]
    if not any(line.startswith("### ") for line in content):
        if [line.strip() for line in content] == ["None."]:
            return [], []
        return [], ["'## Findings' must hold 'None.' or at least one '### F-<n> [<severity>] <title>'"]
    if any(line.strip() == "None." for line in content):
        return [], ["'None.' can't sit alongside findings"]
    findings: list[dict] = []
    errors: list[str] = []
    current: dict | None = None
    for line in content:
        if line.startswith("### "):
            match = FINDING_RE.match(line.rstrip())
            if not match:
                errors.append(f"malformed finding heading: {line.strip()!r}")
                current = None
                continue
            current = {"n": int(match.group(1)), "severity": match.group(2),
                       "title": match.group(3).strip(), "bullets": []}
            findings.append(current)
        elif current is not None:
            bullet = BULLET_RE.match(line)
            if bullet:
                current["bullets"].append((bullet.group(1), bullet.group(2).strip()))
    for position, finding in enumerate(findings, 1):
        tag = f"F-{finding['n']}"
        if finding["n"] != position:
            errors.append(f"finding IDs must run F-1 to F-{len(findings)} without gaps; "
                          f"found {tag} at position {position}")
        if finding["severity"] not in SEVERITIES:
            errors.append(f"{tag} severity {finding['severity']!r} is not one of {', '.join(SEVERITIES)}")
        labels = [label for label, _ in finding["bullets"]]
        if labels != list(BULLETS):
            errors.append(f"{tag} needs the bullets Where, Evidence, Problem, Fix in that order; "
                          f"found {', '.join(labels) or 'none'}")
        elif not all(value for _, value in finding["bullets"]):
            errors.append(f"{tag} has an empty bullet")
    return [{k: f[k] for k in ("n", "severity", "title")} for f in findings], errors


def parse_report(text: str, lens: str, doc: str) -> tuple[list[dict], list[str]]:
    """(findings, errors) for one report; the findings mean something only when errors is empty."""
    text = text.replace("\r\n", "\n")
    front = FRONT_RE.match(text)
    if not front:
        return [], ["front matter missing: the report must open with a --- block holding lens and doc"]
    errors: list[str] = []
    fields = dict(FIELD_RE.findall(front.group(1)))
    if sorted(fields) != ["doc", "lens"]:
        errors.append(f"front matter keys are {sorted(fields)}, expected exactly doc and lens")
    if fields.get("lens") != lens:
        errors.append(f"lens is {fields.get('lens')!r}, expected {lens!r}")
    if fields.get("doc") != doc:
        errors.append(f"doc is {fields.get('doc')!r}, expected {doc!r}")
    lines = text[front.end():].splitlines()
    starts: list[int] = []
    for heading in SECTIONS:
        hits = [i for i, line in enumerate(lines) if line.rstrip() == heading]
        if len(hits) != 1:
            errors.append(f"{heading!r} appears {len(hits)} times, expected once")
        starts.append(hits[0] if len(hits) == 1 else -1)
    if -1 in starts:
        return [], errors
    if not starts[0] < starts[1] < starts[2]:
        return [], errors + ["sections must be in the order Verdict, Findings, Checked and sound"]
    verdict = next((line.strip() for line in lines[starts[0] + 1:starts[1]] if line.strip()), "")
    if verdict not in VERDICTS:
        errors.append(f"verdict {verdict!r} is not one of {', '.join(VERDICTS)}")
    findings, finding_errors = parse_findings(lines[starts[1] + 1:starts[2]])
    errors += finding_errors
    if not any(line.startswith("- ") for line in lines[starts[2] + 1:]):
        errors.append("'## Checked and sound' needs at least one bullet")
    return findings, errors


def cell(text: str) -> str:
    return one_line(text).replace("|", r"\|")


def table(header: str, rows: list[str]) -> list[str]:
    if not rows:
        return ["None."]
    return [header, "|" + "---|" * (header.count("|") - 1), *rows]


def index_table(index: list[dict]) -> list[str]:
    return table("| ID | Severity | Title |",
                 [f"| {e['id']} | {e['severity']} | {cell(e['title'])} |" for e in index])


def open_run(run_arg: str) -> tuple[Path, dict | None]:
    run = Path(run_arg).expanduser().resolve()
    manifest = load_manifest(run)
    if manifest is None:
        print(f"problem: no readable run.json in {run}")
    return run, manifest


def cmd_check(args: argparse.Namespace) -> int:
    run, manifest = open_run(args.run)
    if manifest is None:
        return 2
    doc = Path(manifest["doc"])
    if not doc.is_file() or sha256(doc) != manifest["doc_sha256"]:
        # The reviews may describe a different text, so nothing else runs.
        print(f"problem: doc changed since start (original: {run / 'doc.orig.md'})\nSTATUS: blocked")
        return 3
    lenses = manifest["lenses"]
    retries: list[str] = []
    entries: list[dict] = []
    for lens in lenses:
        if manifest["status"][lens] == "failed":
            continue
        report = run / f"{lens}.md"
        if report.is_file():
            findings, errors = parse_report(read_text(report), lens, manifest["doc"])
        else:
            findings, errors = [], ["report missing"]
        if not errors:
            manifest["status"][lens] = "valid"
            entries += [{"id": f"{lens}/F-{f['n']}", "lens": lens, **f} for f in findings]
            continue
        attempts = manifest["attempts"].get(lens, 0) + 1
        manifest["attempts"][lens] = attempts
        manifest["failures"][lens] = "; ".join(errors)
        if report.is_file():
            # A retry starts from an empty path, so the new reviewer can't read its predecessor.
            report.rename(run / f"{lens}.invalid-{attempts}.md")
        if attempts >= 2:
            manifest["status"][lens] = "failed"
        else:
            manifest["status"][lens] = "retry"
            retries.append(f"retry: {lens} — {manifest['failures'][lens]}")
    failed = [lens for lens in lenses if manifest["status"][lens] == "failed"]
    if retries:
        write_manifest(run, manifest)
        print("\n".join(retries))
        return 2
    if len(failed) == len(lenses):
        write_manifest(run, manifest)
        print("problem: no valid reports\nSTATUS: blocked")
        return 3
    entries.sort(key=lambda e: (SEVERITIES.index(e["severity"]), lenses.index(e["lens"]), e["n"]))
    manifest["index"] = entries
    write_manifest(run, manifest)
    lines = index_table(entries)
    if failed:
        lines.append(f"failed-lenses: {', '.join(failed)}")
    print("\n".join(lines))
    return 0


VERDICT_CHOICES = ("accept", "reject", "defer")
RECOMMENDED_SLOT = "<!-- orchestrator: at most 3 items, only ones that change what oiler does next -->"


def render_decisions(manifest: dict) -> str:
    rows = [f"| {e['id']} | {e['severity']} | {cell(e['title'])} | {d['verdict']} | {cell(d['why'])} |"
            for e in manifest["index"] if (d := manifest["dispositions"].get(e["id"]))]
    return "\n".join([f"# Decisions — {Path(manifest['doc']).name}", "",
                      *table("| ID | Severity | Title | Verdict | Why |", rows)]) + "\n"


def cmd_decide(args: argparse.Namespace) -> int:
    run, manifest = open_run(args.run)
    if manifest is None:
        return 2
    # The stored index, never a re-check: the session edits the doc between decide calls.
    problem = None
    why = one_line(args.why)
    if manifest.get("index") is None:
        problem = "no findings index; run check first"
    elif manifest["mode"] != "apply":
        problem = "this is a file-only run; apply it with /orko-review --run <run-dir> --apply"
    elif args.finding not in {e["id"] for e in manifest["index"]}:
        problem = f"{args.finding} is not in the findings index"
    elif not why:
        problem = "--why is empty"
    if problem:
        print(f"problem: {problem}")
        return 2
    manifest["dispositions"][args.finding] = {"verdict": args.verdict, "why": why}
    write_manifest(run, manifest)
    (run / "decisions.md").write_text(render_decisions(manifest), encoding="utf-8")
    print(f"recorded: {args.finding} {args.verdict}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    run, manifest = open_run(args.run)
    if manifest is None:
        return 2
    index = manifest.get("index")
    if index is None:
        print("problem: no findings index; run check first")
        return 2
    decided = manifest["dispositions"]
    if manifest["mode"] == "apply":
        missing = [e["id"] for e in index if e["id"] not in decided]
        if missing:
            print(f"problem: undecided: {', '.join(missing)}")
            return 2
    lenses = manifest["lenses"]
    failed = [lens for lens in lenses if manifest["status"][lens] == "failed"]
    out = ["## Reviewed",
           f"{manifest['doc']} — {manifest['type']} — {len(lenses)} lenses ({', '.join(lenses)}) — run {run}",
           *(f"Specialist: {name} — {why}" for name, why in manifest["extras"].items())]
    if manifest["mode"] == "file-only":
        out += ["## Findings", *index_table(index)]
        if failed:
            out.append(f"failed-lenses: {', '.join(failed)}")
        out.append(f"Apply later: /orko-review --run {run} --apply")
    else:
        def rows(verdict: str) -> list[str]:
            return [f"| {e['id']} | {e['severity']} | {cell(e['title'])} | {cell(decided[e['id']]['why'])} |"
                    for e in index if decided[e["id"]]["verdict"] == verdict]
        needs = rows("defer") + [f"| {lens}/— | — | lens failed twice | {cell(manifest['failures'].get(lens, ''))} |"
                                 for lens in failed]
        out += ["## Accepted", *table("| ID | Severity | Title | Change |", rows("accept")),
                "## Rejected", *table("| ID | Severity | Title | Why |", rows("reject")),
                "## Needs you", *table("| ID | Severity | Title | Why |", needs),
                "## Recommended", RECOMMENDED_SLOT]
    print("\n".join(out))
    return 0


def resume(run: Path, problems: list[str]) -> list[str]:
    """Flip an earlier file-only run to apply, so the session can enter at the apply step."""
    manifest = load_manifest(run)
    if manifest is None:
        problems.append(f"no readable run.json in {run}")
        return []
    if manifest["mode"] != "file-only":
        problems.append(f"run is in {manifest['mode']} mode; only a file-only run can be applied later")
    if manifest.get("index") is None:
        problems.append("run has no stored findings index; its check never passed")
    doc = Path(manifest["doc"])
    if not doc.is_file() or sha256(doc) != manifest["doc_sha256"]:
        problems.append(f"doc changed since the run started (original: {run / 'doc.orig.md'})")
    if problems:
        return []
    manifest["mode"] = "apply"
    write_manifest(run, manifest)
    return [f"doc: {doc}", f"resume: {run}", *index_table(manifest["index"])]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orko_review.py", description="orko-review helper")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="validate every report and store the findings index")
    check.add_argument("--run", required=True)
    check.set_defaults(func=cmd_check)
    decide = sub.add_parser("decide", help="record one finding's disposition")
    decide.add_argument("--run", required=True)
    decide.add_argument("--finding", required=True, help="<lens>/F-<n>")
    decide.add_argument("--verdict", required=True, choices=VERDICT_CHOICES)
    decide.add_argument("--why", required=True)
    decide.set_defaults(func=cmd_decide)
    summary = sub.add_parser("summary", help="render the run's summary")
    summary.add_argument("--run", required=True)
    summary.set_defaults(func=cmd_summary)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["preflight"]:
        return cmd_preflight(argv[1:])
    if argv[:1] == ["start"]:
        return cmd_start(argv[1:])
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
