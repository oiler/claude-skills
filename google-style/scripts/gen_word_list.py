#!/usr/bin/env python3
# gen_word_list.py — regenerate references/word-list.md from data/word_list.json.
# Run with: python3 gen_word_list.py
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Owns the write of references/word-list.md.

The reference page is generated rather than authored so the checker's data and the
documentation cannot drift. A test in test_style_check.py fails if the committed
page differs from what this script emits.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "word_list.json"
OUTPUT_PATH = HERE.parent / "references" / "word-list.md"

PIN = ("Source: Google developer documentation style guide, "
       "https://developers.google.com/style — pinned to the guide's last update, "
       "2026-07-07. Mirrored 2026-08-18.")
ATTRIBUTION = ("Adapted from the Google developer documentation style guide, "
               "licensed under CC BY 4.0.")

VERDICT_SEVERITY = {"avoid": "error", "prefer": "error", "restricted": "warning"}

VERDICT_HEADINGS = [
    ("avoid", "Don't use these", "The checker reports each of these as an error."),
    ("prefer", "Use this form instead", "One spelling or construction is correct; the other is reported as an error."),
    ("restricted", "Use with care", "Acceptable in a narrow context, reported as a warning so you can judge."),
]


def load_word_list(path: Path | None = None) -> list[dict]:
    data = json.loads((path or DATA_PATH).read_text(encoding="utf-8"))
    return data["entries"]


def render(entries: list[dict]) -> str:
    lines = [
        "<!-- GENERATED FILE — do not edit. Source: scripts/data/word_list.json.",
        "     Regenerate with: python3 scripts/gen_word_list.py -->",
        "",
        "# Word list",
        "",
        PIN,
        "",
        ATTRIBUTION,
        "",
        f"The `word-list` rule in `scripts/style_check.py` flags every term below. This page holds the {len(entries)} entries the checker enforces mechanically; the guide's full word list is much longer and lives at https://developers.google.com/style/word-list.",
        "",
    ]
    for verdict, heading, blurb in VERDICT_HEADINGS:
        rows = [e for e in entries if e["verdict"] == verdict]
        if not rows:
            continue
        lines += [f"## {heading}", "", blurb, "",
                  "| Term | Use instead | Why |", "|---|---|---|"]
        for e in rows:
            lines.append(f"| `{e['term']}` | {e['replacement']} | {e['note']} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render(load_word_list()), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
