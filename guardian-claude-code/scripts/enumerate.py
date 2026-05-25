"""Enumerate the third-party trust surface.

Each enumerate_* function returns a list[Item] for one surface.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from snapshot import Item

log = logging.getLogger(__name__)


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


def enumerate_plugins(plugins_root: Path) -> list[Item]:
    """Walk plugin caches under plugins_root looking for plugin.json files."""
    items: list[Item] = []
    if not plugins_root.exists():
        return items

    for manifest in plugins_root.rglob("plugin.json"):
        try:
            data = json.loads(manifest.read_text())
        except (json.JSONDecodeError, OSError) as e:
            log.warning("skipping plugin at %s: %s", manifest.parent, e)
            continue

        name = data.get("name") or manifest.parent.name
        version = data.get("version")
        repo = data.get("repository")
        source = f"git:{repo}" if repo else f"local:{manifest.parent}"

        capabilities: list[str] = []
        capabilities += [f"skill:{s}" for s in data.get("skills", [])]
        capabilities += [f"command:{c}" for c in data.get("commands", [])]
        for srv in data.get("mcpServers", []):
            srv_name = srv if isinstance(srv, str) else srv.get("name", "?")
            capabilities.append(f"mcpServer:{srv_name}")

        # Hooks ship as a sibling hooks.json
        hooks_file = manifest.parent / "hooks.json"
        if hooks_file.exists():
            try:
                hooks_data = json.loads(hooks_file.read_text())
                capabilities += [f"hook:{event}" for event in hooks_data.keys()]
            except (json.JSONDecodeError, OSError) as e:
                log.warning("skipping hooks.json at %s: %s", hooks_file, e)

        items.append(Item(
            surface="plugin",
            name=name,
            source=source,
            version=version,
            publish_date=None,
            publisher=None,
            capabilities=sorted(capabilities),
            source_url=repo,
            content_hash=None,
        ))

    return items
