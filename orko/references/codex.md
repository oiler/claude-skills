# Codex executor

Step 5 of a build runs one of two executors. With `--executor claude`, `superpowers:subagent-driven-development` works through `tasks.md`. With `--executor codex`, this loop runs instead: Codex writes the code, you judge every delivery from the repository rather than from Codex's report, and two report-only Claude reviewers read each task before you close it.

`init` records the executor, the Codex model plus effort overrides, the boundaries, and the attribution trailers in the ledger header. None of them change on resume, and `init` says so on stderr when a passed trailer differs from the recorded one.

Every script call in this file is written as `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py <subcommand>`. If `${CLAUDE_SKILL_DIR}` is empty in your Bash call, use `~/.claude/skills/orko/scripts/orko.py`. Never use shell command substitution: the prefix matching behind `allowed-tools` cannot see through it, and the resulting permission prompt is invisible inside a long dispatch. Where a command needs a value another command produces, run two commands.

## Defaults

The script builds the whole dispatch, including its routing flags. You do not compose them, and you do not add to them.

- **No `--model` and no `--effort`** unless intake recorded an override with `init --codex-model` or `init --codex-effort`. With neither recorded, the dispatch inherits whatever `~/.codex/config.toml` sets, which is what oiler already tuned. Volunteering a model is how a run silently gets a different one than the machine's default.
- **`--background` and `--write`** on every dispatch. Background because a foreground Codex task runs inside one Bash call, whose ceiling is 10 minutes, and a real task is longer than that. Write because Codex must change files in the working tree. It never commits: the sandbox mounts `.git` read-only, so the script commits the delivery at step 5.
- **`--fresh` on a first attempt**, `--resume` only on the one retry the loop allows.
- **Model slugs pass through as literal strings.** If oiler names a slug at intake, pass it exactly as typed. This skill carries no slug table and never maps, validates, or corrects one.

## Where Codex runs

`prompt task` prints two lines and writes a file. The printed dispatch line carries `--cwd <workspace>/code`, which the companion reads as the job's working directory, so Codex runs at the code repository's git root with a `workspace-write` sandbox rooted there, `approvalPolicy: never`, and no network. That sandbox mounts the repository's `.git` read-only: `git commit` inside a dispatch fails on `.git/index.lock`, so the prompt tells Codex not to run git at all and step 5 of the loop makes the commit. The code repository is both the git root and the whole writable surface, so Codex cannot reach `docs/`. The record stays yours. The task itself goes to `<run_dir>/context/task-<n>.md`, and the dispatch line points at it with an absolute `--prompt-file`, so Codex reads the task as the script wrote it: a prompt forwarded as argument text is re-joined with spaces, which would fold its steps, its code, and its acceptance command into one line.

A `cd` in your own shell does none of that. The dispatch goes through `Agent(subagent_type: "codex:codex-rescue")`, whose shell starts in the session's own working directory, so the directory you stand in never reaches the job. `codex wait` and `preflight` pass the same `--cwd` to the companion themselves, and every other command in the loop resolves the workspace from `--workspace`. Run all of them from the workspace root.

Pass no `model` on the dispatch. `codex:codex-rescue` is a forwarder whose model the plugin sets, and the Codex model rides on the flags line when intake recorded one.

## The loop

Run this once per task in `tasks.md`, in order, starting at the `next_task` that `status` reports.

**1. Record the dispatch base.** Read the code repository's HEAD, then pass it:

```bash
git -C code rev-parse HEAD
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 5.<n> dispatched --slug <slug> --commit <sha>
```

The sha is the base the delivery check diffs against. Two commands, never one substituted command.

**2. Build and dispatch the prompt.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt task <slug> --task <n> --attempt fresh
```

Stdout is three lines: the routing flags, `--background --write --fresh --cwd <workspace>/code --prompt-file <run_dir>/context/task-<n>.md` plus `--model <M>` and `--effort <E>` when intake recorded them, a blank line, then one sentence naming the task. The file at `--prompt-file` holds the task itself: the objective, the `SPEC-NNN R<n>` rows it satisfies, the files, the steps, the acceptance command, the branch, the boundaries, and the testing-README row it must add. It carries no commit instruction and no trailers, and it says so: Codex leaves every change in the working tree and reports the files it changed, and the script owns the subject, the staged set, the `Refs:` line, and the trailers at step 5.

Paste that stdout into `Agent(subagent_type: "codex:codex-rescue")` verbatim, and send nothing else. Do not summarize it, reorder it, drop the flag line, or paste the prompt file's contents beside it: the routing flags travel inside the dispatch text because the `Agent` tool's `model` parameter cannot carry a Codex slug, and the task travels in the file because forwarded argument text is not reproduced byte for byte. The agent returns the job id.

`prompt` refuses a task with no `**Acceptance:**` command and exits non-zero. That is not a bug to work around. The acceptance command is the entire definition of done for the dispatch; fix `tasks.md` and re-run `check tasks <path>` before dispatching.

**3. Wait for the job.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py codex wait <job-id> --slug <slug>
```

