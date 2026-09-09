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
    uv run orko.py record spec --slug SLUG --title TEXT [--workspace DIR]
    uv run orko.py record plan --slug SLUG --title TEXT --implements SPEC-NNN
        [--workspace DIR]
    uv run orko.py record {decision|adr|research} --slug SLUG --title TEXT [--workspace DIR]
    uv run orko.py record disposition --slug SLUG --review REVIEW-NNN --finding FN
        --disposition {accepted|rejected|resolved|noted} [--workspace DIR]
    uv run orko.py record status --slug SLUG --id ID --status {draft|in_review} [--workspace DIR]
    uv run orko.py record amendment --slug SLUG --id SPEC-NNN --text TEXT [--workspace DIR]
    uv run orko.py record delivery-decision --slug SLUG --decision TEXT --rationale TEXT
        [--workspace DIR]
    uv run orko.py record risk --slug SLUG --text TEXT [--workspace DIR]
    uv run orko.py record close --slug SLUG --summary TEXT
        [--changelog "<Added|Changed|Fixed|Removed|Security>: text"]
        [--date YYYY-MM-DD] [--workspace DIR]
    uv run orko.py prompt {spec-review|plan-review} <slug> --lens NAME [--workspace DIR]
    uv run orko.py prompt plan-write <slug> [--workspace DIR]
    uv run orko.py prompt seat <slug> --seat NAME --question TEXT --context-file PATH [--workspace DIR]
    uv run orko.py prompt verifier <slug> --seat NAME [--question TEXT] --context-file PATH [--workspace DIR]
    uv run orko.py escalations <slug> [--workspace DIR]
    uv run orko.py preflight --slug SLUG [--workspace DIR]

Exit codes: 0 success / all checks pass; 1 validation failures; 2 usage or IO error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
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
# `[ \t]*`, never `\s*`: `\s` spans newlines, so an empty `**Acceptance:**` line
# would harvest the next line as the command and hand `**Interfaces:**` to a
# `--write` Codex dispatch as something to run.
ACCEPTANCE_RE = re.compile(r"^\*\*Acceptance:\*\*[ \t]*`?(?P<cmd>[^`\n]+)`?[ \t]*$",
                           re.MULTILINE)
FILES_RE = re.compile(r"^-\s+(?:Create|Modify|Test|Delete):\s*`(?P<path>[^`]+)`", re.MULTILINE)


def parse_tasks(text: str) -> list[dict]:
    """One dict per `### Task N:` block of a `superpowers:writing-plans` file.

    Parsed from the raw text, not `strip_code` output: the acceptance command
    and the file paths live in backticks, and the Codex dispatch needs them.
    """
    heads = list(re.finditer(r"^### Task (?P<n>\d+):\s*(?P<title>.+)$", text, re.MULTILINE))
    tasks = []
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        block = text[head.start():end].rstrip() + "\n"
        acceptance = ACCEPTANCE_RE.search(block)
        tasks.append(dict(
            n=int(head.group("n")), title=head.group("title").strip(), body=block,
            files=[match.group("path").split(":")[0] for match in FILES_RE.finditer(block)],
            acceptance=acceptance.group("cmd").strip() if acceptance else None,
        ))
    return tasks


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
        # The Codex loop dispatches one command per task and judges delivery on
        # its exit code. A task without one has no definition of done.
        if not ACCEPTANCE_RE.search(block):
            findings.append(Finding(line_no, "task block has no '**Acceptance:**' line"))

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


SPEC_ID_RE = re.compile(r"^[A-Z]+-[0-9]{3}$")


def plans_implementing(ws: Path, spec_id: str) -> list[Path]:
    """Every `docs/versions/*/plans/PLAN-*.md` whose `implements:` names the ID."""
    hits = []
    for plan in sorted((ws / "docs" / "versions").glob("*/plans/PLAN-*.md")):
        try:
            text = plan.read_text(encoding="utf-8")
        except OSError:
            continue
        if not text.startswith("---"):
            continue
        block = text.split("---", 2)[1].split("\n")
        for index, line in enumerate(block):
            if not line.startswith("implements:"):
                continue
            span = [line]
            for later in block[index + 1:]:
                if FM_KEY_RE.match(later):
                    break
                span.append(later)
            if re.search(rf"\b{re.escape(spec_id)}\b", "\n".join(span)):
                hits.append(plan)
            break
    return hits


DELIVERY_DECISIONS_HEADING = "## Delivery decisions"


def signed_delivery_rows(plan: Path) -> list[str]:
    """Body rows of the plan's Delivery decisions table with a non-empty third
    cell. That column is `Approved by`, and only a human writes into it."""
    lines = plan.read_text(encoding="utf-8").split("\n")
    if DELIVERY_DECISIONS_HEADING not in lines:
        return []
    start = lines.index(DELIVERY_DECISIONS_HEADING)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
               len(lines))
    rows = [lines[i] for i in range(start + 1, end) if lines[i].lstrip().startswith("|")]
    signed = []
    for row in rows[2:]:  # skip the header and the separator
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[2]:
            signed.append(row)
    return signed


def cmd_check_spec(args: argparse.Namespace) -> int:
    """Run the scaffold's own spec-check.sh and pass its verdict through."""
    if not SPEC_ID_RE.fullmatch(args.id):
        print(f"orko: {args.id!r} is not an ID like SPEC-001", file=sys.stderr)
        return 2
    ws = resolve_workspace(args)
    if ws is None:
        return 2
    docs, script = ws / "docs", ws / "code/scripts/spec-check.sh"
    if not docs.is_dir() or not script.is_file():
        print("orko: workspace lacks docs/ or code/scripts/spec-check.sh", file=sys.stderr)
        return 2
    result = subprocess.run([str(script), args.id, "--docs", str(docs)],
                            capture_output=True, text=True, check=False)
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    if args.require_plan and result.returncode == 0:
        if "no PLAN" in result.stdout:
            print(f"plan-missing: spec-check found no plan implementing {args.id}")
            return 1
        for plan in plans_implementing(ws, args.id):
            status = read_frontmatter_field(plan, "status")
            if status in ("draft", "in_review") and signed_delivery_rows(plan):
                print(f"plan-approval-signed: {plan} has an Approved by value on "
                      f"a {status} plan")
                return 1
    return result.returncode


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


class RecordType(NamedTuple):
    prefix: str | None
    repo: str          # "docs" or "code"
    subdir: str        # relative to the repo; "versions/<v>/specs" uses the run's version
    template: str      # relative to docs/, or "adr-readme", or "orko-research"
    index: str | None  # relative to the repo; None when the type has no index


