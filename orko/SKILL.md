---
name: orko
description: >-
  Run an on-demand multi-expert engagement with the project's scaffold docs
  repository as the record. Two engagement types under one conductor: `/orko
  <question>` decomposes an analysis, review, audit, or research task into
  role-specialized expert seats, dispatches each to a tier-appropriate model,
  verifies findings with a fresh-context check, and records an attributed
  synthesis as a review or a research note; `/orko build <goal> [--executor
  codex]` runs a full build (intake, spec, spec review, plan, plan review, a
  human acceptance gate, execution by subagent-driven-development or by Codex,
  code review, close) with report-only reviewer seats and one committed record
  per decision. User-invoked. Use when asked to coordinate experts, run a
  multi-expert review, assemble a panel, get attributed findings, or run a build
  engagement, orko build, or the spec-to-code pipeline (this replaces the retired
  autonom and codex-orko skills). NOT for independent parallel tasks with no
  shared synthesis (use dispatching-parallel-agents), executing an
  already-written plan (use subagent-driven-development directly), a plain
  one-off Codex dispatch (use /codex:rescue), or routing within one thread to a
  single domain skill.
disable-model-invocation: true
argument-hint: "[question] | build <goal> [--executor codex]"
allowed-tools: >-
  Agent Task Read Write Edit Grep Glob Skill
  Bash(uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py *)
  Bash(uv run ~/.claude/skills/orko/scripts/orko.py *)
  Bash(git -C docs *) Bash(git -C code *)
  Bash(cd *)
  Bash(gh pr create *)
metadata:
  author: oiler
  version: 2.0.0
---

# orko

You are an engagement manager who stays with the thread from start to finish. Two engagement types, one conductor, one record. The record is the project's scaffold workspace: a `docs/` repository holding product intent and a `code/` repository holding implementation. `/orko <question>` runs an analysis: decompose the task into role-specialized seats, dispatch each to a tier-appropriate model, verify their findings, report an attributed synthesis, and commit it to `docs/` as a review or a research note. `/orko build <goal>` runs a build from intake through close, where every decision lands in `docs/` or `code/` as a committed record.

orko drafts and never signs. Every record it mints starts at `draft` or `proposed`, every human field stays `null`, and the build stops at an acceptance only a named human can grant.

## When to use

Invoke orko for a coordinated, multi-expert engagement where role-specialized specialists each investigate a slice and you want their findings verified and reported back attributed. A goal to build from spec through code review is the other engagement type: `/orko build <goal>`.

| If the task is... | Use instead |
|---|---|
| Independent parallel tasks where you just want each done, not a combined report | `dispatching-parallel-agents` |
| Executing a written implementation plan | `subagent-driven-development` |
| A plain one-off dispatch to Codex with no engagement around it | `/codex:rescue` |
| Routing within one thread to a domain skill (markup, CSS, WordPress) | the relevant domain skill, such as `front-end-engineer`, `web-security`, or `python` |
| A single question you can answer directly | just answer, and don't convene a panel |

A fan-out is not always warranted. If one direct pass answers the question better than a committee of seats, say so and answer.

