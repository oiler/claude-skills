"""Shared pytest fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def tmp_state_dir(tmp_path: Path) -> Path:
    """A clean ~/.claude/guardian/ replacement for the test."""
    d = tmp_path / "guardian"
    d.mkdir()
    (d / "cache").mkdir()
    return d


def load_fixture_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())
