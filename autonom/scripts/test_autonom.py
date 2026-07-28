"""Tests for autonom.py — the deterministic spine of the autonom skill."""
import json
from pathlib import Path

import pytest

import autonom


@pytest.fixture(autouse=True)
def _stub_dependency_check(monkeypatch, request):
    """Every test assumes superpowers is installed, so the suite does not depend
    on the machine it runs on. TestDependencyCheck opts out to exercise the real
    detection."""
    if getattr(request.cls, "real_dependency_check", False):
        return
    monkeypatch.setattr(autonom, "superpowers_present", lambda cache=None: True)


class TestSlugify:
    def test_lowercases_and_hyphenates(self):
        assert autonom.slugify("Autonom Pipeline") == "autonom-pipeline"

    def test_strips_punctuation(self):
        assert autonom.slugify("spec -> plan, unattended!") == "spec-plan-unattended"

    def test_transliterates_non_ascii(self):
        assert autonom.slugify("café résumé") == "cafe-resume"

    def test_drops_unmappable_characters(self):
        assert autonom.slugify("日本語 pipeline") == "pipeline"

    def test_truncates_to_sixty_chars_without_trailing_hyphen(self):
        slug = autonom.slugify("word " * 40)
        assert len(slug) <= 60
        assert not slug.endswith("-")

    def test_empty_slug_is_an_error(self):
        with pytest.raises(ValueError):
            autonom.slugify("日本語")


class TestComputePaths:
    def test_builds_every_path_from_root_slug_and_date(self, tmp_path):
        paths = autonom.compute_paths(tmp_path, "demo", "2026-07-28")
        assert paths["spec"] == str(
            tmp_path / "docs/superpowers/specs/2026-07-28-demo-design.md"
        )
        assert paths["plan"] == str(
            tmp_path / "docs/superpowers/plans/2026-07-28-demo.md"
        )
        assert paths["run_dir"] == str(tmp_path / ".superpowers/autonom/demo")
        assert paths["ledger"] == str(
            tmp_path / ".superpowers/autonom/demo/progress.md"
        )
        assert paths["escalations"] == str(
            tmp_path / ".superpowers/autonom/demo/escalations.md"
        )


class TestInit:
    def test_creates_run_dir_and_ledger_header_and_prints_json(self, tmp_path, capsys):
        rc = autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                           "--date", "2026-07-28"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["slug"] == "demo-topic"
        assert payload["next_step"] == 6
        ledger = tmp_path / ".superpowers/autonom/demo-topic/progress.md"
        assert ledger.read_text().splitlines()[0] == (
            "# autonom run — topic: Demo Topic — slug: demo-topic — date: 2026-07-28"
        )

    def test_reinit_same_topic_resumes_instead_of_restarting(self, tmp_path, capsys):
        autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                      "--date", "2026-07-28"])
        capsys.readouterr()
        rc = autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                           "--date", "2026-07-28"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["resumed"] is True
        assert payload["next_step"] == 6

    def test_slug_collision_with_different_topic_is_an_error(self, tmp_path, capsys):
        autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                      "--date", "2026-07-28"])
        capsys.readouterr()
        rc = autonom.main(["init", "demo topic!", "--root", str(tmp_path),
                           "--date", "2026-07-28"])
        assert rc == 2
        assert "collides" in capsys.readouterr().err

    def test_init_gitignores_the_run_directory(self, tmp_path, capsys):
        autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                      "--date", "2026-07-28"])
        assert ".superpowers/" in (tmp_path / ".gitignore").read_text()

    def test_init_does_not_duplicate_an_existing_gitignore_entry(self, tmp_path, capsys):
        (tmp_path / ".gitignore").write_text("node_modules/\n.superpowers/\n")
        autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                      "--date", "2026-07-28"])
        assert (tmp_path / ".gitignore").read_text().count(".superpowers/") == 1


