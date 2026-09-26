"""Tests for orko_sdd.py, the deterministic half of the orko-sdd skill."""
import re
from pathlib import Path

import pytest

from conftest import git, write_plugins

import orko_sdd


def run_log(ledger, *extra, task="1", role="implementer-scoped", model="sonnet",
            effort="medium", why="plan has the code"):
    return orko_sdd.main(["log", "--ledger", str(ledger), "--task", task, "--role", role,
                          "--model", model, "--effort", effort, "--why", why, *extra])


def last_line(ledger):
    return ledger.read_text(encoding="utf-8").splitlines()[-1]


class TestLog:
    def test_on_table_dispatch_appends_line_and_prints_dispatch_params(self, ledger, capsys):
        assert run_log(ledger) == 0
        assert last_line(ledger) == "Task 1: dispatch implementer-scoped sonnet/medium — plan has the code"
        out = capsys.readouterr().out
        assert "subagent_type: orko-sdd-medium" in out
        assert "model: sonnet" in out

    def test_off_table_dispatch_is_rejected_and_not_logged(self, ledger, capsys):
        before = ledger.read_text(encoding="utf-8")
        assert run_log(ledger, model="opus") == 2
        assert ledger.read_text(encoding="utf-8") == before
        assert "implementer-scoped allows sonnet/medium" in capsys.readouterr().err

    def test_override_logs_off_table_dispatch_with_marker(self, ledger):
        assert run_log(ledger, "--override", model="opus", why="spec gap needs judgment") == 0
        assert last_line(ledger) == (
            "Task 1: dispatch implementer-scoped opus/medium — spec gap needs judgment [override]")

    def test_why_newlines_collapse_to_one_line(self, ledger):
        assert run_log(ledger, why="first\nsecond") == 0
        assert last_line(ledger).endswith("— first second")

    def test_refuses_non_ledger_path(self, tmp_path, capsys):
        other = tmp_path / "notes.md"
        other.write_text("x", encoding="utf-8")
        assert run_log(other) == 2
        assert other.read_text(encoding="utf-8") == "x"
        assert "not an SDD plan ledger" in capsys.readouterr().err

    def test_refuses_the_flat_legacy_ledger(self, tmp_path):
        flat = tmp_path / "repo" / ".superpowers" / "sdd" / "progress.md"
        flat.parent.mkdir(parents=True)
        flat.write_text("# SDD ledger — plan: docs/plan.md\n", encoding="utf-8")
        assert run_log(flat) == 2

    def test_refuses_a_ledger_without_the_identity_line(self, ledger, capsys):
        ledger.write_text("notes\n", encoding="utf-8")
        assert run_log(ledger) == 2
        assert "does not start with '# SDD ledger — plan:'" in capsys.readouterr().err

    def test_task_must_be_a_number_a_batch_or_final(self, ledger):
        assert run_log(ledger, task="T1") == 2

    def test_a_batch_logs_one_line_for_its_tasks(self, ledger):
        assert run_log(ledger, task="3,4,5") == 0
        assert last_line(ledger) == "Task 3,4,5: dispatch implementer-scoped sonnet/medium — plan has the code"

    def test_fix_incomplete_takes_same_model_at_next_effort(self, ledger):
        assert run_log(ledger, role="implementer-multifile", model="opus", effort="medium", why="w") == 0
        assert run_log(ledger, role="fix-incomplete", model="sonnet", effort="high", why="w") == 2
        assert run_log(ledger, role="fix-incomplete", model="opus", effort="high", why="w") == 0

    def test_fix_incomplete_rejected_after_a_high_effort_dispatch(self, ledger, capsys):
        assert run_log(ledger, role="implementer-ui", effort="high") == 0
        assert run_log(ledger, role="fix-incomplete", model="sonnet", effort="high", why="w") == 2
        assert "nothing after this task's last implementer dispatch" in capsys.readouterr().err

    def test_a_stalled_scoped_implementer_gets_fix_incomplete_at_sonnet_high(self, ledger):
        assert run_log(ledger) == 0
        assert run_log(ledger, role="fix-incomplete", model="sonnet", effort="high", why="w") == 0

    def test_reviewer_runs_at_opus_medium(self, ledger):
        assert run_log(ledger, role="reviewer", model="opus", effort="medium", why="w") == 0
        assert run_log(ledger, role="reviewer", model="opus", effort="high", why="w") == 2

    def test_reviewer_security_runs_at_opus_high(self, ledger):
        assert run_log(ledger, role="reviewer-security", model="opus", effort="high", why="w") == 0
        assert run_log(ledger, role="reviewer-security", model="opus", effort="medium", why="w") == 2

    def test_re_reviewer_roles_mirror_the_reviewer_roles(self, ledger):
        assert run_log(ledger, role="re-reviewer", model="opus", effort="medium", why="w") == 0
        assert run_log(ledger, role="re-reviewer", model="opus", effort="low", why="w") == 2
        assert run_log(ledger, role="re-reviewer-security", model="opus", effort="high", why="w") == 0
        assert run_log(ledger, role="re-reviewer-security", model="opus", effort="medium", why="w") == 2

    def test_a_dispatch_below_high_orchestrator_effort_logs_with_a_warning(self, ledger, capsys, monkeypatch):
        monkeypatch.setenv("CLAUDE_EFFORT", "medium")
        assert run_log(ledger) == 0
        assert last_line(ledger).startswith("Task 1: dispatch implementer-scoped")
        err = capsys.readouterr().err
        assert "warning: orchestrator effort is medium" in err
        assert "press `s`" in err

    def test_a_dispatch_at_high_orchestrator_effort_prints_no_warning(self, ledger, capsys):
        assert run_log(ledger) == 0
        assert "warning" not in capsys.readouterr().err

    def test_a_dispatch_with_no_effort_set_warns(self, ledger, capsys, monkeypatch):
        monkeypatch.delenv("CLAUDE_EFFORT")
        assert run_log(ledger) == 0
        assert "warning: orchestrator effort is not set" in capsys.readouterr().err

    def test_fix_tier_up_must_rank_above_the_stuck_implementer(self, ledger):
        assert run_log(ledger, role="implementer-multifile", model="opus", effort="medium", why="w") == 0
        assert run_log(ledger, role="fix-tier-up", model="opus", effort="medium", why="w") == 2
        assert run_log(ledger, role="fix-tier-up", model="opus", effort="high", why="w") == 0

    def test_final_reviewer_is_opus_unless_the_ledger_marks_release_critical(self, ledger):
        final = {"task": "final", "role": "final-reviewer", "effort": "high", "why": "w"}
        assert run_log(ledger, model="opus", **final) == 0
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write("orko-sdd: release-critical\n")
        assert run_log(ledger, model="opus", **final) == 2
        assert run_log(ledger, model="fable", **final) == 0

    def test_a_bulleted_release_critical_marker_still_counts(self, ledger):
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write("- `orko-sdd: release-critical`\n")
        assert run_log(ledger, task="final", role="final-reviewer", model="opus", why="w") == 2


