---
lens: executability
doc: /workshop/docs/superpowers/plans/2026-09-25-orko-review.md
---

# executability review

## Verdict

not ready

## Findings

### F-1 [blocker] orko-sdd will create a fresh worktree off master that has no orko-review files

- Where: Global Constraints, first bullet (line 15)
- Evidence: `~/files/repo/claude-skills/orko-sdd/SKILL.md:113-115` tells the orchestrator to "create an isolated worktree without asking, unless the session already runs in a feature worktree", via `git worktree add <repo-root>/.worktrees/<plan-slug> -b feat/<plan-slug> <base-branch>`, and line 121 defines `<plan-slug>` as the plan basename (`2026-09-25-orko-review`). The session starts in the workshop, not in a feature worktree. `git worktree list` shows the prepared worktree at `.worktrees/orko-review` on `feat/orko-review` (f1f0ae8), holding the 16 committed agent, contract, and lens files. `ls ~/files/repo/claude-skills/orko-review` on master prints "No such file or directory". The plan says the worktree is "already created" but gives a relative path and never says not to create another one, and it doesn't say the plan file lives outside the code repository. The v0.1.1 plan said both (`2026-09-25-orko-sdd-v0.1.1.md:15-16`).
- Problem: An orchestrator following orko-sdd creates `.worktrees/2026-09-25-orko-review` on `feat/2026-09-25-orko-review` off master. It has no `orko-review/agents` or `references/`, so the Task 1 `home` fixture symlinks a missing directory, `test_every_catalog_lens_has_a_file_and_every_file_is_in_the_catalog` fails, and the work lands on a branch the release section (R2 Step 2 merges `feat/orko-review`) never merges.
- Fix: Replace line 15 with: "Code repository: `~/files/repo/claude-skills` (public). Work in the existing worktree `~/files/repo/claude-skills/.worktrees/orko-review` on branch `feat/orko-review`; don't run `git worktree add`. That worktree already holds the committed `orko-review/agents/`, `references/reviewer-contract.md`, and the 14 lens files. Paths in the tasks are relative to that worktree's root. This plan file lives in the workshop repository (`/workshop`), so pass SDD's scripts its absolute path and run them from the worktree."

### F-2 [blocker] The release gate can't find the skill before merge

- Where: R2 Step 1 (line 2108)
- Evidence: `tools/skill-evals/scripts/preflight.py:26-27` sets `REPOS = [~/files/repo/claude-skills, ~/files/repo/claude-skills-private]`, and `resolve_skill` (line 89-95) requires `<repo>/orko-review/SKILL.md`. I ran the command as written (without `--out`): `cd / && PYTHONPATH=…/tools/skill-evals python3 -m scripts.preflight orko-review --change-class new --candidate-version 0.1.0` printed `Error: skill not found in any repo: orko-review`. The v0.1.1 plan solved this with a REPOS override (`2026-09-25-orko-sdd-v0.1.1.md:248-251`). The step also uses `$HARNESS` and `$REPO` without sourcing the env file, though R1's own preamble says each Bash call starts fresh.
- Problem: The gate, which must exit 0 before merge, fails at skill resolution. So R2 can't run as written.
- Fix: Replace the Step 1 command with: `source ~/files/scratch/orko-review-smoke.env` in one call, then `cd / && PYTHONPATH="$HARNESS" python3 -c "import sys; from pathlib import Path; import scripts.preflight as p; p.REPOS = [Path('$REPO')]; sys.argv = ['preflight', 'orko-review', '--change-class', 'new', '--candidate-version', '0.1.0', '--out', '$REPO/evals/orko-review/preflight_0.1.0.json']; p.main()"`. Add a sentence: "The gate finds skills only through its `REPOS` list, which names the main checkout, so point it at the worktree for this call."

### F-3 [major] R1 derives REPO from the orchestrator's cwd

