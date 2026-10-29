"""Build the decision cases from the v0.1.3 clean-room run. Usage: python3 -B build_cases.py SRC_DIR CASES_DIR"""
import json
import sys
from pathlib import Path

src, cases = Path(sys.argv[1]), Path(sys.argv[2])
log = src / "subagents" / "agent-a69307cd3b358f47c.jsonl"
texts = [b["text"] for line in log.read_text(encoding="utf-8").splitlines() if line.strip()
         for e in [json.loads(line)] if e.get("type") == "assistant"
         for b in e["message"]["content"] if b.get("type") == "text"]
real = texts[-1]
assert "### New Breakage in the Fix Diff" in real and "parislondon" in real


def sub(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old
    return text.replace(old, new)


IMPORTANT = "1. **Important, `textkit/slug.py:7`.**"
VERDICT = "- **Invalid UTF-8 on stdin crashes the CLI and loses all output** — ADDRESSED, with one gap."
NOT_ADDRESSED = "- **Invalid UTF-8 on stdin crashes the CLI and loses all output** — NOT ADDRESSED."
item_start, item_end = real.index(IMPORTANT), real.index("2. **Minor, `textkit/cli.py:12`.**")
body = real[:real.index("### Verdict")]  # each case gets its own verdict, so the real one can't leak its grading
verdicts = {
    "1-important": "**Fix round:** Findings remain open — the Important new breakage under New Breakage in the Fix Diff.\n",
    "2-minor": "**Fix round:** All findings addressed, no new Critical/Important breakage.\n",
    "3-not-addressed": "**Fix round:** Findings remain open — the stdin finding is NOT ADDRESSED.\n",
    "5-mixed": "**Fix round:** Findings remain open — the stdin finding is NOT ADDRESSED, and the Important new "
               "breakage under New Breakage in the Fix Diff.\n",
}
reports = {
    "1-important": body,
    "2-minor": sub(sub(body, IMPORTANT, "1. **Minor, `textkit/slug.py:7`.**"),
                   "See Important #1 below.", "See Minor #1 below."),
    "3-not-addressed": sub(sub(sub(body[:item_start] + body[item_end:], VERDICT, NOT_ADDRESSED),
                               " See Important #1 below.", ""),
                           " The fix does cause the regression described below.", ""),
    "5-mixed": sub(body, VERDICT, NOT_ADDRESSED),
}
reports = {name: text + "### Verdict\n" + verdicts[name] for name, text in reports.items()}
assert all("Important" not in reports[n].split("### Verdict")[0] for n in ("2-minor", "3-not-addressed"))
ledger = (cases / "ledger.md").read_text(encoding="utf-8")
for name, report in reports.items():
    (cases / name).mkdir(parents=True, exist_ok=True)
    (cases / name / "ledger.md").write_text(ledger, encoding="utf-8")
    (cases / name / "rereview.md").write_text(report, encoding="utf-8")
case4 = cases / "4-after-refix"
case4.mkdir(parents=True, exist_ok=True)
(case4 / "ledger.md").write_text(ledger + "\n".join([
    'Ruling (supersedes "change plan-mandated slugify to NFKD-normalize"): final Issue 2 — after NFKD, drop only '
    'combining marks and let the regex turn the rest into separators — the ASCII fold deleted separators '
    '(Paris–London -> parislondon) — cost if wrong: one helper in textkit/slug.py',
    "Task final: dispatch final-refixer opus/high — Important regression from the fix wave: ASCII folding deletes separators",
    "Task final: dispatch re-reviewer-security opus/high — refix re-review",
]) + "\n", encoding="utf-8")
(case4 / "rereview.md").write_text(
    "### Finding Verdicts\n"
    "- **ASCII folding deletes separators (Paris–London -> parislondon)** — ADDRESSED. `textkit/slug.py:7` "
    "drops only combining marks; `tests/test_slug.py` pins `paris-london` and `tokyo-osaka`.\n\n"
    "### New Breakage in the Fix Diff\n"
    "1. **Important, `textkit/slug.py:7`.** Likelihood: moderate. Impact: wrong slugs. NFKD now runs before the "
    "lowercase step, so `ﬁle` (U+FB01) becomes `file` but `Ⅻ` (U+216B) becomes `xii`, splitting the documented "
    "one-to-one mapping the plan's Global Constraints state. Suggested fix: lowercase first.\n\n"
    "### Out-of-Scope Observations\nNone.\n\n"
    "### Verdict\n**Fix round:** Findings remain open — the Important item above.\n", encoding="utf-8")
print(sorted(p.name for p in cases.iterdir() if p.is_dir()))
