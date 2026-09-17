# Build engagement

A build engagement runs from intake to close in one conductor session, inside a scaffold workspace: a directory holding a `docs/` repository and a `code/` repository. You hold the goal and the boundaries, you write the spec body, and you decide what happens to every finding that comes back. Seats report and never write. `orko.py` owns the paths, the ledger, the dispatch prompts, and every record it mints. The `docs/` repository is the record, so a week later the run is readable from committed files with no session history. The contract for what lands where is [record.md](record.md); this file is the order you do it in. orko drafts and never signs. Every record starts at `draft` or `proposed`, every human field stays `null`, and the run stops twice at a field only a human can set.

Every script call in this file is written as `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py <subcommand>`. If `${CLAUDE_SKILL_DIR}` is empty in your Bash call (it substitutes when the skill is invoked as `/orko`; it does not when SKILL.md is merely read), use `~/.claude/skills/orko/scripts/orko.py`; `~/.claude/skills/orko` is a symlink to the skill folder, so both paths reach the same file, and both are in `allowed-tools`. Never use shell command substitution anywhere in a run: the prefix matching behind `allowed-tools` cannot see through it, so a substituted command produces a permission prompt, and a permission prompt in the middle of a long dispatch is invisible. Where a command needs a value another command produces, run two commands: read the value, then pass it.

Git calls you make yourself are `git -C docs ...` and `git -C code ...`. The workspace root is not a repository, so a bare `git` from it reaches whatever repository happens to sit above it.

## Startup sequence

Run these in order, before writing anything. The order matters: the run cannot be named until `init` has minted its slug, and both branches are named from that slug.

**1. Read what the workspace already decided.**

`cd` to the workspace root and stay there for the whole run; a Codex dispatch needs no `cd` either, because its working directory travels on its dispatch line as `--cwd`. `cd` persists across Bash calls in Claude Code, so a single `cd` elsewhere silently breaks every `git -C docs` call and every relative path for the rest of the run. Every command that changes directory ends by returning: `cd docs && ... && cd ..` is the only sanctioned form. Confirm `pwd` is the workspace root before any `orko.py` call that omits `--workspace`, and prefer passing `--workspace <path>` on every call so the working directory is irrelevant. Then read, in this order: `docs/OBJECTIVE.md`, `docs/STATUS.md`, the active version's README plus its `SCOPE.md`, the accepted specs in that dossier, and `docs/design/`. You are joining a project in progress, and the goal you were handed was written by someone who may not have read all of it. Report any conflict between what you read and the goal, per the authority order in `docs/AGENTS.md`. Never reconcile one silently. A goal that contradicts an accepted spec or the version's scope is a question for oiler at intake, not a judgment call for you at step 1.

**2. Look for an existing run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py status --workspace <path>
```

This prints every run in that workspace as JSON: the header fields, `next_step`, `next_task`, and every record minted so far with its path and last committed hash. If one is incomplete and its topic matches what oiler just asked for, offer to resume it instead of starting fresh. Resume keys on the slug, which is derived from the topic, so a goal phrased even slightly differently mints a second run against the same version. When you resume, copy the `topic` string out of that JSON verbatim and pass it to `init`; after a compaction that JSON is the only place the original topic still exists.

**3. Ask the one intake round.**

Ask, in a single message and nothing else:

- The workspace path, confirmed.
- The owner name that goes in every record's `owner` field.
- The executor: `claude` (the default, through `superpowers:subagent-driven-development`) or `codex`.
- The boundaries: what this run may and may not touch.

In the same message, state what you already read so oiler can override it in one reply: the active version and the delivery profile from `STATUS.md`, the review tiers, and, when the executor is `codex`, that the dispatch inherits the model and effort from `~/.codex/config.toml` unless a slug is named here. Ask nothing else. Every other decision in a build is yours to make afterwards, inside those boundaries.

**4. Create or resume the run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py init build "<goal>" --workspace <path> --owner <name> --boundaries "<text>" --trailer "<line>" --trailer "<line>"
```

Add `--executor codex` when oiler chose Codex, plus `--codex-model <M>` and `--codex-effort <E>` only when a slug and an effort were named. Add `--version <MAJOR.MINOR>` only to override the dossier `STATUS.md` names. `--trailer` is repeatable and carries the attribution lines every commit the script makes reproduces verbatim, the commit of a Codex delivery included; a Codex dispatch reproduces none of them, because its prompt carries no trailers at all. The mode is positional and fixed at `init`: a run created as `build` cannot later be resumed as `analysis`. The goal string is the slug, the branch name, and the topic that resumes the run, so write it as one sentence with no trailing punctuation and no file paths in it. The slug truncates to 60 characters on a word boundary.

