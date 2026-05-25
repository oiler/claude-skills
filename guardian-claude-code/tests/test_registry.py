from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
import pytest
import respx

from registry import (
    Registry,
    NpmMetadata,
    PyPiMetadata,
    GithubRepoMetadata,
)


@pytest.fixture
def reg(tmp_state_dir: Path) -> Registry:
    return Registry(cache_dir=tmp_state_dir / "cache", ttl_seconds=3600)


def test_npm_metadata_parses_publish_date_and_maintainer(reg: Registry):
    with respx.mock(assert_all_called=True) as router:
        router.get("https://registry.npmjs.org/@example%2Ffoo").respond(json={
            "name": "@example/foo",
            "dist-tags": {"latest": "1.2.3"},
            "time": {"1.2.2": "2026-04-01T00:00:00Z", "1.2.3": "2026-05-22T00:00:00Z"},
            "versions": {
                "1.2.3": {"_npmUser": {"name": "alice"}, "repository": {"url": "git+https://github.com/example/foo.git"}}
            }
        })
        meta = reg.npm("@example/foo", "1.2.3")
        assert meta == NpmMetadata(
            package="@example/foo", version="1.2.3",
            publish_date="2026-05-22", publisher="alice",
            repository_url="https://github.com/example/foo",
        )


def test_npm_metadata_caches_within_ttl(reg: Registry, tmp_state_dir: Path):
    with respx.mock() as router:
        route = router.get("https://registry.npmjs.org/example").respond(json={
            "name": "example", "dist-tags": {"latest": "1.0.0"},
            "time": {"1.0.0": "2026-01-01T00:00:00Z"},
            "versions": {"1.0.0": {"_npmUser": {"name": "x"}}},
        })
        reg.npm("example", "1.0.0")
        reg.npm("example", "1.0.0")
        assert route.call_count == 1  # second call hit cache


def test_pypi_metadata_parses(reg: Registry):
    with respx.mock() as router:
        router.get("https://pypi.org/pypi/example-mcp/0.5.0/json").respond(json={
            "info": {
                "name": "example-mcp", "version": "0.5.0",
                "author": "bob",
                "project_urls": {"Source": "https://github.com/example/example-mcp"},
            },
            "urls": [{"upload_time": "2026-03-15T10:00:00"}],
        })
        meta = reg.pypi("example-mcp", "0.5.0")
        assert meta == PyPiMetadata(
            package="example-mcp", version="0.5.0",
            publish_date="2026-03-15", publisher="bob",
            repository_url="https://github.com/example/example-mcp",
        )


def test_github_repo_metadata_parses(reg: Registry):
    with respx.mock() as router:
        router.get("https://api.github.com/repos/example/foo").respond(json={
            "full_name": "example/foo",
            "archived": False,
            "pushed_at": "2026-05-20T12:00:00Z",
        })
        meta = reg.github_repo("https://github.com/example/foo")
        assert meta.full_name == "example/foo"
        assert meta.last_push_date == "2026-05-20"
        assert meta.archived is False


def test_network_failure_returns_none(reg: Registry):
    with respx.mock() as router:
        router.get("https://registry.npmjs.org/missing").mock(
            side_effect=httpx.ConnectError("nope"),
        )
        assert reg.npm("missing", "1.0.0") is None
