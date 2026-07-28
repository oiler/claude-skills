# autonom.py — deterministic spine for the autonom skill
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Owns every deterministic surface of an autonom run: artifact paths, the run
ledger, artifact validation, and the Fable dispatch prompts.

The model authors prose. This script owns structure. In particular the `prompt`
subcommand exists so the orchestrator dispatches reviewer text it cannot edit —
priming a reviewer with the authoring session's context turns a fresh critique
into an echo of the author.

Usage:
    uv run autonom.py init <topic> [--root DIR] [--date YYYY-MM-DD]
    uv run autonom.py ledger <step> <status> [--slug SLUG] [--commit SHA]
    uv run autonom.py status [<slug>] [--root DIR]
    uv run autonom.py prompt {spec|plan} <slug> [--root DIR]
    uv run autonom.py validate {spec|plan} <path>

Exit codes: 0 success / all checks pass; 1 validation failures; 2 usage or IO error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

SLUG_MAX = 60

# Step 6 authors the spec, 7 reviews it, 8 authors the plan, 9 reviews it.
STEPS: dict[int, str] = {
    6: "author spec",
    7: "review spec",
    8: "author plan",
    9: "review plan",
}


def slugify(topic: str) -> str:
    """Lowercase ASCII slug. Raises ValueError if nothing survives."""
    ascii_only = (
        unicodedata.normalize("NFKD", topic)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = "-".join(re.findall(r"[a-z0-9]+", ascii_only.lower()))[:SLUG_MAX].strip("-")
    if not slug:
        raise ValueError(f"topic {topic!r} produced an empty slug")
    return slug


def find_repo_root(start: Path) -> Path | None:
    """Git toplevel of `start`, or None when `start` is not inside a repo."""
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def compute_paths(root: Path, slug: str, date: str) -> dict[str, str]:
    run_dir = root / ".superpowers" / "autonom" / slug
    return {
        "slug": slug,
        "date": date,
        "root": str(root),
        "spec": str(root / "docs/superpowers/specs" / f"{date}-{slug}-design.md"),
        "plan": str(root / "docs/superpowers/plans" / f"{date}-{slug}.md"),
        "run_dir": str(run_dir),
        "ledger": str(run_dir / "progress.md"),
        "escalations": str(run_dir / "escalations.md"),
    }


def ensure_gitignored(root: Path) -> None:
    """Keep the run directory out of git. It is scratch, not history."""
    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if any(line.strip() == ".superpowers/" for line in existing.splitlines()):
        return
    prefix = "" if existing.endswith("\n") or not existing else "\n"
    with gitignore.open("a", encoding="utf-8") as handle:
        handle.write(f"{prefix}.superpowers/\n")


def superpowers_present(cache: Path | None = None) -> bool:
    """True when the superpowers plugin is installed and reachable."""
    base = cache or (Path.home() / ".claude" / "plugins" / "cache")
    if not base.exists():
        return False
    hits = base.glob("*/superpowers/*/skills/subagent-driven-development/SKILL.md")
    return next(hits, None) is not None


def _header(topic: str, slug: str, date: str) -> str:
    return f"# autonom run — topic: {topic} — slug: {slug} — date: {date}"


def _parse_header(ledger: Path) -> dict[str, str] | None:
    """Read topic/slug/date back out of a ledger's first line, or None if
    the header is unreadable."""
    first = ledger.read_text(encoding="utf-8").splitlines()[0]
    match = re.match(
        r"# autonom run — topic: (?P<topic>.*) — slug: (?P<slug>[a-z0-9-]+) "
        r"— date: (?P<date>\d{4}-\d{2}-\d{2})$",
        first,
    )
    if not match:
        return None
    return match.groupdict()


def cmd_init(args: argparse.Namespace) -> int:
    cache = Path(args.plugin_cache) if args.plugin_cache else None
    if not superpowers_present(cache):
        print(
            "autonom: the superpowers plugin (v6.2.0+) is not installed. autonom "
            "drives superpowers:brainstorming, writing-plans, using-git-worktrees, "
            "and subagent-driven-development and cannot run without it.",
            file=sys.stderr,
        )
        return 2

    root = Path(args.root).resolve() if args.root else find_repo_root(Path.cwd())
    if root is None:
        print(f"autonom: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    date = args.date or _dt.date.today().isoformat()
    slug = slugify(args.topic)
    paths = compute_paths(root, slug, date)
    ledger = Path(paths["ledger"])
    ensure_gitignored(root)

    resumed = False
    if ledger.exists():
        existing = _parse_header(ledger)
        if existing is None:
            print(f"autonom: unreadable ledger header in {ledger}", file=sys.stderr)
            return 2
        if existing["topic"] != args.topic:
            print(
                f"autonom: topic {args.topic!r} collides with the existing run "
                f"{existing['topic']!r} (both slugify to {slug!r}). "
                "Choose a distinct topic or resume the existing run.",
                file=sys.stderr,
            )
            return 2
        resumed = True
        paths = compute_paths(root, slug, existing["date"])
    else:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(_header(args.topic, slug, date) + "\n", encoding="utf-8")

    payload = dict(paths, topic=args.topic, resumed=resumed,
                   next_step=_next_step(ledger))
    print(json.dumps(payload, indent=2))
    return 0


def _next_step(ledger: Path) -> int | None:
    """Lowest pipeline step not recorded complete; None when the run is done."""
    done = set()
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines()[1:]:
            match = re.match(r"step (\d+) complete", line.strip())
            if match:
                done.add(int(match.group(1)))
    remaining = [step for step in sorted(STEPS) if step not in done]
    return remaining[0] if remaining else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autonom")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="start or resume a run")
    p_init.add_argument("topic")
    p_init.add_argument("--root", help="repo root (default: git toplevel of cwd)")
    p_init.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p_init.add_argument("--plugin-cache",
                        help="plugin cache root (default: ~/.claude/plugins/cache)")
    p_init.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