def run_verify(ledger, output, *cmd, exit_code=0):
    return orko_sdd.main(["verify", "--ledger", str(ledger), "--exit", str(exit_code),
                          "--output", str(output), "--", *cmd])


class TestVerify:
    def test_records_the_exit_code_and_last_output_line(self, ledger):
        output = ledger.parent / "verify-1.log"
        output.write_text("collected 3 items\n3 passed\n\n", encoding="utf-8")
        assert run_verify(ledger, output, "pytest", "-q", exit_code=3) == 0
        assert last_line(ledger) == "Verify: pytest -q — exit 3 — 3 passed"

    def test_undecodable_output_is_replaced_not_fatal(self, ledger):
        output = ledger.parent / "verify-1.log"
        output.write_bytes(b"ok\n\xff\xfe\n")
        assert run_verify(ledger, output, "pytest") == 0
        assert last_line(ledger) == "Verify: pytest — exit 0 — ��"

    def test_separators_and_newlines_are_flattened(self, ledger):
        output = ledger.parent / "verify-1.log"
        output.write_text("boom — exit 9 — ha\n", encoding="utf-8")
        assert run_verify(ledger, output, "python3", "-c", "a\nb") == 0
        assert last_line(ledger) == "Verify: python3 -c 'a b' — exit 0 — boom - exit 9 - ha"

    def test_tab_separated_em_dash_in_command_does_not_shift_columns(self, ledger):
        output = ledger.parent / "verify-1.log"
        output.write_text("FAILED\n", encoding="utf-8")
        assert run_verify(ledger, output, "pytest", "-k", "x\t—\texit 0\t—\ty", exit_code=1) == 0
        assert last_line(ledger) == "Verify: pytest -k 'x - exit 0 - y' — exit 1 — FAILED"

    def test_doubled_em_dash_in_command_does_not_shift_columns(self, ledger):
        output = ledger.parent / "verify-1.log"
        output.write_text("FAILED\n", encoding="utf-8")
        assert run_verify(ledger, output, "pytest", "-k", "x — — y", exit_code=1) == 0
        assert last_line(ledger) == "Verify: pytest -k 'x - - y' — exit 1 — FAILED"

    def test_output_outside_the_workspace_is_refused(self, ledger, tmp_path, capsys):
        output = tmp_path / "elsewhere.log"
        output.write_text("secret\n", encoding="utf-8")
        before = ledger.read_text(encoding="utf-8")
        assert run_verify(ledger, output, "pytest") == 2
        assert ledger.read_text(encoding="utf-8") == before
        assert "secret" not in capsys.readouterr().out

    def test_symlinked_output_escaping_the_workspace_is_refused(self, ledger, tmp_path, capsys):
        secret_file = tmp_path / "outside.log"
        secret_file.write_text("secret\n", encoding="utf-8")
        symlink = ledger.parent / "evil.log"
        symlink.symlink_to(secret_file)
        before = ledger.read_text(encoding="utf-8")
        assert run_verify(ledger, symlink, "pytest") == 2
        assert ledger.read_text(encoding="utf-8") == before
        assert "secret" not in capsys.readouterr().out

    def test_a_missing_output_file_is_recorded(self, ledger):
        assert run_verify(ledger, ledger.parent / "none.log", "pytest", exit_code=1) == 0
        assert last_line(ledger) == "Verify: pytest — exit 1 — (output file missing)"

    def test_refuses_an_empty_command(self, ledger):
        output = ledger.parent / "verify-1.log"
        output.write_text("x\n", encoding="utf-8")
        assert run_verify(ledger, output) == 2

    def test_a_single_quoted_command_is_recorded_as_given(self, ledger):
        output = ledger.parent / "verify-1.log"
        output.write_text("3 passed\n", encoding="utf-8")
        assert run_verify(ledger, output, "cd a && pytest -q") == 0
        assert last_line(ledger) == "Verify: cd a && pytest -q — exit 0 — 3 passed"

    def test_the_ledger_itself_is_refused_as_output(self, ledger, capsys):
        before = ledger.read_text(encoding="utf-8")
        assert run_verify(ledger, ledger, "pytest") == 2
        assert ledger.read_text(encoding="utf-8") == before
        assert capsys.readouterr().out == ""


