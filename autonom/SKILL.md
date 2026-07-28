---
name: autonom
description: >-
  Runs oiler's superpowers development relay unattended: authors the design spec,
  dispatches a Claude Fable reviewer that edits it, authors the implementation
  plan, dispatches a Fable reviewer that edits that, then either stops for review
  or continues straight into subagent-driven-development. Use ONLY when explicitly
  invoked as /autonom or when oiler names it — "autonom", "run the spec-plan
  pipeline", "unattended spec and plan", "spec to plan without stopping", "run the
  whole pipeline". Invoke after brainstorming's Q&A has concluded and the design is
  agreed. NOT for ordinary spec or plan requests — "write a spec", "write a plan",
  "review my spec" belong to superpowers:brainstorming and superpowers:writing-plans.
disable-model-invocation: true
allowed-tools: >-
  Bash(uv run *) Bash(git add *) Bash(git commit *) Bash(git diff *)
  Bash(git rev-parse *) Bash(git log *) Bash(git worktree *)
  Bash(git checkout -b *) Bash(git checkout autonom/*) Bash(cd *)
  Read Write Edit Agent Skill
metadata:
  author: oiler
  version: 0.1.0
---

# autonom

autonom runs superpowers steps 6 through 9 — author spec, review spec, author plan, review plan — as one unattended relay. You are the orchestrator. You hold the brainstorming context, so you author both artifacts yourself; you dispatch a Claude Fable subagent to review each one.

`scripts/autonom.py` owns every deterministic surface: artifact paths, the run ledger, artifact validation, and the two reviewer prompts. Prose is yours, structure is the script's. If you find yourself constructing an artifact path, inventing a ledger line, or composing a reviewer prompt, you have left the contract — ask the script instead.

Be exact about what that division buys, because overstating it is how it gets weakened. It is not a sandbox. The script owns prompt *generation*, but the prompt still passes through your context on its way to the subagent, and nothing inspects it afterwards; you could paste extra framing into a reviewer dispatch and no check would catch it. What the division does is turn every such move from a judgment call you get to make in the moment into an overt violation of a written contract — and, for the reviews, the separate commit leaves the result auditable afterwards. A bright line plus a record, not a lock. That is enough, and only because you are the one holding it.

Start only after `superpowers:brainstorming`'s Q&A has concluded and the design is agreed. autonom does not do discovery.

## What this does

| Step | Actor | Model | Artifact | Commit |
|---|---|---|---|---|
| 6 | main session | session model | `docs/superpowers/specs/<date>-<slug>-design.md` | `docs: <slug> design spec` |
| 7 | subagent | `fable` | edits the spec in place | `review(fable): spec — <slug>` |
| 8 | main session | session model | `docs/superpowers/plans/<date>-<slug>.md` | `docs: <slug> implementation plan` |
| 9 | subagent | `fable` | edits the plan in place | `review(fable): plan — <slug>` |

**The authoring model is whatever the session is running, and autonom never pins it.** Only the review model is pinned, to `fable`, because the escalation to a more capable reviewer is the entire point of the two review passes. A session on any tier authors on that tier.

Each review lands as its own commit. That separate commit is the mitigation for handing a reviewer write authority: `git diff <author-commit>..<review-commit>` is the complete record of what the review changed, and either pass can be reverted on its own.

## Why this supersedes two stock gates

autonom deliberately overrides two places where stock superpowers stops for a human:

- `superpowers:brainstorming` → the **User Review Gate**, which asks the human to review the spec before a plan is written.
- `superpowers:writing-plans` → the **Execution Handoff**, which asks which execution approach to use.

This is authorized, not a workaround. `superpowers:using-superpowers` states that user instructions take precedence over skills, and the `/autonom` invocation *is* that instruction — oiler pre-authorizes both gates by invoking this skill and answering the onboarding question. Nothing is being slipped past anyone.

Do not "correct" this back. A future reader who sees the gates skipped and restores them turns autonom into an ordinary two-pause workflow with extra machinery, which is the one outcome it exists to prevent. The gate that genuinely cannot be pre-authorized — a reviewer flagging a scope conflict — is preserved below and stops the run in both modes.

## Startup sequence

Run these in order, before authoring anything. The order matters: the run cannot be named until `init` has minted its slug, and the workspace is named from that slug.

**1. Establish the run repository.**

**The run operates on the repository your working directory is inside.** Nothing else selects it. `autonom.py` resolves the root with `git rev-parse --show-toplevel` from cwd, and every path in `init`'s JSON — spec, plan, run directory, ledger, escalations — is derived from that root. So `cd` to the target project first, print `git rev-parse --show-toplevel`, and confirm that repository with oiler as part of onboarding rather than assuming the session started in it. autonom is normally invoked to build something in a *project*, which is usually not the repository this session happens to be sitting in.

This is the same hazard the reviewer prompts guard against with `git -C` (step 7): a working directory is an invisible, inherited, per-process thing, and every place autonom depends on one is a place a run can silently land in the wrong repository. Resolve the root once, out loud, and keep every path derived from it.

**Confirm the run repository is writable by this session while a human is still present.** autonom writes to it from the main session and from two subagents, and the reviewers run for many minutes in a repository that is usually not the session's own. A permission stall *inside* a dispatch is invisible — no output, no prompt you can see, indistinguishable from a reviewer that is still thinking. Onboarding is the last moment anyone is watching, so raise it there rather than discovering it at minute nine of an unattended run.

**2. Look for an existing run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py status
```

This prints every run directory in that repository and its resume point as JSON. If one of them is incomplete and its topic matches what oiler just asked for, offer to resume it instead of starting fresh. Resume keys on the slug, so a topic phrased even slightly differently would mint a duplicate run and re-author artifacts that already exist — this check is the only thing preventing that.

**3. Ask the one onboarding question.**

> **checkpoint** (stop after the plan review) or **auto** (continue straight into `superpowers:subagent-driven-development`)?

Ask it once, immediately, alongside the repository confirmation from step 1, and ask nothing else. Every other decision in the pipeline is already made.

**4. Create or resume the run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py init "<topic>"
```

When resuming a run that `status` found, pass that run's `topic` string **verbatim** — copy it out of the `status` JSON rather than re-describing the work. `init` keys the run on the slug and rejects a different topic that slugifies the same, so a paraphrase either mints a duplicate run under a new slug or exits `2` on the collision. After a compaction the `status` output is the only place the original topic still exists.

Read the slug, both artifact paths, the run directory, the ledger path, the escalations path, and `next_step` from its JSON output. **Never construct an artifact path.** The script derives them from the date and slug so that every other superpowers skill can find them; a hand-built path is a silently orphaned artifact.

`init` runs before the workspace exists on purpose: the slug is the run's one canonical name, and it does not exist until `init` mints it. Running `init` first is safe because its only effects are the run directory — git-ignored, so it never appears in a diff — and possibly one `.gitignore` line.

`next_step` tells you where to start:

- `6` — a new or freshly initialized run. Begin at step 6.
- `7`, `8`, or `9` — a resume. Begin at that step. Never re-run a step the ledger records as complete.
- `null` — every step is already complete. Author nothing and re-run nothing; go straight to *Ending*. Falling through to step 6 here would overwrite a reviewed spec, which is the exact harm the ledger exists to prevent.

**5. Move to an isolated branch — in both modes.**

```bash
git checkout -b autonom/<slug>      # new run
git checkout autonom/<slug>         # resume: the branch already exists
```

A resume must switch, not create — `checkout -b` fails on an existing branch. Use the slug from `init`, so two runs can never collide on a branch name and a human reading `git branch` can see at a glance what each one is for. This is not optional in auto mode and not optional in checkpoint mode either. Two reasons: the spec, plan, and both review commits stay off `master`, and `subagent-driven-development`'s hard gate — never implement on a main branch without explicit consent — is satisfied by construction, so nothing interrupts a full-auto run halfway through.

Create the branch **in the run repository**, with `git checkout -b` or `git worktree add`, and not through `superpowers:using-git-worktrees`. That skill prefers the native `EnterWorktree` tool, which operates on the *session's* repository and branches from `origin/<default-branch>` — the wrong repository, and a ref the run repository may not even have. When the run repository is not the session's own, which is the normal case, the native tool does not apply.

A branch is the default because it leaves the git toplevel unchanged, so every path `init` just emitted stays valid. A worktree is a *different* toplevel: if you use one, `cd` into it and re-run `init "<topic>"` verbatim from there, and use that JSON instead — the first `init`'s paths point at the wrong tree.

If `init` added the `.gitignore` line, it is part of the run. Include it in the first authoring commit (`git add .gitignore` alongside the spec) so the reviewer inherits a clean tree rather than a stray modification it did not make and cannot explain.

**6. On a resume only — reconcile the ledger against the branch.**

Both checks below need the run branch checked out, which is why they come after step 5 and not with `init`: `git log … HEAD` resolves HEAD on whatever branch you are actually on, and run from `master` it would miss the run's commits entirely and conclude the opposite of the truth. Ask the script for the run's state rather than reading `progress.md` — the ledger's format is the script's, not yours:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py status <slug>
```

**If `last_status` is `dispatched`, check whether that review already happened before dispatching another.** A compaction between the reviewer's commit and its `complete` line leaves the ledger looking exactly like a dispatch that never returned. `dispatched_base` is that dispatch's base SHA, so the question is answerable:

```bash
git log --oneline <dispatched_base>..HEAD
```

A `review(fable):` commit in that range means the review is done. Finish the step the way the step itself would have: validate the artifact, record `complete` with that SHA or range, **then run the escalation gate for that step** — `escalations <slug>`, and on exit `1` record `escalated` and stop. Do not skip the gate. A reviewer that escalated and committed, followed by a compaction, is exactly the case this branch handles, and a resume that records `complete` and walks on spends a second Fable dispatch before the scope conflict ever surfaces. Dispatching again is the other failure: a second review of an already-reviewed artifact, which is the duplicate the ledger exists to prevent.

**Then run the escalation gate regardless of where you are resuming**, before authoring anything. `escalated` is recorded *alongside* `complete`, so a step-7 escalation still leaves `next_step: 8` — a resume that trusts `next_step` alone walks straight past an unresolved scope conflict and authors a plan against it.

## What the validators require

Author to this contract the first time. *Error handling* below allows exactly one repair attempt, and it is meant for a real defect — not for discovering the schema by trial.

**Both artifacts** — no `TBD`, `TODO`, `FIXME`, or `XXX`; no `<placeholder>` or `[fill in]`.

**Spec** — one level-1 title, plus level-2-or-deeper headings whose text contains `problem` or `goal`, `architecture` or `design`, `error`, and `test`. Every matched section needs a body. No `**Open question`, `???`, or `[?]`: an unresolved question is an escalation, not a spec line.

**Plan** — a line carrying both `REQUIRED SUB-SKILL` and `superpowers:subagent-driven-development`; a heading that is exactly `## Global Constraints`; at least one `### Task N:` block; and inside every task block a `**Files:**` line and at least one `- [ ] **Step` checkbox. The validator also rejects the vague directives `Similar to Task N`, `add appropriate error handling`, `add validation`, `handle edge cases`, and a bare `Write tests for the above` line.

**Every structural marker must be live prose, never inside a fence or backticks.** The validator blanks fenced blocks and inline code spans before it scans, so that a document may *document* a forbidden marker without *containing* one. The cost is that a required marker written inside a fence is invisible too. This bites hardest on the plan: `superpowers:writing-plans` presents its mandatory header *inside* a ```` ```markdown ```` fence, so copying that template verbatim fails with "missing the mandatory REQUIRED SUB-SKILL header line" against a plan that visibly contains it. Lift the header, `## Global Constraints`, and the task blocks out of the fence.

## The four steps

### Step 6 — author the spec

Write the spec at the `spec` path from `init`, from the design agreed during Q&A, in the shape *What the validators require* prescribes above — that section is the authority on what a passing spec contains.

**Do not invoke `superpowers:brainstorming` here.** Invoking it starts its discovery Q&A and its hard gate, and that gate is the thing autonom has already satisfied: the Q&A concluded before `/autonom` was called. If you want its conventions, read its SKILL.md; do not invoke it. Then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate spec "<spec path>"
git add "<spec path>" .gitignore && git commit -m "docs: <slug> design spec"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 6 complete --slug <slug> --commit <sha>
```

Validate before committing. See *Error handling* for a non-zero exit.

### Step 7 — review the spec on Fable

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py prompt spec <slug>
```

Before dispatching, record the current HEAD in the ledger:

```bash
git rev-parse HEAD
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 7 dispatched --slug <slug> --commit <base sha>
```

Two commands, not one with `$(...)`: command substitution defeats the prefix matching that `allowed-tools` uses, and a permission prompt in the middle of an unattended run is the failure this skill exists to avoid.

That before/after pair is how you identify the review commit below, and the ledger is where it has to live: a Fable dispatch runs for many minutes, and if the session compacts mid-dispatch a base SHA held only in context is gone and the review diff range is unrecoverable. `dispatched` does not advance the run — only `complete` does.

Dispatch one subagent with `subagent_type: "general-purpose"` and `model: "fable"`. The type matters: the prompt requires Read, Edit, and `git add`/`git commit`, and a read-only agent type would do the review and then fail silently at the commit, losing the whole pass. **Its entire prompt is that stdout, passed byte-for-byte.** Add nothing: no summary of the spec, no authoring rationale, no brainstorming Q&A, no list of areas you are worried about, no "focus especially on…".

The reason is the whole reason step 7 exists. You wrote the spec, so you cannot see what you failed to consider — that blind spot is exactly what a fresh reader finds. Every sentence of context you add narrows where the reviewer looks and pre-loads your framing, and a primed reviewer returns an echo of the author rather than a critique of the artifact. The prompt already tells the reviewer to read the repository cold and where its write authority begins and ends. Adding to it can only subtract.

A subagent inherits the *session's* working directory, not the run's repository, and the prompt is built for that in two different ways. Every path in it is absolute, which is what makes Read and Edit land in the run repository. But **git subcommands are cwd-bound no matter how absolute their arguments are**, so the prompt's commit block is anchored separately, with `git -C <root>`. Both halves are load-bearing and neither substitutes for the other: absolute paths alone produce a reviewer whose edits land correctly, whose `git add` fails, and whose `git commit` then succeeds *in the wrong repository* — leaving the run's HEAD unmoved, so you read a review that really happened as "no changes". Never make those paths relative and never drop a `-C`.

The reviewer edits the spec in place and commits it itself, inside its own context — the commit SHA never reaches you in its report, which the prompt deliberately keeps brief. So when it returns, run `git rev-parse HEAD` again. A changed HEAD means the reviewer committed; count what it committed before you record anything:

```bash
git log --oneline <base sha>..HEAD
```

**One commit** is the normal case: that SHA is the `--commit` value and the second endpoint of the review diff range. **More than one** is not an error — a reviewer that splits its edits is behaving reasonably — but the record has to match it. The range `<base sha>..HEAD` still contains everything, so pass the range as `--commit` instead of a single SHA, and say at the checkpoint that the reviewer made N commits. The separate review commit is the entire mitigation for granting a reviewer write authority; a ledger claiming one commit when there were three understates what the reviewer did and quietly weakens the thing that made the write grant safe.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate spec "<spec path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 7 complete --slug <slug> --commit <review sha or range>
```

An unchanged HEAD is *usually* a clean review — the prompt tells the reviewer to make no commit if it made no edits — but never record that on the strength of an unmoved HEAD alone. Confirm the artifact is genuinely untouched first:

```bash
git diff --stat <base sha> -- "<spec path>"
git diff -- "<spec path>"
```

Both run from the run repository, like every other command you issue — startup step 1 established that cwd, and your own commands rely on it throughout. Only the *reviewer's* commands carry `git -C`, because a subagent's working directory is not yours to set.

Both empty means a real clean review: record `ledger 7 complete --slug <slug>` with no `--commit`, and print "no changes" where the spec's diff range would go at the checkpoint. **If either shows changes while HEAD did not move, the review happened and the commit did not land here** — the failure the reviewer's `-C` anchoring exists to prevent, plus a probable stray `review(fable):` commit in another repository. Stop and report it; do not record a clean review over a review that was actually performed, and do not commit the reviewer's edits yourself under your own authorship.

The second validation is not redundant. A reviewer with write authority can break the artifact contract exactly as an author can — strand an edit mid-sentence, delete a required section.

Then run the escalation gate:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py escalations <slug>
```

Exit `0` means continue — absent, empty, and whitespace-only all count as nothing escalated, and absent is the ordinary case because neither the script nor a clean review creates the file. Exit `1` means the reviewer escalated, and the command has already printed the contents for you; see *Error handling*. Do not read or test for the file yourself: what counts as "non-empty" belongs to the script, for the same reason the validators do.

**Emptying `escalations.md` is the human act that marks an escalation resolved, and it is oiler's alone.** Nothing in autonom clears it — no subcommand, no reviewer, and never you. That asymmetry is the whole design: a reviewer and the orchestrator can both raise the gate, only a human can lower it, and a gate the orchestrator can clear is not a gate. So when a resumed run re-fires this check on contents oiler has already dealt with, the answer is not to clear the file and continue; it is to report that the escalation is still outstanding and stop. Say so plainly at the checkpoint, because emptying the file is a step oiler has to know to take.

### Step 8 — author the plan

Write the plan at the `plan` path from `init`, following `superpowers:writing-plans`, against the reviewed spec. Then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate plan "<plan path>"
git add "<plan path>" && git commit -m "docs: <slug> implementation plan"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 8 complete --slug <slug> --commit <sha>
```

### Step 9 — review the plan on Fable

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py prompt plan <slug>
```

Same dispatch discipline as step 7, without exception: `subagent_type: "general-purpose"`, `model: "fable"`, the stdout as the entire prompt, byte-for-byte, nothing added. The plan reviewer's prompt already carries the spec path — it judges the plan against the spec, not against your intent for it.

Record the base SHA the same way — `git rev-parse HEAD`, then `ledger 9 dispatched --slug <slug> --commit <base sha>` — and read the review commit exactly as in step 7. When it returns:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate plan "<plan path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 9 complete --slug <slug> --commit <review sha or range>
```

Unchanged HEAD is handled the same way, including the two `git diff` checks against the plan path before you accept it as a clean review.

Then run the escalation gate again — same command, same meaning:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py escalations <slug>
```

## Reading the script's exit codes

| Exit | Meaning | What you do |
|---|---|---|
| `0` | Success; all checks passed | Continue |
| `1` | Validation failures, one finding per line with its line number | A real defect in the artifact — repair per the table below |
| `2` | Usage or IO error (bad arguments, no such run, not in a git repo, missing dependency) | Stop and report. No repair can fix a malformed invocation, and retrying a `2` in a loop just burns the run |

Never treat `2` as a validation failure. `1` means the artifact is wrong; `2` means the command was wrong.

## Ledger statuses

`complete` is the only status that advances the run. `autonom.py` computes `next_step` by counting `step N complete` lines and nothing else, so the other three statuses are annotations on top of it, not alternatives to it.

- **`dispatched`** — written with `--commit <base sha>` immediately before a Fable dispatch, so the review diff's first endpoint survives a compaction that happens mid-dispatch. It records that a step started, which is deliberately not the same as finishing it.
- **`complete`** — record it whenever a step's work actually finished, every time, without exception. It is the only thing stopping a post-compaction resume from re-dispatching a reviewer over an already-reviewed artifact and minting a duplicate review commit.
- **`escalated`** — an *additional* line, written immediately after that step's `complete` line, never instead of it. A review that finished and escalated is still a finished review; recording only `escalated` pins `next_step` at that step forever and the resume re-runs it.
- **`failed`** — written on its own, *without* a `complete` line, because the step's work did not finish. Not advancing is the point here: the artifact is unreviewed and the step has to run again.

## Error handling

| Condition | Behavior |
|---|---|
| Validator fails on a freshly authored artifact (step 6 or 8) | One repair attempt by the same author, targeted at the reported findings. If it fails again, stop and report both findings sets. No loop. |
| Validator fails after a review pass (step 7 or 9) | Stop. Report the findings and the review diff. No repair attempt — the reviewer subagent is gone, and a main-session rewrite of a Fable edit would silently undo the escalation it was making. |
| Fable subagent dies, errors, or returns nothing | Stop. `ledger <step> failed` and **no** `complete` line — the step did not finish, so the run must not advance past an unreviewed artifact. |
| `escalations` exits `1` after either review | Stop before `superpowers:subagent-driven-development`, **in both modes**. Record `ledger <step> complete` first — the review itself finished — then `ledger <step> escalated` as the additional marker, per *Ledger statuses*. Print the contents the gate emitted, hand the decision to oiler, and say that resolving it means emptying `escalations.md` — the run cannot proceed until the file is empty, and only oiler may empty it. Full-auto authorizes skipping a routine checkpoint; it does not authorize ignoring a flagged scope conflict, which is the one decision in this pipeline that was never a human's to delegate. |
| Session compacts mid-run | Re-invoke `/autonom` from the run repository. `autonom.py status` prints the resume point from the ledger, the `dispatched` line carries the pre-dispatch base SHA so the review diff range is still reconstructible, and committed artifacts are recoverable from git regardless of context. Never re-run a step the ledger records complete. |

## Ending

**checkpoint mode** — stop and print, in one message: both artifact paths, both review diff ranges (`git diff <author-sha>..<review-sha>` for the spec and for the plan, or "no changes" for a review that committed nothing), and the instruction to resume into implementation by invoking `superpowers:subagent-driven-development` with the plan path. The diffs are the point of the checkpoint — they are what oiler reads to decide whether the reviews were right.

**auto mode** — invoke `superpowers:subagent-driven-development` with the plan path, then exit. SDD owns the task loop, its own ledger, per-task review, and the handoff to `finishing-a-development-branch`. Do not duplicate any of it and do not override its model selection.

**An outstanding escalation overrides both, in either mode.** Print the artifact paths, the review diff ranges, and the escalation contents, state that the run is blocked on it and that clearing it means emptying `escalations.md`, then stop. Do **not** print a resume-into-implementation instruction and do not invoke `subagent-driven-development` — implementation is precisely what the escalation is blocking, and an ending that offers a resume line alongside an unresolved scope conflict invites someone to take it.

## Narration

Emit one short line at each step transition — what just finished, what is starting. Fable turns run for many minutes with no output, so the ledger and those lines are the only signal that an unattended run is alive rather than hung. One line, not a status report; a running commentary defeats the purpose of an unattended pipeline.
