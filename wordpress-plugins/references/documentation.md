# Plugin Documentation Standards

PHPDoc conventions, `readme.txt` format, and inline-comment discipline for WordPress VIP plugins. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025) / VIPCS 3.0+.

Release mechanics (semver, git tags, GitHub Releases, CHANGELOG.md) are owned by the `git-tagging` skill — see cross-link at the end of this file. This file covers the three WP-plugin doc artifacts: PHPDoc, `readme.txt`, and inline comments.

---

## PHPDoc

The `WordPress-Docs` PHPCS ruleset (included via `phpcs.xml.dist`) enforces PHPDoc on classes and methods. The examples below match what the scaffolder emits and what VIPCS expects.

### File-level docblock

Every PHP file gets a file-level docblock with `@package` and `@since`.

```php
<?php
/**
 * Core plugin class.
 *
 * @package My_Plugin
 * @since   1.0.0
 */
```

The main plugin file's docblock is the WordPress plugin header — it doubles as the file-level docblock. The scaffolder emits it with `@package` only (not `@since`), which is standard for the entry point; `@since` is most useful on non-entry-point files.

### Class docblock

One-line summary plus `@since`.

```php
/**
 * Main plugin class — singleton entry point.
 *
 * @since 0.1.0
 */
class Plugin {
```

No `@package` needed on the class — the file-level docblock already declares it.

### Function and method docblocks

Every public and protected method gets a docblock. Private methods: document if the intent isn't obvious from the name.

```php
/**
 * Return the singleton instance, creating it on the first call.
 *
 * @since  0.1.0
 * @return static
 */
public static function instance(): static {
```

```php
/**
 * Register a settings option and return its current value.
 *
 * @since  1.2.0
 * @param  string $key     Option name (without plugin prefix).
 * @param  mixed  $default Fallback value when option is not set.
 * @return mixed  Current option value, or $default.
 */
public function get_option( string $key, mixed $default = null ): mixed {
```

Tag order: summary → blank line → `@since` → `@param` lines → `@return`.

`@param` format: `@param  type $name Description.` — period at the end, type before name, two spaces of alignment within the block (conventional; align for readability — VIP examples align).

Hooks (actions) and functions with no return value use `@return void`.

### `@since` discipline

`@since` marks when the symbol was **introduced**. It ties to the plugin's own release version — not to the WordPress version. New symbols in a `1.3.0` release get `@since 1.3.0`.

When an argument is added to an existing function in a later version, document it on the `@param` line:

```php
/**
 * @since 1.0.0
 * @param string $status   Post status filter.
 * @param int    $limit    Maximum results. Added in 1.4.0.
 */
```

### Hook docblocks (`apply_filters` / `do_action`)

WordPress parses docblocks placed immediately above `apply_filters()` and `do_action()` calls to generate the code reference. Each passed argument (including `$value` for filters) gets a `@param` tag.

**Filter:**

```php
/**
 * Filter the list of allowed file types for upload.
 *
 * @since 1.1.0
 * @param string[] $types  Allowed MIME types, keyed by extension.
 * @param int      $post_id Post ID the upload is attached to.
 */
$types = apply_filters( 'my_plugin_allowed_types', $types, $post_id );
```

**Action:**

```php
/**
 * Fires after the plugin settings are saved.
 *
 * @since 1.0.0
 * @param array $settings The saved settings array.
 */
do_action( 'my_plugin_settings_saved', $settings );
```

The first `@param` on a filter always describes the filtered value; subsequent `@param` tags describe the extra arguments passed to callbacks.

---

## `readme.txt`

The scaffolder emits a `readme.txt` skeleton. The exact fields it produces:

```
=== My Plugin ===

Contributors:      oiler
Tags:              wordpress, vip
Requires at least: 6.0
Tested up to:      6.5
Requires PHP:      8.1
Stable tag:        0.1.0
License:           GPL-2.0-or-later
License URI:       https://www.gnu.org/licenses/gpl-2.0.html

My Plugin WordPress plugin.

== Description ==

My Plugin is a WordPress plugin built to VIP coding standards.

== Changelog ==

= 0.1.0 =
* Initial release.
```

### Header fields

| Field | Purpose |
|-------|---------|
| `Contributors` | WordPress.org usernames (comma-separated, no spaces around commas) |
| `Tags` | Discovery tags on WP.org (lowercase, comma-separated; ≤ 5 on WP.org) |
| `Requires at least` | Minimum WordPress version the plugin has been tested against |
| `Tested up to` | Highest WordPress version tested — keep current with WP releases |
| `Requires PHP` | Minimum PHP version; scaffolder emits `8.1` |
| `Stable tag` | The version WP.org serves as the stable download — **must match the plugin header `Version`** |
| `License` | SPDX identifier; scaffolder uses `GPL-2.0-or-later` |
| `License URI` | Full URL of the license text |