class TestPreflight:
    def test_ok_run_reports_resolved_values_through_symlinked_agents(self, fake_home, repo):
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        assert out[-1] == "STATUS: ok"
        assert f"plan: {(repo / 'docs' / 'plan.md').resolve()}" in out
        assert "sdd: 6.4.1" in out
        assert "agents: orko-sdd-low, orko-sdd-medium, orko-sdd-high" in out
        assert "base-branch: master" in out
        assert "final-review: opus/high" in out

    def test_release_critical_selects_fable_final_review(self, fake_home, repo):
        out = orko_sdd.preflight_lines(["docs/plan.md", "--release-critical"], fake_home, repo)
        assert "flags: --release-critical" in out
        assert "final-review: fable/high" in out
        assert out[-1] == "STATUS: ok"

    def test_the_orchestrator_effort_is_reported(self, fake_home, repo):
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        assert "orchestrator-effort: high" in out
        assert out[-1] == "STATUS: ok"

    def test_effort_below_high_blocks_with_a_session_only_fix(self, fake_home, repo, monkeypatch):
        monkeypatch.setenv("CLAUDE_EFFORT", "medium")
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        problem = next(line for line in out if line.startswith("problem: orchestrator effort"))
        assert "press `s`" in problem
        assert "claude --effort high" in problem
        assert out[-1] == "STATUS: blocked"

    def test_unset_effort_blocks(self, fake_home, repo, monkeypatch):
        monkeypatch.delenv("CLAUDE_EFFORT")
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        assert "orchestrator-effort: not set" in out
        assert out[-1] == "STATUS: blocked"

    @pytest.mark.parametrize("level", ["xhigh", "max"])
    def test_effort_above_high_passes(self, fake_home, repo, monkeypatch, level):
        monkeypatch.setenv("CLAUDE_EFFORT", level)
        assert orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)[-1] == "STATUS: ok"

    def test_no_arguments_block_with_usage(self, fake_home, repo):
        out = orko_sdd.preflight_lines([], fake_home, repo)
        assert out[-1] == "STATUS: blocked"
        assert any("usage: /orko-sdd <plan-path>" in line for line in out)

    def test_unknown_flag_blocks(self, fake_home, repo):
        out = orko_sdd.preflight_lines(["docs/plan.md", "--fast"], fake_home, repo)
        assert "problem: unknown flag(s): --fast; usage: /orko-sdd <plan-path> [--release-critical]" in out
        assert out[-1] == "STATUS: blocked"

    def test_two_positionals_block_with_quoting_hint(self, fake_home, repo):
        out = orko_sdd.preflight_lines(["docs/my", "plan.md"], fake_home, repo)
        assert any("expected one plan path, got 2 (wrap a path with spaces in quotes)" in line
                   for line in out)
        assert out[-1] == "STATUS: blocked"

    def test_missing_plan_blocks(self, fake_home, repo):
        out = orko_sdd.preflight_lines(["docs/nope.md"], fake_home, repo)
        assert f"problem: plan not found: {(repo / 'docs' / 'nope.md').resolve()}" in out
        assert out[-1] == "STATUS: blocked"

    def test_other_sdd_version_warns_but_passes(self, fake_home, repo):
        write_plugins(fake_home, "6.5.0")
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        assert any(line.startswith("warning: orko-sdd was written against SDD 6.4.1; installed 6.5.0")
                   for line in out)
        assert out[-1] == "STATUS: ok"

    def test_missing_superpowers_blocks(self, fake_home, repo):
        (fake_home / ".claude" / "plugins" / "installed_plugins.json").unlink()
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        assert "sdd: not found" in out
        assert out[-1] == "STATUS: blocked"

    def test_missing_agents_block_with_install_command(self, fake_home, repo):
        (fake_home / ".claude" / "agents" / "orko-sdd").unlink()
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        problem = next(line for line in out if line.startswith("problem: missing agent(s)"))
        assert "ln -s" in problem
        assert out[-1] == "STATUS: blocked"

    def test_an_agent_with_the_wrong_effort_blocks(self, fake_home, repo):
        agents = fake_home / ".claude" / "agents"
        (agents / "orko-sdd").unlink()
        for effort in ("medium", "high"):
            name = f"orko-sdd-{effort}.md"
            (agents / name).write_text((orko_sdd.SKILL_DIR / "agents" / name).read_text(encoding="utf-8"),
                                       encoding="utf-8")
        (agents / "orko-sdd-low.md").write_text("---\nname: orko-sdd-low\neffort: high\n---\n",
                                                encoding="utf-8")
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)
        assert any(line.startswith("problem: missing agent(s): orko-sdd-low;") for line in out)
        assert out[-1] == "STATUS: blocked"

    def test_project_level_agents_satisfy_the_check(self, fake_home, repo):
        (fake_home / ".claude" / "agents" / "orko-sdd").unlink()
        (repo / ".claude" / "agents").mkdir(parents=True)
        (repo / ".claude" / "agents" / "orko-sdd").symlink_to(orko_sdd.SKILL_DIR / "agents")
        assert orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)[-1] == "STATUS: ok"

    def test_project_agents_count_from_a_subdirectory(self, fake_home, repo):
        (fake_home / ".claude" / "agents" / "orko-sdd").unlink()
        (repo / ".claude" / "agents").mkdir(parents=True)
        (repo / ".claude" / "agents" / "orko-sdd").symlink_to(orko_sdd.SKILL_DIR / "agents")
        out = orko_sdd.preflight_lines(["plan.md"], fake_home, repo / "docs")
        assert out[-1] == "STATUS: ok"

    def test_main_checkout_agents_count_from_a_worktree(self, fake_home, repo, tmp_path):
        (fake_home / ".claude" / "agents" / "orko-sdd").unlink()
        (repo / ".claude" / "agents").mkdir(parents=True)
        (repo / ".claude" / "agents" / "orko-sdd").symlink_to(orko_sdd.SKILL_DIR / "agents")
        worktree = tmp_path / "wt"
        git(repo, "worktree", "add", "-q", str(worktree), "-b", "feat/x")
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, worktree)
        assert out[-1] == "STATUS: ok"

    def test_a_symlink_loop_under_agents_does_not_hang(self, fake_home, repo):
        (fake_home / ".claude" / "agents" / "loop").symlink_to(fake_home / ".claude" / "agents")
        assert orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)[-1] == "STATUS: ok"

    def test_main_is_the_base_when_master_is_absent(self, fake_home, repo):
        git(repo, "branch", "-m", "master", "main")
        assert "base-branch: main" in orko_sdd.preflight_lines(["docs/plan.md"], fake_home, repo)

    def test_outside_a_git_repository_blocks(self, fake_home, tmp_path):
        bare = tmp_path / "bare"
        (bare / "docs").mkdir(parents=True)
        (bare / "docs" / "plan.md").write_text("x", encoding="utf-8")
        out = orko_sdd.preflight_lines(["docs/plan.md"], fake_home, bare)
        assert any(line.startswith("problem: no master or main branch") for line in out)
        assert out[-1] == "STATUS: blocked"

    def test_a_crash_still_exits_zero(self, monkeypatch, capsys):
        def boom(*_args):
            raise RuntimeError("boom")
        monkeypatch.setattr(orko_sdd, "preflight_lines", boom)
        assert orko_sdd.main(["preflight", "docs/plan.md"]) == 0
        out = capsys.readouterr().out
        assert "problem: preflight crashed: RuntimeError('boom')" in out
        assert out.rstrip().endswith("STATUS: blocked")


FIXTURES = Path(__file__).parent / "fixtures"
HEADER = "# SDD ledger — plan: /nonexistent/plan.md"


def run_report(ledger, capsys, *extra, repo=None):
    code = orko_sdd.main(["report", "--ledger", str(ledger),
                          "--repo", str(repo or ledger.parent), *extra])
    assert code == 0
    return capsys.readouterr().out


