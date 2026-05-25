from __future__ import annotations

from datetime import date, timedelta

import pytest

from findings import Category, Severity, Surface
from snapshot import Change, Item, Snapshot
from signals import cooldown_findings, change_findings


def item(name="x", surface="mcp", publish_date=None, version=None):
    return Item(
        surface=surface, name=name, source="npm:x",
        version=version, publish_date=publish_date,
        publisher=None, capabilities=[], source_url=None, content_hash=None,
    )


def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def test_cooldown_fires_for_items_under_7_days(tmp_path):
    items = [
        item("recent", publish_date=days_ago(2)),
        item("old", publish_date=days_ago(30)),
        item("no-date", publish_date=None),
    ]
    findings = cooldown_findings(items, cooldown_days=7)
    names = [f.item for f in findings]
    assert names == ["recent"]
    assert findings[0].severity is Severity.WARN
    assert findings[0].category is Category.COOLDOWN
    assert findings[0].evidence["days_ago"] == 2


def test_cooldown_boundary_at_exactly_7_days_does_not_fire():
    items = [item("boundary", publish_date=days_ago(7))]
    assert cooldown_findings(items, cooldown_days=7) == []


def test_change_findings_emits_new_and_removed_with_info_severity():
    changes = [
        Change(kind="added", previous=None, current=item("a", surface="plugin")),
        Change(kind="removed", previous=item("b", surface="plugin"), current=None),
    ]
    findings = change_findings(changes)
    by_category = {f.category: f for f in findings}
    assert Category.NEW_ITEM in by_category
    assert Category.REMOVED_ITEM in by_category
    assert by_category[Category.NEW_ITEM].severity is Severity.INFO
    assert by_category[Category.NEW_ITEM].surface is Surface.PLUGIN


from signals import capability_diff_findings, url_mismatch_findings, maintainer_change_findings


def test_capability_diff_fires_high_when_capabilities_added():
    changes = [Change(
        kind="changed",
        previous=item("x", surface="mcp"),
        current=item("x", surface="mcp"),
        added_capabilities=["exec"],
        removed_capabilities=[],
    )]
    findings = capability_diff_findings(changes)
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH
    assert findings[0].category is Category.CAPABILITY_DIFF
    assert findings[0].evidence["added"] == ["exec"]


def test_capability_diff_silent_when_only_capabilities_removed():
    """Capability removal isn't a hijack signal; we don't fire on it."""
    changes = [Change(
        kind="changed",
        previous=item("x"), current=item("x"),
        added_capabilities=[], removed_capabilities=["something"],
    )]
    assert capability_diff_findings(changes) == []


def test_url_mismatch_fires_high_when_registry_url_differs_from_manifest():
    items = [item("x", surface="mcp")]
    items[0] = Item(
        surface="mcp", name="x", source="npm:x", version="1.0",
        publish_date=None, publisher=None, capabilities=[],
        source_url="https://github.com/claimed/repo",
        content_hash=None,
    )
    registry_urls = {("mcp", "x"): "https://github.com/actual/different"}
    findings = url_mismatch_findings(items, registry_urls)
    assert len(findings) == 1
    assert findings[0].category is Category.URL_MISMATCH
    assert findings[0].severity is Severity.HIGH


def test_url_mismatch_silent_when_urls_match():
    items = [Item(
        surface="mcp", name="x", source="npm:x", version="1.0",
        publish_date=None, publisher=None, capabilities=[],
        source_url="https://github.com/x/x", content_hash=None,
    )]
    assert url_mismatch_findings(items, {("mcp", "x"): "https://github.com/x/x"}) == []


def test_maintainer_change_fires_high_when_publisher_differs():
    prev_items = [Item(
        surface="mcp", name="x", source="npm:x", version="1.0",
        publish_date=None, publisher="alice", capabilities=[],
        source_url=None, content_hash=None,
    )]
    curr_items = [Item(
        surface="mcp", name="x", source="npm:x", version="1.1",
        publish_date=None, publisher="mallory", capabilities=[],
        source_url=None, content_hash=None,
    )]
    findings = maintainer_change_findings(prev_items, curr_items)
    assert len(findings) == 1
    assert findings[0].category is Category.MAINTAINER_CHANGE
    assert findings[0].evidence["previous_publisher"] == "alice"
    assert findings[0].evidence["current_publisher"] == "mallory"


def test_maintainer_change_silent_when_publisher_unknown_in_either_snapshot():
    prev = [Item(surface="mcp", name="x", source="npm:x", version="1",
                 publish_date=None, publisher=None, capabilities=[],
                 source_url=None, content_hash=None)]
    curr = [Item(surface="mcp", name="x", source="npm:x", version="2",
                 publish_date=None, publisher="someone", capabilities=[],
                 source_url=None, content_hash=None)]
    assert maintainer_change_findings(prev, curr) == []


from signals import repo_health_findings
from registry import GithubRepoMetadata


def test_repo_health_fires_info_for_archived_repo():
    items = [Item(
        surface="plugin", name="x", source="git:https://github.com/a/b",
        version="1.0", publish_date=None, publisher=None, capabilities=[],
        source_url="https://github.com/a/b", content_hash=None,
    )]
    repo_meta = {("plugin", "x"): GithubRepoMetadata(
        full_name="a/b", last_push_date="2026-05-20", archived=True,
    )}
    findings = repo_health_findings(items, repo_meta)
    assert len(findings) == 1
    assert findings[0].severity is Severity.INFO
    assert findings[0].category is Category.REPO_HEALTH
    assert "archived" in findings[0].signal.lower()


def test_repo_health_silent_for_healthy_repo():
    items = [Item(
        surface="plugin", name="x", source="git:https://github.com/a/b",
        version="1.0", publish_date=None, publisher=None, capabilities=[],
        source_url="https://github.com/a/b", content_hash=None,
    )]
    repo_meta = {("plugin", "x"): GithubRepoMetadata(
        full_name="a/b", last_push_date=days_ago(10), archived=False,
    )}
    assert repo_health_findings(items, repo_meta) == []
