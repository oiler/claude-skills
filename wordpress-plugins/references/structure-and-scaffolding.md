# Plugin Structure and Scaffolding

WordPress VIP plugin conventions, directory layout, main-file anatomy, OOP+PSR-4, and scaffolder usage. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025), VIPCS 3.0+.

---

## Scaffolder

Deterministic scaffolder that emits the full skeleton. Run once per plugin; never overwrites an existing directory.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/scaffold_plugin.py \
    --name "My Plugin" \
    --dir /path/to/plugins
```

**Optional overrides** (both are derived from `--name` when omitted):

| Flag | Default derivation | Example |
|------|--------------------|---------|
| `--namespace` | StudlyCaps words joined by `_` | `My_Plugin` |
| `--text-domain` | kebab-case slug | `my-plugin` |

```bash
# Explicit overrides:
uv run ${CLAUDE_SKILL_DIR}/scripts/scaffold_plugin.py \
    --name "Acme Events" \
    --namespace Acme_Events \
    --text-domain acme-events \
    --dir /path/to/plugins
```

**Derivation rules**: slug/text-domain = kebab-case (`"My Plugin"` → `my-plugin`);
namespace = first letter of each word uppercased (remainder preserved), joined by `_` (`"My Plugin"` → `My_Plugin`).

**Refuse-to-overwrite**: if `<dir>/<slug>` already exists the script prints an error to
stderr and exits with code 1. No partial writes.

---

## Directory Layout

```
my-plugin/
├── my-plugin.php          # Main plugin file: header, bootstrap
├── composer.json          # PSR-4 autoload map; vipwpcs dev-deps; lint/fix scripts
├── phpcs.xml.dist         # VIPCS 3.0+ rulesets: WordPress-VIP-Go, WordPressVIPMinimum, WordPress-Docs
├── phpunit.xml.dist       # PHPUnit config; test suite points at tests/
├── uninstall.php          # Cleanup on plugin deletion (WP_UNINSTALL_PLUGIN guard)
├── readme.txt             # WordPress.org / VIP readme format
├── .gitattributes         # export-ignore for dev artifacts; vendor/ rationale comment
├── .gitignore             # vendor/ intentionally NOT ignored on VIP (see note below)
├── src/
│   └── Plugin.php         # Namespaced singleton stub; add further classes here
├── vendor/                # Committed on VIP Go (see VIP-Platform note); absent until
│   └── autoload.php       #   `composer install` runs on non-VIP deploys
└── tests/
    └── bootstrap.php      # Add after scaffolding; PHPUnit looks here per phpunit.xml.dist
```

> `tests/bootstrap.php` is not emitted by the scaffolder — add it when writing the first
> test. PHPUnit is configured to look for `*Test.php` files under `tests/`.

---

## Main Plugin File (`<slug>.php`)

### Header block

```php
<?php
/**
 * Plugin Name: My Plugin
 * Description: My Plugin plugin.
 * Version:     0.1.0
 * Author:      oiler
 * Text Domain: my-plugin
 * Requires PHP: 8.1
 * Requires at least: 6.0
 * License:     GPL-2.0-or-later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 *
 * @package My_Plugin
 */
```

Required fields for VIP: `Plugin Name`, `Text Domain`, `Requires PHP`, `Requires at least`,
`License`. WordPress reads this docblock — do not move it or add code above it.

### `declare(strict_types=1)` and namespace

```php
declare(strict_types=1);

namespace My_Plugin;
```

`declare(strict_types=1)` must appear immediately after the plugin-header docblock (and before `namespace`).
The `namespace` declaration must follow it. VIPCS enforces strict types on VIP.

### `ABSPATH` guard

```php
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
```

Prevents direct HTTP access to the file. Required on VIP; PHPCS will flag its absence.

### Autoloader require

```php
if ( file_exists( __DIR__ . '/vendor/autoload.php' ) ) {
    require_once __DIR__ . '/vendor/autoload.php';
}
```

The `file_exists` guard lets the file load before `composer install` has run (e.g., a
fresh checkout). On VIP Go, `vendor/` is committed so this always resolves.

### Lifecycle hook registration

```php
register_activation_hook( __FILE__, [ \My_Plugin\Plugin::class, 'activate' ] );
register_deactivation_hook( __FILE__, [ \My_Plugin\Plugin::class, 'deactivate' ] );
```

These must be called in the main plugin file — not inside a class or `add_action` callback
— because WordPress only processes them during the initial plugin load. The leading `\`
in the class name is required because the main file itself is namespaced.

### Singleton bootstrap

```php
\My_Plugin\Plugin::instance();
```

Boots the plugin at file-load time. The singleton prevents double-init if the file is
included twice and provides a stable handle for other code.

---

## OOP + PSR-4

**One class per concern.** The scaffolder creates `src/Plugin.php` as the root singleton.
Add further classes as needed:

```
src/
├── Plugin.php          # Core singleton — boots the plugin, wires hooks
├── Enqueues.php        # Scripts and styles (see sass skill for admin CSS workflow)
├── Register_Blocks.php # Block registration (see wordpress-blocks skill)
├── Settings.php        # Admin settings page, if any
└── CPT/
    └── Event.php       # Custom post type — nested namespace is fine
