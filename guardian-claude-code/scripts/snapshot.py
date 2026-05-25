"""Snapshot of the third-party trust surface, with IO and diff."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Item:
    """One enumerated entity. Used for all surfaces; not all fields apply to all."""
    surface: str            # "mcp" | "plugin" | "skill" | "hook"
    name: str               # display key, unique within surface
    source: str             # e.g. "npm:foo", "pip:bar", "git:https://...", "local"
    version: str | None     # registry version, git ref, or skill mtime ISO
    publish_date: str | None  # ISO date when applicable
    publisher: str | None     # registry account name when applicable
    capabilities: list[str] = field(default_factory=list)  # declared tools/hooks
    source_url: str | None = None  # README/manifest claimed repo URL
    content_hash: str | None = None  # for skills/hooks: hash of content


@dataclass(frozen=True)
class Snapshot:
    items: list[Item] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


def save_snapshot(snap: Snapshot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": snap.schema_version,
        "items": [asdict(i) for i in snap.items],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def load_snapshot(path: Path) -> Snapshot:
    if not path.exists():
        return Snapshot()
    data = json.loads(path.read_text())
    version = data.get("schema_version", 0)
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"incompatible snapshot schema: file={version} expected={SCHEMA_VERSION}. "
            f"Delete {path} and re-baseline with `audit.py deep`."
        )
    items = [Item(**i) for i in data.get("items", [])]
    return Snapshot(items=items, schema_version=version)


@dataclass(frozen=True)
class Change:
    kind: str                       # "added" | "removed" | "changed"
    previous: Item | None
    current: Item | None
    added_capabilities: list[str] = field(default_factory=list)
    removed_capabilities: list[str] = field(default_factory=list)


def _key(i: Item) -> tuple[str, str]:
    return (i.surface, i.name)


def diff_snapshots(prev: Snapshot, curr: Snapshot) -> list[Change]:
    prev_by_key = {_key(i): i for i in prev.items}
    curr_by_key = {_key(i): i for i in curr.items}

    changes: list[Change] = []

    for key, item in curr_by_key.items():
        if key not in prev_by_key:
            changes.append(Change(kind="added", previous=None, current=item))

    for key, item in prev_by_key.items():
        if key not in curr_by_key:
            changes.append(Change(kind="removed", previous=item, current=None))

    for key, curr_item in curr_by_key.items():
        if key not in prev_by_key:
            continue
        prev_item = prev_by_key[key]
        if prev_item == curr_item:
            continue
        prev_caps = set(prev_item.capabilities)
        curr_caps = set(curr_item.capabilities)
        changes.append(Change(
            kind="changed",
            previous=prev_item,
            current=curr_item,
            added_capabilities=sorted(curr_caps - prev_caps),
            removed_capabilities=sorted(prev_caps - curr_caps),
        ))

    return changes
