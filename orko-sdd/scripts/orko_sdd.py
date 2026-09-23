#!/usr/bin/env python3
"""orko-sdd helper: preflight, dispatch logging, verification records, and the final report.

Standard library only (Python 3.10+). SKILL.md says when each subcommand runs.
The ledger is the one superpowers:subagent-driven-development keeps at
<repo>/.superpowers/sdd/<plan>/progress.md; its line formats are the same in 6.3.0 and 6.4.1.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SDD_PIN = "6.4.1"
EFFORTS = ("low", "medium", "high")
MODELS = ("haiku", "sonnet", "opus", "fable")
NEXT_EFFORT = {"low": "medium", "medium": "high"}
SKILL_DIR = Path(__file__).resolve().parent.parent
LEDGER_IDENTITY = "# SDD ledger — plan:"
RELEASE_CRITICAL_MARKER = "orko-sdd: release-critical"

# Role -> allowed (model, effort) pairs, from ~/.claude/MODELS.md phases 5-6.
ROLE_TABLE: dict[str, tuple[tuple[str, str], ...]] = {
    "implementer-scoped": (("sonnet", "high"),),
    "implementer-gap": (("opus", "low"),),
    "implementer-multifile": (("opus", "medium"), ("opus", "high")),
    "implementer-ui": (("sonnet", "high"),),
    "implementer-ui-replication": (("opus", "medium"),),
    "reviewer": (("opus", "low"),),
    "re-reviewer": (("opus", "low"),),
    "fix-incomplete": (),  # resolved from the ledger in allowed_combos
    "fix-wrong-diagnosis": (("fable", "high"),),
    "fix-tier-up": (("opus", "medium"), ("opus", "high")),  # filtered in allowed_combos
    "final-reviewer": (("opus", "high"),),
    "final-fixer": (("opus", "medium"),),
}
RELEASE_CRITICAL_FINAL = (("fable", "high"),)

ROLE_SOURCE = {
    "implementer-scoped": "Implementer: tightly scoped task from the approved plan",
    "implementer-gap": "Implementer: minor local gap with one conventional reading",
    "implementer-multifile": "Implementer: multi-file feature or substantial refactor",
    "implementer-ui": "Implementer: frontend/UI from clear art direction",
    "implementer-ui-replication": "Implementer: high-fidelity UI replication or difficult visual debugging",
    "reviewer": "Per-task code reviewer",
    "re-reviewer": "Scoped re-review (CLAUDE.md: opus for scoped re-reviews)",
    "fix-incomplete": ("Fix failure caused by skipped files, incomplete execution or missing verification"
                       " (xhigh is reserved, so a high-effort failure goes to fix-tier-up)"),
    "fix-wrong-diagnosis": "Fix failure after thorough investigation produced a confident but wrong diagnosis",
    "fix-tier-up": "SDD fix rounds 4-5: at least one step above the stuck implementer",
    "final-reviewer": "Final review: ordinary / release-critical whole-branch review",
    "final-fixer": "SDD's single final-review fix dispatch",
}

DISPATCH_RE = re.compile(r"^Task (\d+(?:,\d+)*|final): dispatch (\S+) (\w+)/(\w+) — ")
TASK_ARG_RE = re.compile(r"\d+(?:,\d+)*|final")


def ledger_error(path: Path) -> str | None:
    """Refuse anything but a plan's SDD ledger: the subcommands are pre-approved, so their target is constrained."""
    resolved = path.resolve()
    if resolved.name != "progress.md" or resolved.parts[-4:-2] != (".superpowers", "sdd"):
        return f"refused: {path} is not an SDD plan ledger (.superpowers/sdd/<plan>/progress.md)"
    if not resolved.is_file():
        return f"refused: {path} does not exist; SDD's setup creates it"
    with resolved.open(encoding="utf-8", errors="replace") as fh:
        if not fh.readline().startswith(LEDGER_IDENTITY):
            return f"refused: {path} does not start with '{LEDGER_IDENTITY}'"
    return None


def append_line(path: Path, line: str) -> None:
    text = path.read_text(encoding="utf-8")
    lead = "\n" if text and not text.endswith("\n") else ""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{lead}{line}\n")


