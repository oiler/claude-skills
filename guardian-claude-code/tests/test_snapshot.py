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