- Where: R1 Step 1, `REPO="$(git rev-parse --show-toplevel)"` (line 1872)
- Evidence: The orchestrator session's primary directory is the workshop (`/workshop`), where `git rev-parse --show-toplevel` returns the workshop repo. The step has no `cd` into the worktree first, so `SKILL="$REPO/orko-review"` would point at a missing directory.
- Problem: The scratch project gets dangling `.claude/skills` and `.claude/agents` symlinks. The engagements then fail (the skill is unknown, or preflight reports `agent: missing`), the hash in Step 2 covers the wrong directory, and the evidence commit in Step 6 lands in the wrong repository.
- Fix: Replace the line with `REPO=~/files/repo/claude-skills/.worktrees/orko-review`, the worktree fixed in Global Constraints.

### F-4 [major] R1 Step 1 uses rm -rf, which this environment denies

- Where: R1 Step 1, `rm -rf "$SCR" "$OUT" && mkdir -p …` (line 1885)
- Evidence: `2026-09-25-orko-sdd-v0.1.1.md:34` records "`rm -rf` is denied in this environment, so use fresh directory names instead of deleting old ones". In this review, a Bash call containing `rm -rf` on a scratchpad path was denied by the permission system.
- Problem: The step's first command is refused, and the `&&` chain means the directories aren't created.
- Fix: Drop the `rm -rf`. Use the v0.1.1 pattern: "Pick the first unused suffix `<s>` (empty, then `-2`, `-3`, …) so that `~/files/scratch/orko-review-smoke<s>` doesn't exist yet. The env file is `~/files/scratch/orko-review-smoke<s>.env`, `SCR` is `$HOME/files/scratch/orko-review-smoke<s>`, and `OUT` is `$HOME/files/scratch/orko-review-smoke<s>-out`." Then run `mkdir -p` on fresh paths.

### F-5 [major] "Rerun R1 from Step 2" reuses a scratch spec the apply run already edited

- Where: "After SDD: release steps" preamble (line 1863) and R1 Step 5 closing paragraph (line 2096)
- Evidence: The apply engagement (Step 3) edits `$SCR/docs/superpowers/specs/2026-09-25-textkit-cli-design.md` to fix its accepted findings, and the planted defects are those findings. Step 2 doesn't rebuild the project. Step 5's first check is `len(runs) == 2` over `reviews.glob("*/*/run.json")`, and a rerun adds more run directories to the same `$SCR`.
- Problem: A rerun from Step 2 reviews a spec whose planted defects may already be fixed, and the mechanical checks see four or more runs. The rerun would fail for reasons unrelated to the fix.
- Fix: Change both sentences to "rerun R1 from Step 1, with a fresh suffix (see F-4), so the scratch project and its planted defects are rebuilt".

### F-6 [major] No step probes whether ${CLAUDE_EFFORT} substitutes before the preflight injection

- Where: Tasks 2 and 6, and R1 Step 3's medium-effort engagement
- Evidence: Spec line 395 requires "Probe during implementation: a throwaway skill injecting `echo '${CLAUDE_EFFORT}'` under `claude -p --effort medium`", and says that if it doesn't substitute, "the SKILL.md line `Session effort: ${CLAUDE_EFFORT}.` becomes the fallback". `grep -n -i "probe" plan` finds no such step. `docs/skill-reference.md:55` lists `${CLAUDE_EFFORT}` as a substitution, but nothing I found shows it substitutes inside a `` !`…` `` injection. I didn't run a `claude -p` probe myself, because it isn't read-only. Whether it substitutes is still unverified.
- Problem: If the substitution doesn't happen, preflight prints `effort: unknown` and doesn't block. Then the `--apply` effort gate never fires. In R1 the medium session dispatches reviewers, edits the spec, and creates a third run, so the "medium effort: no Agent dispatch" and "two runs" checks fail after the most expensive step. The fallback SKILL.md line would then have to be designed on the spot.
- Fix: Add a step to Task 6, before Step 3: "Probe: in a scratch directory outside the workshop, create `.claude/skills/effort-probe/SKILL.md` whose body is ``!`echo "effort=[${CLAUDE_EFFORT}]"` ``, then run `claude -p '/effort-probe' --effort medium --model opus`. If the output shows `effort=[medium]`, keep SKILL.md as written. Otherwise, add the line `Session effort: ${CLAUDE_EFFORT}.` under the Preflight heading, add a sentence saying that when preflight prints `effort: unknown` and that line reads below `high`, `--apply` stops with the hint `run /effort high, then rerun`, and record the result in the commit message."

