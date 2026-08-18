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


import segment


def test_mask_preserves_length_and_newlines():
    text = "A line\n\n```py\ncode\n```\nAfter\n"
    masked = segment.mask(text)
    assert len(masked) == len(text)
    assert masked.count("\n") == text.count("\n")


def test_mask_blanks_fenced_code_but_keeps_prose():
    text = "Prose here.\n\n```python\nsimply utilize the thing\n```\n\nMore prose.\n"
    masked = segment.mask(text)
    assert "utilize" not in masked
    assert "Prose here." in masked
    assert "More prose." in masked


def test_mask_blanks_inline_code_and_urls():
    masked = segment.mask("Run `git checkout master` and see https://example.com/utilize now.\n")
    assert "checkout" not in masked
    assert "utilize" not in masked
    assert "Run" in masked and "and see" in masked


def test_mask_blanks_front_matter():
    masked = segment.mask("---\nname: utilize\n---\n\nBody text.\n")
    assert "utilize" not in masked
    assert "Body text." in masked


def test_mask_blanks_link_targets_but_keeps_link_text():
    masked = segment.mask("See the [word list](https://example.com/utilize) page.\n")
    assert "utilize" not in masked
    assert "word list" in masked


def test_mask_blanks_table_delimiter_rows():
    """Delimiter rows are full of hyphens and would trip the em-dash rule."""
    masked = segment.mask("| A | B |\n|---|---|\n| 1 | 2 |\n")
    assert "---" not in masked
    assert "| A | B |" in masked


LEAK_CORPUS = [
    "Prose.\n\n```py\nx=1\n```\n    simply utilize the file(s)\n",
    "---\nname: x\n---\n    simply utilize the file(s)\n",
    "Prose.\n\n    simply utilize the file(s)",
    "Prose.\n\n```bash\nsimply utilize the file(s)\n",
    "```\nok\n```\n\n```\nsimply utilize the file(s)\n",
    "```html\n<!-- sample\n```\n\nReal prose: please simply utilize the file(s).\n\n<!-- end -->\n",
]


def test_mask_blanks_indented_blocks_after_other_masked_regions():
    """A masked fence or front matter leaves a whitespace-only line, not a blank one."""
    after_fence = segment.mask(LEAK_CORPUS[0])
    assert "utilize" not in after_fence
    assert "Prose." in after_fence

    after_front_matter = segment.mask(LEAK_CORPUS[1])
    assert "utilize" not in after_front_matter

    at_eof = segment.mask(LEAK_CORPUS[2])
    assert "utilize" not in at_eof


def test_mask_blanks_an_unclosed_fence_to_end_of_file():
    """A fence with no closing delimiter is still a code sample, not prose."""
    single = segment.mask(LEAK_CORPUS[3])
    assert "utilize" not in single
    assert "Prose." in single

    pair = segment.mask(LEAK_CORPUS[4])
    assert "utilize" not in pair


def test_mask_does_not_let_a_comment_inside_a_fence_swallow_prose():
    """Over-masking is the silent failure: blanked prose is never checked at all."""
    masked = segment.mask(LEAK_CORPUS[5])
    assert "Real prose: please simply utilize the file(s)." in masked
    assert "end" not in masked


def test_mask_is_length_preserving_and_idempotent():
    fixture = (HERE / "fixtures" / "fenced_code.md").read_text(encoding="utf-8")
    for text in [*LEAK_CORPUS, fixture]:
        once = segment.mask(text)
        assert len(once) == len(text)
        assert once.count("\n") == text.count("\n")
        assert segment.mask(once) == once


import style_check
import rules

FIXTURES = HERE / "fixtures"


def run_cli(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "style_check.py"), *args],
        capture_output=True, text=True,
    )


def test_registry_ids_are_unique_and_sorted():
    ids = [r.id for r in rules.RULES]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))


def test_every_rule_names_a_source_page():
    for rule in rules.RULES:
        assert rule.page, f"{rule.id} has no source page"
        assert rule.severity in {"error", "warning"}


def test_finding_reports_true_line_and_column():
    text = "First line.\n\nThe file(s) are ready.\n"
    findings = style_check.check_text(text, Path("x.md"), rules.RULES)
    plural = [f for f in findings if f.rule == "optional-plurals"]
    assert len(plural) == 1
    assert plural[0].line == 3
    assert plural[0].col == 5


def test_no_findings_inside_fenced_code():
    text = "Clean prose.\n\n```text\nthe file(s) are ready\n```\n"
    assert style_check.check_text(text, Path("x.md"), rules.RULES) == []


def test_cli_exits_zero_on_clean_input(tmp_path):
    doc = tmp_path / "clean.md"
    doc.write_text("This page explains the setup.\n", encoding="utf-8")
    result = run_cli(str(doc))
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_exits_one_on_error_finding(tmp_path):
    doc = tmp_path / "dirty.md"
    doc.write_text("Delete the file(s) you no longer need.\n", encoding="utf-8")
    result = run_cli(str(doc))
    assert result.returncode == 1
    assert "optional-plurals" in result.stdout


def test_cli_json_output_is_parseable(tmp_path):
    doc = tmp_path / "dirty.md"
    doc.write_text("Delete the file(s) you no longer need.\n", encoding="utf-8")
    result = run_cli(str(doc), "--json")
    payload = json.loads(result.stdout)
    assert payload[0]["rule"] == "optional-plurals"
    assert set(payload[0]) == {"path", "line", "col", "rule", "severity", "message", "fix"}


def test_cli_exits_two_on_missing_path():
    result = run_cli("no/such/file.md")
    assert result.returncode == 2


def test_only_and_skip_filter_the_registry(tmp_path):
    doc = tmp_path / "dirty.md"
    doc.write_text("Delete the file(s) you no longer need.\n", encoding="utf-8")
    assert run_cli(str(doc), "--skip", "optional-plurals").returncode == 0
    assert run_cli(str(doc), "--only", "optional-plurals").returncode == 1


def test_list_rules_prints_every_rule():
    result = run_cli("--list-rules")
    assert result.returncode == 0
    for rule in rules.RULES:
        assert rule.id in result.stdout


def test_fenced_code_fixture_is_silent():
    """Every banned term in the library, inside fences. Must stay at zero findings."""
    findings = style_check.check_text(
        (FIXTURES / "fenced_code.md").read_text(encoding="utf-8"),
        FIXTURES / "fenced_code.md", rules.RULES,
    )
    assert findings == [], [f.rule for f in findings]
