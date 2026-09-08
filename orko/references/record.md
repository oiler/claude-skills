# The record

## What the record is

The scaffold's `docs/` repository is the record. A run's decisions live there as spec, plan, review, decision, and research files inside `versions/<MAJOR.MINOR>/`, indexed by the version README, and summarized by `STATUS.md`. A week after the run ends, someone with no session history reads those files and knows what you decided and why. The run directory at `<workspace>/.orko/<slug>/` is scratch: findings, `tasks.md`, PR bodies, and the ledger. It is not the record and it is not committed.

orko drafts and never signs. Every artifact you mint starts at `draft`, every decision starts at `proposed`, and every human field is left `null`. Only a named human sets `accepted`, `waived`, `released`, `approved_by`, `approved_at`, or `decided_at`, and the script gives you no flag to set one. The script also owns the write. You never hand-edit a record's frontmatter, its row in the version README artifact index, or an `### F<n>` block skeleton; those are the script's output, and editing them by hand desynchronizes the ledger's hash and trips the overwrite guard on the next `record` call. You write bodies: the spec's requirements, the review's synthesis sections, and the research note's findings.

Every script call in this file is written as `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py <subcommand>`. If `${CLAUDE_SKILL_DIR}` is empty in your Bash call, use `~/.claude/skills/orko/scripts/orko.py`. Never use shell command substitution: the prefix matching behind `allowed-tools` cannot see through it, and the resulting permission prompt is invisible inside a long run. Where a command needs a value another command produces, run two commands: read the value, then pass it.

## The record table

One row per orko event. `<slug>` is the run slug from `init`, `<v>` is the active version.

