#!/usr/bin/env python3
# style_check.py — check Markdown prose against the Google developer documentation style guide.
# Run with: python3 style_check.py PATH [PATH ...]
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Errors gate, warnings inform.

Google itself permits passive voice and semicolons where they read best, so a
zero-warnings gate would be stricter than the guide it implements — and a checker
that blocks on judgment calls trains its reader to ignore it. Errors exit 1;
warnings print and exit 0 unless --strict is passed.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import rules
import segment


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    rule: str
    severity: str
    message: str
    fix: str


def check_text(text: str, path: Path, enabled: list[rules.Rule]) -> list[Finding]:
    ctx = rules.Ctx(path=path, raw=text, masked=segment.mask(text))
    found: list[Finding] = []
    for rule in enabled:
        for raw in rule.check(ctx):
            line, col = segment.line_col(text, raw.offset)
            found.append(Finding(str(path), line, col, rule.id,
                                 raw.severity or rule.severity, raw.message, raw.fix))
    return sorted(found, key=lambda f: (f.path, f.line, f.col, f.rule))


def collect(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.is_file():
            files.append(p)
        else:
            raise FileNotFoundError(raw)
    return files


def select(only: str | None, skip: str | None) -> list[rules.Rule]:
    chosen = list(rules.RULES)
    if only:
        wanted = {r.strip() for r in only.split(",")}
        unknown = wanted - {r.id for r in chosen}
        if unknown:
            raise ValueError(f"unknown rule(s): {', '.join(sorted(unknown))}")
        chosen = [r for r in chosen if r.id in wanted]
    if skip:
        dropped = {r.strip() for r in skip.split(",")}
        unknown = dropped - {r.id for r in rules.RULES}
        if unknown:
            raise ValueError(f"unknown rule(s): {', '.join(sorted(unknown))}")
        chosen = [r for r in chosen if r.id not in dropped]
    return chosen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Markdown prose against the Google developer documentation style guide."
    )
    parser.add_argument("paths", nargs="*", help="Markdown files or directories")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    parser.add_argument("--only", help="comma-separated rule ids to run")
    parser.add_argument("--skip", help="comma-separated rule ids to skip")
    parser.add_argument("--strict", action="store_true", help="make warnings gate too")
    parser.add_argument("--list-rules", action="store_true", help="print the rule inventory and exit")
    args = parser.parse_args(argv)

    if args.list_rules:
        for rule in rules.RULES:
            print(f"{rule.id:20} {rule.severity:8} https://developers.google.com/style/{rule.page}")
        return 0

    if not args.paths:
        parser.error("no paths given")

    try:
        files = collect(args.paths)
        enabled = select(args.only, args.skip)
    except (FileNotFoundError, ValueError) as exc:
        print(f"style_check: {exc}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"style_check: {path}: {exc}", file=sys.stderr)
            return 2
        findings.extend(check_text(text, path, enabled))

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.path}:{f.line}:{f.col}  {f.severity:7} {f.rule:18} {f.message} → {f.fix}")
        errors = sum(1 for f in findings if f.severity == "error")
        warnings = len(findings) - errors
        print(f"\n{errors} error(s), {warnings} warning(s)" if findings else "clean")

    gating = [f for f in findings if f.severity == "error" or args.strict]
    return 1 if gating else 0


if __name__ == "__main__":
    raise SystemExit(main())
