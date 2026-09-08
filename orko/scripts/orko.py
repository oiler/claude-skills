# orko.py — deterministic spine for the orko skill
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Owns every deterministic surface of an orko run: artifact paths, the run
ledger, artifact validation, and every dispatch prompt.

The model authors prose. This script owns structure. In particular the `prompt`
subcommand exists so the orchestrator dispatches reviewer text it cannot edit —
priming a reviewer with the authoring session's context turns a fresh critique
into an echo of the author.

Usage:
    uv run orko.py init {analysis|build} <topic> --workspace DIR --owner NAME
        --boundaries TEXT --trailer LINE [--trailer LINE] [--version V]
        [--executor claude|codex] [--codex-model M] [--codex-effort E]
        [--date YYYY-MM-DD]
    uv run orko.py ledger <step> <status> --slug SLUG [--commit SHA] [--workspace DIR]
    uv run orko.py status [<slug>] [--workspace DIR]
    uv run orko.py check tasks <path>
    uv run orko.py prompt {spec-review|plan-review} <slug> --lens NAME [--workspace DIR]
    uv run orko.py prompt plan-write <slug> [--workspace DIR]
    uv run orko.py prompt seat <slug> --seat NAME --question TEXT --context-file PATH [--workspace DIR]
    uv run orko.py prompt verifier <slug> --seat NAME [--question TEXT] --context-file PATH [--workspace DIR]
    uv run orko.py escalations <slug> [--workspace DIR]
    uv run orko.py preflight [--slug SLUG | --mode {analysis|build}] [--workspace DIR]

Exit codes: 0 success / all checks pass; 1 validation failures; 2 usage or IO error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

SLUG_MAX = 60

HEADER_TITLE = "# orko run"
HEADER_KEYS = ("mode", "topic", "slug", "date", "workspace", "version", "owner",
               "executor", "codex_model", "codex_effort", "boundaries", "trailers")
EXECUTORS = ("claude", "codex")
FRONTMATTER_FIELD_RE = r'^[ \t]*{key}:[ \t]*"?(?P<value>[^"\n]*)"?[ \t]*$'

# Steps per engagement type. Only `complete` advances a run; the names are what
# `status` prints so a resumed conductor knows where it is without the table.
MODES: dict[str, dict[int, str]] = {
    "analysis": {
        1: "open", 2: "propose", 3: "dispatch",
        4: "verify", 5: "synthesize", 6: "close",
    },
    "build": {
        0: "intake", 1: "spec", 2: "spec review", 3: "plan",
        4: "plan review", 5: "execute", 6: "code review", 7: "close",
    },
}

PLACEHOLDER_RE = re.compile(
    r"\b(?:TBD|TODO|FIXME|XXX)\b|<placeholder>|\[fill in\]", re.IGNORECASE
)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
# The ledger header is one line. A topic carrying a newline or any other control
# character writes a header no later command can parse, and the run is then
# unrecoverable without hand-editing the ledger.
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class Finding(NamedTuple):
    line: int
    message: str


def strip_code(text: str) -> str:
    """Blank fenced blocks and inline code spans, preserving line count.

    Every validator scan runs against this, structural checks included: a
    document that *documents* a marker in backticks does not *contain* one.
    """
    out: list[str] = []
    fence: str | None = None
    for line in text.split("\n"):
        stripped = line.lstrip()
        if fence is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            fence = stripped[:3]
            out.append("")
            continue
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            out.append("")
            continue
        out.append(INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line))
    return "\n".join(out)


PLAN_RED_FLAGS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"Similar to Task \d", re.IGNORECASE),
     "'Similar to Task N' — repeat the content; tasks are read out of order"),
    (re.compile(r"add appropriate error handling", re.IGNORECASE),
     "vague directive 'add appropriate error handling' — show the handling"),
    (re.compile(r"\badd validation\b", re.IGNORECASE),
     "vague directive 'add validation' — show the validation"),
    (re.compile(r"handle edge cases", re.IGNORECASE),
     "vague directive 'handle edge cases' — name the cases"),
    (re.compile(r"^\s*[-*]?\s*\[?[ x]?\]?\s*Write tests for the above\s*$",
                re.IGNORECASE | re.MULTILINE),
     "'Write tests for the above' without the actual test code"),
)

