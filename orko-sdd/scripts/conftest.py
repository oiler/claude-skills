"""Shared fixtures for orko_sdd.py tests."""
from pathlib import Path

import pytest


@pytest.fixture
def ledger(tmp_path: Path) -> Path:
    """An SDD plan ledger at the path shape the script accepts."""
    path = tmp_path / "repo" / ".superpowers" / "sdd" / "plan" / "progress.md"
    path.parent.mkdir(parents=True)
    path.write_text("# SDD ledger — plan: docs/plan.md\n", encoding="utf-8")
    return path
