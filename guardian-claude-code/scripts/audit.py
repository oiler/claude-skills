#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27",
#     "packaging>=24.0",
# ]
# ///
"""guardian-claude-code: audit Claude Code's third-party trust surface."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audit.py", description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("quick", help="Fast diff vs last snapshot, no network.")
    sub.add_parser("deep", help="Full audit with registry/GitHub API calls.")
    args = parser.parse_args(argv)

    if args.mode == "quick":
        return run_quick()
    if args.mode == "deep":
        return run_deep()
    return 2


def run_quick() -> int:
    print(json.dumps({"mode": "quick", "findings": []}))
    return 0


def run_deep() -> int:
    print(json.dumps({"mode": "deep", "findings": []}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
