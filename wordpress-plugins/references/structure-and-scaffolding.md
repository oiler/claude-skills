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
    ├── bootstrap.php      # Autoloader + recording WP stubs (emitted by the scaffolder)
    └── PluginTest.php     # Singleton smoke tests (emitted by the scaffolder)
```

> The test harness is emitted ready to run: `composer install && composer test` passes
> on a fresh scaffold. See "Tests" below for what the stubs cover and when to upgrade.

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

`declare(strict_types=1)` must appear immediately after the plugin-header docblock, before `namespace` and before any other statement — PHP requires the `strict_types` declaration to be the very first statement in the file and raises a fatal error otherwise. A docblock is a comment, not a statement, so the plugin header may precede it. VIPCS enforces strict types on VIP.

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

## Tests

The scaffolder emits a zero-dependency unit-test harness: `phpunit/phpunit ^10` (pinned because PHPUnit 10 is the last major supporting the PHP 8.1 baseline — 11 requires 8.2+), a bootstrap, and a smoke test. `composer test` runs it.

**How the bootstrap works.** `tests/bootstrap.php` loads the composer autoloader, then defines recording stubs for the WordPress functions unit tests commonly touch (`add_action`, `add_filter`, `__`, `esc_html__`). Hook stubs record each call into `$GLOBALS['wp_stub_calls']`. A `\wp_stub_reset()` helper is defined for tests that want to clear the recorder between cases, but the emitted `PluginTest.php` does not call it — see below for why calling it from `setUp()` breaks the singleton-registration assertion. Every stub is wrapped in `function_exists()` so a heavier bootstrap can define the real functions first without conflict. One such definer is handled for you: the bootstrap calls `\Brain\Monkey\setUp()` before the stub block if Brain Monkey is installed, because Brain Monkey would otherwise define its functions too late to win — see "When the stubs stop being enough" below.

Asserting hook registration against the recorder:

```php
public function test_registers_init_hook(): void {
	Plugin::instance();
	$hooks = array_column( $GLOBALS['wp_stub_calls'], 1 );
	$this->assertContains( 'init', $hooks );
}
```

This test assumes `register_hooks()` already has an actual `add_action( 'init', ... )` call in place — against the freshly scaffolded empty stub, the assertion fails because there's nothing to record. It also depends on the recorder still holding what was captured at boot: `Plugin::instance()` is a singleton, so `register_hooks()` runs exactly once per PHP process, on the first call to `instance()` anywhere in the suite — calling `instance()` again inside this test does not re-register anything. Don't call `wp_stub_reset()` in `PluginTest::setUp()` for this reason; a reset there wipes the one-time recording before this test can read it, and the emitted `PluginTest.php` does not call it. `wp_stub_reset()` stays available in `tests/bootstrap.php` for tests that exercise non-singleton code which registers hooks on each call — those can reset between cases safely.

**`tests/` is excluded from phpcs** (see the emitted `phpcs.xml.dist`): the bootstrap defines global WordPress function names by design, which `PrefixAllGlobals` would reject — an exclusion, not a suppression comment, because the "violation" is the file's entire purpose.

**When the stubs stop being enough.** The recording stubs verify *that* hooks were registered, not *how they behave*. Once `register_hooks()` wires real callbacks and you need expectation-style assertions (a filter was applied with specific arguments, a function was called once), upgrade to Brain Monkey:

```bash
composer require --dev brain/monkey:^2.6
```

That is the whole upgrade — the emitted bootstrap already hands the WordPress function definitions over. It calls `\Brain\Monkey\setUp()` right after the autoloader whenever `Brain\Monkey\setUp` exists, so Brain Monkey defines `add_action()`/`add_filter()`/`__()` first and the stub block's `function_exists()` guards then step aside on their own. Tests move to `Monkey\Actions\expectAdded( 'init' )` style assertions and are otherwise ordinary PHPUnit.

Do not delete that handoff. Brain Monkey only loads its hook functions inside `Brain\Monkey\setUp()`, which PHPUnit runs *per test* — after the bootstrap — and its own definitions are `function_exists()`-guarded too. Without the bootstrap-time call the stubs are defined first, Brain Monkey declines to redefine them, and `expectAdded()` never intercepts: the failure surfaces as `Mockery\Exception\InvalidCountException: ... should be called at least 1 times but called 0 times` on a test whose subject plainly did call the hook. Verified empirically against `brain/monkey` 2.7.0 (the `^2.6` resolution) on a fresh scaffold — failing without the handoff, passing with it.

**Installing Brain Monkey retires the recording stubs.** Once Brain Monkey owns `add_action()`, `$GLOBALS['wp_stub_calls']` stays empty, so any `array_column( $GLOBALS['wp_stub_calls'], 1 )` assertion above silently stops seeing hooks and fails. Migrate those tests to `Monkey\Actions\expectAdded()` (or `Monkey\Actions\has()`) in the same change — this is a one-way upgrade, not an additive one. Note also that Mockery expectations do not count as PHPUnit assertions, so an expectation-only test is reported "risky"; add `Mockery\Adapter\Phpunit\MockeryPHPUnitIntegration` to the test class to have them counted.

For tests that need actual WordPress loaded (database, WP_Query), that is integration-test territory: `wp-phpunit` with a test database, out of scope for the scaffold.

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

**Dev dependencies stay out of the committed tree.** The committed `vendor/` is a production artifact — build it with `composer install --no-dev`. Dev dependencies (vipwpcs, phpcs, phpunit) exist only in local and CI installs; a plain `composer install` before committing would ship the entire linting and testing toolchain to production. The split matters more now that the dev tree includes PHPUnit: run `composer install` for daily work, and rebuild with `--no-dev` before committing `vendor/` for a VIP deploy.

Reference: https://docs.wpvip.com/technical-references/vip-codebase/composer/

---

## Lifecycle Hooks

### Activation

```php
// In src/Plugin.php
public static function activate(): void {
    // TODO: create tables, set default options, schedule cron events.
}
```

### Deactivation

```php
public static function deactivate(): void {
    // TODO: unschedule cron events and clear transients. Leave persistent data
    // in place; permanent cleanup belongs in uninstall.php.
}
```

Deactivation leaves data in place. It is the right place to clean up runtime state
(scheduled events, transients) but not permanent data (options, tables) — that belongs
in `uninstall.php`.

Neither method calls `flush_rewrite_rules()`, even though older WordPress tutorials teach it as the standard activation step for a plugin that registers custom post types or rewrite rules — the function rebuilds the entire rewrite-rules array from scratch and writes it into a single `wp_options` row, so calling it is never a cheap operation, regardless of which hook triggers it.

> **VIP-Platform only.** Rewrite rules are not flushed automatically as part of a VIP Go deploy. After a deploy that adds or changes rewrite rules, the new rules will not work until they are flushed manually, by one of two paths: running WP-CLI through VIP-CLI (`vip @<app-name>.<environment> -- wp rewrite flush`), or the lower-friction option, the Rewrite Rules Inspector — enabled by default in the VIP dashboard under Rewrite Rules → Flush Rules. This is why the scaffolder's `phpcs.xml.dist` ships `WordPressVIPMinimum`, which restricts `flush_rewrite_rules()` outright: the call regenerates the entire rewrite-rules array and writes it to a shared `wp_options` row. (Inference, not a documented VIP rationale — VIP has not published why the sniff restricts the call this way; VIPCS issue #701 is an open request asking for exactly that.) The scaffolder's own `activate()`/`deactivate()` output above satisfies that sniff by not calling the function at all.

Reference: https://docs.wpvip.com/wordpress-skeleton/serve-static-content-wp/

Self-hosted plugins are not bound by VIP's manual flush step, and calling `flush_rewrite_rules()` once on activation — after registering custom post types or rewrite rules — is standard, correct WordPress practice there. It will still trip the `WordPressVIPMinimum.Functions.RestrictedFunctions` sniff this scaffolder ships, though, so a self-hosted project that wants the call back should relax that specific sniff in its own `phpcs.xml.dist` rather than leave the resulting error standing:

```xml
<rule ref="WordPressVIPMinimum.Functions.RestrictedFunctions">
    <exclude name="WordPressVIPMinimum.Functions.RestrictedFunctions.flush_rewrite_rules_flush_rewrite_rules"/>
</rule>
```

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