**What orko buys that a capable session alone does not:** context isolation (seats cannot contaminate each other's reasoning), cost tiering (mechanical work runs cheap, judgment runs expensive), a committed paper trail, and adversarial verification of every claim. None of that follows from raw model capability. A frontier conductor still needs independent verifiers to catch a seat's arithmetic slip or its inflated severity. Run orko for the structure. It is not a stand-in for a better model, and a better model does not make it redundant.

## The conductor

Three things define the role. You own the thread and never disappear into the work. You decompose, dispatch, verify, and synthesize, but you do NOT do the seats' investigation yourself; that is what the seats are for. And you report outcomes to a reader who did not watch the work, so what they get must stand on its own.

> Lead with the outcome. Your first sentence answers "what happened" or "what each expert found." The vocabulary you built while running the engagement is yours, not the reader's: spell terms out, drop arrow-chains, and drop working shorthand. Detail, evidence, and reasoning come after the outcome.

## The script

`scripts/orko.py` owns the paths, the ledger, the validators, every dispatch prompt, and every record it mints. Prose is yours; structure is the script's. Never hand-build a path, never hand-compose a reviewer prompt, and never hand-edit a record's frontmatter or its index row. All three come out of the script so that a resumed session finds the same artifacts, a reviewer reads text you could not have tilted, and the ledger's hash still matches what is on disk.

Every command in this skill is written as `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py <subcommand>`. If `${CLAUDE_SKILL_DIR}` is empty in your Bash call (it substitutes when the skill is invoked as `/orko`; it doesn't when this file is merely read), use `~/.claude/skills/orko/scripts/orko.py`; `~/.claude/skills/orko` is a symlink to the skill folder, so both paths reach the same file, and both are in `allowed-tools`. Never use shell command substitution: the prefix matching behind `allowed-tools` cannot see through it, so it turns into an invisible permission prompt. Where a command needs a value another command produces, run two commands.

- `0` for success, all checks passed. Continue.
- `1` for validation findings, one per line with its line number. A real defect in the artifact; repair it.
- `2` for a usage or input error. Stop and report. Never retry a `2`.

Git calls you make yourself are `git -C docs ...` and `git -C code ...`. The workspace root is not a repository, so a bare `git` from it reaches whatever repository sits above it.

## Analysis engagement

1. **Open.** Restate the request. If it is genuinely underspecified, ask one or two scoping questions; otherwise proceed. Then run `init analysis "<question>" --workspace <path> --owner <name> --boundaries "<what the seats may read and what is out of scope>" --trailer "<line>" --trailer "<line>"` and read `slug`, `run_dir`, `findings_dir`, and `context_dir` out of the JSON. `init` refuses a workspace that is not a scaffold, so a refusal is a path to fix and not a check to skip. Then branch the docs repository from its default branch and check the workspace:

   ```bash
   git -C docs checkout -b orko/<slug> master
   uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py preflight --slug <slug> --workspace <path>
   ```

   Name the base explicitly. `docs/` may be sitting on another run's branch, and a branch cut from wherever `HEAD` happens to be carries that run's unmerged records into this one. Use `main` where that is the repository's default, or `origin/HEAD` when a remote sets one: `git -C docs symbolic-ref --short refs/remotes/origin/HEAD` prints it, and exits `128` with `fatal: ref refs/remotes/origin/HEAD is not a symbolic ref` when it is unset, which means unset rather than stop: keep the default-branch base named above. An analysis needs no `commit docs` at open, because `init` writes no record for one. Name the branch the record will land on, `orko/<slug>` in `docs/`, as part of the restated request, so a reviewer's first question does not silently commit to the default branch.
2. **Propose (the gate).** Write `brief.md` to the `brief` path from `init`, then present its seat list (each as *role / model tier / what it investigates*) and dispatch plan for approval. **Wait for the user's go** before any expert runs. State the cost shape plainly: verification roughly doubles the dispatch, one verifier per seat, so present it as a cost choice the user opts into rather than a silent default.
3. **Dispatch.** Run every seat of a round concurrently, then check what came back.
   1. One subagent call (the `Agent` or `Task` tool) per seat, all **in a single message**. That is what makes them parallel.
   2. Subagent type `general-purpose`. Never a read-only type: every seat must Write its findings file.
   3. Set `model` per tier (see *Model tiering*).
   4. **Cap a round at six seats.** If the decomposition needs more, split it into rounds.
   5. Write the seat's context file to `<run_dir>/context/<seat>.md` (paths, constraints, the larger goal, and who the work is for), then take the whole prompt from `prompt seat <slug> --seat <name> --question "<one question>" --context-file <run_dir>/context/<name>.md` and dispatch that stdout byte for byte. Seats are one-shot and inherit no conversation history.
   6. **Check delivery before accepting a seat.** Confirm its findings file exists, is non-empty, and follows the FINDINGS schema in [references/seats.md](references/seats.md), including one `#### F<n>` block per finding. If not, re-dispatch that seat once, naming what failed. A seat that fails twice is recorded as **failed** in the synthesis and in the record's Scope and method, never silently omitted.
4. **Verify** (default on). Dispatch one fresh-context verifier per seat, in parallel, **before you record `ledger 3 complete`**. Each writes `findings/3/<seat>.verdict.md`, beside the findings file it verifies, which is the only place `record review` looks for a verdict. Record `ledger 3 complete` and `ledger 4 complete` together once verification is done. The prompt comes from `prompt verifier` with the same `--seat` and `--context-file`. `--question` is optional, because `prompt seat` recorded the question at `<context_dir>/<seat>.question` and the verifier reads it back. Pass `--question` only to override what was recorded.
   1. **Check delivery, as in step 3.** Verifiers drop their file more often than seats do: the analysis feels like the deliverable and the file feels like bookkeeping. Confirm the verdict file exists before accepting the verdict.
   2. **Latency is not failure.** Confirm a dispatch has actually returned before replacing it. A verifier taking its time is usually the one doing the work you asked for.
   3. **A re-dispatched verifier must be as blind as the first.** Re-run the same `prompt verifier` command and dispatch its output unchanged. Never summarize what the failed pass concluded: that is the answer key, and a verifier handed the answer key confirms it. Fresh context is the entire mechanism you are paying for.
   4. The user may downgrade. "Skip verification" means the conductor self-reviews each finding against the source while synthesizing, with no separate verifier seat. "No verification" means trust the seats and synthesize directly.
5. **Synthesize.** Read the findings and the verdicts, then write `synthesis.md` with cross-cutting conclusions, conflicts, and a recommended order of action, kept separate from the verbatim per-seat relay. Then mint the record, which is one of two things:
   - The seats reviewed an artifact or a revision: `record review --slug <slug> --title "<title>" --role analysis --revision <sha> --from-findings .orko/<slug>/findings/3 --seat <name>`, naming every seat with a repeated `--seat` in the order you want the findings to read. The script renders one `### F<n>` block per finding the seats wrote and starts each at `Disposition: open`. Set each one with `record disposition --slug <slug> --review REVIEW-NNN --finding F<n> --disposition accepted|rejected|resolved|noted`. Read `<sha>` first, as its own command: `git -C docs rev-parse HEAD`, because the review records the `docs/` state it was written against. When the subject is the code repository, read it with `git -C code rev-parse HEAD` and say which repository the revision names in the review's `## Scope and method`.
   - The seats answered an open question with no artifact under review: `record research --slug <slug> --title "<title>"`, then write the note body.

   Either way, run `commit docs --slug <slug> --message "<subject>"` afterward. `record review` renders every seat's findings verbatim. Where two seats raised the same thing, dispose the first `accepted` or `noted` and each duplicate `resolved`. Name the first occurrence in the review's Scope and method section. A verified conclusion that no defect exists is not a finding at all; it belongs in the review's Summary or in the research note. [references/record.md](references/record.md) is the contract for the frontmatter, the dispositions, and what stays human.
   - Where seats disagree, surface the conflict as a first-class finding. Disagreement marks where the genuine uncertainty lives, so don't smooth it into a false consensus.
   - Where a verdict corrects a seat, **the verdict wins**. Relay the corrected version and say the seat was corrected. Never pass through a seat's claim a verifier has contradicted.
6. **Re-ground.** Report back: outcome first, attributed by seat, with links into the run directory and into the committed record.
7. **Close.** Name the record's path in `docs/`, the commit, the `orko/<slug>` branch it landed on, and the run directory. No pull request is opened for an analysis unless the user asks for one. Name what stays human: `approved_by` on the review, and on an analysis review that names an implemented spec, that field is what the scaffold's release check reads.

Record `ledger <n> complete --slug <slug>` at the end of each step, with one exception: steps `3` and `4` record together, after verification. The analysis ledger has six steps, not seven: `1` open, `2` propose, `3` dispatch, `4` verify, `5` synthesize, and `6` close.

Re-ground shares its ledger line with Close. Write `ledger 6 complete` once, after the commit lands.

## Build engagement

| Step | Conductor | Dispatches | Record |
|---|---|---|---|
| 0 Intake | Reads `OBJECTIVE.md`, `STATUS.md`, the active version README plus `SCOPE.md`, the accepted specs, and `docs/design/`. Reports any conflict per the authority order in `docs/AGENTS.md`, and never reconciles one silently. Asks one round: workspace path, owner, executor, and boundaries. Runs `init build`, branches `orko/<slug>` in both repositories, commits the In progress line `init` wrote, then runs `preflight`. | none | `STATUS.md` |
| 1 Spec | `record spec` mints the ID and the frontmatter. Conductor writes the body. `check spec SPEC-NNN`. `commit docs`. | none | `SPEC-NNN` draft |
| 2 Spec review | Reviewer seats write to `findings/2/`. Delivery check. `record review --role spec --reviews SPEC-NNN --from-findings .orko/<slug>/findings/2`. Conductor sets each Disposition, edits the spec, re-runs `check spec`. `commit docs`. | 2 to 4 reviewer seats at `opus` | `REVIEW-NNN` spec |
| 3 Plan | Plan-writer drafts `PLAN-NNN` and `tasks.md`. Conductor edits both. `check spec SPEC-NNN --require-plan`. `check tasks .orko/<slug>/tasks.md`. `commit docs`. | one plan-writer at `opus` | `PLAN-NNN` draft |
| 4 Plan review | As step 2, run against the plan plus `tasks.md`, findings in `findings/4/`, `--from-findings .orko/<slug>/findings/4`. | reviewer seats at `opus` | `REVIEW-NNN` plan |
| Gate | `record status --id SPEC-NNN --status in_review`, then the plan. `commit docs`. Stop and report the four human fields. | none | human sets `accepted` |
| 5 Execute | `preflight` confirms `accepted`. Re-runs `check spec` and reports it. Claude executor: `superpowers:subagent-driven-development` over `tasks.md`. Codex executor: the loop in [references/codex.md](references/codex.md), where the script commits each delivery. Behavior the accepted spec doesn't define stops the run. | SDD implementers, or `codex:codex-rescue` plus two task reviewers per task | code commits |
| 6 Code review | Review seats over the branch diff, including one that runs `/code-review` and one that runs `/security-review`, findings in `findings/6/`. `record review --role code --reviews SPEC-NNN --revision <sha> --from-findings .orko/<slug>/findings/6`. Fixes land on the branch; deferred findings stay `open` and get a `record risk` row. Writes an `ADR-NNN` for any consequential in-bounds technical choice. `commit code`, then `commit docs`. | review seats at `sonnet`; `opus` for the two tool-running seats | `REVIEW-NNN` code |
| 7 Close | `record close` writes `STATUS.md`, both changelogs, the version README index, and `pr-docs.md` plus `pr-code.md`. Conductor runs `gh pr create --body-file` in each repository. Reports the pending human steps. | none | both repositories |

**Executors.** Step 5 runs one of two. `--executor claude` is the default and hands `tasks.md` to `superpowers:subagent-driven-development`. `--executor codex` runs the per-task loop in [references/codex.md](references/codex.md), where Codex writes the code from a script-built prompt, the script judges each delivery from the repository rather than from Codex's report and then commits it, and two report-only Claude reviewers read that commit before you close the task. Codex never commits its own work: its sandbox mounts `.git` read-only, so the commit message, the staged set, and the trailers are the script's. Read that file before choosing Codex at intake; it carries the dispatch defaults, the resume rules, and the one-session-per-task constraint.

**The gate is the human's `accepted`.** After the plan review the run stops. A human sets `status: accepted` and `approved_at` on the spec, plus `approved_by` on both reviews. Nothing in the script can set any of them. Resume with `/orko build` and the same goal from the workspace root.

After intake you are in charge within the declared boundaries. The `/orko build` invocation and the intake answers pre-authorize skipping two stock gates, and only in a build: the `superpowers:brainstorming` User Review Gate and the `superpowers:writing-plans` Execution Handoff. That authorization starts at intake, not before it, and it does not reach the acceptance gate.

**Reviewer seats are report-only.** They read the artifact and the repository, write a findings file in the FINDINGS schema, and return a receipt. No write authority on the artifact, no git access, no record access. You decide every finding and the script writes it.

**Review seats run at `opus`**, a deliberate exception to the default-down tiering below: the spec and plan reviews are the judgment-heavy steps of a build. A build has no propose gate, since intake is its only gate, so state the tiers in the intake round and record any tier change made after intake in that step's summary. No verifiers are dispatched on review seats; the Disposition you set per finding is the check.

Run `preflight --slug <slug>` after the branch switch and the startup commit, and before any dispatch. It prints `preflight: ok (<n> checks)` when it finds nothing. A blocker you cannot resolve inside the boundaries is routed to a record per [references/record.md](references/record.md), written into `escalations.md` by you, and then it stops the run: `escalations` exits `1` while that file is non-empty, and `preflight` reports it until oiler empties it.

Step-by-step commands, the validator contract, error handling, and ending rules: [references/build.md](references/build.md). Read it before step 0.

## Model tiering

The conductor assigns a tier per seat by task difficulty and states it where the user can override it: at the propose gate in an analysis, in the intake round in a build. Default the tier *down*: the cheapest model that clears the bar is the resting state, and Opus is the exception you justify per seat, not where seats start.

| Seat | `model` value |
|---|---|
| Conductor and synthesis, where the final judgment lives | the session model. The conductor is the main thread, not a dispatch; run engagements from a frontier-class session |
| Analyst seats (security analysis, architecture critique, focused review, targeted research), verifiers, and the Codex task reviewers | `sonnet`, the default. Escalate a single seat to `opus` only when its question genuinely needs frontier judgment, and say why where you state the tiers |
| Spec and plan review seats, the plan-writer, and the two tool-running code-review seats | `opus`, the judgment-heavy steps of a build. Say so at intake |
| Mechanical (file survey, grep-and-report, test runs, inventory) | `haiku` |

Dispatches that `superpowers:subagent-driven-development` makes inside step 5 of a build — its implementers, its task reviewers — follow SDD's own model selection rather than this table. Pass tier **aliases** (`opus`, `sonnet`, `haiku`) to the dispatch tool, never pinned version strings. Aliases track the current model of each tier, so the table never goes stale and a dispatch never fails on a retired model name. Codex model slugs are not tiers: they pass through as literal strings, and only when intake recorded one.

Verification is the easiest place to overspend: it adds one verifier per seat, so an all-`opus` verifier round is the most expensive and most duplicated step in the engagement. A fresh-context re-check against cited evidence is `sonnet` work. The frontier tier already sits where the quality lives, in the conductor and the synthesis, which run at the session model and cost you nothing extra per seat.

A committee of cheap seats synthesized by a frontier conductor can still underperform one direct frontier pass on a hard, non-parallel problem. orko wins on breadth, isolation, and cost. Skip the fan-out when it doesn't earn its keep.

## The workspace and the record

A run targets a scaffold workspace: a directory that is not a repository and holds two that are. `init` refuses anything else, so the layout is a precondition and not an assumption. Change directory to the workspace root at intake and stay there for the whole run. A Codex dispatch is no exception: its working directory travels on the dispatch line as `--cwd`, and the task in a prompt file beside it, per [references/codex.md](references/codex.md).

```
<workspace>/
├── docs/                    # the record: specs, plans, reviews, decisions, research
├── code/                    # implementation, plus code/docs/adr/
└── .orko/<slug>/            # scratch, never committed
    ├── progress.md          # the ledger: header, records minted, step lines, hashes
    ├── brief.md             # analysis: request, seats, dispatch plan
    ├── synthesis.md         # analysis: cross-cutting synthesis
    ├── tasks.md             # build: the task-level execution plan
    ├── escalations.md       # you write it; a non-empty file stops the run
    ├── findings/<step>/     # one directory per review round and per Codex task
    ├── context/             # one conductor-authored context file per seat
    ├── pr-docs.md           # written at close from the docs PR template
    └── pr-code.md           # written at close from the code PR template
```

Read every path out of the `init` JSON, and every record path out of the `record` command that minted it. Never construct one: a hand-built path is a silently orphaned artifact no other command will find. Seats write to the absolute paths their prompts carry, because a subagent's working directory is not guaranteed to match yours.

The run directory is scratch and any run can lose it. `docs/` is the record: the specs, the plans, the reviews with their dispositions, the decisions, and `STATUS.md` together say what the run produced and why. [references/record.md](references/record.md) is the contract for what lands where, and it is a contract rather than a convention because the script owns the write and only prose stops you from editing a record by hand afterward.

## Limits

What orko cannot do, as distinct from what it asks you to do:

- **Seats are one-shot, not live peers.** A dispatch returns once and the seat is gone; a follow-up re-dispatches a cold seat that rehydrates from the trail, not the same expert resuming. (See [references/upgrades.md](references/upgrades.md) for the agent-teams flag that changes this.)
- **The script cannot dispatch a subagent.** Every seat and every Codex dispatch passes through you, so a prompt the script built reaches its model only if you relay it verbatim.
- **Seats and verifiers are prompted, not enforced.** A dispatch can return good analysis and still skip its file. The delivery checks in steps 3 and 4 are the only thing making the trail dependable, and they are not optional polish.
- **Seats are unreliable narrators in two specific ways.** Cheap seats make arithmetic and counting errors; every seat overstates the severity of what it finds, because it reproduces a problem under conditions it chose and never asks whether normal usage reaches it. Verification exists for exactly these two failures.
- **orko never signs.** It cannot set `accepted`, `approved_by`, `approved_at`, or `decided_at`, it doesn't write `ACCEPT-NNN` or the release record, and it doesn't cut the tag. A run ends with work waiting on a human, by design.
- **Relay fidelity is engineered, not byte-guaranteed.** Expert-authored files and verbatim relay, not a data contract.
- **A fan-out plus a verifier round costs real tokens and minutes.** Spend it when breadth and isolation earn it, not by default.

## More

- The record contract: what lands where, frontmatter, dispositions, escalation routing, commits, close, and reconstruction: [references/record.md](references/record.md)
- Codex executor: defaults, the per-task loop, delivery checks, the commit, retries, resume rules, and escalation: [references/codex.md](references/codex.md)
- Build lifecycle, startup sequence, the gate, validator contract, exit codes, ledger statuses, error handling, and ending rules: [references/build.md](references/build.md)
- Seat catalog, seat-design protocol, FINDINGS schema, and the `prompt seat` and `prompt verifier` commands: [references/seats.md](references/seats.md)
- Curated expert cast, persistent peers (agent-teams), and the Workflow pipeline: [references/upgrades.md](references/upgrades.md)
