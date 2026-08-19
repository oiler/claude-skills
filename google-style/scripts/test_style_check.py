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


REGRESSION_CORPUS = [
    "```py\nx=1\n  ```\n\nReal prose: please simply utilize the file(s).\n",
    "<!--\nnote\n```\n-->\nReal prose here.\n",
    "Text.\n\n    a()\n\n    b()\n\nProse.\n",
    "Text.\n\n    a()\n\n\nProse.\n",
    "Intro.\n\n```text\nexample:\n    ```\ndone\n```\n\nTail prose must survive.\n",
    "Intro.\n\n```text\n    ```\nmore body\n```\n\nTail prose must survive.\n",
    "- item\n\n  ```py\n  x = 1\n  ```\n\nTail prose.\n",
    "- item\n\n    ```py\n    x = 1\n    ```\n\nTail prose.\n",
]


def test_mask_tolerates_a_closing_fence_at_a_different_indent():
    """CommonMark lets the closer's indent differ from the opener's."""
    masked = segment.mask(REGRESSION_CORPUS[0])
    assert "Real prose: please simply utilize the file(s)." in masked
    assert "x=1" not in masked


def test_mask_does_not_let_a_fence_inside_a_comment_swallow_prose():
    """Whichever block construct opens first owns the region."""
    masked = segment.mask(REGRESSION_CORPUS[1])
    assert "Real prose here." in masked
    assert "note" not in masked


def test_mask_keeps_interior_blank_lines_inside_an_indented_block():
    masked = segment.mask(REGRESSION_CORPUS[2])
    assert "a()" not in masked
    assert "b()" not in masked
    assert "Prose." in masked


def test_mask_does_not_run_an_indented_block_into_following_prose():
    """A trailing run of blank lines ends the block; it does not bridge to prose."""
    masked = segment.mask(REGRESSION_CORPUS[3])
    assert "a()" not in masked
    assert "Prose." in masked


def test_mask_does_not_close_a_fence_on_an_indented_fence_line_in_its_body():
    """Showing a nested fence example inside a fence is routine Markdown documentation.

    Closing early turns the real closer into an unclosed opener, and the to-EOF branch
    then blanks the rest of the file.
    """
    trailing_body = segment.mask(REGRESSION_CORPUS[4])
    assert "Tail prose must survive." in trailing_body
    assert "done" not in trailing_body

    leading_body = segment.mask(REGRESSION_CORPUS[5])
    assert "Tail prose must survive." in leading_body
    assert "more body" not in leading_body


def test_mask_closes_a_fence_nested_in_a_list_item():
    """Opener and closer share the list's indent — the case the closer must still handle."""
    two_space = segment.mask(REGRESSION_CORPUS[6])
    assert "x = 1" not in two_space
    assert "Tail prose." in two_space

    four_space = segment.mask(REGRESSION_CORPUS[7])
    assert "x = 1" not in four_space
    assert "Tail prose." in four_space


def test_mask_preserves_length_and_is_stable_over_the_corpus():
    """Length and newline preservation are invariants of mask().

    Stability under a second pass is NOT an invariant — an inline pass can blank a
    line to whitespace after _INDENTED has already run, creating a block boundary a
    second pass would see. It holds for every input here, so the assertion stays as a
    regression guard on this corpus rather than a promise about arbitrary input.
    """
    fixture = (HERE / "fixtures" / "fenced_code.md").read_text(encoding="utf-8")
    for text in [*LEAK_CORPUS, *REGRESSION_CORPUS, fixture]:
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


def findings_for(text: str, rule_id: str) -> list[style_check.Finding]:
    enabled = [r for r in rules.RULES if r.id == rule_id]
    assert enabled, f"no rule with id {rule_id}"
    return style_check.check_text(text, Path("t.md"), enabled)


def test_headings_flags_title_case_and_trailing_period():
    assert findings_for("## Setting Up Your Project\n", "headings")
    assert findings_for("## Set up your project.\n", "headings")
    assert not findings_for("## Set up your project\n", "headings")
    assert not findings_for("## Deploy to Google Cloud\n", "headings")


def test_oxford_comma_flags_two_comma_lists_only():
    assert findings_for("Fetch, parse and render the page.\n", "oxford-comma")
    assert not findings_for("Fetch, parse, and render the page.\n", "oxford-comma")
    assert not findings_for("However, the parser and the renderer differ.\n", "oxford-comma")
    assert not findings_for("If you are done, click Save and close the tab.\n", "oxford-comma")
    assert not findings_for("Save the file, then commit and push.\n", "oxford-comma")


def test_first_person_ignores_quoted_guidance():
    assert findings_for("We recommend pinning the version.\n", "first-person")
    assert not findings_for('The guide says "we recommend" here.\n', "first-person")
    assert not findings_for("> we recommend pinning the version\n", "first-person")
    # Two contractions must not pair into a phantom quote span that hides "we've".
    assert findings_for("It's true that we've seen it.\n", "first-person")


def test_future_covers_will_and_timeless():
    assert findings_for("Support is coming soon.\n", "future")
    assert findings_for("This is currently unsupported.\n", "future")
    assert not findings_for("The command stops the job.\n", "future")


