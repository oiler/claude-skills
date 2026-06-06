---
name: front-end-engineer
description: oiler's authority for writing and reviewing HTML markup. Use whenever building, editing, or auditing HTML / front-end markup — pages, templates, components, partials, layouts. Triggers on "write HTML", "build this page", "markup", "front end", "semantic HTML", "is this semantic", "review this markup", "audit this HTML", "accessible markup", "ARIA", "landmark roles", "heading structure", "which element to use", "semantic element", "convert to semantic HTML", "div soup", "fix this markup". Produces semantically correct HTML (per MDN) in oiler's personal style, and audits existing markup against both. Routes adjacent work to the sass, wordpress-themes, wordpress-blocks, and web-security skills.
---

# front-end-engineer

The authority on HTML markup, and the entry point for front-end work. Produces semantically correct HTML in oiler's style, audits existing markup against the same standard, and routes adjacent concerns to complementary skills.

## How this skill works: two layers

| Layer | Source | When it applies |
|---|---|---|
| **Base — correctness** | MDN / HTML Living Standard → `references/semantic-html.md` | Always. Every mode, every authority level. |
| **Style — preferences** | oiler's authored markup → `references/markup-style.md` | Flexes with authority mode (below). |

**Precedence:** correctness always wins. The style layer only chooses among options the base layer considers valid. If oiler explicitly asks for something semantically off, build it but flag the divergence and why. Never silently emit incorrect markup.

For any element/attribute not covered in `references/semantic-html.md`, fetch the MDN page rather than guessing.

## Modes

- **Write** — author markup that is correct (base layer) and on-style (style layer, subject to authority). Read both reference files first.
- **Audit** — review existing HTML against both layers and report findings with fixes. Follow `references/audit-checklist.md`. Triggers on "review this markup", "is this semantic", "audit this HTML".

## Authority model

FEE adjusts how hard it imposes the **style layer** based on a per-project signal — a line in the project's CLAUDE.md:

- `front-end-engineer: full` — impose oiler's style everywhere.
- `front-end-engineer: adapt` — match the project's existing conventions; assert oiler's style only where the project has no established pattern.

**Default when the signal is absent: `adapt`.** Inspect surrounding files, existing markup, and any linter/formatter config before asserting a preference.

**The correctness floor holds in every mode** — only the style layer flexes; the base layer never yields.

## Routing — collaborate with complementary skills

FEE owns markup. When a task crosses into an adjacent domain, **invoke** the matching skill (directive, not advisory). Load nothing the task doesn't need.

| Task also involves | Invoke |
|---|---|
| Styling / Sass | `sass` |
| Classic WordPress theme context | `wordpress-themes` |
| Gutenberg blocks | `wordpress-blocks` |
| Output escaping / untrusted data | `web-security` |
<!-- Extend this table as new front-end skills are added (e.g. vanilla-js). -->

## Scope

**Owns:** HTML markup — semantics, structure, landmarks/ARIA, and markup-level accessibility and performance attributes (`alt`, `srcset`, `sizes`, `loading`, explicit `width`/`height`, `lang`).

**Routes, does not own:** CSS/Sass, JavaScript behavior, WordPress plumbing (enqueueing, escaping, `render_callback`, template hierarchy, VIP rules), and security escaping of untrusted data.

## References

| File | Use when |
|---|---|
| `references/semantic-html.md` | Checking correctness; any "is this the right element / role" question. |
| `references/markup-style.md` | Applying oiler's style; deciding among valid options. |
| `references/audit-checklist.md` | Running audit mode. |
