# orko.py — deterministic spine for the orko skill
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Owns every deterministic surface of an orko run: artifact paths, the run
ledger, artifact validation, every dispatch prompt, and every Linear payload.

The model authors prose. This script owns structure. In particular the `prompt`
subcommand exists so the orchestrator dispatches reviewer text it cannot edit —
priming a reviewer with the authoring session's context turns a fresh critique
into an echo of the author.

Usage:
    uv run orko.py init {analysis|build} <topic> --team KEY [--root DIR] [--date YYYY-MM-DD]
    uv run orko.py ledger <step> <status> --slug SLUG [--commit SHA] [--root DIR]
    uv run orko.py status [<slug>] [--root DIR]
    uv run orko.py validate {spec|plan} <path>
    uv run orko.py prompt {spec-review|plan-review} <slug> --lens NAME [--root DIR]
    uv run orko.py prompt plan-write <slug> [--root DIR]
    uv run orko.py prompt {seat|verifier} <slug> --seat NAME --question TEXT --context-file PATH [--root DIR]
    uv run orko.py escalations <slug> [--root DIR]
    uv run orko.py linear set <key> <id> --slug SLUG | linear get --slug SLUG
    uv run orko.py post project --slug SLUG --goal TEXT --boundaries TEXT [--branch NAME]
    uv run orko.py post document {spec|plan|brief|synthesis} --slug SLUG
    uv run orko.py post finding --slug SLUG --seat NAME --outcome {handled|deferred|rejected|blocked} --title TEXT   (body on stdin)
    uv run orko.py post escalation --slug SLUG --seat NAME --title TEXT   (body on stdin)
    uv run orko.py post close --slug SLUG --summary TEXT [--pr URL]

Exit codes: 0 success / all checks pass; 1 validation failures; 2 usage or IO error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
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
TEAM_RE = re.compile(r"^[A-Z][A-Z0-9]{0,9}$")

