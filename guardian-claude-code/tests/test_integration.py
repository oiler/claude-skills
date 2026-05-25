from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
AUDIT = ROOT / "scripts" / "audit.py"


def run_audit(mode: str, env_extra: dict[str, str] | None = None) -> dict:
    env = os.environ.copy()
    env.update(env_extra or {})
    result = subprocess.run(
        ["uv", "run", "--quiet", str(AUDIT), mode],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_quick_mode_first_run_emits_baseline_message(tmp_path: Path, monkeypatch):
    payload = run_audit("quick", {"GUARDIAN_STATE_DIR": str(tmp_path)})
    assert payload["mode"] == "quick"
    assert payload["baseline_established"] is False
    assert "first run" in payload["message"].lower()


def test_quick_mode_with_baseline_emits_change_findings(tmp_path: Path):
    state = tmp_path / "guardian"
    state.mkdir()
    # Pre-seed a snapshot with one item
    (state / "snapshot.json").write_text(json.dumps({
        "schema_version": 1,
        "items": [{
            "surface": "mcp", "name": "ghost", "source": "npm:ghost",
            "version": "1.0", "publish_date": None, "publisher": None,
            "capabilities": [], "source_url": None, "content_hash": None,
        }],
    }))
    payload = run_audit("quick", {"GUARDIAN_STATE_DIR": str(state)})
    assert payload["baseline_established"] is True
    # 'ghost' is in baseline but not in current state — should show as removed
    categories = [f["category"] for f in payload["findings"]]
    assert "removed_item" in categories