Read `slug`, `run_dir`, `ledger`, `escalations`, `tasks`, `findings_dir`, `context_dir`, and `next_step` out of the JSON. Never construct a path. Record paths are not in there: those come from each `record` command's own JSON as it mints them.

`init` writes one line into the record: the run's In progress bullet in `docs/STATUS.md`. Startup step 5 commits it, before `preflight`. `next_step` tells you where to start: `0` on a new run, higher on a resume, and `null` when every step is complete. On `null`, go straight to *Ending*. To resume, run the same `init build` command with the same goal. It re-derives the slug, finds the existing ledger, and returns `resumed: true` with the resume point.

**5. Branch both repositories, commit the intake line, then preflight.**

```bash
git -C docs checkout -b orko/<slug>
git -C code checkout -b orko/<slug>
```

On a resume the branches exist, so use `git -C docs checkout orko/<slug>` and the same for `code`; `checkout -b` fails on an existing branch. Then commit the In progress line `init` wrote, because `preflight` reports `docs-dirty` while it is uncommitted. On a resume `init` writes no line, so there is nothing to commit: skip this `commit docs` and go from the checkout straight to `preflight`, because `commit docs` with nothing staged exits `2`.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "Start <topic>" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py preflight --slug <slug> --workspace <path>
```

`preflight` checks in code what prose used to ask you to check, and prints its findings in this order:

`uv-missing` says `uv` is not on PATH, and every script call needs it. `workspace-invalid: <name>` names `docs-not-a-repo`, `code-not-a-repo`, `versions-missing`, or `spec-check-missing`. `docs-dirty` and `code-dirty` mean modified tracked files. Untracked files are ignored by preflight, because a reviewer seat that ran the test suite leaves caches and lockfiles behind and `commit` cannot sweep them in; `check delivery` reads them instead, because an uncommitted working tree is how a Codex delivery arrives, and drops only the tool leftovers [codex.md](codex.md) lists. So a delivery made of new files leaves preflight silent, and `git -C code status --short` is what shows it. `docs-on-default-branch` and `code-on-default-branch` mean a build is sitting where it must never run. `dossier-inactive` means the version dossier is neither `active` nor `proposed`. `spec-not-accepted`, on a resume at step 5 only, means a human has not set `status: accepted`. `codex-unavailable: run /codex:setup (<detail>)`, with executor `codex` only, means the companion reports the CLI is not ready; the probe reads node, the CLI, and auth only, and cannot see the dispatch sandbox, which is `workspace-write` with `.git` mounted read-only, which is why the script commits a Codex delivery and Codex never does. `blocked-escalation` means `escalations.md` is non-empty, and only oiler empties it.

Exit `1` prints one finding per line and stops intake: fix the named condition and run it again. Exit `2` means the run could not be loaded, which is a bad slug or an unresolvable workspace, not an artifact defect. Run `preflight` after the branch switch and the startup commit, not before: run earlier, it reports the two default-branch findings and the `docs-dirty` line `init` itself wrote, on every fresh run. Two findings are resume-only and pass on a fresh run: `spec-not-accepted` fires only once the run reaches step 5, and `blocked-escalation` only once `escalations.md` could exist. On a fresh run their exit `0` means "not yet applicable", not "checked and clean". A clean run prints `preflight: ok (<n> checks)`, so a passing Codex readiness probe is visible rather than silent.

**On a resume, reconcile before you author.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py status <slug> --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py escalations <slug> --workspace <path>
```

A `last_status` of `dispatched` means a round started and the ledger never recorded it finishing. That is what a compaction mid-dispatch looks like, and it is not proof the seats never delivered: list the step's findings directory first and read what is there. Re-dispatching a seat whose findings file already exists spends a second dispatch and returns a second copy of the same review. `status <slug>` also prints `dispatched_base`, the SHA on the most recent `dispatched` line for the resume step, and `next_task`, which is where a Codex step 5 picks up. Run `escalations <slug>` regardless of where you are resuming: `escalated` is recorded alongside `complete`, so `next_step` still points forward past an unresolved conflict, and a resume that trusts `next_step` alone walks straight into building against it.

## Why two stock gates are skipped

orko build deliberately overrides two places where stock superpowers stops for a human:

- `superpowers:brainstorming` and its **User Review Gate**, which asks the human to review the spec before a plan is written.
- `superpowers:writing-plans` and its **Execution Handoff**, which asks which execution approach to use.

This is authorized, not a workaround. `superpowers:using-superpowers` states that user instructions take precedence over skills, and the `/orko build` invocation and the intake answers *are* that instruction. Nothing is being slipped past anyone, and the scaffold's own gate sits between the two: no implementation starts until a human sets the spec to `accepted`. Do not "correct" this back. A future reader who restores both gates turns orko build into an ordinary workflow with extra machinery, which is the one outcome it exists to prevent.

## The steps

Each step ends with its ledger line. `complete` is the only status that advances the run, so record it every time a step's work actually finished. Run `commit docs` after every `record` write: a record that is not committed has no hash in the ledger, so the overwrite guard cannot see the next write to it: it is unguarded until it is committed. Step summaries have no record of their own. What a reader could not reconstruct from the artifacts goes where it belongs: a seat that failed delivery twice goes in the review's Scope and method section, as do the lenses you dropped; a tier change made after intake goes in your narration to oiler. The scaffold's rule is one record per decision that matters, and a step summary is not one.

### 0 Intake

Startup has already run `init`, branched both repositories, committed the In progress line, and cleared `preflight`. Confirm the startup commit landed, then close the step:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 0 complete --slug <slug> --workspace <path>
```

### 1 Spec

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record spec --slug <slug> --title "<title>" --workspace <path>
```

The script copies the scaffold's spec template, mints `SPEC-NNN`, fills the frontmatter, updates the version README index, and prints JSON with the path. Read the path from that JSON and write the body into it, in the shape *What the checks require* prescribes below. Delete the template's example Given/when/then lines rather than editing around them. Do not invoke `superpowers:brainstorming` here. It starts its own discovery round and its own gate, and the intake round has already settled what that round would ask.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py check spec SPEC-NNN --slug <slug> --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "SPEC-NNN: <title>" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 1 complete --slug <slug> --workspace <path>
```

Exit `1` from `check spec` is a real defect: one repair against the reported findings, then stop if it fails again.

### 2 Spec review

Pick the lenses. The default is all four in [spec-reviewer.md](spec-reviewer.md): `requirements`, `architecture`, `testability`, `security`. Drop one only when it has nothing to examine, and say which you dropped and why in the review's Scope and method.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 2 dispatched --slug <slug> --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt spec-review <slug> --lens <lens> --workspace <path>
```

`dispatched` does not advance the run; it tells a resumed session that a round started, so it checks the findings directory instead of dispatching again. `prompt` creates `findings/2/` and refuses to run at all once the run is complete. Dispatch one `general-purpose` subagent per lens at `opus`, with that stdout as the entire prompt, byte for byte. Add nothing: no summary of the spec, no authoring rationale, no list of areas you are worried about. You wrote the spec, so you cannot see what you failed to consider, and that blind spot is exactly what a fresh reader finds. Send all the dispatches in one message so the seats run in parallel. When they return, check delivery: each seat's file must exist at `<findings_dir>/2/<lens>.md` and carry the FINDINGS schema, including one `#### F<n>` block per finding. A seat that returned a receipt but wrote no file gets one re-dispatch with the same prompt. A seat that fails twice is recorded as failed in the review's Scope and method, and the step proceeds with the seats that delivered.

Then mint the review over what they wrote:

```bash
git -C docs rev-parse HEAD
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record review --slug <slug> --title "<title>" --role spec --reviews SPEC-NNN --revision <sha> --from-findings .orko/<slug>/findings/2 --seat requirements --seat architecture --seat testability --seat security --workspace <path>
```

Name every seat with `--seat`, in the order you want the findings to read; unnamed seats are ordered lexically by filename, which is rarely what you want. The script renders one `### F<n>` block per finding, each starting at `Disposition: open`. You write the Summary, Unresolved risks, and Conclusion.

