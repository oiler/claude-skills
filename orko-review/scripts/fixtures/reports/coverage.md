---
lens: coverage
doc: /workshop/docs/superpowers/plans/2026-09-25-orko-review.md
---

# coverage review

## Verdict

ready with changes

## Findings

### F-1 [major] The `${CLAUDE_EFFORT}` substitution probe the spec requires during implementation has no task

- Where: Task 6 (SKILL.md), and the plan as a whole; spec "Verification hooks for load-bearing facts", row "`${CLAUDE_EFFORT}` substitutes before the `!` injection runs"
- Evidence: Spec line 395: "Probe during implementation: a throwaway skill injecting `echo '${CLAUDE_EFFORT}'` under `claude -p --effort medium`. If it doesn't substitute, preflight gets the literal and prints `effort: unknown`, and the SKILL.md line `Session effort: ${CLAUDE_EFFORT}.` becomes the fallback." `grep -n "CLAUDE_EFFORT" docs/superpowers/plans/2026-09-25-orko-review.md` prints only lines 489, 1712, 1764 (a unit-test parameter, the SKILL.md test, and the injection line). No step runs the probe, and neither SKILL.md draft nor any task mentions the `Session effort:` fallback line.
- Problem: The whole effort gate (the spec's "Session effort" decision) rests on an unverified platform fact. If substitution doesn't happen, preflight prints `effort: unknown` and never blocks, and the plan discovers it only at R1's `low.jsonl` check, after SDD's final review, which forces a SKILL.md change, a re-hash, and a full R1 rerun.
- Fix: Add a step at the start of Task 6 (before writing SKILL.md): "Probe: create `~/files/scratch/effort-probe/.claude/skills/effort-probe/SKILL.md` with `disable-model-invocation: true` and the body line ``!`echo 'effort=${CLAUDE_EFFORT}'` ``; run `cd ~/files/scratch/effort-probe && claude -p '/effort-probe' --effort medium --output-format stream-json --verbose` and confirm the injected text reads `effort=medium`. If it reads the literal, add the line `Session effort: ${CLAUDE_EFFORT}.` under `## 1. Preflight` in SKILL.md, tell the session to block `--apply` itself when that line shows a level below high, and add a test for the line. Record the probe result in the Task 6 commit message."

### F-2 [major] The live engagement runs the dispatching sessions at `--effort high`, so the reviewer-effort pin and the file-only warning are never exercised; the change from the spec's eval plan isn't recorded

- Where: R1 Step 3 ("The first two run at `--effort high`, the third at `--effort medium`")
- Evidence: Spec Eval plan (line 406): "Two `claude -p --model opus --effort medium` sessions (oiler's session default, so the effort note and the reviewer pin are both exercised)". Spec verification hooks (line 394): "The live engagement runs the operator session at `--effort medium`, so a reviewer inheriting effort would differ from the pin". The plan runs apply and file-only at `--effort high` and adds a third apply session at medium that blocks before dispatch.
- Problem: The spec's eval plan is itself contradictory (an apply run at medium blocks under the spec's own Session-effort decision), and the plan's third session reconciles that part correctly. But no session that actually dispatches reviewers runs at medium, so the spec's stated purpose ("the reviewer pin [is] exercised") is lost, and preflight's `--file-only` warn-and-continue path never runs live. The plan also doesn't say it departed from the spec.
- Fix: In R1 Step 3, run the file-only session at `--effort medium` (it warns and continues, so its reviewers dispatch under a medium session), keep the apply session at `--effort high`, and keep the medium apply session that must block. In Step 5 add `check("file-only at medium: effort warning shown", "warning: session effort is medium" in <file.jsonl text>)`. Add one sentence under R1: "The spec's eval plan runs the apply session at medium, which its own Session-effort decision blocks; this plan runs the file-only session at medium instead and records the spec correction as deferred."

### F-3 [major] The workshop audit checklist that the project CLAUDE.md requires before shipping appears nowhere in the release steps

- Where: "After SDD: release steps (orchestrator)", R2
- Evidence: Project CLAUDE.md, "When oiler asks to do skill work", step 4: "Run the audit checklist (in `docs/skill-engineering.md`) before shipping." `docs/skill-engineering.md:190-212` lists the checklist and says items without `[preflight]` are "human judgment the script cannot make" (for example line 206, "Non-obvious constraints carry their why", line 207 "Hub restatements checked against their references", line 211 the symlink decision). R2 Step 1 runs only the executable gate, which covers only the `[preflight]` items.
- Problem: An evergreen instruction is skipped. The gate does not cover the unmarked items, so the release could ship without them being checked.
- Fix: Add R2 Step 0: "Walk the audit checklist in `docs/skill-engineering.md` (Audit checklist before shipping) against the branch's `orko-review/` and record each unmarked item as pass or a fix; any fix reruns R1 from Step 2."