TASK_HEADING_RE = re.compile(r"^###\s+Task\s+\d+\s*:", re.MULTILINE)


def validate_plan(text: str) -> list[Finding]:
    scanned = strip_code(text)
    lines = scanned.split("\n")
    findings: list[Finding] = []

    for index, line in enumerate(lines, start=1):
        for match in PLACEHOLDER_RE.finditer(line):
            findings.append(Finding(index, f"placeholder marker {match.group(0)!r}"))
        for pattern, message in PLAN_RED_FLAGS:
            if pattern.search(line):
                findings.append(Finding(index, message))

    if not ("REQUIRED SUB-SKILL" in scanned
            and "subagent-driven-development" in scanned):
        findings.append(Finding(
            1, "missing the mandatory 'REQUIRED SUB-SKILL: ... "
               "superpowers:subagent-driven-development' header line"))

    if not re.search(r"^##\s+Global Constraints\s*$", scanned, re.MULTILINE):
        findings.append(Finding(1, "missing the '## Global Constraints' section"))

    task_starts = [
        (scanned[:match.start()].count("\n") + 1, match.start())
        for match in TASK_HEADING_RE.finditer(scanned)
    ]
    if not task_starts:
        findings.append(Finding(1, "no '### Task N:' task block found"))

    for position, (line_no, offset) in enumerate(task_starts):
        end = task_starts[position + 1][1] if position + 1 < len(task_starts) else len(scanned)
        block = scanned[offset:end]
        if "**Files:**" not in block:
            findings.append(Finding(line_no, "task block has no '**Files:**' subsection"))
        if not re.search(r"^\s*-\s*\[ \]\s*\*\*Step", block, re.MULTILINE):
            findings.append(Finding(line_no, "task block has no '- [ ] **Step' checkbox"))

    return sorted(findings)


