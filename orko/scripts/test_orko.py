"""Tests for orko.py — the deterministic spine of the orko skill."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

import orko
from conftest import FIXTURE_WORKSPACE


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

    def test_truncates_on_a_word_boundary(self):
        slug = orko.slugify(
            "Add a subtract function with a test and a CLI entry point that "
            "reads two numbers from argv")
        assert slug == "add-a-subtract-function-with-a-test-and-a-cli-entry-point"
        assert len(slug) <= 60

    def test_hard_cuts_when_the_first_word_is_longer_than_the_limit(self):
        slug = orko.slugify("a" * 80)
        assert slug == "a" * 60

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
        assert payload["next_step"] == 0

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

    def test_init_creates_the_scratch_subdirectories(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        payload = json.loads(capsys.readouterr().out)
        for key in ("findings_dir", "context_dir", "unposted_dir"):
            assert Path(payload[key]).is_dir(), key

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

    def test_ledger_rejects_a_non_sha_commit(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["ledger", "1", "complete", "--slug", "demo-topic",
                        "--root", str(tmp_path), "--commit", "not a sha"])
        assert rc == 2
        assert "--commit must be a short or full SHA" in capsys.readouterr().err

    def test_ledger_accepts_a_sha_range_as_a_dispatched_base(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        self._complete_through_spec(tmp_path)
        rc = orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                        "--root", str(tmp_path), "--commit", "ba5e123..dec0de1"])
        assert rc == 0
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["dispatched_base"] == (
            "ba5e123..dec0de1"
        )

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
                        "--root", str(tmp_path), "--commit", "ba5e123"])
        assert rc == 0
        text = (tmp_path / ".orko/demo-topic/progress.md").read_text()
        assert text.splitlines()[1] == "step 2 dispatched commit=ba5e123"

    @pytest.mark.parametrize("status", ["dispatched", "escalated", "failed"])
    def test_only_complete_advances_the_resume_point(self, tmp_path, capsys, status):
        self._init(tmp_path, capsys)
        self._complete_through_spec(tmp_path)
        orko.main(["ledger", "2", status, "--slug", "demo-topic",
                   "--root", str(tmp_path), "--commit", "ba5e123"])
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
        self._complete_through_spec(tmp_path, commit="aaa1111")
        orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                   "--root", str(tmp_path), "--commit", "bbb2222"])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["last_status"] == "dispatched"
        assert payload["dispatched_base"] == "bbb2222"

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
            (0, "complete", "000aaa0"),
            (1, "complete", "aaa1111"),
            (2, "dispatched", "bbb2222"),
            (2, "complete", "ccc3333"),
            (3, "complete", "ddd4444"),
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
        for commit in ("bbb2222", "eee5555"):
            orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                       "--root", str(tmp_path), "--commit", commit])
        self._complete_through_spec(tmp_path)
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["dispatched_base"] == "eee5555"

    def test_an_escalated_line_is_the_last_status_after_a_completed_step(
        self, tmp_path, capsys
    ):
        self._init(tmp_path, capsys)
        self._complete_through_spec(tmp_path, commit="aaa1111")
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


class TestValidateCLI:
    def test_passing_tasks_exits_zero(self, tmp_path, capsys):
        target = tmp_path / "tasks.md"
        target.write_text(PLAN_OK)
        assert orko.main(["check", "tasks", str(target)]) == 0
        assert "OK" in capsys.readouterr().out

    def test_failing_tasks_exits_one_and_lists_findings(self, tmp_path, capsys):
        target = tmp_path / "tasks.md"
        target.write_text(PLAN_OK + "\nTBD\n")
        assert orko.main(["check", "tasks", str(target)]) == 1
        assert "tasks.md:" in capsys.readouterr().out

    def test_missing_file_exits_two(self, tmp_path, capsys):
        assert orko.main(["check", "tasks", str(tmp_path / "nope.md")]) == 2
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
    def _init(self, tmp_path, capsys, mode="build"):
        orko.main(["init", mode, "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        capsys.readouterr()

    def test_spec_review_substitutes_every_token_including_the_lens(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        assert orko.main(["prompt", "spec-review", "demo-topic", "--lens", "security",
                          "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert "{{" not in out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out
        assert str(tmp_path / ".orko/demo-topic/findings/security.md") in out
        assert "Your lens is **security**" in out
        assert "trust boundary" in out
        assert "## Lenses" not in out

    def test_plan_review_carries_the_spec_path(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["prompt", "plan-review", "demo-topic", "--lens", "coverage",
                   "--root", str(tmp_path)])
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/plan.md") in out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out
        assert "{{" not in out

    def test_unknown_lens_is_a_usage_error_naming_the_valid_ones(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["prompt", "spec-review", "demo-topic", "--lens", "vibes",
                        "--root", str(tmp_path)])
        assert rc == 2
        err = capsys.readouterr().err
        for lens in ("requirements", "architecture", "testability", "security"):
            assert lens in err

    def test_review_kinds_require_a_lens(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["prompt", "plan-review", "demo-topic", "--root", str(tmp_path)])
        assert rc == 2

    def test_plan_write_names_both_artifact_paths(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        assert orko.main(["prompt", "plan-write", "demo-topic",
                          "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out
        assert str(tmp_path / ".orko/demo-topic/plan.md") in out
        assert "{{" not in out

    def test_seat_prompt_inlines_the_context_file(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("Look at src/hot.py\n")
        assert orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                          "--question", "Where is the N+1?",
                          "--context-file", str(ctx), "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert "You are the perf on an orko engagement" in out
        assert "Where is the N+1?" in out
        assert "Look at src/hot.py" in out
        assert str(tmp_path / ".orko/demo-topic/findings/perf.md") in out
        assert "{{" not in out

    def test_verifier_prompt_names_findings_and_verdict_paths(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--root", str(tmp_path)])
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/findings/perf.md") in out
        assert str(tmp_path / ".orko/demo-topic/findings/perf.verdict.md") in out
        assert "{{" not in out

    def test_seat_records_the_question_for_a_later_verifier(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--root", str(tmp_path)])
        recorded = tmp_path / ".orko/demo-topic/context/perf.question"
        assert recorded.read_text(encoding="utf-8") == "Where is the N+1?"

    def test_verifier_reads_the_recorded_question_when_none_is_passed(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--root", str(tmp_path)])
        capsys.readouterr()
        assert orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                          "--context-file", str(ctx), "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/findings/perf.verdict.md") in out
        assert "{{" not in out

    def test_verifier_without_a_question_or_a_record_is_a_usage_error(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        rc = orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                        "--context-file", str(ctx), "--root", str(tmp_path)])
        assert rc == 2
        assert "no recorded question for seat perf" in capsys.readouterr().err

    def test_context_containing_template_tokens_is_passed_through(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("see {{ROOT}} and {{SEAT}}\n")
        assert orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                          "--question", "Where is the N+1?",
                          "--context-file", str(ctx), "--root", str(tmp_path)]) == 0
        assert "see {{ROOT}} and {{SEAT}}" in capsys.readouterr().out

    def test_seat_kinds_require_seat_question_and_context(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                        "--root", str(tmp_path)])
        assert rc == 2

    def test_missing_context_file_is_an_io_error(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                        "--question", "q", "--context-file", str(tmp_path / "nope.md"),
                        "--root", str(tmp_path)])
        assert rc == 2

    def test_no_charter_mentions_git_or_write_authority(self):
        for name in ("spec-reviewer.md", "plan-reviewer.md"):
            text = (orko.references_dir() / name).read_text(encoding="utf-8")
            assert "git -C" not in text
            assert "write authority on the spec" not in text
            assert "write authority on the plan" not in text
            assert "Report only" in text

    def test_lens_table_parses(self):
        text = (orko.references_dir() / "spec-reviewer.md").read_text(encoding="utf-8")
        lenses = orko._lenses(text)
        assert set(lenses) == {"requirements", "architecture", "testability", "security"}
        assert lenses["security"].endswith("handled?")


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


class TestPreflight:
    def _repo(self, tmp_path, branch="feat/x"):
        subprocess.run(["git", "init", "-q", "-b", branch, str(tmp_path)], check=True)
        return tmp_path

    def test_clean_repo_on_feature_branch_passes(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 0

    def test_master_fails_for_build(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 1
        assert "on-default-branch" in capsys.readouterr().out

    def test_master_is_fine_for_analysis(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "analysis"]) == 0

    def test_missing_uv_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: None)
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 1
        assert "uv-missing" in capsys.readouterr().out

    def test_unignored_run_dir_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 1
        assert "run-dir-not-ignored" in capsys.readouterr().out

    def test_slug_supplies_the_mode(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        orko.main(["init", "build", "Demo", "--team", "JRF", "--root", str(root),
                   "--date", "2026-09-04"])
        capsys.readouterr()
        assert orko.main(["preflight", "--root", str(root), "--slug", "demo"]) == 1
        assert "on-default-branch" in capsys.readouterr().out

    def test_outstanding_escalation_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        orko.main(["init", "build", "Demo", "--team", "JRF", "--root", str(root),
                   "--date", "2026-09-04"])
        (root / ".orko/demo/escalations.md").write_text("## Scope\n\nbody\n")
        capsys.readouterr()
        assert orko.main(["preflight", "--root", str(root), "--slug", "demo"]) == 1
        assert "blocked-escalation" in capsys.readouterr().out

    def test_not_a_repo_is_exit_two(self, tmp_path, capsys):
        assert orko.main(["preflight", "--root", str(tmp_path), "--mode", "build"]) == 2


class TestFixtures:
    """The validator's required shape derives from a real artifact, not an
    imagined structure. A rule change that rejects the fixture fails here."""

    def test_plan_fixture_passes(self):
        text = (Path(orko.__file__).parent / "fixtures/tasks.md").read_text(encoding="utf-8")
        assert orko.validate_plan(text) == []

    def test_fixtures_carry_no_stale_run_paths(self):
        text = (Path(orko.__file__).parent / "fixtures/tasks.md").read_text(encoding="utf-8")
        assert "docs/sessions/" not in orko.strip_code(text).replace(
            "`docs/sessions/`", "")


class TestFixtureWorkspace:
    def test_both_repos_on_master_with_one_commit(self, workspace):
        for repo in ("docs", "code"):
            out = subprocess.run(["git", "-C", str(workspace / repo), "log", "--oneline"],
                                 capture_output=True, text=True, check=True).stdout
            assert len(out.splitlines()) == 1
            branch = subprocess.run(["git", "-C", str(workspace / repo), "symbolic-ref", "--short", "HEAD"],
                                    capture_output=True, text=True, check=True).stdout.strip()
            assert branch == "master"

    def test_spec_check_is_executable(self, workspace):
        script = workspace / "code" / "scripts" / "spec-check.sh"
        result = subprocess.run([str(script)], capture_output=True, text=True)
        assert result.returncode == 2  # usage: no SPEC id given

    def test_spec_check_matches_scaffold_when_present(self):
        scaffold = Path.home() / "files/repo/project-scaffold-ai/project-name/code/scripts/spec-check.sh"
        if not scaffold.exists():
            pytest.skip("scaffold not checked out")
        ours = FIXTURE_WORKSPACE / "code/scripts/spec-check.sh"
        assert hashlib.sha256(ours.read_bytes()).hexdigest() == hashlib.sha256(scaffold.read_bytes()).hexdigest()


class TestWorkspace:
    def test_valid_fixture_has_no_findings(self, workspace):
        assert orko.validate_workspace(workspace) == []

    def test_refuses_docs_not_a_repo(self, workspace):
        shutil.rmtree(workspace / "docs" / ".git")
        assert orko.validate_workspace(workspace) == ["docs-not-a-repo"]

    def test_refuses_code_not_a_repo(self, workspace):
        shutil.rmtree(workspace / "code" / ".git")
        assert orko.validate_workspace(workspace) == ["code-not-a-repo"]

    def test_refuses_versions_missing(self, workspace):
        shutil.rmtree(workspace / "docs" / "versions")
        assert orko.validate_workspace(workspace) == ["versions-missing"]

    def test_refuses_spec_check_missing(self, workspace):
        (workspace / "code" / "scripts" / "spec-check.sh").unlink()
        assert orko.validate_workspace(workspace) == ["spec-check-missing"]

    def test_find_workspace_walks_up_from_docs_and_code(self, workspace):
        (workspace / ".orko").mkdir()
        assert orko.find_workspace(workspace / "docs" / "templates") == workspace
        assert orko.find_workspace(workspace / "code" / "scripts") == workspace
        assert orko.find_workspace(workspace) == workspace

    def test_find_workspace_requires_orko_dir(self, workspace):
        assert orko.find_workspace(workspace) is None

    def test_find_workspace_outside_is_none(self, tmp_path):
        assert orko.find_workspace(tmp_path) is None
