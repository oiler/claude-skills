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
    uv run orko.py init {analysis|build} <topic> --team KEY [--root DIR] [--date YYYY-MM-DD]
    uv run orko.py ledger <step> <status> --slug SLUG [--commit SHA] [--root DIR]
    uv run orko.py status [<slug>] [--root DIR]
    uv run orko.py check tasks <path>
    uv run orko.py prompt {spec-review|plan-review} <slug> --lens NAME [--root DIR]
    uv run orko.py prompt plan-write <slug> [--root DIR]
    uv run orko.py prompt seat <slug> --seat NAME --question TEXT --context-file PATH [--root DIR]
    uv run orko.py prompt verifier <slug> --seat NAME [--question TEXT] --context-file PATH [--root DIR]
    uv run orko.py escalations <slug> [--root DIR]
    uv run orko.py preflight [--slug SLUG | --mode {analysis|build}] [--root DIR]

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
        # The slug is the Linear Project name and the branch name, so a cut
        # landing mid-word reads as a typo forever. Drop the partial word —
        # unless the first word alone overruns, where a hard cut is all there is.
        cut = slug[:SLUG_MAX]
        if slug[SLUG_MAX] != "-" and "-" in cut:
            cut = cut.rsplit("-", 1)[0]
        slug = cut
    slug = slug.strip("-")
    if not slug:
        raise ValueError(f"topic {topic!r} produced an empty slug")
    return slug


def find_repo_root(start: Path) -> Path | None:
    """Git toplevel of `start`, or None when `start` is not inside a repo."""
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def compute_paths(root: Path, slug: str, date: str) -> dict[str, str]:
    """Every path a run touches, derived from root and slug alone.

    The run directory is scratch and Linear is the record, so artifacts need
    no date in their filename; stability for the validators and seats is all
    that matters.
    """
    run_dir = root / ".orko" / slug
    return {
        "slug": slug,
        "date": date,
        "root": str(root),
        "run_dir": str(run_dir),
        "ledger": str(run_dir / "progress.md"),
        "escalations": str(run_dir / "escalations.md"),
        "spec": str(run_dir / "spec.md"),
        "plan": str(run_dir / "plan.md"),
        "brief": str(run_dir / "brief.md"),
        "synthesis": str(run_dir / "synthesis.md"),
        "findings_dir": str(run_dir / "findings"),
        "context_dir": str(run_dir / "context"),
        "unposted_dir": str(run_dir / "unposted"),
    }


def ensure_gitignored(root: Path) -> None:
    """Append `.orko/` to the target's .gitignore once. The run directory is
    scratch; a trail that commits by accident is the failure this prevents."""
    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if any(line.strip() == ".orko/" for line in existing.splitlines()):
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    with gitignore.open("a", encoding="utf-8") as handle:
        handle.write(f"{prefix}.orko/\n")


def _header(mode: str, topic: str, slug: str, date: str) -> str:
    # `X` is a placeholder: the team field is a leftover of the Linear record
    # and Task 4 rewrites the header without it.
    return (f"# orko run — mode: {mode} — team: X — topic: {topic} "
            f"— slug: {slug} — date: {date}")


HEADER_LINE_RE = re.compile(
    r"# orko run — mode: (?P<mode>analysis|build) — team: (?P<team>[A-Z0-9]+) "
    r"— topic: (?P<topic>.*) — slug: (?P<slug>[a-z0-9-]+) "
    r"— date: (?P<date>\d{4}-\d{2}-\d{2})$"
)


