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


def test_deep_mode_writes_snapshot_and_emits_findings(tmp_path: Path):
    state = tmp_path / "guardian"
    state.mkdir()
    payload = run_audit("deep", {"GUARDIAN_STATE_DIR": str(state),
                                  "GUARDIAN_OFFLINE": "1"})
    assert payload["mode"] == "deep"
    assert "findings" in payload
    # Snapshot file was created
    assert (state / "snapshot.json").exists()
    # In offline mode, expect an info-level finding noting skipped network checks
    info_skipped = [f for f in payload["findings"]
                    if f["category"] in ("repo_health", "cooldown", "maintainer_change")]
    # Offline = no findings from those categories
    assert info_skipped == []
    # Should still emit a notice
    assert any("offline" in (f["signal"] or "").lower() for f in payload["findings"]) \
        or payload.get("notices")


import shutil


def test_integration_three_fixture_plugins(tmp_path: Path, fixtures_dir: Path):
    """End-to-end deep-mode run against the integration fixture tree."""
    state = tmp_path / "guardian"
    state.mkdir()

    # Pre-seed snapshot: capability-expansion was 1.0.0 with only 'skill:base'
    (state / "snapshot.json").write_text(json.dumps({
        "schema_version": 1,
        "items": [{
            "surface": "plugin", "name": "capability-expansion",
            "source": "git:https://github.com/example/cap-exp",
            "version": "1.0.0",
            "publish_date": None, "publisher": None,
            "capabilities": ["skill:base"],
            "source_url": "https://github.com/example/cap-exp",
            "content_hash": None,
        }],
    }))

    # Point HOME at our fixture so enumerate_plugins finds our plugin tree
    fake_home = tmp_path / "home"
    plugins = fake_home / ".claude" / "plugins" / "cache"
    plugins.mkdir(parents=True)
    shutil.copytree(fixtures_dir / "integration" / "plugins", plugins / "marketplace",
                    dirs_exist_ok=True)

    payload = run_audit("deep", {
        "GUARDIAN_STATE_DIR": str(state),
        "GUARDIAN_OFFLINE": "1",   # avoid network in CI
        "HOME": str(fake_home),
    })

    findings_by_item = {}
    for f in payload["findings"]:
        findings_by_item.setdefault(f["item"], []).append(f["category"])

    # capability-expansion went from {skill:base} to {skill:base, command:run-shell}
    assert "capability_diff" in findings_by_item.get("capability-expansion", [])

    # benign-update is brand new
    assert "new_item" in findings_by_item.get("benign-update", [])

    # url-mismatch is also new (offline mode skips the actual URL check)
    assert "new_item" in findings_by_item.get("url-mismatch", [])
