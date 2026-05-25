"""Registry / GitHub API client with on-disk cache."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx

log = logging.getLogger(__name__)

_SSH_FORM = re.compile(r"^ssh://git@(?P<host>[^/]+)/(?P<path>.+)$")
_SCP_FORM = re.compile(r"^git@(?P<host>[^:]+):(?P<path>.+)$")


def canonicalize_repo_url(url: str | None) -> str | None:
    """Canonicalize a git repository URL to https://host/owner/repo form.

    Handles the common alternatives so equality comparison is meaningful:
    - ssh://git@host/path.git -> https://host/path
    - git@host:path.git       -> https://host/path
    - git+https://host/path   -> https://host/path
    - trailing /              -> stripped
    - trailing .git           -> stripped
    """
    if not url:
        return url
    s = url.removeprefix("git+")

    if m := _SSH_FORM.match(s):
        s = f"https://{m['host']}/{m['path']}"
    elif m := _SCP_FORM.match(s):
        s = f"https://{m['host']}/{m['path']}"

    s = s.removesuffix(".git").rstrip("/")
    return s


@dataclass(frozen=True)
class NpmMetadata:
    package: str
    version: str
    publish_date: str | None      # ISO date
    publisher: str | None
    repository_url: str | None


@dataclass(frozen=True)
class PyPiMetadata:
    package: str
    version: str
    publish_date: str | None
    publisher: str | None
    repository_url: str | None


@dataclass(frozen=True)
class GithubRepoMetadata:
    full_name: str
    last_push_date: str | None
    archived: bool


class Registry:
    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600):
        self.cache_dir = cache_dir
        self.ttl = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._client = httpx.Client(timeout=10.0, follow_redirects=True)

    # --- cache layer ---
    def _cache_path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{h}.json"

    def _get_cached(self, key: str) -> dict | None:
        p = self._cache_path(key)
        if not p.exists():
            return None
        if time.time() - p.stat().st_mtime > self.ttl:
            return None
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return None

    def _set_cached(self, key: str, value: dict) -> None:
        self._cache_path(key).write_text(json.dumps(value))

    def _fetch_json(self, url: str) -> dict | None:
        cached = self._get_cached(url)
        if cached is not None:
            return cached
        try:
            r = self._client.get(url)
            r.raise_for_status()
            data = r.json()
            self._set_cached(url, data)
            return data
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            log.warning("registry fetch failed for %s: %s", url, e)
            return None

    # --- npm ---
    def npm(self, package: str, version: str) -> NpmMetadata | None:
        url = f"https://registry.npmjs.org/{quote(package, safe='')}"
        data = self._fetch_json(url)
        if data is None:
            return None
        time_map = data.get("time", {})
        publish = time_map.get(version)
        publish_date = publish.split("T")[0] if publish else None

        version_data = data.get("versions", {}).get(version, {})
        publisher = (version_data.get("_npmUser") or {}).get("name")
        repo = (version_data.get("repository") or {}).get("url")
        if repo:
            repo = canonicalize_repo_url(repo)

        return NpmMetadata(
            package=package, version=version,
            publish_date=publish_date, publisher=publisher,
            repository_url=repo,
        )

    # --- pypi ---
    def pypi(self, package: str, version: str) -> PyPiMetadata | None:
        url = f"https://pypi.org/pypi/{package}/{version}/json"
        data = self._fetch_json(url)
        if data is None:
            return None
        info = data.get("info", {})
        urls = data.get("urls", [])
        upload = urls[0]["upload_time"] if urls else None
        publish_date = upload.split("T")[0] if upload else None
        repo = (info.get("project_urls") or {}).get("Source")
        return PyPiMetadata(
            package=package, version=version,
            publish_date=publish_date, publisher=info.get("author"),
            repository_url=repo,
        )

    # --- github ---
    def github_repo(self, repo_url: str) -> GithubRepoMetadata | None:
        parsed = urlparse(repo_url)
        if parsed.netloc != "github.com":
            return None
        owner_repo = parsed.path.strip("/").removesuffix(".git")
        url = f"https://api.github.com/repos/{owner_repo}"
        data = self._fetch_json(url)
        if data is None:
            return None
        pushed = data.get("pushed_at")
        return GithubRepoMetadata(
            full_name=data.get("full_name", owner_repo),
            last_push_date=pushed.split("T")[0] if pushed else None,
            archived=bool(data.get("archived")),
        )