### F-4 [minor] The plan-lens review reports never become fixtures, though the spec's eval plan says the plan's review "does the same for the plan lenses"

- Where: Task 4 Step 1 (copies only `accuracy`, `completeness`, `design`)
- Evidence: Spec line 404: "Those reports become `scripts/fixtures/` and are the validator's passing reference fixtures. The plan's review does the same for the plan lenses." Task 4 Step 1's loop is `for lens in accuracy completeness design`. This plan's own review run (`2026-09-25-orko-review/2026-09-25-201930/`) produces `coverage`, `executability`, and `verification` reports.
- Problem: Either the spec intends plan-lens fixtures and the plan omits them, or the sentence means only "the plan is reviewed the same way by hand". The plan resolves neither reading, and the validator is never tested against a real report whose front matter names a plan lens and a plan doc.
- Fix: Either add to Task 4 Step 1 a second copy loop for `coverage executability verification` from this plan's review run directory (with the same scrub) plus a `test_real_reports_pass` parametrization for them, or add one line to Task 4: "Plan-lens reports aren't fixtures: the spec's 'does the same' means the plan gets the same hand-run review; the validator is lens-agnostic."

### F-5 [minor] No negative fixture for the "title is non-empty" validation rule

- Where: Task 4 Step 2, `MUTATIONS`
- Evidence: Spec verification hook (line 397): "negative fixtures derived from one of them, one mutation per validation rule". Spec validation rules (line 266): "the title is non-empty". `MUTATIONS` covers every other rule; "malformed heading" replaces `### F-2 [x] ` with `### Finding 2 `, which fails on the ID, not the title. Nothing produces `### F-1 [major] ` with an empty title.
- Problem: One validation rule has no mutation, so a regression that accepts an empty title (for example changing `(\S.*)` to `(.*)` in `FINDING_RE`) stays green.
- Fix: Add `"empty title": (mutate(r"^(### F-1 \[major\]) .*$", r"\1 "), "malformed finding heading"),` to `MUTATIONS`.

### F-6 [minor] The live check for "reviewers ran on Opus" reads the requested model parameter, not the subagent transcript's resolved model

- Where: R1 Step 5, check "every Agent call is orko-review-reviewer on opus"
- Evidence: Spec verification hooks (line 393): "Live engagement reads each subagent transcript's agent type and resolved model". The plan's check inspects `a.get("model") == "opus"` on the parent's Agent tool_use input only.
- Problem: The check proves the session asked for Opus, not that the reviewer ran on it, which is what the spec's hook names.
- Fix: In the per-SID transcript loop in Step 5, also collect each subagent transcript's assistant `message.model` values and add `check(f"{label}: every reviewer transcript ran on an Opus model", all(m.startswith("claude-opus") for m in models), ", ".join(sorted(set(models))))`.

### F-7 [minor] The live check allows failed lenses, but the spec's pass criterion is that reports exist and pass `check`

- Where: R1 Step 5, check "index stored"
- Evidence: Spec Eval plan (line 406), Pass: "reports exist and pass `check`". `index` is stored when at least one lens is valid (`cmd_check`, Task 4), so a run with a lens failed twice still passes the plan's check.
- Problem: A reviewer that twice fails to write a valid report passes the live engagement.
- Fix: Add `check(f"{label}: every lens valid", manifest and all(s == "valid" for s in manifest["status"].values()), json.dumps(manifest.get("status")))`.

### F-8 [minor] `--run` is accepted without `--apply`, and the resume tests encode that

- Where: Task 5 Step 3 (`preflight_lines` `--run` branch) and `TestResume`
- Evidence: Spec line 312: "`preflight --effort <level> --run <run-dir> --apply`"; spec Goal and argument-hint: "`--run <run-dir> --apply`". The plan's branch never checks for `--apply`; `test_resume_refuses_an_apply_run`, `test_resume_refuses_a_run_without_an_index`, `test_resume_refuses_a_changed_doc`, and `test_resume_below_high_blocks_without_flipping` all call `--run` without `--apply`.
- Problem: The plan quietly widens the spec's grammar; `/orko-review --run <dir>` flips a run to apply though oiler didn't type the flag the spec made mandatory.
- Fix: In the `--run` branch add `if "--apply" not in flags: problems.append(f"--run needs --apply; {USAGE}")`, add `--apply` to the four resume tests' argv, and add `test_resume_without_apply_blocks`.

