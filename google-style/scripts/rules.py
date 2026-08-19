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

# Oxford-specific, so it lives here rather than in vocab.json, whose keys each
# document one rule's suppressors. Shapes of correctly punctuated prose that the
# pattern would otherwise read as a list: "and"/"or" catch the rule re-matching
# across its own serial comma ("Fetch, parse, and render the page and exit"), the
# auxiliaries catch a clause continuation ("…only, must not start or end with a
# hyphen"), and the relative pronouns and negations catch a modifying clause
# ("…§1, which carries this figure and the setting"; "…, never inside the folder
# and never as a sibling"). Each is one-directional: a genuine list item
# essentially never opens with one of these words.
#
# Known blind spot, deliberately not chased: an and/or inside a single list item
# after a clause comma can still match ("…1-64 chars, lowercase a-z/0-9 and
# hyphens only"). Rewording the prose is cheaper than a suppressor that can eat
# real lists.
_OXFORD_MID_SKIP = frozenset({
    "and", "or",
    "must", "should", "can", "cannot", "may", "might", "will", "would", "shall",
    "do", "does", "did", "is", "are", "was", "were", "has", "have", "had",
    "which", "who", "that", "never", "not", "no",
})


# Both oxford suppressors read the text before the comma, so they need the
# current sentence, not the current line. Prose here is never hard-wrapped, so a
# line is a whole paragraph: scanning from the line start would hand every
# sentence after the first a run-on prefix and silently disable both
# suppressors. Closing quotes and brackets ride along after the stop.
_SENTENCE_END = re.compile(r"[.!?][\"'’”)\]]*[ \t]")


def _sentence_start(text: str, pos: int) -> int:
    """Offset of the sentence containing `pos`, or of its line, whichever is later."""
    start = text.rfind("\n", 0, pos) + 1
    for m in _SENTENCE_END.finditer(text, start, pos):
        start = m.end()
    return start


def _is_introductory(clause: str) -> bool:
    words = _WORD.findall(clause)
    if not words:
        return True
    return (words[0].lower() in VOCAB["subordinators"]
            or words[-1].lower() in VOCAB["intro_stoplist"])


def _oxford(ctx: Ctx) -> Iterator[Raw]:
    for m in _SERIAL.finditer(ctx.masked):
        start = _sentence_start(ctx.masked, m.start())
        if _is_introductory(ctx.masked[start:m.start()]):
            continue
        # "Save the file, then commit and push" is a sequence, not a list —
        # when the segment after the comma opens with a connective or
        # subordinator, the and/or joins verbs, not list items.
        mid_words = _WORD.findall(m.group("mid"))
        if not mid_words or mid_words[0].lower() in (
                VOCAB["subordinators"] | VOCAB["intro_stoplist"] | _OXFORD_MID_SKIP):
            continue
        conj = m.group("conj")
        # Quote the source, not the mask: masking is offset-preserving, so the
        # masked slice renders inline code as a run of spaces.
        mid = ctx.raw[m.start("mid"):m.end("mid")].strip()
        yield Raw(m.start(), f"missing serial comma before '{conj}'",
                  f"Write \"…, {mid}, {conj} …\".")


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


# --- units and ranges -------------------------------------------------------
# Shared by the `units` and `ranges` rules, which turn on the same distinction:
# units-of-measure.html defines a unit as "both symbols (like the degree symbol
# (º)) and abbreviations (like MB for megabytes) but not nouns (like file)".
# Longest alternatives first so a partial never wins under a trailing guard.
_UNIT_ABBREV = r"MHz|GHz|KiB|MiB|GiB|MB|GB|KB|TB|ms|Hz|px|kg|cm|mm"
# Ranges additionally accept the bare symbols, which never appear glued to the
# number the way an abbreviation does, so the `units` rule has no use for them.
_RANGE_UNIT = rf"{_UNIT_ABBREV}|[°º][CF]?|%"


# --- spacing ----------------------------------------------------------------
# Comma and semicolon only: the colons rule owns space-before-colon,
# and two rules firing on one span teaches the model the checker is noisy.
_SPACING = re.compile(
    r"(?<=[.!?])[ \t]{2,}(?=[A-Z])|(?P<before>[ \t]+)(?=[,;](?:[ \t]|$))")


