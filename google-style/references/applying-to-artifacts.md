# Applying this style to artifacts

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: none — this file is workshop-authored application guidance.

## Which skill owns this artifact

Google's guide never asks which documents it governs, because Google already knows the answer: everything the developer documentation team ships. oiler's library has a second prose standard, `writing-style`, so this skill needs a stopping condition the guide can't supply.

The pair splits by artifact type, not by how explicitly a request names a skill. That's a different split from the one between `writing-style` and `writing-style-builder`, which divides broad against restrictive.

| Artifact | Skill |
|---|---|
| Spec, design doc, implementation plan | `google-style` |
| README, API doc, guide, tutorial, reference | `google-style` |
| PRD, product brief, roadmap, RACI | `google-style` |
| Changelog, release notes, PR description | `google-style` |
| Claude's chat explanations, summaries, review findings | `google-style` |
| Letter, memo, email to a human | `writing-style` |
| Cover letter, application, essay, article, blog post | `writing-style` |
| Social post, written feedback to a human | `writing-style` |

The line underneath the table: an artifact addressed to a reader who has to do something with a system belongs here, and an artifact addressed to a person as a person belongs to `writing-style`.

`writing-style`'s own description already excludes specs, design docs, implementation plans, code comments, docstrings, commit messages, PR descriptions, changelogs, READMEs, and technical documentation. The two skills agree on the technical half from both sides, so the table restates a boundary rather than inventing one.

When the artifact is personal prose, say so, hand off to `writing-style`, and stop applying these rules. A partial handoff, where Google's word list keeps firing inside a cover letter, is worse than no handoff at all.

## Edge cases

| Edge case | Skill | Reason |
|---|---|---|
| A release announcement posted to Slack | `writing-style` | The subject is technical, but the artifact is a message to people. Audience decides, not subject matter. |
| A PR description | `google-style` | It documents a change for a reviewer who has to act on it. Technical artifact, technical voice. |
| An email explaining a technical decision to a colleague | `writing-style` | An email is a letter. A technical subject doesn't convert it into documentation. |
| A commit message | Neither | Git convention governs: imperative mood, no trailing period. Neither skill overrides it. |

The technical email carries one rule across the handoff. Its prose belongs to `writing-style`, and any code, command, filename, flag, or environment variable inside it still takes the code-font treatment in `code-and-ui.md`. Code formatting marks what the reader types verbatim, which makes it a correctness rule rather than a voice rule, and correctness rules don't switch off at a skill boundary.

## What to do at the boundary

If an artifact is still a genuine coin flip after the table and the edge cases, pick a side and say which way you went and why, in one sentence, before you start writing. Don't pick silently.

The reader can correct a recorded decision in the next turn. A silent one leaves the reader to reverse-engineer the choice from the finished prose, which nobody does, so the wrong call survives into the artifact.

Keep the note to one sentence. Something on the order of "Treating this as technical documentation because the audience is a reviewer, not a correspondent" is the whole obligation. The boundary note is a footnote to the work, never a section of it.

A coin flip that keeps recurring for the same artifact type is a defect in the table above, not a judgment call to re-decide each time. Fix the table.

## Per-artifact notes

For each artifact: the rules that bite hardest, and the parts of the artifact's own format that this skill leaves alone.

### Spec

Hardest rules: `future` and `first-person`. A spec describes a design that doesn't exist yet, which pulls constantly toward `will soon`, `in a future release`, and `currently` — all errors. Write the design in the present tense as though it already runs: `the checker reports warnings`, not `the checker will report warnings`. Design prose also slides into `we` by reflex; name the actor or address the reader instead.

Left alone: the superpowers spec template's required headings. Their exact text is load-bearing for the tooling that reads the file, so keep them verbatim even where they aren't sentence case. Sentence case applies to headings you add.

### Implementation plan

Hardest rules: the auxiliary verbs from prescriptive documentation, and imperative procedure steps. A plan exists to say what has to happen, so `should` is the wrong verb almost everywhere in it: use `must` for a required action, `can` for an optional one, and `might` for a possible outcome. Each step gets one action, phrased as a command to the reader.

Left alone: the same template rule as the spec. Required headings, task numbering, and checkbox syntax stay as the template defines them.

### README

Hardest rules: `headings`, `link-text`, and second person. Sentence case throughout with no end punctuation on headings; link text that names its destination rather than reading `here` or `read more`; and `you` for the reader, because a README talks to someone who has to install or run something.

Left alone: conventional section order, and any registry's required fields. A WordPress `readme.txt` field order comes from `wordpress-plugins`, not from here.

### PR description

Hardest rules: excessive claims, and the timeless-documentation rules read in reverse. A PR description is genuinely time-stamped, because it describes a change relative to a base, so `new`, `existing`, and `now` are honest words here in a way they aren't on a reference page. What still binds: no `simply` or `obviously`, and no performance claim the diff doesn't demonstrate.

Left alone: the repository's PR template, its trailer conventions, and any checklist the reviewers rely on.

### Changelog

Hardest rules: jargon and timeless documentation. Each entry is a sentence, in sentence case, written for someone who didn't watch the change happen. Spell out the internal shorthand that made sense inside the PR.

Left alone: Keep a Changelog's section names. `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security` name the sections exactly — don't lowercase them for sentence case, and don't rename them. Release notes also sit inside the guide's own exception for time-stamped content, so they may use dated wording.

### Chat reply

Hardest rules: `first-person`, excessive claims, and heading case in structured answers. `we` and `let's` are the reflex phrasings in an explanation, and `simply` and `obviously` are the reflex fillers.

Left alone: oiler's `CLAUDE.md`, which sits above this skill. Brevity, no emoji, tables over prose, and never hard-wrapping markdown all win wherever they conflict with Google's conversational-tone guidance. The checker also never runs on a chat turn, because there's no file to check. In a chat reply these rules apply from memory or they don't apply.

## Running the checker

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/style_check.py <path>
```

`<path>` takes one or more Markdown files or directories.

| Exit code | Meaning |
|---|---|
| 0 | No errors. Warnings might still have printed. |
| 1 | At least one error, or, with `--strict`, at least one warning. |

Errors are the rules Google states flatly, so they gate. Warnings are the ones that need a person to read the sentence before deciding, so they inform without gating. `--strict` promotes warnings to gating findings for a run where you want the stricter reading.

The loop:

1. Write the file.
2. Run the checker on it.
3. Fix every error. An error has one right answer, so there's no judgment to exercise.
4. Rerun. Repeat until the run exits 0.
5. Read the warnings and decide each one. A warning is a question, not a verdict: passive voice is sometimes the right construction, an uncontracted negation is sometimes the clearer one, and oiler's spaced em dashes are house style that the checker flags and `CLAUDE.md` protects.

Run the loop again after any later edit to the file, including a reviewer's edit. An edit breaks the contract exactly as authoring can: someone rewording a sentence introduces `currently` or a Title Case heading as readily as a first draft does. The passing run belongs to the file's current bytes, not to the file's name.

Three flags help when you're working on part of the problem. `--only` and `--skip` take comma-separated rule ids. `--json` emits findings as JSON for tooling. `--list-rules` prints every rule with its severity and its source page; read it before you name a rule in prose, because the severity is part of what naming the rule claims.
