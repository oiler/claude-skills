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


# --- Task 2: profile inference + distribution (item 10) ---

def test_infer_private_individual(tmp_path):
    root = make_plugin(tmp_path)
    profile, _ = vp.infer_profile(root, {"name": "demo-plugin"})
    assert profile == "private-individual"


def test_infer_self_marketplace(tmp_path):
    mkt = {"name": "demo", "owner": {"name": "oiler"},
           "plugins": [{"name": "demo-plugin", "source": "./"}]}
    root = make_plugin(tmp_path, marketplace=mkt)
    profile, _ = vp.infer_profile(root, {"name": "demo-plugin"})
    assert profile == "self-marketplace"


def test_infer_container_marketplace(tmp_path):
    container = tmp_path / "market"
    (container / ".claude-plugin").mkdir(parents=True)
    (container / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
        {"name": "m", "owner": {"name": "oiler"},
         "plugins": [{"name": "demo-plugin", "source": "./plug"}]}), encoding="utf-8")
    root = make_plugin(container)  # make_plugin builds at <base>/plug
    profile, _ = vp.infer_profile(root, {"name": "demo-plugin"})
    assert profile == "container-marketplace"


def test_infer_public_from_full_branding(tmp_path):
    extra = {"license": "MIT", "homepage": "https://x", "repository": "https://x", "keywords": ["a"]}
    root = make_plugin(tmp_path, manifest_extra=extra)
    profile, _ = vp.infer_profile(root, json.loads((root / ".claude-plugin" / "plugin.json").read_text()))
    assert profile == "public"


def test_partial_branding_fails(tmp_path):
    root = make_plugin(tmp_path, manifest_extra={"license": "MIT"})
    manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
    report = vp.Report()
    vp.check_distribution(root, manifest, "private-individual", None, report)
    assert fails(report, "branding-partial")


def test_missing_readme_fails(tmp_path):
    root = make_plugin(tmp_path, readme=False)
    report = vp.Report()
    vp.check_distribution(root, {"name": "demo-plugin"}, "private-individual", None, report)
    assert fails(report, "readme")


def test_self_marketplace_requires_source_dot(tmp_path):
    mkt = {"name": "demo", "owner": {"name": "oiler"},
           "plugins": [{"name": "demo-plugin", "source": "./demo-plugin"}]}
    root = make_plugin(tmp_path, marketplace=mkt)
    report = vp.Report()
    vp.check_distribution(root, {"name": "demo-plugin"}, "self-marketplace", None, report)
    assert fails(report, "marketplace-source")


def test_self_marketplace_name_must_match(tmp_path):
    mkt = {"name": "demo", "owner": {"name": "oiler"},
           "plugins": [{"name": "other", "source": "./"}]}
    root = make_plugin(tmp_path, marketplace=mkt)
    report = vp.Report()
    vp.check_distribution(root, {"name": "demo-plugin"}, "self-marketplace", None, report)
    assert fails(report, "marketplace-name")


def test_public_requires_changelog_connectors_and_tokens(tmp_path):
    extra = {"license": "MIT", "homepage": "https://x", "repository": "https://x", "keywords": ["a"]}
    root = make_plugin(tmp_path, manifest_extra=extra)
    manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
    report = vp.Report()
    vp.check_distribution(root, manifest, "public", None, report)
    checks = {f.check for f in report.failures}
    assert {"public-changelog.md", "public-connectors.md", "genericize"} <= checks


def test_private_with_tilde_tokens_fails_coupling(tmp_path):
    root = make_plugin(tmp_path)
    skill = root / "skills" / "demo-skill" / "SKILL.md"
    skill.write_text(skill.read_text() + "\nUse ~~file-storage when connected.\n", encoding="utf-8")
    report = vp.Report()
    vp.check_distribution(root, {"name": "demo-plugin"}, "private-individual", None, report)
    assert fails(report, "coupling")


