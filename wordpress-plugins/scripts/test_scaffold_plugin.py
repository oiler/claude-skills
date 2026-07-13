# test_scaffold_plugin.py — run with: uv run test_scaffold_plugin.py
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
import sys, subprocess
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


if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))