### F-7 [minor] The fixture scrub's expected output is wrong, and it leaves the username in slugs

- Where: Task 4 Step 1 (lines 999-1009)
- Evidence: I ran the step's commands into a scratch copy. `grep -c "/Users/" "$DST"/*.md` printed `accuracy.md:1`, `completeness.md:0`, `design.md:0`, not 0 for each. The hit is the literal `` (`/Users/…`) `` at accuracy.md:33. `grep -n USER` still finds line 17 of accuracy.md, with `-Users-USER-files-projects-proj-a/…`, `-Users-USER-files-repo-proj-b/…`, and `-Users-USER-files-projects-proj-c/…`, because the sed patterns match only `~`.
- Problem: An implementer who trusts "expect 0 for each" either stops or edits the fixture beyond the one recorded scrub. The public repo also gets the username and names of private project directories, against the intent of the Global Constraint at line 27.
- Fix: Add a third expression, `-e 's#-Users-USER-#-Users-USER-#g'`, change the check to `grep -c "USER" "$DST"/*.md   # expect 0 for each`, and add to the commit message: "and `-Users-USER-` project slugs replaced by `-Users-USER-`." The `(/Users/…)` literal stays. Confirm afterwards that `test_real_reports_pass` still counts 8, 23, and 15.

### F-8 [minor] The mechanical checks don't read the subagent transcripts' agent type and resolved model

- Where: R1 Step 5 script, the `every Agent call is orko-review-reviewer on opus` check (lines 2047-2048)
- Evidence: Spec line 393 sets the hook "Live engagement reads each subagent transcript's agent type and resolved model". The script only checks the Agent tool_use `input`, which is what the session requested. On disk, `~/.claude/projects/*/<sid>/subagents/agent-*.meta.json` holds `{"agentType": "orko-sdd-low", …, "model": "haiku"}`, and the sibling `.jsonl` records `"model":"claude-haiku-4-5-20251001"`, so the resolved values can be read.
- Problem: A misresolved agent, such as one that fell back or loaded a different agent file, passes the check.
- Fix: In the per-session transcript loop (line 2077 onward), add: for each `subagents/*.meta.json`, `check(f"{label}: {t.stem} is orko-review-reviewer", meta["agentType"] == "orko-review-reviewer")`, and check that some `message.model` in the matching `.jsonl` starts with `claude-opus`.

### F-9 [minor] The evidence commit omits the attribution lines the plan requires

