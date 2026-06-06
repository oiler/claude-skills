# Audit Mode — checklist

> Use in audit mode: given existing HTML, report findings against both layers with a concrete fix for each. Base-layer violations are **errors** (correctness). Style-layer divergences are **advisories** — their weight depends on authority mode (full = enforce, adapt = report only where the project has no established pattern).

## How to run an audit
1. Identify authored markup vs. generated/boilerplate; audit authored markup.
2. Pass 1 — base layer: check each rule in semantic-html.md. Any failure is an ERROR.
3. Pass 2 — style layer: check each rule in markup-style.md. Any divergence is an ADVISORY.
4. For every finding, give: location, which layer, the rule, and the corrected markup.
5. Summarize: error count, advisory count, then the fixes.

## Base-layer checks (errors)
- [ ] Exactly one `<main>`, not nested in a sectioning element.
- [ ] `<section>` has a heading and a thematic purpose; non-semantic groups use `<div>`.
- [ ] Heading levels are sequential; no skips for styling; one logical `<h1>`.
- [ ] No `role` duplicating a native element's implicit role; native element preferred over ARIA.
- [ ] Interactive ARIA widgets carry all required states/relationships, and `aria-labelledby`/`aria-controls` reference IDs that exist.
- [ ] Elements with a non-native interactive role are keyboard operable.
- [ ] Every form control has a programmatic label.
- [ ] Lists contain only valid children; data tables use `<th scope>`/`<caption>`; no layout tables.
- [ ] Content images have meaningful `alt`; decorative images have `alt=""`.
- [ ] `<html lang>`, charset, and viewport present; `<a>` for navigation, `<button>` for actions.

## Style-layer checks (advisories)
- [ ] Tab indentation.
- [ ] Class naming matches oiler's convention (site-scoped prefix; BEM-like `--` modifiers).
- [ ] Landmark/sectioning usage matches oiler's structure.
- [ ] Content images carry explicit `width`/`height` + `loading="lazy"` + `srcset`/`sizes`.
- [ ] Comment usage matches oiler's labeling/toggle convention.
- [ ] Nav link text lowercase; active link marked `class="current"`.
- [ ] Attribute ordering matches oiler's convention.

## Output format
**Errors (N):** location → rule → fix.
**Advisories (M):** location → rule → fix (note when suppressed by `adapt` mode).
