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


import json

import gen_word_list

_VOCAB_PATH = Path(__file__).resolve().parent / "data" / "vocab.json"
VOCAB: dict[str, set[str]] = {
    k: set(v) for k, v in json.loads(_VOCAB_PATH.read_text(encoding="utf-8")).items()
}


def _blank(m: re.Match[str]) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in m.group(0))


# Double quotes only. A single-quote alternative pairs the apostrophes of two
# contractions ("it's … we've") into a phantom quote span and blanks the real
# first-person hit between them; the guide's own quoting convention is double.
_QUOTED = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”")
_BLOCKQUOTE = re.compile(r"^[ \t]*>[^\n]*$", re.MULTILINE)


def _without_citations(text: str) -> str:
    """Blank quoted material and blockquotes.

    Reference files quote the guide verbatim, and the guide says "we recommend".
    A rule that flags its own source quotation is a rule nobody trusts.
    """
    return _BLOCKQUOTE.sub(_blank, _QUOTED.sub(_blank, text))


# --- headings ---------------------------------------------------------------
_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def _headings(ctx: Ctx) -> Iterator[Raw]:
    for m in _HEADING.finditer(ctx.masked):
        title = m.group(2).rstrip()
        if title.endswith(".") and not title.endswith("..."):
            yield Raw(m.start(2), "heading ends with a period",
                      "Drop it. Headings and titles take no end punctuation.")
        words = _WORD.findall(title)
        capped = [w for w in words[1:]
                  if w[:1].isupper() and not w.isupper()
                  and w.lower() not in VOCAB["proper_nouns"]]
        if len(capped) >= 2:
            yield Raw(m.start(2), f"heading looks like Title Case ({', '.join(capped[:3])})",
                      "Use sentence case: capitalize the first word and proper nouns only.")


# --- oxford-comma -----------------------------------------------------------
_SERIAL = re.compile(r",[ \t]+(?P<mid>[^,\n]{1,40}?)[ \t]+(?P<conj>and|or)[ \t]+", re.IGNORECASE)


def _is_introductory(clause: str) -> bool:
    words = _WORD.findall(clause)
    if not words:
        return True
    return (words[0].lower() in VOCAB["subordinators"]
            or words[-1].lower() in VOCAB["intro_stoplist"])


def _oxford(ctx: Ctx) -> Iterator[Raw]:
    for m in _SERIAL.finditer(ctx.masked):
        start = ctx.masked.rfind("\n", 0, m.start()) + 1
        if _is_introductory(ctx.masked[start:m.start()]):
            continue
        # "Save the file, then commit and push" is a sequence, not a list —
        # when the segment after the comma opens with a connective or
        # subordinator, the and/or joins verbs, not list items.
        mid_words = _WORD.findall(m.group("mid"))
        if not mid_words or mid_words[0].lower() in (
                VOCAB["subordinators"] | VOCAB["intro_stoplist"]):
            continue
        conj = m.group("conj")
        yield Raw(m.start(), f"missing serial comma before '{conj}'",
                  f"Write \"…, {m.group('mid').strip()}, {conj} …\".")


# --- first-person -----------------------------------------------------------
_FIRST_PERSON = re.compile(r"\b(we|we're|we've|we'll|our|ours|us|let's)\b", re.IGNORECASE)


def _first_person(ctx: Ctx) -> Iterator[Raw]:
    text = _without_citations(ctx.masked)
    for m in _FIRST_PERSON.finditer(text):
        yield Raw(m.start(), f"first person: {m.group(0)}",
                  "Write from the reader's side. Use \"you\", or name the product.")