def cmd_check_tasks(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {target}: {error}", file=sys.stderr)
        return 2
    findings = validate_plan(text)
    if not findings:
        print(f"OK: {target} passes the tasks validator")
        return 0
    for finding in findings:
        print(f"{target}:{finding.line}: {finding.message}")
    return 1


def slugify(topic: str) -> str:
    """Lowercase ASCII slug. Raises ValueError if nothing survives."""
    ascii_only = (
        unicodedata.normalize("NFKD", topic)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = "-".join(re.findall(r"[a-z0-9]+", ascii_only.lower()))
    if len(slug) > SLUG_MAX:
        # The slug is the branch name the run works on, so a cut landing
        # mid-word reads as a typo forever. Drop the partial word —
        # unless the first word alone overruns, where a hard cut is all there is.
        cut = slug[:SLUG_MAX]
        if slug[SLUG_MAX] != "-" and "-" in cut:
            cut = cut.rsplit("-", 1)[0]
        slug = cut
    slug = slug.strip("-")
    if not slug:
        raise ValueError(f"topic {topic!r} produced an empty slug")
    return slug


def is_git_repo(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    return result.returncode == 0 and Path(result.stdout.strip()) == path.resolve()


# Each condition is one finding, so a test can remove exactly one and see
# exactly one test go red (mutation rule in the spec's Testing section).
def validate_workspace(ws: Path) -> list[str]:
    findings: list[str] = []
    if not is_git_repo(ws / "docs"):
        findings.append("docs-not-a-repo")
    if not is_git_repo(ws / "code"):
        findings.append("code-not-a-repo")
    if not (ws / "docs" / "versions").is_dir():
        findings.append("versions-missing")
    if not (ws / "code" / "scripts" / "spec-check.sh").is_file():
        findings.append("spec-check-missing")
    return findings


def find_workspace(start: Path) -> Path | None:
    """Nearest ancestor holding docs/, code/, and .orko/. The workspace root
    is not a repository, so git cannot find it; the run directory can."""
    for candidate in (start.resolve(), *start.resolve().parents):
        if all((candidate / name).is_dir() for name in ("docs", "code", ".orko")):
            return candidate
    return None


def resolve_workspace(args: argparse.Namespace) -> Path | None:
    if getattr(args, "workspace", None):
        return Path(args.workspace).resolve()
    found = find_workspace(Path.cwd())
    if found is None:
        print(f"orko: no workspace found above {Path.cwd()}; pass --workspace",
              file=sys.stderr)
    return found


def read_frontmatter_field(path: Path, key: str) -> str | None:
    """First `key: value` line inside the leading --- block, quotes stripped."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    block = text.split("---", 2)[1]
    match = re.search(FRONTMATTER_FIELD_RE.format(key=re.escape(key)), block, re.MULTILINE)
    return match.group("value").strip() if match else None


def read_active_version(ws: Path) -> str | None:
    return read_frontmatter_field(ws / "docs" / "STATUS.md", "active_version")


def dossier_dir(ws: Path, version: str) -> Path:
    return ws / "docs" / "versions" / version


def dossier_status(ws: Path, version: str) -> str | None:
    return read_frontmatter_field(dossier_dir(ws, version) / "README.md", "status")


def compute_paths(ws: Path, slug: str, date: str) -> dict[str, str]:
    """Every path a run touches, derived from the workspace and slug alone.

    The run directory is scratch and the scaffold docs repository is the
    record, so artifacts need no date in their filename; stability for the
    validators and seats is all that matters.
    """
    run_dir = ws / ".orko" / slug
    return {
        "slug": slug, "date": date, "workspace": str(ws),
        "docs": str(ws / "docs"), "code": str(ws / "code"),
        "run_dir": str(run_dir),
        "ledger": str(run_dir / "progress.md"),
        "escalations": str(run_dir / "escalations.md"),
        "tasks": str(run_dir / "tasks.md"),
        "brief": str(run_dir / "brief.md"),
        "synthesis": str(run_dir / "synthesis.md"),
        "findings_dir": str(run_dir / "findings"),
        "context_dir": str(run_dir / "context"),
    }


def _header_line(fields: dict) -> str:
    return "header: " + json.dumps({key: fields.get(key) for key in HEADER_KEYS})


def _parse_header(ledger: Path) -> dict | None:
    """The run's header fields, or None when the ledger cannot supply them.

    Empty, truncated, short-of-a-key, and carrying a mode no MODES table knows
    are all unreadable rather than a crash: callers turn None into exit 2. The
    mode check is load-bearing — every caller indexes MODES with it.
    """
    if not ledger.exists():
        return None
    lines = ledger.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2 or lines[0] != HEADER_TITLE or not lines[1].startswith("header: "):
        return None
    try:
        fields = json.loads(lines[1].removeprefix("header: "))
    except json.JSONDecodeError:
        return None
    if fields.get("mode") not in MODES:
        return None
    return fields if set(HEADER_KEYS) <= set(fields) else None


def cmd_init(args: argparse.Namespace) -> int:
    ws = Path(args.workspace).resolve()
    findings = validate_workspace(ws)
    if findings:
        for finding in findings:
            print(f"workspace-invalid: {finding}", file=sys.stderr)
        return 2
    if CONTROL_RE.search(args.topic):
        print("orko: topic contains a control character", file=sys.stderr)
        return 2
    version = args.version or read_active_version(ws)
    if not version:
        print("orko: docs/STATUS.md has no active_version; pass --version", file=sys.stderr)
        return 2
    status = dossier_status(ws, version)
    if status not in ("active", "proposed"):
        print(f"orko: dossier {version} status is {status!r}; needs active or proposed",
              file=sys.stderr)
        return 2
    date = args.date or _dt.date.today().isoformat()
    try:
        slug = slugify(args.topic)
    except ValueError as error:
        print(f"orko: {error}", file=sys.stderr)
        return 2
    paths = compute_paths(ws, slug, date)
    ledger = Path(paths["ledger"])
    resumed = False
    if ledger.exists():
        existing = _parse_header(ledger)
        if existing is None:
            print(f"orko: unreadable ledger header in {ledger}", file=sys.stderr)
            return 2
        if existing["topic"] != args.topic or existing["mode"] != args.mode:
            print(f"orko: run {slug!r} exists as a {existing['mode']} run for "
                  f"{existing['topic']!r}; resume it with the same mode and topic",
                  file=sys.stderr)
            return 2
        resumed = True
        header = existing
        paths = compute_paths(ws, slug, existing["date"])
    else:
        header = dict(mode=args.mode, topic=args.topic, slug=slug, date=date,
                      workspace=str(ws), version=version, owner=args.owner,
                      executor=args.executor, codex_model=args.codex_model,
                      codex_effort=args.codex_effort, boundaries=args.boundaries,
                      trailers=list(args.trailer))
        ledger.parent.mkdir(parents=True, exist_ok=True)
        for key in ("findings_dir", "context_dir"):
            Path(paths[key]).mkdir(parents=True, exist_ok=True)
        ledger.write_text(f"{HEADER_TITLE}\n{_header_line(header)}\n", encoding="utf-8")
    payload = dict(paths, **header, resumed=resumed,
                   next_step=_next_step(ledger, header["mode"]))
    print(json.dumps(payload, indent=2))
    return 0


# A `--commit` value is a SHA or a SHA range. Anything with whitespace in it
# would write a ledger line LEDGER_LINE_RE cannot parse, silently losing the step.
COMMIT_RE = re.compile(r"[0-9a-f]{7,40}(\.\.[0-9a-f]{7,40})?")

# A ledger step is either a whole step of the mode's table or a `5.n` sub-step
# — one execute task under a codex executor. Sub-steps never advance the run.
STEP_RE = re.compile(r"^\d+(\.\d+)?$")
LEDGER_LINE_RE = re.compile(
    r"^step (?P<step>\d+(?:\.\d+)?) (?P<status>dispatched|complete|failed|escalated)"
    r"(?: commit=(?P<commit>\S+))?$"
)
RECORD_LINE_RE = re.compile(
    r"^record (?P<type>[a-z]+) (?P<role>[a-z-]+) (?P<id>[A-Z]+-\d{3}|-) (?P<path>\S+)$"
)
HASH_LINE_RE = re.compile(r"^hash (?P<path>\S+) (?P<sha>[0-9a-f]{64})$")
# Files a `record` command edited besides the record itself — index READMEs,
# STATUS.md, changelogs — so `commit` knows what else to stage.
TOUCHED_LINE_RE = re.compile(r"^touched (?P<path>\S+)$")


def append_ledger(ledger: Path, line: str) -> None:
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _ledger_lines(ledger: Path) -> list[str]:
    """Every ledger line after the two header lines, stripped."""
    if not ledger.exists():
        return []
    return [line.strip() for line in ledger.read_text(encoding="utf-8").splitlines()[2:]]


def _ledger_entries(ledger: Path) -> list[dict[str, str | None]]:
    """Parsed step records in order, header excluded. Unparseable lines are
    skipped: the ledger is append-only, so a malformed line is damage to
    inspect, never a reason to refuse to report the rest of the run."""
    entries: list[dict[str, str | None]] = []
    for line in _ledger_lines(ledger):
        match = LEDGER_LINE_RE.match(line)
        if match:
            entries.append(match.groupdict())
    return entries


def records(ledger: Path) -> list[dict[str, str]]:
    """Minted records in ledger order: spec, plan, findings, decisions."""
    return [match.groupdict() for line in _ledger_lines(ledger)
            if (match := RECORD_LINE_RE.match(line))]


def record_for(ledger: Path, type_: str, role: str) -> dict[str, str] | None:
    for entry in records(ledger):
        if entry["type"] == type_ and entry["role"] == role:
            return entry
    return None


def hashes(ledger: Path) -> dict[str, str]:
    """Path to its last recorded sha — a re-hash of the same path supersedes."""
    out: dict[str, str] = {}
    for line in _ledger_lines(ledger):
        match = HASH_LINE_RE.match(line)
        if match:
            out[match.group("path")] = match.group("sha")
    return out


def touched(ledger: Path) -> list[str]:
    seen: list[str] = []
    for line in _ledger_lines(ledger):
        match = TOUCHED_LINE_RE.match(line)
        if match and match.group("path") not in seen:
            seen.append(match.group("path"))
    return seen


def _next_step(ledger: Path, mode: str) -> int | None:
    """Lowest step of `mode` not recorded complete; None when the run is done.

    Only `complete` advances the run. `dispatched`, `escalated`, and `failed`
    are annotations that survive a compaction, and none of them may move the
    resume point — a dispatched-but-unreturned review has not happened yet.
    """
    done = {
        int(entry["step"])
        for entry in _ledger_entries(ledger)
        if entry["status"] == "complete" and "." not in entry["step"]
    }
    remaining = [step for step in sorted(MODES[mode]) if step not in done]
    return remaining[0] if remaining else None


def next_task(ledger: Path) -> int:
    """1 + the highest `5.n` recorded complete: the next execute task to dispatch."""
    done = [int(entry["step"].split(".")[1]) for entry in _ledger_entries(ledger)
            if entry["status"] == "complete" and entry["step"].startswith("5.")]
    return max(done, default=0) + 1


def _dispatched_base(entries: list[dict[str, str | None]],
                     step: int | None) -> str | None:
    """Base SHA of the most recent `dispatched` line for `step`.

    This is what makes the resume rule actionable: after a compaction between a
    reviewer's commit and its `complete` line, it is the only way to ask whether
    that review already happened without hand-parsing the ledger.
    """
    if step is None:
        return None
    for entry in reversed(entries):
        if entry["step"] == str(step) and entry["status"] == "dispatched":
            return entry["commit"]
    return None


def _run_dir_root(ws: Path) -> Path:
    return ws / ".orko"


def _describe_run(ws: Path, slug: str) -> dict | None:
    """Run summary for `slug`, or None when its ledger header is unreadable."""
    ledger = _run_dir_root(ws) / slug / "progress.md"
    header = _parse_header(ledger)
    if header is None:
        return None
    entries = _ledger_entries(ledger)
    next_step = _next_step(ledger, header["mode"])
    steps = MODES[header["mode"]]
    return dict(
        compute_paths(ws, slug, header["date"]),
        **header,
        next_step=next_step,
        # `is not None`: build starts at step 0, and a falsy test would report
        # the intake step as already done.
        next_step_name=steps.get(next_step) if next_step is not None else None,
        last_status=entries[-1]["status"] if entries else None,
        dispatched_base=_dispatched_base(entries, next_step),
        next_task=next_task(ledger),
        records=[dict(entry, sha=hashes(ledger).get(entry["path"]))
                 for entry in records(ledger)],
    )


def cmd_ledger(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args)
    if ws is None:
        return 2
    ledger = _run_dir_root(ws) / args.slug / "progress.md"
    header = _parse_header(ledger)
    if header is None:
        print(f"orko: no run named {args.slug!r}; run init first", file=sys.stderr)
        return 2
    if not STEP_RE.fullmatch(args.step):
        print(f"orko: step {args.step!r} must be a number or a sub-step like 5.1",
              file=sys.stderr)
        return 2
    if "." in args.step:
        # Sub-steps exist only for the execute step of a codex-executed build:
        # that is the one place orko dispatches a numbered series of tasks.
        if (header["mode"] != "build" or header["executor"] != "codex"
                or args.step.split(".")[0] != "5"):
            print(f"orko: sub-step {args.step} is only valid for step 5 of a "
                  "build run with --executor codex", file=sys.stderr)
            return 2
    elif int(args.step) not in MODES[header["mode"]]:
        valid = ", ".join(str(step) for step in sorted(MODES[header["mode"]]))
        print(f"orko: step {args.step} is not a step of a {header['mode']} run "
              f"(valid: {valid})", file=sys.stderr)
        return 2
    if args.commit and not COMMIT_RE.fullmatch(args.commit):
        print("orko: --commit must be a short or full SHA", file=sys.stderr)
        return 2
    line = f"step {args.step} {args.status}"
    if args.commit:
        line += f" commit={args.commit}"
    append_ledger(ledger, line)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args)
    if ws is None:
        return 2

    if args.slug:
        if not (_run_dir_root(ws) / args.slug / "progress.md").exists():
            print(f"orko: no run named {args.slug!r}", file=sys.stderr)
            return 2
        run = _describe_run(ws, args.slug)
        if run is None:
            print(f"orko: unreadable ledger header for run {args.slug!r}",
                  file=sys.stderr)
            return 2
        print(json.dumps(run, indent=2))
        return 0

    base = _run_dir_root(ws)
    slugs = sorted(
        child.name for child in base.iterdir() if (child / "progress.md").exists()
    ) if base.exists() else []
    runs = [_describe_run(ws, slug) for slug in slugs]
    print(json.dumps([run for run in runs if run is not None], indent=2))
    return 0


def references_dir() -> Path:
    """The skill's references/ directory, resolved through any symlink."""
    return Path(__file__).resolve().parent.parent / "references"


PROMPT_SOURCES = {
    "spec-review": "spec-reviewer.md",
    "plan-review": "plan-reviewer.md",
    "plan-write": "plan-writer.md",
    "seat": "seat-prompt.md",
    "verifier": "verifier-prompt.md",
}
REVIEW_KINDS = ("spec-review", "plan-review")
SEAT_KINDS = ("seat", "verifier")
LENS_ROW_RE = re.compile(r"^\|\s*([a-z][a-z0-9-]*)\s*\|\s*(.+?)\s*\|\s*$")


def _lenses(text: str) -> dict[str, str]:
    """Rows of the `## Lenses` table: name -> question. The table lives in the
    charter so the lens list is prose the conductor can read, and parsing it
    here keeps the script the only thing that assembles a dispatch."""
    lenses: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## Lenses":
            in_table = True
            continue
        if not in_table:
            continue
        match = LENS_ROW_RE.match(line)
        if not match or match.group(1) == "lens":
            continue
        if set(match.group(2)) <= {"-", " "}:
            continue
        lenses[match.group(1)] = match.group(2)
    return lenses


def _strip_lenses(text: str) -> str:
    """The dispatched prompt carries one lens, not the menu. `## Lenses` must be
    the last section of a review charter: everything from it on is dropped."""
    head, _, _ = text.partition("\n## Lenses")
    return head.rstrip() + "\n"


def _record_path_or(run: dict, type_: str, role: str, fallback: str) -> str:
    entry = record_for(Path(run["ledger"]), type_, role)
    return str(Path(run["workspace"]) / entry["path"]) if entry else fallback


def cmd_prompt(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    source = references_dir() / PROMPT_SOURCES[args.kind]
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {source}: {error}", file=sys.stderr)
        return 2

    findings_dir = Path(run["findings_dir"])
    subs = {
        "{{SPEC_PATH}}": _record_path_or(run, "spec", "spec", "(no spec minted yet)"),
        "{{PLAN_PATH}}": _record_path_or(run, "plan", "plan", "(no plan minted yet)"),
        "{{TASKS_PATH}}": run["tasks"],
        "{{RUN_DIR}}": run["run_dir"],
        "{{WORKSPACE}}": run["workspace"],
        "{{DOCS}}": run["docs"],
        "{{CODE}}": run["code"],
        "{{SLUG}}": run["slug"],
    }

    if args.kind in REVIEW_KINDS:
        if not args.lens:
            print(f"orko: {args.kind} needs --lens", file=sys.stderr)
            return 2
        lenses = _lenses(text)
        if args.lens not in lenses:
            print(f"orko: unknown lens {args.lens!r}; valid: {', '.join(lenses)}",
                  file=sys.stderr)
            return 2
        subs["{{ARTIFACT_PATH}}"] = subs[
            "{{SPEC_PATH}}" if args.kind == "spec-review" else "{{PLAN_PATH}}"]
        subs["{{LENS_NAME}}"] = args.lens
        subs["{{LENS_QUESTION}}"] = lenses[args.lens]
        subs["{{FINDINGS_PATH}}"] = str(findings_dir / f"{args.lens}.md")
        text = _strip_lenses(text)
    elif args.kind in SEAT_KINDS:
        if not (args.seat and args.context_file):
            print(f"orko: {args.kind} needs --seat, --question, and --context-file",
                  file=sys.stderr)
            return 2
        question = args.question
        question_file = Path(run["context_dir"]) / f"{args.seat}.question"
        if not question:
            if args.kind == "seat":
                print(f"orko: {args.kind} needs --seat, --question, and "
                      "--context-file", file=sys.stderr)
                return 2
            # A verifier must be re-runnable from the trail alone: the seat
            # dispatch recorded its question so a resumed session need not
            # remember it, and a remembered-wrong question is a tilted verifier.
            try:
                question = question_file.read_text(encoding="utf-8")
            except OSError:
                print(f"orko: no recorded question for seat {args.seat}; "
                      "pass --question", file=sys.stderr)
                return 2
        try:
            context = Path(args.context_file).read_text(encoding="utf-8")
        except OSError as error:
            print(f"orko: cannot read {args.context_file}: {error}", file=sys.stderr)
            return 2
        subs["{{SEAT}}"] = args.seat
        subs["{{QUESTION}}"] = question
        subs["{{CONTEXT}}"] = context.rstrip()
        subs["{{FINDINGS_PATH}}"] = str(findings_dir / f"{args.seat}.md")
        subs["{{VERDICT_PATH}}"] = str(findings_dir / f"{args.seat}.verdict.md")

    # Scanned on the raw template, before splicing: a context file or question
    # that happens to quote `{{WORKSPACE}}` is operator text to pass through, not a
    # template defect, and a post-substitution scan would blame the charter for
    # it. `_strip_lenses` has already run for review kinds, so what is scanned
    # is exactly what gets emitted.
    missing = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)) - set(subs))
    if missing:
        print(f"orko: template {source.name} names tokens this kind cannot "
              f"supply: {', '.join(missing)}", file=sys.stderr)
        return 2
    for token, value in subs.items():
        text = text.replace(token, value)
    sys.stdout.write(text)
    if args.kind == "seat":
        try:
            question_file.write_text(question, encoding="utf-8")
        except OSError as error:
            print(f"orko: cannot record the question at {question_file}: {error}",
                  file=sys.stderr)
            return 2
    return 0


def cmd_escalations(args: argparse.Namespace) -> int:
    """Gate the escalation check. `0` = nothing to escalate, `1` = stop the run.

    "Non-empty" lives here rather than in the orchestrator's prose for the same
    reason the validators do: a reviewer that writes a bare heading must not
    halt a run, and an orchestrator with no `ls`/`test` permission has no other
    way to tell an absent file from an empty one.
    """
    ws = resolve_workspace(args)
    if ws is None:
        return 2
    run_dir = _run_dir_root(ws) / args.slug
    if not (run_dir / "progress.md").exists():
        print(f"orko: no run named {args.slug!r}", file=sys.stderr)
        return 2

    target = run_dir / "escalations.md"
    if not target.exists():
        return 0
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {target}: {error}", file=sys.stderr)
        return 2
    if not text.strip():
        return 0
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return 1


DEFAULT_BRANCHES = {"master", "main"}


def _current_branch(root: Path) -> str | None:
    # symbolic-ref, not rev-parse --abbrev-ref: the latter fails on a branch
    # with no commits yet, and a fresh `git init -b master` is exactly the
    # repo a first build engagement is most likely to start in.
    result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def cmd_preflight(args: argparse.Namespace) -> int:
    """Check in code what the prose used to ask the conductor to check.

    Prose that asks the conductor to check something is a check nothing runs;
    each condition here was once such a sentence.
    """
    ws = resolve_workspace(args)
    if ws is None:
        return 2

    mode = args.mode
    run = None
    if args.slug:
        run = _describe_run(ws, args.slug)
        if run is None:
            print(f"orko: no run named {args.slug!r}", file=sys.stderr)
            return 2
        mode = run["mode"]
    if mode is None:
        print("orko: preflight needs --mode or --slug", file=sys.stderr)
        return 2

    findings: list[str] = []
    if shutil.which("uv") is None:
        findings.append("uv-missing: `uv` is not on PATH; every script call needs it")
    branch = _current_branch(ws)
    if mode == "build" and branch in DEFAULT_BRANCHES:
        findings.append(f"on-default-branch: HEAD is {branch}; a build runs on "
                        "orko/<slug>, never on a default branch")
    if run is not None:
        gate = Path(run["escalations"])
        if gate.exists() and gate.read_text(encoding="utf-8").strip():
            findings.append("blocked-escalation: escalations.md is non-empty; only "
                            "oiler may empty it, and the run stays stopped until then")

    for finding in findings:
        print(finding)
    return 1 if findings else 0


def _load_run(args: argparse.Namespace) -> tuple[Path, dict] | None:
    ws = resolve_workspace(args)
    if ws is None:
        return None
    run = _describe_run(ws, args.slug)
    if run is None:
        print(f"orko: no run named {args.slug!r}", file=sys.stderr)
        return None
    return ws, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orko")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="start or resume a run")
    p_init.add_argument("mode", choices=sorted(MODES))
    p_init.add_argument("topic")
    p_init.add_argument("--workspace", required=True,
                        help="scaffold workspace root holding docs/ and code/")
    p_init.add_argument("--owner", required=True)
    p_init.add_argument("--boundaries", required=True)
    p_init.add_argument("--trailer", action="append", default=[])
    p_init.add_argument("--version")
    p_init.add_argument("--executor", choices=EXECUTORS, default="claude")
    p_init.add_argument("--codex-model")
    p_init.add_argument("--codex-effort")
    p_init.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p_init.set_defaults(func=cmd_init)

    p_ledger = sub.add_parser("ledger", help="append a step record")
    p_ledger.add_argument("step")
    p_ledger.add_argument(
        "status", choices=["dispatched", "complete", "failed", "escalated"])
    p_ledger.add_argument("--slug", required=True)
    p_ledger.add_argument("--workspace")
    p_ledger.add_argument("--commit")
    p_ledger.set_defaults(func=cmd_ledger)

    p_status = sub.add_parser("status", help="print the resume point")
    p_status.add_argument("slug", nargs="?")
    p_status.add_argument("--workspace")
    p_status.set_defaults(func=cmd_status)

    p_check = sub.add_parser("check", help="validate an artifact")
    check_sub = p_check.add_subparsers(dest="kind", required=True)
    p_ct = check_sub.add_parser("tasks")
    p_ct.add_argument("path")
    p_ct.set_defaults(func=cmd_check_tasks)

    p_prompt = sub.add_parser("prompt", help="emit a dispatch prompt")
    p_prompt.add_argument("kind", choices=sorted(PROMPT_SOURCES))
    p_prompt.add_argument("slug")
    p_prompt.add_argument("--lens")
    p_prompt.add_argument("--seat")
    p_prompt.add_argument("--question")
    p_prompt.add_argument("--context-file")
    p_prompt.add_argument("--workspace")
    p_prompt.set_defaults(func=cmd_prompt)

    p_escalations = sub.add_parser(
        "escalations", help="0 when there is nothing to escalate, 1 when there is")
    p_escalations.add_argument("slug")
    p_escalations.add_argument("--workspace")
    p_escalations.set_defaults(func=cmd_escalations)

    p_pre = sub.add_parser("preflight", help="check repo, branch, tooling, and record state")
    p_pre.add_argument("--slug")
    p_pre.add_argument("--mode", choices=sorted(MODES))
    p_pre.add_argument("--workspace")
    p_pre.set_defaults(func=cmd_preflight)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