def test_word_list_uses_the_data_file_severity():
    avoid = findings_for("Utilize the whitelist.\n", "word-list")
    assert {f.severity for f in avoid} == {"error"}
    restricted = findings_for("Clone the repo first.\n", "word-list")
    assert [f.severity for f in restricted] == ["warning"]


def test_date_format_flags_ambiguous_numeric_dates():
    assert findings_for("Released 03/04/25.\n", "date-format")
    assert not findings_for("Released March 4, 2025.\n", "date-format")
    assert not findings_for("Released 2025-03-04.\n", "date-format")


def test_excessive_claims_flags_just_only_before_a_verb():
    assert findings_for("Simply run the installer.\n", "excessive-claims")
    assert findings_for("Just run the installer.\n", "excessive-claims")
    assert not findings_for("The change is just under the limit.\n", "excessive-claims")


def test_link_text_flags_undescriptive_text():
    assert findings_for("See [click here](https://example.com).\n", "link-text")
    assert not findings_for("See the [word list](https://example.com).\n", "link-text")


def test_latin_splits_severity():
    hard = findings_for("Use a client, e.g. curl.\n", "latin")
    assert [f.severity for f in hard] == ["error"]
    soft = findings_for("Compare A vs. B.\n", "latin")
    assert [f.severity for f in soft] == ["warning"]


def test_em_dash_errors_on_double_hyphen_and_warns_on_spacing():
    hard = findings_for("The parser--the slow one--is next.\n", "em-dash")
    assert [f.severity for f in hard] == ["error", "error"]
    soft = findings_for("The parser — the slow one — is next.\n", "em-dash")
    assert {f.severity for f in soft} == {"warning"}


def test_spacing_flags_double_space_and_leading_space():
    assert findings_for("Done.  Next step.\n", "spacing")
    assert findings_for("Done , then go.\n", "spacing")
    assert not findings_for("Done. Next step.\n", "spacing")


def test_units_require_a_space():
    assert findings_for("Allocate 512MB of memory.\n", "units")
    assert not findings_for("Allocate 512 MB of memory.\n", "units")


def test_gendered_and_ableist_terms():
    assert findings_for("Ask the chairman or he/she who owns it.\n", "gendered")
    assert findings_for("Run a sanity check on the crazy output.\n", "ableist")
    assert not findings_for("Ask the person who owns it.\n", "gendered")


def test_please_is_flagged_in_instructions():
    assert findings_for("Please run the installer.\n", "please")


def test_ly_hyphens_respects_exceptions():
    assert findings_for("A newly-added feature.\n", "ly-hyphens")
    assert not findings_for("A supply-chain risk.\n", "ly-hyphens")
    assert not findings_for("An early-stage project.\n", "ly-hyphens")


def test_periods_flags_acronym_periods():
    assert findings_for("Servers in the U.S. only.\n", "periods")
    assert not findings_for("Servers in the US only.\n", "periods")


def test_am_pm_requires_space_and_capitals():
    assert findings_for("Starts at 10am.\n", "am-pm")
    assert findings_for("Starts at 10 a.m.\n", "am-pm")
    assert not findings_for("Starts at 10 AM.\n", "am-pm")


def test_oxford_comma_does_not_re_match_across_its_own_serial_comma():
    """A correct list plus a trailing verb pair: the later 'and' must not re-match."""
    assert not findings_for("Fetch, parse, and render the page and exit.\n", "oxford-comma")
    assert findings_for("Fetch, parse and render the page.\n", "oxford-comma")


def test_oxford_comma_skips_a_clause_continuation_opening_with_a_modal():
    """"…only, must not start or end with a hyphen" joins verbs, not list items."""
    assert not findings_for(
        "Names use lowercase and hyphens only, must not start or end with a hyphen.\n",
        "oxford-comma")
    assert not findings_for(
        "The path is optional, is read once and cached forever.\n", "oxford-comma")


def test_oxford_fix_text_quotes_raw_source_not_masked_text():
    """Masking is offset-preserving, so masked text renders inline code as spaces."""
    findings = findings_for("Fetch, parse the `--force` flag and render.\n", "oxford-comma")
    assert findings
    assert "`--force`" in findings[0].fix
    assert "  " not in findings[0].fix


def test_ly_hyphens_allows_adjectival_ly_words():
    """daily-use is a compound modifier, not an adverb wearing a stray hyphen."""
    assert not findings_for("A daily-use skill.\n", "ly-hyphens")
    assert not findings_for("A weekly-scheduled job.\n", "ly-hyphens")
    assert not findings_for("A costly-to-run query.\n", "ly-hyphens")
    assert findings_for("A newly-added feature.\n", "ly-hyphens")


def test_spacing_still_reports_a_real_space_before_a_comma_after_inline_code():
    """The raw-span guard must not swallow the space the author actually typed."""
    assert findings_for("A `b` , c\n", "spacing")
    assert findings_for("Use `--force` , then go.\n", "spacing")
    assert not findings_for("Use `--force`, then go.\n", "spacing")
