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
from findings import Finding, Category, Severity, Surface
from registry import Registry
from signals import (
    cooldown_findings, capability_diff_findings,
    url_mismatch_findings, maintainer_change_findings,
    repo_health_findings, change_findings,
)
from overrides import load_overrides, apply_overrides


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


def _enrich_with_registry(items: list, reg: Registry) -> tuple[list, dict, dict]:
    """Populate publish_date/publisher and gather registry URLs + repo metadata."""
    from snapshot import Item as _Item  # avoid circular hint
    enriched: list = []
    registry_urls: dict = {}
    repo_meta: dict = {}
    for i in items:
        new_publish = i.publish_date
        new_publisher = i.publisher
        if i.surface == "mcp" and i.source.startswith("npm:") and i.version:
            pkg = i.source.removeprefix("npm:")
            meta = reg.npm(pkg, i.version)
            if meta:
                new_publish = meta.publish_date
                new_publisher = meta.publisher
                if meta.repository_url:
                    registry_urls[(i.surface, i.name)] = meta.repository_url
                    rm = reg.github_repo(meta.repository_url)
                    if rm:
                        repo_meta[(i.surface, i.name)] = rm
        elif i.surface == "mcp" and i.source.startswith("pip:") and i.version:
            pkg = i.source.removeprefix("pip:")
            meta = reg.pypi(pkg, i.version)
            if meta:
                new_publish = meta.publish_date
                new_publisher = meta.publisher
                if meta.repository_url:
                    registry_urls[(i.surface, i.name)] = meta.repository_url
                    rm = reg.github_repo(meta.repository_url)
                    if rm:
                        repo_meta[(i.surface, i.name)] = rm
        elif i.surface == "plugin" and i.source_url:
            rm = reg.github_repo(i.source_url)
            if rm:
                repo_meta[(i.surface, i.name)] = rm

        enriched.append(_Item(
            surface=i.surface, name=i.name, source=i.source, version=i.version,
            publish_date=new_publish, publisher=new_publisher,
            capabilities=i.capabilities, source_url=i.source_url,
            content_hash=i.content_hash,
        ))
    return enriched, registry_urls, repo_meta


def run_deep() -> int:
    sd = state_dir()
    snap_path = sd / "snapshot.json"
    overrides_path = sd / "trust-overrides.json"
    offline = os.environ.get("GUARDIAN_OFFLINE") == "1"

    prev = load_snapshot(snap_path)
    current_raw = _enumerate_all()
    notices: list[str] = []

    if offline:
        current = current_raw
        notices.append("offline mode — registry, publisher, and repo-health checks skipped")
        registry_urls: dict = {}
        repo_meta: dict = {}
    else:
        reg = Registry(cache_dir=sd / "cache", ttl_seconds=3600)
        items, registry_urls, repo_meta = _enrich_with_registry(
            current_raw.items, reg,
        )
        current = Snapshot(items=items)

    findings: list[Finding] = []
    if not offline:
        findings += cooldown_findings(current.items)
        findings += url_mismatch_findings(current.items, registry_urls)
        findings += maintainer_change_findings(prev.items, current.items)
        findings += repo_health_findings(current.items, repo_meta)

    if prev.items:
        changes = diff_snapshots(prev, current)
        findings += capability_diff_findings(changes)
        findings += change_findings(changes)

    findings = apply_overrides(findings, load_overrides(overrides_path))

    save_snapshot(current, snap_path)

    output = {
        "mode": "deep",
        "findings": [f.to_dict() for f in findings],
    }
    if notices:
        output["notices"] = notices
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
