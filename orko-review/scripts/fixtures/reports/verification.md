---
lens: verification
doc: /workshop/docs/superpowers/plans/2026-09-25-orko-review.md
---

# verification review

## Verdict

not ready

## Findings

### F-1 [blocker] R2's gate command can't find the skill, so "Exit 0 is required" can never be met before the merge

- Where: "R2: Gate, tag, and release", Step 1 (line 2108)
- Evidence: Ran the command as written: `cd / && PYTHONPATH=…/tools/skill-evals python3 -m scripts.preflight orko-review --change-class new --candidate-version 0.1.0` printed `Error: skill not found in any repo: orko-review`. `tools/skill-evals/scripts/preflight.py:26-27` sets `REPOS = [~/files/repo/claude-skills, ~/files/repo/claude-skills-private]`, and `resolve_skill()` (line 90) looks only for `<repo>/orko-review/SKILL.md`. `ls ~/files/repo/claude-skills/orko-review` reports no such directory: the main checkout is on `master`, and the skill exists only in the `.worktrees/orko-review` worktree on `feat/orko-review`. The gate also reads evidence from `evidence_dir(repo, …) = <repo>/evals/<skill>` (line 228), so it would miss the R1 report too, which R1 writes to `$REPO/evals/orko-review` with `$REPO` taken from the worktree. The orko-sdd v0.1.1 plan already ran into this: `docs/superpowers/plans/2026-09-25-orko-sdd-v0.1.1.md:248` says "The gate finds skills only through its `REPOS` list, which names the main checkout, so point that list at the worktree", and line 251 overrides `p.REPOS` before calling the gate.
- Problem: The release step can't run as written, and the plan says it needs exit 0 before the merge. The gate's script-tests, binding, and evidence checks, which are the executable proof that the built skill matches its evidence, never run against the candidate.
- Fix: Replace R2 Step 1 with the v0.1.1 form: `cd / && PYTHONPATH=$HARNESS python3 -c "import sys; from pathlib import Path; import scripts.preflight as p; p.REPOS = [Path('$REPO')]; sys.argv = ['preflight', 'orko-review', '--change-class', 'new', '--candidate-version', '0.1.0', '--out', '$REPO/evals/orko-review/preflight_0.1.0.json']; sys.exit(p.main())"` (match the entry point exactly to line 251 of the v0.1.1 plan). Source `~/files/scratch/orko-review-smoke.env` first so `$HARNESS` and `$REPO` are set. In R1 Step 1, state that the commands run from `~/files/repo/claude-skills/.worktrees/orko-review`, so `git rev-parse --show-toplevel` returns the worktree.

### F-2 [major] The live engagement never reads the resolved model or agent type from the subagent transcripts, which the spec names as the hook

- Where: R1 Step 5, the mechanical-check script (lines 2045-2048)
- Evidence: The spec's hook table (spec line 393) says: "Reviewers ran on Opus via `orko-review-reviewer` | Live engagement reads each subagent transcript's agent type and resolved model". The plan's check reads only the Agent call's input: `a.get("subagent_type") == "orko-review-reviewer" and a.get("model") == "opus"`. That is the session's request, not what ran. The real transcript layout carries both values: `~/.claude/projects/<proj>/<sid>/subagents/agent-<id>.meta.json` holds `{"agentType":"orko-sdd-low",…,"model":"haiku"}`, and each `.jsonl` line carries `message.model` (for example `claude-haiku-4-5-20251001`). The orko-sdd plan already reads them: `docs/superpowers/plans/2026-09-22-orko-sdd.md:1815-1819`.
- Problem: If the agent name failed to resolve and a general-purpose agent ran, or the per-call model were ignored, every check would still pass. This load-bearing spec fact has no verification in the built result.
- Fix: In the Step 5 script's per-session loop, add a check that for every `subagents/*.jsonl` of `SID_APPLY` and `SID_FILE`, `json.loads(p.with_suffix(".meta.json").read_text())["agentType"] == "orko-review-reviewer"` and the first `message.model` in the transcript starts with `claude-opus`. Record the resolved model IDs in the detail column. Copy the pattern from orko-sdd plan lines 1815-1819.