def write_ledger(ledger, *lines):
    ledger.write_text("\n".join([HEADER, *lines]) + "\n", encoding="utf-8")


def section(out, name, following):
    return out.split(f"## {name}", 1)[1].split(f"## {following}", 1)[0]


class TestReportOnARealLedger:
    @pytest.fixture
    def out(self, ledger, capsys):
        ledger.write_text((FIXTURES / "ledger-orko-v2-build.md").read_text(encoding="utf-8"),
                          encoding="utf-8")
        return run_report(ledger, capsys, "--plan", "/nonexistent/plan.md")

    def test_every_ruling_is_a_decided_row(self, out):
        rows = [line for line in section(out, "Decided", "Follow-up").splitlines()
                if line.startswith("| ") and not line.startswith("| # | Ruling |")]
        assert len(rows) == 18

    def test_a_ruling_splits_into_ruling_detail_and_cost(self, out):
        assert ("| fixtures copied in T8 are refreshed once more after T11 if the workshop plan changed"
                " | spec says copies refresh when originals change"
                " | stale fixture, no behavior impact. |") in out

    def test_complete_tasks_carry_their_commit_ranges(self, out):
        assert "| 1 | complete | b41d456..fcc0685 (?) | — |" in out
        assert "| 11 | complete | c8d2903..63d6119 (?) | — |" in out

    def test_a_task_parked_line_keeps_its_finding_in_decided(self, out):
        assert ("| parked: em-dashes across orko/references and SKILL.md (34 in the two new files)"
                " | branch-wide house style question, decided at final review, not per task. | — |") in out

    def test_deferred_minors_are_listed_inline_and_parked_rulings_stay_in_decided(self, out):
        follow_up = section(out, "Follow-up", "Verified")
        assert ("- Task 1 deferred minors: test_orko.py continuation-line indentation over-indented"
                " after sed (E127, ~40 sites) — reflow once before branch review · ") in follow_up
        assert "parked" not in follow_up


