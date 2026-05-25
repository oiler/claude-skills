from __future__ import annotations

import json
from pathlib import Path

import pytest

from findings import Category, Finding, Severity, Surface
from overrides import (
    Override,
    apply_overrides,
    load_overrides,
    save_overrides,
)


def make_finding(category=Category.COOLDOWN, item="x", surface=Surface.MCP, evidence=None):
    return Finding(
        severity=Severity.WARN,
        category=category,
        surface=surface,
        item=item,
        signal="...",
        evidence=evidence or {},
        fix_hint="",
    )


def test_load_missing_file_returns_empty(tmp_state_dir: Path):
    assert load_overrides(tmp_state_dir / "trust-overrides.json") == []


def test_save_and_load_roundtrip(tmp_state_dir: Path):
    overrides = [Override(
        surface="mcp", item="x", rules={"cooldown_exempt": True},
        reason="actively tracked", added="2026-05-24",
    )]
    path = tmp_state_dir / "trust-overrides.json"
    save_overrides(overrides, path)
    assert load_overrides(path) == overrides


def test_cooldown_exempt_silences_only_cooldown():
    overrides = [Override(surface="mcp", item="x", rules={"cooldown_exempt": True})]
    findings = [
        make_finding(category=Category.COOLDOWN, item="x"),
        make_finding(category=Category.CAPABILITY_DIFF, item="x"),
    ]
    out = apply_overrides(findings, overrides)
    assert [f.category for f in out] == [Category.CAPABILITY_DIFF]


def test_high_signal_categories_never_silenced_by_normal_rules():
    overrides = [Override(
        surface="mcp", item="x",
        rules={"silence_until_date": "2099-01-01", "cooldown_exempt": True},
    )]
    findings = [
        make_finding(category=Category.URL_MISMATCH, item="x"),
        make_finding(category=Category.MAINTAINER_CHANGE, item="x"),
        make_finding(category=Category.CAPABILITY_DIFF, item="x"),
    ]
    out = apply_overrides(findings, overrides)
    assert len(out) == 3  # all three high-signal categories survive


def test_force_silence_all_silences_everything():
    overrides = [Override(
        surface="mcp", item="x",
        rules={"force_silence_all": True},
        reason="known-safe in our private fork",
    )]
    findings = [
        make_finding(category=Category.COOLDOWN, item="x"),
        make_finding(category=Category.CAPABILITY_DIFF, item="x"),
        make_finding(category=Category.URL_MISMATCH, item="x"),
    ]
    out = apply_overrides(findings, overrides)
    assert out == []


def test_force_silence_all_requires_reason():
    with pytest.raises(ValueError, match="force_silence_all requires reason"):
        Override(surface="mcp", item="x", rules={"force_silence_all": True})


def test_silence_until_version_suppresses_below_threshold():
    overrides = [Override(
        surface="plugin", item="x", rules={"silence_until_version": "2.0.0"},
    )]
    below = make_finding(category=Category.COOLDOWN, item="x",
                         surface=Surface.PLUGIN,
                         evidence={"current_version": "1.9.0"})
    above = make_finding(category=Category.COOLDOWN, item="x",
                         surface=Surface.PLUGIN,
                         evidence={"current_version": "2.0.0"})
    out_below = apply_overrides([below], overrides)
    out_above = apply_overrides([above], overrides)
    assert out_below == []
    assert out_above == [above]


def test_silence_until_date_suppresses_before_date(monkeypatch):
    import overrides as ov
    monkeypatch.setattr(ov, "today", lambda: "2026-05-24")
    overrides_list = [Override(
        surface="plugin", item="x", rules={"silence_until_date": "2026-06-01"},
    )]
    f = make_finding(category=Category.COOLDOWN, item="x", surface=Surface.PLUGIN)
    assert apply_overrides([f], overrides_list) == []

    monkeypatch.setattr(ov, "today", lambda: "2026-06-02")
    assert apply_overrides([f], overrides_list) == [f]


def test_override_matches_by_surface_and_item():
    overrides = [Override(surface="mcp", item="x", rules={"cooldown_exempt": True})]
    # Same name, different surface — override should NOT apply
    f = make_finding(category=Category.COOLDOWN, item="x", surface=Surface.PLUGIN)
    assert apply_overrides([f], overrides) == [f]
