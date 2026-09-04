"""Tests for orko.py — the deterministic spine of the orko skill."""
import json
from pathlib import Path

import pytest

import orko


class TestSlugify:
    def test_lowercases_and_hyphenates(self):
        assert orko.slugify("Orko Pipeline") == "orko-pipeline"

    def test_strips_punctuation(self):
        assert orko.slugify("spec -> plan, unattended!") == "spec-plan-unattended"

    def test_transliterates_non_ascii(self):
        assert orko.slugify("café résumé") == "cafe-resume"

    def test_drops_unmappable_characters(self):
        assert orko.slugify("日本語 pipeline") == "pipeline"

    def test_truncates_to_sixty_chars_without_trailing_hyphen(self):
        slug = orko.slugify("word " * 40)
        assert len(slug) <= 60
        assert not slug.endswith("-")

    def test_empty_slug_is_an_error(self):
        with pytest.raises(ValueError):
            orko.slugify("日本語")


class TestComputePaths:
    def test_builds_every_path_under_the_run_dir(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        run_dir = tmp_path / ".orko/demo"
        assert paths["run_dir"] == str(run_dir)
        assert paths["ledger"] == str(run_dir / "progress.md")
        assert paths["escalations"] == str(run_dir / "escalations.md")
        assert paths["spec"] == str(run_dir / "spec.md")
        assert paths["plan"] == str(run_dir / "plan.md")
        assert paths["brief"] == str(run_dir / "brief.md")
        assert paths["synthesis"] == str(run_dir / "synthesis.md")
        assert paths["findings_dir"] == str(run_dir / "findings")
        assert paths["context_dir"] == str(run_dir / "context")
        assert paths["unposted_dir"] == str(run_dir / "unposted")

    def test_no_shipped_path_points_outside_the_run_dir(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        for key, value in paths.items():
            if key in {"slug", "date", "root"}:
                continue
            assert value.startswith(str(tmp_path / ".orko/demo")), key


class TestInit:
    def test_creates_run_dir_and_ledger_header_and_prints_json(self, tmp_path, capsys):
        rc = orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-09-04"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["slug"] == "demo-topic"
        assert payload["mode"] == "build"
        assert payload["team"] == "JRF"
        assert payload["next_step"] == 0
        ledger = tmp_path / ".orko/demo-topic/progress.md"
        assert ledger.read_text().splitlines()[0] == (
            "# orko run — mode: build — team: JRF — topic: Demo Topic "
            "— slug: demo-topic — date: 2026-09-04"
        )

    def test_reinit_same_topic_resumes_instead_of_restarting(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-07-28"])
        capsys.readouterr()
        rc = orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-07-28"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["resumed"] is True
        assert payload["next_step"] == 0

    def test_slug_collision_with_different_topic_is_an_error(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-07-28"])
        capsys.readouterr()
        rc = orko.main(["init", "build", "demo topic!", "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-07-28"])
        assert rc == 2
        assert "collides" in capsys.readouterr().err

    def test_init_gitignores_the_run_directory(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-07-28"])
        assert ".orko/" in (tmp_path / ".gitignore").read_text()

    def test_init_does_not_duplicate_an_existing_gitignore_entry(self, tmp_path, capsys):
        (tmp_path / ".gitignore").write_text("node_modules/\n.orko/\n")
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-07-28"])
        assert (tmp_path / ".gitignore").read_text().count(".orko/") == 1


class TestModes:
    def _init(self, tmp_path, capsys, mode="build"):
        orko.main(["init", mode, "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        capsys.readouterr()

    def test_init_requires_a_team(self, tmp_path):
        with pytest.raises(SystemExit) as raised:
            orko.main(["init", "build", "Demo Topic", "--root", str(tmp_path)])
        assert raised.value.code == 2

    def test_init_rejects_a_lowercase_team_key(self, tmp_path, capsys):
        rc = orko.main(["init", "build", "Demo Topic", "--team", "jrf",
                        "--root", str(tmp_path)])
        assert rc == 2
        assert "team key" in capsys.readouterr().err

    def test_init_rejects_a_team_key_with_trailing_newline(self, tmp_path, capsys):
        rc = orko.main(["init", "build", "Demo Topic", "--team", "JRF\n",
                        "--root", str(tmp_path)])
        assert rc == 2
        assert "team key" in capsys.readouterr().err

    def test_analysis_run_starts_at_step_one(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        run = json.loads(capsys.readouterr().out)
        assert run["mode"] == "analysis"
        assert run["next_step"] == 1
        assert run["next_step_name"] == "open"

    def test_build_run_starts_at_intake(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        run = json.loads(capsys.readouterr().out)
        assert run["next_step"] == 0
        assert run["next_step_name"] == "intake"

    def test_ledger_rejects_a_step_outside_the_runs_mode(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["ledger", "7", "complete", "--slug", "demo-topic",
                        "--root", str(tmp_path)])
        assert rc == 2
        assert "analysis" in capsys.readouterr().err

    def test_ledger_rejects_step_zero_on_analysis(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["ledger", "0", "complete", "--slug", "demo-topic",
                        "--root", str(tmp_path)])
        assert rc == 2

    def test_reinit_with_a_different_mode_is_an_error(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["init", "analysis", "Demo Topic", "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-09-04"])
        assert rc == 2
        assert "mode" in capsys.readouterr().err

    def test_run_is_done_after_the_last_step_of_its_mode(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        for step in range(1, 7):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["next_step"] is None


class TestErrorContracts:
    def test_init_outside_a_git_repo_returns_usage_error(self, tmp_path, capsys,
                                                         monkeypatch):
        monkeypatch.chdir(tmp_path)
        rc = orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                        "--date", "2026-07-28"])
        assert rc == 2
        assert "not inside a git repository" in capsys.readouterr().err

    def test_init_with_an_unreadable_ledger_header_returns_usage_error(
        self, tmp_path, capsys
    ):
        run_dir = tmp_path / ".orko" / "demo-topic"
        run_dir.mkdir(parents=True)
        (run_dir / "progress.md").write_text("not a valid header\n")
        rc = orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-07-28"])
        assert rc == 2
        assert "unreadable ledger header" in capsys.readouterr().err

    def test_an_empty_ledger_reports_an_error_rather_than_crashing(
        self, tmp_path, capsys
    ):
        run_dir = tmp_path / ".orko" / "demo-topic"
        run_dir.mkdir(parents=True)
        (run_dir / "progress.md").write_text("")
        assert orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                          "--root", str(tmp_path), "--date", "2026-07-28"]) == 2
        assert "unreadable ledger header" in capsys.readouterr().err
        assert orko.main(["status", "demo-topic", "--root", str(tmp_path)]) == 2

    @pytest.mark.parametrize("topic", [
        "Demo\nTopic",
        "Demo\tTopic",
        "Demo\x00Topic",
    ])
    def test_a_topic_with_a_control_character_is_rejected(self, tmp_path, capsys,
                                                          topic):
        rc = orko.main(["init", "build", topic, "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-07-28"])
        assert rc == 2
        assert "control character" in capsys.readouterr().err
        assert not (tmp_path / ".orko").exists()

    def test_a_topic_that_slugifies_to_nothing_is_an_error_not_a_traceback(
        self, tmp_path, capsys
    ):
        rc = orko.main(["init", "build", "日本語", "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-07-28"])
        assert rc == 2
        assert "empty slug" in capsys.readouterr().err


class TestLedgerAndStatus:
    def _init(self, tmp_path, capsys, topic="Demo Topic"):
        orko.main(["init", "build", topic, "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-07-28"])
        capsys.readouterr()

    def _complete_through_spec(self, tmp_path, commit=None):
        """Walk a build run past intake and the spec step, to the spec review."""
        for step in (0, 1):
            argv = ["ledger", str(step), "complete", "--slug", "demo-topic",
                    "--root", str(tmp_path)]
            if commit and step == 1:
                argv += ["--commit", commit]
            orko.main(argv)

    def test_ledger_appends_a_line_with_commit(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["ledger", "1", "complete", "--slug", "demo-topic",
                        "--root", str(tmp_path), "--commit", "abc1234"])
        assert rc == 0
        text = (tmp_path / ".orko/demo-topic/progress.md").read_text()
        assert text.splitlines()[1] == "step 1 complete commit=abc1234"

    def test_ledger_is_append_only(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        for step in (1, 2):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--root", str(tmp_path)])
        lines = (tmp_path / ".orko/demo-topic/progress.md").read_text().splitlines()
        assert lines[1] == "step 1 complete"
        assert lines[2] == "step 2 complete"

    def test_ledger_records_a_dispatched_base_sha(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                        "--root", str(tmp_path), "--commit", "base123"])
        assert rc == 0
        text = (tmp_path / ".orko/demo-topic/progress.md").read_text()
        assert text.splitlines()[1] == "step 2 dispatched commit=base123"

    @pytest.mark.parametrize("status", ["dispatched", "escalated", "failed"])
    def test_only_complete_advances_the_resume_point(self, tmp_path, capsys, status):
        self._init(tmp_path, capsys)
        self._complete_through_spec(tmp_path)
        orko.main(["ledger", "2", status, "--slug", "demo-topic",
                   "--root", str(tmp_path), "--commit", "base123"])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["next_step"] == 2

    def test_status_with_slug_reports_the_resume_point(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        self._complete_through_spec(tmp_path)
        capsys.readouterr()
        rc = orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["next_step_name"] == "spec review"
        assert payload["topic"] == "Demo Topic"

    def test_status_reports_none_when_the_run_is_complete(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        for step in range(0, 8):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["next_step"] is None

    def test_bare_status_lists_every_run(self, tmp_path, capsys):
        self._init(tmp_path, capsys, topic="Alpha Feature")
        self._init(tmp_path, capsys, topic="Beta Feature")
        orko.main(["ledger", "0", "complete", "--slug", "alpha-feature",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        rc = orko.main(["status", "--root", str(tmp_path)])
        assert rc == 0
        runs = json.loads(capsys.readouterr().out)
        assert [r["slug"] for r in runs] == ["alpha-feature", "beta-feature"]
        assert [r["next_step"] for r in runs] == [1, 0]

    def test_bare_status_on_a_repo_with_no_runs_prints_an_empty_list(self, tmp_path, capsys):
        rc = orko.main(["status", "--root", str(tmp_path)])
        assert rc == 0
        assert json.loads(capsys.readouterr().out) == []

    def test_status_exposes_the_last_status_and_the_dispatched_base(
        self, tmp_path, capsys
    ):
        self._init(tmp_path, capsys)
        self._complete_through_spec(tmp_path, commit="aaa111")
        orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                   "--root", str(tmp_path), "--commit", "bbb222"])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["last_status"] == "dispatched"
        assert payload["dispatched_base"] == "bbb222"

    def test_a_fresh_run_reports_no_last_status_and_no_dispatched_base(
        self, tmp_path, capsys
    ):
        self._init(tmp_path, capsys)
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["last_status"] is None
        assert payload["dispatched_base"] is None

    def test_the_dispatched_base_is_scoped_to_the_step_being_resumed(
        self, tmp_path, capsys
    ):
        self._init(tmp_path, capsys)
        for step, status, commit in (
            (0, "complete", "000aaa"),
            (1, "complete", "aaa111"),
            (2, "dispatched", "bbb222"),
            (2, "complete", "ccc333"),
            (3, "complete", "ddd444"),
        ):
            orko.main(["ledger", str(step), status, "--slug", "demo-topic",
                       "--root", str(tmp_path), "--commit", commit])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 4
        assert payload["last_status"] == "complete"
        # Step 2's base must not leak into a step-4 resume.
        assert payload["dispatched_base"] is None

    def test_the_latest_dispatch_wins_when_a_step_was_dispatched_twice(
        self, tmp_path, capsys
    ):
        self._init(tmp_path, capsys)
        for commit in ("bbb222", "eee555"):
            orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                       "--root", str(tmp_path), "--commit", commit])
        self._complete_through_spec(tmp_path)
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["dispatched_base"] == "eee555"

    def test_an_escalated_line_is_the_last_status_after_a_completed_step(
        self, tmp_path, capsys
    ):
        self._init(tmp_path, capsys)
        self._complete_through_spec(tmp_path, commit="aaa111")
        orko.main(["ledger", "1", "escalated", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["last_status"] == "escalated"

    def test_a_malformed_ledger_line_is_skipped_not_fatal(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        ledger = tmp_path / ".orko/demo-topic/progress.md"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write("this is not a step record\n")
        self._complete_through_spec(tmp_path)
        capsys.readouterr()
        assert orko.main(["status", "demo-topic", "--root", str(tmp_path)]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["last_status"] == "complete"

    def test_status_for_an_unknown_slug_is_an_error(self, tmp_path, capsys):
        rc = orko.main(["status", "nope", "--root", str(tmp_path)])
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
        out = orko.strip_code("alpha `TODO` omega\nsecond line\n")
        assert "TODO" not in out
        assert out.splitlines()[0].startswith("alpha ")
        assert len(out.splitlines()) == 2

    def test_blanks_fenced_blocks(self):
        text = "before\n```\nTODO inside a fence\n```\nafter\n"
        out = orko.strip_code(text)
        assert "TODO" not in out
        assert out.splitlines()[0] == "before"
        assert out.splitlines()[4] == "after"

    def test_blanks_tilde_fences(self):
        out = orko.strip_code("~~~\nTBD\n~~~\n")
        assert "TBD" not in out

    def test_leaves_ordinary_prose_untouched(self):
        assert orko.strip_code("plain words\n") == "plain words\n"


class TestValidateSpec:
    def test_a_complete_spec_passes(self):
        assert orko.validate_spec(SPEC_OK) == []

    def test_placeholder_markers_are_reported_with_line_numbers(self):
        findings = orko.validate_spec(SPEC_OK + "\nStill TODO here.\n")
        assert len(findings) == 1
        assert findings[0].line == 19
        assert "TODO" in findings[0].message

    def test_markers_inside_code_spans_are_ignored(self):
        assert orko.validate_spec(SPEC_OK + "\nWe scan for `TODO` markers.\n") == []

    def test_missing_section_is_reported(self):
        text = SPEC_OK.replace("## Testing\n\nWe test it.\n", "")
        messages = " ".join(f.message for f in orko.validate_spec(text))
        assert "testing" in messages.lower()

    def test_empty_section_body_is_reported(self):
        text = SPEC_OK.replace("Everything stops loudly.\n", "")
        messages = " ".join(f.message for f in orko.validate_spec(text))
        assert "empty" in messages.lower()

    def test_missing_title_is_reported(self):
        text = SPEC_OK.replace("# Demo Design Spec\n", "")
        messages = " ".join(f.message for f in orko.validate_spec(text))
        assert "title" in messages.lower()

    def test_open_question_marker_is_reported(self):
        findings = orko.validate_spec(SPEC_OK + "\n**Open question:** which one?\n")
        assert any("open question" in f.message.lower() for f in findings)

    def test_heading_keyword_matching_does_not_match_substrings(self):
        text = SPEC_OK.replace("## Testing", "## Latest news")
        messages = " ".join(f.message for f in orko.validate_spec(text))
        assert "testing" in messages.lower()

    def test_the_title_cannot_satisfy_a_section_requirement(self):
        text = SPEC_OK.replace(
            "## Architecture\n\nA box connected to another box.\n\n", ""
        )
        messages = " ".join(f.message for f in orko.validate_spec(text))
        assert "architecture" in messages.lower()


class TestValidateCLI:
    def test_passing_spec_exits_zero(self, tmp_path, capsys):
        target = tmp_path / "spec.md"
        target.write_text(SPEC_OK)
        assert orko.main(["validate", "spec", str(target)]) == 0
        assert "OK" in capsys.readouterr().out

    def test_failing_spec_exits_one_and_lists_findings(self, tmp_path, capsys):
        target = tmp_path / "spec.md"
        target.write_text(SPEC_OK + "\nTBD\n")
        assert orko.main(["validate", "spec", str(target)]) == 1
        assert "spec.md:19:" in capsys.readouterr().out

    def test_missing_file_exits_two(self, tmp_path, capsys):
        assert orko.main(["validate", "spec", str(tmp_path / "nope.md")]) == 2
        assert "cannot read" in capsys.readouterr().err


PLAN_OK = """# Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Build the demo.

## Global Constraints

- Python 3.12+.

---

### Task 1: First component

**Files:**
- Create: `src/demo.py`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Commit**
"""


class TestValidatePlan:
    def test_a_complete_plan_passes(self):
        assert orko.validate_plan(PLAN_OK) == []

    def test_missing_required_sub_skill_header_is_reported(self):
        text = PLAN_OK.replace("REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development", "Go build it")
        messages = " ".join(f.message for f in orko.validate_plan(text))
        assert "REQUIRED SUB-SKILL" in messages

    def test_missing_global_constraints_is_reported(self):
        text = PLAN_OK.replace("## Global Constraints", "## Notes")
        messages = " ".join(f.message for f in orko.validate_plan(text))
        assert "Global Constraints" in messages

    def test_no_task_blocks_is_reported(self):
        text = PLAN_OK.replace("### Task 1: First component", "### Notes")
        messages = " ".join(f.message for f in orko.validate_plan(text))
        assert "task block" in messages.lower()

    def test_task_without_files_subsection_is_reported(self):
        text = PLAN_OK.replace("**Files:**\n- Create: `src/demo.py`\n", "")
        messages = " ".join(f.message for f in orko.validate_plan(text))
        assert "Files:" in messages

    def test_task_without_step_checkbox_is_reported(self):
        text = PLAN_OK.replace("- [ ] **Step 1: Write the failing test**\n", "")
        text = text.replace("- [ ] **Step 2: Commit**\n", "")
        messages = " ".join(f.message for f in orko.validate_plan(text))
        assert "checkbox" in messages.lower()

    @pytest.mark.parametrize("red_flag", [
        "Similar to Task 1",
        "Add appropriate error handling",
        "add validation",
        "handle edge cases",
        "Write tests for the above",
    ])
    def test_red_flags_are_reported(self, red_flag):
        messages = " ".join(
            f.message for f in orko.validate_plan(PLAN_OK + f"\n{red_flag}\n")
        )
        assert red_flag.lower().split()[0] in messages.lower()

    def test_red_flags_inside_code_spans_are_ignored(self):
        assert orko.validate_plan(
            PLAN_OK + "\nNever write `Similar to Task N` in a plan.\n"
        ) == []

    def test_placeholder_markers_are_reported(self):
        findings = orko.validate_plan(PLAN_OK + "\nTBD\n")
        assert any("TBD" in f.message for f in findings)


class TestPrompt:
    def _init(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-07-28"])
        capsys.readouterr()

    @pytest.mark.xfail(reason="rewritten in Task 6", strict=True)
    def test_spec_prompt_substitutes_every_token(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        assert orko.main(["prompt", "spec", "demo-topic",
                          "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert "{{" not in out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out
        assert str(tmp_path / ".orko/demo-topic") in out

    @pytest.mark.xfail(reason="rewritten in Task 6", strict=True)
    def test_plan_prompt_carries_the_spec_path_as_its_contract(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["prompt", "plan", "demo-topic", "--root", str(tmp_path)])
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/plan.md") in out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out

    @pytest.mark.xfail(reason="rewritten in Task 6", strict=True)
    def test_output_is_the_reference_file_verbatim_with_substitutions_only(
        self, tmp_path, capsys
    ):
        self._init(tmp_path, capsys)
        orko.main(["prompt", "spec", "demo-topic", "--root", str(tmp_path)])
        out = capsys.readouterr().out
        paths = orko.compute_paths(tmp_path, "demo-topic", "2026-07-28")
        expected = (orko.references_dir() / "spec-reviewer.md").read_text(
            encoding="utf-8"
        )
        expected = (expected
                    .replace("{{ARTIFACT_PATH}}", paths["spec"])
                    .replace("{{SPEC_PATH}}", paths["spec"])
                    .replace("{{RUN_DIR}}", paths["run_dir"])
                    .replace("{{ROOT}}", paths["root"])
                    .replace("{{SLUG}}", "demo-topic"))
        assert out == expected

    @pytest.mark.xfail(reason="rewritten in Task 6", strict=True)
    @pytest.mark.parametrize("kind", ["spec", "plan"])
    def test_prompt_anchors_the_reviewer_git_commands_to_the_run_root(
        self, tmp_path, capsys, kind
    ):
        self._init(tmp_path, capsys)
        assert orko.main(["prompt", kind, "demo-topic",
                          "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert f"git -C {tmp_path} add " in out
        assert f"git -C {tmp_path} commit -m " in out
        assert "\n    git add " not in out

    def test_unknown_slug_is_an_error(self, tmp_path, capsys):
        assert orko.main(["prompt", "spec", "nope", "--root", str(tmp_path)]) == 2
        assert "no run" in capsys.readouterr().err

    @pytest.mark.xfail(reason="rewritten in Task 6", strict=True)
    def test_both_reference_files_ship_and_carry_the_scope_carve_out(self):
        for name in ("spec-reviewer.md", "plan-reviewer.md"):
            text = (orko.references_dir() / name).read_text(encoding="utf-8")
            assert "{{ARTIFACT_PATH}}" in text
            assert "{{RUN_DIR}}" in text
            assert "{{ROOT}}" in text
            assert "escalations.md" in text


class TestEscalations:
    def _init(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-07-28"])
        capsys.readouterr()

    def _escalations_path(self, tmp_path) -> Path:
        return tmp_path / ".orko/demo-topic/escalations.md"

    def test_absent_file_exits_zero_and_prints_nothing(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        assert orko.main(["escalations", "demo-topic",
                          "--root", str(tmp_path)]) == 0
        assert capsys.readouterr().out == ""

    def test_empty_file_exits_zero(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        self._escalations_path(tmp_path).write_text("")
        assert orko.main(["escalations", "demo-topic",
                          "--root", str(tmp_path)]) == 0

    def test_whitespace_only_file_exits_zero(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        self._escalations_path(tmp_path).write_text("\n\n   \n\t\n")
        assert orko.main(["escalations", "demo-topic",
                          "--root", str(tmp_path)]) == 0
        assert capsys.readouterr().out == ""

    def test_file_with_content_exits_one_and_prints_it(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        self._escalations_path(tmp_path).write_text(
            "## Escalation\n\nThe spec contradicts itself about `007`.\n"
        )
        assert orko.main(["escalations", "demo-topic",
                          "--root", str(tmp_path)]) == 1
        out = capsys.readouterr().out
        assert "contradicts itself" in out
        assert out.endswith("\n")

    def test_unknown_slug_is_an_error(self, tmp_path, capsys):
        assert orko.main(["escalations", "nope", "--root", str(tmp_path)]) == 2
        assert "no run" in capsys.readouterr().err

    def test_outside_a_git_repo_is_an_error(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert orko.main(["escalations", "demo-topic"]) == 2
        assert "not inside a git repository" in capsys.readouterr().err