RECORD_TYPES: dict[str, RecordType] = {
    "spec": RecordType("SPEC", "docs", "versions/<v>/specs", "templates/spec.md", "versions/<v>/README.md"),
    "plan": RecordType("PLAN", "docs", "versions/<v>/plans", "templates/plan.md", "versions/<v>/README.md"),
    "review": RecordType("REVIEW", "docs", "versions/<v>/reviews", "templates/review.md", "versions/<v>/README.md"),
    "decision": RecordType("DEC", "docs", "decisions", "templates/decision.md", "decisions/README.md"),
    "adr": RecordType("ADR", "code", "docs/adr", "adr-readme", None),
    "research": RecordType(None, "docs", "research", "orko-research", None),
}
ID_RE = re.compile(r"^(?P<prefix>[A-Z]+)-(?P<n>\d{3})$")
FM_KEY_RE = re.compile(r"^(?P<key>[A-Za-z_]+):(?P<rest>.*)$")


def _split_frontmatter(text: str) -> tuple[list[str], str]:
    if not text.startswith("---\n"):
        raise ValueError("template has no frontmatter")
    head, _, body = text[4:].partition("\n---\n")
    return head.split("\n"), body


def _render_value(key: str, value, quoted: bool) -> list[str]:
    if value is None:
        return [f"{key}: null"]
    if isinstance(value, list):
        return [f"{key}:"] + [f"  - {item}" for item in value]
    return [f'{key}: "{value}"' if quoted else f"{key}: {value}"]


def set_frontmatter(text: str, updates: dict) -> str:
    """Rewrite top-level keys inside the leading --- block, body untouched."""
    lines, body = _split_frontmatter(text)
    out: list[str] = []
    seen: set[str] = set()
    index = 0
    while index < len(lines):
        match = FM_KEY_RE.match(lines[index])
        if not match:
            out.append(lines[index])
            index += 1
            continue
        key = match.group("key")
        block_end = index + 1
        while block_end < len(lines) and lines[block_end].startswith((" ", "\t", "-")):
            block_end += 1
        if key in updates:
            quoted = match.group("rest").strip().startswith('"')
            out.extend(_render_value(key, updates[key], quoted))
            seen.add(key)
        else:
            out.extend(lines[index:block_end])
        index = block_end
    for key, value in updates.items():
        if key not in seen:
            out.extend(_render_value(key, value, False))
    return "---\n" + "\n".join(out) + "\n---\n" + body


def _type_dir(ws: Path, type_: str, version: str) -> Path:
    rt = RECORD_TYPES[type_]
    return ws / rt.repo / rt.subdir.replace("<v>", version)


def next_id(ws: Path, type_: str) -> str:
    """One past the highest existing ID of this type, across every dossier."""
    rt = RECORD_TYPES[type_]
    assert rt.prefix, f"{type_} has no ID"
    pattern = rt.subdir.replace("<v>", "*")
    highest = 0
    for path in (ws / rt.repo).glob(f"{pattern}/{rt.prefix}-*.md"):
        match = re.match(rf"{rt.prefix}-(\d{{3}})", path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{rt.prefix}-{highest + 1:03d}"


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
    # Intake is a visible commitment: a build announces itself in STATUS.md the
    # moment it starts, so a reader of the docs repo sees work in flight rather
    # than a surprise pull request at close.
    if not resumed and args.mode == "build":
        _status_progress_line(ws, args.topic, f"- {args.topic}: in progress")
        append_ledger(ledger, "touched docs/STATUS.md")
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
                     step: int | str | None) -> str | None:
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
    "task-review": "task-reviewer.md",
    # `task` is assembled by `render_task_prompt`, not spliced from a charter:
    # its routing line and its trailers are executor state, not prose.
    "task": None,
}
REVIEW_KINDS = ("spec-review", "plan-review")
SEAT_KINDS = ("seat", "verifier")
TASK_KINDS = ("task", "task-review")
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


def _task_or_exit(run: dict, n: int) -> dict | None:
    try:
        tasks = parse_tasks(Path(run["tasks"]).read_text(encoding="utf-8"))
    except OSError:
        print(f"orko: no tasks.md at {run['tasks']}", file=sys.stderr)
        return None
    for task in tasks:
        if task["n"] == n:
            # The acceptance command is the whole definition of done for a Codex
            # dispatch. Rendering `None` into one would ask it to run nothing and
            # call that a pass.
            if task["acceptance"] is None:
                print(f"orko: Task {n} has no **Acceptance:** command", file=sys.stderr)
                return None
            return task
    print(f"orko: tasks.md has no Task {n}", file=sys.stderr)
    return None


def render_task_prompt(run: dict, task: dict, attempt: str, failure: str | None) -> str:
    """The whole Codex dispatch: routing line, then the task.

    The routing flags lead the text rather than riding on the dispatching tool's
    parameters, because the `Agent` tool's `model` cannot carry a Codex slug.
    """
    flags = ["--background", "--write", "--fresh" if attempt == "fresh" else "--resume"]
    if run["codex_model"]:
        flags += ["--model", run["codex_model"]]
    if run["codex_effort"]:
        flags += ["--effort", run["codex_effort"]]
    spec_id = (record_for(Path(run["ledger"]), "spec", "spec") or {}).get("id", "SPEC-?")
    plan_id = (record_for(Path(run["ledger"]), "plan", "plan") or {}).get("id", "PLAN-?")
    lines = [
        " ".join(flags), "",
        f"Implement Task {task['n']} of the orko build for {run['topic']}.",
        f"Refs: {spec_id}, {plan_id}. Cite both in the commit message.",
        f"Boundaries: {run['boundaries']}",
        f"Working directory: {run['code']} (the code repository). Do not touch {run['docs']}.",
        f"Branch: orko/{run['slug']} (already checked out).",
        "",
        task["body"],
        f"Acceptance: run `{task['acceptance']}` and make it exit 0.",
        "For every requirement row this task satisfies, add or update a row in "
        "docs/testing/README.md (in the code repository) mapping `SPEC-NNN R<n>` "
        "to the test that proves it.",
    ]
    if failure:
        lines += ["", f"The previous attempt failed: {failure}. Fix that first."]
    lines += ["", "When the acceptance command passes, commit every change with a message that "
              "starts with the task title, cites the Refs line, and ends with these trailers verbatim:",
              *run["trailers"], "", "Leave the tree clean. Report the commit sha."]
    return "\n".join(lines) + "\n"


