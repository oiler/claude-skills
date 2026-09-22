"""Tests for orko_sdd.py, the deterministic half of the orko-sdd skill."""
from pathlib import Path

import pytest

from conftest import git, write_plugins

import orko_sdd


def run_log(ledger, *extra, task="1", role="implementer-scoped", model="sonnet",
            effort="high", why="plan has the code"):
    return orko_sdd.main(["log", "--ledger", str(ledger), "--task", task, "--role", role,
                          "--model", model, "--effort", effort, "--why", why, *extra])


def last_line(ledger):
    return ledger.read_text(encoding="utf-8").splitlines()[-1]


class TestLog:
    def test_on_table_dispatch_appends_line_and_prints_dispatch_params(self, ledger, capsys):
        assert run_log(ledger) == 0
        assert last_line(ledger) == "Task 1: dispatch implementer-scoped sonnet/high — plan has the code"
        out = capsys.readouterr().out
        assert "subagent_type: orko-sdd-high" in out
        assert "model: sonnet" in out

    def test_off_table_dispatch_is_rejected_and_not_logged(self, ledger, capsys):
        before = ledger.read_text(encoding="utf-8")
        assert run_log(ledger, model="opus") == 2
        assert ledger.read_text(encoding="utf-8") == before
        assert "implementer-scoped allows sonnet/high" in capsys.readouterr().err

    def test_override_logs_off_table_dispatch_with_marker(self, ledger):
        assert run_log(ledger, "--override", model="opus", why="spec gap needs judgment") == 0
        assert last_line(ledger) == (
            "Task 1: dispatch implementer-scoped opus/high — spec gap needs judgment [override]")

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
        assert last_line(ledger) == "Task 3,4,5: dispatch implementer-scoped sonnet/high — plan has the code"

    def test_fix_incomplete_takes_same_model_at_next_effort(self, ledger):
        assert run_log(ledger, role="implementer-multifile", model="opus", effort="medium", why="w") == 0
        assert run_log(ledger, role="fix-incomplete", model="sonnet", effort="high", why="w") == 2
        assert run_log(ledger, role="fix-incomplete", model="opus", effort="high", why="w") == 0

    def test_fix_incomplete_rejected_after_a_high_effort_dispatch(self, ledger, capsys):
        assert run_log(ledger) == 0
        assert run_log(ledger, role="fix-incomplete", model="sonnet", effort="high", why="w") == 2
        assert "nothing after this task's last implementer dispatch" in capsys.readouterr().err

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
                if line.startswith("| ") and not line.startswith("| Ruling | Detail |")]
        assert len(rows) == 18

    def test_a_ruling_splits_into_ruling_detail_and_cost(self, out):
        assert ("| fixtures copied in T8 are refreshed once more after T11 if the workshop plan changed"
                " | spec says copies refresh when originals change"
                " | stale fixture, no behavior impact. |") in out

    def test_complete_tasks_carry_their_commit_ranges(self, out):
        assert "| 1 | complete | b41d456..fcc0685 (?) | — |" in out
        assert "| 11 | complete | c8d2903..63d6119 (?) | — |" in out

    def test_parked_findings_and_deferred_minors_reach_follow_up(self, out):
        follow_up = section(out, "Follow-up", "Recommended")
        assert "- 19 deferred minor finding(s): see " in follow_up
        assert "- Task 9 parked: em-dashes across orko/references and SKILL.md" in follow_up


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
        assert f"| 1. Alpha | complete | {a[:7]}..{b[:7]} (1) | sonnet/high, opus/low |" in out
        assert "| 2. Bravo | in progress | — | opus/medium |" in out
        assert ("| 3. Charlie | skipped — evergreen conflict — CLAUDE.md:3 — adds a third-party"
                " dependency | — | — |") in out
        assert "| 4. Delta | skipped — depends on Task 3 | — | — |" in out
        assert "| 5. Echo | not started | — | — |" in out
        assert "| final review | dispatched | — | opus/high |" in out
        assert "| uv run pytest -q | 0 | 12 passed \\| 0 failed |" in out
        assert "- Task 3 skipped: evergreen conflict" in section(out, "Follow-up", "Recommended")

    def test_plan_headings_inside_fences_are_ignored(self, ledger, capsys):
        ledger.write_text(f"# SDD ledger — plan: {FIXTURES / 'plan-sample.md'}\n", encoding="utf-8")
        out = run_report(ledger, capsys)
        assert "Not a real task" not in out
        assert out.count("| 1. Alpha |") == 1
        assert "| 6. Foxtrot | not started | — | — |" in out

    def test_empty_sections_say_so(self, ledger, capsys):
        write_ledger(ledger)
        out = run_report(ledger, capsys)
        assert "| none | — | — |" in out
        assert "- none" in section(out, "Follow-up", "Recommended")
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

    def test_rulings_inside_dispatch_lines_are_not_decisions(self, ledger, capsys):
        write_ledger(ledger, "Task 1: dispatch implementer-scoped sonnet/high — fine. Ruling: ship it — why: x")
        assert "| none | — | — |" in section(run_report(ledger, capsys), "Decided", "Follow-up")

    def test_bulleted_lines_parse(self, ledger, capsys):
        write_ledger(ledger,
                     "- Task 1: complete (commits aaaaaaa..bbbbbbb, 2 parked)",
                     "- Ruling: keep going — why: nothing blocks — cost if wrong: rework")
        out = run_report(ledger, capsys)
        assert "| 1 | complete (2 parked) | aaaaaaa..bbbbbbb (?) | — |" in out
        assert "| keep going | nothing blocks | rework |" in out

    def test_a_batch_dispatch_reaches_each_task(self, ledger, capsys):
        write_ledger(ledger, "Task 3,4: dispatch implementer-scoped sonnet/high — same-shape batch")
        out = run_report(ledger, capsys)
        assert "| 3 | in progress | — | sonnet/high |" in out
        assert "| 4 | in progress | — | sonnet/high |" in out

    def test_non_decided_sections_fit_forty_lines(self, ledger, capsys):
        write_ledger(ledger, "Task 1: complete (commits aaaaaaa..bbbbbbb, review clean)",
                     *[f"Follow-up: item {i}" for i in range(60)],
                     *[f"Ruling: decision {i} — why: reason {i} — cost if wrong: none" for i in range(30)])
        out = run_report(ledger, capsys)
        before, rest = out.split("## Decided", 1)
        kept = (before + "## Follow-up" + rest.split("## Follow-up", 1)[1]).splitlines()
        assert len(kept) + orko_sdd.RECOMMENDED_RESERVE <= 40
        assert f"more in {ledger}" in out
        assert sum(1 for line in out.splitlines() if line.startswith("| decision ")) == 30
