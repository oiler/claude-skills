"""Tests for orko_review.py, the deterministic half of the orko-review skill."""
import re
from datetime import datetime
from pathlib import Path

import pytest

from conftest import FIXTURE_DOC, FIXTURE_PLAN, FIXTURES, git, report_text, write

import orko_review

SPEC_REL = "docs/superpowers/specs/2026-09-25-widget-design.md"
PLAN_REL = "docs/superpowers/plans/2026-09-25-widget.md"

# Header lines copied from the workshop's plans (the absolute one with its user path replaced).
REAL_SPEC_LINES = {
    "absolute": ("**Spec:** `/srv/proj/docs/superpowers/specs/2026-09-25-orko-sdd-v0.1.1-design.md`",
                 "/srv/proj/docs/superpowers/specs/2026-09-25-orko-sdd-v0.1.1-design.md"),
    "tilde": ("**Spec:** `~/files/projects/001-claude-skills-creator/docs/superpowers/specs/2026-09-22-orko-sdd-design.md`",
              "~/files/projects/001-claude-skills-creator/docs/superpowers/specs/2026-09-22-orko-sdd-design.md"),
    "repo-relative": ("**Spec:** `docs/superpowers/specs/2026-08-26-design-sys-design.md`",
                      "docs/superpowers/specs/2026-08-26-design-sys-design.md"),
    "trailing parenthetical": (
        "**Spec:** `docs/superpowers/specs/2026-07-18-wordpress-plugins-test-harness-design.md` "
        "(in the workshop repo — read it if any task's rationale is unclear).",
        "docs/superpowers/specs/2026-07-18-wordpress-plugins-test-harness-design.md"),
    "trailing period": ("**Spec:** `docs/superpowers/specs/2026-08-05-cowork-builder-v0.4.0-upgrade-design.md`.",
                        "docs/superpowers/specs/2026-08-05-cowork-builder-v0.4.0-upgrade-design.md"),
    "unquoted with period": ("**Spec:** docs/specs/a-design.md.", "docs/specs/a-design.md"),
}


class TestDetectType:
    def test_parent_directory_specs_is_spec(self, project):
        assert orko_review.detect_type(project / SPEC_REL)[0] == "spec"

    def test_parent_directory_plans_is_plan(self, project):
        assert orko_review.detect_type(project / PLAN_REL)[0] == "plan"

    def test_design_suffix_outside_specs_is_spec(self, tmp_path):
        assert orko_review.detect_type(write(tmp_path / "auth-design.md", "# Auth\n"))[0] == "spec"

    def test_leading_spec_line_is_plan(self, tmp_path):
        doc = write(tmp_path / "rollout.md", "# Rollout\n\n- **Spec:** `x.md`\n")
        assert orko_review.detect_type(doc)[0] == "plan"

    def test_indented_spec_line_is_plan(self, tmp_path):
        doc = write(tmp_path / "rollout.md", "# Rollout\n\n  **Spec:** `x.md`\n")
        assert orko_review.detect_type(doc)[0] == "plan"

    def test_mid_line_spec_mention_stays_generic(self, tmp_path):
        doc = write(tmp_path / "notes.md", "| Upstream pin | plan header (`**Spec:**` line) |\n")
        assert orko_review.detect_type(doc)[0] == "generic"

    def test_spec_line_after_line_40_stays_generic(self, tmp_path):
        doc = write(tmp_path / "notes.md", "x\n" * 40 + "**Spec:** `a.md`\n")
        assert orko_review.detect_type(doc)[0] == "generic"


class TestSpecResolution:
    @pytest.mark.parametrize("line,token", REAL_SPEC_LINES.values(), ids=REAL_SPEC_LINES.keys())
    def test_token_from_each_observed_header_form(self, line, token):
        value = orko_review.SPEC_LINE_RE.match(line).group(1)
        assert orko_review.spec_token(value) == token

    def test_url_value_is_unresolvable(self):
        assert orko_review.spec_token(" https://agentskills.io/specification") is None

    def test_repo_relative_value_resolves_from_repo_root(self, project):
        assert orko_review.resolve_spec(project / PLAN_REL, project) == project / SPEC_REL

    def test_plan_relative_value_resolves_from_plan_directory(self, project):
        plan = write(project / "docs" / "superpowers" / "plans" / "p.md",
                     "**Spec:** `../specs/2026-09-25-widget-design.md`\n")
        assert orko_review.resolve_spec(plan, project) == project / SPEC_REL

    def test_absolute_value_resolves(self, project, tmp_path):
        spec = write(tmp_path / "elsewhere" / "s.md", "# s\n").resolve()
        plan = write(project / "p.md", f"**Spec:** `{spec}`\n")
        assert orko_review.resolve_spec(plan, project) == spec

    def test_tilde_value_expands_home(self, project, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "h"))
        spec = write(tmp_path / "h" / "specs" / "s.md", "# s\n").resolve()
        plan = write(project / "p.md", "**Spec:** `~/specs/s.md`\n")
        assert orko_review.resolve_spec(plan, project) == spec

    def test_first_spec_line_wins(self, project):
        plan = write(project / "p.md", f"**Spec:** `{SPEC_REL}`\n\n**Spec:** {{{{SPEC_PATH}}}}\n")
        assert orko_review.resolve_spec(plan, project) == project / SPEC_REL

    def test_non_bold_spec_line_is_unresolvable(self, project):
        plan = write(project / "p.md", f"- Spec: `{SPEC_REL}`\n")
        assert orko_review.resolve_spec(plan, project) is None

    def test_missing_file_is_unresolvable(self, project):
        plan = write(project / "p.md", "**Spec:** `docs/nope.md`\n")
        assert orko_review.resolve_spec(plan, project) is None

    def test_unexpandable_tilde_value_is_unresolvable(self, project):
        plan = write(project / "p.md", "**Spec:** `~nosuchuser_zz/x.md`\n")
        assert orko_review.resolve_spec(plan, project) is None


