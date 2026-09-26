---
lens: design
doc: /workshop/docs/superpowers/specs/2026-09-25-orko-review-design.md
---

# design review

## Verdict

ready with changes

## Findings

### F-1 [major] Reviewers can read sibling reports and earlier runs, which breaks the independence the skill exists to guarantee

- Where: Run directory; Reviewer contract and report format; Risks and mitigations ("The session primes a reviewer anyway")
- Evidence: The run layout puts every lens's report in one directory (`<reviews-dir>/<doc-stem>/<timestamp>/<lens>.md`), and earlier runs of the same doc sit in sibling timestamp directories with their reports and `decisions.md`. The contract tells each reviewer to "read the codebase" and forbids only editing. During this review I ran `find .` inside `docs/superpowers/reviews/` as ordinary orientation, and it listed the run directory and all three briefs. Had the other reports been written, the same command would have surfaced them. A re-dispatched reviewer (step 5) is guaranteed to find the other lenses' finished reports, plus its own predecessor's invalid report at the path it is told to write to.
- Problem: The Problem section's third cost is reviewer priming. The fixed dispatch sentence closes the session-to-reviewer channel but leaves the reviewer-to-reviewer and prior-run-to-reviewer channels open. The Risks table doesn't list this, and the live engagement can't detect it, because it checks only Agent prompts.
- Fix: Add a contract bullet: "Don't open anything under the reviews directory except your brief and your report path: not other reviewers' reports, not earlier runs, not `run.json`." Add it to Risks with that mitigation. In `check`, before a re-dispatch, move an invalid report to `<lens>.invalid-<n>.md` so the retry starts from an empty path. Optionally, the live engagement can grep each reviewer transcript for Read or Bash calls touching other `<lens>.md` files.

### F-2 [major] `check` detects a doc hash change but has no defined response, and there's no way to recover the original

- Where: Script `check`; SKILL.md step 5; Risks row "A reviewer edits the doc instead of the report"
- Evidence: `check` reports a hash change "as a `problem:` line". The spec doesn't say whether that exits 0 or 2. Step 5's only exit-2 action is "re-dispatch each lens it names", and a hash change names no lens. `run.json` stores only the SHA-256, not the content.
- Problem: As written, a reviewer that edits the doc leads to one of two outcomes. If exit is 0, `--apply` layers accepted edits on top of the unreviewed change. If exit is 2, the session loops on re-dispatch with no lens to re-dispatch. Either way the mitigation stops at detection, and the original text can only be recovered from git, which may not hold it because the doc is often uncommitted (the skill never commits).
- Fix: `start` copies the doc to `<run>/doc.orig.md`. On a hash mismatch, `check` prints `problem: doc changed since start (original: <run>/doc.orig.md)` and `STATUS: blocked`, and exits 3 (distinct from the per-lens exit 2). SKILL.md step 5: "On `STATUS: blocked`, report the problem lines and stop; don't apply."

### F-3 [minor] The `Change` column in the Accepted table has no data source

- Where: Script `summary` (Accepted table) vs `decide`
- Evidence: `summary` prints `| ID | Severity | Title | Change |` for accepted findings. `decide` takes only `--finding`, `--verdict`, and `--why`, and the report format's closest field is the reviewer's `Fix:`, which is a proposal, not the edit made.
- Problem: The planner must invent where `Change` comes from: `--why`, the reviewer's Fix, or a new flag. Each choice gives a different summary.
- Fix: Pick one and state it. Recommended: for `accept`, `--why` states the change made ("Change" column = `--why`), and the table header reads `| ID | Severity | Title | Change |` with that mapping written under `decide`.

### F-4 [minor] `decide` depends on "the index" after the doc has been edited, but the index isn't persisted

- Where: Script `decide` ("Refuses (exit 2) an ID not in the index"); `check`
- Evidence: The index is described only as `check`'s stdout. `check` also compares the doc hash. In `--apply`, the session edits the doc between `decide` calls.
- Problem: If `decide` or `summary` re-derive the index by re-running `check`'s logic, the hash comparison fails after the first accepted edit. The spec doesn't say which way it works.
- Fix: "`check` writes the findings index (ID, severity, title per finding) and the per-lens status into `run.json`; `decide` and `summary` read it from there and never re-validate reports or re-hash the doc."

### F-5 [minor] No path from a `--file-only` run to applying it

- Where: Goal (`--file-only`); `decide` ("Refuses … a run in `file-only` mode")
- Evidence: `decide` refuses file-only runs, and `/orko-review` takes only a doc path. oiler's quoted prompts include "pause when complete and report back here", which is the read-first-then-apply workflow `--file-only` serves.
- Problem: After reading a file-only run's reports, oiler's only way to get the scripted apply step is to rerun the whole battery: three to five more Opus-high reviewers, and the new reports differ from the ones he read. Otherwise he applies by hand with no disposition record.
- Fix: Either add `/orko-review --run <run-dir> --apply` (preflight validates the run and flips `mode` in `run.json`, then the session enters at step 7), or add a non-goal saying so explicitly: "Applying a file-only run later. Rerun `/orko-review`."