def last_implementer_dispatch(ledger_text: str, task: str) -> tuple[str, str] | None:
    found = None
    for line in ledger_text.splitlines():
        m = DISPATCH_RE.match(line)
        if m and task in m.group(1).split(",") and m.group(2).startswith(("implementer-", "fix-")):
            found = (m.group(3), m.group(4))
    return found


def rank(combo: tuple[str, str]) -> tuple[int, int]:
    return MODELS.index(combo[0]), EFFORTS.index(combo[1])


def marker_text(line: str) -> str:
    """A ledger line as the orchestrator meant it: bullets and backticks dropped."""
    line = line.strip()
    line = line[2:] if line.startswith("- ") else line
    return line.strip("`")


def allowed_combos(role: str, task: str, ledger_text: str) -> tuple[tuple[str, str], ...]:
    if role in ("fix-incomplete", "fix-tier-up"):
        prior = last_implementer_dispatch(ledger_text, task)
        if prior is None:
            return ()
        if role == "fix-incomplete":
            return ((prior[0], NEXT_EFFORT[prior[1]]),) if prior[1] in NEXT_EFFORT else ()
        return tuple(c for c in ROLE_TABLE[role] if rank(c) > rank(prior))
    if role == "final-reviewer" and RELEASE_CRITICAL_MARKER in map(marker_text, ledger_text.splitlines()):
        return RELEASE_CRITICAL_FINAL
    return ROLE_TABLE[role]


def combos_text(role: str) -> str:
    if role == "fix-incomplete":
        return "same model as the task's last implementer or fix dispatch, next effort up (low → medium → high)"
    if role == "fix-tier-up":
        return "opus/medium, opus/high; only above the task's last implementer or fix dispatch"
    if role == "final-reviewer":
        return "opus/high; fable/high when the ledger carries `orko-sdd: release-critical`"
    return ", ".join(f"{m}/{e}" for m, e in ROLE_TABLE[role])


def render_role_table() -> str:
    rows = ["| Role | Model/effort | MODELS.md row |", "|---|---|---|"]
    rows += [f"| `{role}` | {combos_text(role)} | {ROLE_SOURCE[role]} |" for role in ROLE_TABLE]
    return "\n".join(rows)


FLAGS = ("--release-critical",)
USAGE = "usage: /orko-sdd <plan-path> [--release-critical]"
FRONTMATTER_FIELD_RE = re.compile(r"^(name|effort):\s*(\S+)\s*$", re.M)
AGENT_INSTALL = f"ln -s {SKILL_DIR / 'agents'} ~/.claude/agents/orko-sdd"


def installed_sdd_version(home: Path) -> str | None:
    path = home / ".claude" / "plugins" / "installed_plugins.json"
    try:
        plugins = json.loads(path.read_text(encoding="utf-8")).get("plugins", {})
    except (OSError, ValueError):
        return None
    for key, entries in plugins.items():
        if key.startswith("superpowers@") and entries:
            return entries[0].get("version")
    return None


