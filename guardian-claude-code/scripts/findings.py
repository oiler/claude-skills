"""Finding records and enums emitted by guardian-claude-code."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    HIGH = "high"
    WARN = "warn"
    INFO = "info"

    @property
    def rank(self) -> int:
        return {"high": 3, "warn": 2, "info": 1}[self.value]


class Category(Enum):
    COOLDOWN = "cooldown"
    CAPABILITY_DIFF = "capability_diff"
    URL_MISMATCH = "url_mismatch"
    MAINTAINER_CHANGE = "maintainer_change"
    REPO_HEALTH = "repo_health"
    NEW_ITEM = "new_item"
    REMOVED_ITEM = "removed_item"


class Surface(Enum):
    MCP = "mcp"
    PLUGIN = "plugin"
    SKILL = "skill"
    HOOK = "hook"
    CONNECTOR = "connector"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    category: Category
    surface: Surface
    item: str
    signal: str
    evidence: dict[str, Any] = field(default_factory=dict)
    fix_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "surface": self.surface.value,
            "item": self.item,
            "signal": self.signal,
            "evidence": dict(self.evidence),
            "fix_hint": self.fix_hint,
        }