Then decide every finding, one at a time. For an accepted finding, edit the spec first, then record the disposition:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record disposition --slug <slug> --review REVIEW-NNN --finding F3 --disposition accepted --workspace <path>
```

`accepted`, `rejected`, `resolved`, or `noted`, once per finding. `noted` is for a finding whose recommendation is no change. A finding whose fix belongs in the other artifact is `resolved` with the target named in your edit, and applied when that artifact's step runs. Do not edit an artifact outside its own step: the ledger has no line for it.

A seat's `scope:` mark is a recommendation to escalate, not a determination. A finding is outside boundaries only when acting on it would touch a file or behavior the intake boundaries excluded. When one genuinely is, route it per *Routing a change after acceptance* in [record.md](record.md), write the escalation into `.orko/<slug>/escalations.md` yourself, and stop.

**The usual path, with nothing escalated.** Re-run the check on the edited spec, then close the step. The second check is not redundant: folding several findings into a spec can strand an edit mid-sentence or empty a required section the same way writing it can. Commit before the ledger lines, or the minted review and its dispositions stay uncommitted, the ledger carries no hash for them, and the resume opens on `docs-dirty`:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py check spec SPEC-NNN --slug <slug> --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "REVIEW-NNN: spec review" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 2 complete --slug <slug> --workspace <path>
```

**Only when a finding escalated**, add one more line after `complete`, never instead of it, and stop:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 2 escalated --slug <slug> --workspace <path>
```

### 3 Plan

The plan is drafted by a seat, not by you. It is long, mechanical against a fixed spec, and benefits from a reader who has not spent a step arguing with reviewers. Mint the record first so the seat has a template to write into.

```bash
git -C code rev-parse HEAD
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 3 dispatched --slug <slug> --commit <sha> --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record plan --slug <slug> --title "<title>" --implements SPEC-NNN --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt plan-write <slug> --workspace <path>
```

Read the SHA from `git -C code rev-parse HEAD` and pass it to `ledger` as its own command, so the base survives a compaction mid-dispatch. On a fresh run nothing has landed on the code branch yet, so this is the pre-run HEAD, which is correct. Dispatch one `general-purpose` seat at `opus` with that stdout as the entire prompt. It writes two files: the `PLAN-NNN` body at the record path, and the task list at `.orko/<slug>/tasks.md`. Check both exist, then read and edit both yourself. The plan is your artifact and the seat's draft is a draft. Read every `**Acceptance:**` line yourself before the first dispatch, and reject any that is not the repository's own test or lint runner: the script runs that line as a shell command with your privileges. Every path in `tasks.md` is relative to the code repository root, the `**Files:**` lines, the acceptance command, and every `Run:` line alike, because `check delivery` diffs and runs there. The Global Constraints must not forbid `docs/testing/README.md` in the code repository: it is the scaffold's requirement-to-test map, every task's dispatch writes a row there, and the boundaries you recorded at intake are read with that one file inside them.

Your edits go into the committed `PLAN-NNN` and `tasks.md` in place. `CHANGE-CONTROL.md` permits editing a draft directly, and the overwrite guard exists to protect a human's edit, not to stop yours. After editing, re-run `check spec --require-plan` and `check tasks`, then `commit docs`, which records the new hash.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py check spec SPEC-NNN --slug <slug> --require-plan --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py check tasks .orko/<slug>/tasks.md --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "PLAN-NNN: <title>" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 3 complete --slug <slug> --workspace <path>
```

Use `--require-plan` from here on. Without it, a spec whose plan is missing or whose `implements:` list is a flow list passes with a warning and no mapping checked at all. `--require-plan` also reports `plan-approval-signed` when a plan whose status is exactly `draft` carries a value in the Delivery decisions `Approved by` column. Clear the cell: a seat that wrote a name there forged an approval no human gave. The check is scoped to `draft` on purpose. The gate sets the plan to `in_review` before a human signs, so a signature there is the real one and step 5 must not stop on it. A cell still holding the template's bracketed placeholder is not a signature either; `spec-check` fails that on its own. `tasks.md` is scratch and is never committed; it is regenerable from `PLAN-NNN`, and `commit docs` stages only recorded paths, so it cannot ride along.

### 4 Plan review

Identical to step 2, against the plan plus `tasks.md`. The command is `prompt plan-review`, the default lenses are the four in [plan-reviewer.md](plan-reviewer.md), `coverage`, `interfaces`, `placeholders`, and `tests`, and the findings land in `findings/4/`. Read the revision with `git -C docs rev-parse HEAD` as its own command, then mint `record review --slug <slug> --title "<title>" --role plan --reviews PLAN-NNN --revision <sha> --from-findings .orko/<slug>/findings/4`. Your edits go into the committed `PLAN-NNN` and `tasks.md` in place, as in step 3. After them, re-run both `check spec SPEC-NNN --slug <slug> --require-plan` and `check tasks .orko/<slug>/tasks.md`, then `commit docs`, which records the new hash, then `ledger 4 complete`, and `ledger 4 escalated` after it when a finding escalated. `commit docs` comes before the ledger lines on the escalation path too. The plan reviewer's prompt already carries the spec path: it judges the plan against the spec, not against your intent for it.

