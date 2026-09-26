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
