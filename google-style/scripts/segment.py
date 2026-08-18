#!/usr/bin/env python3
# segment.py — blank out the regions of a Markdown file that a prose checker must not read.
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Offset-preserving masking.

Every excluded character is replaced by a space rather than removed, so a finding's
offset in the masked text is the same offset in the original. That is what lets the
engine report a true line and column without tracking a second coordinate system.

A style checker that reads inside a code sample reports nonsense and, worse, teaches
the reader to ignore it. Masking is applied in order, and each pass runs against the
already-masked buffer so a region blanked by an earlier pass cannot re-match.
"""
from __future__ import annotations

import re

_FRONT_MATTER = re.compile(r"\A---\n.*?\n---[ \t]*(?:\n|\Z)", re.DOTALL)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE = re.compile(r"^([ \t]*)(```|~~~)[^\n]*\n.*?^\1\2[^\n]*(?:\n|\Z)", re.DOTALL | re.MULTILINE)
_INDENTED = re.compile(r"(?:(?<=\n\n)|\A)(?:(?: {4}|\t)[^\n]*\n)+", re.MULTILINE)
_TABLE_DELIM = re.compile(r"^[ \t]*\|[ \t:|-]+\|[ \t]*$", re.MULTILINE)
_LINK_DEF = re.compile(r"^\[[^\]]+\]:[^\n]*$", re.MULTILINE)
_INLINE_CODE = re.compile(r"(``[^`]+``|`[^`\n]+`)")
_LINK_TARGET = re.compile(r"(?<=\]\()[^)\n]*(?=\))")  # inside the parens only — the link-text rule needs `](` intact
_ANGLE_URL = re.compile(r"<https?://[^>\s]+>")
_BARE_URL = re.compile(r"https?://\S+|www\.\S+")
_IMAGE_BANG = re.compile(r"!(?=\[)")
_PATH_LIKE = re.compile(r"(?<![\w/])(?:~|\.{1,2})?/[\w./-]+")

_PASSES = (
    _FRONT_MATTER, _HTML_COMMENT, _FENCE, _INDENTED, _TABLE_DELIM, _LINK_DEF,
    _INLINE_CODE, _ANGLE_URL, _LINK_TARGET, _BARE_URL, _IMAGE_BANG, _PATH_LIKE,
)


def _blank(match: re.Match[str]) -> str:
    """Replace the match with spaces, keeping every newline where it was."""
    return "".join("\n" if ch == "\n" else " " for ch in match.group(0))


def mask(text: str) -> str:
    for pattern in _PASSES:
        text = pattern.sub(_blank, text)
    return text


def line_col(text: str, offset: int) -> tuple[int, int]:
    """1-indexed line and column for a character offset."""
    line = text.count("\n", 0, offset) + 1
    start = text.rfind("\n", 0, offset) + 1
    return line, offset - start + 1