def _parse_header(ledger: Path) -> dict[str, str] | None:
    """Read mode/team/topic/slug/date out of a ledger's first line, or None if
    unreadable. Empty is unreadable, not a crash: callers turn None into exit 2."""
    if not ledger.exists():
        return None
    lines = ledger.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None
    match = HEADER_LINE_RE.match(lines[0])
    return match.groupdict() if match else None


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else find_repo_root(Path.cwd())
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    if CONTROL_RE.search(args.topic):
        print("orko: topic contains a newline or control character; the ledger "
              "header is a single line and could not be read back", file=sys.stderr)
        return 2
    date = args.date or _dt.date.today().isoformat()
    try:
        slug = slugify(args.topic)
    except ValueError as error:
        print(f"orko: {error}", file=sys.stderr)
        return 2
    paths = compute_paths(root, slug, date)
    ledger = Path(paths["ledger"])
    ensure_gitignored(root)

    resumed = False
    if ledger.exists():
        existing = _parse_header(ledger)
        if existing is None:
            print(f"orko: unreadable ledger header in {ledger}", file=sys.stderr)
            return 2
        if existing["topic"] != args.topic:
            print(f"orko: topic {args.topic!r} collides with the existing run "
                  f"{existing['topic']!r} (both slugify to {slug!r}). Choose a "
                  "distinct topic or resume the existing run.", file=sys.stderr)
            return 2
        if existing["mode"] != args.mode:
            print(f"orko: run {slug!r} is a {existing['mode']} engagement; "
                  f"cannot resume it as {args.mode}. A run's mode is fixed at init.",
                  file=sys.stderr)
            return 2
        resumed = True
        paths = compute_paths(root, slug, existing["date"])
    else:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        for key in ("findings_dir", "context_dir", "unposted_dir"):
            Path(paths[key]).mkdir(parents=True, exist_ok=True)
        ledger.write_text(
            _header(args.mode, args.topic, slug, date) + "\n",
            encoding="utf-8",
        )

    header = _parse_header(ledger)
    payload = dict(paths, mode=header["mode"], team=header["team"],
                   topic=args.topic, resumed=resumed,
                   next_step=_next_step(ledger, header["mode"]))
    print(json.dumps(payload, indent=2))
    return 0


# A `--commit` value is a SHA or a SHA range. Anything with whitespace in it
# would write a ledger line LEDGER_LINE_RE cannot parse, silently losing the step.
COMMIT_RE = re.compile(r"[0-9a-f]{7,40}(\.\.[0-9a-f]{7,40})?")

LEDGER_LINE_RE = re.compile(
    r"^step (?P<step>\d+) (?P<status>dispatched|complete|failed|escalated)"
    r"(?: commit=(?P<commit>\S+))?$"
)

def _ledger_entries(ledger: Path) -> list[dict[str, str | None]]:
    """Parsed step records in order, header excluded. Unparseable lines are
    skipped: the ledger is append-only, so a malformed line is damage to
    inspect, never a reason to refuse to report the rest of the run."""
    if not ledger.exists():
        return []
    entries: list[dict[str, str | None]] = []
    for line in ledger.read_text(encoding="utf-8").splitlines()[1:]:
        match = LEDGER_LINE_RE.match(line.strip())
        if match:
            entries.append(match.groupdict())
    return entries


def _next_step(ledger: Path, mode: str) -> int | None:
    """Lowest step of `mode` not recorded complete; None when the run is done.

    Only `complete` advances the run. `dispatched`, `escalated`, and `failed`
    are annotations that survive a compaction, and none of them may move the
    resume point — a dispatched-but-unreturned review has not happened yet.
    """
    done = {
        int(entry["step"])
        for entry in _ledger_entries(ledger)
        if entry["status"] == "complete"
    }
    remaining = [step for step in sorted(MODES[mode]) if step not in done]
    return remaining[0] if remaining else None


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
        if int(entry["step"]) == step and entry["status"] == "dispatched":
            return entry["commit"]
    return None


def _run_dir_root(root: Path) -> Path:
    return root / ".orko"


def _describe_run(root: Path, slug: str) -> dict | None:
    """Run summary for `slug`, or None when its ledger header is unreadable."""
    ledger = _run_dir_root(root) / slug / "progress.md"
    header = _parse_header(ledger)
    if header is None:
        return None
    entries = _ledger_entries(ledger)
    next_step = _next_step(ledger, header["mode"])
    steps = MODES[header["mode"]]
    return dict(
        compute_paths(root, slug, header["date"]),
        mode=header["mode"],
        team=header["team"],
        topic=header["topic"],
        next_step=next_step,
        # `is not None`: build starts at step 0, and a falsy test would report
        # the intake step as already done.
        next_step_name=steps.get(next_step) if next_step is not None else None,
        last_status=entries[-1]["status"] if entries else None,
        dispatched_base=_dispatched_base(entries, next_step),
    )


def _resolved_root(args: argparse.Namespace) -> Path | None:
    """Shared root resolution. None means: not a repo, report exit 2."""
    return Path(args.root).resolve() if args.root else find_repo_root(Path.cwd())