def test_profile_override_mismatch_fails(tmp_path):
    root = make_plugin(tmp_path)
    report = vp.Report()
    vp.check_distribution(root, {"name": "demo-plugin"}, "private-individual", "public", report)
    assert fails(report, "profile-override")


def test_container_unlisted_plugin_fails_even_when_public(tmp_path):
    container = tmp_path / "market"
    (container / ".claude-plugin").mkdir(parents=True)
    (container / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
        {"name": "m", "owner": {"name": "oiler"},
         "plugins": [{"name": "other", "source": "./other"}]}), encoding="utf-8")
    extra = {"license": "MIT", "homepage": "https://x", "repository": "https://x", "keywords": ["a"]}
    root = make_plugin(container, manifest_extra=extra)
    manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
    profile, _ = vp.infer_profile(root, manifest)
    assert profile == "public"
    report = vp.Report()
    vp.check_distribution(root, manifest, profile, None, report)
    assert fails(report, "container-listing")


def test_container_listed_plugin_no_container_failure(tmp_path):
    container = tmp_path / "market"
    (container / ".claude-plugin").mkdir(parents=True)
    (container / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
        {"name": "m", "owner": {"name": "oiler"},
         "plugins": [{"name": "demo-plugin", "source": "./plug"}]}), encoding="utf-8")
    root = make_plugin(container)
    manifest = {"name": "demo-plugin"}
    profile, _ = vp.infer_profile(root, manifest)
    report = vp.Report()
    vp.check_distribution(root, manifest, profile, None, report)
    assert not fails(report, "container-listing")
    assert not fails(report, "container-parse")


# --- Task 3: skills layer (items 1, 3, 6) ---

def test_no_skills_dir_fails(tmp_path):
    root = make_plugin(tmp_path, skills=())
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "skills-missing")


def test_wrong_case_skill_filename_fails(tmp_path):
    root = make_plugin(tmp_path)
    d = root / "skills" / "demo-skill"
    (d / "SKILL.md").rename(d / "renamed.tmp")
    (d / "renamed.tmp").rename(d / "skill.md")
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "skill-filename")


def test_prefixed_skill_filename_fails(tmp_path):
    root = make_plugin(tmp_path)
    d = root / "skills" / "demo-skill"
    (d / "SKILL.md").rename(d / "demo-SKILL.md")
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "skill-filename")


def test_non_kebab_skill_dir_fails(tmp_path):
    root = make_plugin(tmp_path, skills=("Demo_Skill",))
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "skill-dir-kebab")


def test_frontmatter_name_mismatch_fails(tmp_path):
    root = make_plugin(tmp_path)
    d = root / "skills" / "demo-skill"
    (d / "SKILL.md").write_text("---\nname: other-name\ndescription: X. Use when testing.\n---\n\nBody.\n", encoding="utf-8")
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "skill-name-match")


def test_broken_frontmatter_fails(tmp_path):
    root = make_plugin(tmp_path)
    d = root / "skills" / "demo-skill"
    (d / "SKILL.md").write_text("---\nname: [unclosed\n---\n\nBody.\n", encoding="utf-8")
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "frontmatter")


def test_empty_description_fails(tmp_path):
    root = make_plugin(tmp_path)
    d = root / "skills" / "demo-skill"
    (d / "SKILL.md").write_text("---\nname: demo-skill\ndescription: ''\n---\n\nBody.\n", encoding="utf-8")
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "description-empty")


def test_tilde_token_in_description_fails(tmp_path):
    root = make_plugin(tmp_path)
    d = root / "skills" / "demo-skill"
    (d / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Reads ~~file-storage. Use when testing.\n---\n\nBody.\n",
        encoding="utf-8")
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert fails(report, "description-token")


def test_happy_skills_layer_no_failures(tmp_path):
    root = make_plugin(tmp_path, skills=("demo-skill", "second-skill"))
    report = vp.Report()
    vp.check_skills_layer(root, report)
    assert report.failures == []
