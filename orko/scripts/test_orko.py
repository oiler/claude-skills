"""Tests for orko.py — the deterministic spine of the orko skill."""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import orko
from conftest import FIXTURE_WORKSPACE


def init_run(workspace, capsys, mode="build", topic="Demo Topic", *extra):
    code = orko.main(["init", mode, topic, "--workspace", str(workspace),
                      "--owner", "oiler", "--boundaries", "code/ only",
                      "--trailer", "Co-Authored-By: T <t@example.invalid>",
                      "--trailer", "Claude-Session: https://example.invalid/s", *extra])
    captured = capsys.readouterr()
    out = captured.out
    return code, (json.loads(out) if out.strip().startswith("{") else captured.err)


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
    def test_builds_every_path_from_the_workspace_and_slug(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        run_dir = tmp_path / ".orko/demo"
        assert paths["workspace"] == str(tmp_path)
        assert paths["docs"] == str(tmp_path / "docs")
        assert paths["code"] == str(tmp_path / "code")
        assert paths["run_dir"] == str(run_dir)
        assert paths["ledger"] == str(run_dir / "progress.md")
        assert paths["escalations"] == str(run_dir / "escalations.md")
        assert paths["tasks"] == str(run_dir / "tasks.md")
        assert paths["brief"] == str(run_dir / "brief.md")
        assert paths["synthesis"] == str(run_dir / "synthesis.md")
        assert paths["findings_dir"] == str(run_dir / "findings")
        assert paths["context_dir"] == str(run_dir / "context")

    def test_the_run_dir_hangs_off_the_workspace_root(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        assert Path(paths["run_dir"]) == tmp_path / ".orko" / "demo"

    def test_no_scratch_path_points_outside_the_run_dir(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        for key, value in paths.items():
            if key in {"slug", "date", "workspace", "docs", "code"}:
                continue
            assert value.startswith(str(tmp_path / ".orko/demo")), key

    def test_no_run_artifact_lives_in_either_repository(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        for key, value in paths.items():
            if key in {"slug", "date", "workspace", "docs", "code"}:
                continue
            assert not value.startswith(str(tmp_path / "docs")), key
            assert not value.startswith(str(tmp_path / "code")), key


class TestInit:
    def test_writes_json_header_with_every_field(self, workspace, capsys):
        code, payload = init_run(workspace, capsys)
        assert code == 0
        ledger = Path(payload["ledger"]).read_text(encoding="utf-8").splitlines()
        assert ledger[0] == "# orko run"
        header = json.loads(ledger[1].removeprefix("header: "))
        assert header["mode"] == "build" and header["owner"] == "oiler"
        assert header["version"] == "0.1" and header["executor"] == "claude"
        assert header["codex_model"] is None and header["boundaries"] == "code/ only"
        assert len(header["trailers"]) == 2
        assert payload["docs"] == str(workspace / "docs")

    def test_run_dir_is_under_workspace_root(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        assert Path(payload["run_dir"]) == workspace / ".orko" / "demo-topic"
        assert not (workspace / ".gitignore").exists()

    def test_records_codex_executor_and_overrides(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic",
                              "--executor", "codex", "--codex-model", "gpt-5.6-sol",
                              "--codex-effort", "high")
        assert payload["executor"] == "codex" and payload["codex_model"] == "gpt-5.6-sol"

    def test_refuses_invalid_workspace_by_name(self, workspace, capsys):
        (workspace / "code" / "scripts" / "spec-check.sh").unlink()
        code, err = init_run(workspace, capsys)
        assert code == 2
        assert "spec-check-missing" in err

    def test_refuses_inactive_dossier(self, workspace, capsys):
        readme = workspace / "docs" / "versions" / "0.1" / "README.md"
        readme.write_text(readme.read_text().replace("status: active", "status: closed"))
        code, _ = init_run(workspace, capsys)
        assert code == 2

    def test_version_override(self, workspace, capsys):
        shutil.copytree(workspace / "docs/versions/0.1", workspace / "docs/versions/0.2")
        _, payload = init_run(workspace, capsys, "build", "Demo Topic", "--version", "0.2")
        assert payload["version"] == "0.2"

    def test_resume_keeps_header_and_reports_resumed(self, workspace, capsys):
        init_run(workspace, capsys)
        _, payload = init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        assert payload["resumed"] is True and payload["executor"] == "claude"

    def test_mode_collision_is_refused(self, workspace, capsys):
        init_run(workspace, capsys)
        code, _ = init_run(workspace, capsys, "analysis")
        assert code == 2

    def test_topic_collision_on_same_slug_is_refused(self, workspace, capsys):
        init_run(workspace, capsys, "build", "Demo Topic")
        code, _ = init_run(workspace, capsys, "build", "demo topic!")
        assert code == 2

    def test_creates_the_scratch_subdirectories(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        for key in ("findings_dir", "context_dir"):
            assert Path(payload[key]).is_dir(), key

    def test_reports_the_first_step_of_the_mode(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        assert payload["slug"] == "demo-topic"
        assert payload["mode"] == "build"
        assert payload["next_step"] == 0
        assert payload["resumed"] is False


class TestDossier:
    def test_reads_the_active_version_from_status(self, workspace):
        assert orko.read_active_version(workspace) == "0.1"

    def test_dossier_dir_is_under_docs_versions(self, workspace):
        assert orko.dossier_dir(workspace, "0.1") == workspace / "docs/versions/0.1"

    def test_reads_the_dossier_status(self, workspace):
        assert orko.dossier_status(workspace, "0.1") == "active"

    def test_missing_file_reads_as_none(self, workspace):
        assert orko.dossier_status(workspace, "9.9") is None

    def test_missing_frontmatter_reads_as_none(self, workspace, tmp_path):
        target = tmp_path / "plain.md"
        target.write_text("# No frontmatter\n\nactive_version: 0.2\n")
        assert orko.read_frontmatter_field(target, "active_version") is None

    def test_no_active_version_is_a_usage_error(self, workspace, capsys):
        status = workspace / "docs" / "STATUS.md"
        status.write_text(status.read_text().replace('active_version: "0.1"', "owner: x"))
        code, err = init_run(workspace, capsys)
        assert code == 2
        assert "active_version" in err


class TestModes:
    def test_analysis_run_starts_at_step_one(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        run = json.loads(capsys.readouterr().out)
        assert run["mode"] == "analysis"
        assert run["next_step"] == 1
        assert run["next_step_name"] == "open"

    def test_build_run_starts_at_intake(self, workspace, capsys):
        init_run(workspace, capsys)
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        run = json.loads(capsys.readouterr().out)
        assert run["next_step"] == 0
        assert run["next_step_name"] == "intake"

    def test_ledger_rejects_a_step_outside_the_runs_mode(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        rc = orko.main(["ledger", "7", "complete", "--slug", "demo-topic",
                        "--workspace", str(workspace)])
        assert rc == 2
        assert "analysis" in capsys.readouterr().err

    def test_ledger_rejects_step_zero_on_analysis(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        rc = orko.main(["ledger", "0", "complete", "--slug", "demo-topic",
                        "--workspace", str(workspace)])
        assert rc == 2

    def test_reinit_with_a_different_mode_is_an_error(self, workspace, capsys):
        init_run(workspace, capsys)
        code, err = init_run(workspace, capsys, "analysis")
        assert code == 2
        assert "mode" in err

    def test_run_is_done_after_the_last_step_of_its_mode(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        for step in range(1, 7):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        assert json.loads(capsys.readouterr().out)["next_step"] is None


class TestErrorContracts:
    def test_an_invalid_workspace_names_every_finding(self, workspace, capsys):
        shutil.rmtree(workspace / "docs" / ".git")
        (workspace / "code" / "scripts" / "spec-check.sh").unlink()
        code, err = init_run(workspace, capsys)
        assert code == 2
        assert "workspace-invalid: docs-not-a-repo" in err
        assert "workspace-invalid: spec-check-missing" in err

    def test_no_workspace_above_the_cwd_is_a_usage_error(self, tmp_path, capsys,
                                                         monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert orko.main(["status", "demo-topic"]) == 2
        assert "no workspace found above" in capsys.readouterr().err

    def test_init_with_an_unreadable_ledger_header_returns_usage_error(
        self, workspace, capsys
    ):
        run_dir = workspace / ".orko" / "demo-topic"
        run_dir.mkdir(parents=True)
        (run_dir / "progress.md").write_text("not a valid header\n")
        code, err = init_run(workspace, capsys)
        assert code == 2
        assert "unreadable ledger header" in err

    def test_an_empty_ledger_reports_an_error_rather_than_crashing(
        self, workspace, capsys
    ):
        run_dir = workspace / ".orko" / "demo-topic"
        run_dir.mkdir(parents=True)
        (run_dir / "progress.md").write_text("")
        code, err = init_run(workspace, capsys)
        assert code == 2
        assert "unreadable ledger header" in err
        assert orko.main(["status", "demo-topic", "--workspace", str(workspace)]) == 2

    def test_a_header_whose_json_is_truncated_is_unreadable(self, workspace, capsys):
        run_dir = workspace / ".orko" / "demo-topic"
        run_dir.mkdir(parents=True)
        (run_dir / "progress.md").write_text('# orko run\nheader: {"mode": "bui\n')
        code, err = init_run(workspace, capsys)
        assert code == 2
        assert "unreadable ledger header" in err

    def test_a_header_missing_a_key_is_unreadable(self, workspace, capsys):
        run_dir = workspace / ".orko" / "demo-topic"
        run_dir.mkdir(parents=True)
        (run_dir / "progress.md").write_text(
            '# orko run\nheader: {"mode": "build", "topic": "Demo Topic"}\n')
        code, err = init_run(workspace, capsys)
        assert code == 2
        assert "unreadable ledger header" in err

    def test_a_header_with_an_unknown_mode_is_unreadable(self, workspace, capsys):
        # Every caller indexes MODES with the mode, so a header naming one that
        # does not exist must read as unreadable, not raise KeyError.
        _, payload = init_run(workspace, capsys)
        ledger = Path(payload["ledger"])
        title, header, *rest = ledger.read_text(encoding="utf-8").splitlines()
        fields = json.loads(header.removeprefix("header: "))
        fields["mode"] = "bogus"
        ledger.write_text("\n".join([title, "header: " + json.dumps(fields), *rest]) + "\n",
                          encoding="utf-8")
        capsys.readouterr()
        assert orko.main(["status", "demo-topic", "--workspace", str(workspace)]) == 2
        assert "unreadable ledger header" in capsys.readouterr().err

    @pytest.mark.parametrize("topic", [
        "Demo\nTopic",
        "Demo\tTopic",
        "Demo\x00Topic",
    ])
    def test_a_topic_with_a_control_character_is_rejected(self, workspace, capsys,
                                                          topic):
        code, err = init_run(workspace, capsys, "build", topic)
        assert code == 2
        assert "control character" in err
        assert not (workspace / ".orko").exists()

    def test_a_topic_that_slugifies_to_nothing_is_an_error_not_a_traceback(
        self, workspace, capsys
    ):
        code, err = init_run(workspace, capsys, "build", "日本語")
        assert code == 2
        assert "empty slug" in err

    def test_ledger_for_an_unknown_slug_names_the_run(self, workspace, capsys):
        rc = orko.main(["ledger", "1", "complete", "--slug", "nope",
                        "--workspace", str(workspace)])
        assert rc == 2
        assert "no run named" in capsys.readouterr().err


class TestLedgerAndStatus:
    def _init(self, workspace, capsys, topic="Demo Topic"):
        init_run(workspace, capsys, "build", topic)

    def _complete_through_spec(self, workspace, commit=None):
        """Walk a build run past intake and the spec step, to the spec review."""
        for step in (0, 1):
            argv = ["ledger", str(step), "complete", "--slug", "demo-topic",
                    "--workspace", str(workspace)]
            if commit and step == 1:
                argv += ["--commit", commit]
            orko.main(argv)

    def test_ledger_appends_a_line_with_commit(self, workspace, capsys):
        self._init(workspace, capsys)
        rc = orko.main(["ledger", "1", "complete", "--slug", "demo-topic",
                        "--workspace", str(workspace), "--commit", "abc1234"])
        assert rc == 0
        text = (workspace / ".orko/demo-topic/progress.md").read_text()
        assert text.splitlines()[2] == "step 1 complete commit=abc1234"

    def test_ledger_rejects_a_non_sha_commit(self, workspace, capsys):
        self._init(workspace, capsys)
        rc = orko.main(["ledger", "1", "complete", "--slug", "demo-topic",
                        "--workspace", str(workspace), "--commit", "not a sha"])
        assert rc == 2
        assert "--commit must be a short or full SHA" in capsys.readouterr().err

    def test_ledger_accepts_a_sha_range_as_a_dispatched_base(self, workspace, capsys):
        self._init(workspace, capsys)
        self._complete_through_spec(workspace)
        rc = orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                        "--workspace", str(workspace), "--commit", "ba5e123..dec0de1"])
        assert rc == 0
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        assert json.loads(capsys.readouterr().out)["dispatched_base"] == (
            "ba5e123..dec0de1"
        )

    def test_ledger_is_append_only(self, workspace, capsys):
        self._init(workspace, capsys)
        for step in (1, 2):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        lines = (workspace / ".orko/demo-topic/progress.md").read_text().splitlines()
        assert lines[2] == "step 1 complete"
        assert lines[3] == "step 2 complete"

    def test_ledger_records_a_dispatched_base_sha(self, workspace, capsys):
        self._init(workspace, capsys)
        rc = orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                        "--workspace", str(workspace), "--commit", "ba5e123"])
        assert rc == 0
        text = (workspace / ".orko/demo-topic/progress.md").read_text()
        assert text.splitlines()[2] == "step 2 dispatched commit=ba5e123"

    @pytest.mark.parametrize("status", ["dispatched", "escalated", "failed"])
    def test_only_complete_advances_the_resume_point(self, workspace, capsys, status):
        self._init(workspace, capsys)
        self._complete_through_spec(workspace)
        orko.main(["ledger", "2", status, "--slug", "demo-topic",
                   "--workspace", str(workspace), "--commit", "ba5e123"])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        assert json.loads(capsys.readouterr().out)["next_step"] == 2

    def test_status_with_slug_reports_the_resume_point(self, workspace, capsys):
        self._init(workspace, capsys)
        self._complete_through_spec(workspace)
        capsys.readouterr()
        rc = orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["next_step_name"] == "spec review"
        assert payload["topic"] == "Demo Topic"

    def test_status_carries_the_header_fields(self, workspace, capsys):
        self._init(workspace, capsys)
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["owner"] == "oiler"
        assert payload["version"] == "0.1"
        assert payload["executor"] == "claude"
        assert payload["boundaries"] == "code/ only"
        assert len(payload["trailers"]) == 2

    def test_status_reports_none_when_the_run_is_complete(self, workspace, capsys):
        self._init(workspace, capsys)
        for step in range(0, 8):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        assert json.loads(capsys.readouterr().out)["next_step"] is None

    def test_bare_status_lists_every_run(self, workspace, capsys):
        self._init(workspace, capsys, topic="Alpha Feature")
        self._init(workspace, capsys, topic="Beta Feature")
        orko.main(["ledger", "0", "complete", "--slug", "alpha-feature",
                   "--workspace", str(workspace)])
        capsys.readouterr()
        rc = orko.main(["status", "--workspace", str(workspace)])
        assert rc == 0
        runs = json.loads(capsys.readouterr().out)
        assert [r["slug"] for r in runs] == ["alpha-feature", "beta-feature"]
        assert [r["next_step"] for r in runs] == [1, 0]

    def test_bare_status_with_no_runs_prints_an_empty_list(self, workspace, capsys):
        rc = orko.main(["status", "--workspace", str(workspace)])
        assert rc == 0
        assert json.loads(capsys.readouterr().out) == []

    def test_status_exposes_the_last_status_and_the_dispatched_base(
        self, workspace, capsys
    ):
        self._init(workspace, capsys)
        self._complete_through_spec(workspace, commit="aaa1111")
        orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                   "--workspace", str(workspace), "--commit", "bbb2222"])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["last_status"] == "dispatched"
        assert payload["dispatched_base"] == "bbb2222"

    def test_a_fresh_run_reports_no_last_status_and_no_dispatched_base(
        self, workspace, capsys
    ):
        self._init(workspace, capsys)
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["last_status"] is None
        assert payload["dispatched_base"] is None

    def test_the_dispatched_base_is_scoped_to_the_step_being_resumed(
        self, workspace, capsys
    ):
        self._init(workspace, capsys)
        for step, status, commit in (
            (0, "complete", "000aaa0"),
            (1, "complete", "aaa1111"),
            (2, "dispatched", "bbb2222"),
            (2, "complete", "ccc3333"),
            (3, "complete", "ddd4444"),
        ):
            orko.main(["ledger", str(step), status, "--slug", "demo-topic",
                       "--workspace", str(workspace), "--commit", commit])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 4
        assert payload["last_status"] == "complete"
        # Step 2's base must not leak into a step-4 resume.
        assert payload["dispatched_base"] is None

    def test_the_latest_dispatch_wins_when_a_step_was_dispatched_twice(
        self, workspace, capsys
    ):
        self._init(workspace, capsys)
        for commit in ("bbb2222", "eee5555"):
            orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                       "--workspace", str(workspace), "--commit", commit])
        self._complete_through_spec(workspace)
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        assert json.loads(capsys.readouterr().out)["dispatched_base"] == "eee5555"

    def test_an_escalated_line_is_the_last_status_after_a_completed_step(
        self, workspace, capsys
    ):
        self._init(workspace, capsys)
        self._complete_through_spec(workspace, commit="aaa1111")
        orko.main(["ledger", "1", "escalated", "--slug", "demo-topic",
                   "--workspace", str(workspace)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["last_status"] == "escalated"

    def test_a_malformed_ledger_line_is_skipped_not_fatal(self, workspace, capsys):
        self._init(workspace, capsys)
        ledger = workspace / ".orko/demo-topic/progress.md"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write("this is not a step record\n")
        self._complete_through_spec(workspace)
        capsys.readouterr()
        assert orko.main(["status", "demo-topic", "--workspace", str(workspace)]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 2
        assert payload["last_status"] == "complete"

    def test_status_for_an_unknown_slug_is_an_error(self, workspace, capsys):
        rc = orko.main(["status", "nope", "--workspace", str(workspace)])
        assert rc == 2
        assert "no run" in capsys.readouterr().err


class TestLedgerSubSteps:
    def test_substep_accepted_on_codex_build(self, workspace, capsys):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        assert orko.main(["ledger", "5.1", "complete", "--slug", "demo-topic",
                          "--workspace", str(workspace)]) == 0

    def test_substep_rejected_on_claude_build(self, workspace, capsys):
        init_run(workspace, capsys)
        assert orko.main(["ledger", "5.1", "complete", "--slug", "demo-topic",
                          "--workspace", str(workspace)]) == 2

    def test_next_step_ignores_substeps(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic",
                              "--executor", "codex")
        ledger = Path(payload["ledger"])
        for step in ("0", "1", "2", "3", "4"):
            orko.main(["ledger", step, "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        orko.main(["ledger", "5.1", "complete", "--slug", "demo-topic",
                   "--workspace", str(workspace)])
        orko.main(["ledger", "5.2", "complete", "--slug", "demo-topic",
                   "--workspace", str(workspace)])
        assert orko._next_step(ledger, "build") == 5
        assert orko.next_task(ledger) == 3

    def test_status_reports_next_task_and_records(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic",
                              "--executor", "codex")
        ledger = Path(payload["ledger"])
        orko.append_ledger(
            ledger,
            "record spec spec SPEC-001 docs/versions/0.1/specs/SPEC-001-demo-topic.md",
        )
        orko.append_ledger(
            ledger,
            "hash docs/versions/0.1/specs/SPEC-001-demo-topic.md " + "a" * 64,
        )
        capsys.readouterr()
        assert orko.main(["status", "demo-topic", "--workspace", str(workspace)]) == 0
        out = json.loads(capsys.readouterr().out)
        assert out["next_task"] == 1
        assert out["records"] == [{"type": "spec", "role": "spec", "id": "SPEC-001",
                                   "path": "docs/versions/0.1/specs/SPEC-001-demo-topic.md",
                                   "sha": "a" * 64}]

    def test_touched_paths_are_deduplicated_in_order(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic",
                              "--executor", "codex")
        ledger = Path(payload["ledger"])
        orko.append_ledger(ledger, "touched docs/STATUS.md")
        orko.append_ledger(ledger, "touched docs/STATUS.md")
        assert orko.touched(ledger) == ["docs/STATUS.md"]


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


class TestCheckTasksCLI:
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
    def test_spec_review_substitutes_every_token_including_the_lens(self, workspace, capsys):
        init_run(workspace, capsys)
        assert orko.main(["prompt", "spec-review", "demo-topic", "--lens", "security",
                          "--workspace", str(workspace)]) == 0
        out = capsys.readouterr().out
        assert "{{" not in out
        assert "(no spec minted yet)" in out
        assert str(workspace / "docs") in out
        assert str(workspace / "code") in out
        assert str(workspace / ".orko/demo-topic/findings/security.md") in out
        assert "Your lens is **security**" in out
        assert "trust boundary" in out
        assert "## Lenses" not in out

    def test_plan_review_names_both_records(self, workspace, capsys):
        init_run(workspace, capsys)
        orko.main(["prompt", "plan-review", "demo-topic", "--lens", "coverage",
                   "--workspace", str(workspace)])
        out = capsys.readouterr().out
        assert "(no plan minted yet)" in out
        assert "(no spec minted yet)" in out
        assert "{{" not in out

    def test_unknown_lens_is_a_usage_error_naming_the_valid_ones(self, workspace, capsys):
        init_run(workspace, capsys)
        rc = orko.main(["prompt", "spec-review", "demo-topic", "--lens", "vibes",
                        "--workspace", str(workspace)])
        assert rc == 2
        err = capsys.readouterr().err
        for lens in ("requirements", "architecture", "testability", "security"):
            assert lens in err

    def test_review_kinds_require_a_lens(self, workspace, capsys):
        init_run(workspace, capsys)
        rc = orko.main(["prompt", "plan-review", "demo-topic",
                        "--workspace", str(workspace)])
        assert rc == 2

    def test_plan_write_names_the_tasks_file_and_both_repositories(self, workspace, capsys):
        init_run(workspace, capsys)
        assert orko.main(["prompt", "plan-write", "demo-topic",
                          "--workspace", str(workspace)]) == 0
        out = capsys.readouterr().out
        assert str(workspace / ".orko/demo-topic/tasks.md") in out
        assert str(workspace / "docs") in out
        assert str(workspace / "code") in out
        assert "{{" not in out

    def test_seat_prompt_inlines_the_context_file(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        ctx = workspace / ".orko/demo-topic/context/perf.md"
        ctx.write_text("Look at src/hot.py\n")
        assert orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                          "--question", "Where is the N+1?",
                          "--context-file", str(ctx),
                          "--workspace", str(workspace)]) == 0
        out = capsys.readouterr().out
        assert "You are the perf on an orko engagement" in out
        assert "Where is the N+1?" in out
        assert "Look at src/hot.py" in out
        assert str(workspace / ".orko/demo-topic/findings/perf.md") in out
        assert "{{" not in out

    def test_verifier_prompt_names_findings_and_verdict_paths(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        ctx = workspace / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--workspace", str(workspace)])
        out = capsys.readouterr().out
        assert str(workspace / ".orko/demo-topic/findings/perf.md") in out
        assert str(workspace / ".orko/demo-topic/findings/perf.verdict.md") in out
        assert "{{" not in out

    def test_seat_records_the_question_for_a_later_verifier(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        ctx = workspace / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--workspace", str(workspace)])
        recorded = workspace / ".orko/demo-topic/context/perf.question"
        assert recorded.read_text(encoding="utf-8") == "Where is the N+1?"

    def test_verifier_reads_the_recorded_question_when_none_is_passed(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        ctx = workspace / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--workspace", str(workspace)])
        capsys.readouterr()
        assert orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                          "--context-file", str(ctx),
                          "--workspace", str(workspace)]) == 0
        out = capsys.readouterr().out
        assert str(workspace / ".orko/demo-topic/findings/perf.verdict.md") in out
        assert "{{" not in out

    def test_verifier_without_a_question_or_a_record_is_a_usage_error(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        ctx = workspace / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        rc = orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                        "--context-file", str(ctx), "--workspace", str(workspace)])
        assert rc == 2
        assert "no recorded question for seat perf" in capsys.readouterr().err

    def test_context_containing_template_tokens_is_passed_through(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        ctx = workspace / ".orko/demo-topic/context/perf.md"
        ctx.write_text("see {{WORKSPACE}} and {{SEAT}}\n")
        assert orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                          "--question", "Where is the N+1?",
                          "--context-file", str(ctx),
                          "--workspace", str(workspace)]) == 0
        assert "see {{WORKSPACE}} and {{SEAT}}" in capsys.readouterr().out

    def test_seat_kinds_require_seat_question_and_context(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        rc = orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                        "--workspace", str(workspace)])
        assert rc == 2

    def test_missing_context_file_is_an_io_error(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        rc = orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                        "--question", "q", "--context-file", str(workspace / "nope.md"),
                        "--workspace", str(workspace)])
        assert rc == 2

    def test_no_charter_names_a_single_repository_root(self):
        for name in ("spec-reviewer.md", "plan-reviewer.md", "plan-writer.md"):
            text = (orko.references_dir() / name).read_text(encoding="utf-8")
            assert "{{ROOT}}" not in text
            assert re.search(r"^\*\*Docs repository:\*\* \{\{DOCS\}\}$", text,
                             re.MULTILINE), name
            assert re.search(r"^\*\*Code repository:\*\* \{\{CODE\}\}$", text,
                             re.MULTILINE), name

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
    def _escalations_path(self, workspace) -> Path:
        return workspace / ".orko/demo-topic/escalations.md"

    def test_absent_file_exits_zero_and_prints_nothing(self, workspace, capsys):
        init_run(workspace, capsys)
        assert orko.main(["escalations", "demo-topic",
                          "--workspace", str(workspace)]) == 0
        assert capsys.readouterr().out == ""

    def test_empty_file_exits_zero(self, workspace, capsys):
        init_run(workspace, capsys)
        self._escalations_path(workspace).write_text("")
        assert orko.main(["escalations", "demo-topic",
                          "--workspace", str(workspace)]) == 0

    def test_whitespace_only_file_exits_zero(self, workspace, capsys):
        init_run(workspace, capsys)
        self._escalations_path(workspace).write_text("\n\n   \n\t\n")
        assert orko.main(["escalations", "demo-topic",
                          "--workspace", str(workspace)]) == 0
        assert capsys.readouterr().out == ""

    def test_file_with_content_exits_one_and_prints_it(self, workspace, capsys):
        init_run(workspace, capsys)
        self._escalations_path(workspace).write_text(
            "## Escalation\n\nThe spec contradicts itself about `007`.\n"
        )
        assert orko.main(["escalations", "demo-topic",
                          "--workspace", str(workspace)]) == 1
        out = capsys.readouterr().out
        assert "contradicts itself" in out
        assert out.endswith("\n")

    def test_unknown_slug_is_an_error(self, workspace, capsys):
        assert orko.main(["escalations", "nope",
                          "--workspace", str(workspace)]) == 2
        assert "no run" in capsys.readouterr().err

    def test_outside_a_workspace_is_an_error(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert orko.main(["escalations", "demo-topic"]) == 2
        assert "no workspace found above" in capsys.readouterr().err


class TestPreflight:
    def _repo(self, tmp_path, branch="feat/x"):
        subprocess.run(["git", "init", "-q", "-b", branch, str(tmp_path)], check=True)
        return tmp_path

    def test_clean_repo_on_feature_branch_passes(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--workspace", str(root), "--mode", "build"]) == 0

    def test_master_fails_for_build(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--workspace", str(root), "--mode", "build"]) == 1
        assert "on-default-branch" in capsys.readouterr().out

    def test_master_is_fine_for_analysis(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--workspace", str(root),
                          "--mode", "analysis"]) == 0

    def test_missing_uv_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        monkeypatch.setattr(orko.shutil, "which", lambda name: None)
        assert orko.main(["preflight", "--workspace", str(root), "--mode", "build"]) == 1
        assert "uv-missing" in capsys.readouterr().out

    @pytest.mark.xfail(reason="preflight rewritten in Task 13", strict=True)
    def test_slug_supplies_the_mode(self, workspace, capsys, monkeypatch):
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        init_run(workspace, capsys, "build", "Demo")
        assert orko.main(["preflight", "--workspace", str(workspace),
                          "--slug", "demo"]) == 1
        assert "on-default-branch" in capsys.readouterr().out

    def test_outstanding_escalation_is_reported(self, workspace, capsys, monkeypatch):
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        init_run(workspace, capsys, "build", "Demo")
        (workspace / ".orko/demo/escalations.md").write_text("## Scope\n\nbody\n")
        assert orko.main(["preflight", "--workspace", str(workspace),
                          "--slug", "demo"]) == 1
        assert "blocked-escalation" in capsys.readouterr().out

    @pytest.mark.xfail(reason="preflight rewritten in Task 13", strict=True)
    def test_not_a_repo_is_exit_two(self, tmp_path, capsys):
        assert orko.main(["preflight", "--workspace", str(tmp_path),
                          "--mode", "build"]) == 2


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

    def test_status_finds_run_from_inside_code_without_flag(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys)
        monkeypatch.chdir(workspace / "code" / "scripts")
        capsys.readouterr()
        assert orko.main(["status", "demo-topic"]) == 0

    def test_status_outside_workspace_exits_2(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert orko.main(["status", "demo-topic"]) == 2


class TestFrontmatter:
    TEMPLATE = '---\nid: SPEC-NNN\ntitle: "[Capability]"\nstatus: draft\nimplements:\n  - SPEC-NNN\napproved_at: null\n---\n\n# body\n'

    def test_replaces_scalar_and_keeps_quotes(self):
        out = orko.set_frontmatter(self.TEMPLATE, {"id": "SPEC-004", "title": "Demo"})
        assert "id: SPEC-004\n" in out and 'title: "Demo"\n' in out

    def test_list_renders_as_block_sequence(self):
        out = orko.set_frontmatter(self.TEMPLATE, {"implements": ["SPEC-002"]})
        assert "implements:\n  - SPEC-002\napproved_at" in out
        assert "[SPEC" not in out.split("---")[1]

    def test_none_renders_null_and_body_untouched(self):
        out = orko.set_frontmatter(self.TEMPLATE, {"approved_at": None})
        assert "approved_at: null\n" in out and out.endswith("# body\n")

    def test_missing_key_is_appended(self):
        out = orko.set_frontmatter(self.TEMPLATE, {"reviewer": "orko (a, b)"})
        assert "reviewer: orko (a, b)\n---\n\n# body" in out

    def test_no_frontmatter_raises(self):
        with pytest.raises(ValueError):
            orko.set_frontmatter("# body only\n", {"id": "SPEC-001"})


class TestMintId:
    def test_first_spec_is_001(self, workspace):
        assert orko.next_id(workspace, "spec") == "SPEC-001"

    def test_scans_every_dossier(self, workspace):
        other = workspace / "docs/versions/0.2/specs"
        other.mkdir(parents=True)
        (other / "SPEC-003-old.md").write_text("x")
        assert orko.next_id(workspace, "spec") == "SPEC-004"

    def test_decision_and_adr_scan_their_own_dirs(self, workspace):
        (workspace / "docs/decisions/DEC-007-x.md").write_text("x")
        (workspace / "code/docs/adr/ADR-002-x.md").write_text("x")
        assert orko.next_id(workspace, "decision") == "DEC-008"
        assert orko.next_id(workspace, "adr") == "ADR-003"


def rec(workspace, capsys, *args):
    capsys.readouterr()
    code = orko.main(["record", *args, "--workspace", str(workspace)])
    out = capsys.readouterr()
    return code, (json.loads(out.out) if out.out.strip().startswith("{") else out.err)


class TestRecordSpecPlan:
    def test_spec_mints_001_with_frontmatter(self, workspace, capsys):
        init_run(workspace, capsys)
        code, out = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo capability")
        assert code == 0 and out["id"] == "SPEC-001"
        path = Path(out["path"])
        assert path == workspace / "docs/versions/0.1/specs/SPEC-001-demo-topic.md"
        text = path.read_text()
        assert "id: SPEC-001\n" in text and 'title: "Demo capability"' in text
        assert "status: draft\n" in text and 'product_version: "0.1"' in text
        assert 'owner: "oiler"' in text and "approved_at: null" in text
        assert "# SPEC-001 — Demo capability" in text

    def test_spec_row_replaces_readme_placeholder(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo capability")
        readme = (workspace / "docs/versions/0.1/README.md").read_text()
        assert "| [SPEC-001] |" not in readme
        assert "| SPEC-001 | Specification | Demo capability | draft | oiler |" in readme

    def test_plan_writes_block_sequence(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo capability")
        code, out = rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Demo plan", "--implements", "SPEC-001")
        text = Path(out["path"]).read_text()
        assert "implements:\n  - SPEC-001\n" in text
        assert "[SPEC" not in text.split("---")[1]

    def test_second_mint_of_same_role_returns_existing(self, workspace, capsys):
        init_run(workspace, capsys)
        _, first = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        code, second = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        assert code == 0 and second["path"] == first["path"] and second["resumed"] is True
        assert not (workspace / "docs/versions/0.1/specs/SPEC-002-demo-topic.md").exists()

    def test_release_index_survives_three_mints(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan", "--implements", "SPEC-001")
        readme = (workspace / "docs/versions/0.1/README.md").read_text()
        assert "| [0.1.0] | planned |" in readme
        assert "| PLAN-001 | Delivery plan | Plan | draft | oiler |" in readme

    def test_record_line_in_ledger(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        assert orko.record_for(Path(payload["ledger"]), "spec", "spec")["id"] == "SPEC-001"


class TestRecordReview:
    def _findings_dir(self, workspace):
        src = Path(orko.__file__).parent / "fixtures/findings"
        dst = workspace / ".orko/demo-topic/findings/2"
        shutil.copytree(src, dst)
        return dst

    def test_parse_findings(self):
        text = (Path(orko.__file__).parent / "fixtures/findings/requirements.md").read_text()
        seat, findings = orko.parse_findings(text)
        assert seat["seat"] == "requirements" and len(findings) == 2
        assert findings[0]["severity"] == "high" and findings[1]["title"] == "Non-goals contradict scope"

    def test_parse_verdicts(self):
        text = (Path(orko.__file__).parent / "fixtures/findings/requirements.verdict.md").read_text()
        verdicts = orko.parse_verdicts(text)
        assert verdicts["F1"].startswith("confirmed: ")
        assert verdicts["F2"].startswith("overstated: ")

    def test_review_renders_f_blocks_in_seat_order(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        d = self._findings_dir(workspace)
        code, out = rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec",
                        "--reviews", "SPEC-001", "--revision", "abc1234", "--from-findings", str(d),
                        "--title", "Spec review")
        assert code == 0
        text = Path(out["path"]).read_text()
        assert out["path"].endswith("REVIEW-001-demo-topic-spec.md")
        assert "reviews:\n  - SPEC-001\n" in text
        assert 'reviewer: "orko (requirements, security)"' in text
        assert "approved_by: null" in text
        assert text.count("### F") == 3
        f1 = text.split("### F1")[1].split("### F2")[0]
        assert "- Severity: `high`" in f1 and "- Disposition: `open`" in f1
        assert "Verified: confirmed: the quoted line" in f1
        assert "### F3 — Upload path is unbounded" in text

    def test_review_row_in_index(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        d = self._findings_dir(workspace)
        rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec", "--reviews", "SPEC-001",
            "--revision", "abc1234", "--from-findings", str(d), "--title", "Spec review")
        assert "| REVIEW-001 | Review | Spec review | draft | oiler |" in (workspace / "docs/versions/0.1/README.md").read_text()

    def test_seat_flags_set_order(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        d = self._findings_dir(workspace)
        code, out = rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec",
                        "--reviews", "SPEC-001", "--revision", "abc1234", "--from-findings", str(d),
                        "--seat", "security", "--seat", "requirements", "--title", "Spec review")
        assert code == 0
        text = Path(out["path"]).read_text()
        assert "### F1 — Upload path is unbounded" in text
        assert 'reviewer: "orko (security, requirements)"' in text

    def test_missing_findings_file_exits_2(self, workspace, capsys):
        init_run(workspace, capsys)
        d = self._findings_dir(workspace)
        code, err = rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec",
                        "--reviews", "SPEC-001", "--revision", "abc1234", "--from-findings", str(d),
                        "--seat", "nobody", "--title", "Spec review")
        assert code == 2 and "no findings file" in err
