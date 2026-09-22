"""Tests for orko_sdd.py, the deterministic half of the orko-sdd skill."""
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
