"""Shared fixtures for orko_sdd.py tests."""
import json
import subprocess
from pathlib import Path

import pytest

import orko_sdd


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@example.invalid", "-c", "user.name=t", *args],
        check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def write_plugins(home: Path, version: str) -> None:
    path = home / ".claude" / "plugins" / "installed_plugins.json"
    path.write_text(json.dumps({"version": 2, "plugins": {
        "superpowers@claude-plugins-official": [{"scope": "user", "version": version}]}}),
        encoding="utf-8")


@pytest.fixture
def ledger(tmp_path: Path) -> Path:
    """An SDD plan ledger at the path shape the script accepts."""
    path = tmp_path / "repo" / ".superpowers" / "sdd" / "plan" / "progress.md"
    path.parent.mkdir(parents=True)
    path.write_text("# SDD ledger — plan: docs/plan.md\n", encoding="utf-8")
    return path


@pytest.fixture
def fake_home(tmp_path: Path) -> Path:
    """A home with superpowers 6.4.1 installed and the agents linked as a directory symlink."""
    home = tmp_path / "home"
    (home / ".claude" / "plugins").mkdir(parents=True)
    write_plugins(home, orko_sdd.SDD_PIN)
    (home / ".claude" / "agents").mkdir()
    (home / ".claude" / "agents" / "orko-sdd").symlink_to(orko_sdd.SKILL_DIR / "agents")
    return home


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repository on master whose one commit holds a plan at docs/plan.md."""
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "plan.md").write_text("### Task 1: Alpha\n", encoding="utf-8")
    git(root, "init", "-q", "-b", "master")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root