### The gate

The run stops here, before any implementation.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record status --slug <slug> --id SPEC-NNN --status in_review --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record status --slug <slug> --id PLAN-NNN --status in_review --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "SPEC-NNN, PLAN-NNN: ready for review" --workspace <path>
```

Then report, in one message: the spec path, the plan path, both review paths, and the four fields a human sets, which are `status: accepted` and `approved_at` on the spec, `approved_by` on the spec review, and `approved_by` on the plan review. Name all four. Say that the human commits the acceptance edit on `orko/<slug>` in `docs/` and then resumes by running the same `init build` command with the same goal from the workspace root. An uncommitted edit stops the resume at `docs-dirty` before `preflight` ever reaches `spec-not-accepted`. Report the `release-check.sh` selection fragility described in [record.md](record.md) to oiler here, and change nothing about the scaffold's scripts from inside a run.

### 5 Execute

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py preflight --slug <slug> --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py check spec SPEC-NNN --slug <slug> --require-plan --workspace <path>
```

`preflight` at step 5 confirms the spec is `accepted` and re-records the hash of every record the ledger names that HEAD holds, because the gate asks a human to edit the spec and both reviews, so none of those edits is reported as tampering on the next write. It re-records only on a preflight that found nothing, from the working tree of a repository the dirty checks just passed, so the bytes it hashes are the committed ones; an uncommitted hand edit to a committed record is `docs-dirty` at exit `1` first, so the old floor stands and the guard keeps tripping. A record no commit holds gets no floor, and `preflight` says so on stderr: it is unguarded until it is committed. Report the `check spec` output, which the workspace `AGENTS.md` asks for before implementation begins.

**Executor `claude`.** Invoke `superpowers:subagent-driven-development` with the `tasks.md` path. It owns the task loop, its own ledger, per-task review, and its model selection; do not duplicate or override any of it. Inside step 5 it runs that per-task loop only, an implementer plus a task review per task. orko's step 6 is the whole-branch review and step 7 owns the pull requests, so do not run SDD's Final Review, its fix wave, its workspace deletion, or `superpowers:finishing-a-development-branch`; record `ledger 5 complete` once the last task's review is clean. SDD's own ledger lands in `<the nearest git root above the workspace>/.superpowers/sdd/tasks/`, because the orko workspace is not a repository and every run's plan file is named `tasks.md`, so runs collide there. Leave it where it lands and never delete it from inside a run.

**Executor `codex`.** Run the loop in [codex.md](codex.md), once per task, starting at the `next_task` that `status` reports. It records `ledger 5.<n> dispatched --commit <sha>` and `ledger 5.<n> complete` per task, and those sub-steps do not advance the run.

Either way, when the last task is done:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 5 complete --slug <slug> --workspace <path>
```

A requirement whose plan row says `Performed by: owner` is reported as pending at close, never performed by you. Behavior the accepted spec does not define stops the run: `record amendment` when the intake boundaries already authorize it, otherwise `record decision`. Either way, write the escalation, record `ledger 5 escalated`, and stop. Recording an amendment does not resume the run; only the human does.

### 6 Code review

The diff range is the branch's own work in the code repository. Read the default branch ref, then the point the branch left it. `symbolic-ref` prints `origin/<name>` when a remote sets one, and exits `128` with `fatal: ref refs/remotes/origin/HEAD is not a symbolic ref` when it does not. Read that exit as unset, not as a stop: it is the one non-zero git exit in this skill that is not one. Fall back to `master`, or `main` where that is the repository's default:

```bash
git -C code symbolic-ref --short refs/remotes/origin/HEAD
git -C code merge-base <origin/default> HEAD
mkdir -p .orko/<slug>/findings/6 && git -C code diff <base>...HEAD > .orko/<slug>/findings/6/branch.diff
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 6 dispatched --slug <slug> --commit <base> --workspace <path>
```

Every seat reviews `git -C code diff <base>...HEAD`, the same range, and reads it from `.orko/<slug>/findings/6/branch.diff`, which you write before dispatching. Name four things in every step-6 seat prompt: that file, the code repository's absolute path, the base sha, and the head sha. The two tool-running seats' prompts are yours to write, on `prompt seat`'s shape — the FINDINGS schema, substantiate every claim, write then return, never sign — because no script command builds them yet. A tool that reports a different repository, a different base, or an unreachable sha has not reviewed the range: the seat records that in its Confidence line as a failed tool run, reviews the diff file directly, and says so, and you name any such substitution in `REVIEW-NNN`'s Scope and method. Dispatch, in one message:

- one `general-purpose` seat at `opus` that runs `/code-review` with the diff file as its target,
- one `general-purpose` seat at `opus` that runs `/security-review` from inside the code repository,
- any domain seats the branch warrants, at `sonnet`, dispatched through `prompt seat`.

A domain seat needs a context file. Write it to `<context_dir>/<seat>.md` first, carrying the diff range, the paths to look at, the goal, and who the work is for, then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt seat <slug> --seat <name> --question "<one question>" --context-file <run_dir>/context/<name>.md --workspace <path>
```