| orko event | Record | Repository | Status | Human field | Command |
|---|---|---|---|---|---|
| Build intake | `STATUS.md` In progress line; version README index row per minted ID | `docs/` | n/a | none | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py init build "<topic>" --workspace <path> --owner <name> --boundaries "<text>"` |
| Spec drafted | `versions/<v>/specs/SPEC-NNN-<slug>.md` | `docs/` | `draft` | `approved_at` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record spec --slug <slug> --title "<title>"` |
| Spec review round | `versions/<v>/reviews/REVIEW-NNN-<slug>-spec.md`, `reviews:` naming `SPEC-NNN`, `revision:` the `docs/` commit reviewed | `docs/` | `draft` | `approved_by` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record review --slug <slug> --title "<title>" --role spec --reviews SPEC-NNN --revision <sha> --from-findings findings/2` |
| Plan drafted | `versions/<v>/plans/PLAN-NNN-<slug>.md`, `implements:` naming `SPEC-NNN` | `docs/` | `draft` | none | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record plan --slug <slug> --title "<title>" --implements SPEC-NNN` |
| Plan review round | `REVIEW-NNN-<slug>-plan.md`, `reviews:` naming `PLAN-NNN` | `docs/` | `draft` | `approved_by` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record review --slug <slug> --title "<title>" --role plan --reviews PLAN-NNN --revision <sha> --from-findings findings/4` |
| Gate handoff | spec and plan set to `in_review` | `docs/` | `in_review` | spec `accepted` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record status --slug <slug> --id SPEC-NNN --status in_review` |
| Implementation | commits on `orko/<slug>` citing `SPEC-NNN` and `PLAN-NNN`; testing rows written by the implementer | `code/` | n/a | none | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit code --slug <slug> --message "<subject>"` |
| Post-gate behavior change | dated entry under the spec's `## Amendments` | `docs/` | unchanged | none | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record amendment --slug <slug> --id SPEC-NNN --text "<text>"` |
| Code review round | `REVIEW-NNN-<slug>-code.md`, `reviews:` naming `SPEC-NNN`, `revision:` the `code/` commit | `docs/` | `draft` | `approved_by` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record review --slug <slug> --title "<title>" --role code --reviews SPEC-NNN --revision <sha> --from-findings findings/6` |
| Escalation, product | `docs/decisions/DEC-NNN-<slug>.md` and the decisions index row | `docs/` | `proposed` | `decided_at` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record decision --slug <slug> --title "<title>"` |
| Escalation, technical | `code/docs/adr/ADR-NNN-<slug>.md`, from the fenced template in the ADR README | `code/` | `proposed` | `decided_at` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record adr --slug <slug> --title "<title>"` |
| Escalation, delivery | a row in the plan's Delivery decisions table, `Approved by` empty | `docs/` | inherits plan | `Approved by` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record delivery-decision --slug <slug> --decision "<decision>" --rationale "<why>"` |
| Deferred code-review finding | the finding stays `Disposition: open`, plus a bullet under the version README's Risks, blockers, and open decisions | `docs/` | n/a | none | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record risk --slug <slug> --text "<text>"` |
| Close | `STATUS.md`, both `CHANGELOG.md` files, the version README index, two PR bodies in the run directory | both | n/a | none | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record close --slug <slug> --summary "<text>" --changelog "Added: <text>"` |
| Analysis of an artifact or revision | `REVIEW-NNN-<slug>.md` in the active dossier | `docs/` | `draft` | `approved_by` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record review --slug <slug> --title "<title>" --role analysis --revision <sha> --from-findings findings/<step>` |
| Analysis of an open question | `docs/research/<date>-<slug>.md`, stamped as AI-generated plus unverified | `docs/` | n/a | none | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record research --slug <slug> --title "<title>"` |

Close does not move the work to Recently completed. `RELEASE.md` places that after the tag, which orko does not cut.

`record spec`, `record plan`, `record review`, `record decision`, `record adr`, and `record research` print JSON with `id`, `type`, `role`, `path`, and `resumed`. Read the path from that JSON. Never construct one. A second mint of the same type and role for a slug returns the record that already exists with `resumed: true`, so a rerun after an interruption is a no-op rather than a duplicate ID.

## Frontmatter orko writes

Per the type's template, `record` fills `id`, `title`, `status`, `product_version` equal to the dossier folder, `owner` from intake, `reviewer: orko (<seat list>)`, `reviewed_at` as the run date, `revision`, and `supersedes: null`. The plan's `owner` is the intake owner too: the scaffold's engineering owner and orko's intake owner are the same person in this use.

Every human field is written as `null` and the script has no flag to set it: `approved_by`, `approved_at`, and `decided_at`. `accepted_by` and `accepted_at` belong to `ACCEPT-NNN`, which orko does not write at all. The template's bracketed placeholders in `id` and `title` are replaced at mint, and the seeded placeholder row in the version README artifact index is replaced by the first minted row rather than left above it.

## Block sequences

Frontmatter ID lists are YAML block sequences, one `- SPEC-001` per line. This is not a style preference. `spec-check.sh` line 80 and `release-check.sh` lines 74 and 81 find a plan or a review by `grep -E '^[[:space:]]*- SPEC-NNN$'`. A flow list such as `implements: [SPEC-001]` matches nothing.

The failure is silent. `spec-check.sh` reports a warning rather than a failure and then skips every mapping check, so a spec with a flow-list plan passes with no requirement mapping verified at all. `record plan` and `record review` write block sequences. Do not reformat one by hand, and do not accept a reviewer's suggestion to compact one.

## The review collision

`release-check.sh` selects one review per implemented spec: the first file under `reviews/` whose block list names the spec, chosen with `head -1` at line 81, and it requires `approved_by` on that file. orko mints the spec review before the code review, so the spec review is the file that gets selected.

That is why the gate asks the human to approve the spec review and the plan review as well as accept the spec. It is consistent with the scaffold, because a review's dispositions are proposals until a human sets `approved_by`. It is also a scaffold fragility worth a follow-up: `release-check.sh` could check every review that names the spec rather than the first. Report it to oiler at the gate. Do not change the scaffold's scripts from inside a run.

## Findings to F blocks

Reviewer findings map one-to-one onto the review template's `### F<n>` blocks. Each seat writes its findings file in the schema `references/seats.md` defines, with a per-finding block:

```markdown
#### F1 — <title>
- Severity: blocking|high|medium|low|note
- Evidence: <file:line or tool result>
- Requirement: <SPEC-NNN R<n>, policy, or principle>
- Impact: <consequence>
- Recommendation: <concrete edit>
```

`Verdict` and `Confidence & gaps` stay seat-level and feed the review's Summary and Unresolved risks. The verifier's `Verified F<n>: <one line>` is appended to that finding's Evidence.

`record review --from-findings <dir>` reads every findings file in the directory and renders one `### F<n>` block per finding, numbered across seats in the order you name them with `--seat` (repeatable). Name every seat, in the order you want the findings to read. When you name none, the script orders files lexically by stem, which is the seat names' alphabetical order and rarely the order you want.

Every rendered finding starts at `Disposition: open`. You set each one:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record disposition --slug <slug> --review REVIEW-NNN --finding F3 --disposition accepted
```

The disposition is `accepted`, `rejected`, or `resolved`, and the command sets exactly one open finding. A second disposition of the same finding exits `2`: the record of what you decided is written once. A disposition is a proposal, not an approval. It has no effect until a human sets `approved_by` on the review.

In a spec or plan review, apply each accepted disposition to the draft artifact directly. `CHANGE-CONTROL.md` permits editing a draft. Then re-run `check spec`.

## Routing a change after acceptance

Once the human accepts the spec, a choice you make during implementation is routed by what kind of choice it is, per `docs/templates/plan.md` line 31 and `CHANGE-CONTROL.md`:

| The change | Record | Command |
|---|---|---|
| Externally observable behavior the accepted spec does not define | dated amendment on the spec | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record amendment --slug <slug> --id SPEC-NNN --text "<text>"` |
| A product-scope question | `DEC-NNN` in `docs/decisions/` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record decision --slug <slug> --title "<title>"` |
| A choice with long-lived architectural consequence | `ADR-NNN` in `code/docs/adr/` | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record adr --slug <slug> --title "<title>"` |
| Everything else | a Delivery decisions row in the plan | `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record delivery-decision --slug <slug> --decision "<decision>" --rationale "<why>"` |