class TestErrorContracts:
    def test_init_outside_a_git_repo_returns_usage_error(self, tmp_path, capsys,
                                                          monkeypatch):
        monkeypatch.chdir(tmp_path)
        rc = autonom.main(["init", "Demo Topic", "--date", "2026-07-28"])
        assert rc == 2
        assert "not inside a git repository" in capsys.readouterr().err

    def test_init_with_an_unreadable_ledger_header_returns_usage_error(
        self, tmp_path, capsys
    ):
        run_dir = tmp_path / ".superpowers" / "autonom" / "demo-topic"
        run_dir.mkdir(parents=True)
        (run_dir / "progress.md").write_text("not a valid header\n")
        rc = autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                           "--date", "2026-07-28"])
        assert rc == 2
        assert "unreadable ledger header" in capsys.readouterr().err


class TestDependencyCheck:
    real_dependency_check = True

    def _fake_cache(self, tmp_path, present: bool):
        cache = tmp_path / "plugins"
        if present:
            (cache / "claude-plugins-official/superpowers/6.2.0/skills"
             / "subagent-driven-development").mkdir(parents=True)
            (cache / "claude-plugins-official/superpowers/6.2.0/skills"
             / "subagent-driven-development/SKILL.md").write_text("x")
        else:
            cache.mkdir(parents=True)
        return cache

    def test_detects_an_installed_superpowers_plugin(self, tmp_path):
        assert autonom.superpowers_present(self._fake_cache(tmp_path, True)) is True

    def test_detects_a_missing_superpowers_plugin(self, tmp_path):
        assert autonom.superpowers_present(self._fake_cache(tmp_path, False)) is False

    def test_init_fails_and_names_the_dependency_when_missing(self, tmp_path, capsys):
        cache = self._fake_cache(tmp_path, False)
        rc = autonom.main(["init", "Demo Topic", "--root", str(tmp_path),
                           "--date", "2026-07-28", "--plugin-cache", str(cache)])
        assert rc == 2
        assert "superpowers" in capsys.readouterr().err


class TestLedgerAndStatus:
    def _init(self, tmp_path, capsys, topic="Demo Topic"):
        autonom.main(["init", topic, "--root", str(tmp_path), "--date", "2026-07-28"])
        capsys.readouterr()

    def test_ledger_appends_a_line_with_commit(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = autonom.main(["ledger", "6", "complete", "--slug", "demo-topic",
                           "--root", str(tmp_path), "--commit", "abc1234"])
        assert rc == 0
        text = (tmp_path / ".superpowers/autonom/demo-topic/progress.md").read_text()
        assert text.splitlines()[1] == "step 6 complete commit=abc1234"

    def test_ledger_is_append_only(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        for step in (6, 7):
            autonom.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                          "--root", str(tmp_path)])
        lines = (tmp_path / ".superpowers/autonom/demo-topic/progress.md").read_text().splitlines()
        assert lines[1] == "step 6 complete"
        assert lines[2] == "step 7 complete"

    def test_status_with_slug_reports_the_resume_point(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        autonom.main(["ledger", "6", "complete", "--slug", "demo-topic",
                      "--root", str(tmp_path)])
        capsys.readouterr()
        rc = autonom.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 7
        assert payload["next_step_name"] == "review spec"
        assert payload["topic"] == "Demo Topic"

    def test_status_reports_none_when_the_run_is_complete(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        for step in (6, 7, 8, 9):
            autonom.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                          "--root", str(tmp_path)])
        capsys.readouterr()
        autonom.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["next_step"] is None

    def test_bare_status_lists_every_run(self, tmp_path, capsys):
        self._init(tmp_path, capsys, topic="Alpha Feature")
        self._init(tmp_path, capsys, topic="Beta Feature")
        autonom.main(["ledger", "6", "complete", "--slug", "alpha-feature",
                      "--root", str(tmp_path)])
        capsys.readouterr()
        rc = autonom.main(["status", "--root", str(tmp_path)])
        assert rc == 0
        runs = json.loads(capsys.readouterr().out)
        assert [r["slug"] for r in runs] == ["alpha-feature", "beta-feature"]
        assert [r["next_step"] for r in runs] == [7, 6]

    def test_bare_status_on_a_repo_with_no_runs_prints_an_empty_list(self, tmp_path, capsys):
        rc = autonom.main(["status", "--root", str(tmp_path)])
        assert rc == 0
        assert json.loads(capsys.readouterr().out) == []

    def test_status_for_an_unknown_slug_is_an_error(self, tmp_path, capsys):
        rc = autonom.main(["status", "nope", "--root", str(tmp_path)])
        assert rc == 2
        assert "no run" in capsys.readouterr().err


