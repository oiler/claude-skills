"""Compare v0.1.1 and v0.1.2 `log` and `preflight` against oiler's 2026-09-25 MODELS.md; print a markdown scorecard.

usage: policy_compare.py OLD_SCRIPT NEW_SCRIPT OUT_DIR
"""
import json
import os
import subprocess
import sys
from pathlib import Path

old_script, new_script, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)

# (case, role, model/effort, what MODELS.md 2026-09-25 says) — expected: accepted by policy?
CASES = [
    ("scoped implementer, new policy", "implementer-scoped", "sonnet/medium", True),
    ("scoped implementer, old policy", "implementer-scoped", "sonnet/high", False),
    ("ordinary review, new policy", "reviewer", "opus/medium", True),
    ("ordinary review, old policy", "reviewer", "opus/low", False),
    ("security review, new policy", "reviewer-security", "opus/high", True),
    ("security review at medium", "reviewer-security", "opus/medium", False),
    ("ordinary re-review, mirrors reviewer", "re-reviewer", "opus/medium", True),
    ("security re-review, mirrors reviewer", "re-reviewer-security", "opus/high", True),
    ("gap implementer, unchanged", "implementer-gap", "opus/low", True),
    ("multifile implementer, unchanged", "implementer-multifile", "opus/medium", True),
    ("final reviewer, unchanged", "final-reviewer", "opus/high", True),
    ("final fixer, unchanged", "final-fixer", "opus/medium", True),
]


def ledger(tag: str, name: str) -> Path:
    home = out / tag / name / ".superpowers" / "sdd" / "plan"
    home.mkdir(parents=True, exist_ok=True)
    path = home / "progress.md"
    path.write_text("# SDD ledger — plan: docs/plan.md\n", encoding="utf-8")
    return path


def run(script: Path, args: list[str], effort: str | None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_EFFORT"}
    if effort is not None:
        env["CLAUDE_EFFORT"] = effort
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=env)


def log_case(script: Path, tag: str, i: int, role: str, combo: str, effort: str = "high") -> tuple[bool, bool]:
    model, eff = combo.split("/")
    task = "final" if role.startswith("final-") else "1"
    proc = run(script, ["log", "--ledger", str(ledger(tag, f"c{i}-{effort}")), "--task", task, "--role", role,
                        "--model", model, "--effort", eff, "--why", "policy case"], effort)
    return proc.returncode == 0, "warning: orchestrator effort" in proc.stderr


rows, results = [], []
for i, (case, role, combo, want) in enumerate(CASES):
    o, _ = log_case(old_script, "old", i, role, combo)
    n, _ = log_case(new_script, "new", i, role, combo)
    ok = "met" if n == want else "NOT MET"
    rows.append(f"| {case} | `{role}` {combo} | {'accept' if want else 'reject'} | "
                f"{'accept' if o else 'reject'} | {'accept' if n else 'reject'} | {ok} |")
    results.append({"case": case, "role": role, "combo": combo, "policy": want, "old": o, "new": n})

print("## log against MODELS.md (2026-09-25)\n")
print("| Case | Dispatch | Policy | v0.1.1 | v0.1.2 | Condition |\n|---|---|---|---|---|---|")
print("\n".join(rows))

# Orchestrator effort: preflight on a real repo with a plan, and log's mid-run warning.
proj = out / "proj"
(proj / "docs").mkdir(parents=True, exist_ok=True)
(proj / "docs" / "plan.md").write_text("### Task 1: Alpha\n", encoding="utf-8")
subprocess.run(["git", "-C", str(proj), "init", "-q", "-b", "master"], check=True)
subprocess.run(["git", "-C", str(proj), "-c", "user.email=t@x.invalid", "-c", "user.name=t", "commit", "-q",
                "--allow-empty", "-m", "init"], check=True)
print("\n## Orchestrator effort\n")
print("| Session effort | Policy | v0.1.1 preflight | v0.1.2 preflight | v0.1.2 log warns | Condition |\n|---|---|---|---|---|---|")
for effort in ("low", "medium", "high", "xhigh", "max", None):
    want_ok = effort in ("high", "xhigh", "max")
    statuses = []
    for script in (old_script, new_script):
        proc = subprocess.run([sys.executable, str(script), "preflight", "docs/plan.md"], cwd=proj,
                              capture_output=True, text=True,
                              env={**{k: v for k, v in os.environ.items() if k != "CLAUDE_EFFORT"},
                                   **({"CLAUDE_EFFORT": effort} if effort else {})})
        statuses.append(proc.stdout.strip().splitlines()[-1].split(": ", 1)[1])
    _, warned = log_case(new_script, "new", 99, "implementer-scoped", "sonnet/medium", effort=effort) \
        if effort else (None, "warning: orchestrator effort is not set" in run(
            new_script, ["log", "--ledger", str(ledger("new", "unset")), "--task", "1", "--role",
                         "implementer-scoped", "--model", "sonnet", "--effort", "medium", "--why", "w"], None).stderr)
    ok = (statuses[1] == "ok") == want_ok and warned == (not want_ok)
    print(f"| {effort or 'not set'} | {'run' if want_ok else 'block'} | {statuses[0]} | {statuses[1]} | "
          f"{'yes' if warned else 'no'} | {'met' if ok else 'NOT MET'} |")
    results.append({"effort": effort, "old_preflight": statuses[0], "new_preflight": statuses[1], "new_log_warns": warned})

(out / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
