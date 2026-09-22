#!/usr/bin/env python3
"""orko-sdd helper: preflight, dispatch logging, verification records, and the final report.

Standard library only (Python 3.10+). SKILL.md says when each subcommand runs.
The ledger is the one superpowers:subagent-driven-development keeps at
<repo>/.superpowers/sdd/<plan>/progress.md; its line formats are the same in 6.3.0 and 6.4.1.
"""
from __future__ import annotations

import argparse
import re
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
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