class TestReportOnARun:
    def test_statuses_models_and_verify_rows(self, ledger, repo, capsys):
        a = git(repo, "rev-parse", "HEAD")
        git(repo, "commit", "-q", "--allow-empty", "-m", "task 1")
        b = git(repo, "rev-parse", "HEAD")
        ledger.write_text("\n".join([
            f"# SDD ledger — plan: {FIXTURES / 'plan-sample.md'}",
            "Task 1: dispatch implementer-scoped sonnet/high — plan has the code",
            "Task 1: dispatch reviewer opus/low — task review",
            f"Task 1: complete (commits {a[:7]}..{b[:7]}, review clean)",
            "Task 2: dispatch implementer-multifile opus/medium — three files",
            "Task 3: skipped — evergreen conflict — CLAUDE.md:3 — adds a third-party dependency",
            "Task 4: skipped — depends on Task 3",
            "Task final: dispatch final-reviewer opus/high — whole branch",
            "Verify: uv run pytest -q — exit 0 — 12 passed | 0 failed",
        ]) + "\n", encoding="utf-8")
        out = run_report(ledger, capsys, repo=repo)
        assert f"| 1. Alpha | complete | {a[:7]}..{b[:7]} (1) | impl sonnet/high · rev opus/low |" in out
        assert "| 2. Bravo | in progress | — | impl opus/medium |" in out
        assert "| 3. Charlie | skipped — evergreen conflict | — | — |" in out
        assert "| 4. Delta | skipped — depends on Task 3 | — | — |" in out
        assert "| 5. Echo | not started | — | — |" in out
        assert "| final review | dispatched | — | rev opus/high |" in out
        assert "| uv run pytest -q | 0 | 12 passed \\| 0 failed |" in out
        assert section(out, "Follow-up", "Verified").strip() == (
            "- Task 3 skipped: evergreen conflict — CLAUDE.md:3 — adds a third-party dependency"
            " (Task 4 depends on it)")

    def test_recommended_is_the_last_section_after_verified(self, ledger, capsys):
        write_ledger(ledger, "Verify: pytest -q — exit 0 — 3 passed")
        headings = [line for line in run_report(ledger, capsys).splitlines() if line.startswith("## ")]
        assert headings == ["## Done", "## Decided", "## Follow-up", "## Verified", "## Recommended"]

    def test_a_final_parked_line_names_its_finding_in_decided_only(self, ledger, capsys):
        write_ledger(ledger, "Task final: parked — X — Ruling: Y — cost if wrong: Z")
        out = run_report(ledger, capsys)
        assert "| 1 | parked: X | Y | Z |" in section(out, "Decided", "Follow-up")
        assert "parked" not in section(out, "Follow-up", "Verified")

    def test_a_final_completion_line_shows_the_final_review_complete(self, ledger, capsys):
        write_ledger(ledger, "Task final: dispatch final-reviewer opus/high — whole branch",
                     "Task final: complete (commits aaaaaaa..bbbbbbb, 2 parked)")
        out = run_report(ledger, capsys)
        assert "| final review | complete (2 parked) | aaaaaaa..bbbbbbb (?) | rev opus/high |" in out

    def test_plan_headings_inside_fences_are_ignored(self, ledger, capsys):
        ledger.write_text(f"# SDD ledger — plan: {FIXTURES / 'plan-sample.md'}\n", encoding="utf-8")
        out = run_report(ledger, capsys)
        assert "Not a real task" not in out
        assert out.count("| 1. Alpha |") == 1
        assert "| 6. Foxtrot | not started | — | — |" in out

    def test_an_unreadable_plan_is_noted_first_in_follow_up(self, ledger, capsys):
        write_ledger(ledger, "Ruling: no cost — b")  # HEADER points the ledger's plan at /nonexistent/plan.md
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert follow_up.strip().splitlines()[0] == (
            "- plan not readable: /nonexistent/plan.md; tasks never dispatched are not listed")

    def test_empty_sections_say_so(self, ledger, capsys):
        write_ledger(ledger)
        out = run_report(ledger, capsys, "--plan", str(FIXTURES / "plan-sample.md"))
        assert "| — | none | — | — |" in out
        assert "- none" in section(out, "Follow-up", "Verified")
        assert "| none run | — | — |" in out

    def test_pipes_in_rulings_are_escaped(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use a | b table — why: clarity — cost if wrong: none")
        assert "| use a \\| b table | clarity | none |" in run_report(ledger, capsys)

    def test_ruling_variants_and_repeats_are_all_kept(self, ledger, capsys):
        write_ledger(ledger,
                     "Ruling (supersedes the one above): use X — why: y — cost if wrong: z",
                     "Ruling: same — why: a — cost if wrong: b",
                     "Ruling: same — why: a — cost if wrong: b")
        out = run_report(ledger, capsys)
        assert "| use X | y | z |" in out
        assert out.count("| same | a | b |") == 2

    def test_an_unlabeled_ruling_treats_its_last_part_as_the_cost(self, ledger, capsys):
        # SDD 6.4.1's plain format carries no "why:"/"cost if wrong:" labels at all.
        write_ledger(ledger, "Ruling: use X — because Y — rework of Z")
        assert "| use X | because Y | rework of Z |" in run_report(ledger, capsys)

    def test_a_labeled_why_with_its_own_em_dash_does_not_donate_a_cost(self, ledger, capsys):
        # A "why:"-labeled ruling with no cost label must not treat its own why text's
        # trailing " — " clause as a positional cost.
        write_ledger(ledger, "Ruling: keep A — why: B is slow — measured at 3s")
        assert "| keep A | B is slow — measured at 3s | — |" in run_report(ledger, capsys)

    def test_a_ruling_with_nested_parens_in_its_annotation_still_matches(self, ledger, capsys):
        write_ledger(ledger, "Ruling (supersedes Task 3 (merge-base) ruling): drop it "
                             "— why: y — cost if wrong: z")
        assert "| drop it | y | z |" in run_report(ledger, capsys)

    def test_rulings_inside_dispatch_lines_are_not_decisions(self, ledger, capsys):
        write_ledger(ledger, "Task 1: dispatch implementer-scoped sonnet/high — fine. Ruling: ship it — why: x")
        assert "| — | none | — | — |" in section(run_report(ledger, capsys), "Decided", "Follow-up")

    def test_bulleted_lines_parse(self, ledger, capsys):
        write_ledger(ledger,
                     "- Task 1: complete (commits aaaaaaa..bbbbbbb, 2 parked)",
                     "- Ruling: keep going — why: nothing blocks — cost if wrong: rework")
        out = run_report(ledger, capsys)
        assert "| 1 | complete (2 parked) | aaaaaaa..bbbbbbb (?) | — |" in out
        assert "| keep going | nothing blocks | rework |" in out

    def test_models_carry_a_label_for_each_role(self, ledger, capsys):
        write_ledger(ledger, "Task 1: dispatch fix-incomplete opus/high — w",
                     "Task 2: dispatch scout opus/low — w",
                     "Task final: dispatch final-reviewer opus/high — w",
                     "Task final: dispatch final-fixer opus/medium — w",
                     "Task final: dispatch re-reviewer opus/low — w")
        out = run_report(ledger, capsys)
        assert "| 1 | in progress | — | fix opus/high |" in out
        assert "| 2 | in progress | — | scout opus/low |" in out
        assert "| final review | dispatched | — | rev opus/high · fix opus/medium · re-rev opus/low |" in out

    def test_security_review_roles_share_the_review_labels(self, ledger, capsys):
        write_ledger(ledger, "Task 1: dispatch reviewer-security opus/high — w",
                     "Task 1: dispatch re-reviewer-security opus/high — w")
        assert "| 1 | in progress | — | rev opus/high · re-rev opus/high |" in run_report(ledger, capsys)

    def test_a_batch_dispatch_reaches_each_task(self, ledger, capsys):
        write_ledger(ledger, "Task 3,4: dispatch implementer-scoped sonnet/high — same-shape batch")
        out = run_report(ledger, capsys)
        assert "| 3 | in progress | — | impl sonnet/high |" in out
        assert "| 4 | in progress | — | impl sonnet/high |" in out

    def test_a_batch_completion_marks_each_task_complete(self, ledger, capsys):
        write_ledger(ledger, "Task 3,4: complete (commits aaaaaaa..bbbbbbb, review clean)")
        out = run_report(ledger, capsys)
        assert "| 3 | complete | aaaaaaa..bbbbbbb (?) | — |" in out
        assert "| 4 | complete | aaaaaaa..bbbbbbb (?) | — |" in out

    def test_rulings_inside_minor_and_verify_lines_are_not_decisions(self, ledger, capsys):
        write_ledger(ledger, "Task 1: minor (deferred): naming nit. Ruling: leave it — why: cosmetic",
                     "Verify: grep -c Ruling: progress.md — exit 0 — Ruling: 3")
        assert "| — | none | — | — |" in section(run_report(ledger, capsys), "Decided", "Follow-up")

    def test_follow_up_is_never_truncated(self, ledger, capsys):
        write_ledger(ledger, *[f"Follow-up: item {i}" for i in range(60)])
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert "- item 59" in follow_up
        assert "more in" not in follow_up


class TestRulings:
    def test_a_bold_ruling_parses(self, ledger, capsys):
        write_ledger(ledger, "**Ruling:** keep A — why: b — cost if wrong: c")
        assert "| 1 | keep A | b | c |" in run_report(ledger, capsys)

    def test_a_ruling_in_a_table_cell_ends_at_the_cell(self, ledger, capsys):
        write_ledger(ledger, "| T3 | Ruling: keep A — b — c |")
        assert "| 1 | keep A | b | c |" in run_report(ledger, capsys)

    def test_an_escaped_pipe_in_a_table_cell_ruling_stays_in_the_cell(self, ledger, capsys):
        write_ledger(ledger, "| T3 | Ruling: use a \\| b — c — d | x |")
        assert "| 1 | use a \\| b | c | d |" in run_report(ledger, capsys)

    def test_a_wrapped_ruling_keeps_its_indented_continuation(self, ledger, capsys):
        write_ledger(ledger, "- Ruling: keep A — because the", "  loop is slow — cost if wrong: rework")
        assert "| 1 | keep A | because the loop is slow | rework |" in run_report(ledger, capsys)

    def test_an_empty_ruling_is_kept_and_flagged(self, ledger, capsys):
        write_ledger(ledger, "Ruling:")
        out = run_report(ledger, capsys)
        assert "| 1 | (no ruling text) | — | — |" in out
        assert "- Decided #1: not in the" in section(out, "Follow-up", "Verified")

    def test_a_ruling_missing_its_why_is_flagged(self, ledger, capsys):
        write_ledger(ledger, "Ruling: keep A — why: b — cost if wrong: c",
                     "Ruling: keep B — cost if wrong: c")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert ("- Decided #2: not in the `Ruling: <what> — <why> — cost if wrong: <cost>` shape"
                in follow_up)
        assert "#1" not in follow_up

    def test_a_superseding_ruling_marks_the_row_it_replaces(self, ledger, capsys):
        write_ledger(ledger, "Ruling: ship no entry point — plan asks only for main — cost if wrong: add one",
                     "Ruling: keep going — x — y",
                     'Ruling (supersedes "ship no entry point"): add __main__.py — users need a command'
                     " — cost if wrong: delete it")
        out = run_report(ledger, capsys)
        assert "| 1 | ship no entry point (superseded by #3) | plan asks only for main | add one |" in out
        assert "| 3 | add __main__.py (supersedes #1) | users need a command | delete it |" in out

    def test_a_supersedes_note_may_quote_parentheses(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use f(x) — b — c",
                     'Ruling (supersedes "use f(x)"): use g — b — c')
        assert "| 2 | use g (supersedes #1) | b | c |" in run_report(ledger, capsys)

    def test_a_supersedes_phrase_links_the_latest_matching_ruling(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use X for A — b — c", "Ruling: use X for B — b — c",
                     'Ruling (supersedes "use X"): use Y — b — c')
        out = run_report(ledger, capsys)
        assert "| 1 | use X for A | b | c |" in out
        assert "| 2 | use X for B (superseded by #3) | b | c |" in out

    def test_a_sub_bullet_under_a_ruling_is_not_joined_to_it(self, ledger, capsys):
        write_ledger(ledger, "- Ruling: keep A — b — c", "  - Task 1: minor (deferred): nit")
        out = run_report(ledger, capsys)
        assert "| 1 | keep A | b | c |" in out
        assert "- Task 1 deferred minor: nit" in out

    def test_a_supersedes_note_may_use_typographic_quotes(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use X — b — c", "Ruling (supersedes “use X”): use Y — b — c")
        assert "| 2 | use Y (supersedes #1) | b | c |" in run_report(ledger, capsys)

    def test_a_plain_ruling_that_reverses_another_is_flagged(self, ledger, capsys):
        write_ledger(ledger, "Ruling: ship no entry point — b — c",
                     "Ruling: the final review reverses the Task 2 entry-point ruling — b — c")
        assert ("- Decided #2: reads as reversing an earlier ruling; if it does, mark it with"
                ' `Ruling (supersedes "<words>"): …`'
                in section(run_report(ledger, capsys), "Follow-up", "Verified"))

    def test_an_unindented_line_after_a_ruling_is_flagged(self, ledger, capsys):
        write_ledger(ledger, "Ruling: keep A — because the", "loop is slow — cost if wrong: rework")
        assert ("- Decided #1: the next ledger line may continue it"
                in section(run_report(ledger, capsys), "Follow-up", "Verified"))

    def test_bold_is_stripped_only_from_rulings(self, ledger, capsys):
        write_ledger(ledger, "Task 1: minor (deferred): **Ruling:** leaves ** in the row")
        assert "- Task 1 deferred minor: **Ruling:** leaves ** in the row" in run_report(ledger, capsys)

    def test_an_unbalanced_annotation_falls_back_to_the_first_colon(self, ledger, capsys):
        write_ledger(ledger, "Ruling (supersedes Task 2 (entry point): add main — b — cost if wrong: c")
        assert "| 1 | add main | b | c |" in run_report(ledger, capsys)

    def test_a_bold_word_with_the_colon_outside_parses(self, ledger, capsys):
        write_ledger(ledger, "**Ruling**: keep A — b — cost if wrong: c")
        assert "| 1 | keep A | b | c |" in run_report(ledger, capsys)

    def test_a_line_that_looks_like_a_ruling_but_does_not_parse_is_flagged(self, ledger, capsys):
        write_ledger(ledger, "Ruling (draft: keep A — b — c")
        assert "- Not read as a ruling: Ruling (draft: keep A — b — c" in run_report(ledger, capsys)

    def test_other_annotations_are_ignored(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use X — b — c", "Ruling (oiler approved): use Y — b — c")
        out = run_report(ledger, capsys)
        assert "| 2 | use Y | b | c |" in out
        assert "Decided #" not in out

    def test_a_supersedes_note_counts_anywhere_in_the_annotation(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use X — b — c", 'Ruling (oiler approved; Supersedes "use X"): use Y — b — c')
        assert "| 2 | use Y (supersedes #1) | b | c |" in run_report(ledger, capsys)

    def test_a_supersedes_chain_marks_each_pair(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use X — b — c", 'Ruling (supersedes "use X"): use Y — b — c',
                     'Ruling (supersedes "use Y"): use Z — b — c')
        out = run_report(ledger, capsys)
        assert "| 2 | use Y (supersedes #1) (superseded by #3) | b | c |" in out
        assert "| 3 | use Z (supersedes #2) | b | c |" in out

    def test_a_row_superseded_twice_names_both(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use X — b — c", 'Ruling (supersedes "use X"): use Y — b — c',
                     'Ruling (supersedes "use X"): use Z — b — c')
        assert "| 1 | use X (superseded by #2, #3) | b | c |" in run_report(ledger, capsys)

    def test_a_quoted_supersedes_note_that_matches_nothing_is_flagged(self, ledger, capsys):
        write_ledger(ledger, 'Ruling (supersedes "nothing like this"): use Y — b — c')
        assert "- Decided #1: supersedes no earlier ruling" in run_report(ledger, capsys)

    def test_reversal_wording_variants_are_flagged(self, ledger, capsys):
        write_ledger(ledger, "Ruling: the final review reversed both Task 2 rulings — b — c")
        assert "- Decided #1: reads as reversing" in run_report(ledger, capsys)

    def test_a_numbered_item_under_a_ruling_is_not_joined_to_it(self, ledger, capsys):
        write_ledger(ledger, "- Ruling: keep A — b — cost if wrong: c", "  1. nit")
        assert "| 1 | keep A | b | c |" in run_report(ledger, capsys)

    def test_an_escaped_pipe_in_a_plain_ruling_is_not_doubled(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use a \\| b — c — d")
        assert "| 1 | use a \\| b | c | d |" in run_report(ledger, capsys)

    def test_a_ruling_quoted_in_a_follow_up_line_is_not_a_decision(self, ledger, capsys):
        write_ledger(ledger, "Follow-up: revisit Ruling: X — y — cost if wrong: z")
        out = run_report(ledger, capsys)
        assert "| — | none | — | — |" in out
        assert "- revisit Ruling: X — y — cost if wrong: z" in out

    def test_a_final_prefixed_parked_line_keeps_its_finding(self, ledger, capsys):
        write_ledger(ledger, "Final: parked — fd never closed — Ruling: process exits — cost if wrong: none")
        assert "| 1 | parked: fd never closed | process exits | none |" in run_report(ledger, capsys)

    def test_a_supersedes_note_that_matches_nothing_is_flagged(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use X — b — c",
                     "Ruling (supersedes the one above): use Y — b — c")
        out = run_report(ledger, capsys)
        assert "| 2 | use Y | b | c |" in out
        assert "- Decided #2: supersedes no earlier ruling" in section(out, "Follow-up", "Verified")

    def test_an_indented_bold_ruling_after_a_ruling_stays_its_own_row(self, ledger, capsys):
        write_ledger(ledger, "**Ruling:** keep B — b — cost if wrong: c",
                     "  **Ruling:** keep C — b — cost if wrong: c")
        out = run_report(ledger, capsys)
        assert "| 1 | keep B | b | c |" in out
        assert "| 2 | keep C | b | c |" in out

    def test_an_unindented_bold_ruling_after_a_ruling_is_not_flagged_as_a_continuation(self, ledger, capsys):
        write_ledger(ledger, "**Ruling:** keep A — b — cost if wrong: c",
                     "**Ruling:** keep B — b — cost if wrong: c")
        assert "may continue it" not in run_report(ledger, capsys)

    def test_an_indented_backticked_entry_after_a_ruling_is_not_joined_to_it(self, ledger, capsys):
        write_ledger(ledger, "Ruling: keep A — b — c", "  `Task 2: complete (commits aaaaaaa..bbbbbbb)`")
        assert "| 1 | keep A | b | c |" in run_report(ledger, capsys)

    def test_a_parked_line_with_no_finding_is_flagged(self, ledger, capsys):
        write_ledger(ledger, "Task 6: parked — Ruling: x — cost if wrong: z")
        assert "- Decided #1: not in the" in section(run_report(ledger, capsys), "Follow-up", "Verified")

    def test_every_cell_ruling_on_a_table_row_is_a_row(self, ledger, capsys):
        write_ledger(ledger, "| T3 | Ruling: keep A — b — c | Ruling: keep B — d — e |")
        out = run_report(ledger, capsys)
        assert "| 1 | keep A | b | c |" in out
        assert "| 2 | keep B | d | e |" in out

    def test_supersedes_words_match_with_whitespace_collapsed(self, ledger, capsys):
        write_ledger(ledger, "Ruling: use   X — b — c", 'Ruling (supersedes "use X"): use Y — b — c')
        assert "| 2 | use Y (supersedes #1) | b | c |" in run_report(ledger, capsys)


class TestFollowUp:
    def test_dependent_skips_fold_into_their_root(self, ledger, capsys):
        write_ledger(ledger, "Task 3: skipped — evergreen conflict — CLAUDE.md:3 — adds a dependency",
                     "Task 4: skipped — depends on Task 3",
                     "Task 5: skipped — depends on Task 4")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert ("- Task 3 skipped: evergreen conflict — CLAUDE.md:3 — adds a dependency"
                " (Tasks 4, 5 depend on it)") in follow_up
        assert "Task 4 skipped" not in follow_up

    def test_a_dependent_skip_whose_root_ran_keeps_its_own_line(self, ledger, capsys):
        write_ledger(ledger, "Task 4: skipped — depends on Task 3")
        assert "- Task 4 skipped: depends on Task 3" in run_report(ledger, capsys)

    def test_minors_on_a_batch_group_under_the_batch(self, ledger, capsys):
        write_ledger(ledger, "Task 3,4: minor (deferred): shared nit")
        assert "- Task 3,4 deferred minor: shared nit" in run_report(ledger, capsys)

    def test_a_skip_decision_joins_its_chain_line(self, ledger, capsys):
        write_ledger(ledger, "Task 3: skipped — evergreen conflict — CLAUDE.md:3 — adds a dependency",
                     "Task 4: skipped — depends on Task 3",
                     "Task 3: skip decision — rewrite on the stdlib, or amend CLAUDE.md")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert ("- Task 3 skipped: evergreen conflict — CLAUDE.md:3 — adds a dependency"
                " (Task 4 depends on it). Decide: rewrite on the stdlib, or amend CLAUDE.md") in follow_up
        assert "Task 4 skipped" not in follow_up

    def test_minors_after_a_final_review_say_they_may_be_resolved(self, ledger, capsys):
        write_ledger(ledger, "Task 1: minor (deferred): a",
                     "Task final: dispatch final-reviewer opus/high — whole branch")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert "- Deferred minors as ledgered; the final fix wave may have resolved" in follow_up

    def test_a_skip_decision_on_a_dependent_joins_the_root_line(self, ledger, capsys):
        write_ledger(ledger, "Task 3: skipped — evergreen conflict — CLAUDE.md:3 — x",
                     "Task 4: skipped — depends on Task 3", "Task 4: skip decision — drop both")
        assert "(Task 4 depends on it). Decide: drop both" in run_report(ledger, capsys)

    def test_a_skip_decision_for_an_unskipped_task_gets_its_own_line(self, ledger, capsys):
        write_ledger(ledger, "Task 5: skip decision — drop it")
        out = run_report(ledger, capsys)
        assert "- Task 5 decision: drop it" in out
        assert "| 5 |" not in out

    def test_a_skip_cycle_still_reaches_follow_up(self, ledger, capsys):
        write_ledger(ledger, "Task 3: skipped — depends on Task 4", "Task 4: skipped — depends on Task 3")
        assert "- Task 3 skipped: depends on Task 4 (Task 4 depends on it)" in run_report(ledger, capsys)

    def test_the_minors_lead_line_needs_a_final_review(self, ledger, capsys):
        write_ledger(ledger, "Task 1: minor (deferred): a")
        assert "Deferred minors as ledgered" not in run_report(ledger, capsys)
        write_ledger(ledger, "Task 1: minor (deferred): a", "Task final: complete (commits aaaaaaa..bbbbbbb, review clean)")
        assert "Deferred minors as ledgered" in run_report(ledger, capsys)

    def test_a_follow_up_line_without_a_leading_colon_is_kept_whole(self, ledger, capsys):
        write_ledger(ledger, "Follow-up — fix cli.py:9 crash")
        assert "- Follow-up — fix cli.py:9 crash" in run_report(ledger, capsys)

    def test_follow_up_lines_drop_their_prefix(self, ledger, capsys):
        write_ledger(ledger, "Follow-up: decide X")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert "- decide X" in follow_up
        assert "- Follow-up" not in follow_up

    def test_a_parked_line_without_a_ruling_stays_in_follow_up(self, ledger, capsys):
        write_ledger(ledger, "Task 2: parked — reviewer nit")
        assert "- Task 2 parked without a ruling: reviewer nit" in run_report(ledger, capsys)

    def test_deferred_minors_are_listed_inline_by_task(self, ledger, capsys):
        write_ledger(ledger, "Task 1: minor (deferred): a", "Task 1: minor (deferred): b",
                     "Task final: minor (deferred): c")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert "- Task 1 deferred minors: a · b" in follow_up
        assert "- Task final deferred minor: c" in follow_up

    def test_a_dashed_deferred_minor_drops_its_dash(self, ledger, capsys):
        write_ledger(ledger, "Task 1: minor (deferred) — text")
        assert "- Task 1 deferred minor: text" in run_report(ledger, capsys)

    def test_a_deferred_minor_without_a_colon_keeps_its_text(self, ledger, capsys):
        write_ledger(ledger, "Task 1: minor (deferred) nit")
        assert "- Task 1 deferred minor: nit" in run_report(ledger, capsys)

    def test_a_capitalized_depends_on_folds_into_its_chain(self, ledger, capsys):
        write_ledger(ledger, "Task 3: skipped — evergreen conflict — x", "Task 4: skipped — Depends on Task 3")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert "- Task 3 skipped: evergreen conflict — x (Task 4 depends on it)" in follow_up
        assert "Task 4 skipped" not in follow_up

    def test_depends_on_tasks_plural_folds_into_its_chain(self, ledger, capsys):
        write_ledger(ledger, "Task 3: skipped — evergreen conflict — x", "Task 4: skipped — depends on Tasks 3")
        assert "- Task 3 skipped: evergreen conflict — x (Task 4 depends on it)" in run_report(ledger, capsys)

    def test_a_skip_reason_drops_its_trailing_period(self, ledger, capsys):
        write_ledger(ledger, "Task 3: skipped — evergreen conflict — x.")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified").splitlines()
        assert "- Task 3 skipped: evergreen conflict — x" in follow_up

    def test_a_noted_follow_up_line_drops_its_prefix(self, ledger, capsys):
        write_ledger(ledger, "Follow-up (final review): decide X")
        follow_up = section(run_report(ledger, capsys), "Follow-up", "Verified")
        assert "- decide X" in follow_up
        assert "final review" not in follow_up

    def test_parked_lines_accept_colon_and_hyphen_separators(self, ledger, capsys):
        write_ledger(ledger, "Task 2: parked: nit a", "Task 3: parked - nit b")
        out = run_report(ledger, capsys)
        assert "- Task 2 parked without a ruling: nit a" in out
        assert "- Task 3 parked without a ruling: nit b" in out

    def test_a_parked_line_on_a_batch_stays_under_the_batch(self, ledger, capsys):
        write_ledger(ledger, "Task 3,4: parked — shared nit")
        assert "- Task 3,4 parked without a ruling: shared nit" in run_report(ledger, capsys)



class TestReportOnTheSmokeLedgers:
    """Ledgers from the v0.1.0 clean-room runs, with local paths scrubbed."""

    def render(self, name, ledger, capsys):
        ledger.write_text((FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8")
        return run_report(ledger, capsys, "--plan", "/nonexistent/plan.md")

    def test_a_well_formed_run_raises_no_ruling_warning(self, ledger, capsys):
        out = self.render("ledger-orko-sdd-run2.md", ledger, capsys)
        assert "Decided #" not in section(out, "Follow-up", "Verified")
        assert "| 10 | parked: `python3 -m textkit --help` shows prog as `__main__.py`" in out

    def test_each_parked_finding_and_skip_appears_once(self, ledger, capsys):
        out = self.render("ledger-orko-sdd-run2.md", ledger, capsys)
        assert out.count("non-UTF-8 stdin raises UnicodeDecodeError") == 1
        assert section(out, "Follow-up", "Verified").count("skipped") == 1

    def test_run_3s_malformed_ruling_and_reversals_are_flagged(self, ledger, capsys):
        out = self.render("ledger-orko-sdd-run3.md", ledger, capsys)
        warnings = [line for line in section(out, "Follow-up", "Verified").splitlines()
                    if line.startswith("- Decided #")]
        assert [w.split(":", 1)[0] for w in warnings] == ["- Decided #2", "- Decided #5, #6"]
        assert "reads as reversing" in warnings[1]

    def test_run_1s_plain_reversals_are_flagged(self, ledger, capsys):
        out = self.render("ledger-orko-sdd-run1.md", ledger, capsys)
        assert "- Decided #4, #6: reads as reversing an earlier ruling" in out
        assert "| 16 | parked: __main__.py:13 devnull fd never closed |" in out


class TestSkillMd:
    @pytest.fixture
    def text(self):
        return (orko_sdd.SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_role_table_matches_the_script(self, text):
        assert orko_sdd.render_role_table() in text

    def test_allowed_tools_grants_exactly_the_four_subcommands(self, text):
        frontmatter = text.split("---", 2)[1]
        grants = re.findall(r"Bash\(([^)]*)\)", frontmatter.split("allowed-tools:", 1)[1])
        assert grants == [f"python3 ${{CLAUDE_SKILL_DIR}}/scripts/orko_sdd.py {sub} *"
                          for sub in ("preflight", "log", "verify", "report")]

    def test_ruling_formats_match_the_script(self, text):
        assert orko_sdd.RULING_SHAPE in text
        assert orko_sdd.SUPERSEDES_SHAPE in text
        assert orko_sdd.SKIP_DECISION_SHAPE in text
