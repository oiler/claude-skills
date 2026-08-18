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

Order is load-bearing. The block-level constructs — front matter, HTML comments, and
fences — are matched by one alternation rather than three passes, because each of
them can contain the opening delimiter of another. A `<!--` inside an HTML sample and
a stray fence inside a comment are the same bug in mirror image, and no ordering of
separate passes fixes both: whichever construct runs first wins, and the other one
bleeds. Matching them together makes the rule positional instead — whichever
construct *opens* first owns the region, and scanning resumes after its close.

`_INDENTED` runs after that alternation, because a masked region leaves a
whitespace-only line where a blank line used to be, and that is what marks the start
of an indented block. The inline passes run last and deliberately do not create block
boundaries — a paragraph line does not stop being a paragraph because it held a code
span.
"""
from __future__ import annotations

import re

# Front matter, HTML comment, or fence — whichever opens leftmost claims the region.
# An unterminated fence runs to EOF: it is still a code sample. The closer accepts
# CommonMark's 0-3 spaces, or the opener's own indent for a fence nested in a list
# item. Accepting *any* indent instead would let a fence line shown as an example
# inside the body close the block early, which turns the real closer into an unclosed
# opener and sends the rest of the file down the to-EOF branch.
_BLOCK = re.compile(
    r"\A---\n.*?\n---[ \t]*(?:\n|\Z)"
    r"|<!--.*?-->"
    r"|^(?P<ind>[ \t]*)(?P<fence>```|~~~)[^\n]*\n"
    r"(?:.*?^(?:[ ]{0,3}|(?P=ind))(?P=fence)[^\n]*(?:\n|\Z)|.*\Z)",
    re.DOTALL | re.MULTILINE,
)
# Interior blank lines belong to an indented block, so they are matched only when
# another indented line follows; a trailing run of blank lines ends the block instead
# of bridging it into the prose underneath. The leading boundary is consumed rather
# than looked behind — Python forbids a variable-width lookbehind, and blanking a
# whitespace-only line leaves it unchanged.
_INDENTED_LINE = r"(?: {4}|\t)[^\n]*(?:\n|\Z)"
_INDENTED = re.compile(
    rf"(?:\n[ \t]*\n|\A){_INDENTED_LINE}(?:(?:[ \t]*\n)+{_INDENTED_LINE})*"
)
_TABLE_DELIM = re.compile(r"^[ \t]*\|[ \t:|-]+\|[ \t]*$", re.MULTILINE)
_LINK_DEF = re.compile(r"^\[[^\]]+\]:[^\n]*$", re.MULTILINE)
_INLINE_CODE = re.compile(r"(``[^`]+``|`[^`\n]+`)")
_LINK_TARGET = re.compile(r"(?<=\]\()[^)\n]*(?=\))")  # inside the parens only — the link-text rule needs `](` intact
_ANGLE_URL = re.compile(r"<https?://[^>\s]+>")
_BARE_URL = re.compile(r"https?://\S+|www\.\S+")
_IMAGE_BANG = re.compile(r"!(?=\[)")
_PATH_LIKE = re.compile(r"(?<![\w/])(?:~|\.{1,2})?/[\w./-]+")

_PASSES = (
    _BLOCK, _INDENTED, _TABLE_DELIM, _LINK_DEF,
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
