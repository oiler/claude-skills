"""Enumerate the third-party trust surface.

Each enumerate_* function returns a list[Item] for one surface.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from snapshot import Item


@dataclass(frozen=True)
class McpSource:
    kind: str           # "npm" | "pip" | "git" | "local"
    package: str        # registry name, git URL, or local path
    version: str | None


_NPM_SPEC = re.compile(r"^(?P<pkg>(?:@[^/]+/)?[^@]+)(?:@(?P<ver>[^@]+))?$")
_PIP_SPEC = re.compile(r"^(?P<pkg>[A-Za-z0-9_.-]+)(?:==(?P<ver>[^=]+))?$")


def parse_mcp_source(command: str, args: list[str]) -> McpSource:
    """Infer source kind/package/version from how an MCP server is launched."""
    # npm: npx [-y] @scope/pkg@version
    if command in {"npx", "bunx"}:
        for arg in args:
            if arg.startswith("-"):
                continue
            m = _NPM_SPEC.match(arg)
            if m:
                return McpSource(kind="npm", package=m["pkg"], version=m["ver"])

    # pip: uvx pkg==version  or  python -m pkg (skip, no version)
    if command in {"uvx", "pipx"}:
        for arg in args:
            if arg.startswith("-"):
                continue
            m = _PIP_SPEC.match(arg)
            if m:
                return McpSource(kind="pip", package=m["pkg"], version=m["ver"])

    # Local path
    if args and args[0].startswith("/"):
        return McpSource(kind="local", package=args[0], version=None)

    return McpSource(kind="local", package=f"{command} {' '.join(args)}".strip(),
                     version=None)


def enumerate_mcp_servers(payload: dict[str, Any]) -> list[Item]:
    items: list[Item] = []
    for entry in payload.get("servers", []):
        src = parse_mcp_source(entry.get("command", ""), entry.get("args", []))
        items.append(Item(
            surface="mcp",
            name=entry["name"],
            source=f"{src.kind}:{src.package}",
            version=src.version,
            publish_date=None,        # filled by signals.py via registry lookup
            publisher=None,
            capabilities=sorted(entry.get("tools", [])),
            source_url=None,
            content_hash=None,
        ))
    return items