### F-6 [minor] The apply step has no rule for findings whose fix lives in another file

- Where: SKILL.md step 7; Goal ("edits the doc")
- Evidence: The plan `coverage` lens checks for "spec decisions the plan quietly reverses". Fixing that can mean editing the spec, not the plan. The `generic-consistency` lens reports contradictions with cited docs, and evergreen conflicts are deferred.
- Problem: `accept` means "make the edit", but it's unclear whether the session may edit a file other than the doc under review. The disposition record and the byte-identical and no-commit guarantees are all scoped to one doc.
- Fix: Add to step 7: "Edit only the document under review. A finding whose fix belongs in another file is `defer`, with `--why` naming the file."

### F-7 [minor] The `superpowers/` ancestor rule is unbounded

- Where: Decisions taken, "Reports directory"; preflight `reviews-dir:`
- Evidence: The rule says "nearest ancestor directory named `superpowers/`" with no stop. `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.4.1/skills/writing-plans/SKILL.md`, a file this spec itself cites, has a `superpowers` ancestor, so reviewing a doc there resolves to `.../claude-plugins-official/superpowers/reviews/` inside the plugin cache. The spec also never says how "repo root" is found (the evergreen and agent scans use it) or what happens outside a git repo.
- Problem: This is a small edge case, but reports land somewhere nobody looks, and the missing repo-root definition leaves the evergreen scan undefined for non-git docs.
- Fix: "Repo root = `git rev-parse --show-toplevel` from the doc's directory; outside a repo, the doc's directory. The `superpowers/` search stops at the repo root."

### F-8 [minor] The session-effort note arrives too late to act on

- Where: Decisions taken, "Session effort"; SKILL.md step 1
- Evidence: The note prints at preflight, inside the same turn that dispatches reviewers and applies findings. `MODELS.md` line 3 raises the session to high for "verification passes", and the Mechanics section says changing `/effort` doesn't break the cache.
- Problem: In `--apply` at medium, the verification pass runs below policy. The note tells oiler afterward, not before. The stated rationale (the apply step is a verification pass) is what the mitigation doesn't protect.
- Fix: Either accept this explicitly as a recorded tradeoff ("the note teaches; it doesn't gate") or, in `--apply` mode below high, have preflight print `STATUS: blocked` with the hint `/effort high, then rerun`, and let `--file-only` continue with the note. This is a product decision for oiler.

### F-9 [minor] The paths block, the one part of the brief the script composes, has no template

- Where: Script `start` ("A brief is, in order: a paths block …"); Verification hooks ("no other prose"); Determinism ledger (briefs = tier 1)
- Evidence: The brief the dogfood run produced for this review opens with `# Review brief: design`, a `## Paths` heading, and labeled bullets (`- Lens:`, `- Document under review:`, `- Evergreen docs:`, `- Write your report to:`). None of that text is in the spec. The contract refers to "the path under Paths" and "your lens name, from Paths", so the heading name is load-bearing.
- Problem: Tier 1 needs the template spelled out. Without it the planner invents the labels, and the contract's references to "Paths" may not match what `start` writes. The "no other prose" hook can't be tested against an undefined template.
- Fix: Put the verbatim template in the spec, the same one the dogfood briefs used, with the placeholders named. For example: `# Review brief: <lens>` / `## Paths` / `- Lens: <lens>` / `- Document under review: <abs path>` / `- Spec: <abs path>` (plans only) / `- Evergreen docs: <abs paths, or none>` / `- Write your report to: <abs path>`.

### F-10 [minor] The validator fixtures are fixed before the review that may change the format they test

- Where: Eval plan ("Fixtures (dogfood)"); Verification hooks ("Report validator accepts real reports")
- Evidence: The fixtures are this spec's own review reports, written against the drafted contract. The same review can produce accepted findings that change the report format or contract; this review changes nothing in the format, but the other lenses may.
- Problem: If an accepted finding changes the format, the "real report" fixtures no longer match the spec, and either the tests or the fixtures get hand-edited silently. The spec also names only passing fixtures, so `check`'s rejection behavior has no named fixtures.
- Fix: Add: "If an accepted finding changes the report format, the fixtures are regenerated or hand-edited and the edit is recorded in the plan. Negative fixtures (missing section, gap in F-numbers, empty Checked and sound, bad severity, `lens:`/`doc:` mismatch) are derived from a passing fixture, one mutation each."

### F-11 [nit] Non-negotiable #8 is cited for the wrong rule

- Where: Problem, last paragraph ("which non-negotiable #8 forbids")
- Evidence: Workshop `CLAUDE.md` #8: "any smoke test of a built skill runs in a subagent that has read only the skill's shipped files". That rule is about smoke tests of built skills, not doc reviews. The closer sources are `MODELS.md` line 11 ("Independence comes from a fresh context, not a different model") and the workshop memory rule "never prime a re-dispatched verifier with the prior pass's conclusions".
- Problem: Citing #8 stretches it and invites the "don't relitigate" framing onto a rule that doesn't say this.
- Fix: Replace it with: "which defeats the fresh-context independence that `MODELS.md` names as the point of spec and plan review."

