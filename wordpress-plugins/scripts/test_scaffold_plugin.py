# test_scaffold_plugin.py — run with: uv run test_scaffold_plugin.py
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
import json, sys, subprocess
import xml.etree.ElementTree as ET
import pytest
from scaffold_plugin import slugify, namespacify, build_files, validate_inputs, InvalidInput

def test_slugify_spaces_and_case():
    assert slugify("My Cool Plugin") == "my-cool-plugin"

def test_slugify_strips_punctuation():
    assert slugify("Acme's VIP Plugin!") == "acmes-vip-plugin"

def test_namespacify():
    assert namespacify("My Cool Plugin") == "My_Cool_Plugin"

def test_build_files_has_required_keys():
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    expected = {
        "my-plugin/my-plugin.php", "my-plugin/composer.json",
        "my-plugin/phpcs.xml.dist", "my-plugin/phpunit.xml.dist",
        "my-plugin/uninstall.php", "my-plugin/readme.txt",
        "my-plugin/.gitattributes", "my-plugin/.gitignore",
        "my-plugin/src/Plugin.php",
    }
    assert expected <= set(files.keys())

def test_main_file_has_header_and_namespace():
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    main = files["my-plugin/my-plugin.php"]
    assert "Plugin Name: My Plugin" in main
    assert "Text Domain: my-plugin" in main
    assert "namespace My_Plugin;" in main
    assert "if ( ! defined( 'ABSPATH' ) )" in main  # direct-access guard

def test_composer_has_psr4_map():
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    assert '"My_Plugin\\\\": "src/"' in files["my-plugin/composer.json"]

def test_phpcs_references_vip_ruleset():
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    assert "WordPressVIPMinimum" in files["my-plugin/phpcs.xml.dist"]
    assert "WordPress-VIP-Go" in files["my-plugin/phpcs.xml.dist"]

def test_uninstall_has_guard():
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    assert "WP_UNINSTALL_PLUGIN" in files["my-plugin/uninstall.php"]

def test_main_file_namespace_order():
    """namespace must appear before the ABSPATH guard; declare must precede namespace."""
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    main = files["my-plugin/my-plugin.php"]
    declare_pos = main.index("declare(strict_types=1);")
    namespace_pos = main.index("namespace My_Plugin;")
    abspath_pos = main.index("if ( ! defined( 'ABSPATH' ) )")
    assert declare_pos < namespace_pos, "declare(strict_types=1) must come before namespace"
    assert namespace_pos < abspath_pos, "namespace must come before ABSPATH guard"

def test_src_plugin_php_namespace_order():
    """src/Plugin.php: declare then namespace, no ABSPATH guard needed but ordering is correct."""
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    plugin = files["my-plugin/src/Plugin.php"]
    declare_pos = plugin.index("declare(strict_types=1);")
    namespace_pos = plugin.index("namespace My_Plugin;")
    assert declare_pos < namespace_pos, "declare(strict_types=1) must come before namespace in src/Plugin.php"

def test_refuse_to_overwrite_existing_directory(tmp_path):
    """Scaffolder must exit non-zero and refuse to overwrite an existing target directory."""
    script = str(
        (
            __import__("pathlib").Path(__file__).parent / "scaffold_plugin.py"
        ).resolve()
    )
    args_base = [sys.executable, script, "--name", "Test Plugin", "--dir", str(tmp_path)]

    # First run: must succeed.
    result_first = subprocess.run(args_base, capture_output=True, text=True)
    assert result_first.returncode == 0, f"First run failed: {result_first.stderr}"

    # Count files from first run so we can verify nothing new is written.
    target = tmp_path / "test-plugin"
    files_before = set(target.rglob("*"))

    # Second run with identical args: must fail.
    result_second = subprocess.run(args_base, capture_output=True, text=True)
    assert result_second.returncode != 0, "Expected non-zero exit when target dir already exists"
    assert "Error" in result_second.stderr or "error" in result_second.stderr, (
        f"Expected error message on stderr, got: {result_second.stderr!r}"
    )

    # Directory contents must be unchanged.
    files_after = set(target.rglob("*"))
    assert files_before == files_after, "Scaffolder wrote files on second (refused) run"


