# wordpress-plugins — Changelog

## v0.2.0 — 2026-07-18

### Added — test harness, audit coverage, admin-UI reference

- **The scaffolder now emits a runnable test harness.** `tests/bootstrap.php` (composer autoloader + `function_exists`-guarded recording stubs for `add_action`/`add_filter`/`__`/`esc_html__`, with a `wp_stub_reset()` helper) and `tests/PluginTest.php` (singleton smoke tests); `composer.json` gains a `test` script and `phpunit/phpunit ^10` (last major supporting the PHP 8.1 baseline). Previously `phpunit.xml.dist` referenced a bootstrap and test directory that were never written — every scaffold shipped a harness that errored on first run, unnoticed because it was never run once. A new scaffolder regression test cross-checks every path in the emitted phpunit config against the emitted file map so config and files can't drift again. Verified end-to-end: fresh scaffold → `composer install && composer test && composer lint`, all green.
- **Audit checklist gains A7 — Test Harness Missing or Broken** (advisory): bootstrap path resolves, `tests/` non-empty, `composer test` exits 0.
- **New `references/admin-ui.md`**: admin list-table columns (three-hook contract, the `manage_pages_columns` vs `manage_pages_custom_column` core asymmetry verified against `class-wp-posts-list-table.php`, native vs meta-backed sorting via `pre_get_posts`) and the Settings API (sanitize callbacks, nonce/capability discipline, the option-name prefixing rule `PrefixAllGlobals` does not enforce). SKILL.md routes Admin UI work there.

### Fixed — emitted config correctness

- **`composer install` failed on Composer ≥2.2**: the emitted `composer.json` lacked `config.allow-plugins` for `dealerdirect/phpcodesniffer-composer-installer`, so a fresh install exited 1 and VIPCS never registered with phpcs.
- **`phpunit.xml.dist` used the PHPUnit 9 schema**: the three `convert*ToExceptions` attributes were removed in PHPUnit 10 (legacy-schema deprecation on 10.5). Now emits the 10.x schema with `cacheDirectory=".phpunit.cache"` (paired `.gitignore` entry added).
- **`phpcs.xml.dist` now excludes `tests/`**: the stub bootstrap defines global WP function names by design, which `PrefixAllGlobals` would reject with unfixable errors.
- **Stale docs corrected**: SKILL.md claimed a "stub test" was emitted before it was; `structure-and-scaffolding.md` said the bootstrap must be added by hand. Both now describe what the scaffolder actually produces, and the committed-`vendor/` section documents building the production tree with `composer install --no-dev` so dev dependencies stay out of VIP deploys.
- **Fresh scaffolder output failed `composer lint` with 4 errors**, all pre-existing and none introduced by this branch's other changes: an unpunctuated inline comment in `uninstall.php`, a single-line docblock in `src/Plugin.php` missing its short description, and two calls to `flush_rewrite_rules()` — a function VIPCS restricts. The scaffolder was shipping code that failed the very ruleset it ships. Worse, the skill's own reference had been teaching the restricted pattern as correct, and misstated *why* VIPCS flags it — it claimed VIPCS objects to calling the function on every page load, when in fact VIPCS restricts the call outright, full stop. The corrected guidance is platform-split: the emitted template no longer calls `flush_rewrite_rules()` on activation, and `references/structure-and-scaffolding.md` now documents that on WordPress VIP rewrite rules are **not** flushed at deploy — they must be flushed manually via VIP-CLI (`vip @<app-name>.<environment> -- wp rewrite flush`) — while a self-hosted plugin may legitimately keep the activation call and relax the `WordPressVIPMinimum.Functions.RestrictedFunctions` sniff in its own `phpcs.xml.dist`. `composer lint` now exits 0 with zero errors on fresh scaffolder output.

### Fixed — scaffolder input handling

Found by a multi-expert review engagement (orko) and confirmed by independent verification. All four are reproduced by regression tests; this change set alone grows the suite from 11 to 21 (later work in this same v0.2.0 entry adds further tests on top of that).

- **A degenerate plugin name wrote outside the target directory.** `slugify()` returns `""` for names with no alphanumerics (`"!!!"`, `"---"`, `"   "`). Every output path was then built as `f"{slug}/{filename}"` → `"/composer.json"` — an absolute path. `Path(dir) / "/composer.json"` discards `dir` entirely and resolves to the filesystem root. Scope: this only fired when `--dir` did not already exist; under documented usage (`--dir` pointing at an existing plugins directory) the pre-existing overwrite guard caught it first. Fixed by rejecting any slug that is not `^[a-z0-9][a-z0-9-]*$` before any write, and by joining paths component-wise rather than by f-string.
- **`--namespace` and `--text-domain` skipped their sanitizers when passed explicitly.** `namespacify()` / `slugify()` only ran when the flag was *omitted*. An explicit `--namespace` was spliced verbatim into `namespace {ns};` in the generated PHP — a code context, not a comment. Fixed by validating explicit values to the same charset the derived ones produce.
- **Unescaped interpolation into `phpcs.xml.dist` XML attributes.** `name`, `namespace`, and `text_domain` all landed inside attribute values with no escaping; a `"` broke out of the attribute and a `<` would have broken the element. Fixed by constraining namespace/text-domain at the boundary and XML-escaping the free-form `name`.
- **A newline in `--name` injected a line into the generated `.gitignore`.** Fixed by rejecting control characters in `--name`.

The common thread: values were validated on the *derivation* path but trusted on the *explicit* path. Validation now happens at the boundary, in `validate_inputs()`, for both.

Across the whole v0.2.0 entry — test-harness emission, the scaffolder-input fixes above, and the final whole-branch review pass that followed — the suite stands at 32 tests.

## v0.1.0

Initial release. VIP plugin-development skill with deterministic scaffolder, audit checklist, security/performance/standards references.