Findings land in `findings/6/`. Mint the review over them with `record review --role code --reviews SPEC-NNN --revision <code sha> --from-findings .orko/<slug>/findings/6`, reading the SHA from `git -C code rev-parse HEAD` first. Decide every finding as in step 2, with one difference: an accepted finding is fixed on the branch by dispatching an implementer, or by re-dispatching Codex, not by you editing code. The conductor decides and records; it does not implement. The implementer commits its own changes on the branch with the run's trailers and reports the sha, exactly as the task implementers do; a re-dispatched Codex commits nothing, and a step-6 fix is not task-scoped, so neither `check delivery --task` nor `commit code --task` applies here: write the re-dispatch prompt yourself, naming the accepted findings by their `F<n>` labels, the files, and the same no-commit rule the task prompt carries, and dispatch it as [codex.md](codex.md) says; then verify the fix as the step-6 seats did, by re-reading the uncommitted working tree yourself (`git -C code diff` for edits, `git -C code status --short --untracked-files=all` for new files) and having one report-only seat re-run the repository's test command; then land it with `commit code --slug <slug> --message "REVIEW-NNN: <what the fix addresses>" --path <file> --workspace <path>`, one `--path` per repo-relative file that status listing shows, never a directory. Exit `2` there, `nothing to stage` or `nothing changed`, means nothing stageable changed: the re-dispatch wrote nothing, or it wrote to a path you did not list, which the skip line on stderr names. Otherwise `commit code` at this step is for what the script minted, an `ADR-NNN`, and for anything a `record` command touched, so run it only when the step produced one of those, and otherwise skip it: with nothing recorded to stage it exits `2`. For code the run wrote outside the record, name each file: `commit code --slug <slug> --message "<subject>" --path <repo-relative file> --workspace <path>`. A finding escalates only when the work cannot be complete without acting on it and acting on it would leave the boundaries. Every other out-of-bounds finding is deferred: it keeps `Disposition: open` and gets a `record risk` bullet under the version README's risks, so it outlives the run. Two duties before you close the step. Check whether `code/ARCHITECTURE.md` or `code/DESIGN.md` describes something the branch changed materially, and update it. Write an `ADR-NNN` with `record adr` for any consequential in-bounds technical choice the implementation made; an in-bounds choice recorded as an ADR is not an escalation and does not stop the run. When a finding does escalate, write `escalations.md`, run `commit docs`, then add `ledger 6 escalated --slug <slug>` after the `complete` line, and stop.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "REVIEW-NNN: code review" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 6 complete --slug <slug> --workspace <path>
```

### 7 Close

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py record close --slug <slug> --summary "<text>" --changelog "Added: <text>" --changelog "Fixed: <text>" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit docs --slug <slug> --message "Close <topic>" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py commit code --slug <slug> --message "Close <topic>" --workspace <path>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 7 complete --slug <slug> --workspace <path>
```

`record close` sets `STATUS.md` `as_of` and rewrites the run's In progress line to "awaiting acceptance", inserts each `--changelog` entry under its subheading in both changelogs, refreshes the version README index, and writes the two pull request bodies. `--changelog` is repeatable and its section is `Added`, `Changed`, `Fixed`, `Removed`, or `Security`. It is idempotent, so a rerun after an interruption is safe.

Then push both branches and open both pull requests, each `gh` call from inside its own repository:

```bash
git -C docs push -u origin orko/<slug>
git -C code push -u origin orko/<slug>
cd docs && gh pr create --title "<topic> (SPEC-NNN)" --body-file ../.orko/<slug>/pr-docs.md && cd ..
cd code && gh pr create --title "<topic> (SPEC-NNN)" --body-file ../.orko/<slug>/pr-code.md && cd ..
```

