"""Shared fixtures for orko_review.py tests."""
import subprocess
from pathlib import Path

import pytest

import orko_review

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE_DOC = "/workshop/docs/superpowers/specs/2026-09-25-orko-review-design.md"
FIXTURE_PLAN = "/workshop/docs/superpowers/plans/2026-09-25-orko-review.md"


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A git repo laid out like a superpowers project: a spec, a plan that names it, and a CLAUDE.md."""
    root = tmp_path / "proj"
    write(root / "CLAUDE.md", "# proj\n")
    write(root / "docs" / "superpowers" / "specs" / "2026-09-25-widget-design.md", "# Widget design\n")
    write(root / "docs" / "superpowers" / "plans" / "2026-09-25-widget.md",
          "# Widget Implementation Plan\n\n**Spec:** `docs/superpowers/specs/2026-09-25-widget-design.md`\n")
    git(root, "init", "-q")
    return root.resolve()


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """A home whose ~/.claude/agents links the skill's agents directory, as the install command does."""
    home = tmp_path / "home"
    (home / ".claude" / "agents").mkdir(parents=True)
    (home / ".claude" / "agents" / "orko-review").symlink_to(orko_review.SKILL_DIR / "agents")
    return home


def report_text(lens: str, doc: str, source: str = "design") -> str:
    """A real review report from the fixtures, rebound to another lens and doc."""
    text = (FIXTURES / "reports" / f"{source}.md").read_text(encoding="utf-8")
    return (text.replace(f"lens: {source}\n", f"lens: {lens}\n", 1)
                .replace(f"doc: {FIXTURE_DOC}\n", f"doc: {doc}\n", 1))
