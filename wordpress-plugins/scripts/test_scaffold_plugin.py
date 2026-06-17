# test_scaffold_plugin.py — run with: uv run test_scaffold_plugin.py
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
import sys, subprocess
from scaffold_plugin import slugify, namespacify, build_files

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

if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))
