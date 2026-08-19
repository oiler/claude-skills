# Changelog — google-style

All notable changes to this skill are documented here. The format follows Keep a Changelog, and this skill uses semantic versioning under the per-skill tag `google-style-vX.Y.Z`.

## [0.1.0] — 2026-08-18

### Added

- The Google developer documentation style guide as the standing standard for technical and project prose, pinned to the guide's last update of 2026-07-07.
- Seven distilled reference files, one workshop-authored application guide, and one generated word list. Each distilled file names the guide pages it covers.
- `scripts/style_check.py`: 31 rules, 19 that gate and 12 that inform, with offset-preserving masking so no finding lands inside a code sample.
- `references/applying-to-artifacts.md`: the boundary with the `writing-style` skill, its edge cases, and per-artifact notes.

### Notes

Three optional frontmatter fields are left unset on purpose:

- `disable-model-invocation`: auto-invocation is the activation model. A standing prose standard that waits for an explicit request isn't standing.
- `paths`: a glob would silently exclude the chat surface, where Claude's own explanations, summaries, and review findings are also in scope.
- `allowed-tools`: this skill layers under the domain skills and must not restrict the tools they need.

One trigger-eval negative carries a waiver. The query `the checker exits 2 on a directory that has no markdown in it — debug it` routes here because the description claims ownership of `scripts/style_check.py`, and the skill needs that claim to carry its instruction to run the checker on every documentation file. Commit 931810b added an explicit exclusion naming the bundled checker scripts, and routing held at 3/3 across four runs. The overlap stands on the merits: `SKILL.md` documents the exit-code contract a debugger needs, while `python` remains the implementing skill for the code itself. Full rationale in `evals/google-style/waivers.json`.