Both `gh` lines end in `cd ..` for a reason: `cd` persists across Bash calls, so a `cd docs` that never returns leaves every later `git -C docs` and every relative body-file path resolving against the wrong directory. Push first: `gh pr create` on an unpushed branch asks the question interactively, and an interactive question inside a Bash call stalls the run with no visible prompt. `ledger 7 complete` is recorded with the two close commits, before the pushes, so a barred or failed push leaves the ledger line standing and the publication pending. If a push fails for want of a remote or credentials, or `gh` is missing or unauthenticated, nothing is lost: the body files are already written. Report both paths, both push commands, and both `gh` commands to the human as pending.

## What check spec and check tasks require

Write to this contract the first time. *Error handling* allows exactly one repair attempt, and it is meant for a real defect, not for discovering the schema by trial. **The spec**, per the scaffold's own `spec-check.sh`, which `check spec` runs and passes through: `product_version` equal to the dossier folder and `owner` set, both written by `record spec`; `serves` naming at least one `OUT-<n>` outcome that `OBJECTIVE.md` lists, which the template seeds as `OUT-1` and you replace with the outcomes the spec advances; at least one `### R<n>` requirement heading; at least one `- Given ... when ... then ...` line under `## Acceptance criteria`; and content under all seven of `## Problem and intended outcome`, `## Users and scenarios`, `## Evidence and classification`, `## Scope`, `## Non-goals`, `## Failure and recovery behavior`, and `## Data, privacy, security, and accessibility`. No bracketed placeholder survives anywhere outside a fence, inline code, a link, a checkbox, or an ID list.

**The plan**, checked through the same command from step 3 on: an `implements:` block sequence naming the spec, one `- SPEC-NNN` per line, never a flow list; a `| SPEC-NNN R<n> |` mapping row for every requirement heading; and verification evidence in each of those rows that is neither empty nor bracketed.

**`tasks.md`**, per `check tasks`: a line carrying both `REQUIRED SUB-SKILL` and `superpowers:subagent-driven-development`; a heading that is exactly `## Global Constraints`; at least one titled `### Task N:` block, since the title is the delivery commit's subject; and inside every task block a `**Files:**` line, at least one `- [ ] **Step` checkbox, and one `**Acceptance:**` line naming the single command that proves the task done. That line holds one backticked command, which prose may follow. The validator and the dispatch read the same command out of it. Every path in the block is relative to the code repository root, because that is where `check delivery` diffs and runs them. The acceptance line is what a Codex dispatch is judged on, so a task without one cannot be dispatched. The checker also rejects `TBD`, `TODO`, `FIXME`, `XXX`, and the vague directives `Similar to Task N`, `add appropriate error handling`, `add validation`, `handle edge cases`, and a bare `Write tests for the above`.

**Every structural marker in `tasks.md` must be live prose, never inside a fence.** The checker blanks fenced blocks before it scans, and inline code spans too for every rule but one, so a document may *document* a forbidden marker without *containing* one. The exception is the `**Acceptance:**` line, which the checker reads with its backticks intact, because the command lives in them. The dispatch reads that line the same way, and both enumerate task blocks from the same fence-blanked text, so a task block shown inside a fence is invisible to both and the two never disagree. The cost is that a required marker written inside a fence is invisible too. `superpowers:writing-plans` presents its mandatory header inside a fence, so copying that template verbatim fails with "missing the mandatory REQUIRED SUB-SKILL header line" against a file that visibly contains it. Lift the header, `## Global Constraints`, and the task blocks out of the fence.

## Reading the script's exit codes

| Exit | Meaning | What you do |
|---|---|---|
| `0` | Success; all checks passed | Continue |
| `1` | Findings, one per line | A real defect in the artifact or the workspace; repair per the table below |
| `2` | Usage or IO error: bad arguments, no such run, an unresolvable workspace, a malformed ID, or a missing dependency | Stop, then report. No repair can fix a malformed invocation, and retrying a `2` in a loop just burns the run |

Never treat `2` as a findings result. `1` means the artifact is wrong; `2` means the command was wrong.

## Ledger statuses

`complete` is the only status that advances the run. `orko.py` computes `next_step` by counting integer `step N complete` lines and nothing else, so the other three statuses are annotations on top of it, and `5.<n>` sub-steps never advance the run on their own.

