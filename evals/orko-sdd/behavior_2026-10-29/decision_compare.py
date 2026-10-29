"""Decision comparison, orko-sdd v0.1.3 vs v0.1.4. Usage: python3 -B decision_compare.py OLD_SKILL NEW_SKILL SDD_DIR CASES OUT_JSON"""
import json
import re
import subprocess
import sys
from pathlib import Path

old_skill, new_skill, sdd, cases, out = (Path(a) for a in sys.argv[1:6])
RUNS = 3
QUESTION = """You are the orchestrator of an /orko-sdd run. The superpowers subagent-driven-development skill, its re-review template, and the orko-sdd skill below are loaded in your session, and orko-sdd wins where they conflict. The ledger and the report of the re-review you just received are below. Decide what you do next, up to and including any next dispatch.
Reply with only these lines, in order, nothing else:
LEDGER: <each line you append to the ledger, one per LEDGER line>
LOG: <each orko_sdd.py log command you run, in full>
FINDINGS-SENT: <one line per finding you send in a fix dispatch, if you dispatch one>"""


def prompt(skill: Path, case: Path) -> str:
    parts = [("superpowers subagent-driven-development SKILL.md", sdd / "SKILL.md"),
             ("superpowers re-review-prompt.md", sdd / "re-review-prompt.md"),
             ("orko-sdd SKILL.md", skill), ("ledger (progress.md)", case / "ledger.md"),
             ("re-review report you just received", case / "rereview.md")]
    body = "\n\n".join(f"===== {name} =====\n{path.read_text(encoding='utf-8')}" for name, path in parts)
    return f"{body}\n\n===== your task =====\n{QUESTION}"


def lines(text: str, tag: str) -> list[str]:
    return [l.split(":", 1)[1].strip() for l in text.splitlines() if l.strip().startswith(f"{tag}:")]


def grade(case: str, arm: str, text: str) -> bool:
    ledger, logs, sent = lines(text, "LEDGER"), lines(text, "LOG"), lines(text, "FINDINGS-SENT")
    refix = any(re.search(r"--role final-refixer\b", l) and "--model opus" in l and "--effort high" in l for l in logs)
    parked = any(l.startswith("Task final: parked") for l in ledger)
    deferred = any(l.startswith("Task final: minor (deferred)") for l in ledger)
    supersedes = any(l.startswith("Ruling (supersedes") for l in ledger)
    if arm == "v0.1.3":
        return {"1-important": parked and not refix, "2-minor": deferred and not refix,
                "3-not-addressed": parked and not refix, "5-mixed": parked and not refix}[case]
    return {"1-important": supersedes and refix,
            "2-minor": deferred and not refix,
            "3-not-addressed": parked and not refix,
            "4-after-refix": parked and not refix,
            "5-mixed": refix and parked and bool(sent) and not any("UTF-8" in s or "stdin" in s for s in sent)}[case]


results = []
for case in sorted(p for p in cases.iterdir() if p.is_dir()):
    for arm, skill in (("v0.1.3", old_skill), ("v0.1.4", new_skill)):
        if arm == "v0.1.3" and case.name == "4-after-refix":
            continue
        for run in range(RUNS):
            proc = subprocess.run(["claude", "-p", "--model", "opus", "--effort", "high", "--tools", "",
                                   "--output-format", "json"], input=prompt(skill, case),
                                  capture_output=True, text=True, timeout=900)
            data = json.loads(proc.stdout or "{}")
            text = data.get("result", "")
            results.append({"case": case.name, "arm": arm, "run": run + 1, "pass": grade(case.name, arm, text),
                            "cost_usd": data.get("total_cost_usd"), "output": text})
            print(case.name, arm, run + 1, results[-1]["pass"], flush=True)


def passes(case: str, arm: str) -> int:
    return sum(r["pass"] for r in results if r["case"] == case and r["arm"] == arm)


need = {"1-important": 3, "4-after-refix": 3, "5-mixed": 3, "2-minor": 2, "3-not-addressed": 2}
verdict = all(passes(c, "v0.1.4") >= n for c, n in need.items()) and passes("1-important", "v0.1.3") >= 2
out.write_text(json.dumps({"pass": verdict, "results": results}, indent=2) + "\n", encoding="utf-8")
print(f"pass={verdict}")