class TestRepoRootAndReviewsDir:
    def test_repo_root_is_the_docs_repository(self, project):
        assert orko_review.repo_root(project / SPEC_REL) == project

    def test_repo_root_outside_git_is_the_docs_directory(self, tmp_path):
        doc = write(tmp_path / "loose" / "x.md", "# x\n").resolve()
        assert orko_review.repo_root(doc) == doc.parent

    def test_nearest_superpowers_ancestor(self, project):
        assert orko_review.reviews_dir(project / PLAN_REL, project) == project / "docs/superpowers/reviews"

    def test_superpowers_search_stops_at_repo_root(self, tmp_path):
        root = tmp_path / "superpowers" / "proj"
        doc = write(root / "docs" / "notes.md", "# n\n")
        git(root, "init", "-q")
        root, doc = root.resolve(), doc.resolve()
        assert orko_review.reviews_dir(doc, root) == root / "docs" / "reviews"

    def test_specs_directory_gets_a_sibling_reviews(self, project):
        doc = write(project / "docs/versions/0.15/specs/x.md", "# x\n")
        assert orko_review.reviews_dir(doc, project) == project / "docs/versions/0.15/reviews"

    def test_other_directory_gets_its_own_reviews(self, project):
        doc = write(project / "docs/versions/0.15/spec.md", "# x\n")
        assert orko_review.reviews_dir(doc, project) == project / "docs/versions/0.15/reviews"

    def test_repo_root_doc_gets_root_reviews(self, project):
        doc = write(project / "OBJECTIVE.md", "# o\n")
        assert orko_review.reviews_dir(doc, project) == project / "reviews"


class TestEvergreenAndLenses:
    def test_evergreen_docs_at_root_and_in_docs(self, project):
        write(project / "docs" / "OBJECTIVE.md", "# o\n")
        assert orko_review.evergreen_docs(project) == [project / "CLAUDE.md", project / "docs" / "OBJECTIVE.md"]

    def test_no_evergreen_docs(self, tmp_path):
        assert orko_review.evergreen_docs(tmp_path) == []

    def test_every_catalog_lens_has_a_file_and_every_file_is_in_the_catalog(self):
        expected = {orko_review.lens_file(t, lens) for t, lenses in orko_review.CORE_LENSES.items() for lens in lenses}
        expected |= {orko_review.lens_file("spec", lens) for lens in orko_review.EXTRA_LENSES}
        assert all(p.is_file() for p in expected)
        assert set(orko_review.LENS_DIR.glob("*.md")) == expected

    def test_specialist_names_never_equal_core_names(self):
        core = {lens for lenses in orko_review.CORE_LENSES.values() for lens in lenses}
        assert not core & set(orko_review.EXTRA_LENSES)


def pre(argv, home, cwd):
    return orko_review.preflight_lines(argv, home, cwd)


def blocked(lines):
    return lines[-1] == "STATUS: blocked"


