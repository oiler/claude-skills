# Markup Style Layer — oiler

> oiler's personal HTML conventions. This is the **style layer** — it operates only within what the base layer (semantic-html.md) considers correct. Flexes with authority mode (see SKILL.md). Extracted from authored samples; re-extract when new authored markup is added.

**Extracted:** 2026-06-06 — from foxlaboratory.com `<body>` and baseballprospectus.com `.container`.

## Indentation & whitespace
- Tabs used in foxlaboratory theme markup (sample: foxlaboratory L83–L104).
- Four-space indentation used in baseballprospectus theme markup (sample: bp L377–L383).
- Both samples use blank lines between major structural blocks (e.g. between `</header>` and `<main>`, between `</section>` elements) (sample: foxlaboratory L105–L108; bp L368–L372).

## Document structure & landmarks
- `<header>`, `<nav>`, `<main>`, and `<footer>` are used as top-level landmark elements wrapping the page (sample: foxlaboratory L83, L90, L108, L143).
- `<section>` is used for named content groupings within a page region (sample: bp L313, L372, L424, L474).
- `<main>` receives both `id` and `role="main"` explicitly even though `<main>` already carries implicit main role (sample: foxlaboratory L108).

## Class naming
- Site-scoped utility prefix (`fdl-`) applied to all owned structural components in the foxlaboratory theme: `fdl-header`, `fdl-nav`, `fdl-text-logo`, `fdl-details`, `fdl-page-content` (sample: foxlaboratory L83, L84, L90, L97, L108).
- BEM-like double-dash modifier used for widget sub-elements: `ootb-tabcordion--tabs`, `ootb-tabcordion--entry`, `ootb-tabcordion--entry-container`, `ootb-tabcordion--entry-content` (sample: bp L477, L484, L485, L486).
- Flat hyphen-separated multi-word classes used for content/layout zones alongside BEM: `hp-top`, `hp-bottom`, `pay-status`, `box-label` (sample: bp L313, L372, L321, L512).
- Compound space-separated classes used to encode item metadata directly: `item item0 post-107684 Features` — position index + WordPress post ID + category slug (sample: bp L316, L329, L342).
- `is-active` state class applied to the active tab and panel (sample: bp L478, L484).

## IDs
- IDs used for landmark anchoring and JS targeting: `id="site-content"` on `<main>`, `id="sidebar-primary"` on sidebar `<div>` (sample: foxlaboratory L108, L138).
- Tabcordion panel IDs follow a `<group>__<tab-slug>` pattern: `recent_articles__features`, `recent_articles__prospects` (sample: bp L484, L491).
- Tab trigger IDs follow `tab_<slug>`: `tab_features`, `tab_prospects`, `tab_fantasy` (sample: bp L478, L479, L480).

## ARIA & interactive widgets
- Tab container gets `role="tablist"` and `aria-label` (sample: bp L477, L516).
- Each tab element (`<h6>`) gets `role="tab"`, `aria-selected="true/false"`, and `aria-controls` pointing to its panel ID (sample: bp L478–L481).
- Inactive tabs get `tabindex="-1"` to remove them from natural tab order; active tab has no `tabindex` attribute (sample: bp L478–L481).
- Tab panels: `role="tabpanel"` + `tabindex="0"`. Note: in the sample, `aria-labelledby` points to generic ordinal IDs (`tab1`, `tab2`) that do NOT match the actual tab element IDs (`tab_features`, …) — an apparent bug, not a pattern to copy; the base layer (semantic-html.md) requires `aria-labelledby` to reference the real tab `id`. (sample: bp L484, L478)
- `<main>` carries explicit `role="main"` in addition to the implicit role (sample: foxlaboratory L108).

## Comments
- Commented-out markup is preserved in place as toggle markers rather than deleted: `<!--<ul class="notebook-tax-page-list">-->`, `<!--<h4></h4>-->`, `<!--<img ...>-->` (sample: foxlaboratory L109, L112, L144).
- Short descriptive labels used as section comments ahead of widget blocks: `<!-- front box recent articles -->`, `<!-- box three -->` (sample: bp L475, L514).
- Larger commented-out blocks of functional markup are preserved multi-line, indented to match surrounding code (sample: bp L525–L527, L535–L537, L545–L547).

## Links & navigation
- Nav link text is all-lowercase: "home", "about", "work", "notes", "contact" (sample: foxlaboratory L91–L95).
- Active/current nav link is marked with `class="current"` (sample: foxlaboratory L91).
- Article links within content grids use `class="item"` plus positional and metadata classes (sample: bp L316, L329, L342, L355).

## Images
- Decorative or context-provided images use empty alt (`alt=""`); branded logos use descriptive alt text (sample: bp L317 `alt=""`; foxlaboratory L86 `alt="Fox Digital Labs, LLC"`).
- Content images carry both explicit `width` and `height` attributes, `loading="lazy"`, `srcset`, and `sizes` (sample: bp L317, L330).
- Logo/header images carry explicit `width` only (no height, no lazy, no srcset) (sample: foxlaboratory L86–L87).
- Attribute order on content `<img>`: `width`, `height`, `src`, `class`, `alt`, `loading`, `srcset`, `sizes` (sample: bp L317).

## Attribute ordering
- On `<main>`: `id`, `role`, `class` (sample: foxlaboratory L108).
- On structural `<div>` with data hook: `class`, `data-*` (sample: bp L476).
- On tab trigger elements: `class`, `role`, `aria-selected`, `aria-controls`, `id`, then `tabindex` only when inactive (sample: bp L478–L481).
- On tab panel elements: `id`, `class`, `data-title`, `tabindex`, `role`, `aria-labelledby` (sample: bp L484, L491).

## Document-level
- No clear convention observed in samples. (`<html lang>` and `<head>` are WordPress-generated boilerplate excluded from authored regions in both samples.)

## Tentative (seen once — confirm before promoting)
- `<h6>` used as tab trigger element within a tabcordion widget (not a heading hierarchy choice) — seen only in the bp tabcordion, not confirmed elsewhere (sample: bp L478–L481).
- `data-tabacco` attribute used as JS initialization hook on the tabcordion root element (sample: bp L476).
- `<table>` used for small key/value metadata display in a site header (sample: foxlaboratory L98–L103).
- Trailing whitespace after `href` value before `>` on nav links without a class: `<a href="/about" >about</a>` — may be an artifact, not a convention (sample: foxlaboratory L92–L95).