def git_out(cwd: Path, *args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def project_agent_dirs(cwd: Path) -> list[Path]:
    """.claude/agents from cwd up to the repository root, plus the main checkout's when cwd is a worktree."""
    start = cwd.resolve()
    top = git_out(start, "rev-parse", "--show-toplevel")
    stop = Path(top).resolve() if top else start
    dirs = []
    for directory in (start, *start.parents):
        dirs.append(directory / ".claude" / "agents")
        if directory == stop:
            break
    common = git_out(start, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common:
        dirs.append(Path(common).resolve().parent / ".claude" / "agents")
    return dirs


def installed_agents(*roots: Path) -> dict[str, str]:
    """Map orko-sdd agent name -> effort, scanning as Claude Code does: recursively, through symlinks."""
    found: dict[str, str] = {}
    seen: set[str] = set()
    for root in roots:
        for dirpath, dirs, files in os.walk(root, followlinks=True):
            real = os.path.realpath(dirpath)
            if real in seen:
                dirs[:] = []
                continue
            seen.add(real)
            for name in files:
                if not name.endswith(".md"):
                    continue
                try:
                    text = (Path(dirpath) / name).read_text(encoding="utf-8")
                except OSError:
                    continue
                parts = text.split("---", 2)
                if not text.startswith("---") or len(parts) < 3:
                    continue
                fields = dict(FRONTMATTER_FIELD_RE.findall(parts[1]))
                if fields.get("name", "").startswith("orko-sdd-"):
                    found[fields["name"]] = fields.get("effort", "")
    return found


def preflight_lines(argv: list[str], home: Path, cwd: Path) -> list[str]:
    out: list[str] = []
    problems: list[str] = []
    flags = [a for a in argv if a.startswith("--")]
    positionals = [a for a in argv if not a.startswith("--")]
    unknown = [f for f in flags if f not in FLAGS]
    if unknown:
        problems.append(f"unknown flag(s): {' '.join(unknown)}; {USAGE}")
    if len(positionals) != 1:
        problems.append(f"expected one plan path, got {len(positionals)} "
                        f"(wrap a path with spaces in quotes); {USAGE}")
    else:
        plan = (cwd / positionals[0]).resolve()
        out.append(f"plan: {plan}")
        if not plan.is_file():
            problems.append(f"plan not found: {plan}")
    known = [f for f in flags if f in FLAGS]
    out.append(f"flags: {' '.join(known) or 'none'}")

    version = installed_sdd_version(home)
    out.append(f"sdd: {version or 'not found'}")
    if version is None:
        problems.append("superpowers plugin not found in ~/.claude/plugins/installed_plugins.json")
    elif version != SDD_PIN:
        out.append(f"warning: orko-sdd was written against SDD {SDD_PIN}; installed {version}. "
                   "Check that SKILL.md's changes still apply")

    agents = installed_agents(home / ".claude" / "agents", *project_agent_dirs(cwd))
    wanted = [f"orko-sdd-{e}" for e in EFFORTS]
    present = [a for a, e in zip(wanted, EFFORTS) if agents.get(a) == e]
    out.append(f"agents: {', '.join(present) or 'none'}")
    if len(present) < len(wanted):
        missing = ", ".join(a for a in wanted if a not in present)
        problems.append(f"missing agent(s): {missing}; install with: {AGENT_INSTALL}")

    if git_out(cwd, "rev-parse", "--verify", "--quiet", "refs/heads/master") is not None:
        out.append("base-branch: master")
    elif git_out(cwd, "rev-parse", "--verify", "--quiet", "refs/heads/main") is not None:
        out.append("base-branch: main")
    else:
        problems.append(f"no master or main branch in {cwd} (is it a git repository?)")

    out.append(f"final-review: {'fable/high' if '--release-critical' in known else 'opus/high'}")
    out += [f"problem: {p}" for p in problems]
    out.append("STATUS: blocked" if problems else "STATUS: ok")
    return out


def cmd_preflight(argv: list[str]) -> int:
    try:
        lines = preflight_lines(argv, Path.home(), Path.cwd())
    except Exception as exc:  # the injection aborts the whole invocation on a nonzero exit
        lines = [f"problem: preflight crashed: {exc!r}", "STATUS: blocked"]
    print("\n".join(lines))
    return 0


VERIFY_TAIL_LINES = 40


def one_line(text: str) -> str:
    """Flatten text for a ledger field: no newlines, and no em dash that would shift the Verify columns."""
    return " ".join(text.split()).replace("—", "-")


def cmd_verify(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    if err := ledger_error(ledger):
        print(err, file=sys.stderr)
        return 2
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        print("refused: give the command you ran after --", file=sys.stderr)
        return 2
    workspace = ledger.resolve().parent
    output = Path(args.output).resolve()
    if output.parent != workspace:
        print(f"refused: --output must be a file directly in the SDD workspace ({workspace})", file=sys.stderr)
        return 2
    if output == ledger.resolve():
        print("refused: --output is the ledger itself; redirect the command into its own file", file=sys.stderr)
        return 2
    try:
        lines = output.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lines = ["(output file missing)"]
    tail = next((one_line(line) for line in reversed(lines) if line.strip()), "(no output)")[:120]
    # One argument is a single-quoted shell command line: record it as written, not re-quoted.
    shown = cmd[0] if len(cmd) == 1 else shlex.join(cmd)
    append_line(ledger, f"Verify: {one_line(shown)} — exit {args.exit} — {tail}")
    print("\n".join(lines[-VERIFY_TAIL_LINES:]))
    return 0


LEDGER_PLAN_RE = re.compile(r"^# SDD ledger — plan: (.+)$")
PLAN_TASK_RE = re.compile(r"^#{2,4} Task (\d+):\s*(.*)$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
TASK_LINE_RE = re.compile(r"^Task (\d+): ")
RULING_RE = re.compile(r"\bRuling(?: \(.*?\))?:\s*(.*)$")
COMPLETE_RE = re.compile(
    r"^Task (\d+(?:,\d+)*|final): (?:\w+ )?complete \(commits ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})(.*)$")
SKIPPED_RE = re.compile(r"^Task (\d+): skipped — (.+)$")
PARKED_RE = re.compile(r"^Task (\d+|final): parked — (.+)$")
MINOR_RE = re.compile(r"^Task (\d+): minor \(deferred\)")
VERIFY_RE = re.compile(r"^Verify: (.+?) — exit (-?\d+) — (.*)$")
PARKED_COUNT_RE = re.compile(r"(\d+) parked")
REPORT_LINE_CAP = 40
RECOMMENDED_RESERVE = 3


@dataclass
class Ledger:
    plan: str | None = None
    seen: list[str] = field(default_factory=list)
    complete: dict[str, tuple[str, str, int]] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    models: dict[str, list[str]] = field(default_factory=dict)
    parked: list[tuple[str, str]] = field(default_factory=list)
    minors: int = 0
    followups: list[str] = field(default_factory=list)
    rulings: list[tuple[str, str, str]] = field(default_factory=list)
    verifies: list[tuple[str, str, str]] = field(default_factory=list)


def parse_ledger(text: str) -> Ledger:
    """Read an orchestrator-written ledger. SDD's lines are freeform, so unknown lines are ignored."""
    led = Ledger()
    for raw in text.splitlines():
        line = raw.strip()
        line = line[2:] if line.startswith("- ") else line
        if m := LEDGER_PLAN_RE.match(line):
            led.plan = m.group(1).strip()
            continue
        if dispatch := DISPATCH_RE.match(line):
            combo = f"{dispatch.group(3)}/{dispatch.group(4)}"
            for task in dispatch.group(1).split(","):
                combos = led.models.setdefault(task, [])
                if combo not in combos:
                    combos.append(combo)
                if task != "final" and task not in led.seen:
                    led.seen.append(task)
            continue
        # SDD asks for every ruling, in order: variants count and repeats are kept.
        # A deferred minor or a Verify line that mentions "Ruling:" is not one; a parked line's is read below.
        if (not (MINOR_RE.match(line) or VERIFY_RE.match(line) or PARKED_RE.match(line))
                and (m := RULING_RE.search(line)) and m.group(1).strip()):
            led.rulings.append(split_ruling(m.group(1).strip()))
        if (m := TASK_LINE_RE.match(line)) and m.group(1) not in led.seen:
            led.seen.append(m.group(1))
        if m := COMPLETE_RE.match(line):
            parked = PARKED_COUNT_RE.search(m.group(4))
            for task in m.group(1).split(","):
                led.complete[task] = (m.group(2), m.group(3), int(parked.group(1)) if parked else 0)
                if task != "final" and task not in led.seen:
                    led.seen.append(task)
        elif m := SKIPPED_RE.match(line):
            led.skipped[m.group(1)] = m.group(2)
        elif m := PARKED_RE.match(line):
            finding = m.group(2)
            # The Ruling column names the parked finding, which the text after "Ruling:" never does.
            if (r := RULING_RE.search(finding)) and r.group(1).strip():
                finding = finding[:r.start()].rstrip().removesuffix("—").rstrip()
                led.rulings.append((f"parked: {finding}",
                                    *detail_and_cost([p.strip() for p in r.group(1).strip().split(" — ")])))
            led.parked.append((m.group(1), finding))
        elif MINOR_RE.match(line):
            led.minors += 1
        elif line.startswith("Follow-up"):
            led.followups.append(line)
        elif m := VERIFY_RE.match(line):
            led.verifies.append((m.group(1), m.group(2), m.group(3)))
    return led


def split_ruling(text: str) -> tuple[str, str, str]:
    parts = [p.strip() for p in text.split(" — ")]
    return (parts[0], *detail_and_cost(parts[1:]))


def detail_and_cost(rest: list[str]) -> tuple[str, str]:
    """The parts of a ruling after its <what>, as (detail, cost)."""
    cost = ""
    # SDD 6.4.1 writes plain rulings with no labels at all: <what> — <why> — <cost>.
    # Only fall back to positional cost when no part carries a "why:" or "cost if wrong"
    # label — a labeled why whose own text contains " — " must not donate its tail to cost.
    if len(rest) >= 2 and not any(p.lower().startswith(("why:", "cost if wrong")) for p in rest):
        rest, cost = rest[:-1], rest[-1]
    detail: list[str] = []
    for part in rest:
        lower = part.lower()
        if lower.startswith("cost if wrong"):
            cost = part.split(":", 1)[1].strip() if ":" in part else part
        else:
            detail.append(part[4:].strip() if lower.startswith("why:") else part)
    return " — ".join(detail), cost


def plan_tasks(plan: str | None, repo: Path, problems: list[str] | None = None) -> list[tuple[str, str]]:
    """The plan's H2-H4 `Task N:` headings outside code fences; the first occurrence of each N wins.

    A set-but-unreadable plan is tolerated (never-dispatched tasks just don't show up in
    Done), but it's noted in `problems` when the caller wants to surface that to oiler.
    """
    if not plan:
        return []
    path = Path(plan)
    path = path if path.is_absolute() else repo / path
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        if problems is not None:
            problems.append(f"- plan not readable: {path}; tasks never dispatched are not listed")
        return []
    tasks: dict[str, str] = {}
    fence = None
    for line in text.splitlines():
        if m := FENCE_RE.match(line):
            marker = m.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and line.strip() == marker:
                fence = None
            continue
        if fence is None and (m := PLAN_TASK_RE.match(line)) and m.group(1) not in tasks:
            tasks[m.group(1)] = m.group(2).strip()
    return list(tasks.items())


def commit_count(repo: Path, a: str, b: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "rev-list", "--count", f"{a}..{b}"],
                          capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "?"


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_report(ledger_path: Path, plan_override: str | None, repo: Path) -> str:
    led = parse_ledger(ledger_path.read_text(encoding="utf-8"))
    plan_problems: list[str] = []
    tasks = plan_tasks(plan_override or led.plan, repo, plan_problems)
    titles = dict(tasks)
    order = [n for n, _ in tasks] + sorted((n for n in led.seen if n not in titles), key=int)

    done = []
    for n in order:
        commits = "—"
        if n in led.skipped:
            status = f"skipped — {led.skipped[n]}"
        elif n in led.complete:
            a, b, parked = led.complete[n]
            status = f"complete ({parked} parked)" if parked else "complete"
            commits = f"{a}..{b} ({commit_count(repo, a, b)})"
        elif n in led.seen:
            status = "in progress"
        else:
            status = "not started"
        label = f"{n}. {titles[n]}" if titles.get(n) else n
        models = ", ".join(led.models.get(n, [])) or "—"
        done.append(f"| {cell(label)} | {cell(status)} | {commits} | {models} |")
    if "final" in led.models or "final" in led.complete:
        status, commits = "dispatched", "—"
        if "final" in led.complete:
            a, b, parked = led.complete["final"]
            status = f"complete ({parked} parked)" if parked else "complete"
            commits = f"{a}..{b} ({commit_count(repo, a, b)})"
        models = ", ".join(led.models.get("final", [])) or "—"
        done.append(f"| final review | {status} | {commits} | {models} |")

    decided = [f"| {' | '.join(cell(p) or '—' for p in r)} |" for r in led.rulings]
    followups = list(plan_problems) + [f"- Task {n} skipped: {reason}" for n, reason in led.skipped.items()]
    if led.minors:
        followups.append(f"- {led.minors} deferred minor finding(s): see {ledger_path}")
    followups += [f"- Task {n} parked: {text}" for n, text in led.parked]
    followups += [f"- {line}" for line in led.followups]
    verified = [f"| {cell(c)} | {e} | {cell(t)} |" for c, e, t in led.verifies]

    done_block = ["## Done", "| Task | Status | Commits | Models |", "|---|---|---|---|", *done, ""]
    verified_block = ["## Verified", "| Command | Exit | Last line |", "|---|---|---|",
                      *(verified or ["| none run | — | — |"]), ""]
    # Recommended, the one section the orchestrator writes, comes last so its edit can't swallow script text.
    recommended = ["## Recommended",
                   "<!-- orchestrator: at most 3 items, only ones that change what oiler does next -->"]
    followups = followups or ["- none"]
    # Decided is exempt from the cap (SDD: every ruling reaches oiler); Follow-up gives way.
    budget = REPORT_LINE_CAP - (len(done_block) + 2 + len(recommended) + RECOMMENDED_RESERVE
                                + len(verified_block))
    if len(followups) > max(budget, 1):
        keep = max(budget - 1, 0)
        followups = followups[:keep] + [f"- +{len(followups) - keep} more in {ledger_path}"]

    return "\n".join([
        *done_block,
        "## Decided", "| Ruling | Detail | Cost if wrong |", "|---|---|---|",
        *(decided or ["| none | — | — |"]), "",
        "## Follow-up", *followups, "",
        *verified_block,
        *recommended,
    ])


def cmd_report(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    if err := ledger_error(ledger):
        print(err, file=sys.stderr)
        return 2
    print(render_report(ledger, args.plan, Path(args.repo)))
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    if err := ledger_error(ledger):
        print(err, file=sys.stderr)
        return 2
    if not TASK_ARG_RE.fullmatch(args.task):
        print("refused: --task must be a task number, a comma-separated batch such as 3,4,5, "
              f"or 'final'; got {args.task!r}", file=sys.stderr)
        return 2
    why = " ".join(args.why.split())
    if not why:
        print("refused: --why is empty", file=sys.stderr)
        return 2
    allowed = allowed_combos(args.role, args.task.split(",")[0], ledger.read_text(encoding="utf-8"))
    suffix = ""
    if (args.model, args.effort) not in allowed:
        if not args.override:
            options = (", ".join(f"{m}/{e}" for m, e in allowed)
                       or "nothing after this task's last implementer dispatch")
            print(f"rejected: {args.role} allows {options}; choose again (see SKILL.md's fix-loop table), "
                  "or pass --override with the reason in --why", file=sys.stderr)
            return 2
        suffix = " [override]"
    line = f"Task {args.task}: dispatch {args.role} {args.model}/{args.effort} — {why}{suffix}"
    append_line(ledger, line)
    print(f"{line}\nsubagent_type: orko-sdd-{args.effort}\nmodel: {args.model}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orko_sdd.py", description="orko-sdd helper")
    sub = parser.add_subparsers(dest="command", required=True)

    log = sub.add_parser("log", help="validate a dispatch against the role table and append it to the ledger")
    log.add_argument("--ledger", required=True)
    log.add_argument("--task", required=True, help="task number, comma-separated batch, or 'final'")
    log.add_argument("--role", required=True, choices=list(ROLE_TABLE))
    log.add_argument("--model", required=True, choices=MODELS)
    log.add_argument("--effort", required=True, choices=EFFORTS)
    log.add_argument("--why", required=True)
    log.add_argument("--override", action="store_true")
    log.set_defaults(func=cmd_log)

    verify = sub.add_parser("verify", help="record a test or lint command's exit code and last output line")
    verify.add_argument("--ledger", required=True)
    verify.add_argument("--exit", type=int, required=True, help="the command's exit code, from $?")
    verify.add_argument("--output", required=True, help="the command's output file, in the SDD workspace")
    verify.add_argument("cmd", nargs=argparse.REMAINDER, help="-- then the command as it was run")
    verify.set_defaults(func=cmd_verify)

    report = sub.add_parser("report", help="build the final report from the ledger and git")
    report.add_argument("--ledger", required=True)
    report.add_argument("--plan", help="plan path; defaults to the one on the ledger's first line")
    report.add_argument("--repo", default=".", help="repository for commit counts")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["preflight"]:
        # Raw args: argparse exits 2 on an unknown flag, and preflight must always exit 0.
        return cmd_preflight(argv[1:])
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