def _spacing(ctx: Ctx) -> Iterator[Raw]:
    """Masking blanks inline code to spaces, so a whitespace run in the masked
    text is not always whitespace the author typed. Both branches confirm against
    ctx.raw at the same offsets, but they need different amounts of it.
    """
    for m in _SPACING.finditer(ctx.masked):
        if m.group("before") is not None:
            # Only the character touching the punctuation decides. The run can
            # legitimately swallow a masked span — "Use `--force` , then go" is a
            # real finding — so testing the whole span would drop true positives.
            if ctx.raw[m.end() - 1] not in " \t":
                continue
            yield Raw(m.end() - 1, "spacing around punctuation",
                      "One space after a sentence, none before a comma or semicolon.")
        elif not ctx.raw[m.start():m.end()].strip():
            # The sentence-gap branch reports the whole run, so the whole run has
            # to be whitespace the author typed.
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
        # The page is word-list, not excessive-claims. excessive-claims.html is
        # about competitive and unverifiable product claims ("Our product is
        # faster than ExampleCorp's product") and never mentions these words.
        # What attests them is the word list's own entry:
        #   "easy, easily — What might be easy for you might not be easy for
        #    others. Try eliminating this word from the sentence because usually
        #    the same meaning can be conveyed without it."
        # with matching entries for "simple, simply" and for "just" ("Avoid.
        # Usually, just is a filler word that you can delete"). The rest of the
        # list — effortlessly, painless(ly), trivially, obviously, of course,
        # clearly, no problem, all you need to do — is a workshop extension of
        # that same principle, not text the guide states. The terms are good
        # guidance either way; only the attribution was wrong.
        "excessive-claims", "error", "word-list",
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
        rf"\b\d+(?:\.\d+)?(?:{_UNIT_ABBREV})\b",
        "missing space before the unit: {match}",
        "Put a space between the number and the unit: 512 MB.",
        flags=0,
    ),
    regex_rule(
        # The pronoun pairs are attested on pronouns.html, "Gender-neutral
        # pronouns": "don't use he, him, his, she, or her as gender-neutral
        # pronouns, and don't use he/she or (s)he or other such punctuational
        # approaches. Instead, use the singular they." That is the page.
        # The role nouns after them — guys, manpower, man-hours, mankind,
        # chairman, chairmen, policeman, salesman, middleman — are a workshop
        # extension of inclusive-documentation.html's principle of avoiding
        # ableist, gendered, and violent language. Only "manpower" has its own
        # word-list entry; the rest appear nowhere in the guide. Kept, labeled.
        "gendered", "error", "pronouns",
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

# --- passive ----------------------------------------------------------------
_PASSIVE = re.compile(
    r"\b(?:is|are|was|were|be|been|being|gets|got)[ \t]+(\w+(?:ed|en))\b", re.IGNORECASE)


def _passive(ctx: Ctx) -> Iterator[Raw]:
    for m in _PASSIVE.finditer(ctx.masked):
        if m.group(1).lower() in VOCAB["adjectival_participles"]:
            continue
        # Masking is offset-preserving, so the auxiliary and the participle can
        # sit adjacent in the masked text and be separated by inline code in the
        # source: "is `--json` formatted" is not a passive. One guard kills both
        # that false positive and the mask run the message would otherwise print
        # back at the reader.
        if ctx.raw[m.start():m.end()] != m.group(0):
            continue
        yield Raw(m.start(), f"possible passive voice: {m.group(0)}",
                  "Name the actor: \"the installer creates the file\".")


# --- contractions -----------------------------------------------------------
_PRONOUN_RE = re.compile(
    r"\b(?:you|we|they|it|he|she|who|what|there|here|these|those|that|i)'(?:re|s|ve|ll|d|m)\b",
    re.IGNORECASE)
_APOSTROPHE_RE = re.compile(r"\b\w+'(?:re|ve|ll)\b", re.IGNORECASE)
_THREE_WORD = re.compile(r"\b\w+n't've\b", re.IGNORECASE)
_IS_CONTRACTION = re.compile(r"\b(\w+'s)[ \t]+(?:a|an|the|not|only|now|going to)\b", re.IGNORECASE)
_UNCONTRACTED = re.compile(
    r"\b(?:do|does|did|is|are|was|were|will|would|should|could|has|have|had|can)[ \t]+not\b|\bcannot\b",
    re.IGNORECASE)


def _contractions(ctx: Ctx) -> Iterator[Raw]:
    for m in _THREE_WORD.finditer(ctx.masked):
        yield Raw(m.start(), f"three-word contraction: {m.group(0)}",
                  "Write it out. Only common two-word contractions are standard.")
    for m in _APOSTROPHE_RE.finditer(ctx.masked):
        # \b\w+' also holds after the first apostrophe of a three-word form, so
        # "mightn't've" matched again as "t've". The branch above already
        # reported it, and a second, garbled finding on the same span is worse
        # than none.
        if m.start() > 0 and ctx.masked[m.start() - 1] == "'":
            continue
        if _PRONOUN_RE.fullmatch(m.group(0)):
            continue
        yield Raw(m.start(), f"nonstandard contraction: {m.group(0)}",
                  "Contract pronouns only. Write the noun and verb out.")
    for m in _IS_CONTRACTION.finditer(ctx.masked):
        # "it's a valid form" is a standard pronoun contraction the guide
        # recommends; only a noun + 's meaning "is" (browser's) is nonstandard.
        if _PRONOUN_RE.fullmatch(m.group(1)):
            continue
        yield Raw(m.start(), f"'s standing in for \"is\": {m.group(0)}",
                  "Write \"is\" out when the subject is a noun.")
    for m in _UNCONTRACTED.finditer(ctx.masked):
        yield Raw(m.start(), f"uncontracted negation: {m.group(0)}",
                  "Contract it. A scanning reader misses a standalone \"not\", "
                  "but cannot misread \"don't\" as \"do\".")


# --- semicolons and condition-order (procedural context) --------------------
_STEP_LINE = re.compile(r"^[ \t]*(?:\d+[.)][ \t]+|[-*][ \t]+)?(?P<first>[A-Za-z]+)\b")


def _is_procedural(line: str) -> bool:
    m = _STEP_LINE.match(line)
    return bool(m) and m.group("first").lower() in VOCAB["imperative_verbs"]


def _iter_lines(text: str) -> Iterator[tuple[int, str]]:
    offset = 0
    for line in text.split("\n"):
        yield offset, line
        offset += len(line) + 1


def _semicolons(ctx: Ctx) -> Iterator[Raw]:
    for offset, line in _iter_lines(ctx.masked):
        if ";" in line and _is_procedural(line):
            yield Raw(offset + line.index(";"), "semicolon in a procedural step",
                      "Split it into two sentences, or two steps.")


_CONDITION = re.compile(r"\b(if|when|unless)\b", re.IGNORECASE)


def _condition_order(ctx: Ctx) -> Iterator[Raw]:
    for offset, line in _iter_lines(ctx.masked):
        if not _is_procedural(line):
            continue
        m = _CONDITION.search(line)
        if m and m.start() > 0:
            yield Raw(offset + m.start(), f"instruction before its condition ({m.group(0)})",
                      "Put the condition first, so the reader knows whether the step applies "
                      "before they start doing it.")


# --- acronyms ---------------------------------------------------------------
_ACRONYM = re.compile(r"\b([A-Z]{2,6})s?\b")


def _acronyms(ctx: Ctx) -> Iterator[Raw]:
    seen: set[str] = set()
    for m in _ACRONYM.finditer(ctx.masked):
        token = m.group(1)
        if token in VOCAB["known_acronyms"] or token in seen:
            continue
        # Both expansion forms are anchored to this occurrence: the term then the
        # acronym in parentheses ("flux capacitor (FLUX)"), or the acronym then
        # the term ("FLUX (flux capacitor)"). The earlier check searched the 120
        # characters before the match for "TOKEN (", which is unanchored — any
        # longer token ending in TOKEN matched, and "SUPERFLUX (" silently
        # suppressed the real FLUX finding after it.
        #
        # m.end() stops before a closing paren, so slice one char past it or
        # "(FLUX)" never matches its own first occurrence.
        expanded = (f"({token})" in ctx.masked[:m.end() + 1]
                    or re.match(r"[ \t]*\(", ctx.masked[m.end():]))
        seen.add(token)
        if not expanded:
            yield Raw(m.start(), f"unexpanded acronym: {token}",
                      f"Spell it out on first use, then give the acronym in parentheses: "
                      f"spelled-out term ({token}).")


# --- colons -----------------------------------------------------------------
_HEADING_COLON = re.compile(r"^#{1,6}[^\n]*:[ \t]*$", re.MULTILINE)
_SPACED_COLON = re.compile(r"[ \t]+(?=:[ \t])")
_DOUBLE_COLON = re.compile(r"::")


def _colons(ctx: Ctx) -> Iterator[Raw]:
    """Three different mistakes, so three different messages — and two of them
    need a raw-text guard.

    Masking is offset-preserving, which means a blanked inline-code span reads as
    the whitespace before a colon ("`--json`: emit JSON", the ordinary shape of
    CLI reference prose) and a heading ending in inline code reads as
    colon-terminated ("### Task 2: `references/foo.md`"). Both are correct prose,
    and unguarded they were almost every finding this rule produced.
    """
    # Attested, but cross-page: colons.html says nothing about headings, so the
    # attestation is headings.html's summary — "Avoid using -ing verbs, numbers,
    # and excessive punctuation in headings."
    for m in _HEADING_COLON.finditer(ctx.masked):
        if not ctx.raw[m.start():m.end()].rstrip().endswith(":"):
            continue
        yield Raw(m.start(), "heading ends with a colon",
                  "Drop it. A heading names its section; it does not introduce it.")
    # Workshop punctuation hygiene, not stated on colons.html — that page covers
    # only introductory-phrase completeness and lowercase after the colon, and
    # the word "space" does not appear on it.
    for m in _SPACED_COLON.finditer(ctx.masked):
        # Only the character touching the colon decides. The run can legitimately
        # swallow a masked span, and what the author typed there was code.
        if ctx.raw[m.end() - 1] not in " \t":
            continue
        yield Raw(m.end() - 1, "space before a colon",
                  "Close it up. A colon attaches to the word before it.")
    # Workshop punctuation hygiene as well; the guide has no double-colon entry.
    for m in _DOUBLE_COLON.finditer(ctx.masked):
        yield Raw(m.start(), "double colon",
                  "Use one colon. Doubling it is code syntax, not prose punctuation.")


RULES += [
    Rule("passive", "warning", "voice", _passive),
    Rule("colons", "warning", "colons", _colons),
    Rule("contractions", "warning", "contractions", _contractions),
    Rule("semicolons", "warning", "semicolons", _semicolons),
    Rule("condition-order", "warning", "sentence-structure", _condition_order),
    Rule("acronyms", "warning", "abbreviations", _acronyms),
    regex_rule(
        "anthropomorphism", "warning", "anthropomorphism",
        r"\b(?:system|API|service|function|method|script|tool|app|application|code|"
        r"server|database|module|library|model|agent|page|browser)[ \t]+"
        r"(?:thinks|wants|knows|believes|likes|decides|feels|understands|sees|"
        r"remembers|tries|expects|refuses|prefers|assumes)\b",
        "anthropomorphism: {match}",
        "Describe what the software does, not what it wants.",
    ),
    regex_rule(
        "ellipsis", "warning", "ellipses",
        r"…|\.\.\.",
        "ellipsis: {match}",
        "In general, don't use ellipses. When you must, use three periods in a row, "
        "not the single ellipsis character.",
        flags=0,
    ),
    regex_rule(
        "quotes", "warning", "quotation-marks",
        r"[\"”][ \t]*[.,]",
        "punctuation outside the quotation marks",
        "American convention puts the period or comma inside the closing quotation mark.",
        flags=0,
    ),
    regex_rule(
        "ordinals", "warning", "numbers",
        r"\b\d+(?:st|nd|rd|th)\b",
        "numeric ordinal: {match}",
        "Spell ordinals out: first, second, third.",
    ),
    regex_rule(
        "ranges", "warning", "units-of-measure",
        # A hyphenated numeric range is the guide's RECOMMENDED form, not a
        # finding: numbers.html says "Use a hyphen with no space on either side
        # of it … Recommended: 2012-2016", and hyphens.html lists "8-20 files"
        # and "5-10 minutes" as Recommended. Only units-of-measure.html asks for
        # "to", and only when the range carries a unit — hence the mandatory
        # unit on the closing number. Flagging the bare form was an inversion
        # against three pages at once; do not widen this back out.
        rf"(?<![\d.])\d+(?:\.\d+)?[ \t]*(?:{_RANGE_UNIT})?[ \t]*-[ \t]*"
        rf"\d+(?:\.\d+)?[ \t]*(?:{_RANGE_UNIT})(?![A-Za-z0-9])",
        "hyphenated range with units: {match}",
        "In a range with units, use \"to\" and repeat the unit: 10 MB to 20 MB. "
        "A hyphen can be misread as a minus sign.",
        flags=0,
    ),
    regex_rule(
        "exclamation", "warning", "periods",
        r"(?<!\])!(?!\[)",
        "exclamation mark",
        "Cut it. Reference prose stays level.",
        flags=0,
    ),
]

RULES.sort(key=lambda r: r.id)