# --- word-list --------------------------------------------------------------
def _build_word_list_rule() -> Rule:
    entries = gen_word_list.load_word_list()
    lookup = {e["term"]: e for e in entries}
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(e["term"]) for e in
                          sorted(entries, key=lambda e: -len(e["term"]))) + r")\b",
        re.IGNORECASE,
    )
    severity_for = gen_word_list.VERDICT_SEVERITY

    def check(ctx: Ctx) -> Iterator[Raw]:
        for m in pattern.finditer(ctx.masked):
            entry = lookup[m.group(0).lower()]
            yield Raw(m.start(), f"{m.group(0)} — {entry['note']}",
                      f"Use {entry['replacement']}.",
                      severity_for[entry["verdict"]])

    return Rule("word-list", "error", "word-list", check)


# --- latin ------------------------------------------------------------------
_LATIN = {
    r"\bi\.e\.": ("i.e.", "Use \"that is\".", "error"),
    r"\be\.g\.": ("e.g.", "Use \"for example\".", "error"),
    r"\betc\.": ("etc.", "Rephrase the list, or name the remaining cases.", "warning"),
    r"\bvia\b": ("via", "Use \"with\", \"by using\", or \"through\".", "warning"),
    r"\bvs\.?\b": ("vs.", "Use \"versus\" or \"compared with\".", "warning"),
}
_LATIN_RE = [(re.compile(p, re.IGNORECASE), v) for p, v in _LATIN.items()]


def _latin(ctx: Ctx) -> Iterator[Raw]:
    for pattern, (term, fix, severity) in _LATIN_RE:
        for m in pattern.finditer(ctx.masked):
            yield Raw(m.start(), f"Latin abbreviation: {term}", fix, severity)


# --- em-dash ----------------------------------------------------------------
_DOUBLE_HYPHEN = re.compile(r"(?<=\w)--(?=\w)|(?<=\s)--(?=\s)")
_SPACED_EM = re.compile(r"(?<=\S)[ \t]+—[ \t]+(?=\S)")


def _em_dash(ctx: Ctx) -> Iterator[Raw]:
    for m in _DOUBLE_HYPHEN.finditer(ctx.masked):
        yield Raw(m.start(), "-- used as an em dash",
                  "Use a real em dash (—).", "error")
    for m in _SPACED_EM.finditer(ctx.masked):
        yield Raw(m.start(), "spaces around an em dash",
                  "Close the spaces: word—word. Reported as a warning because oiler's "
                  "house style spaces em dashes and CLAUDE.md outranks this skill.",
                  "warning")


# --- am-pm ------------------------------------------------------------------
# The word boundary belongs to the bare-suffix branch only: after "a.m." the last
# character is a period, so a trailing \b never holds and that branch stays dead.
_TIME = re.compile(r"\b\d{1,2}(?::\d{2})?[ \t]*(?:[ap]\.m\.|[ap]m\b)", re.IGNORECASE)


def _am_pm(ctx: Ctx) -> Iterator[Raw]:
    for m in _TIME.finditer(ctx.masked):
        if re.search(r"\s(?:AM|PM)$", m.group(0)):
            continue
        yield Raw(m.start(), f"time format: {m.group(0)}",
                  "Write the time, a space, then AM or PM in capitals: 10:30 AM.")


# --- ly-hyphens -------------------------------------------------------------
_LY_HYPHEN = re.compile(r"\b(\w+ly)-(\w+)", re.IGNORECASE)


def _ly_hyphens(ctx: Ctx) -> Iterator[Raw]:
    for m in _LY_HYPHEN.finditer(ctx.masked):
        if m.group(1).lower() in VOCAB["ly_exceptions"]:
            continue
        yield Raw(m.start(), f"hyphen after an -ly adverb: {m.group(0)}",
                  f"Drop the hyphen: {m.group(1)} {m.group(2)}.")


# --- spacing ----------------------------------------------------------------
# Comma and semicolon only: the colons rule owns space-before-colon,
# and two rules firing on one span teaches the model the checker is noisy.
_SPACING = re.compile(r"(?<=[.!?])[ \t]{2,}(?=[A-Z])|[ \t]+(?=[,;](?:[ \t]|$))")