```

**Namespace = PSR-4 key.** The `composer.json` emitted by the scaffolder maps the
namespace to `src/`:

```json
"autoload": {
    "psr-4": {
        "My_Plugin\\": "src/"
    }
}
```

Every class under `src/` must declare `namespace My_Plugin;` (or a sub-namespace like `My_Plugin\CPT`). File path mirrors the namespace: `My_Plugin\CPT\Event` → `src/CPT/Event.php`.

**After adding or renaming a class**, regenerate the autoload map:

```bash
composer dump-autoload
```

On VIP, commit the regenerated `vendor/composer/` files alongside the new class.

**Coding standards** — `composer.json` ships two scripts:

```bash
composer lint   # phpcs — report violations
composer fix    # phpcbf — auto-fix what it can
```

PHPCS is configured via `phpcs.xml.dist` against `WordPress-VIP-Go`, `WordPressVIPMinimum`,
and `WordPress-Docs` rulesets.

---

## VIP-Platform: Committed `vendor/`

> **VIP-Platform only.** Self-hosters may skip this section and run `composer install` at
> deploy time instead.

WordPress VIP Go does not run `composer install` during deployment. The `vendor/` directory
must be committed to the plugin repository so the autoloader is present on the platform.

The scaffolder configures this correctly:

- **`.gitignore`** — `vendor/` is intentionally absent from `.gitignore`. A comment in the
  file explains why. Do not add `vendor/` to `.gitignore` on VIP-targeted plugins.
- **`.gitattributes`** — marks `vendor/` as `export-ignore`. This strips it from
  WordPress.org installable zips (where the platform runs `composer install` itself)
  while keeping it committed in the repo. The `export-ignore` does not affect VIP Go
  deployment.

**Consequence:** `composer update` must be followed by a commit of the updated `vendor/`
before the change reaches production on VIP.

Reference: https://docs.wpvip.com/technical-references/vip-codebase/composer/

---

## Lifecycle Hooks

### Activation

```php
// In src/Plugin.php
public static function activate(): void {
    // Create custom tables, set default options, schedule cron events.
    flush_rewrite_rules(); // Only here, on activation — never on every page load.
}
```

`flush_rewrite_rules()` is correct on activation (and deactivation) because it rebuilds
the rules once after the plugin registers its custom post types or rewrite rules. Calling
it on every page load causes a full database write on every request — a performance
violation that VIPCS will flag.

### Deactivation

```php
public static function deactivate(): void {
    // Unschedule cron events, remove transients, flush rewrites.
    flush_rewrite_rules();
}
```

Deactivation leaves data in place. It is the right place to clean up runtime state
(scheduled events, transients) but not permanent data (options, tables) — that belongs
in `uninstall.php`.

### Uninstall: `uninstall.php` over the uninstall hook

WordPress provides two uninstall mechanisms:

| Mechanism | When it runs |
|-----------|-------------|
| `register_uninstall_hook()` | At plugin deletion, but only if the plugin is loaded |
| `uninstall.php` | At plugin deletion; WordPress loads this file directly |

**Use `uninstall.php`.** The uninstall hook only fires if WordPress can load the plugin
(which may fail if dependencies are missing). `uninstall.php` is loaded directly by
WordPress and is therefore more reliable. The scaffolder emits it with the required guard:

```php
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
    exit; // Prevents direct HTTP access.
}

// Remove options, custom tables, scheduled events here.
// Example: delete_option( 'my-plugin_settings' );
```

Delete permanent data here: options (`delete_option`), custom tables (`$wpdb->query`),
user meta (`delete_user_meta`), scheduled events (`wp_clear_scheduled_hook`).

---

## Cross-skill References

- **Gutenberg blocks** — when registering custom blocks inside a plugin, see the
  `wordpress-blocks` skill for block.json, `render_callback`, and asset enqueueing
  conventions.
- **Admin CSS** — for plugin admin stylesheets authored in Sass, see the `sass` skill
  for file organization, variable conventions, and build integration.