### F-3 [minor] Task 4 Step 1's expected grep output is wrong: accuracy.md keeps one `/Users/` match

- Where: Task 4 Step 1, the comment `# expect 0 for each` (line 1007)
- Evidence: I ran the step's exact `sed` loop against `docs/superpowers/reviews/2026-09-25-orko-review-design/2026-09-25-195039/`, then `grep -c "/Users/"`, which printed `design.md:0`, `accuracy.md:1`, `completeness.md:0`. The remaining hit is accuracy.md line 33, the prose `absolute (\`/Users/…\`)`, which isn't a real path.
- Problem: An implementer following the expected output sees a mismatch and either stops or edits a real fixture beyond the recorded path scrub. The constraint that matters (no `~`) still holds.
- Fix: Change the check to `grep -c "~" "$DST"/*.md   # expect 0 for each`.

### F-4 [minor] Some red phases aren't red: tests pass before their implementation exists

- Where: Task 4 Step 3 and Task 5 Step 2 (the expected failure lines 1178 and 1532)
- Evidence: I assembled each task's tests on top of the previous task's implementation (scratchpad `red4`, `red5`) and ran the task's `-k` filter. Task 4: `PASSED TestCheck::test_missing_run_manifest_refuses` (29 failed, 1 passed): before Task 4, `main` falls through to the usage fallback, which returns 2 for anything. Task 5: `PASSED TestResume::test_resume_refuses_an_apply_run`, `test_resume_refuses_a_run_without_an_index`, and `test_resume_below_high_blocks_without_flipping` (13 failed, 3 passed): before Task 5, `--run` with no doc path is already blocked for "expected one doc path, got 0", or for the effort gate. On the final build, mutations to the resume mode check and the resume index check each kill one of these tests, so they do pin behavior once the code exists. They just never went red first.
- Problem: The expected-failure lines claim the whole filter fails (Task 5: "`TestResume` fails on `resume:` missing"), so red/green isn't demonstrated for four tests. Two of the resume refusal tests assert only `blocked(...)`, so they'd also pass if the block came from an unrelated problem.
- Fix: In the resume refusal tests, assert the specific problem text: `"problem: run is in apply mode; only a file-only run can be applied later"`, and `"problem: run has no stored findings index; its check never passed"`. Those assertions go red before Task 5. In `test_resume_below_high_blocks_without_flipping`, also assert `"hint: run /effort high, then rerun" in lines`. In `test_missing_run_manifest_refuses`, capture stderr and assert `"no readable run.json"`. Update both expected-failure lines to name every test that fails.

### F-5 [minor] Surviving mutations: seven spec-stated behaviors have no test that fails when the behavior is removed

- Where: Tasks 1, 2, 4, and 5 test lists; the Review Focus bullet on `--why` newlines
- Evidence: I applied each mutation to the fully assembled build (all 114 tests pass unmutated) and ran the suite. Each one SURVIVED with 114 passed: (a) `cmd_decide` stores `args.why` without `one_line`; (b) `agent_dirs` skips every project-level `.claude/agents`; (c) `FINDING_RE` accepts an empty title (`\] ?(.*)$`); (d) effort `xhigh`/`max` treated as below high (`if value == "high"`); (e) the symlink-loop guard in `reviewer_effort` removed; (f) `SPEC_LINE_RE` without `^\s*` (leading whitespace); (g) `--spec` pointing at a missing file not blocked. Spec sources: Review Focus line 37 says "A `--why` holding a newline is stored and rendered as one line… Test in Task 3", but Task 3 only covers the `--extra` reason, and Task 5's `test_records_replaces_and_renders_decisions` overwrites the newline value before asserting. Spec "Path resolution" says the agent scan covers "each `.claude/agents/` from the cwd up to the cwd's repo root", and R1 relies on exactly that link (`$SCR/.claude/agents/orko-review`). Spec validation rules say "the title is non-empty", and its hook asks for "one mutation per validation rule". Spec "preflight" says effort is ordered "low < medium < high < xhigh < max" and the scan runs "with loop protection". Doc-type rule 3 says "after optional leading whitespace or `- `".
- Problem: A regression in any of these ships green. For (b), the first sign would be R1 failing after SDD's final review. For (c), a spec validation rule has no mutation, contrary to the spec's hook.
- Fix: Add one focused test each: (a) in `TestDecide`, `decide(run, "design/F-2", "reject", "a\nb")`, then assert the stored why is `"a b"`; (b) in `TestPreflight`, an empty home plus `project/.claude/agents/orko-review` symlinked to `SKILL_DIR / "agents"`, then assert `"agent: orko-review-reviewer"`; (c) a `MUTATIONS` entry `"empty title": (mutate(r"^(### F-3 \[[a-z]+\]) .*$", r"\1 "), "malformed finding heading")`; (d) parametrize `test_spec_doc_reports_its_resolution` or a new test over `high`, `xhigh`, `max`, then assert `STATUS: ok`; (e) a home whose `.claude/agents/loop` symlinks to its own parent directory, then assert preflight returns; (f) `TestDetectType` with `"  **Spec:** \`x.md\`"`, expecting `plan`; (g) `TestPreflight` with `--spec docs/nope.md` on the plan, expecting `problem: spec not found`.

