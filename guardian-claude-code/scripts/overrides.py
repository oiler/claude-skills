"""Trust-override evaluation. Overrides apply only to noisy categories."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

from findings import Category, Finding

# Categories that overrides can silence. The rest are high-signal and only
# silenceable via force_silence_all.
SILENCEABLE_CATEGORIES = {
    Category.COOLDOWN,
    Category.REPO_HEALTH,
    Category.NEW_ITEM,
    Category.REMOVED_ITEM,
}


def today() -> str:
    """Return today as ISO date. Module-level for test monkeypatching."""
    return date.today().isoformat()


@dataclass(frozen=True)
class Override:
    surface: str
    item: str
    rules: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    added: str = ""

    def __post_init__(self) -> None:
        if self.rules.get("force_silence_all") and not self.reason:
            raise ValueError("force_silence_all requires reason")


def load_overrides(path: Path) -> list[Override]:
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [Override(**o) for o in data.get("overrides", [])]


def save_overrides(overrides: list[Override], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"overrides": [asdict(o) for o in overrides]}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def _matches(override: Override, finding: Finding) -> bool:
    return override.surface == finding.surface.value and override.item == finding.item


def _silenced_by(override: Override, finding: Finding) -> bool:
    rules = override.rules

    if rules.get("force_silence_all"):
        return True

    if finding.category not in SILENCEABLE_CATEGORIES:
        return False

    if finding.category is Category.COOLDOWN and rules.get("cooldown_exempt"):
        return True

    if (until_v := rules.get("silence_until_version")) is not None:
        current = finding.evidence.get("current_version")
        if current is not None:
            try:
                if Version(str(current)) < Version(str(until_v)):
                    return True
            except InvalidVersion:
                pass  # fall through; can't compare

    if (until_d := rules.get("silence_until_date")) is not None:
        if today() < until_d:
            return True

    return False


def apply_overrides(findings: list[Finding], overrides: list[Override]) -> list[Finding]:
    """Return findings not silenced by any override."""
    out = []
    for f in findings:
        silenced = any(_silenced_by(o, f) for o in overrides if _matches(o, f))
        if not silenced:
            out.append(f)
    return out
