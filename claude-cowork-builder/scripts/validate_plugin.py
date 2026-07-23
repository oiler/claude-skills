# validate_plugin.py — Cowork plugin structural validator (claude-cowork-builder)
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""
Deterministic validator for the [script]-tagged items of the claude-cowork-builder
audit checklist (references/audit-checklist.md). The script is the authority for
what it checks; judgment items stay with the model.

Usage:
    uv run validate_plugin.py <plugin-dir> [--json] [--profile NAME]

Exit codes: 0 all script checks pass; 1 one or more failures; 2 usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
BRANDING = ("license", "homepage", "repository", "keywords")
PROFILES = ("private-individual", "self-marketplace", "container-marketplace", "public")
REQUIRED_FIELDS = ("name", "version", "description", "author")
ALLOWED_IN_CLAUDE_PLUGIN = {"plugin.json", "marketplace.json"}


@dataclass
class Finding:
    item: int
    check: str
    status: str  # "pass" | "fail"
    detail: str = ""


@dataclass
class Report:
    profile: str = ""
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def ok(self, item: int, check: str, detail: str = "") -> None:
        self.findings.append(Finding(item, check, "pass", detail))

    def fail(self, item: int, check: str, detail: str) -> None:
        self.findings.append(Finding(item, check, "fail", detail))

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.status == "fail"]


def read_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return None, f"{path.name}: {e}"
    if not isinstance(data, dict):
        return None, f"{path.name}: top level is not a JSON object"
    return data, None


def parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    m = re.match(r"^---\n(.*?)\n---(\n|$)", text, re.DOTALL)
    if not m:
        return None, "missing or unclosed YAML frontmatter fence"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, f"frontmatter does not parse: {e}"
    if not isinstance(data, dict):
        return None, "frontmatter is not a YAML mapping"
    return data, None


def has_exact(d: Path, name: str) -> bool:
    """Case-exact file presence — Path.is_file() lies on case-insensitive filesystems."""
    return d.is_dir() and name in [f.name for f in d.iterdir()]


def skill_dirs(root: Path) -> list[Path]:
    skills = root / "skills"
    if not skills.is_dir():
        return []
    return sorted(p for p in skills.iterdir() if p.is_dir())


def check_manifest(root: Path, report: Report) -> dict | None:
    if has_exact(root, "plugin.json"):
        report.fail(2, "manifest-at-root", "plugin.json found at the plugin root — the manifest lives at .claude-plugin/plugin.json")
    mp = root / ".claude-plugin" / "plugin.json"
    if not has_exact(root / ".claude-plugin", "plugin.json"):
        report.fail(2, "manifest-missing", "no manifest at .claude-plugin/plugin.json")
        return None
    manifest, err = read_json(mp)
    if err:
        report.fail(2, "manifest-parse", err)
        return None
    for fname in REQUIRED_FIELDS:
        if not manifest.get(fname):
            report.fail(2, f"manifest-field-{fname}", f"manifest missing required field {fname!r}")
    name = manifest.get("name", "")
    if name and not KEBAB.match(name):
        report.fail(2, "manifest-name-kebab", f"name {name!r} is not kebab-case")
    version = manifest.get("version", "")
    if version and not SEMVER.match(str(version)):
        report.fail(2, "manifest-version-semver", f"version {version!r} is not MAJOR.MINOR.PATCH")
    return manifest


def check_claude_plugin_contents(root: Path, report: Report) -> None:
    cp = root / ".claude-plugin"
    if not cp.is_dir():
        return  # manifest-missing already reported
    extras = sorted(p.name for p in cp.iterdir() if p.name not in ALLOWED_IN_CLAUDE_PLUGIN)
    if extras:
        report.fail(2, "claude-plugin-extras", f".claude-plugin/ holds only the manifests; found: {', '.join(extras)}")


TILDE_TOKEN = re.compile(r"~~[a-z0-9-]+")


def infer_profile(root: Path, manifest: dict | None) -> tuple[str, str]:
    """Infer the distribution profile from repo shape. Returns (profile, evidence)."""
    branding = manifest is not None and all(manifest.get(k) for k in BRANDING)
    if (root / ".claude-plugin" / "marketplace.json").is_file():
        base, evidence = "self-marketplace", "marketplace.json beside plugin.json"
    elif (root.parent / ".claude-plugin" / "marketplace.json").is_file():
        base, evidence = "container-marketplace", "parent repo carries .claude-plugin/marketplace.json"
    else:
        base, evidence = "private-individual", "no marketplace.json in plugin or parent"
    if branding:
        return "public", f"{evidence}; full branding metadata present"
    return base, evidence