### F-12 [nit] `summary`'s file-only output is specified but never used

- Where: Script `summary` ("In `file-only` mode, `summary` prints only `## Reviewed` and the findings index") vs SKILL.md step 6
- Evidence: Step 6 prints `check`'s findings index and stops. No step runs `summary` in file-only mode.
- Problem: It's a behavior with no caller, and it needs a test anyway.
- Fix: Either have step 6 run `summary` (which also gives file-only runs the `## Reviewed` header with run dir and lenses), or drop the file-only branch of `summary` and have it exit 2 on a file-only run.

### F-13 [nit] Goal's file-only bullet says the session writes the reports

- Where: Goal, `--file-only` bullet ("the session writes the reports")
- Evidence: Everywhere else the reviewers write the reports ("each write a full report", step 4, ledger "Reviewer writes").
- Problem: This contradicts the mechanism and could be read as allowing the session to write reports.
- Fix: "The reviewers write their reports; the session prints the findings index and stops without touching the doc."

### F-14 [nit] The `-design.md` rule classifies "design docs" as specs, but the Decisions table lists "design doc" as generic

- Where: Doc-type detection rule 2 vs Decisions taken, "Doc types" ("`generic` (any other doc: OBJECTIVE.md, roadmap, design doc)")
- Evidence: Rule 2 maps any `*-design.md` to `spec`.
- Problem: A project design doc named `auth-design.md` gets spec lenses, while the Decisions row says design docs are generic.
- Fix: Change the Decisions example to "OBJECTIVE.md, roadmap, `DESIGN.md`", or state that `*-design.md` follows the superpowers spec naming and is deliberately treated as a spec.

### F-15 [nit] The mapping from lens name to lens file is implied, not stated

- Where: File structure (`spec-design.md`, `extra-security.md`) vs Lenses table and `--extra <lens>` (`design`, `security`)
- Evidence: Report files, `lens:` frontmatter, and finding IDs use the bare name (this run: `design.md`, `lens: design`). Files carry a `<type>-` or `extra-` prefix.
- Problem: It's small, but the planner has to infer the mapping and the uniqueness rule (no specialist name may equal a core name).
- Fix: One sentence under Lenses: "A lens's name is its filename without the `<type>-`/`extra-` prefix and `.md`; names are unique across the core set of a type and the specialist catalog."

## Checked and sound

- Goal-to-mechanism trace. Fixed battery: core lenses per type plus a validated specialist catalog. Script-owned report path: reviews-dir resolution plus the run directory. No priming from the session: the script-assembled brief and the fixed one-sentence prompt (see F-1 for the remaining channel). `--apply` and `--file-only`: steps 6–8 with `decide` and `summary`. Each of the three costs in the Problem section has a delivering mechanism.
- The reports-dir rule gives the locations the Problem cites: `planning/reviews/` and a per-version `reviews/` folder. This dogfood run resolved to `docs/superpowers/reviews/2026-09-25-orko-review-design/2026-09-25-195039/`, as rule 1 predicts.
- Simpler alternatives considered. A SKILL.md-only version with brief templates the session fills in would drop the script but reopen the priming channel and conflict with the workshop's "Determinism first" rule (workshop `CLAUDE.md`). Dropping `decide`/`summary` in favor of a model-written disposition table would lose the "refuse an incomplete set" check that mitigates rubber-stamping. The script's five subcommands each serve a stated goal; I found no part that serves none.
- The reviewer model and effort decisions match the on-disk `~/.claude/MODELS.md`. Line 3 sets the session at medium, raised to high for spec and plan work. Rows 11 and 14 set spec and plan review to Opus 5.5 high with fresh context. Mechanics: "Subagents without an `effort:` in their definition inherit the session level at dispatch". So pinning `effort: high` in the agent file is required, as the spec says.
- The drafted agent file (`orko-review/agents/orko-review-reviewer.md`) matches the spec's Agent section word for word, and the agents-dir symlink pattern matches the existing `~/.claude/agents/orko-sdd -> …/orko-sdd/agents`.
- The contract complies with the global CLAUDE.md reviewer rule. It says "Report every finding … Don't filter", and nothing tells reviewers to be conservative.
- Keeping CLAUDE.md loaded for reviewers is the right call: the document-authority table and "accuracy over agreement" are review rules.
- The one-round, no-commit, and slash-only non-goals are consistent with the steps (step 8 stops, no step commits, `disable-model-invocation: true`).
- Specialist selection reintroduces some session judgment, but the cap of two, the required reason, and recording in `run.json` bound the "focus changes with the wording of the day" cost the Problem section names.
- The live-engagement design uses planted defects, a `--effort medium` operator, and a byte-identical plan check for file-only. Together these exercise the effort pin, the dispatch-prompt rule, the evergreen-conflict defer, and the file-only guarantee.
- `Recommended` goes last, after the verbatim script output, which is consistent with the orko-sdd precedent (`orko-sdd/SKILL.md:161`).
