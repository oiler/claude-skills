# scaffold_plugin.py — WordPress VIP plugin scaffolder
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Deterministic plugin scaffolder for WordPress VIP.

Usage:
    uv run scaffold_plugin.py --name "My Plugin" --dir /path/to/plugins
    uv run scaffold_plugin.py --name "My Plugin" --namespace My_Plugin --text-domain my-plugin --dir /path/to/plugins
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Derivation helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Convert a human-readable plugin name to a kebab-case slug.

    "My Cool Plugin" -> "my-cool-plugin"
    "Acme's VIP Plugin!" -> "acmes-vip-plugin"
    """
    lowered = name.lower()
    # Remove anything that isn't alphanumeric or a space/hyphen
    cleaned = re.sub(r"[^a-z0-9\s\-]", "", lowered)
    # Collapse runs of whitespace/hyphens to a single hyphen
    slugged = re.sub(r"[\s\-]+", "-", cleaned)
    return slugged.strip("-")


def namespacify(name: str) -> str:
    """Convert a human-readable plugin name to a PHP namespace (StudlyCaps words joined by _).

    "My Cool Plugin" -> "My_Cool_Plugin"
    """
    words = name.split()
    parts = []
    for word in words:
        # Strip non-alphanumeric chars, title-case
        clean = re.sub(r"[^a-zA-Z0-9]", "", word)
        if clean:
            parts.append(clean[0].upper() + clean[1:])
    return "_".join(parts)


# ---------------------------------------------------------------------------
# File content builders
# ---------------------------------------------------------------------------

def _main_php(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return f"""\
<?php
/**
 * Plugin Name: {name}
 * Description: {name} plugin.
 * Version:     0.1.0
 * Author:      oiler
 * Text Domain: {text_domain}
 * Requires PHP: 8.1
 * Requires at least: 6.0
 * License:     GPL-2.0-or-later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 *
 * @package {namespace}
 */

if ( ! defined( 'ABSPATH' ) ) {{
\texit;
}}

namespace {namespace};

// Composer autoloader — vendor/ is committed for VIP Go platform compatibility.
if ( file_exists( __DIR__ . '/vendor/autoload.php' ) ) {{
\trequire_once __DIR__ . '/vendor/autoload.php';
}}

// Activation / deactivation hooks must be registered before the plugin bootstraps.
register_activation_hook( __FILE__, [ \\{namespace}\\Plugin::class, 'activate' ] );
register_deactivation_hook( __FILE__, [ \\{namespace}\\Plugin::class, 'deactivate' ] );

\\{namespace}\\Plugin::instance();
"""


def _composer_json(name: str, namespace: str, text_domain: str, slug: str) -> str:
    data = {
        "name": f"oiler/{slug}",
        "description": f"{name} WordPress plugin",
        "type": "wordpress-plugin",
        "license": "GPL-2.0-or-later",
        "require": {
            "php": ">=8.1"
        },
        "require-dev": {
            "automattic/vipwpcs": "*",
            "dealerdirect/phpcodesniffer-composer-installer": "*"
        },
        "autoload": {
            "psr-4": {
                f"{namespace}\\": "src/"
            }
        },
        "scripts": {
            "lint": "phpcs",
            "fix": "phpcbf"
        }
    }
    return json.dumps(data, indent=4) + "\n"


def _phpcs_xml_dist(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return f"""\
<?xml version="1.0"?>
<ruleset name="{name}">
    <description>PHPCS ruleset for {name} — WordPress VIP standards.</description>

    <!-- Scan all PHP files in the project root. -->
    <file>.</file>

    <!-- Exclude generated / third-party code. -->
    <exclude-pattern>*/vendor/*</exclude-pattern>
    <exclude-pattern>*/node_modules/*</exclude-pattern>

    <!-- Target PHP 8.1+. -->
    <config name="testVersion" value="8.1-"/>

    <!-- WordPress text domain and function prefix for i18n / naming checks. -->
    <config name="text_domain" value="{text_domain}"/>

    <rule ref="WordPress-VIP-Go"/>
    <rule ref="WordPressVIPMinimum"/>
    <rule ref="WordPress-Docs"/>

    <!-- Set the expected text domain for i18n rules. -->
    <rule ref="WordPress.WP.I18n">
        <properties>
            <property name="text_domain" type="array" value="{text_domain}"/>
        </properties>
    </rule>

    <!-- Enforce namespace/prefix to avoid collisions. -->
    <rule ref="WordPress.NamingConventions.PrefixAllGlobals">
        <properties>
            <property name="prefixes" type="array" value="{namespace}"/>
        </properties>
    </rule>
</ruleset>
"""


def _phpunit_xml_dist(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<phpunit
    bootstrap="tests/bootstrap.php"
    colors="true"
    convertErrorsToExceptions="true"
    convertNoticesToExceptions="true"
    convertWarningsToExceptions="true"
>
    <testsuites>
        <testsuite name="unit">
            <directory suffix="Test.php">./tests/</directory>
        </testsuite>
    </testsuites>
</phpunit>
"""


def _uninstall_php(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return f"""\
<?php
/**
 * Uninstall script for {name}.
 *
 * Runs when the plugin is deleted from the WordPress admin.
 * Keep side-effects minimal and reversible where possible.
 *
 * @package {namespace}
 */

