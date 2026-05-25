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
