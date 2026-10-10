"""Compare v0.1.2 and v0.1.3 `log` and `preflight` against oiler's 2026-10-10 MODELS.md; print a markdown scorecard.

usage: policy_compare.py OLD_SCRIPT NEW_SCRIPT OUT_DIR
"""
import json
import os
import subprocess
import sys
from pathlib import Path

old_script, new_script, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)

# The role table didn't change in v0.1.3, so every log case must keep v0.1.2's answer.
CASES = [
    ("scoped implementer", "implementer-scoped", "sonnet/medium", True),
    ("scoped implementer at high", "implementer-scoped", "sonnet/high", False),
    ("ordinary review", "reviewer", "opus/medium", True),
    ("ordinary review at low", "reviewer", "opus/low", False),
    ("security review", "reviewer-security", "opus/high", True),
    ("security review at medium", "reviewer-security", "opus/medium", False),
    ("ordinary re-review", "re-reviewer", "opus/medium", True),
    ("security re-review", "re-reviewer-security", "opus/high", True),
    ("security re-review at medium", "re-reviewer-security", "opus/medium", False),
    ("gap implementer", "implementer-gap", "opus/low", True),
    ("multifile implementer", "implementer-multifile", "opus/medium", True),
    ("final reviewer", "final-reviewer", "opus/high", True),
    ("final fixer", "final-fixer", "opus/medium", True),
]


def env_with(effort: str | None) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_EFFORT"}
    return {**env, "CLAUDE_EFFORT": effort} if effort else env


def ledger(tag: str, name: str) -> Path:
    home = out / tag / name / ".superpowers" / "sdd" / "plan"
    home.mkdir(parents=True, exist_ok=True)
    path = home / "progress.md"
    path.write_text("# SDD ledger — plan: docs/plan.md\n", encoding="utf-8")
    return path


def log_case(script: Path, tag: str, name: str, role: str, combo: str, effort: str | None) -> tuple[bool, bool]:
    model, eff = combo.split("/")
    task = "final" if role.startswith("final-") else "1"
    proc = subprocess.run([sys.executable, str(script), "log", "--ledger", str(ledger(tag, name)), "--task", task,
                           "--role", role, "--model", model, "--effort", eff, "--why", "policy case"],
                          capture_output=True, text=True, env=env_with(effort))
    return proc.returncode == 0, "warning: orchestrator effort" in proc.stderr


rows, results = [], []
for i, (case, role, combo, want) in enumerate(CASES):
    o, _ = log_case(old_script, "old", f"c{i}", role, combo, "high")
    n, _ = log_case(new_script, "new", f"c{i}", role, combo, "high")
    rows.append(f"| {case} | `{role}` {combo} | {'accept' if want else 'reject'} | "
                f"{'accept' if o else 'reject'} | {'accept' if n else 'reject'} | {'met' if n == want else 'NOT MET'} |")
    results.append({"case": case, "role": role, "combo": combo, "policy": want, "old": o, "new": n})

print("## log against MODELS.md (2026-10-10)\n")
print("| Case | Dispatch | Policy | v0.1.2 | v0.1.3 | Condition |\n|---|---|---|---|---|---|")
print("\n".join(rows))

proj = out / "proj"
(proj / "docs").mkdir(parents=True, exist_ok=True)
(proj / "docs" / "plan.md").write_text("### Task 1: Alpha\n", encoding="utf-8")
subprocess.run(["git", "-C", str(proj), "init", "-q", "-b", "master"], check=True)
subprocess.run(["git", "-C", str(proj), "-c", "user.email=t@x.invalid", "-c", "user.name=t", "commit", "-q",
                "--allow-empty", "-m", "init"], check=True)


def preflight(script: Path, effort: str | None) -> tuple[str, bool]:
    lines = subprocess.run([sys.executable, str(script), "preflight", "docs/plan.md"], cwd=proj,
                           capture_output=True, text=True, env=env_with(effort)).stdout.strip().splitlines()
    return lines[-1].split(": ", 1)[1], any(l.startswith("warning: orchestrator effort") for l in lines)


print("\n## Orchestrator effort\n")
print("| Session effort | Policy | v0.1.2 preflight | v0.1.3 preflight | v0.1.3 preflight warns | v0.1.3 log warns "
      "| Condition |\n|---|---|---|---|---|---|---|")
for effort in ("low", "medium", "high", "xhigh", "max", None):
    at_policy = effort in ("high", "xhigh", "max")
    old_status, _ = preflight(old_script, effort)
    new_status, new_warns = preflight(new_script, effort)
    _, log_warns = log_case(new_script, "new", f"effort-{effort}", "implementer-scoped", "sonnet/medium", effort)
    ok = new_status == "ok" and new_warns == (not at_policy) and log_warns == (not at_policy)
    print(f"| {effort or 'not set'} | {'run' if at_policy else 'run with warning'} | {old_status} | {new_status} | "
          f"{'yes' if new_warns else 'no'} | {'yes' if log_warns else 'no'} | {'met' if ok else 'NOT MET'} |")
    results.append({"effort": effort, "old_preflight": old_status, "new_preflight": new_status,
                    "new_preflight_warns": new_warns, "new_log_warns": log_warns})

(out / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
