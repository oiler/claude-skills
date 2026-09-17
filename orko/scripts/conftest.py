"""Shared fixtures for orko.py tests."""
import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURE_WORKSPACE = Path(__file__).parent / "fixtures" / "workspace"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q", "-b", "master")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "scaffold")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A scaffold workspace: docs/ and code/ as independent repos on master."""
    target = tmp_path / "ws"
    shutil.copytree(FIXTURE_WORKSPACE, target)
    _init_repo(target / "docs")
    _init_repo(target / "code")
    return target
