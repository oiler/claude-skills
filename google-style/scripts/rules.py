#!/usr/bin/env python3
# rules.py — the rule definitions for style_check.py.
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Rule inventory derived from github.com/vale-cli/Google (MIT), a Vale port of the same guide, neither maintained nor endorsed by Google.

Each rule names the guide page it enforces. That `page` value is not decoration: it
is how a reader checks a surprising finding against the source, and how the quarterly
refresh knows which rules a changed page affects.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Ctx:
    path: Path
    raw: str
    masked: str


@dataclass(frozen=True)
class Raw:
    offset: int
    message: str
    fix: str
    severity: str | None = None


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    page: str
    check: Callable[[Ctx], Iterator[Raw]]


def regex_rule(rule_id: str, severity: str, page: str, pattern: str,
               message: str, fix: str, flags: int = re.IGNORECASE) -> Rule:
    compiled = re.compile(pattern, flags)

    def check(ctx: Ctx) -> Iterator[Raw]:
        for m in compiled.finditer(ctx.masked):
            yield Raw(m.start(), message.format(match=m.group(0).strip()), fix)

    return Rule(rule_id, severity, page, check)


RULES: list[Rule] = [
    regex_rule(
        "optional-plurals", "error", "pluralization",
        r"\b\w+\(s\)",
        "{match} — parenthetical plural",
        "Use the plural form, or rewrite so the number is clear.",
    ),
]

RULES.sort(key=lambda r: r.id)