### F-6 [minor] The planted-defect checks match anywhere in a report, so they can pass when no reviewer flagged the defect

- Where: R1 Step 5, the checks `planted: wrong path reported`, `planted: click conflict reported`, `planted: ambiguous requirement reported`, `planted: uncovered blank-line requirement reported`, and `apply: click conflict deferred` (lines 2058-2064, 2069-2070)
- Evidence: `text` joins each valid report whole, and the checks are substring tests (`"slugs.py" in text`, `"click" in text`, `"quickly" in text`, `"blank" in ptext`). A reviewer that writes under `## Checked and sound` "Checked the `click` dependency claim" or "blank-line handling is covered" makes the check pass. On the other side, `click_ids` keys on the finding title containing "click". A reviewer who titles the finding "Spec contradicts CLAUDE.md's stdlib-only rule" makes `apply: click conflict deferred` fail even though the session deferred it correctly.
- Problem: The pass criterion "each planted defect appears in at least one report" can pass without a finding, and the defer check can fail on wording alone.
- Fix: Slice each report to its Findings section before searching: `re.search(r"^## Findings\n(.*?)^## Checked and sound", t, re.M | re.S).group(1)`. Pick `click_ids` by parsing each finding block (heading through the next `### `) and matching `click` anywhere in the block, not just in the title.

### F-7 [minor] The isolation check misses `run.json` and directory listings, and nothing checks that the apply session edited only the spec

- Where: R1 Step 5, the stray-reads loop (lines 2077-2087), the `file-only: plan unchanged` check, and R1 Step 3 (line 1970)
- Evidence: `touched` uses `re.findall(r"/reviews/[^\"]*?([\w.-]+)\.md", s)`, so only `.md` paths count. The spec's contract bullet forbids "not other reviewers' reports, not earlier runs, not `run.json`", but a `Read` of `…/run.json`, a `Bash` `ls` of the reviews directory, or a `Glob` over it passes. The spec's non-goal "Editing any file other than the doc under review" has no check. `plan.sha` is taken after the apply run (line 1970 follows line 1967), so if the apply session edited the plan, the plan-unchanged check would miss it.
- Problem: Two spec pass criteria (reviewer isolation, and the apply run editing only the doc) are weaker than the spec describes.
- Fix: Count as a stray any tool input under the run's reviews directory that isn't the reviewer's own `briefs/<lens>.md` or `<lens>.md`: use `re.findall(r"/reviews/[^\"\s]*", s)`, then compare against the two allowed paths. Take `plan.sha` before the apply run. Add a check that after the apply run, `git -C "$SCR" status --porcelain` lists only the spec as modified, plus the untracked `docs/superpowers/reviews/`.

### F-8 [minor] The plan has no step for the spec's `${CLAUDE_EFFORT}` substitution probe