- Where: R1 Step 6 (lines 2102-2103)
- Evidence: Global Constraints (lines 28-30) say "Commits end with the two attribution lines". The Step 6 message is just `"orko-review: clean-room live engagement evidence"`.
- Problem: This commit is inconsistent with the plan's own rule and with every task commit.
- Fix: Give it the same message form as the task commits: the title, a blank line, then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01R5ifSsB49A2qikKPzmuszD`.

### F-10 [minor] R1 combines cd or git -C with other work in one Bash call

- Where: R1 Step 1 (`git -C "$SCR" init` in the setup block), the scratch commit line (line 1949), and R1 Step 6 (`git -C "$REPO" add` and `commit` together)
- Evidence: `orko-sdd/SKILL.md:119`: "the harness has refused (observed in Claude Code 2.1.280–2.1.281) a Bash call that combines `cd` or `git -C` with git work, so split those into separate calls". The v0.1.1 plan (line 34) makes this a rule: "each step keeps `cd` and `git -C` in calls of their own".
- Problem: These calls may be refused, and the steps don't say to split them.
- Fix: Add to the R1 preamble: "Keep each `cd` and each `git -C` command in a Bash call of its own." Split Step 6 into `git -C "$REPO" add evals/orko-review` and a separate `git -C "$REPO" commit …` call. Run the scratch commit's `add` and `commit` as two calls.

### F-11 [minor] R1 Step 3 says "background Bash call" per engagement but gives one sequential block

- Where: R1 Step 3 (lines 1962-1977)
- Evidence: The text says "Run each as a background Bash call", but the code is one block. It holds one `source` and one `cd`, with `sha256sum … > "$OUT/plan.sha"` between the first and second `claude -p`.
- Problem: It's unclear whether the three sessions run concurrently or in sequence. If they run concurrently, the separate calls lack `source` and `cd "$SCR"`, and `plan.sha` may be taken after the file-only run starts. A concurrent apply run also edits the spec that the file-only coverage reviewer reads.
- Fix: State the order: "Run them one after another, each as its own background Bash call starting with `source ~/files/scratch/orko-review-smoke.env` and `cd "$SCR"` on separate lines. Take `plan.sha` in its own call after the apply run finishes and before the file-only run starts."

### F-12 [minor] preflight accepts `--run <dir>` without `--apply`

- Where: Task 5 Step 3, the `preflight_lines` insertion (lines 1650-1657), and Task 5 tests `test_resume_refuses_an_apply_run` and the others that pass `["--run", str(run)]` with no `--apply`
- Evidence: Spec line 312 defines the form as `preflight --effort <level> --run <run-dir> --apply`, and the argument-hint says `--run <run-dir> --apply`. In the plan's code, `mode` defaults to `apply` and nothing requires the flag. Most `TestResume` tests exercise the bare form.
- Problem: The bare `--run <dir>` form works but isn't documented, and the tests pin the undocumented form rather than the documented one.
- Fix: Either require the flag (in the `--run` branch, add `if "--apply" not in flags: problems.append(f"--run needs --apply; {USAGE}")`, and add `"--apply"` to the resume tests' argv), or add the bare form to the spec and argument-hint. Record which decision was taken.

### F-13 [nit] Task 1's expected red output doesn't match what pytest prints

- Where: Task 1 Step 3 (line 259)
- Evidence: With only `conftest.py` and the test file in place, `uv run --with pytest pytest -q` printed `ImportError while loading conftest '…/conftest.py'` and then `E   ModuleNotFoundError: No module named 'orko_review'`. It isn't a collection error in a test module.
- Problem: This is a small mismatch that an implementer checking the expected text word for word might question.
- Fix: "Expected: `ImportError while loading conftest`, caused by `ModuleNotFoundError: No module named 'orko_review'`."

### F-14 [nit] Task 4's red step has one test that passes before the change

- Where: Task 4 Step 3 (line 1178)
- Evidence: I ran the Task 4 tests against the Task 3 module with `-k "ParseReport or Check"`. `test_missing_run_manifest_refuses` passes, because `main(["check", …])` falls through to the usage branch and returns 2. The rest fail with `AttributeError: … 'parse_report'` or `assert 2 == 0` / `assert 2 == 3`.
- Problem: "Expected: FAIL with AttributeError" isn't true of every selected test, and one test passes whether or not the change is made.
- Fix: Change the expectation to "every test fails except `test_missing_run_manifest_refuses`, which passes on the usage fallback". Or make that test assert the `error: no readable run.json` stderr line too, so it's red before Task 4.

## Checked and sound

- I assembled all six tasks' code into a private scratch copy, following each placement instruction literally: the import additions, "add above `main`", "add above `build_parser`", the `main` fallback replacement, and the `preflight_lines` insertion after `hints += e_hints`. Every anchor exists and applies cleanly. The assembler is `/private/tmp/claude-501/-Users-USER-files-projects-001-claude-skills-creator/6a832d46-cb2d-49f8-8787-8a2294fa4ff1/scratchpad/xreviewer/asm.py`, and the result is in `xreviewer/orko-review/`. Another agent overwrote the shared `scratchpad/exec/` during this review, so cite `xreviewer/`, not `exec/`.
- Green at each stage: Task 1 gives 31 passed, Task 2 49, Task 3 62, Task 4 92, Task 5 108, and Task 6 114. The full suite in `xreviewer/` gives `114 passed`.
- Red at each stage, with each task's tests run against the previous task's module. Task 2 fails with `AttributeError … 'preflight_lines'` (17 tests), Task 3 with `… 'cmd_start'` (13), and Task 5 with argparse `invalid choice: 'decide'` / `'summary'` → `SystemExit: 2`, which matches "exit 2 from argparse".
- The worktree `.worktrees/orko-review` exists on `feat/orko-review` (f1f0ae8). `git ls-files orko-review` lists the agent file, `references/reviewer-contract.md`, and exactly the 14 lens files that `CORE_LENSES` and `EXTRA_LENSES` map to. The agent file has `name: orko-review-reviewer`, `effort: high`, and `disallowedTools: Agent`.
- `render_brief` output matches the brief this review received: the Paths block, then the lens file, then a blank line, then the contract.
- Fixture sources: I listed the directory and read only the front matter and `### F-` heading counts of the three reports under `docs/superpowers/reviews/2026-09-25-orko-review-design/2026-09-25-195039/`. The plan names that directory as its fixture source, it belongs to a different document's run, and I read no finding bodies except the one line cited in F-7 after scrubbing. Counts are accuracy 8, completeness 23, and design 15. design F-1 is `[major]`, F-2 is `[major]`, F-8 is `[minor]`, and F-15 exists, as the mutation and summary tests assume.
- The real preflight run from the workshop cwd against this plan resolved `type: plan (parent directory plans/)`, the spec at the workshop's `docs/superpowers/specs/2026-09-25-orko-review-design.md`, `evergreen: …/CLAUDE.md`, and `reviews-dir: …/docs/superpowers/reviews`. It exited 0 with `STATUS: blocked` only for `agent: missing`, which is expected before activation. Against `2026-09-25-orko-sdd-v0.1.1.md` it resolved the absolute `**Spec:**` value.
- Tools and flags exist: `/sbin/sha256sum`, `/usr/bin/uuidgen`, and Claude Code 2.1.283 with `--effort`, `--session-id`, `--permission-mode`, `--resume`, `--output-format`, `--verbose`, and `--model`.
- The harness has `scripts.utils.hash_dir(path)` (utils.py:35). `scripts.preflight` accepts `--change-class`, `--candidate-version`, and `--out` (preflight.py:713-719), and `scripts.library_status` accepts `--check` (library_status.py:318).
- The public repo's `.gitignore` covers `__pycache__/` and `.pytest_cache/`, so running the tests doesn't trip the gate's `git status --porcelain -- orko-review/` dirty check (preflight.py:472).
- The README has the `orko-sdd` row at line 13 to insert after, and `docs/changelogs/` exists with `orko-sdd.md` in the same heading form as the planned changelog.
- In the stream-json from the orko-sdd v0.1.2 smoke (`~/files/scratch/orko-sdd-v012-smoke-out/`), Agent tool_use blocks are `"name":"Agent"` with `subagent_type`, `model`, and `prompt` inputs, and events carry `parent_tool_use_id`. Subagent transcripts live at `~/.claude/projects/*/<sid>/subagents/*.jsonl`, which is the layout the Step 5 script globs.
- `~/files/scratch` isn't inside a git repository, and there's no `CLAUDE.md` in `~`, `~/files`, or `~/files/scratch`, so the scratch project is isolated from the workshop as R1 intends.
- Task sizes suit a single pass. Task 4 (validator, `check`, and fixtures) is the largest but has one purpose, and no task depends on something a later task creates. Task 1 imports `report_text`/`FIXTURES`, which aren't used until Task 4's fixtures exist, and the tests that use them are added in Task 4.