def cmd_ledger(args: argparse.Namespace) -> int:
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    ledger = _run_dir_root(root) / args.slug / "progress.md"
    header = _parse_header(ledger)
    if header is None:
        print(f"orko: no run named {args.slug!r}; run init first", file=sys.stderr)
        return 2
    if args.step not in MODES[header["mode"]]:
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
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2

    if args.slug:
        if not (_run_dir_root(root) / args.slug / "progress.md").exists():
            print(f"orko: no run named {args.slug!r}", file=sys.stderr)
            return 2
        run = _describe_run(root, args.slug)
        if run is None:
            print(f"orko: unreadable ledger header for run {args.slug!r}",
                  file=sys.stderr)
            return 2
        print(json.dumps(run, indent=2))
        return 0

    base = _run_dir_root(root)
    slugs = sorted(
        child.name for child in base.iterdir() if (child / "progress.md").exists()
    ) if base.exists() else []
    runs = [_describe_run(root, slug) for slug in slugs]
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
        "{{SPEC_PATH}}": run["spec"],
        "{{PLAN_PATH}}": run["plan"],
        "{{RUN_DIR}}": run["run_dir"],
        "{{ROOT}}": run["root"],
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
        subs["{{ARTIFACT_PATH}}"] = run["spec" if args.kind == "spec-review" else "plan"]
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
    # that happens to quote `{{ROOT}}` is operator text to pass through, not a
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
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    run_dir = _run_dir_root(root) / args.slug
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


def _is_git_repo(root: Path) -> bool:
    return find_repo_root(root) is not None


def cmd_preflight(args: argparse.Namespace) -> int:
    """Check in code what the prose used to ask the conductor to check.

    Prose that asks the conductor to check something is a check nothing runs;
    each condition here was once such a sentence.
    """
    root = Path(args.root).resolve() if args.root else find_repo_root(Path.cwd())
    if root is None or not _is_git_repo(root):
        print(f"orko: not inside a git repository: {root or Path.cwd()}",
              file=sys.stderr)
        return 2

    mode = args.mode
    run = None
    if args.slug:
        run = _describe_run(root, args.slug)
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
    branch = _current_branch(root)
    if mode == "build" and branch in DEFAULT_BRANCHES:
        findings.append(f"on-default-branch: HEAD is {branch}; a build runs on "
                        "orko/<slug>, never on a default branch")
    gitignore = root / ".gitignore"
    ignored = gitignore.exists() and any(
        line.strip() == ".orko/" for line in gitignore.read_text(encoding="utf-8").splitlines()
    )
    if not ignored:
        findings.append("run-dir-not-ignored: .gitignore lacks `.orko/`; init adds it")
    if run is not None:
        gate = Path(run["escalations"])
        if gate.exists() and gate.read_text(encoding="utf-8").strip():
            findings.append("blocked-escalation: escalations.md is non-empty; only "
                            "oiler may empty it, and the run stays stopped until then")

    for finding in findings:
        print(finding)
    return 1 if findings else 0


def _load_run(args: argparse.Namespace) -> tuple[Path, dict] | None:
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return None
    run = _describe_run(root, args.slug)
    if run is None:
        print(f"orko: no run named {args.slug!r}", file=sys.stderr)
        return None
    return root, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orko")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="start or resume a run")
    p_init.add_argument("mode", choices=sorted(MODES))
    p_init.add_argument("topic")
    p_init.add_argument("--team", required=True, help="Linear team key, e.g. JRF")
    p_init.add_argument("--root", help="repo root (default: git toplevel of cwd)")
    p_init.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p_init.set_defaults(func=cmd_init)

    p_ledger = sub.add_parser("ledger", help="append a step record")
    p_ledger.add_argument("step", type=int)
    p_ledger.add_argument(
        "status", choices=["dispatched", "complete", "failed", "escalated"])
    p_ledger.add_argument("--slug", required=True)
    p_ledger.add_argument("--root")
    p_ledger.add_argument("--commit")
    p_ledger.set_defaults(func=cmd_ledger)

    p_status = sub.add_parser("status", help="print the resume point")
    p_status.add_argument("slug", nargs="?")
    p_status.add_argument("--root")
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
    p_prompt.add_argument("--root")
    p_prompt.set_defaults(func=cmd_prompt)

    p_escalations = sub.add_parser(
        "escalations", help="0 when there is nothing to escalate, 1 when there is")
    p_escalations.add_argument("slug")
    p_escalations.add_argument("--root")
    p_escalations.set_defaults(func=cmd_escalations)

    p_pre = sub.add_parser("preflight", help="check repo, branch, tooling, and record state")
    p_pre.add_argument("--slug")
    p_pre.add_argument("--mode", choices=sorted(MODES))
    p_pre.add_argument("--root")
    p_pre.set_defaults(func=cmd_preflight)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
