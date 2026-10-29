# /// script
# requires-python = ">=3.10"
# ///
"""Replay every recorded invalid orko-review report through v0.1.0's and v0.1.1's parsers.

Usage: python3 -B replay.py OLD_SCRIPT NEW_SCRIPT ROOT OUT_JSON. The output holds counts, project names,
and run stamps only: the reports belong to private projects.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses look their module up here while the class is built
    spec.loader.exec_module(module)
    return module


old, new = load(sys.argv[1], "orko_review_old"), load(sys.argv[2], "orko_review_new")
root, out = Path(sys.argv[3]), Path(sys.argv[4])
rows = []
for report in sorted(p for p in root.rglob("*.invalid-*.md") if "reviews" in p.parts):
    text = report.read_text(encoding="utf-8", errors="replace")
    head = text.replace("\r\n", "\n").split("\n---\n", 1)[0]
    fields = dict(re.findall(r"^(lens|doc):[ \t]*(.*?)[ \t]*$", head, re.M))
    lens, doc = fields.get("lens", ""), fields.get("doc", "")
    _, old_errors = old.parse_report(text, lens, doc)
    findings, new_errors = new.parse_report(text, lens, doc)
    parts = report.parts
    rows.append({
        "project": parts[parts.index("projects") + 1] if "projects" in parts else parts[len(root.parts)],
        "run": report.parent.name, "lens": report.name.split(".")[0],
        "headings": len(re.findall(r"^### F-\d+ ", text, re.M)),
        "old_failed": bool(old_errors),
        "old_flagged_findings": len({m for e in old_errors for m in re.findall(r"^(F-\d+) ", e)}),
        "new_report_errors": len(new_errors), "new_indexed": len(findings),
        "new_malformed": sum(1 for f in findings if f.get("malformed")),
    })
passed = bool(rows) and all(
    r["old_failed"] and r["new_report_errors"] == 0 and r["new_indexed"] == r["headings"]
    and r["new_malformed"] == r["old_flagged_findings"] for r in rows)
out.write_text(json.dumps({"rows": rows, "pass": passed}, indent=2) + "\n", encoding="utf-8")
print(f"{len(rows)} reports, pass={passed}")
