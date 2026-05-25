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
