"""Signal-detection functions. Each takes records and returns list[Finding]."""
from __future__ import annotations

from datetime import date

from findings import Category, Finding, Severity, Surface
from snapshot import Change, Item


def _days_between(iso_date: str) -> int | None:
    try:
        return (date.today() - date.fromisoformat(iso_date)).days
    except ValueError:
        return None


def cooldown_findings(items: list[Item], cooldown_days: int = 7) -> list[Finding]:
    out = []
    for i in items:
        if not i.publish_date:
            continue
        days = _days_between(i.publish_date)
        if days is None or days >= cooldown_days:
            continue
        out.append(Finding(
            severity=Severity.WARN,
            category=Category.COOLDOWN,
            surface=Surface(i.surface),
            item=i.name,
            signal=f"Published {days} day(s) ago — within {cooldown_days}-day cooldown.",
            evidence={
                "current_version": i.version,
                "publish_date": i.publish_date,
                "days_ago": days,
            },
            fix_hint="Wait until publish date is older than cooldown, or pin to prior version.",
        ))
    return out


def change_findings(changes: list[Change]) -> list[Finding]:
    out = []
    for c in changes:
        if c.kind == "added" and c.current is not None:
            out.append(Finding(
                severity=Severity.INFO,
                category=Category.NEW_ITEM,
                surface=Surface(c.current.surface),
                item=c.current.name,
                signal="New item appeared since last snapshot.",
                evidence={"source": c.current.source, "version": c.current.version},
                fix_hint="Confirm you added this intentionally.",
            ))
        elif c.kind == "removed" and c.previous is not None:
            out.append(Finding(
                severity=Severity.INFO,
                category=Category.REMOVED_ITEM,
                surface=Surface(c.previous.surface),
                item=c.previous.name,
                signal="Item present in last snapshot is gone.",
                evidence={"source": c.previous.source, "version": c.previous.version},
                fix_hint="If unintentional, restore from VCS.",
            ))
    return out


def capability_diff_findings(changes: list[Change]) -> list[Finding]:
    out = []
    for c in changes:
        if c.kind != "changed" or not c.added_capabilities or c.current is None:
            continue
        out.append(Finding(
            severity=Severity.HIGH,
            category=Category.CAPABILITY_DIFF,
            surface=Surface(c.current.surface),
            item=c.current.name,
            signal=(
                f"Update declares new capabilities: "
                f"{', '.join(c.added_capabilities)}. Classic hijack tell."
            ),
            evidence={
                "added": list(c.added_capabilities),
                "previous_version": c.previous.version if c.previous else None,
                "current_version": c.current.version,
            },
            fix_hint="Inspect the changelog; revert if capability expansion is unexpected.",
        ))
    return out


def url_mismatch_findings(
    items: list[Item],
    registry_urls: dict[tuple[str, str], str | None],
) -> list[Finding]:
    out = []
    for i in items:
        key = (i.surface, i.name)
        registry_url = registry_urls.get(key)
        if not i.source_url or not registry_url:
            continue
        if i.source_url.rstrip("/") == registry_url.rstrip("/"):
            continue
        out.append(Finding(
            severity=Severity.HIGH,
            category=Category.URL_MISMATCH,
            surface=Surface(i.surface),
            item=i.name,
            signal="Manifest source URL doesn't match registry repository URL.",
            evidence={
                "manifest_url": i.source_url,
                "registry_url": registry_url,
            },
            fix_hint="Verify the package's true origin before trusting further updates.",
        ))
    return out


def maintainer_change_findings(
    prev_items: list[Item], curr_items: list[Item],
) -> list[Finding]:
    prev_by_key = {(i.surface, i.name): i for i in prev_items}
    out = []
    for curr in curr_items:
        key = (curr.surface, curr.name)
        prev = prev_by_key.get(key)
        if prev is None or not prev.publisher or not curr.publisher:
            continue
        if prev.publisher == curr.publisher:
            continue
        out.append(Finding(
            severity=Severity.HIGH,
            category=Category.MAINTAINER_CHANGE,
            surface=Surface(curr.surface),
            item=curr.name,
            signal=(
                f"Publisher changed: {prev.publisher} → {curr.publisher}. "
                f"'I sold my package' attack vector."
            ),
            evidence={
                "previous_publisher": prev.publisher,
                "current_publisher": curr.publisher,
                "previous_version": prev.version,
                "current_version": curr.version,
            },
            fix_hint="Confirm legitimate ownership transfer before trusting future updates.",
        ))
    return out
