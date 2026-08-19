---
name: google-style
description: "Write and edit all technical and project prose to the Google developer documentation style guide. Use whenever producing or revising documentation: a spec, design doc, implementation plan, README, API doc, reference page, guide, tutorial, PRD, product brief, roadmap, RACI, changelog, release notes, or PR description — and for Claude's own explanations, summaries, and review findings in chat. ALWAYS trigger on 'write the README', 'draft the spec', 'document this', 'write the docs', 'write up this design', 'changelog entry', 'PR description', 'release notes', 'clean up this doc', 'edit this documentation', 'turn these notes into a tutorial', 'is this doc clear', 'sentence case', 'style guide', 'Google style', 'developer documentation'. Bundles a checker at scripts/style_check.py that gates the mechanically verifiable rules; run it on every documentation file you write. Do NOT use for personal or external-facing prose — letters, memos, emails, cover letters, essays, articles, blog posts, social posts, or written feedback to a human — those belong to the writing-style skill. Do NOT use for writing, debugging, or modifying code — including this skill's own bundled checker scripts — nor for docstring format, readme.txt field order, or commit-message grammar; those belong to the domain skill that owns the file."
---

# Google developer documentation style

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

This skill is the standing prose standard for technical and project artifacts: specs, design docs, implementation plans, `README` files, API docs, reference pages, guides, tutorials, product requirement documents, product briefs, roadmaps, changelogs, release notes, PR descriptions, and Claude's own explanations, summaries, and review findings in chat.

## When this skill does not apply

Personal and external-facing prose belongs to the `writing-style` skill: a letter, memo, email, cover letter, application, essay, article, blog post, social post, or written feedback to a human.

On detecting a personal artifact, the skill states the handoff and stops applying its own rules. A partial handoff, where the word list keeps firing inside a cover letter, is worse than no handoff at all.

The split is by artifact type, not by how explicitly a request names a skill. An artifact addressed to a reader who has to do something with a system belongs here; an artifact addressed to a person as a person belongs to `writing-style`.

For an artifact that sits between the two, and for the per-artifact notes, read `references/applying-to-artifacts.md`. That file also carries the edge cases: a release announcement in Slack, a technical email, a commit message.

## Layering

This skill decorates other work rather than displacing it, so four rules bound what it touches.

1. **oiler's CLAUDE.md outranks this skill.** Brevity, no emoji, tables over prose, never hard-wrap markdown, `oiler` lowercase. Google's guidance is the floor beneath those rules, never a replacement for them. Where the guide's conversational tone would run longer than CLAUDE.md's brevity rule allows, brevity wins, because the reader chose that rule for every artifact and this skill applies to one.
2. **Domain skills keep their own file conventions.** This skill governs prose. It does not govern `readme.txt` field order, docstring format, or commit-message grammar. The skill that owns the file owns its format, and a style rule that rewrites a required field breaks the file for the tool that parses it.
3. **Superpowers templates keep their structure.** Apply the style to the prose inside a spec or plan. Do not rewrite a template's required headings to satisfy sentence case, because the heading text is load-bearing for the tooling that reads it.
4. **Personal prose exits immediately.** The handoff to `writing-style` runs before any rule here applies, per the preceding section. Half a handoff leaves two voices in one document.

## The rules that apply to every sentence

Ten rules earn a place in the always-loaded layer. Everything else waits in `references/` until the task needs it.

1. **Second person, not first.** Address the reader directly. First person is a gating error, and quoted source material is exempt.
2. **Active voice with a named actor.** Name the thing that acts: `the installer creates the file`, not `the file is created`.
3. **Present tense.** Describe what the software does, not what it did or what it is going to do.
4. **Sentence case for every heading and title, with no end punctuation.** Capitalize the first word and proper nouns, and leave the rest lowercase.
5. **Serial commas.** Put a comma before the final `and` or `or` in a list of three or more items.
6. **Descriptive link text that names the destination.** Link the words that say where the link goes, not `here` or `read more`.
7. **Code font for code and file names, bold for UI elements.** Backticks mark what the reader types verbatim; bold marks what the reader clicks.
8. **Timeless documentation with no pre-announcements.** Drop `currently`, `at this time`, and `in a future release`. A document that dates itself is wrong by the next release.
9. **Conditions before instructions.** Put the condition first, so the reader knows whether a step applies before starting it.
10. **Write for a global audience.** No idioms, and no directional language such as `above` or `below`. Name the section or the figure instead.

## Run the checker

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/style_check.py <path>          # one file or a directory
python3 ${CLAUDE_SKILL_DIR}/scripts/style_check.py <path> --json   # machine-readable
python3 ${CLAUDE_SKILL_DIR}/scripts/style_check.py --list-rules    # the 31 rules and their pages
```

The loop: write the file, run the checker, fix every error, and rerun until it exits 0. Then read the warnings and apply judgment.

Errors gate, and warnings inform. The guide itself permits passive voice and semicolons where they read best, so blocking on them would be stricter than the standard this skill implements, and a checker that blocks on judgment calls teaches the reader to ignore it.

The loop reruns after any later edit, including a reviewer's, because an edit breaks the contract as readily as authoring does.

## Reference routing

| If you're writing or checking… | Read |
|---|---|
| Anything — which skill owns this artifact, and per-artifact notes | `references/applying-to-artifacts.md` |
| Tone, jargon, claims about the future, third-party content | `references/voice-and-tone.md` |
| Person, voice, tense, capitalization, contractions, abbreviations | `references/language-and-grammar.md` |
| Commas, dashes, ellipses, hyphens, quotation marks, semicolons | `references/punctuation.md` |
| Headings, lists, procedures, tables, notices, numbers, dates, units | `references/formatting-and-structure.md` |
| Code in text, code samples, CLI syntax, placeholders, UI elements | `references/code-and-ui.md` |
| Links, cross-references, images, alt text | `references/links-and-images.md` |
| Accessibility, global audience, inclusive language | `references/accessibility-and-global.md` |
| A word the checker flagged, or a term you are unsure of | `references/word-list.md` |

Load only the files the current task needs. Loading all nine defeats the point of the split.