def cmd_prompt(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    if args.kind in TASK_KINDS:
        if args.task is None:
            print(f"orko: {args.kind} needs --task N", file=sys.stderr)
            return 2
        task = _task_or_exit(run, args.task)
        if task is None:
            return 2
    if args.kind == "task":
        sys.stdout.write(render_task_prompt(run, task, args.attempt, args.failure))
        return 0
    # Every other kind files its findings under the step that asked for them, and
    # a complete run has no such step. A `findings/None/` directory is a defect,
    # not a resting place.
    if run["next_step"] is None and args.kind != "task-review":
        print(f"orko: run {run['slug']} is complete; nothing left to prompt",
              file=sys.stderr)
        return 2
    source = references_dir() / PROMPT_SOURCES[args.kind]
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {source}: {error}", file=sys.stderr)
        return 2

    # Findings are filed under the step that asked for them: a task's two
    # reviewers and a plan reviewer of the same lens name would otherwise
    # overwrite each other in one flat directory.
    findings_dir = Path(run["findings_dir"]) / (
        f"5.{args.task}" if args.kind == "task-review" else str(run["next_step"]))
    findings_dir.mkdir(parents=True, exist_ok=True)
    subs = {
        "{{SPEC_PATH}}": _record_path_or(run, "spec", "spec", "(no spec minted yet)"),
        "{{PLAN_PATH}}": _record_path_or(run, "plan", "plan", "(no plan minted yet)"),
        "{{TASKS_PATH}}": run["tasks"],
        "{{BOUNDARIES}}": run["boundaries"],
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
    elif args.kind == "task-review":
        if not args.lens:
            print(f"orko: {args.kind} needs --lens", file=sys.stderr)
            return 2
        lenses = _lenses(text)
        if args.lens not in lenses:
            print(f"orko: unknown lens {args.lens!r}; valid: {', '.join(lenses)}",
                  file=sys.stderr)
            return 2
        entries = _ledger_entries(Path(run["ledger"]))
        base = _dispatched_base(entries, f"5.{args.task}")
        # No base means no recorded dispatch for this task. Guessing one would
        # hand the reviewer somebody else's diff, so refuse instead.
        if base is None:
            print(f"orko: no ledger 5.{args.task} dispatched --commit line",
                  file=sys.stderr)
            return 2
        subs["{{TASK_N}}"] = str(task["n"])
        subs["{{TASK_BODY}}"] = task["body"].rstrip()
        subs["{{DIFF_BASE}}"] = base
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


def codex_companion_path() -> Path | None:
    hits = sorted((Path.home() / ".claude/plugins/cache/openai-codex/codex").glob(
        "*/scripts/codex-companion.mjs"))
    return hits[-1] if hits else None


def codex_setup_ready() -> tuple[bool, str]:
    """Ask the openai-codex companion whether the CLI is usable right now."""
    companion = codex_companion_path()
    if companion is None:
        return False, "openai-codex plugin not installed"
    try:
        result = subprocess.run(
            ["node", str(companion), "setup", "--json"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        # The companion is a Node script, and a machine with the plugin but no
        # node is a preflight finding, never a traceback out of `preflight`.
        return False, "node is not on PATH"
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, result.stderr.strip() or "setup --json returned no JSON"
    return payload.get("ready") is True, json.dumps(payload.get("codex", {}))


def run_companion(args: list[str]) -> subprocess.CompletedProcess:
    """One call to the openai-codex companion. Isolated so tests can stand in
    for a plugin this machine may not have installed."""
    companion = codex_companion_path()
    if companion is None:
        raise FileNotFoundError("openai-codex plugin not installed")
    return subprocess.run(["node", str(companion), *args],
                          capture_output=True, text=True, check=False)


def cmd_codex_wait(args: argparse.Namespace) -> int:
    """Block until a background Codex job settles, then print its result."""
    if _load_run(args) is None:
        return 2
    try:
        status = run_companion(["status", args.job_id, "--wait",
                                "--timeout-ms", str(args.timeout_ms), "--json"])
        result = run_companion(["result", args.job_id, "--json"])
    except FileNotFoundError as error:
        print(f"orko: {error}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(result.stdout or status.stdout)
    except json.JSONDecodeError:
        print(f"orko: companion returned no JSON: {result.stderr.strip()}",
              file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("status") == "completed" else 1


def _dirty(repo: Path, untracked: bool = True) -> bool:
    """Working-tree dirt. `untracked=False` counts modified and staged files only.

    Preflight ignores untracked files: a reviewer seat that ran the test suite
    leaves caches and lockfiles behind, and none of them can reach a commit
    `commit` makes. `check delivery` still counts them, because a Codex delivery
    that left a file unstaged is an incomplete delivery.
    """
    flags = ["--porcelain"] if untracked else ["--porcelain", "--untracked-files=no"]
    return bool(_git(repo, "status", *flags).stdout.strip())


def cmd_preflight(args: argparse.Namespace) -> int:
    """Check in code what the prose used to ask the conductor to check.

    Prose that asks the conductor to check something is a check nothing runs;
    each condition here was once such a sentence. Each condition is one
    finding, so a test can remove exactly one and see exactly one test go red.
    """
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded

    findings: list[str] = []
    checks = 0
    if shutil.which("uv") is None:
        findings.append("uv-missing: `uv` is not on PATH; every script call needs it")
    checks += 1
    for name in validate_workspace(ws):
        findings.append(f"workspace-invalid: {name}")
    checks += 1
    for repo in ("docs", "code"):
        # Modified and staged only: see `_dirty`.
        if _dirty(ws / repo, untracked=False):
            findings.append(f"{repo}-dirty: uncommitted changes in {repo}/")
        checks += 1
    # A second loop, not a second clause in the first: the findings print in
    # the order they are appended, and the interface fixes that order.
    for repo in ("docs", "code"):
        branch = _current_branch(ws / repo)
        if run["mode"] == "build" and branch in DEFAULT_BRANCHES:
            findings.append(f"{repo}-on-default-branch: {repo}/ is on {branch}; a "
                            "build runs on orko/<slug>, never on a default branch")
        checks += 1
    if dossier_status(ws, run["version"]) not in ("active", "proposed"):
        findings.append(f"dossier-inactive: versions/{run['version']} is not active")
    checks += 1
    if run["mode"] == "build" and run["next_step"] == 5:
        checks += 1
        spec = record_for(Path(run["ledger"]), "spec", "spec")
        path = ws / spec["path"] if spec else None
        if path is None or read_frontmatter_field(path, "status") != "accepted":
            findings.append("spec-not-accepted: a human sets status: accepted "
                            "before execution begins")
        else:
            # The acceptance edit is a human's, so re-hash here or the next
            # overwrite guard reports the human's own edit as tampering.
            append_ledger(Path(run["ledger"]), f"hash {spec['path']} {sha256_file(path)}")
    if run["executor"] == "codex":
        ready, detail = codex_setup_ready()
        if not ready:
            findings.append(f"codex-unavailable: run /codex:setup ({detail})")
        checks += 1
    gate = Path(run["escalations"])
    if gate.exists() and gate.read_text(encoding="utf-8").strip():
        findings.append("blocked-escalation: escalations.md is non-empty; only "
                        "oiler may empty it, and the run stays stopped until then")
    checks += 1

    for finding in findings:
        print(finding)
    if findings:
        return 1
    # A silent exit 0 cannot be told from a preflight that never ran, and the
    # Codex readiness probe is the one check whose silence costs a wasted dispatch.
    print(f"preflight: ok ({checks} checks)")
    return 0


def _load_run(args: argparse.Namespace) -> tuple[Path, dict] | None:
    ws = resolve_workspace(args)
    if ws is None:
        return None
    run = _describe_run(ws, args.slug)
    if run is None:
        print(f"orko: no run named {args.slug!r}", file=sys.stderr)
        return None
    return ws, run


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(ws: Path, path: Path) -> str:
    return str(path.resolve().relative_to(ws.resolve()))


def record_path(ws: Path, type_: str, version: str, id_: str | None,
                slug: str, role: str, date: str = "") -> Path:
    """`<type dir>/<ID>-<slug>[-<role>].md`, or `<date>-<slug>[-<role>].md` for
    a type that mints no ID — a research note needs the date to sort."""
    parts = (date if not id_ else None, id_, slug, role if role != type_ else None)
    stem = "-".join(part for part in parts if part)
    return _type_dir(ws, type_, version) / f"{stem}.md"


def overwrite_guard(ledger: Path, ws: Path, path: Path) -> str | None:
    """A finding when the file changed since its hash was recorded — the record
    carries hand edits the run never saw, so a rewrite would destroy them."""
    recorded = hashes(ledger).get(rel(ws, path))
    if recorded is None:
        return None
    if not path.exists():
        return None
    if sha256_file(path) == recorded:
        return None
    return f"edited-since-commit: {rel(ws, path)} differs from its last committed hash"


def update_index(index_path: Path, row: list[str], id_cell: str) -> None:
    """Replace or append a row in the first table under the index heading.

    The table is the run of consecutive `|` lines: the version README has a
    Release index table right after the Artifact index, and a scan that does
    not stop at the first blank line overwrites the release row.
    """
    lines = index_path.read_text(encoding="utf-8").split("\n")
    heading = "## Artifact index" if "versions" in index_path.parts else None
    start = 0
    if heading:
        start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
        if start is None:
            raise ValueError(f"{index_path} has no '{heading}' heading")
    first = next((i for i in range(start, len(lines)) if lines[i].startswith("|")), None)
    if first is None:
        raise ValueError(f"{index_path} has no table under {heading or 'the top'}")
    table = []
    for i in range(first, len(lines)):
        if not lines[i].startswith("|"):
            break
        table.append(i)
    rendered = "| " + " | ".join(row) + " |"
    body = table[2:]  # skip header and separator
    for i in body:
        cell = lines[i].split("|")[1].strip()
        if cell.startswith("[") or cell == id_cell:
            lines[i] = rendered
            break
    else:
        lines.insert(body[-1] + 1 if body else table[-1] + 1, rendered)
    index_path.write_text("\n".join(lines), encoding="utf-8")


def _load_template(ws: Path, type_: str) -> str:
    """The scaffold's own template for a record type. The ADR template lives in
    a fenced block inside the ADR README; research has no scaffold template, so
    the skill ships one."""
    rt = RECORD_TYPES[type_]
    if rt.template == "adr-readme":
        text = (ws / "code/docs/adr/README.md").read_text(encoding="utf-8")
        return text.split("```markdown\n", 1)[1].split("```", 1)[0]
    if rt.template == "orko-research":
        return (references_dir() / "templates/research.md").read_text(encoding="utf-8")
    return (ws / "docs" / rt.template).read_text(encoding="utf-8")


def _mint(ws: Path, run: dict, type_: str, role: str, title: str,
          updates: dict, index_row: list[str] | None) -> tuple[int, dict]:
    """Write one record from its template, index it, and log it to the ledger.

    Resumable by construction: a role already in the ledger is returned as-is
    rather than minted twice, so a rerun of an interrupted run is a no-op.
    """
    ledger = Path(run["ledger"])
    existing = record_for(ledger, type_, role)
    if existing:
        return 0, dict(id=existing["id"], type=type_, role=role,
                       path=str(ws / existing["path"]), resumed=True)
    rt = RECORD_TYPES[type_]
    id_ = next_id(ws, type_) if rt.prefix else None
    path = record_path(ws, type_, run["version"], id_, run["slug"], role, run["date"])
    guard = overwrite_guard(ledger, ws, path)
    if guard:
        print(f"orko: {guard}", file=sys.stderr)
        return 2, {}
    try:
        text = _load_template(ws, type_)
        fields = dict(updates)
        if id_:
            fields["id"] = id_
            text = text.replace(f"{rt.prefix}-NNN — [", f"{id_} — [", 1)
        text = set_frontmatter(text, fields)
        if id_:
            text = re.sub(rf"^# {id_} — \[.*\]$", lambda m: f"# {id_} — {title}",
                          text, count=1, flags=re.MULTILINE)
        else:
            text = re.sub(r"^# \[Title\]$", lambda m: f"# {title}",
                          text, count=1, flags=re.MULTILINE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        append_ledger(ledger, f"record {type_} {role} {id_ or '-'} {rel(ws, path)}")
        if rt.index and index_row:
            row = [id_ if cell == "ID" else cell for cell in index_row]
            index_path = ws / rt.repo / rt.index.replace("<v>", run["version"])
            update_index(index_path, row, id_ or "")
            append_ledger(ledger, f"touched {rel(ws, index_path)}")
    except ValueError as error:
        print(f"orko: {error}", file=sys.stderr)
        return 2, {}
    return 0, dict(id=id_, type=type_, role=role, path=str(path), resumed=False)


FINDING_HEAD_RE = re.compile(r"^#### F(?P<n>\d+) — (?P<title>.+)$", re.MULTILINE)
FIELD_RE = re.compile(r"^- (?P<key>Severity|Evidence|Requirement|Impact|Recommendation): (?P<val>.+)$", re.MULTILINE)
VERDICT_RE = re.compile(r"^- F(?P<n>\d+) -> (?P<rest>.+)$", re.MULTILINE)


def parse_findings(text: str) -> tuple[dict, list[dict]]:
    """Seat-level header plus one dict per `#### F<n>` block."""
    seat = {"seat": "", "verdict": "", "gaps": ""}
    m = re.search(r"^### FINDINGS — Seat: (?P<seat>.+)$", text, re.MULTILINE)
    if m:
        seat["seat"] = m.group("seat").strip()
    for key, label in (("verdict", "Verdict"), ("gaps", "Confidence & gaps")):
        m = re.search(rf"^- {re.escape(label)}: (?P<v>.+)$", text, re.MULTILINE)
        if m:
            seat[key] = m.group("v").strip()
    heads = list(FINDING_HEAD_RE.finditer(text))
    findings = []
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[head.end():end]
        fields = {m.group("key").lower(): m.group("val").strip() for m in FIELD_RE.finditer(block)}
        findings.append(dict(title=head.group("title").strip(), **fields))
    return seat, findings


def parse_verdicts(text: str) -> dict[str, str]:
    return {f"F{m.group('n')}": m.group("rest").strip() for m in VERDICT_RE.finditer(text)}


def render_review(
    seats: list[tuple[dict, list[dict], dict[str, str]]],
) -> tuple[str, str, str, dict[str, list[str]]]:
    """seats: (seat_meta, findings, verdicts) in dispatch order.

    The fourth value maps each seat to the `F<n>` labels its findings became, so
    the conductor can disposition against the right numbers: `--seat` order
    silently renumbers every finding, and a mis-ordered mint sends 24
    dispositions to the wrong blocks.
    """
    summary, risks, blocks = [], [], []
    seat_ranges: dict[str, list[str]] = {}
    n = 0
    for meta, findings, verdicts in seats:
        summary.append(f"- {meta['seat']}: {meta['verdict']}")
        if meta["gaps"]:
            risks.append(f"- {meta['seat']}: {meta['gaps']}")
        labels: list[str] = []
        for local, f in enumerate(findings, start=1):
            n += 1
            labels.append(f"F{n}")
            evidence = f.get("evidence", "")
            if f"F{local}" in verdicts:
                evidence += " | Verified: " + verdicts[f"F{local}"]
            blocks.append("\n".join([
                f"### F{n} — {f['title']}",
                "",
                f"- Seat: {meta['seat']}",
                f"- Severity: `{f.get('severity', 'note')}`",
                f"- Evidence: {evidence}",
                f"- Requirement: {f.get('requirement', '')}",
                f"- Impact: {f.get('impact', '')}",
                f"- Recommendation: {f.get('recommendation', '')}",
                "- Disposition: `open`",
            ]))
        seat_ranges[meta["seat"]] = labels
    return ("\n".join(summary), "\n\n".join(blocks),
            "\n".join(risks) or "None recorded.", seat_ranges)


def _fill_section(text: str, heading: str, body: str) -> str:
    """Replace the comment placeholder under `## heading` with body."""
    pattern = re.compile(rf"(^## {re.escape(heading)}\n\n)<!--.*?-->\n", re.MULTILINE | re.DOTALL)
    return pattern.sub(lambda m: m.group(1) + body + "\n", text, count=1)


def cmd_record_review(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    src = Path(args.from_findings)
    seats = []
    names = list(args.seat) or sorted(p.stem for p in src.glob("*.md") if not p.name.endswith(".verdict.md"))
    for path in (src / f"{name}.md" for name in names):
        if not path.exists():
            print(f"orko: no findings file {path}", file=sys.stderr)
            return 2
        meta, findings = parse_findings(path.read_text(encoding="utf-8"))
        vpath = path.with_name(path.stem + ".verdict.md")
        verdicts = parse_verdicts(vpath.read_text(encoding="utf-8")) if vpath.exists() else {}
        seats.append((meta, findings, verdicts))
    if not seats:
        print(f"orko: no findings files under {src}", file=sys.stderr)
        return 2
    names = ", ".join(meta["seat"] for meta, _, _ in seats)
    summary, blocks, risks, seat_ranges = render_review(seats)
    code, out = _mint(ws, run, "review", args.role, args.title,
                      {"title": args.title, "status": "draft", "product_version": run["version"],
                       "reviews": list(args.reviews), "revision": args.revision,
                       "reviewer": f"orko ({names})", "reviewed_at": run["date"],
                       "approved_by": None, "approved_at": None},
                      ["ID", "Review", args.title, "draft", run["owner"]])
    if code != 0:
        return code
    if not out["resumed"]:
        path = Path(out["path"])
        text = path.read_text(encoding="utf-8")
        text = _fill_section(text, "Summary", summary)
        text = re.sub(r"### F1 — \[Finding\].*?(?=\n## )", lambda m: blocks + "\n", text, count=1, flags=re.DOTALL)
        text = _fill_section(text, "Unresolved risks and questions", risks)
        path.write_text(text, encoding="utf-8")
    print(json.dumps(dict(out, seats=seat_ranges), indent=2))
    return 0


def cmd_record_spec(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    code, out = _mint(ws, run, "spec", "spec", args.title,
                      {"title": args.title, "status": "draft",
                       "product_version": run["version"], "owner": run["owner"],
                       "approved_at": None, "supersedes": None},
                      ["ID", "Specification", args.title, "draft", run["owner"]])
    if code == 0:
        print(json.dumps(out, indent=2))
    return code


def cmd_record_plan(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    code, out = _mint(ws, run, "plan", "plan", args.title,
                      {"title": args.title, "status": "draft",
                       "product_version": run["version"],
                       "implements": [args.implements], "owner": run["owner"]},
                      ["ID", "Delivery plan", args.title, "draft", run["owner"]])
    if code == 0:
        print(json.dumps(out, indent=2))
    return code


def find_record(ws: Path, id_: str) -> Path | None:
    """The file an ID names, across the docs and code trees."""
    prefix = id_.split("-")[0]
    for rt in RECORD_TYPES.values():
        if rt.prefix != prefix:
            continue
        pattern = rt.subdir.replace("<v>", "*")
        hits = sorted((ws / rt.repo).glob(f"{pattern}/{id_}-*.md"))
        if hits:
            return hits[0]
    return None


def _guarded_edit(ws: Path, run: dict, path: Path, transform) -> int:
    """Rewrite a record in place, refusing when it carries edits the run never saw."""
    ledger = Path(run["ledger"])
    guard = overwrite_guard(ledger, ws, path)
    if guard:
        print(f"orko: {guard}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    new = transform(text)
    if new is None:
        return 2
    path.write_text(new, encoding="utf-8")
    return 0


def cmd_record_disposition(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    path = find_record(ws, args.review)
    if path is None:
        print(f"orko: no record {args.review}", file=sys.stderr)
        return 2

    def transform(text: str) -> str | None:
        # `(?!^### )` keeps the match inside this finding's own block: a plain
        # `.*?` runs past an already-dispositioned F1 and rewrites F2 instead.
        pattern = re.compile(
            rf"(^### {re.escape(args.finding)} — (?:(?!^### ).)*?- Disposition: `)open(`)",
            re.MULTILINE | re.DOTALL)
        new, n = pattern.subn(
            lambda m: m.group(1) + args.disposition + m.group(2), text, count=1)
        if n == 0:
            print(f"orko: {args.review} has no open finding {args.finding}", file=sys.stderr)
            return None
        return new
    return _guarded_edit(ws, run, path, transform)


def cmd_record_status(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    path = find_record(ws, args.id)
    if path is None:
        print(f"orko: no record {args.id}", file=sys.stderr)
        return 2
    return _guarded_edit(ws, run, path, lambda t: set_frontmatter(t, {"status": args.status}))


def cmd_record_amendment(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    path = find_record(ws, args.id)
    if path is None or "## Amendments" not in path.read_text(encoding="utf-8"):
        print(f"orko: {args.id} has no Amendments section", file=sys.stderr)
        return 2
    line = f"- {_dt.date.today().isoformat()}: {args.text}"
    return _guarded_edit(ws, run, path, lambda text: _append_after_heading_text(
        text, "## Amendments", line, table=False, blank_before=True))


def cmd_record_decision(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    code, out = _mint(ws, run, "decision", "decision", args.title,
                      {"title": args.title, "status": "proposed", "owner": run["owner"],
                       "decided_at": None, "supersedes": None, "superseded_by": None},
                      ["ID", args.title, "proposed", run["date"], "—"])
    if code == 0:
        print(json.dumps(out, indent=2))
    return code


def cmd_record_adr(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    code, out = _mint(ws, run, "adr", "adr", args.title,
                      {"title": args.title, "status": "proposed", "decided_at": None,
                       "supersedes": None, "superseded_by": None}, None)
    if code == 0:
        print(json.dumps(out, indent=2))
    return code


def cmd_record_research(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    code, out = _mint(ws, run, "research", "research", args.title,
                      {"title": args.title, "collected_at": run["date"]}, None)
    if code == 0:
        print(json.dumps(out, indent=2))
    return code


def _append_after_heading_text(text: str, heading: str, line: str, table: bool,
                               blank_before: bool = False) -> str:
    """Append `line` at the end of the section under `heading`: after the last
    `|` row when `table`, else after the last non-blank line of the section.

    The section ends at the next `## ` heading, so an append never spills into
    whatever follows.
    """
    lines = text.split("\n")
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    section = range(start + 1, end)
    if table:
        anchor = max(i for i in section if lines[i].startswith("|"))
    else:
        anchor = max((i for i in section if lines[i].strip()), default=start)
    lines.insert(anchor + 1, line)
    if blank_before:
        lines.insert(anchor + 1, "")
    return "\n".join(lines)


def _append_after_heading(path: Path, heading: str, line: str, table: bool) -> None:
    path.write_text(
        _append_after_heading_text(path.read_text(encoding="utf-8"), heading, line, table),
        encoding="utf-8")


def cmd_record_delivery_decision(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    ledger = Path(run["ledger"])
    plan = record_for(ledger, "plan", "plan")
    if plan is None:
        print("orko: no plan minted for this run", file=sys.stderr)
        return 2
    path = ws / plan["path"]
    guard = overwrite_guard(ledger, ws, path)
    if guard:
        print(f"orko: {guard}", file=sys.stderr)
        return 2
    heading = "## Delivery decisions"
    try:
        _append_after_heading(path, heading,
                              f"| {args.decision} | {args.rationale} |  |", table=True)
    except ValueError:
        # The plan-writer is told to delete unused template rows, so a plan that
        # lost the whole section is a plausible input, not a bug in the script.
        print(f"orko: {path} has no '{heading}' section", file=sys.stderr)
        return 2
    append_ledger(ledger, f"touched {rel(ws, path)}")
    return 0


def cmd_record_risk(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    readme = dossier_dir(ws, run["version"]) / "README.md"
    heading = "## Risks, blockers, and open decisions"
    try:
        _append_after_heading(readme, heading, f"- {args.text}", table=False)
    except ValueError:
        print(f"orko: {readme} has no '{heading}' section", file=sys.stderr)
        return 2
    append_ledger(Path(run["ledger"]), f"touched {rel(ws, readme)}")
    return 0


CHANGELOG_SECTIONS = ("Added", "Changed", "Fixed", "Removed", "Security")


def _insert_under(text: str, heading: str, line: str, within: str | None = None) -> str:
    """Record `line` under `heading`, creating the heading when absent.

    Idempotent, because `close` is rerunnable: a line already standing in the
    section is left alone rather than filed twice. Entries append after the
    section's last bullet, so `--changelog` order survives into the file and
    consecutive bullets stay a tight list with one blank line before whatever
    heading follows.

    `within` scopes the whole operation to one `## ` section: a changelog entry
    belongs under Unreleased, and an unscoped insert would land it in whatever
    released section happens to carry the same `### Added` heading first.
    """
    if within:
        head, sep, rest = text.partition(within + "\n")
        section, sep2, after = rest.partition("\n## ")
        section = _insert_under(section, heading, line)
        return head + sep + section + (sep2 + after if sep2 else "")
    lines = text.split("\n")
    if heading not in lines:
        # An empty section carries no newline of its own, so `rstrip` plus a
        # blank line would open the heading with two blank lines above it.
        body = text.rstrip("\n")
        lines = ((body + "\n\n" if body else "\n") + f"{heading}\n\n").split("\n")
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")),
               len(lines))
    block, body = line.split("\n"), lines[start + 1:end]
    if any(body[i:i + len(block)] == block for i in range(len(body) - len(block) + 1)):
        return "\n".join(lines)
    bullets = [i for i in range(start + 1, end) if lines[i].startswith("- ")]
    if bullets:
        at = bullets[-1] + 1
    else:
        at = start + 1
        if at >= len(lines) or lines[at].strip():
            lines.insert(at, "")
        at += 1
    lines.insert(at, line)
    if at + 1 >= len(lines) or lines[at + 1].strip():
        lines.insert(at + 1, "")
    return "\n".join(lines)


def _status_progress_line(ws: Path, topic: str, new_line: str) -> None:
    """Set this run's one bullet under `## In progress`, replacing any earlier one."""
    status = ws / "docs/STATUS.md"
    lines = status.read_text(encoding="utf-8").split("\n")
    for i, line in enumerate(lines):
        if line.startswith(f"- {topic}"):
            lines[i] = new_line
            break
    else:
        anchor = lines.index("## In progress")
        # the template has a blank line then an HTML comment under the heading;
        # insert after the comment so the bullet is not glued to it
        insert_at = anchor + 1
        while insert_at < len(lines) and (not lines[insert_at].strip() or lines[insert_at].startswith("<!--")):
            insert_at += 1
        # insert_at is now the section's first real line, or the next heading.
        # The bullet joins an existing list directly and stands off anything
        # else with a blank, so the next heading is never glued to it.
        lines.insert(insert_at, new_line)
        if insert_at + 1 >= len(lines) or not lines[insert_at + 1].startswith("- "):
            lines.insert(insert_at + 1, "")
    status.write_text("\n".join(lines), encoding="utf-8")


def cmd_record_close(args: argparse.Namespace) -> int:
    """Hand the run to a human: STATUS, both changelogs, the index, two PR bodies.

    Nothing here moves work to Recently completed. Acceptance is oiler's call,
    and a run that marked its own work done would be grading its own homework.
    """
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    entries = []
    for item in args.changelog:
        section, _, text = item.partition(":")
        if section.strip() not in CHANGELOG_SECTIONS or not text.strip():
            print(f"orko: --changelog must be '<{'|'.join(CHANGELOG_SECTIONS)}>: text'",
                  file=sys.stderr)
            return 2
        entries.append((section.strip(), text.strip()))
    ledger = Path(run["ledger"])
    # The PR bodies trace everything the run minted. STATUS and the changelogs
    # cite the work itself: a reader asking what shipped is not served by a
    # review or decision ID on a changelog line.
    ids = sorted(entry["id"] for entry in records(ledger) if entry["id"] != "-")
    id_text = ", ".join(sorted(entry["id"] for entry in records(ledger)
                               if entry["type"] in ("spec", "plan")))

    status = ws / "docs/STATUS.md"
    # The close date, not the run's init date: a build that opens on Monday and
    # closes on Friday is as of Friday.
    as_of = args.date or _dt.date.today().isoformat()
    status.write_text(set_frontmatter(status.read_text(encoding="utf-8"),
                                      {"as_of": as_of}), encoding="utf-8")
    _status_progress_line(ws, run["topic"], f"- {run['topic']} ({id_text}): awaiting acceptance")
    append_ledger(ledger, "touched docs/STATUS.md")

    # Refresh the artifact index from each record's own frontmatter: the row was
    # written when the record was minted, and `record status` has moved on since.
    readme = dossier_dir(ws, run["version"]) / "README.md"
    kinds = {"spec": "Specification", "plan": "Delivery plan", "review": "Review"}
    for entry in records(ledger):
        if entry["type"] in kinds:
            path = ws / entry["path"]
            update_index(readme, [entry["id"], kinds[entry["type"]],
                                  read_frontmatter_field(path, "title") or entry["id"],
                                  read_frontmatter_field(path, "status") or "draft",
                                  run["owner"]], entry["id"])
    append_ledger(ledger, f"touched {rel(ws, readme)}")

    for changelog in (ws / "code/CHANGELOG.md", dossier_dir(ws, run["version"]) / "CHANGELOG.md"):
        text = changelog.read_text(encoding="utf-8")
        for section, item in entries:
            text = _insert_under(text, f"### {section}", f"- {item} ({id_text})",
                                 within="## Unreleased")
        changelog.write_text(text, encoding="utf-8")
        append_ledger(ledger, f"touched {rel(ws, changelog)}")

    out = {}
    for repo in ("docs", "code"):
        template = ws / repo / ".github/PULL_REQUEST_TEMPLATE.md"
        body = template.read_text(encoding="utf-8") if template.exists() else "## Purpose\n\n## Artifacts\n"
        body = _insert_under(body, "## Purpose", args.summary)
        heading = next((line for line in body.split("\n") if line.startswith("## ")
                        and ("Artifacts" in line or "Traceability" in line)), None)
        if heading:
            body = _insert_under(body, heading, "\n".join(f"- {i}" for i in ids))
        path = Path(run["run_dir"]) / f"pr-{repo}.md"
        path.write_text(body, encoding="utf-8")
        out[f"pr_{repo}"] = str(path)
    print(json.dumps(out, indent=2))
    return 0


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)


def cmd_commit(args: argparse.Namespace) -> int:
    """Stage this run's own paths in one repo, commit them with the run's IDs
    and trailers, then re-hash what landed so the overwrite guard has a floor."""
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    repo = ws / args.repo
    ledger = Path(run["ledger"])
    staged: list[str] = []
    for entry in records(ledger):
        if entry["path"].startswith(args.repo + "/"):
            staged.append(entry["path"].removeprefix(args.repo + "/"))
    for path in touched(ledger):
        if path.startswith(args.repo + "/"):
            staged.append(path.removeprefix(args.repo + "/"))
    def keeps(path: str) -> bool:
        return ((repo / path).exists() and not Path(path).is_absolute()
                and ".." not in Path(path).parts)

    # A typo'd `--path` that silently vanished meant the file never committed and
    # nothing said so, so every dropped one is named on stderr.
    for path in args.path:
        if not keeps(path):
            print(f"orko: skipping {path} (missing, absolute, or outside {args.repo}/)",
                  file=sys.stderr)
    staged = [p for p in staged + list(args.path) if keeps(p)]
    if not staged:
        print(f"orko: nothing to stage in {args.repo}", file=sys.stderr)
        return 2
    result = _git(repo, "add", "--", *staged)
    if result.returncode != 0:
        print(f"orko: git add failed: {result.stderr.strip()}", file=sys.stderr)
        return 2
    if _git(repo, "diff", "--cached", "--quiet", "--", *staged).returncode == 0:
        print(f"orko: nothing changed in {args.repo}", file=sys.stderr)
        return 2
    ids = sorted({e["id"] for e in records(ledger) if e["id"] != "-"})
    message = args.message.rstrip() + "\n\n" + (f"Refs: {', '.join(ids)}\n" if ids else "")
    message += "\n" + "\n".join(run["trailers"]) + "\n"
    # `-- *staged` scopes the commit to orko's own paths: anything the user had
    # already staged in this repo stays staged rather than riding along under
    # orko's message and Refs line with no hash line to prove it.
    result = subprocess.run(["git", "-C", str(repo), "commit", "-q", "-F", "-", "--", *staged],
                            input=message, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"orko: git commit failed: {result.stderr.strip()}", file=sys.stderr)
        return 2
    for p in staged:
        append_ledger(ledger, f"hash {args.repo}/{p} {sha256_file(repo / p)}")
    print(json.dumps({"repo": args.repo, "commit": _git(repo, "rev-parse", "HEAD").stdout.strip(),
                      "staged": staged}, indent=2))
    return 0


def run_acceptance(cmd: str, cwd: Path) -> int:
    """The task's own acceptance command, run as written.

    The only `shell=True` in the script: the command is a shell line from a
    `tasks.md` the plan validator has already accepted, never a flag.
    """
    return subprocess.run(cmd, shell=True, cwd=str(cwd), check=False).returncode


# The Codex task prompt tells every delivery to map its requirement rows into
# this file, so a plan that never lists it under Files must not fail the check
# for obeying the prompt.
DELIVERY_ALWAYS_ALLOWED = ("docs/testing/README.md",)


def cmd_check_delivery(args: argparse.Namespace) -> int:
    """Judge one Codex delivery in code, not by reading its report.

    Each condition is one finding, so a test can remove exactly one and see
    exactly one test go red.
    """
    loaded = _load_run(args)
    if loaded is None:
        return 2
    ws, run = loaded
    task = _task_or_exit(run, args.task)
    if task is None:
        return 2
    base = _dispatched_base(_ledger_entries(Path(run["ledger"])), f"5.{args.task}")
    # No base means no recorded dispatch: there is no diff to judge, and
    # guessing one would grade somebody else's work.
    if base is None:
        print(f"orko: no `ledger 5.{args.task} dispatched --commit` line", file=sys.stderr)
        return 2
    code = ws / "code"
    findings: list[str] = []
    if _dirty(code):
        findings.append("tree-dirty: uncommitted or untracked files in code/")
    changed = [line for line in
               _git(code, "diff", "--name-only", f"{base}..HEAD").stdout.splitlines() if line]
    if not changed:
        findings.append("diff-empty: no commits since the dispatch base")
    outside = sorted(set(changed) - set(task["files"]) - set(DELIVERY_ALWAYS_ALLOWED))
    if changed and outside:
        findings.append("diff-outside-allowlist: " + ", ".join(outside))
    if task["acceptance"]:
        # The acceptance line is model-authored shell run with the conductor's
        # privileges. Printing it is the whole of the visibility this gets.
        print(f"acceptance: {task['acceptance']}")
        rc = run_acceptance(task["acceptance"], code)
        if rc != 0:
            findings.append(f"acceptance-failed: exit {rc}")
    for finding in findings:
        print(finding)
    return 1 if findings else 0


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

    p_cs = check_sub.add_parser("spec")
    p_cs.add_argument("id")
    p_cs.add_argument("--slug")
    p_cs.add_argument("--workspace")
    p_cs.add_argument("--require-plan", action="store_true")
    p_cs.set_defaults(func=cmd_check_spec)

    p_cd = check_sub.add_parser("delivery")
    p_cd.add_argument("--slug", required=True)
    p_cd.add_argument("--workspace")
    p_cd.add_argument("--task", type=int, required=True)
    p_cd.set_defaults(func=cmd_check_delivery)

    p_record = sub.add_parser("record", help="mint or update a scaffold record")
    record_sub = p_record.add_subparsers(dest="kind", required=True)
    for kind, func, extra in (("spec", cmd_record_spec, ()),
                              ("plan", cmd_record_plan, ("--implements",))):
        p = record_sub.add_parser(kind)
        p.add_argument("--slug", required=True)
        p.add_argument("--workspace")
        p.add_argument("--title", required=True)
        for flag in extra:
            p.add_argument(flag, required=True)
        p.set_defaults(func=func)

    p_review = record_sub.add_parser("review")
    p_review.add_argument("--slug", required=True)
    p_review.add_argument("--workspace")
    p_review.add_argument("--title", required=True)
    p_review.add_argument("--role", choices=["spec", "plan", "code", "analysis"], required=True)
    p_review.add_argument("--reviews", action="append", default=[])
    p_review.add_argument("--seat", action="append", default=[],
                          help="seat name, repeatable; sets the order findings render in")
    p_review.add_argument("--revision", required=True)
    p_review.add_argument("--from-findings", required=True)
    p_review.set_defaults(func=cmd_record_review)

    p = record_sub.add_parser("disposition")
    p.add_argument("--slug", required=True)
    p.add_argument("--workspace")
    p.add_argument("--review", required=True)
    p.add_argument("--finding", required=True)
    p.add_argument("--disposition", required=True,
                   choices=["accepted", "rejected", "resolved", "noted"])
    p.set_defaults(func=cmd_record_disposition)

    p = record_sub.add_parser("status")
    p.add_argument("--slug", required=True)
    p.add_argument("--workspace")
    p.add_argument("--id", required=True)
    p.add_argument("--status", required=True, choices=["draft", "in_review"])
    p.set_defaults(func=cmd_record_status)

    p = record_sub.add_parser("amendment")
    p.add_argument("--slug", required=True)
    p.add_argument("--workspace")
    p.add_argument("--id", required=True)
    p.add_argument("--text", required=True)
    p.set_defaults(func=cmd_record_amendment)

    for kind, func in (("decision", cmd_record_decision), ("adr", cmd_record_adr),
                       ("research", cmd_record_research)):
        p = record_sub.add_parser(kind)
        p.add_argument("--slug", required=True)
        p.add_argument("--workspace")
        p.add_argument("--title", required=True)
        p.set_defaults(func=func)

    p = record_sub.add_parser("delivery-decision")
    p.add_argument("--slug", required=True)
    p.add_argument("--workspace")
    p.add_argument("--decision", required=True)
    p.add_argument("--rationale", required=True)
    p.set_defaults(func=cmd_record_delivery_decision)

    p = record_sub.add_parser("risk")
    p.add_argument("--slug", required=True)
    p.add_argument("--workspace")
    p.add_argument("--text", required=True)
    p.set_defaults(func=cmd_record_risk)

    p = record_sub.add_parser("close")
    p.add_argument("--slug", required=True)
    p.add_argument("--workspace")
    p.add_argument("--summary", required=True)
    p.add_argument("--date", help="YYYY-MM-DD stamped as STATUS.md as_of (default: today)")
    p.add_argument("--changelog", action="append", default=[],
                   help="'<Added|Changed|Fixed|Removed|Security>: text', repeatable")
    p.set_defaults(func=cmd_record_close)

    p_prompt = sub.add_parser("prompt", help="emit a dispatch prompt")
    p_prompt.add_argument("kind", choices=sorted(PROMPT_SOURCES))
    p_prompt.add_argument("slug")
    p_prompt.add_argument("--lens")
    p_prompt.add_argument("--seat")
    p_prompt.add_argument("--question")
    p_prompt.add_argument("--context-file")
    p_prompt.add_argument("--task", type=int)
    p_prompt.add_argument("--attempt", choices=["fresh", "resume"], default="fresh")
    p_prompt.add_argument("--failure")
    p_prompt.add_argument("--workspace")
    p_prompt.set_defaults(func=cmd_prompt)

    p_escalations = sub.add_parser(
        "escalations", help="0 when there is nothing to escalate, 1 when there is")
    p_escalations.add_argument("slug")
    p_escalations.add_argument("--workspace")
    p_escalations.set_defaults(func=cmd_escalations)

    p_commit = sub.add_parser("commit", help="stage and commit this run's paths in one repo")
    p_commit.add_argument("repo", choices=["docs", "code"])
    p_commit.add_argument("--slug", required=True)
    p_commit.add_argument("--workspace")
    p_commit.add_argument("--message", required=True)
    p_commit.add_argument("--path", action="append", default=[],
                          help="extra repo-relative path to stage, repeatable")
    p_commit.set_defaults(func=cmd_commit)

    p_codex = sub.add_parser("codex", help="drive a background Codex job")
    codex_sub = p_codex.add_subparsers(dest="codex_command", required=True)
    p_wait = codex_sub.add_parser("wait")
    p_wait.add_argument("job_id")
    p_wait.add_argument("--slug", required=True)
    p_wait.add_argument("--workspace")
    p_wait.add_argument("--timeout-ms", type=int, default=1800000)
    p_wait.set_defaults(func=cmd_codex_wait)

    p_pre = sub.add_parser("preflight", help="check repos, branches, tooling, and record state")
    p_pre.add_argument("--slug", required=True)
    p_pre.add_argument("--workspace")
    p_pre.set_defaults(func=cmd_preflight)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