@pytest.mark.parametrize("degenerate", ["!!!", "   ", "---", "'''", "!@#$%"])
def test_degenerate_name_rejected(degenerate):
    """A name that slugifies to "" made every output path absolute, and
    Path(dir) / "/composer.json" discards dir — writing to the filesystem root."""
    assert slugify(degenerate) == ""
    with pytest.raises(InvalidInput):
        build_files(degenerate, "X", "x")


def test_explicit_namespace_with_php_payload_rejected():
    """--namespace bypassed namespacify() when passed explicitly, splicing raw into `namespace {ns};`."""
    with pytest.raises(InvalidInput):
        validate_inputs(
            "Test Plugin",
            'Foo; } function evil(){ system($_GET["c"]); } namespace Foo',
            "test-plugin",
            "test-plugin",
        )


def test_explicit_text_domain_with_payload_rejected():
    with pytest.raises(InvalidInput):
        validate_inputs("Test Plugin", "Test_Plugin", 'x"/><evil', "test-plugin")


def test_name_with_newline_rejected():
    """A newline in --name injected an extra line into the generated .gitignore."""
    with pytest.raises(InvalidInput):
        build_files("Evil Plugin\nvendor/secrets.php", "Evil_Plugin", "evil-plugin")


def test_xml_metachars_in_name_are_escaped():
    """name is free-form prose, so it is escaped rather than rejected."""
    files = build_files('Quote" & <Angle> Plugin', "Quote_Angle_Plugin", "quote-angle-plugin")
    phpcs = files["quote-angle-plugin/phpcs.xml.dist"]
    assert "&quot;" in phpcs and "&amp;" in phpcs and "&lt;Angle&gt;" in phpcs
    assert '<Angle>' not in phpcs

    import xml.dom.minidom
    xml.dom.minidom.parseString(phpcs)  # raises if the payload broke the document


def test_valid_inputs_still_pass():
    validate_inputs("My Cool Plugin", "My_Cool_Plugin", "my-cool-plugin", "my-cool-plugin")


def test_composer_has_test_harness_config():
    """composer.json must define the test script, the PHPUnit dev-dep pinned to ^10
    (last major supporting the PHP 8.1 baseline), and allow-plugins for the phpcs
    installer plugin (Composer >=2.2 blocks unlisted plugins and exits 1)."""
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    composer = json.loads(files["my-plugin/composer.json"])
    assert composer["scripts"]["test"] == "phpunit"
    assert composer["require-dev"]["phpunit/phpunit"] == "^10"
    assert composer["config"]["allow-plugins"]["dealerdirect/phpcodesniffer-composer-installer"] is True

def test_phpcs_excludes_tests_dir():
    """tests/bootstrap.php defines global WP function names (add_action, __, ...) by
    design; PrefixAllGlobals cannot be satisfied there, so tests/ must be excluded."""
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    assert "<exclude-pattern>*/tests/*</exclude-pattern>" in files["my-plugin/phpcs.xml.dist"]

def test_phpunit_config_is_phpunit10():
    """The convert*ToExceptions attributes were removed in PHPUnit 10 (legacy-schema
    deprecation on 10.5); the emitted config must use the 10.x schema and cache dir."""
    xml = build_files("My Plugin", "My_Plugin", "my-plugin")["my-plugin/phpunit.xml.dist"]
    for legacy in ("convertErrorsToExceptions", "convertNoticesToExceptions", "convertWarningsToExceptions"):
        assert legacy not in xml
    assert 'cacheDirectory=".phpunit.cache"' in xml
    assert "https://schema.phpunit.de/10.5/phpunit.xsd" in xml

def test_gitignore_covers_phpunit_caches():
    """PHPUnit 10 writes .phpunit.cache/ when cacheDirectory is set; keep the pair
    (.gitignore entry <-> cacheDirectory value) consistent."""
    gi = build_files("My Plugin", "My_Plugin", "my-plugin")["my-plugin/.gitignore"]
    assert ".phpunit.result.cache" in gi
    assert ".phpunit.cache/" in gi


