"""Tests for validate_plugin.py — business logic per check group."""
import json

import validate_plugin as vp


def make_plugin(tmp_path, *, name="demo-plugin", version="0.1.0", description="A demo.",
                skills=("demo-skill",), manifest_extra=None, marketplace=None, readme=True):
    """Build a minimal valid plugin tree; kwargs poke holes in it."""
    root = tmp_path / "plug"
    (root / ".claude-plugin").mkdir(parents=True)
    manifest = {"name": name, "version": version, "description": description,
                "author": {"name": "oiler"}}
    manifest.update(manifest_extra or {})
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    if marketplace is not None:
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(marketplace), encoding="utf-8")
    for s in skills:
        d = root / "skills" / s
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {s}\ndescription: Demo skill for testing. Use when testing.\n---\n\n# {s}\n\nBody.\n",
            encoding="utf-8")
    if readme:
        (root / "README.md").write_text("# demo\n", encoding="utf-8")
    return root


def fails(report, check):
    return [f for f in report.failures if f.check == check]


# --- Task 1: manifest (item 2) ---

def test_valid_manifest_no_failures(tmp_path):
    root = make_plugin(tmp_path)
    report = vp.Report()
    manifest = vp.check_manifest(root, report)
    assert report.failures == []
    assert manifest["name"] == "demo-plugin"


def test_manifest_missing(tmp_path):
    root = make_plugin(tmp_path)
    (root / ".claude-plugin" / "plugin.json").unlink()
    report = vp.Report()
    assert vp.check_manifest(root, report) is None
    assert fails(report, "manifest-missing")


def test_manifest_at_plugin_root_is_flagged(tmp_path):
    root = make_plugin(tmp_path)
    (root / "plugin.json").write_text("{}", encoding="utf-8")
    report = vp.Report()
    vp.check_manifest(root, report)
    assert fails(report, "manifest-at-root")


def test_manifest_unparseable(tmp_path):
    root = make_plugin(tmp_path)
    (root / ".claude-plugin" / "plugin.json").write_text("{not json", encoding="utf-8")
    report = vp.Report()
    assert vp.check_manifest(root, report) is None
    assert fails(report, "manifest-parse")


def test_manifest_missing_required_fields(tmp_path):
    root = make_plugin(tmp_path)
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "demo-plugin"}), encoding="utf-8")
    report = vp.Report()
    vp.check_manifest(root, report)
    missing = {f.check for f in report.failures}
    assert {"manifest-field-version", "manifest-field-description", "manifest-field-author"} <= missing


def test_manifest_name_not_kebab(tmp_path):
    root = make_plugin(tmp_path, name="Demo_Plugin")
    report = vp.Report()
    vp.check_manifest(root, report)
    assert fails(report, "manifest-name-kebab")


def test_manifest_version_not_semver(tmp_path):
    root = make_plugin(tmp_path, version="1.0")
    report = vp.Report()
    vp.check_manifest(root, report)
    assert fails(report, "manifest-version-semver")


def test_claude_plugin_dir_holds_only_manifests(tmp_path):
    root = make_plugin(tmp_path)
    (root / ".claude-plugin" / "skills").mkdir()
    (root / ".claude-plugin" / "notes.txt").write_text("x", encoding="utf-8")
    report = vp.Report()
    vp.check_claude_plugin_contents(root, report)
    assert fails(report, "claude-plugin-extras")


def test_claude_plugin_dir_clean_no_failures(tmp_path):
    root = make_plugin(tmp_path)
    report = vp.Report()
    vp.check_claude_plugin_contents(root, report)
    assert report.failures == []


def test_frontmatter_parses():
    fm, err = vp.parse_frontmatter("---\nname: x\ndescription: y\n---\n\nBody\n")
    assert err is None
    assert fm == {"name": "x", "description": "y"}


def test_frontmatter_unclosed_fence():
    fm, err = vp.parse_frontmatter("---\nname: x\n")
    assert fm is None and "fence" in err
