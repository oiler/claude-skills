---
lens: completeness
doc: /workshop/docs/superpowers/specs/2026-09-25-orko-review-design.md
---

# completeness review

## Verdict

ready with changes

## Findings

### F-1 [major] "Lens" name has two meanings: short name vs. file stem

- Where: File structure (lines 107-120), Lenses table (lines 149-164), Run directory (`<lens>.md`, line 225), Eval plan (line 340), `start --extra <lens>` (line 268), finding ID `<lens>/F-<n>` (line 217)
- Evidence: Lens files are named `spec-accuracy.md`, `extra-security.md`; the table and the brief this reviewer received use the short name (`completeness`, report path `.../completeness.md`). The Eval plan says the session "dispatches `spec-accuracy`, `spec-completeness`, and `spec-design` reviewers". The catalog in preflight's `extras-available:` could print either `security` or `extra-security`.
- Problem: A planner can't tell which string is the lens identity used in `run.json`, report filenames, the report's `lens:` front matter, `--extra` arguments, and `<lens>/F-<n>` IDs. `check`'s `lens:` binding and `decide`'s ID validation both depend on it.
- Fix: Add one sentence under Lenses: "A lens's name is the file stem without its `spec-`/`plan-`/`generic-`/`extra-` prefix (`accuracy`, `security`). That name is used everywhere: `run.json`, `briefs/<name>.md`, `<name>.md`, the report's `lens:` line, `--extra <name>`, and finding IDs `<name>/F-<n>`." Change the Eval plan's "`spec-accuracy`, `spec-completeness`, and `spec-design` reviewers" to "the three `spec` lenses".

### F-2 [major] "Repo root" is used throughout but never defined

- Where: Decisions table, Reports directory (line 51); Doc-type detection (line 177); preflight `evergreen:` and `agent:` (lines 264, 266)
- Evidence: "repo root" appears in reports-dir resolution, `**Spec:**` resolution, evergreen discovery, and agent discovery; no rule says how it is found, whose repo it is (the doc's or the cwd's), or what happens outside a git repo. This review's own run shows the two can differ: the doc lives in the workshop repo while the reviewer's cwd is the `claude-skills` worktree.
- Problem: A planner must invent the resolution (for example `git -C <doc-dir> rev-parse --show-toplevel`) and the no-repo fallback; two plausible readings (doc's repo vs. cwd's repo) produce different evergreen lists and different `**Spec:**` resolutions.
- Fix: Add to Doc-type detection or a new "Path resolution" paragraph: "Repo root is `git -C <doc's directory> rev-parse --show-toplevel`. If the doc isn't in a git repo, repo root is the doc's directory; evergreen discovery then checks only that directory, and the agent scan checks only `~/.claude/agents/` and `<cwd>/.claude/agents/`." Say whether a relative `<doc-path>` resolves against the cwd.

### F-3 [major] `superpowers/` ancestor search is unbounded

- Where: Decisions table, Reports directory (line 51)
- Evidence: The rule is "Nearest ancestor directory named `superpowers/`". The superpowers plugin itself lives at `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.4.1/…`, so any doc under that tree resolves to a `reviews/` directory inside the plugin cache. A project nested under any directory named `superpowers` would likewise write outside its own repo.
- Problem: The search can escape the project and write reports into an unrelated tree.
- Fix: "Nearest ancestor directory named `superpowers/`, searching no higher than the repo root (F-2)".

### F-4 [major] Rule 3 of doc-type detection matches a quoted `**Spec:**`, not only a header line