- Where: The whole plan; the spec's hook row "`${CLAUDE_EFFORT}` substitutes before the `!` injection runs" (spec line 395)
- Evidence: `grep -n -i "probe\|Session effort:"` on the plan returns nothing. The spec says "Probe during implementation: a throwaway skill injecting `echo '${CLAUDE_EFFORT}'` under `claude -p --effort medium`", and names the fallback. Outside this plan, another session's probe transcripts under `~/.claude/projects/-private-tmp-claude-501--Users-USER-files-projects-001-claude-skills-creator-00000000-0000-0000-0000-000000000000-scratchpad-effort-review-probe/*.jsonl` contain `SUBST=medium`, `SQ=medium`, `SUBST=high`, and `SQ=high`. That suggests substitution works, including inside single quotes, but the plan neither runs the probe nor cites that result.
- Problem: The effort gate depends on this fact. Without the probe, the first in-plan evidence is R1's medium-effort run, after SDD's final review, when a failure means reworking SKILL.md and rerunning R1.
- Fix: Add a step before Task 6 that either runs the spec's throwaway-skill probe under `claude -p --effort medium` and records its output, or cites the existing probe transcript and its `SQ=medium` line as the verification, with the date and Claude Code version.

### F-9 [minor] The file-only engagement runs at `--effort high`, so neither the warn-and-continue path nor reviewer dispatch under a medium session runs live

- Where: R1 Step 3 (lines 1962, 1971-1973)
- Evidence: The spec's hook row (line 394) says "The live engagement runs the operator session at `--effort medium`, so a reviewer inheriting effort would differ from the pin". The spec's eval plan runs both sessions at `--effort medium`. The plan runs apply and file-only at `high` and adds a third apply run at `medium` that blocks before dispatch. Spec "preflight" says that in `file-only` mode, effort below high "prints a `warning:` line and continues", and SKILL.md step 1 says "Pass each `warning:` line on to oiler". No run exercises either behavior.
- Problem: Running apply at high is the right call, since the spec's gate makes apply at medium block. But moving file-only to high as well leaves the warn-and-continue branch and its SKILL.md relay unexercised live, and no reviewer is ever dispatched from a medium-effort session.
- Fix: Run the file-only engagement with `--effort medium`. Add mechanical checks that `file.jsonl`'s injected preflight output contains `warning: session effort is medium`, and that the final result mentions the warning.

### F-10 [minor] The plan doesn't turn its own review reports into plan-lens fixtures, as the spec's eval plan says

- Where: Task 4 Step 1 (lines 995-1009)
- Evidence: The spec's eval plan (line 404) says the spec's own review reports "become `scripts/fixtures/` and are the validator's passing reference fixtures. The plan's review does the same for the plan lenses." Task 4 Step 1 copies only `accuracy`, `completeness`, and `design` from the spec review run. `TestParseReport::test_real_reports_pass` covers only those three.
- Problem: The validator is never checked against a real `coverage`, `executability`, or `verification` report. Their shape differs (for example, per-task findings and long Evidence bullets), and the spec expects them to be reference fixtures.
- Fix: In Task 4 Step 1, also copy `coverage.md`, `executability.md`, and `verification.md` from `docs/superpowers/reviews/2026-09-25-orko-review/2026-09-25-201930/` through the same scrub (with `FIXTURE_DOC`-style constants for the plan path). Extend `test_real_reports_pass` with their finding counts. If the plan's review is rerun before implementation, name the run directory that's used.

### F-11 [nit] Task 6's expected failure text doesn't match what pytest prints

- Where: Task 6 Step 2 (line 1732)
- Evidence: On the Task 6 red build, `pytest -q -rA -k SkillFiles` printed `1 passed, 108 deselected, 5 errors`: five `ERROR … FileNotFoundError` entries (the failure is in the `skill` fixture, not the test body) and `PASSED test_agent_pins_high_effort_and_no_subagents`.
- Problem: "FAIL with `FileNotFoundError`" reads as five failures. pytest reports five errors, which may confuse an implementer checking red.
- Fix: Change the expected output to: "5 errors (`FileNotFoundError` for `SKILL.md` in the `skill` fixture); `test_agent_pins_high_effort_and_no_subagents` already passes because the agent file was committed with the drafts."