### F-9 [minor] Refusals in `check`, `decide`, and `summary` print `error:` to stderr, but the plan's constraint says every blocking condition prints `problem:`

- Where: Global Constraints ("Every blocking condition prints `problem: <text>`"); Task 4 `open_run`; Task 5 `cmd_decide`, `cmd_summary`
- Evidence: Spec line 310: "Every blocking condition prints `problem: <text>` and, where one exists, `hint: <text>`." `open_run` prints `error: no readable run.json`; `cmd_decide` prints `error: {problem}`; `cmd_summary` prints `error: no findings index` and `undecided:`.
- Problem: The plan restates the spec's rule and then doesn't follow it in three subcommands.
- Fix: Either change these to `print(f"problem: …")` on stdout (and update `test_apply_refuses_while_findings_are_undecided` to read `.out`), or narrow the Global Constraints line to "Every preflight, start, and check blocking condition prints `problem:`; decide and summary refuse with `error:` on stderr" and flag the spec line for the same narrowing.

### F-10 [minor] Release steps don't commit the gate verdict, and the R1 evidence commit omits the attribution lines

- Where: R1 Step 6; R2 Steps 1-2
- Evidence: `docs/skill-engineering.md:214`: "commit the passing verdict with the release so every tag carries the exact content hash it approved." R2 Step 1 writes `evals/orko-review/preflight_0.1.0.json`; no step commits it before the tag. R1 Step 6 commits with `-m "orko-review: clean-room live engagement evidence"` and no trailer, against the plan's own Global Constraint "Commits end with the two attribution lines".
- Problem: The tag could land without its gate verdict, and one commit breaks the plan's own constraint.
- Fix: In R2 Step 1 add "then `git -C "$REPO" add evals/orko-review/preflight_0.1.0.json && git -C "$REPO" commit` (with the two attribution lines)" before Step 2's merge. Add the two attribution lines to R1 Step 6's commit message.

### F-11 [nit] `start` prints a `run:` line the spec's `start` section doesn't list

- Where: Task 3, `cmd_start` and `test_prints_the_run_and_one_exact_dispatch_prompt_per_lens`
- Evidence: Spec line 331: "Prints one line per lens: `<lens>: Read <absolute brief path> and follow it.`" The plan prints `run: <run>` first.
- Problem: A deviation, though a needed one: the spec's SKILL steps 5-8 use `<run-dir>` without saying where the session gets it.
- Fix: Keep it. Add to Task 3: "Adds a `run:` line the spec omits, because SKILL.md steps 5-8 need the run directory; defer the spec update."

### F-12 [nit] Preflight blocks on an agent whose effort isn't `high`, which the spec doesn't ask for

- Where: Task 2, `preflight_lines` and `test_agent_without_high_effort_blocks`
- Evidence: Spec line 325: "`agent:` found or missing …; blocked if missing". The plan adds `problem: orko-review-reviewer must pin effort: high`.
- Problem: Extra behavior not in the spec. It's defensible (it enforces the spec's effort-control decision at run time), but unrecorded.
- Fix: Keep it and add one line to Task 2 naming it as an addition that backs the spec's "Effort control" decision.

### F-13 [nit] Heading matching tolerates trailing whitespace; the spec says "matched exactly"

- Where: Review Focus bullet 5; Task 4 `parse_report` (`line.rstrip() == heading`) and `test_trailing_whitespace_on_headings_is_tolerated`
- Evidence: Spec line 264: "The headings `## Verdict`, `## Findings`, and `## Checked and sound` appear once each, in that order, matched exactly."
- Problem: The plan loosens a spec rule without saying so.
- Fix: Keep the tolerance and write in Review Focus: "Deliberately looser than the spec's 'matched exactly': trailing whitespace is ignored. Defer the spec wording."

### F-14 [nit] `decisions.md` is rendered by `decide`, not "rendered by summary"

- Where: Task 5, `cmd_decide` / `cmd_summary`
- Evidence: Spec Run directory tree (line 280): "`decisions.md` … written by decide, rendered by summary". The plan's `cmd_summary` never reads or renders `decisions.md`.
- Problem: The spec phrase is ambiguous; the plan picks one reading silently.
- Fix: Add one line to Task 5: "`decide` writes and re-renders `decisions.md`; `summary` renders from `run.json`, not from `decisions.md`."

### F-15 [nit] README row isn't in the spec's release plan

- Where: Task 6, Files and Step 5
- Evidence: Spec Release plan (line 424) names the changelog but not the README. The public `README.md:13` has an `orko-sdd` row with the same second-symlink note, so the plan follows repo convention.
- Problem: Out of spec scope, though consistent with the repo.
- Fix: Keep it; no change needed beyond noting it follows the `orko-sdd` README precedent.