- **`dispatched`** is written immediately before a round of seats goes out, so a compaction mid-dispatch leaves a record that the round started. With `--commit` it also pins the diff base.
- **`complete`** is recorded whenever a step's work actually finished, every time, without exception. It is the only thing stopping a post-compaction resume from re-dispatching a review round over an artifact already reviewed.
- **`escalated`** is an *additional* line, written immediately after that step's `complete` line, never instead of it. Recording only `escalated` pins `next_step` at that step forever and the resume re-runs it. One carve-out: for a Codex sub-step `5.<n>`, `escalated` is written alone, because a `5.<n> complete` would advance `next_task` past a task that never delivered.
- **`failed`** is written on its own, *without* a `complete` line, because the step's work did not finish. Not advancing is the point: the step has to run again.

## Error handling

| Condition | Behavior |
|---|---|
| `check spec` exits `1` on a freshly written spec or plan | One repair by the same author against the findings. A second failure stops the run and reports both findings sets. |
| `check spec` exits `1` after you fold in review findings | Repair your own edit. The reviewer never touched the file, so there is no reviewer intent to undo. |
| `check spec` or `check tasks` exits `2` | The command was wrong or the workspace is unresolvable. Stop and report. Never retry. |
| A reviewer seat returns without a findings file | Re-dispatch once, naming what failed, with the same prompt from `prompt`. A second failure records the seat as failed in the review's Scope and method, and the step proceeds. |
| A Codex dispatch returns empty or a failed job | A delivery failure. Re-dispatch once per the loop in [codex.md](codex.md). A return carrying no job id is not one: resolve the job with `codex wait latest`. |
| `check delivery` fails twice on one task | `record decision`, `record adr`, or `record delivery-decision` per the routing rule, `commit docs`, `ledger 5.<n> escalated`, stop. |
| Implementation needs behavior the accepted spec does not define | Stop. `record amendment` when the boundaries already authorize the behavior, otherwise `record decision`. |
| A finding is outside boundaries | Route it to an amendment, `DEC-NNN`, `ADR-NNN`, or a delivery decision row, append to `escalations.md`, record `complete` then `escalated`, and stop. On a Codex sub-step `5.<n>`, `escalated` stands alone. |
| A human edited a record orko wrote | `record` refuses to overwrite a file whose hash differs from the last committed one. Read the change, report it, and continue from the human's version. The gate's expected edit is exempt because a clean `preflight` re-records the floor from the working tree of every record HEAD holds, once the dirty checks pass. |
| The human sets `accepted` and later returns the spec to `draft` | `preflight` at step 5 reports `spec-not-accepted`. Stop and report. |
| A push fails, or `gh` is missing or unauthenticated at close | The body files are already written. Report their paths, both push commands, and both `gh pr create` commands for the human. |
| `preflight` exits `1` | Stop and print the findings. A build never starts on a default branch, in a dirty repository, or without `uv`. |
| The session compacts mid-run | Re-invoke `/orko build` from the workspace root. `status` names the resume step, `next_task`, the executor, and every record path. Reconcile `dispatched` entries against the findings directory and run the escalation gate before writing anything. |
| `${CLAUDE_SKILL_DIR}` is empty in Bash | Fall back to `~/.claude/skills/orko/scripts/orko.py`. |
| Script exit `2` | Stop and report. Never retry a usage error. |

## Ending

**At the gate**, after step 4, report the spec path, the plan path, both review paths, the lenses that ran and any you dropped, the four human fields by name, the instruction to commit that edit in `docs/` on `orko/<slug>`, and the `init build` command that resumes the run. Do not start implementation. **After close**, report the two pull request URLs, or, when the pushes were barred or failed, both push commands and both `gh pr create` commands as still pending, because `ledger 7 complete` is already recorded and no resume returns to them. Report both branches, the count of findings by disposition, and what stays human: `approved_by` on the code review, `ACCEPT-NNN`, the release record, and the tag. orko performs none of those, and `RELEASE.md` places the move to Recently completed after the tag.

**An outstanding escalation overrides both.** Print the record ID you raised, the artifact paths, and the escalation contents. State that the run is blocked and that clearing it means oiler emptying `escalations.md`, then stop. Do not print a resume instruction and do not invoke an executor: implementation is precisely what the escalation is blocking, and an ending that offers a resume line beside an unresolved conflict invites someone to take it.

## Narration

Emit one short line at each step transition naming what just finished and what is starting. Seat rounds and Codex dispatches run for many minutes with no output, so the ledger and those lines are the only signal that a long run is alive rather than hung. One line, not a status report; a running commentary defeats the purpose.