def _spacing(ctx: Ctx) -> Iterator[Raw]:
    for m in _SPACING.finditer(ctx.masked):
        # Masking blanks inline code to spaces, so whitespace in the masked text
        # is not always whitespace the author typed: "`--force`," reads as a
        # space before a comma. Confirm against the raw span before reporting.
        if ctx.raw[m.start():m.end()].strip():
            continue
        yield Raw(m.start(), "spacing around punctuation",
                  "One space after a sentence, none before a comma or semicolon.")


RULES: list[Rule] = [
    regex_rule(
        "optional-plurals", "error", "pluralization",
        r"\b\w+\(s\)",
        "{match} — parenthetical plural",
        "Use the plural form, or rewrite so the number is clear.",
    ),
]

RULES += [
    Rule("headings", "error", "headings", _headings),
    Rule("oxford-comma", "error", "commas", _oxford),
    Rule("first-person", "error", "person", _first_person),
    _build_word_list_rule(),
    Rule("latin", "error", "abbreviations", _latin),
    Rule("em-dash", "error", "dashes", _em_dash),
    Rule("am-pm", "error", "dates-times", _am_pm),
    Rule("ly-hyphens", "error", "hyphens", _ly_hyphens),
    regex_rule(
        "future", "error", "timeless-documentation",
        r"\b(will soon|coming soon|in a future release|in an upcoming release|"
        r"currently|at this time|as of this writing|at present|for now)\b",
        "time-bound phrasing: {match}",
        "Write timeless documentation. State what is true, not what changed or is coming.",
    ),
    regex_rule(
        "date-format", "error", "dates-times",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        "ambiguous date: {match}",
        "Write the month out: January 5, 2026. Numeric dates read differently by region.",
    ),
    regex_rule(
        "excessive-claims", "error", "excessive-claims",
        r"\b(simply|easily|effortlessly|painless(?:ly)?|trivially|obviously|of course|"
        r"clearly|no problem|all you need to do)\b|"
        r"\bjust\b(?=[ \t]+(?:add|run|click|set|call|use|type|enter|open|edit|paste|copy|"
        r"install|create|delete|update|write|do)\b)",
        "excessive claim: {match}",
        "Cut it. What is easy for the writer is not always easy for the reader.",
    ),
    Rule("spacing", "error", "periods", _spacing),
    regex_rule(
        "units", "error", "units-of-measure",
        r"\b\d+(?:\.\d+)?(?:MB|GB|KB|TB|KiB|MiB|GiB|ms|Hz|MHz|GHz|px|kg|cm|mm)\b",
        "missing space before the unit: {match}",
        "Put a space between the number and the unit: 512 MB.",
        flags=0,
    ),
    regex_rule(
        "gendered", "error", "inclusive-documentation",
        r"\b(he/she|s/he|his/her|he or she|guys|manpower|man-hours|mankind|"
        r"chairman|chairmen|policeman|salesman|middleman)\b",
        "gendered language: {match}",
        "Use they, or name the role: the person, the team, the operator.",
    ),
    regex_rule(
        "ableist", "error", "inclusive-documentation",
        r"\b(crazy|insane|lame|cripple[sd]?|sanity[ -]check|dumb)\b|\bblind to\b|\bdeaf to\b",
        "ableist language: {match}",
        "Say what you mean: unexpected, unusable, confidence check, unaware of.",
    ),
    regex_rule(
        "please", "error", "word-list",
        r"\bplease\b",
        "please in instructions",
        "Cut it. Instructions are not requests, and politeness words do not translate evenly.",
    ),
    regex_rule(
        "periods", "error", "abbreviations",
        r"\b(?:[A-Z]\.){2,}",
        "periods inside an acronym: {match}",
        "Drop the periods: US, API.",
        flags=0,
    ),
    regex_rule(
        "link-text", "error", "cross-references",
        r"\[(?:click here|here|this|this link|this page|read more|more|link|"
        r"learn more|see here|documentation)\]\(",
        "undescriptive link text: {match}",
        "Name the destination: \"see the word list\".",
    ),
]

RULES.sort(key=lambda r: r.id)