// Guard: only run when WordPress triggers the uninstall, not on direct access.
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {{
\texit;
}}

// TODO: Remove plugin options, custom database tables, and scheduled events here.
// Example: delete_option( '{text_domain}_settings' );
"""


def _readme_txt(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return f"""\
=== {name} ===

Contributors:      oiler
Tags:              wordpress, vip
Requires at least: 6.0
Tested up to:      6.5
Requires PHP:      8.1
Stable tag:        0.1.0
License:           GPL-2.0-or-later
License URI:       https://www.gnu.org/licenses/gpl-2.0.html

{name} WordPress plugin.

== Description ==

{name} is a WordPress plugin built to VIP coding standards.

== Changelog ==

= 0.1.0 =
* Initial release.
"""


def _gitattributes(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return """\
# Export ignore: strip dev artefacts when WordPress.org generates the installable zip.
# NOTE: vendor/ is intentionally committed for WordPress VIP Go platform compatibility
# (the platform does not run `composer install`). The export-ignore below only strips it
# from WP.org release zips where it is not needed.
/vendor export-ignore
/.github export-ignore
/tests export-ignore
/phpcs.xml.dist export-ignore
/phpunit.xml.dist export-ignore
/.gitattributes export-ignore
"""


def _gitignore(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return f"""\
# {name} — .gitignore
#
# vendor/ is intentionally NOT ignored. WordPress VIP Go requires vendor/ to be
# committed because the platform does not run `composer install` at deploy time.
# See: https://docs.wpvip.com/technical-references/vip-codebase/composer/
#
# If you are deploying outside VIP, add `vendor/` below.

node_modules/
.DS_Store
*.log
.phpunit.result.cache
"""


def _src_plugin_php(name: str, namespace: str, text_domain: str, slug: str) -> str:
    return f"""\
<?php
/**
 * Core plugin class.
 *
 * @package {namespace}
 */

namespace {namespace};

/**
 * Main plugin class — singleton entry point.
 */
class Plugin {{

\t/** @var static|null Singleton instance. */
\tprivate static ?self $instance = null;

\t/**
\t * Return (and create on first call) the singleton instance.
\t */
\tpublic static function instance(): static {{
\t\tif ( null === static::$instance ) {{
\t\t\tstatic::$instance = new static();
\t\t}}
\t\treturn static::$instance;
\t}}

\t/** Boot the plugin. */
\tprivate function __construct() {{
\t\t$this->register_hooks();
\t}}

\t/** Wire up WordPress action/filter hooks. */
\tprivate function register_hooks(): void {{
\t\t// TODO: add add_action() / add_filter() calls here.
\t}}

\t/**
\t * Run on plugin activation.
\t * Called by register_activation_hook() in the main plugin file.
\t */
\tpublic static function activate(): void {{
\t\t// TODO: flush rewrite rules, create tables, set defaults.
\t\tflush_rewrite_rules();
\t}}

\t/**
\t * Run on plugin deactivation.
\t * Called by register_deactivation_hook() in the main plugin file.
\t */
\tpublic static function deactivate(): void {{
\t\t// TODO: clean up scheduled events, temp data.
\t\tflush_rewrite_rules();
\t}}
}}
"""


# ---------------------------------------------------------------------------
# Public API consumed by tests
# ---------------------------------------------------------------------------

def build_files(name: str, namespace: str, text_domain: str) -> dict[str, str]:
    """Return a mapping of relative-path -> file-content for the full plugin skeleton."""
    slug = slugify(name)

    builders = {
        f"{slug}/{slug}.php": _main_php,
        f"{slug}/composer.json": _composer_json,
        f"{slug}/phpcs.xml.dist": _phpcs_xml_dist,
        f"{slug}/phpunit.xml.dist": _phpunit_xml_dist,
        f"{slug}/uninstall.php": _uninstall_php,
        f"{slug}/readme.txt": _readme_txt,
        f"{slug}/.gitattributes": _gitattributes,
        f"{slug}/.gitignore": _gitignore,
        f"{slug}/src/Plugin.php": _src_plugin_php,
    }

    return {path: fn(name, namespace, text_domain, slug) for path, fn in builders.items()}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a VIP-compliant WordPress plugin skeleton."
    )
    parser.add_argument(
        "--name",
        required=True,
        help='Human-readable plugin name, e.g. "My Cool Plugin"',
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="PHP namespace (StudlyCaps_Words). Derived from --name if omitted.",
    )
    parser.add_argument(
        "--text-domain",
        dest="text_domain",
        default=None,
        help="WordPress text domain (kebab-case). Derived from --name if omitted.",
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Parent directory in which to create the plugin folder.",
    )
    args = parser.parse_args()

    namespace = args.namespace or namespacify(args.name)
    text_domain = args.text_domain or slugify(args.name)
    slug = slugify(args.name)
    target = Path(args.dir) / slug

    if target.exists():
        print(
            f"Error: target directory already exists: {target}",
            file=sys.stderr,
        )
        sys.exit(1)

    files = build_files(args.name, namespace, text_domain)

    for rel_path, content in files.items():
        abs_path = Path(args.dir) / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        print(f"  created  {abs_path}")

    print(f"\nPlugin scaffolded at: {target}")


if __name__ == "__main__":
    main()