This polls the companion script, naming the code repository as the job's workspace root, and prints the result JSON.

The forwarder's return normally carries the job id, a `task-...` string. When it carries only a companion background handle, or nothing at all, do not guess and do not treat the dispatch as lost:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py codex wait latest --slug <slug> --workspace <path>
```

`latest` resolves the newest job registered under the code repository and names it on stderr as `orko: latest job is <id>`. So `No job found for "<id>"` reads two ways. With an explicit id it means the id you were handed is not a job id, which `latest` recovers, or the job registered under another root. With `latest` it means no job is registered under `code/` at all, and that is the dropped-`--cwd` case: count it as that attempt's delivery failure and retry as in step 7. If the second attempt answers the same way, record the dispatch line you sent in `escalations.md` alongside the escalation.

The default timeout is 1800000 milliseconds; override it with `--timeout-ms <n>` for a task you expect to run longer. The companion reports `status`, `threadId`, `touchedFiles`, `rawOutput`, and `reasoningSummary`, with no model name and no token count, so record the job id and the wall time from `startedAt` and `completedAt` in your step summary, and in `escalations.md` when the task escalates, and say the model is whatever `~/.codex/config.toml` sets when intake recorded no override. Exit `0` means the job completed; delivery is still judged by `check delivery`. An empty return from the agent or a failed job is a delivery failure.

**4. Check the delivery.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py check delivery --slug <slug> --task <n>
```

The script judges the repository, not Codex's report. Codex cannot commit, so the delivery is the working tree: the check reads every path `git status` reports as modified, added, deleted, or untracked, plus everything in `<base>..HEAD`, which is why a delivery `commit code --task` has already landed still passes a re-check. It prints `acceptance: <cmd>` before it runs that command, so the line it executes is visible in the transcript. Every path in `tasks.md` is relative to the code repository root, the `**Files:**` lines, the acceptance command, and every `Run:` line alike, because the check diffs and runs there. Read every `**Acceptance:**` line in `tasks.md` yourself before the first dispatch, and reject any that is not the repository's own test or lint runner: the script runs it as a shell command with your privileges.

What the acceptance command itself leaves behind is never part of the delivery. The script drops seven names from what it read: `.venv/`, `uv.lock`, `.pytest_cache/`, `__pycache__/`, `.ruff_cache/`, `.mypy_cache/`, and `node_modules/`. It matches each as a leading path prefix and as any path segment, so `tests/__pycache__/x.pyc` is a leftover too. A leftover is neither a change nor a breach of the allowlist. Its findings:

| Finding | What it means |
|---|---|
| `diff-empty` | no change since the dispatch base in either the working tree or a commit; the dispatch delivered nothing |
| `diff-outside-allowlist: <paths>` | the delivery touches files the task did not list. `docs/testing/README.md` is always inside the allowlist, because the task prompt tells every delivery to write it |
| `acceptance-failed: exit <n>` | the script ran the acceptance command and it did not exit `0` |

Codex's own claim that the acceptance command passed is not evidence. Its sandbox has no network, so a command that fetches anything fails there and passes here, or the reverse. Any finding stops the loop here: a failed delivery is never committed, so go to step 7 rather than step 5.

**5. Commit the delivery.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit code --slug <slug> --task <n> --workspace <path>
```

Only after `check delivery` exits `0`. The script stages the task's `**Files:**` paths plus `docs/testing/README.md`, and nothing else: whatever Codex wrote outside that allowlist cannot be staged, and step 4 has already named it. The subject is `Task <n>: <title>` taken from `tasks.md` unless you pass `--message`, and the `Refs:` line and the attribution trailers come from the ledger, not from a model. The acceptance command's leftovers stay untracked. The JSON names the commit sha.

This is the commit Codex was once told to make itself, and it is stronger here: the subject, the staged set, the `Refs:` line, and the trailers are all script-owned.

**6. Review the task.** Build both reviewer prompts and dispatch them in one message, both at `sonnet`:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt task-review <slug> --task <n> --lens spec-compliance
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt task-review <slug> --task <n> --lens code-quality
```

The reviewers read `<base>..HEAD`, which exists because step 5 committed. Both are report-only, and their findings land in `findings/5.<n>/<lens>.md`. Run `check delivery` again on their files if either one edited the tree; a reviewer that wrote code is a failed seat, not a delivery.

