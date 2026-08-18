# test_style_check.py — run with: uv run --with pytest pytest -q
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
import json
import subprocess
import sys
from pathlib import Path

import pytest

import gen_word_list

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / "references" / "word-list.md"


def test_word_list_entries_have_required_keys():
    entries = gen_word_list.load_word_list()
    assert len(entries) >= 35
    for e in entries:
        assert set(e) == {"term", "verdict", "replacement", "note", "anchor"}
        assert e["verdict"] in {"avoid", "prefer", "restricted"}
        assert e["term"] and e["replacement"] and e["note"]


def test_word_list_terms_are_unique_and_lowercase():
    terms = [e["term"] for e in gen_word_list.load_word_list()]
    assert terms == sorted(terms), "keep data/word_list.json sorted by term"
    assert len(terms) == len(set(terms))
    assert all(t == t.lower() for t in terms)


def test_word_list_excludes_terms_other_rules_own():
    """Two rules flagging one term teaches the model the checker is noisy."""
    terms = {e["term"] for e in gen_word_list.load_word_list()}
    owned_elsewhere = {"simply", "easily", "obviously", "guys", "crazy",
                       "sanity check", "e.g.", "i.e.", "etc.",
                       "please", "please note"}
    assert terms & owned_elsewhere == set()


def test_generated_reference_matches_the_data_file():
    """The committed reference page must be exactly what the generator emits."""
    expected = gen_word_list.render(gen_word_list.load_word_list())
    assert REFERENCE.read_text(encoding="utf-8") == expected, (
        "references/word-list.md is stale — run `python3 scripts/gen_word_list.py`"
    )