def test_emits_test_files():
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    assert "my-plugin/tests/bootstrap.php" in files
    assert "my-plugin/tests/PluginTest.php" in files
    assert len(files) == 11

def test_bootstrap_stubs_are_guarded():
    """Stubs must be defined only when WP hasn't provided the real function, so a
    future integration bootstrap (wp-phpunit / Brain Monkey) can coexist."""
    b = build_files("My Plugin", "My_Plugin", "my-plugin")["my-plugin/tests/bootstrap.php"]
    for fn in ("add_action", "add_filter", "__", "esc_html__"):
        assert f"function_exists( '{fn}' )" in b
    assert "wp_stub_reset" in b
    assert "vendor/autoload.php" in b

def test_plugin_test_uses_namespace():
    t = build_files("My Plugin", "My_Plugin", "my-plugin")["my-plugin/tests/PluginTest.php"]
    assert "namespace My_Plugin\\Tests;" in t
    assert "use My_Plugin\\Plugin;" in t
    assert "Plugin::instance()" in t

def test_phpunit_config_paths_exist_in_build_output():
    """Regression guard for the shipped defect: phpunit.xml.dist referenced paths the
    scaffolder never wrote. Parse the emitted config and cross-check every referenced
    path against build_files() keys, so config and file map can never drift again."""
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    root = ET.fromstring(files["my-plugin/phpunit.xml.dist"])
    bootstrap = root.get("bootstrap")
    assert bootstrap, "phpunit.xml.dist must declare a bootstrap"
    assert f"my-plugin/{bootstrap}" in files
    dirs = list(root.iter("directory"))
    assert dirs, "phpunit.xml.dist must declare at least one testsuite directory"
    for d in dirs:
        prefix = d.text.strip().removeprefix("./").rstrip("/")
        suffix = d.get("suffix", "")
        matches = [k for k in files if k.startswith(f"my-plugin/{prefix}/") and k.endswith(suffix)]
        assert matches, f"testsuite dir '{d.text}' matches no emitted file"


def test_emitted_php_has_no_vip_restricted_functions():
    """VIPCS restricts *calls* to flush_rewrite_rules(): it rewrites the whole rules array
    into wp_options. This checks for an actual call — `flush_rewrite_rules(` appearing
    outside of `//` comment text — not for any mention of the function's name. The
    scaffolder's own guidance comments name the function on purpose, to warn developers
    off it, and that mention must not trip this test."""
    files = build_files("My Plugin", "My_Plugin", "my-plugin")
    for path, content in files.items():
        if path.endswith(".php"):
            for line in content.splitlines():
                code = line.split("//", 1)[0]
                assert "flush_rewrite_rules(" not in code, f"{path} calls a VIPCS-restricted function: {line.strip()}"


def test_uninstall_inline_comments_are_punctuated():
    """WordPress-Docs requires inline comments to end in terminal punctuation."""
    uninstall = build_files("My Plugin", "My_Plugin", "my-plugin")["my-plugin/uninstall.php"]
    for line in uninstall.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") and len(stripped) > 2:
            assert stripped[-1] in ".!?", f"unpunctuated inline comment: {stripped}"


def test_src_plugin_docblocks_have_short_descriptions():
    """Every docblock must open with a short description line, not a tag.

    Covers both multi-line docblocks (an opener line of exactly `/**` followed
    directly by a `@tag` line) and single-line docblocks that open straight into
    a tag, e.g. `/** @var static|null Singleton instance. */` — the latter is
    the actual pre-fix defect this test was written to guard against.
    """
    plugin = build_files("My Plugin", "My_Plugin", "my-plugin")["my-plugin/src/Plugin.php"]
    lines = plugin.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "/**":
            following = lines[i + 1].strip()
            assert following.startswith("*") and not following.startswith("* @"), (
                f"docblock at line {i + 1} opens straight into a tag: {following}"
            )
        elif stripped.startswith("/** @"):
            pytest.fail(f"single-line docblock at line {i + 1} opens straight into a tag: {stripped}")


if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))
