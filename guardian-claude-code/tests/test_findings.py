from __future__ import annotations

import json

import pytest

from findings import Finding, Severity, Category, Surface


def test_finding_serializes_to_dict_with_expected_fields():
    f = Finding(
        severity=Severity.HIGH,
        category=Category.CAPABILITY_DIFF,
        surface=Surface.MCP,
        item="example-mcp",
        signal="Added shell-exec tool not present in previous version",
        evidence={"current_version": "1.2.3", "previous_version": "1.2.2"},
        fix_hint="pin to previous version",
    )
    d = f.to_dict()
    assert d == {
        "severity": "high",
        "category": "capability_diff",
        "surface": "mcp",
        "item": "example-mcp",
        "signal": "Added shell-exec tool not present in previous version",
        "evidence": {"current_version": "1.2.3", "previous_version": "1.2.2"},
        "fix_hint": "pin to previous version",
    }


def test_finding_json_roundtrip():
    f = Finding(
        severity=Severity.WARN,
        category=Category.COOLDOWN,
        surface=Surface.PLUGIN,
        item="foo",
        signal="published 2 days ago",
        evidence={"days_ago": 2},
        fix_hint="wait until day 7",
    )
    s = json.dumps(f.to_dict())
    back = json.loads(s)
    assert back["severity"] == "warn"
    assert back["evidence"]["days_ago"] == 2


def test_severity_ordering_high_above_warn_above_info():
    assert Severity.HIGH.rank > Severity.WARN.rank > Severity.INFO.rank


def test_malformed_manifest_is_a_category():
    assert Category.MALFORMED_MANIFEST.value == "malformed_manifest"