SPEC_OK = """# Demo Design Spec

## Problem

Things are bad.

## Architecture

A box connected to another box.

## Error handling

Everything stops loudly.

## Testing

We test it.
"""


class TestStripCode:
    def test_blanks_inline_code_but_keeps_line_count(self):
        out = autonom.strip_code("alpha `TODO` omega\nsecond line\n")
        assert "TODO" not in out
        assert out.splitlines()[0].startswith("alpha ")
        assert len(out.splitlines()) == 2

    def test_blanks_fenced_blocks(self):
        text = "before\n```\nTODO inside a fence\n```\nafter\n"
        out = autonom.strip_code(text)
        assert "TODO" not in out
        assert out.splitlines()[0] == "before"
        assert out.splitlines()[4] == "after"

    def test_blanks_tilde_fences(self):
        out = autonom.strip_code("~~~\nTBD\n~~~\n")
        assert "TBD" not in out

    def test_leaves_ordinary_prose_untouched(self):
        assert autonom.strip_code("plain words\n") == "plain words\n"


class TestValidateSpec:
    def test_a_complete_spec_passes(self):
        assert autonom.validate_spec(SPEC_OK) == []

    def test_placeholder_markers_are_reported_with_line_numbers(self):
        findings = autonom.validate_spec(SPEC_OK + "\nStill TODO here.\n")
        assert len(findings) == 1
        assert findings[0].line == 19
        assert "TODO" in findings[0].message

    def test_markers_inside_code_spans_are_ignored(self):
        assert autonom.validate_spec(SPEC_OK + "\nWe scan for `TODO` markers.\n") == []

    def test_missing_section_is_reported(self):
        text = SPEC_OK.replace("## Testing\n\nWe test it.\n", "")
        messages = " ".join(f.message for f in autonom.validate_spec(text))
        assert "testing" in messages.lower()

    def test_empty_section_body_is_reported(self):
        text = SPEC_OK.replace("Everything stops loudly.\n", "")
        messages = " ".join(f.message for f in autonom.validate_spec(text))
        assert "empty" in messages.lower()

    def test_missing_title_is_reported(self):
        text = SPEC_OK.replace("# Demo Design Spec\n", "")
        messages = " ".join(f.message for f in autonom.validate_spec(text))
        assert "title" in messages.lower()

    def test_open_question_marker_is_reported(self):
        findings = autonom.validate_spec(SPEC_OK + "\n**Open question:** which one?\n")
        assert any("open question" in f.message.lower() for f in findings)

    def test_heading_keyword_matching_does_not_match_substrings(self):
        text = SPEC_OK.replace("## Testing", "## Latest news")
        messages = " ".join(f.message for f in autonom.validate_spec(text))
        assert "testing" in messages.lower()

    def test_the_title_cannot_satisfy_a_section_requirement(self):
        text = SPEC_OK.replace(
            "## Architecture\n\nA box connected to another box.\n\n", ""
        )
        messages = " ".join(f.message for f in autonom.validate_spec(text))
        assert "architecture" in messages.lower()

    def test_the_design_spec_is_the_passing_fixture(self):
        spec = (
            Path.home()
            / "files/projects/001-claude-skills-creator"
            / "docs/superpowers/specs/2026-07-28-autonom-design.md"
        )
        if not spec.exists():
            pytest.skip("workshop spec not present in this checkout")
        assert autonom.validate_spec(spec.read_text(encoding="utf-8")) == []


class TestValidateCLI:
    def test_passing_spec_exits_zero(self, tmp_path, capsys):
        target = tmp_path / "spec.md"
        target.write_text(SPEC_OK)
        assert autonom.main(["validate", "spec", str(target)]) == 0
        assert "OK" in capsys.readouterr().out

    def test_failing_spec_exits_one_and_lists_findings(self, tmp_path, capsys):
        target = tmp_path / "spec.md"
        target.write_text(SPEC_OK + "\nTBD\n")
        assert autonom.main(["validate", "spec", str(target)]) == 1
        assert "spec.md:19:" in capsys.readouterr().out

    def test_missing_file_exits_two(self, tmp_path, capsys):
        assert autonom.main(["validate", "spec", str(tmp_path / "nope.md")]) == 2
        assert "cannot read" in capsys.readouterr().err
