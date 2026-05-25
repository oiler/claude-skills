from __future__ import annotations

import json
from pathlib import Path

import pytest

from enumerate import enumerate_mcp_servers, parse_mcp_source


def test_parse_npm_source():
    s = parse_mcp_source("npx", ["-y", "@example/mcp-server@1.2.3"])
    assert s.kind == "npm"
    assert s.package == "@example/mcp-server"
    assert s.version == "1.2.3"


def test_parse_pip_source():
    s = parse_mcp_source("uvx", ["example-mcp==0.5.0"])
    assert s.kind == "pip"
    assert s.package == "example-mcp"
    assert s.version == "0.5.0"


def test_parse_local_source_when_no_registry():
    s = parse_mcp_source("node", ["/abs/path/to/server.js"])
    assert s.kind == "local"
    assert s.package == "/abs/path/to/server.js"
    assert s.version is None


def test_enumerate_mcp_servers_from_fixture(fixtures_dir: Path):
    payload = json.loads((fixtures_dir / "mcp_responses" / "sample.json").read_text())
    items = enumerate_mcp_servers(payload)
    names = sorted(i.name for i in items)
    assert names == ["example-git", "example-npm", "example-pip"]

    by_name = {i.name: i for i in items}
    assert by_name["example-npm"].source == "npm:@example/mcp-server"
    assert by_name["example-npm"].version == "1.2.3"
    assert by_name["example-npm"].capabilities == ["list_files", "read_file"]
    assert by_name["example-pip"].source == "pip:example-mcp"
    assert by_name["example-pip"].version == "0.5.0"
    assert by_name["example-git"].source == "local:/abs/path/to/server.js"
    assert by_name["example-git"].version is None


from enumerate import enumerate_plugins


def test_enumerate_plugins_reads_valid_manifest(fixtures_dir: Path):
    items = enumerate_plugins(fixtures_dir / "plugins")
    by_name = {i.name: i for i in items}
    assert "example-plugin" in by_name

    p = by_name["example-plugin"]
    assert p.surface == "plugin"
    assert p.source == "git:https://github.com/example/plugin"
    assert p.version == "1.4.2"
    # capabilities = sorted union of skills, commands, hooks
    assert "skill:foo-skill" in p.capabilities
    assert "skill:bar-skill" in p.capabilities
    assert "command:greet" in p.capabilities
    assert "hook:SessionStart" in p.capabilities
    assert p.source_url == "https://github.com/example/plugin"


def test_enumerate_plugins_skips_broken_manifest(fixtures_dir: Path, caplog):
    items = enumerate_plugins(fixtures_dir / "plugins")
    names = [i.name for i in items]
    assert "broken-plugin" not in names
    assert any("broken-plugin" in r.message for r in caplog.records)