- Where: Doc-type detection, rule 3 (line 174)
- Evidence: This spec's own line 13 contains `` `**Spec:**` `` inside a table cell within its first 40 lines. It is caught earlier by rules 1 and 2, but a generic doc or a spec outside `specs/` without a `-design.md` suffix that quotes the header would be typed `plan`, then blocked because its "spec" doesn't resolve.
- Problem: "contain a `**Spec:**` line" has two readings: a line that contains the token anywhere, or a line that starts with it. The first misclassifies.
- Fix: "3. One of the first 40 lines starts with `**Spec:**` (after optional leading whitespace or `- `) → `plan`." Use the same match for the resolution step, and say the first matching line wins (the workshop's `2026-05-26-wordpress-themes-v0.2-refresh.md` has `Spec:` on lines 13, 891, and 1030).

### F-5 [major] `**Spec:**` value extraction ("strip backticks and surrounding text") is underspecified

- Where: Doc-type detection, resolution paragraph (line 177)
- Evidence: `grep -n "Spec:" docs/superpowers/plans/*.md` shows values such as `` `docs/.../2026-05-26-wordpress-themes-v0.2-design.md` (in oiler/001-claude-skills-creator) `` and `https://agentskills.io/specification`, and older plans that use `- Spec:` or `Spec:` without bold (`2026-05-26-python-skill-refresh.md:14`, `2026-05-26-wordpress-blocks-refresh.md:14`). The writing-plans template itself contains placeholder text `[path to the spec/design doc …]`.
- Problem: "Surrounding text" isn't defined, so a planner can't write the extractor or its tests. Older non-bold plans in a `plans/` directory are typed `plan` by rule 1 but will always block; the spec doesn't say whether that is intended.
- Fix: Define the extraction: "If the value contains a backtick-quoted span, take the first one; otherwise take the first whitespace-delimited token. Values that start with `http` are unresolvable." State that plans with a non-bold `Spec:` line block with the `--spec` hint by design, and add that case to the verification-hooks tests.

### F-6 [major] `check`'s format rules are incomplete

- Where: Reviewer contract and report format (lines 189-217); `check` (line 274)
- Evidence: The only stated rules are: `None.` allowed, four severities, non-empty `## Checked and sound`, gapless `F-n` IDs, `lens:`/`doc:` match. Not stated: whether the verdict must be one of the three values; whether each finding must carry all four `Where/Evidence/Problem/Fix` bullets; whether extra sections or text before `## Verdict` are allowed; whether `None.` with verdict `not ready` is valid; how headings are matched (exact text, case).
- Problem: The validator is the tier-3 control on reviewer output; a planner will either under-validate or reject valid reports. The real-report fixtures can't settle rules the spec never states.
- Fix: Add a "Validation rules" list under the format block: required front matter keys; required sections in order; verdict exactly one of the three strings; each `### F-n [sev] title` followed by exactly the four labeled bullets, each non-empty; title non-empty and single-line; other content is ignored (or rejected — pick one).

### F-7 [major] Doc-hash change in `check`: exit code and session response undefined

- Where: `check` (line 274); Risks table, first row (line 348)
- Evidence: "a change means a reviewer (or someone) edited the doc, reported as a `problem:` line." Nothing says whether this is exit 2 (retry) or exit 0 with a warning, which lens is blamed, or what SKILL.md step 5/7 does about it.
- Problem: The risk's mitigation is "`check` detects the hash change", but detection without a defined consequence is untestable and the session may proceed to apply findings against a doc a reviewer altered. A retry can't fix it because re-dispatch doesn't restore the doc.
- Fix: Decide and state: "A hash change makes `check` exit 3 with `problem: doc changed since start`; SKILL.md tells the session to stop and report it (no apply, no retry), because the reviews may describe a different text." Add the step to SKILL.md content and a test.

### F-8 [major] The `Change` column in `## Accepted` has no source

- Where: `summary` output (line 294); `decide` (line 282)
- Evidence: `decide` takes only `--finding`, `--verdict`, and `--why`. The Accepted table has a `Change` column; Rejected and Needs you have `Why`.
- Problem: `summary` is tier 1 but has no recorded data for `Change`. A planner will either render `--why` there (then the column name is wrong) or add a flag the spec doesn't define.
- Fix: Either rename the column to `Why` and state that for `accept`, `--why` describes the edit made, or add `--change '<one line>'` required when `--verdict accept`, and add it to SKILL.md step 7 and the allowed behavior of `decide`.

### F-9 [minor] `check` retry counter counts `check` calls, not dispatches

- Where: `check` (line 280); SKILL.md step 5 (line 239)
- Evidence: "Exit 2 … records a retry count in `run.json`; on a lens's second failure, `check` marks it `failed`." Nothing ties the count to a re-dispatch.
- Problem: If the session runs `check` twice without re-dispatching (or runs it before all reviewers returned), a lens is marked `failed` with no retry. Also unstated: whether a `failed` lens can recover if its report later appears.
- Fix: State that the second failing `check` marks the lens `failed` regardless, that SKILL.md must re-dispatch between calls, and that a `failed` lens is final for the run (its later report is ignored). Or record the dispatch count via `start`/a subcommand; pick one.

### F-10 [minor] File-only output: `check` index or `summary`?

- Where: Goal (line 32); SKILL.md step 6 (line 240); `summary` (line 303)
- Evidence: Step 6 says print `check`'s findings index and the run directory, and stop. `summary` defines a file-only form ("only `## Reviewed` and the findings index") that no step calls.
- Problem: Two outputs for one step; the file-only `summary` form is dead code or the step is wrong, and a test for it has no user.
- Fix: Change step 6 to "run `summary --run <run-dir>`, paste its output unchanged, and stop", or delete the file-only form from `summary`.

### F-11 [minor] Failed lenses have no row format in `## Needs you`

- Where: `summary` (line 303)
- Evidence: "`Needs you` holds the deferred findings and any `failed` lens." The table columns are `ID | Severity | Title | Why`; a lens has no ID, severity, or title.
- Problem: The planner must invent the row.
- Fix: Specify it, for example `| <lens>/— | — | lens failed twice | <check's last failure reason> |`, or print failed lenses as a separate `failed-lenses:` line under the table.

### F-12 [minor] Edge cases in indexing and output not covered

- Where: `check` index (lines 276-280); `summary` (lines 288-301)
- Evidence: Titles are free text; the index and summary are markdown tables. "Sorted by … lens" doesn't say alphabetical or `run.json` order. No behavior is stated when every lens fails (empty index) or when all reports say `None.`
- Problem: A `|` in a title breaks the table; the sort order is untestable as written; the all-failed run has no defined outcome (apply over nothing, or stop).
- Fix: "Escape `|` in titles. Lens order is the order in `run.json` (core lenses first, then extras). If every lens is `failed`, `check` exits 2 with `problem: no valid reports` and the session stops."

### F-13 [minor] `decide` preconditions are incomplete

- Where: `decide` (line 284)
- Evidence: "Refuses … an ID not in the index." The index is printed by `check`; it isn't said to be stored.
- Problem: If `decide` runs before a successful `check`, "the index" doesn't exist; if `decide` re-parses reports, it can accept IDs from a lens `check` marked `failed`.
- Fix: "`check` stores the index in `run.json` on exit 0. `decide` and `summary` refuse (exit 2) when no stored index exists, and validate IDs against it."

### F-14 [minor] Scope of edits in apply mode is unstated

- Where: Goal (line 31); SKILL.md step 7 (lines 241-245)
- Evidence: "edits the doc". A plan's `coverage` finding may say the spec is wrong; an evergreen conflict may call for updating the stale evergreen doc (global CLAUDE.md, Document authority: "likely update the stale evergreen doc").
- Problem: Two readings: the session edits only the reviewed doc, or whatever file the finding's fix names.
- Fix: Add to Non-goals: "Editing any file other than the reviewed doc. A finding whose fix lands elsewhere (the spec, an evergreen doc) is `defer`."

### F-15 [minor] `--spec` on a non-plan doc and `--extra`/`--why` pairing unstated

- Where: preflight and `start` signatures (lines 254, 268)
- Evidence: `--spec` is described only for plans. `--extra` and `--why` are repeatable, independent flags.
- Problem: Whether `--spec` on a spec or generic doc is blocked, ignored, or added to the paths block is open. Pairing of repeated `--extra`/`--why` (by position) isn't stated, so `--extra a --extra b --why x --why y` has two readings.
- Fix: "`--spec` on a non-plan doc blocks with `problem: --spec applies only to plans`. Each `--extra` must be immediately followed by its `--why`; otherwise `start` exits 2."

### F-16 [minor] Brief paths block and preflight `problem:` lines have no defined format

- Where: `start` (line 270); SKILL.md step 1 (line 235); preflight (lines 256-266)
- Evidence: The brief is "a paths block … the lens file verbatim, and `reviewer-contract.md` verbatim", and the verification hook says "no other prose". The brief this reviewer received opens with `# Review brief: completeness` and a `## Paths` list with labeled keys (Lens, Document under review, Evergreen docs, Write your report to), none of which the spec defines. SKILL.md step 1 says to report "the `problem:` lines", but preflight's output list never mentions a `problem:` key.
- Problem: Tier-1 surfaces with no specified shape; the concatenation test can't be written without inventing the header and keys. The `evergreen:` line with several docs has no stated separator.
- Fix: Add the paths-block template verbatim (as in the brief used for this review), and state: "each blocking condition prints `problem: <text>` and, where one exists, `hint: <text>`; `evergreen:` lists paths comma-separated."

### F-17 [minor] Non-markdown docs, paths with spaces, and same-second runs

- Where: Run directory (line 229); preflight `doc:` (line 258); Risks table, `$ARGUMENTS` row (line 354)
- Evidence: `<doc-stem>` is "the doc filename without `.md`"; preflight blocks on "anything but one positional"; the run directory is timestamped to the second.
- Problem: A `.txt` or `.rst` doc has no defined stem (or should be blocked). A path with spaces splits into two positionals and blocks with no explanation. Two runs in the same second collide, contradicting "earlier reports are never overwritten".
- Fix: "Preflight blocks docs not ending in `.md`. Paths with spaces are unsupported (recorded under Risks). `start` refuses (exit 2) if the run directory already exists."

### F-18 [minor] "Below `high`" needs an ordering and an unset case

- Where: Decisions table, Session effort (line 54); SKILL.md step 1 (line 235)
- Evidence: The note fires "when it is below `high`". No ordering of effort values is given, and nothing covers `${CLAUDE_EFFORT}` being empty or not substituted.
- Problem: The live-engagement check at `--effort medium` covers one value only; `xhigh`/`max` and the unsubstituted case are open.
- Fix: "Order: low < medium < high < xhigh < max. If the value is empty or still reads `${CLAUDE_EFFORT}`, say the effort is unknown and continue."

### F-19 [minor] Re-applying a file-only run is neither supported nor a non-goal

- Where: Goal (lines 31-32); `decide` refuses file-only runs (line 284); Non-goals (lines 34-40)
- Evidence: oiler can run `--file-only`, read the reports, and then want them applied. `decide` refuses a file-only run, so the only path is a new review.
- Problem: A planner could reasonably add a "promote to apply" path, or oiler could expect one.
- Fix: Add to Non-goals: "Applying an earlier run's reports. To apply, rerun `/orko-review` in apply mode."

### F-20 [minor] Machine-wide activation skips the ask required by the project CLAUDE.md

- Where: Release plan (line 358)
- Evidence: Project CLAUDE.md, "When oiler asks to do skill work" step 5: "For any **new** skill, ask whether to symlink it into `~/.claude/skills/<name>`". The spec says "machine-wide activation (skill and agent; daily-use, so yes by default)" and lists only "Merge, push, and tag" as needing confirmation.
- Problem: Evergreen conflict (small): the release plan pre-answers a question the evergreen doc says to ask.
- Fix: "Machine-wide activation (skill and agent): recommend yes (daily-use); ask oiler per CLAUDE.md step 5. Merge, push, tag, and activation need oiler's confirmation."

### F-21 [nit] `**Spec:**` line citations point at line 9; the lines are 11

- Where: Platform facts (line 71)
- Evidence: `grep -n "Spec:"` prints `2026-09-25-orko-sdd-v0.1.1.md:11`, `2026-09-22-orko-sdd.md:11`, `2026-08-26-design-sys.md:11`; the spec cites `:9` for all three.
- Problem: Receipts don't re-check; the fixtures step copies from these lines.
- Fix: Change `:9` to `:11` in all three citations.

### F-22 [nit] Contract bullets in the spec omit the reply line the contract file carries

- Where: Reviewer contract and report format (lines 181-187)
- Evidence: `references/reviewer-contract.md` ends "then reply with one line: the report path"; the spec's summary of the contract doesn't mention the reply, nor that the contract also carries the severity definitions.
- Problem: The spec and the drafted file disagree on what the contract contains; the planner reading only the spec won't know the severity definitions are part of it.
- Fix: Add two bullets: the severity definitions (blocker/major/minor/nit, as in the file) and "reply with one line: the report path".

### F-23 [nit] Non-negotiable #8 is stretched to cover reviewer priming

- Where: Problem (line 25)
- Evidence: Project CLAUDE.md #8: "Verification is clean-room or it's theater — any smoke test of a built skill runs in a subagent that has read only the skill's shipped files". It governs smoke tests of built skills, not doc reviews.
- Problem: The term is used with a second meaning; the principle is right but the citation isn't.
- Fix: "…so it can prime reviewers with its own conclusions, the same failure non-negotiable #8 guards against in skill smoke tests."

## Checked and sound

- The drafted agent file (`orko-review/agents/orko-review-reviewer.md` in the worktree) matches the spec's Agent block verbatim: `effort: high`, `disallowedTools: Agent`, same body.
- The worktree's `references/lenses/` holds exactly the 14 lens files the File structure lists, with matching names.
- The brief this reviewer received follows the stated order: paths block, lens bullets, contract verbatim (the contract section matches `references/reviewer-contract.md`).
- `~/.claude/MODELS.md` line 3 says the session default is Opus 5.5 at medium, "raised to high for spec and plan work, brownfield bug fixes, and verification passes", matching the spec's Effort control and Session effort rows.
- `superpowers/6.4.1/skills/writing-plans/SKILL.md:69` carries the `**Spec:** [path to the spec/design doc …]` header line as cited.
- `docs/skill-reference.md:87` confirms a nonzero `!` command aborts the invocation, supporting "preflight always exits 0".
- Reports-dir resolution for this spec (`docs/superpowers/specs/…`) lands in `docs/superpowers/reviews/`, which is where this run's directory is; the `<doc-stem>/<timestamp>/briefs/` layout matches the Run directory section.
- Non-goals cover rounds, commits, code review, auto-invocation, and changes to orko-sdd/orko, and SKILL.md step 8 restates the no-second-round and no-commit rules.
- Every tier-4 surface in the Determinism ledger carries a waiver, as the Spec checklist claims.
- The `allowed-tools` list names exactly the five subcommands the Script section defines.