### F-12 [nit] The R1 Step 6 evidence commit lacks the attribution lines the plan's Global Constraints require

- Where: R1 Step 6 (line 2103)
- Evidence: Global Constraints (lines 28-30) say "Commits end with the two attribution lines". `grep -c "Co-Authored-By"` on the plan returns 7: the constraint plus the six task commits. The command `git -C "$REPO" commit -m "orko-review: clean-room live engagement evidence"` doesn't include them.
- Problem: The evidence commit breaks the plan's own commit rule.
- Fix: Append the blank line and the two attribution lines to the R1 Step 6 commit message, the same way the task commits do.

## Checked and sound

- Assembled every code block in the plan, in task order, into a scratch copy of the worktree's `orko-review/` (existing agent, contract, and 14 lens files), plus the fixtures from Task 4 Step 1's `sed` loop. `uv run --with pytest pytest -q` from `orko-review/scripts` printed `114 passed`.
- Task 1's red step matches: `conftest.py` imports `orko_review`, so collection fails with `ModuleNotFoundError`.
- Task 2's red step: all 18 `-k Preflight` tests fail with the expected `AttributeError` (`preflight_lines`, including through `monkeypatch.setattr` in `test_crash_still_exits_zero`). Task 3's red step: all 13 `-k Start` tests fail on `cmd_start`.
- Task 4 and Task 5 red steps: every `TestParseReport` test and every `TestDecide` and `TestSummary` test fails before its implementation. The Task 5 tests error with `SystemExit: 2` from argparse, which is what "exit 2 from argparse (`invalid choice`)" describes.
- Mutations killed on the final build, each by the one test named: resume without the mode check (`test_resume_refuses_an_apply_run`), resume without the index check (`test_resume_refuses_a_run_without_an_index`), `check` without the all-failed exit 3 (`test_every_lens_failed_blocks`), and `start` without the extras cap (`test_bad_specialists_refuse_without_creating_a_run[three]`).
- The six `REAL_SPEC_LINES` match the workshop plans verbatim, with only the user path swapped in the absolute form: `2026-09-25-orko-sdd-v0.1.1.md:11`, `2026-09-22-orko-sdd.md:11`, `2026-08-26-design-sys.md:11`, `2026-07-18-wordpress-plugins-test-harness.md:13`, and `2026-08-05-cowork-builder-v0.4.0-upgrade.md:11`.
- The fixture facts the tests depend on hold in the source reports: finding counts are 8, 23, and 15; every verdict is `ready with changes` on line 10; design `F-1` is `[major]`, `F-2` exists, `F-8` is `[minor]`, and `F-15` is the last. Every `MUTATIONS` pattern matches the design fixture, and every mutation produces its named error.
- The Review Focus items for CRLF, trailing whitespace on headings, a relative doc path from a subdirectory, and a second run's own directory each have a test that passes on the build.
- The brief test compares the whole brief to the template filled with the lens and contract files, which pins the spec's "verbatim and no other prose" hook. The start-output test pins the exact dispatch sentence.
- The `SkillFiles` tests pin `allowed-tools` to the five `SUBCOMMANDS`, `disable-model-invocation: true`, the preflight injection line, the agent and model named in the dispatch step, SKILL.md staying under 150 lines, and the agent's `effort: high` and `disallowedTools: Agent`.
- The R1 tooling exists on this machine: `/sbin/sha256sum` (and `sha256sum -c` prints `OK`, exit 0), `/usr/bin/uuidgen`, and the `claude` flags `--session-id`, `--effort`, and `--resume`. The subagent transcript glob `~/.claude/projects/*/<sid>/subagents/*.jsonl` matches the real layout.
- `tools/skill-evals/scripts/utils.py:35` defines `hash_dir`, which R1 Step 2 imports. The gate's `check_scripts` discovers `scripts/test_*.py` and runs `pytest scripts -q` from the skill directory, which works with this suite's `conftest.py` layout.
- Test sizing is in line with the neighbor: 86 test functions (114 with parametrization) for five subcommands, against 140 in `orko-sdd/scripts/test_*.py`. No scratch checks are promoted into the suite.
