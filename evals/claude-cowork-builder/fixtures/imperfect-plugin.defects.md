# `imperfect-plugin` — defect manifest (grading key)

Grading key for the audit behavior-eval. `imperfect-plugin/` is a plausible small team-tool plugin (`team-ops`) carrying **exactly eight planted defects**. Everything else in the fixture is deliberately valid: manifest at `.claude-plugin/plugin.json` with `author` as an object, semver `version`, parseable `.mcp.json`, `README.md` present at the plugin root.

Four defects are caught mechanically by `scripts/validate_plugin.py` — an audit run that starts with the validator (as the checklist instructs) gets those for free, so **finding all four script defects is the floor, not the score**. The run is scored on how many of the four **judgment** defects it surfaces on its own.

Mechanical baseline, reproduced:

```bash
uv run claude-cowork-builder/scripts/validate_plugin.py \
  evals/claude-cowork-builder/fixtures/imperfect-plugin --json
```

→ exit 1, failures on items **6, 1, 8, 7** (in that emission order).

## The eight planted defects

| # | File | Exact planted text | Audit item | Authority |
|---|---|---|---|---|
| 1 | `skills/weekly-report/skill.md` | the filename itself — lowercase `skill.md` where the platform requires exactly `SKILL.md` | 1 | script |
| 2 | `skills/crm-sync/SKILL.md` frontmatter | `description: Helps with ~~CRM tasks.` — a raw `~~` token in `description` frontmatter | 6 | script |
| 3 | `skills/weekly-report/skill.md` § Steps, step 6 | `Save the report to /Users/alex/reports/ as weekly-report.html` — a machine-specific absolute path where the working folder belongs | 8 | script |
| 4 | `skills/weekly-report/skill.md` § Output Format | `open weekly-report.html` inside a fenced ```` ```bash ```` block | 7 | script |
| 5 | `skills/crm-sync/SKILL.md` frontmatter | `description: Helps with ~~CRM tasks.` — thin, generic, no trigger phrases, no `Use when…` clause | 3 | judgment |
| 6 | `skills/crm-sync/SKILL.md` body | no `## Without connected sources` section at all; `## With your CRM connected` says "This skill requires your CRM connector" and dead-ends the user when it is not configured | 5 | judgment |
| 7 | `.mcp.json`, `crm` server entry | `"Authorization": "Bearer EXAMPLE-NOT-A-SECRET-0000"` — a literal credential where a `${VAR}` substitution belongs | 9 | judgment |
| 8 | `skills/weekly-report/skill.md` § Steps, step 7 | "Update cell B2 of the tracking spreadsheet through the Sheets connector with this week's shipped count" | 14 | judgment |

## Notes on individual rows

**Defects 2 and 5 share one string.** The single frontmatter line `description: Helps with ~~CRM tasks.` carries both defects: the `~~CRM` token (item 6, mechanical) and the thin generic description with no trigger phrases and no `Use when…` clause (item 3, judgment). They are separate findings against separate checklist items and should be scored separately — an audit that reports only "the description is thin" has found defect 5, not defect 2, and vice versa.

**Defect 2 is caught mechanically by item 6.** The validator's `TILDE_TOKEN` regex matches acronyms and two-word tokens (`~~CRM`, `~~cloud storage`, `~~CI/CD`), so the uppercase acronym spelling used here is caught by the item 6 `description-token` check. The uppercase spelling is deliberate: it is the real corpus spelling, and acronym matching was a regex bug fixed in this release — this fixture doubles as a live regression demonstration. There is no coupling between profile and `~~` tokens in skill *bodies*; a private plugin carrying body tokens passes. The one token rule enforced everywhere is item 6's, and it is scoped to `description` frontmatter only.

**Defect 7 uses an unmistakably fake credential.** `EXAMPLE-NOT-A-SECRET-0000` cannot be mistaken for a real bearer token and is safe to commit. The finding is the *shape* — a literal string where `${VAR}` belongs — not the value. The entry's `url` is `https://`, so the https-only half of item 9 is clean; defect 7 is the only item 9 finding in this fixture.

**Defect 8 is a silent-corruption bug, not a style note.** Native connectors are create-only; an in-place cell update duplicates rather than overwrites. An audit that flags step 7 only as "hardcoded cell reference" has missed the defect.

## Incidental observations — not planted, do not score

These follow from the fixture's deliberately minimal file set (`plugin.json`, two skills, `.mcp.json`, `README.md`) and are **not** among the eight. Treat a report of one of these as neither a hit nor a false positive.

- **No `CONNECTORS.md`.** The plugin references a CRM connector but ships no `CONNECTORS.md`, and neither skill carries the CONNECTORS banner line. The fixture's file set is fixed by the eval design; a banner pointing at a file that does not exist would have been a worse artifact than no banner.
- **Manifest `name` is `team-ops`, the directory is `imperfect-plugin/`.** The divergence is an artifact of the fixture path, not a checklist violation — item 13 explicitly expects packaging to use the manifest `name` when the two differ.