class TestPreflight:
    def test_spec_doc_reports_its_resolution(self, project, home):
        lines = pre(["--effort", "high", SPEC_REL], home, project)
        assert lines[-1] == "STATUS: ok"
        assert "mode: apply" in lines
        assert "effort: high" in lines
        assert f"doc: {project / SPEC_REL}" in lines
        assert "type: spec (parent directory specs/)" in lines
        assert "lenses: accuracy, completeness, design" in lines
        assert "extras-available: security, frontend, data, performance, operations" in lines
        assert f"evergreen: {project / 'CLAUDE.md'}" in lines
        assert f"reviews-dir: {project / 'docs/superpowers/reviews'}" in lines
        assert "agent: orko-review-reviewer" in lines

    @pytest.mark.parametrize("level", ["high", "xhigh", "max"])
    def test_high_and_above_pass_the_effort_gate(self, project, home, level):
        assert pre(["--effort", level, SPEC_REL], home, project)[-1] == "STATUS: ok"

    def test_project_level_agent_link_is_found(self, project, tmp_path):
        (project / ".claude" / "agents").mkdir(parents=True)
        (project / ".claude" / "agents" / "orko-review").symlink_to(orko_review.SKILL_DIR / "agents")
        lines = pre(["--effort", "high", SPEC_REL], tmp_path / "emptyhome", project)
        assert "agent: orko-review-reviewer" in lines

    def test_symlink_loop_in_agents_directory_terminates(self, project, home):
        (home / ".claude" / "agents" / "loop").symlink_to(home / ".claude" / "agents")
        assert pre(["--effort", "high", SPEC_REL], home, project)[-1] == "STATUS: ok"

    def test_spec_flag_pointing_at_a_missing_file_blocks(self, project, home):
        lines = pre(["--effort", "high", PLAN_REL, "--spec", "docs/nope.md"], home, project)
        assert any(l.startswith("problem: spec not found") for l in lines)

    def test_relative_doc_path_resolves_against_the_cwd(self, project, home):
        lines = pre(["--effort", "high", "specs/2026-09-25-widget-design.md"], home, project / "docs/superpowers")
        assert f"doc: {project / SPEC_REL}" in lines

    def test_plan_reports_its_spec(self, project, home):
        lines = pre(["--effort", "high", PLAN_REL], home, project)
        assert f"spec: {project / SPEC_REL}" in lines
        assert "lenses: coverage, executability, verification" in lines

    def test_plan_with_unresolvable_spec_blocks_with_hint(self, project, home):
        write(project / PLAN_REL, "# Plan\n\n**Spec:** `docs/nope.md`\n")
        lines = pre(["--effort", "high", PLAN_REL], home, project)
        assert blocked(lines)
        assert "hint: pass --spec <path>" in lines

    def test_spec_flag_overrides_the_plan_header(self, project, home):
        other = write(project / "other-design.md", "# o\n")
        lines = pre(["--effort", "high", PLAN_REL, "--spec", "other-design.md"], home, project)
        assert f"spec: {other}" in lines

    def test_spec_flag_on_a_spec_blocks(self, project, home):
        lines = pre(["--effort", "high", SPEC_REL, "--spec", PLAN_REL], home, project)
        assert "problem: --spec applies only to plans" in lines

    def test_missing_doc_blocks(self, project, home):
        assert blocked(pre(["--effort", "high", "docs/nope.md"], home, project))

    def test_non_markdown_doc_blocks(self, project, home):
        write(project / "notes.txt", "x\n")
        lines = pre(["--effort", "high", "notes.txt"], home, project)
        assert any(l.startswith("problem: not a Markdown doc") for l in lines)

    def test_two_positionals_block_and_suggest_quoting(self, project, home):
        lines = pre(["--effort", "high", "my", "spec.md"], home, project)
        assert any("wrap a path with spaces in quotes" in l for l in lines)

    def test_unknown_flag_blocks(self, project, home):
        assert blocked(pre(["--effort", "high", SPEC_REL, "--fast"], home, project))

    def test_both_mode_flags_block(self, project, home):
        assert blocked(pre(["--effort", "high", SPEC_REL, "--apply", "--file-only"], home, project))

    def test_apply_below_high_blocks_with_effort_hint(self, project, home):
        lines = pre(["--effort", "medium", SPEC_REL], home, project)
        assert blocked(lines)
        assert "hint: run /effort high, then rerun" in lines

    def test_file_only_below_high_warns_and_continues(self, project, home):
        lines = pre(["--effort", "medium", SPEC_REL, "--file-only"], home, project)
        assert lines[-1] == "STATUS: ok"
        assert "mode: file-only" in lines
        assert any(l.startswith("warning: session effort is medium") for l in lines)

    @pytest.mark.parametrize("value", ["", "${CLAUDE_EFFORT}"])
    def test_unknown_effort_warns_and_does_not_block(self, project, home, value):
        lines = pre(["--effort", value, SPEC_REL], home, project)
        assert "effort: unknown" in lines
        assert lines[-1] == "STATUS: ok"

    def test_missing_agent_blocks_with_install_hint(self, project, tmp_path):
        lines = pre(["--effort", "high", SPEC_REL], tmp_path / "emptyhome", project)
        assert "agent: missing" in lines
        assert f"hint: install with: {orko_review.AGENT_INSTALL}" in lines

    def test_agent_without_high_effort_blocks(self, project, tmp_path):
        agents = tmp_path / "h2" / ".claude" / "agents"
        write(agents / "r.md", "---\nname: orko-review-reviewer\neffort: medium\n---\nx\n")
        lines = pre(["--effort", "high", SPEC_REL], tmp_path / "h2", project)
        assert "problem: orko-review-reviewer must pin effort: high" in lines

    def test_crash_still_exits_zero(self, monkeypatch, capsys):
        def boom(*_):
            raise RuntimeError("x")
        monkeypatch.setattr(orko_review, "preflight_lines", boom)
        assert orko_review.main(["preflight", "a.md"]) == 0
        assert capsys.readouterr().out.strip().endswith("STATUS: blocked")