**7. Decide and re-dispatch.** The loop allows one retry per task, for a step-4 delivery failure or a step-6 finding alike:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt task <slug> --task <n> --attempt resume --failure "<what failed>"
```

Name the failure concretely: the finding, and for `diff-outside-allowlist` the paths. Dispatch the stdout verbatim as in step 2 and wait as in step 3. A failed delivery leaves the tree exactly as Codex left it, which is what `--resume` continues from: do not clean it up, do not commit it, and do not write the fix yourself. A second delivery failure is an escalation. A re-dispatch after step 6, on a task already committed, lands a second commit; pass `--message` to name the fix.

`record disposition` is not used for review findings here. Task-review findings have no review record: `REVIEW-NNN` for the code is minted once at step 6 of the build, over the whole branch diff. Decide each finding in your own message, and either fix it now by re-dispatching as above, or carry it to step 6's review, where the code review seats see it in the branch diff anyway.

**8. Close the task.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 5.<n> complete --slug <slug>
```

After the last task, and only then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 5 complete --slug <slug>
```

`next_step` counts integer steps only, so the run does not leave the build's step 5 until that line exists. `status` reports `next_task` as one past the highest `5.<n> complete`, and a resume at step 5 starts there, never at task 1.

## Resume rules

`--resume` does not name a thread. It resolves to the newest resumable task job in this workspace for this Claude session. The plugin throws in two cases: when no previous job exists, and when one is still running. It also drops every job for the session at `SessionEnd`.

So `--attempt resume` is only correct as the immediate retry of a dispatch this session just made and waited on. On either plugin error, or after any session boundary, fall back to a fresh dispatch that carries the failure text forward:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt task <slug> --task <n> --attempt fresh --failure "<what failed>"
```

A fresh attempt with `--failure` is not a wasted retry. It is the same one retry, with the context that `--resume` would have supplied written into the prompt instead.

An empty return from `Agent(subagent_type: "codex:codex-rescue")` is a delivery failure, not a transient glitch. The agent forwards one call and returns nothing on any failure, so an empty return means the dispatch never ran.

## Escalation

Two delivery failures on one task stop the run. Do not try a third dispatch, and do not write the code yourself.

1. Route the blocker per the rule in `references/record.md`: `record decision` for a product-scope question, `record adr` for a choice with long-lived architectural consequence, `record delivery-decision` for everything else, which is where an execution-environment blocker belongs. The ADR route is closed when the intake boundaries exclude `code/docs/adr/`, because writing there is itself outside the boundaries.
2. Write the escalation into `<run_dir>/escalations.md` yourself, naming the task, both `check delivery` finding sets, and the record ID. A delivery-decision row has no ID of its own, so for that route name `PLAN-NNN` and quote the row's first cell. Carry each attempt's job id and wall time there too: the escalation path writes no step summary, and this file is the only artifact it leaves.
3. `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "<subject>"`. A record that is not committed has no hash in the ledger, and the next write to it trips the overwrite guard.
4. `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 5.<n> escalated --slug <slug>`, alone and with no `complete` line. build.md's rule that `escalated` follows a `complete` line covers whole steps; a `5.<n> complete` would advance `next_task` past a task that never delivered.
5. Stop and report. Leave the code repository's working tree exactly as Codex left it and say so in the report: it is the evidence, and `preflight` reports `code-dirty` until a human clears it. `escalations` exits `1` while that file is non-empty, and `preflight` reports `blocked-escalation` until oiler empties it.

## One session per task

The whole loop for a single task must finish inside one Claude session, because the plugin's `SessionEnd` hook deletes the session's jobs, which takes the job id and the resume target with it. Compaction inside a session is fine: the ledger, not your context, is what `status` reads to resume.

Do not start a task you cannot finish. If a session is ending, close the current task through step 8 first, or leave it undispatched. A dispatched task with no `5.<n> complete` line resumes cleanly at the top of the loop, and the re-dispatch is fresh.

## Preflight

With executor `codex`, `preflight` adds one check:

```
codex-unavailable: run /codex:setup (<detail>)
```

The script runs the companion's `setup --json`, which reports node, Codex CLI, and auth state with no model turn, and requires `ready: true`. That is the whole of what it can see. It cannot see the dispatch sandbox, which is `workspace-write` with the repository's `.git` mounted read-only, and that is why Codex never commits and step 5 of the loop does. A clean `preflight` prints `preflight: ok (<n> checks)`, so a passing probe is visible rather than silent. Run `/codex:setup`, then re-run `preflight`. Do not dispatch a task while this finding stands: a dispatch into an unauthenticated CLI returns empty, which you would read as a delivery failure and retry.