**`Stable tag` ↔ plugin `Version` parity is required.** WordPress.org reads `Stable tag` to determine which tagged release to serve as the installable zip. If they diverge, users get the wrong version. The `git-tagging` skill creates the release tag — update `Stable tag` and the plugin header `Version` in the same commit that bumps the version, before tagging.

### Sections

`== Description ==` — public-facing description shown on the plugin's WP.org page. Can use markdown-like syntax (headers with `=`, bold with `**`).

`== Installation ==` — numbered steps for manual install. Include when the plugin has non-obvious setup (e.g., API key config, mu-plugin loader). Omit when it's drag-and-drop only.

`== Frequently Asked Questions ==` — Q&A pairs. Each question is a `= Question? =` subheading. Skip entirely if there's nothing worth answering.

`== Changelog ==` — newest version first. One version per `= X.Y.Z =` subheading, bulleted entries. VIP reviewers read this.

`== Upgrade Notice ==` — short (≤ 300 chars) per-version message shown in the WP admin upgrade prompt. Only needed when the upgrade requires action (e.g., database migration, settings reset).

### Changelog format

```
== Changelog ==

= 1.3.0 =
* Add: filter `my_plugin_allowed_types` to control upload MIME types.
* Fix: settings not saving on multisite when blog ID > 9999.

= 1.2.0 =
* Add: `get_option()` helper method.
* Change: minimum PHP version bumped to 8.1.

= 0.1.0 =
* Initial release.
```

The three header levels are: `===` for the plugin title, `==` for top-level sections (Description, Installation, Changelog, etc.), and `=` for subsection headings within a section (changelog versions, FAQ questions).

Prefix bullets with `Add:`, `Fix:`, `Change:`, or `Remove:` for readability. Entries map 1:1 to commits or PRs — the CHANGELOG.md maintained by `git-tagging` is the source of truth; copy relevant entries here.

---

## Inline Comments

Comment the **why**, not the what. If the name of the function or variable already explains the operation, the comment adds nothing.

**Skip it — the name explains it:**

```php
// Flush rewrite rules.    ← useless; flush_rewrite_rules() says the same
flush_rewrite_rules();
```

**Keep it — the why isn't obvious:**

```php
// Only flush on activation, not on every page load — each flush causes
// a full database write.
flush_rewrite_rules();
```

```php
// Activation/deactivation hooks must be registered in the main plugin file,
// not inside a class. WordPress only processes them during the initial plugin
// load when it scans the main file directly.
register_activation_hook( __FILE__, [ \My_Plugin\Plugin::class, 'activate' ] );
```

```php
// The file_exists guard lets the plugin load before `composer install` has run
// (e.g., a fresh checkout). On VIP Go, vendor/ is committed so this always resolves.
if ( file_exists( __DIR__ . '/vendor/autoload.php' ) ) {
    require_once __DIR__ . '/vendor/autoload.php';
}
```

**Section separators** are acceptable when a file is long and the blocks are genuinely distinct (e.g., hooks, helpers, lifecycle). Use a short word or phrase, not a decorative line:

```php
// --- Lifecycle ---------------------------------------------------------------
```

Avoid end-of-line comments on densely packed code — they become stale faster than any other form. Prefer a docblock or a preceding line comment.

---

## Version Mechanics: Defer to `git-tagging`

Semver rules, git tag creation, GitHub Releases, and CHANGELOG.md maintenance are owned by the `git-tagging` skill. The WP-plugin-specific relationship is:

1. Bump `Version` in the main plugin file header.
2. Bump `Stable tag` in `readme.txt` to match.
3. Add a `= X.Y.Z =` entry to `readme.txt` Changelog (copy from CHANGELOG.md).
4. Commit, then let `git-tagging` handle the tag and GitHub Release.

Do not duplicate semver or tagging guidance here.

---

## Cross-skill References

- **Release mechanics** (semver, git tags, GitHub Releases, CHANGELOG.md) → `git-tagging` skill
- **Plugin structure and scaffolder** → [`structure-and-scaffolding.md`](structure-and-scaffolding.md)
- **VIPCS ruleset that enforces `WordPress-Docs`** → [`vip-standards.md`](vip-standards.md)