`record amendment` appends a dated line inside the spec's `## Amendments` section. `record delivery-decision` appends a table row with `Approved by` empty, which the plan template says inherits the plan's status. `record risk` appends a bullet under the version README's Risks, blockers, and open decisions heading.

Every one of these four is an escalation. Write the escalation into `<run_dir>/escalations.md` yourself. Name the record ID. State the decision you need. Then stop the run. `escalations` exits `1` while that file is non-empty, and `preflight` reports `blocked-escalation` until oiler empties it. An amendment is the only one you may take without a human when the boundaries recorded at intake already authorize the behavior; even then, record it and report it.

## Commits

Each repository is committed separately, and the script owns the staged set:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "<subject>"
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit code --slug <slug> --message "<subject>"
```

`commit docs` stages the run's own record paths in `docs/` plus every `touched` path the `record` commands logged there: `STATUS.md`, the version README, the changelog. `commit code` does the same for `code/`. Add an extra repo-relative path with `--path` (repeatable) when a run wrote something outside the record, such as `docs/adr/` files in the code repository. Nothing else is staged, and the commit is scoped to those paths, so a file the user had already staged in that repository stays staged rather than riding along under orko's message.

The message the script builds is your `--message` subject, then a `Refs:` line naming every ID the run has minted, then the attribution trailers recorded at `init --trailer` (repeatable), verbatim. After the commit, the script records a `hash <path> <sha256>` ledger line for every file it staged.

Those hash lines are the overwrite guard. `record` refuses to write a file when all three hold: a hash is recorded for that path, the file exists, and its current sha differs from the recorded one. That means a human edited a record orko wrote. Read the change, report it, and continue from the human's version rather than overwriting it. The gate's expected edit is exempt: `preflight` re-records the spec's hash at step 5 when it confirms `status: accepted`, so the human's acceptance is not reported as tampering on the next write.

Git calls you make yourself use `git -C docs` and `git -C code`, never a bare `git` from the workspace root. The workspace root is not a repository.

## Close and what stays human

`record close --summary "<text>"` with zero or more `--changelog "<section>: <text>"` entries, where `<section>` is `Added`, `Changed`, `Fixed`, `Removed`, or `Security`:

- Sets `STATUS.md` `as_of` and rewrites the run's In progress line to "awaiting acceptance".
- Inserts each changelog entry under its subheading in the Unreleased section of both `code/CHANGELOG.md` and `docs/versions/<v>/CHANGELOG.md`. Changelog and STATUS lines cite only the SPEC and PLAN IDs: a reader asking what shipped is not served by a review or decision ID.
- Refreshes the version README index Status column from each record's current frontmatter.
- Writes `<run_dir>/pr-docs.md` and `<run_dir>/pr-code.md` from each repository's `.github/PULL_REQUEST_TEMPLATE.md`, with the summary under Purpose and every minted ID listed under Artifacts.

It is idempotent, so a rerun after an interruption is safe. Then run `commit docs`, `commit code`, and `gh pr create --body-file <run_dir>/pr-<repo>.md` in each repository. If `gh` is missing or unauthenticated, the body files are already written: report their paths and the two commands for the human to run.

What stays human after close: `approved_by` on the code review, `ACCEPT-NNN`, the release record, and the tag. Report all four. `RELEASE.md` places the move to Recently completed after the tag, and orko performs none of those post-tag steps.

## Reconstruction

A lost run directory does not lose the record. Everything that matters is committed in `docs/` and `code/`: the spec, the plan, every review with its dispositions, the decisions, the index rows, and `STATUS.md`. Only scratch is gone.

To pick a run back up, `cd` to the workspace root and run:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py status
```

It prints the header, `next_step`, `next_task`, and every record the ledger knows with its path and last committed hash. A resume with the same topic re-derives the same slug, and each `record` command re-finds the run's existing record of that type and role in the ledger and returns it with `resumed: true` rather than minting a duplicate ID.

If the ledger is gone as well, do not re-mint. Read the committed records in `docs/versions/<v>/` and the version README index, which together say exactly what the run produced, and report to oiler what is left to do before starting anything new.
