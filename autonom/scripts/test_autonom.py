"""Tests for autonom.py — the deterministic spine of the autonom skill."""
import json

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