## Checked and sound

- SKILL.md frontmatter in Task 6 matches the spec's Skill identity block word for word: `name`, the six-line `description`, `argument-hint`, `disable-model-invocation: true`, and the five `allowed-tools` grants.
- The committed agent file (`~/files/repo/claude-skills/.worktrees/orko-review/orko-review/agents/orko-review-reviewer.md`) matches the spec's Agent block verbatim, has no `omitClaudeMd`, and Task 6 tests `effort: high` and `disallowedTools: Agent`.
- All 14 lens files named in the spec exist in the worktree under `references/lenses/`, and Task 1 tests that the catalog and the directory match exactly.
- Global Constraints values match the spec: core lenses per type, specialist catalog and order, cap of two, the lens-naming rule, evergreen names and locations, effort order, run-directory pattern, dispatch sentence, test command, and the "`!`cmd`` injection that exits nonzero aborts the invocation" quote.
- `AGENT_INSTALL` matches the spec's Installation agents command verbatim; the `hint: pass --spec <path>` and `problem: --spec applies only to plans` strings match the spec.
- Doc-type detection rules 1-4, the 40-line window, the `**Spec:**` line regex (optional whitespace or `- `), spec-token extraction (first backtick span, else first token with `.`, `,`, `)` stripped), the `http` exclusion, and the absolute/repo-root/plan-dir order all match the spec, each with a test.
- `REAL_SPEC_LINES` reproduces the five cited plan header lines; `grep -n '\*\*Spec:\*\*'` on `2026-09-22-orko-sdd.md:11`, `2026-08-26-design-sys.md:11`, `2026-09-25-orko-sdd-v0.1.1.md:11`, `2026-07-18-wordpress-plugins-test-harness.md:13`, and `2026-08-05-cowork-builder-v0.4.0-upgrade.md:11` shows the same values (the absolute one with its user path replaced).
- Reports-directory resolution (superpowers ancestor bounded by the repo root, `specs`/`plans` sibling, own-directory fallback, repo-root doc) and repo-root rules (the doc's repo, the doc's directory outside git) are implemented and tested per the spec.
- Preflight covers every spec line: doc, mode, effort (block in apply, warn in file-only, `unknown` for empty or literal), type with rule, spec, lenses, extras-available, evergreen or `none`, reviews-dir, agent scan (home plus cwd up to the cwd's repo root, recursive, symlinks followed, loop-protected), and always exits 0 even on a crash.
- Brief template: paths block, optional `Spec:` line for plans, evergreen comma list or `none`, then the lens file and the contract verbatim; Task 3 tests a brief against the template.
- `start` validates unknown, duplicate, more than two, missing and empty `--why`, refuses an existing run directory, and writes `run.json` with every manifest field the spec lists plus `doc.orig.md`.
- `check` implements hash-first blocking with exit 3, move-aside to `<lens>.invalid-<n>.md`, the two-strike `failed` rule with later reports ignored, exit 2/0/3 as specified, and the index sort and pipe escaping, each tested.
- `decide` refusal set (no index, unknown ID, file-only run, empty `--why`) and replace-on-repeat, and `summary`'s apply refusal on undecided findings, section order with Recommended last, `None.` for empty tables, the failed-lens row format, and the file-only resume command all match the spec.
- Resume flow checks run.json, file-only mode, stored index, and doc hash, flips the mode, prints `resume:`, and SKILL.md routes a `resume:` line to step 7, matching "skips steps 2-6 and enters at step 7".
- SKILL.md steps 1-8 and the quoting rule cover the spec's SKILL.md content section; the under-150-lines target has a test.
- R1 builds the spec's scratch project (outside the workshop tree, project-level links, a CLAUDE.md, the three planted spec defects, a plan with one uncovered requirement) and checks the fixed dispatch prompt, agent type, dispositions, deferral of the CLAUDE.md conflict, plan byte-identity, no commit, no second round, planted-defect presence, and reviewer isolation, as the spec's pass criteria and Risks table require.
- Release plan matches the spec: branch `feat/orko-review` (worktree exists at `f1f0ae8`), changelog path, gate command with `--change-class new --candidate-version 0.1.0`, tag `orko-review-v0.1.0`, GitHub release, library-status regeneration, activation asked with the recommended yes, and oiler's confirmation before merge, push, tag, and activation.
- `sha256sum` used in R1 exists on this machine (`/sbin/sha256sum`).
- Not checked: the finding counts (8, 23, 15) and the specific severities the tests assume in the fixture reports (`design/F-1` major, `design/F-8` minor), because the source reports sit under the reviews directory this brief puts off limits.
