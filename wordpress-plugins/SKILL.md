---
name: wordpress-plugins
description: >
  Build, audit, secure, and scale WordPress plugins to VIP Coding Standards,
  with a deterministic scaffolder. Use for all WordPress plugin work: build a
  plugin, plugin development, WordPress VIP plugin, VIP coding standards, VIPCS,
  VIP compliant, audit my plugin, scaffold a plugin, composer autoload, PSR-4,
  plugin performance, object cache, transients, plugin security, nonces,
  escape output, prepared statements, readme.txt, plugin release, shortcodes,
  REST endpoints, register post type or taxonomy, enqueue scripts/styles,
  admin settings page, Options/Settings API,
  activation/deactivation/uninstall hooks, cron jobs, wp_schedule_event,
  multisite or network-activated plugin, phpcs, plugin unit tests, WP_Mock,
  plugin changelog, plugin versioning.
  NOT for: Gutenberg blocks or block editor components (use wordpress-blocks);
  theme code in functions.php or theme templates (use wordpress-themes);
  generic OWASP fundamentals unrelated to WordPress (use web-security); block
  themes or FSE (not covered).
allowed-tools: Bash(uv run *) Bash(composer *) Bash(grep *) Read Write Edit
---

## WordPress Plugins skill

Baseline: **WordPress 6.x**, **PHP 8.1+**, **VIP Coding Standards (2025) / VIPCS 3.0+**. All guidance enforces VIP-Platform constraints by default. Rules that apply only on VIP Platform (e.g., no direct DB writes outside designated APIs) are labelled **[VIP only]** so self-hosted developers are not misled.

Before proceeding, read the reference file that matches your mode (table below). The references contain the authoritative detail; this file routes you to the right one.

---

## Mode routing

| Mode | What you're doing | Read first |
|---|---|---|
| **Build** | New plugin from scratch | `references/structure-and-scaffolding.md` |
| **Audit** | Review an existing plugin for quality/compliance | `references/audit-checklist.md` |
| **Add feature** | Add a new capability to an existing plugin | `references/structure-and-scaffolding.md` + the relevant deep reference below |
| **Release** | Publish or version a plugin | `references/documentation.md` (readme.txt); delegate semver/tag/CHANGELOG mechanics to `git-tagging` |
| **Tooling** | Set up VIPCS, phpcs.xml.dist, CI | `references/vip-standards.md` + `references/structure-and-scaffolding.md` |
| **Performance / scale** | Caching, query bounds, remote calls | `references/vip-performance.md` |
| **Security** | Nonces, caps, escaping, prepared statements, REST auth | `references/security.md` |

### Scaffolder (Build mode)

To generate a plugin skeleton, run:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/scaffold_plugin.py --name "My Plugin Name" --dir wp-content/plugins
```

The scaffolder produces the main plugin file, PSR-4 `src/` layout, `composer.json`, and stub test. See `references/structure-and-scaffolding.md` for what it generates and how to extend it.

---

## Cross-skill routing

| Need | Skill |
|---|---|
| OWASP fundamentals, threat modelling, HTTP security headers | `web-security` |
| Gutenberg blocks, block editor, block.json, `@wordpress/blocks` | `wordpress-blocks` |
| Semver, git tags, GitHub Releases, CHANGELOG.md | `git-tagging` |
| Admin CSS, Sass architecture, BEM, design tokens | `sass` |

**Boundary vs `wordpress-themes`:** if the code lives in a theme (functions.php, theme template files, theme-only hooks) use `wordpress-themes`. If the code is standalone, distributable, or meant to be reusable across themes/sites — it's a plugin; use this skill.

---

## Critical rules

These apply to every task; no exceptions without an explicit label:

- **VIP constraints by default.** Flag platform-only rules with **[VIP only]** rather than silently omitting them.
- **Cache every remote call.** Wrap `wp_remote_*` calls in transients or object-cache; never hit an external API on every page load.
- **Bound every query.** All `WP_Query` / `get_posts` calls must set `posts_per_page` or equivalent. No unbounded loops over `get_posts()`.
- **Escape at echo, not before.** Use `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses_post()` at the point of output.
- **Verify nonces.** Every form submission and AJAX handler must call `check_admin_referer()` or `check_ajax_referer()` before acting.
- **Check capabilities.** Gate all privileged actions with `current_user_can()` using the minimum required capability.
- **Never `flush_rewrite_rules()` on every page load.** Call it only on activation/deactivation hooks.
- **Commit `vendor/`.** [VIP only] VIP Go sites do not run `composer install` at deploy time; `vendor/` must be committed.