PLACEHOLDER_RE = re.compile(
    r"\b(?:TBD|TODO|FIXME|XXX)\b|<placeholder>|\[fill in\]", re.IGNORECASE
)
OPEN_QUESTION_RE = re.compile(r"\*\*Open question|\?\?\?|\[\?\]", re.IGNORECASE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
# The ledger header is one line. A topic carrying a newline or any other control
# character writes a header no later command can parse, and the run is then
# unrecoverable without hand-editing the ledger.
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

# Heading-keyword requirements. Matching is by whole word against the heading
# text, so "Latest news" does not satisfy "testing" but "Testing" does. The list
# mirrors what superpowers:brainstorming actually emits.
SPEC_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("a problem or goal section", ("problem", "goal")),
    ("an architecture or design section", ("architecture", "design")),
    ("an error handling section", ("error",)),
    ("a testing section", ("test",)),
)


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


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line_number, level, text) for every ATX heading, 1-indexed."""
    found = []
    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            found.append((index, len(match.group(1)), match.group(2)))
    return found


def _section_is_empty(lines: list[str], headings: list[tuple[int, int, str]],
                      position: int) -> bool:
    start, level, _ = headings[position]
    end = len(lines)
    for line_no, other_level, _ in headings[position + 1:]:
        if other_level <= level:
            end = line_no - 1
            break
    body = [line for line in lines[start:end] if line.strip()]
    return not body


def validate_spec(text: str) -> list[Finding]:
    scanned = strip_code(text)
    lines = scanned.split("\n")
    findings: list[Finding] = []

    for index, line in enumerate(lines, start=1):
        for match in PLACEHOLDER_RE.finditer(line):
            findings.append(
                Finding(index, f"placeholder marker {match.group(0)!r}")
            )
        if OPEN_QUESTION_RE.search(line):
            findings.append(Finding(index, "unresolved open question marker"))

    headings = _headings(lines)
    if not any(level == 1 for _, level, _ in headings):
        findings.append(Finding(1, "missing a title (no level-1 heading)"))

    for label, keywords in SPEC_SECTIONS:
        matches = [
            position for position, (_, level, heading) in enumerate(headings)
            if level >= 2 and any(
                re.search(rf"\b{re.escape(kw)}", heading, re.IGNORECASE)
                for kw in keywords
            )
        ]
        if not matches:
            findings.append(Finding(1, f"missing {label}"))
            continue
        for position in matches:
            if _section_is_empty(lines, headings, position):
                line_no, _, heading = headings[position]
                findings.append(Finding(line_no, f"section {heading!r} is empty"))

    return sorted(findings)


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


def cmd_validate(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {target}: {error}", file=sys.stderr)
        return 2

    findings = {"spec": validate_spec, "plan": validate_plan}[args.kind](text)
    if not findings:
        print(f"OK: {target} passes the {args.kind} validator")
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
    slug = "-".join(re.findall(r"[a-z0-9]+", ascii_only.lower()))[:SLUG_MAX].strip("-")
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


def _header(mode: str, team: str, topic: str, slug: str, date: str) -> str:
    return (f"# orko run — mode: {mode} — team: {team} — topic: {topic} "
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
    # fullmatch, not match: `$` also matches before a trailing newline, and a
    # newline in the team key writes a two-line header nothing can parse back.
    if not TEAM_RE.fullmatch(args.team):
        print(f"orko: team key {args.team!r} must be the Linear team key, "
              "uppercase letters and digits (for example JRF)", file=sys.stderr)
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
        for key in ("findings_dir", "context_dir"):
            Path(paths[key]).mkdir(parents=True, exist_ok=True)
        ledger.write_text(
            _header(args.mode, args.team, args.topic, slug, date) + "\n",
            encoding="utf-8",
        )

    header = _parse_header(ledger)
    payload = dict(paths, mode=header["mode"], team=header["team"],
                   topic=args.topic, resumed=resumed,
                   next_step=_next_step(ledger, header["mode"]))
    print(json.dumps(payload, indent=2))
    return 0


LEDGER_LINE_RE = re.compile(
    r"^step (?P<step>\d+) (?P<status>dispatched|complete|failed|escalated)"
    r"(?: commit=(?P<commit>\S+))?$"
)

LINEAR_KEYS = ("project", "spec_doc", "plan_doc", "brief_doc",
               "synthesis_doc", "blocked_label")
LINEAR_LINE_RE = re.compile(
    r"^linear (?P<key>" + "|".join(LINEAR_KEYS) + r") (?P<id>\S+)$"
)


def _linear_ids(ledger: Path) -> dict[str, str]:
    """Recorded Linear IDs, last write wins. Lives in the ledger so a resumed
    session can re-fetch the Project and documents without the transcript."""
    ids: dict[str, str] = {}
    if not ledger.exists():
        return ids
    for line in ledger.read_text(encoding="utf-8").splitlines()[1:]:
        match = LINEAR_LINE_RE.match(line.strip())
        if match:
            ids[match.group("key")] = match.group("id")
    return ids


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
        linear=_linear_ids(ledger),
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
        if not (args.seat and args.question and args.context_file):
            print(f"orko: {args.kind} needs --seat, --question, and --context-file",
                  file=sys.stderr)
            return 2
        try:
            context = Path(args.context_file).read_text(encoding="utf-8")
        except OSError as error:
            print(f"orko: cannot read {args.context_file}: {error}", file=sys.stderr)
            return 2
        subs["{{SEAT}}"] = args.seat
        subs["{{QUESTION}}"] = args.question
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


def cmd_linear(args: argparse.Namespace) -> int:
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    ledger = _run_dir_root(root) / args.slug / "progress.md"
    if _parse_header(ledger) is None:
        print(f"orko: no run named {args.slug!r}", file=sys.stderr)
        return 2
    if args.action == "set":
        if CONTROL_RE.search(args.id) or args.id.split() != [args.id]:
            print("orko: a Linear ID cannot contain whitespace", file=sys.stderr)
            return 2
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(f"linear {args.key} {args.id}\n")
        return 0
    print(json.dumps(_linear_ids(ledger), indent=2))
    return 0


DOC_KINDS = {"spec": "Spec", "plan": "Plan", "brief": "Brief", "synthesis": "Synthesis"}


def _emit_posts(posts: list[dict]) -> int:
    """The one place payloads leave the script. Every `post` subcommand ends
    here so the shape the conductor relays is identical across entities."""
    print(json.dumps({"posts": posts}, indent=2))
    return 0


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


def _project_description(run: dict, goal: str, boundaries: str,
                         branch: str | None) -> str:
    lines = [
        f"**Goal:** {goal}",
        "",
        f"- Mode: {run['mode']}",
        f"- Slug: `{run['slug']}`",
        f"- Repository: `{run['root']}`",
        f"- Branch: `{branch}`" if branch else "- Branch: none (analysis, read-only)",
        f"- Run directory: `{run['run_dir']}`",
        f"- Boundaries: {boundaries}",
        "",
        "Record kept by orko. Issues in this project are decisions kicked up to "
        "the conductor, one per decision, attributed by seat in the first line "
        "of each description. Documents hold the working artifacts.",
    ]
    return "\n".join(lines) + "\n"


def cmd_post_project(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    if run["mode"] == "build" and not args.branch:
        print("orko: a build project needs --branch (the orko/<slug> branch the "
              "run works on)", file=sys.stderr)
        return 2
    # Checked here rather than by argparse so a missing field is reported the
    # same way as a missing --branch: exit 2 with an `orko:` line, not a
    # usage dump. The branch check runs first because it is mode-specific.
    if not args.boundaries:
        print("orko: post project needs --boundaries (what the run may and may "
              "not touch)", file=sys.stderr)
        return 2
    description = _project_description(run, args.goal, args.boundaries, args.branch)
    existing = run["linear"].get("project")
    if existing:
        post_args = {"id": existing, "description": description}
        then = None
    else:
        post_args = {"name": run["slug"], "addTeams": [run["team"]],
                     "summary": args.goal[:255], "description": description}
        then = f"linear set project <returned id> --slug {run['slug']}"
    return _emit_posts([{"tool": "mcp__linear__save_project",
                         "args": post_args, "then": then}])


def cmd_post_document(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    project = run["linear"].get("project")
    if not project:
        print("orko: no Linear project recorded for this run; post project first "
              "and record its id with `linear set project`", file=sys.stderr)
        return 2
    source = Path(run[args.kind])
    try:
        content = source.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {source}: {error}", file=sys.stderr)
        return 2
    key = f"{args.kind}_doc"
    existing = run["linear"].get(key)
    if existing:
        post_args = {"id": existing, "content": content}
        then = None
    else:
        post_args = {"title": DOC_KINDS[args.kind], "project": project,
                     "content": content}
        then = f"linear set {key} <returned id> --slug {run['slug']}"
    return _emit_posts([{"tool": "mcp__linear__save_document",
                         "args": post_args, "then": then}])


def cmd_post_close(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    project = run["linear"].get("project")
    if not project:
        print("orko: no Linear project recorded for this run", file=sys.stderr)
        return 2
    post_args: dict = {
        "id": project,
        "state": "Completed",
        "description": f"**Closed.** {args.summary}\n",
    }
    if args.pr:
        post_args["links"] = [{"url": args.pr, "title": "Pull request"}]
    return _emit_posts([{"tool": "mcp__linear__save_project",
                         "args": post_args, "then": None}])


# Decision outcomes and the JRF team state each maps to. The team has no
# "Blocked" state, so an out-of-boundaries finding is a Todo carrying the
# `blocked` label, and the run stops on it (see cmd_post_escalation).
OUTCOMES: dict[str, str] = {
    "handled": "Done",
    "deferred": "Backlog",
    "rejected": "Canceled",
    "blocked": "Todo",
}
BLOCKED_LABEL = {"name": "blocked", "color": "#eb5757"}


def _finding_posts(run: dict, seat: str, outcome: str, title: str,
                   body: str) -> list[dict]:
    posts: list[dict] = []
    labels: list[str] = []
    if outcome == "blocked":
        labels = [BLOCKED_LABEL["name"]]
        if not run["linear"].get("blocked_label"):
            posts.append({
                "tool": "mcp__linear__save_issue_label",
                "args": {"team": run["team"], **BLOCKED_LABEL},
                "then": f"linear set blocked_label <returned id> --slug {run['slug']}",
            })
    issue_args: dict = {
        "team": run["team"],
        "project": run["linear"]["project"],
        "title": title,
        "state": OUTCOMES[outcome],
        "description": f"Seat: {seat}\n\n{body.rstrip()}\n",
    }
    if labels:
        issue_args["labels"] = labels
    posts.append({"tool": "mcp__linear__save_issue", "args": issue_args,
                  "then": None})
    return posts


def _read_body() -> str | None:
    body = sys.stdin.read()
    return body if body.strip() else None


def cmd_post_finding(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    if not run["linear"].get("project"):
        print("orko: no Linear project recorded for this run", file=sys.stderr)
        return 2
    body = _read_body()
    if body is None:
        print("orko: the finding body (stdin) is empty; pipe the finding's "
              "evidence and the conductor's reasoning", file=sys.stderr)
        return 2
    outcome = "blocked" if args.entity == "escalation" else args.outcome
    if args.entity == "escalation":
        gate = Path(run["escalations"])
        with gate.open("a", encoding="utf-8") as handle:
            handle.write(f"## {args.title}\n\nSeat: {args.seat}\n\n{body.rstrip()}\n\n")
    return _emit_posts(_finding_posts(run, args.seat, outcome, args.title, body))


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

    p_validate = sub.add_parser("validate", help="check an artifact")
    p_validate.add_argument("kind", choices=["spec", "plan"])
    p_validate.add_argument("path")
    p_validate.set_defaults(func=cmd_validate)

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

    p_post = sub.add_parser("post", help="emit a Linear payload for the conductor to send")
    post_sub = p_post.add_subparsers(dest="entity", required=True)

    p_pp = post_sub.add_parser("project")
    p_pp.add_argument("--slug", required=True)
    p_pp.add_argument("--root")
    p_pp.add_argument("--goal", required=True)
    p_pp.add_argument("--boundaries")
    p_pp.add_argument("--branch")
    p_pp.set_defaults(func=cmd_post_project)

    p_pd = post_sub.add_parser("document")
    p_pd.add_argument("kind", choices=sorted(DOC_KINDS))
    p_pd.add_argument("--slug", required=True)
    p_pd.add_argument("--root")
    p_pd.set_defaults(func=cmd_post_document)

    p_pc = post_sub.add_parser("close")
    p_pc.add_argument("--slug", required=True)
    p_pc.add_argument("--root")
    p_pc.add_argument("--summary", required=True)
    p_pc.add_argument("--pr")
    p_pc.set_defaults(func=cmd_post_close)

    for entity in ("finding", "escalation"):
        p_pf = post_sub.add_parser(entity)
        p_pf.add_argument("--slug", required=True)
        p_pf.add_argument("--root")
        p_pf.add_argument("--seat", required=True)
        p_pf.add_argument("--title", required=True)
        if entity == "finding":
            p_pf.add_argument("--outcome", required=True, choices=sorted(OUTCOMES))
        p_pf.set_defaults(func=cmd_post_finding)

    p_linear = sub.add_parser("linear", help="record or read Linear IDs")
    linear_sub = p_linear.add_subparsers(dest="action", required=True)
    p_set = linear_sub.add_parser("set")
    p_set.add_argument("key", choices=LINEAR_KEYS)
    p_set.add_argument("id")
    p_set.add_argument("--slug", required=True)
    p_set.add_argument("--root")
    p_set.set_defaults(func=cmd_linear)
    p_get = linear_sub.add_parser("get")
    p_get.add_argument("--slug", required=True)
    p_get.add_argument("--root")
    p_get.set_defaults(func=cmd_linear)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