def _skill_bodies(root: Path) -> str:
    parts = []
    for d in skill_dirs(root):
        if has_exact(d, "SKILL.md"):
            parts.append((d / "SKILL.md").read_text(encoding="utf-8"))
    return "\n".join(parts)


def check_distribution(root: Path, manifest: dict | None, profile: str,
                       override: str | None, report: Report) -> None:
    if override and override != profile:
        report.fail(10, "profile-override", f"--profile {override} but the repo shape infers {profile} — reshape the repo or drop the override")
    name = (manifest or {}).get("name", "")
    if manifest is not None:
        present = [k for k in BRANDING if manifest.get(k)]
        if present and len(present) < len(BRANDING):
            report.fail(10, "branding-partial", f"partial branding metadata ({', '.join(present)}) — ship all of {', '.join(BRANDING)} or none")
    if not has_exact(root, "README.md"):
        report.fail(10, "readme", "README.md missing at the plugin root")
    tokens = sorted(set(TILDE_TOKEN.findall(_skill_bodies(root))))
    if profile == "public":
        for fname in ("CHANGELOG.md", "CONNECTORS.md"):
            if not has_exact(root, fname):
                report.fail(10, f"public-{fname.lower()}", f"{fname} required at the plugin root for a public plugin")
        if not tokens:
            report.fail(10, "genericize", "public profile but no ~~category placeholders in skill bodies — going public is the trigger to genericize")
    elif tokens:
        report.fail(10, "coupling", f"~~ tokens in skill bodies ({', '.join(tokens)}) but profile {profile} is private — private plugins use concrete tool names")
    if profile in ("self-marketplace", "public") and (root / ".claude-plugin" / "marketplace.json").is_file():
        mkt, err = read_json(root / ".claude-plugin" / "marketplace.json")
        if err:
            report.fail(10, "marketplace-parse", err)
        else:
            if not mkt.get("owner"):
                report.fail(10, "marketplace-owner", "marketplace.json missing owner")
            entries = [e for e in (mkt.get("plugins") or []) if isinstance(e, dict)]
            selfed = [e for e in entries if e.get("source") == "./"]
            if not selfed:
                report.fail(10, "marketplace-source", 'self-marketplace requires a plugins entry with source "./"')
            elif name and selfed[0].get("name") != name:
                report.fail(10, "marketplace-name", f"marketplace entry name {selfed[0].get('name')!r} != manifest name {name!r}")
    if (root.parent / ".claude-plugin" / "marketplace.json").is_file():
        mkt, err = read_json(root.parent / ".claude-plugin" / "marketplace.json")
        if err:
            report.fail(10, "container-parse", err)
        else:
            srcs = {str(e.get("source", "")).rstrip("/") for e in (mkt.get("plugins") or []) if isinstance(e, dict)}
            if f"./{root.name}" not in srcs:
                report.fail(10, "container-listing", f"container marketplace.json does not list ./{root.name}")


def check_skills_layer(root: Path, report: Report) -> None:
    dirs = skill_dirs(root)
    if not dirs:
        report.fail(1, "skills-missing", "no skills/ directory with skill subdirectories — skills are the primary layer of a Cowork plugin")
        return
    for d in dirs:
        if not KEBAB.match(d.name):
            report.fail(1, "skill-dir-kebab", f"{d.name}: skill directory name is not kebab-case")
        if not has_exact(d, "SKILL.md"):
            names = [f.name for f in d.iterdir() if f.is_file()]
            near = [n for n in names if n.lower() == "skill.md" or n.lower().endswith("-skill.md")]
            hint = f"found {near[0]!r} — the filename must be exactly SKILL.md" if near else "no SKILL.md present"
            report.fail(1, "skill-filename", f"{d.name}: {hint} (wrong filename fails silently at runtime)")
            continue
        fm, err = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
        if err:
            report.fail(3, "frontmatter", f"{d.name}: {err}")
            continue
        fm_name = fm.get("name")
        if fm_name is not None and fm_name != d.name:
            report.fail(1, "skill-name-match", f"{d.name}: frontmatter name {fm_name!r} != folder name")
        desc = str(fm.get("description") or "").strip()
        if not desc:
            report.fail(3, "description-empty", f"{d.name}: description missing or empty")
        elif TILDE_TOKEN.search(desc):
            report.fail(6, "description-token", f"{d.name}: raw ~~ token in description frontmatter — descriptions use plain category language")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("plugin_dir")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--profile", choices=PROFILES)
    args = ap.parse_args(argv)
    root = Path(args.plugin_dir).resolve()
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 2
    report = Report()
    check_manifest(root, report)
    check_claude_plugin_contents(root, report)
    for f in report.failures:
        print(f"FAIL item {f.item:>2} [{f.check}] {f.detail}")
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main())
