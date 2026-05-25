from __future__ import annotations

from pathlib import Path

import pytest

from snapshot import Snapshot, Item, load_snapshot, save_snapshot, SCHEMA_VERSION


def make_item(name: str = "foo", **kw) -> Item:
    defaults = dict(
        surface="mcp",
        name=name,
        source="npm:example",
        version="1.0.0",
        publish_date=None,
        publisher=None,
        capabilities=["read"],
        source_url=None,
        content_hash=None,
    )
    defaults.update(kw)
    return Item(**defaults)


def test_save_and_load_roundtrip(tmp_state_dir: Path):
    snap = Snapshot(items=[make_item("a"), make_item("b", version="2.0")])
    path = tmp_state_dir / "snapshot.json"
    save_snapshot(snap, path)
    back = load_snapshot(path)
    assert back == snap
    assert back.schema_version == SCHEMA_VERSION


def test_load_missing_file_returns_empty(tmp_state_dir: Path):
    snap = load_snapshot(tmp_state_dir / "does-not-exist.json")
    assert snap.items == []
    assert snap.schema_version == SCHEMA_VERSION


def test_load_incompatible_schema_raises(tmp_state_dir: Path):
    path = tmp_state_dir / "snapshot.json"
    path.write_text('{"schema_version": 999, "items": []}')
    with pytest.raises(ValueError, match="incompatible snapshot schema"):
        load_snapshot(path)


from snapshot import diff_snapshots, Change


def test_diff_detects_added_removed_changed():
    prev = Snapshot(items=[
        make_item("kept", version="1.0"),
        make_item("removed", version="1.0"),
        make_item("changed", version="1.0"),
    ])
    curr = Snapshot(items=[
        make_item("kept", version="1.0"),
        make_item("changed", version="2.0"),  # version bumped
        make_item("added", version="1.0"),
    ])
    changes = diff_snapshots(prev, curr)
    added = [c for c in changes if c.kind == "added"]
    removed = [c for c in changes if c.kind == "removed"]
    changed = [c for c in changes if c.kind == "changed"]
    assert {c.current.name for c in added} == {"added"}
    assert {c.previous.name for c in removed} == {"removed"}
    assert {c.current.name for c in changed} == {"changed"}


def test_diff_identifies_capability_expansion():
    prev = Snapshot(items=[make_item("x", capabilities=["read"])])
    curr = Snapshot(items=[make_item("x", capabilities=["read", "exec"])])
    changes = diff_snapshots(prev, curr)
    assert len(changes) == 1
    c = changes[0]
    assert c.kind == "changed"
    assert c.added_capabilities == ["exec"]
    assert c.removed_capabilities == []


def test_diff_keys_by_surface_plus_name():
    """An MCP and a plugin with the same name are different items."""
    prev = Snapshot(items=[make_item("foo", surface="mcp")])
    curr = Snapshot(items=[make_item("foo", surface="plugin")])
    changes = diff_snapshots(prev, curr)
    kinds = sorted(c.kind for c in changes)
    assert kinds == ["added", "removed"]
