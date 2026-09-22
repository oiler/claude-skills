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
import subprocess
import sys
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


def allowed_combos(role: str, task: str, ledger_text: str) -> tuple[tuple[str, str], ...]:
    if role in ("fix-incomplete", "fix-tier-up"):
        prior = last_implementer_dispatch(ledger_text, task)
        if prior is None:
            return ()
        if role == "fix-incomplete":
            return ((prior[0], NEXT_EFFORT[prior[1]]),) if prior[1] in NEXT_EFFORT else ()
        return tuple(c for c in ROLE_TABLE[role] if rank(c) > rank(prior))
    if role == "final-reviewer" and RELEASE_CRITICAL_MARKER in ledger_text.splitlines():
        return RELEASE_CRITICAL_FINAL
    return ROLE_TABLE[role]


def combos_text(role: str) -> str:
    if role == "fix-incomplete":
        return "same model as the task's last implementer dispatch, next effort up (low → medium → high)"
    if role == "fix-tier-up":
        return "opus/medium, opus/high; only above the task's last implementer dispatch"
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
