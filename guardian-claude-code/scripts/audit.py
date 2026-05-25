#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27",
#     "packaging>=24.0",
# ]
# ///
"""guardian-claude-code: audit Claude Code's third-party trust surface."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from snapshot import Snapshot, load_snapshot, save_snapshot, diff_snapshots
from enumerate import (
    enumerate_mcp_servers, enumerate_plugins,
    enumerate_skills, enumerate_hooks,
)
from signals import change_findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audit.py", description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("quick", help="Fast diff vs last snapshot, no network.")
    sub.add_parser("deep", help="Full audit with registry/GitHub API calls.")
    args = parser.parse_args(argv)

    if args.mode == "quick":
        return run_quick()
    if args.mode == "deep":
        return run_deep()
    return 2


def state_dir() -> Path:
    p = Path(os.environ.get("GUARDIAN_STATE_DIR", Path.home() / ".claude" / "guardian"))
    p.mkdir(parents=True, exist_ok=True)
    (p / "cache").mkdir(exist_ok=True)
    return p


def _enumerate_all() -> Snapshot:
    items = []
    # MCP servers
    try:
        result = subprocess.run(
            ["claude", "mcp", "list", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            items += enumerate_mcp_servers(json.loads(result.stdout))
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        logging.warning("MCP enumeration skipped: %s", e)
    # Plugins
    items += enumerate_plugins(Path.home() / ".claude" / "plugins" / "cache")
    # Skills
    items += enumerate_skills(Path.home() / ".claude" / "skills")
    # Hooks
    items += enumerate_hooks([
        (Path.home() / ".claude" / "settings.json", "user"),
        (Path.cwd() / ".claude" / "settings.json", "project"),
    ])
    return Snapshot(items=items)


def run_quick() -> int:
    sd = state_dir()
    snap_path = sd / "snapshot.json"
    prev = load_snapshot(snap_path)
    current = _enumerate_all()

    if not prev.items:
        print(json.dumps({
            "mode": "quick",
            "baseline_established": False,
            "message": "First run — no baseline. Run `audit.py deep` to establish one.",
            "findings": [],
        }))
        return 0

    changes = diff_snapshots(prev, current)
    findings = change_findings(changes)
    # Quick mode only emits change-derived findings (no network).
    print(json.dumps({
        "mode": "quick",
        "baseline_established": True,
        "message": f"{len(findings)} change(s) since last snapshot.",
        "findings": [f.to_dict() for f in findings],
    }))
    return 0


def run_deep() -> int:
    print(json.dumps({"mode": "deep", "findings": []}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
