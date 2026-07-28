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
  Bash(git rev-parse *) Bash(git log *) Bash(git worktree *) Read Write Edit
  Agent Skill
---

# autonom

autonom runs superpowers steps 6 through 9 — author spec, review spec, author plan, review plan — as one unattended relay. You are the orchestrator. You hold the brainstorming context, so you author both artifacts yourself; you dispatch a Claude Fable subagent to review each one.

`scripts/autonom.py` owns every deterministic surface: artifact paths, the run ledger, artifact validation, and the two reviewer prompts. Prose is yours, structure is the script's. If you find yourself constructing an artifact path, inventing a ledger line, or composing a reviewer prompt, you have left the contract — ask the script instead. That division is what makes the run survivable: it cannot skip a step, misname an artifact, lose its place after a compaction, or advance past a half-finished document.

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

Run these in order, before authoring anything.

**1. Look for an existing run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py status
```

This prints every run directory and its resume point as JSON. If one of them is incomplete and its topic matches what oiler just asked for, offer to resume it instead of starting fresh. Resume keys on the slug, so a topic phrased even slightly differently would mint a duplicate run and re-author artifacts that already exist — this check is the only thing preventing that.

**2. Ask the one onboarding question.**

> **checkpoint** (stop after the plan review) or **auto** (continue straight into `superpowers:subagent-driven-development`)?

Ask it once, immediately, and do not ask anything else. Every other decision in the pipeline is already made.

**3. Ensure an isolated workspace — in both modes.**

Invoke `superpowers:using-git-worktrees`. This is not optional in auto mode and not optional in checkpoint mode either. Two reasons: the spec, plan, and both review commits stay off `master`, and `subagent-driven-development`'s hard gate — never implement on a main branch without explicit consent — is satisfied by construction, so nothing interrupts a full-auto run halfway through.

**4. Create or resume the run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py init "<topic>"
```

When resuming a run that `status` found, pass that run's `topic` string **verbatim** — copy it out of the `status` JSON rather than re-describing the work. `init` keys the run on the slug and rejects a different topic that slugifies the same, so a paraphrase either mints a duplicate run under a new slug or exits `2` on the collision. After a compaction the `status` output is the only place the original topic still exists.

Read the slug, both artifact paths, the run directory, the ledger path, the escalations path, and `next_step` from its JSON output. **Never construct an artifact path.** The script derives them from the date and slug so that every other superpowers skill can find them; a hand-built path is a silently orphaned artifact.

`next_step` tells you where to start:

- `6` — a new or freshly initialized run. Begin at step 6.
- `7`, `8`, or `9` — a resume. Begin at that step. Never re-run a step the ledger records as complete.
- `null` — every step is already complete. Author nothing and re-run nothing; go straight to *Ending*. Falling through to step 6 here would overwrite a reviewed spec, which is the exact harm the ledger exists to prevent.

## What the validators require

Author to this contract the first time. *Error handling* below allows exactly one repair attempt, and it is meant for a real defect — not for discovering the schema by trial.

**Both artifacts** — no `TBD`, `TODO`, `FIXME`, or `XXX`; no `<placeholder>` or `[fill in]`.

**Spec** — one level-1 title, plus level-2-or-deeper headings whose text contains `problem` or `goal`, `architecture` or `design`, `error`, and `test`. Every matched section needs a body. No `**Open question`, `???`, or `[?]`: an unresolved question is an escalation, not a spec line.

**Plan** — a line carrying both `REQUIRED SUB-SKILL` and `superpowers:subagent-driven-development`; a heading that is exactly `## Global Constraints`; at least one `### Task N:` block; and inside every task block a `**Files:**` line and at least one `- [ ] **Step` checkbox. The validator also rejects the vague directives `Similar to Task N`, `add appropriate error handling`, `add validation`, `handle edge cases`, and a bare `Write tests for the above` line.

**Every structural marker must be live prose, never inside a fence or backticks.** The validator blanks fenced blocks and inline code spans before it scans, so that a document may *document* a forbidden marker without *containing* one. The cost is that a required marker written inside a fence is invisible too. This bites hardest on the plan: `superpowers:writing-plans` presents its mandatory header *inside* a ```` ```markdown ```` fence, so copying that template verbatim fails with "missing the mandatory REQUIRED SUB-SKILL header line" against a plan that visibly contains it. Lift the header, `## Global Constraints`, and the task blocks out of the fence.

## The four steps

### Step 6 — author the spec

Write the spec at the `spec` path from `init`, following `superpowers:brainstorming`'s spec conventions and the design agreed during Q&A. Then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate spec "<spec path>"
git add "<spec path>" && git commit -m "docs: <slug> design spec"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 6 complete --slug <slug> --commit <sha>
```

Validate before committing. See *Error handling* for a non-zero exit.

### Step 7 — review the spec on Fable

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py prompt spec <slug>
```

Record `git rev-parse HEAD` before dispatching — the before/after pair is how you identify the review commit below.

Dispatch one subagent with `subagent_type: "general-purpose"` and `model: "fable"`. The type matters: the prompt requires Read, Edit, and `git add`/`git commit`, and a read-only agent type would do the review and then fail silently at the commit, losing the whole pass. **Its entire prompt is that stdout, passed byte-for-byte.** Add nothing: no summary of the spec, no authoring rationale, no brainstorming Q&A, no list of areas you are worried about, no "focus especially on…".

The reason is the whole reason step 7 exists. You wrote the spec, so you cannot see what you failed to consider — that blind spot is exactly what a fresh reader finds. Every sentence of context you add narrows where the reviewer looks and pre-loads your framing, and a primed reviewer returns an echo of the author rather than a critique of the artifact. The prompt already tells the reviewer to read the repository cold and where its write authority begins and ends. Adding to it can only subtract.

Every path in that prompt is absolute, because `compute_paths` builds it from the run's repository root. That is what makes the dispatch safe: a subagent inherits the *session's* working directory, not the run's repository, so relative paths would send the reviewer's edits and its commit into whatever repo the session happens to be sitting in, and you would read the unchanged HEAD as a clean review. Never "tidy" those paths into relative form.

The reviewer edits the spec in place and commits it itself, inside its own context — the commit SHA never reaches you in its report, which the prompt deliberately keeps brief. So when it returns, run `git rev-parse HEAD` again. A changed HEAD is the review commit; that SHA is the `--commit` value and the second endpoint of the review diff range.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate spec "<spec path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 7 complete --slug <slug> --commit <review sha>
```

An unchanged HEAD is not a failure. The prompt tells the reviewer to make no commit if it made no edits, so unchanged means a clean review: record `ledger 7 complete --slug <slug>` with no `--commit`, and print "no changes" where the spec's diff range would go at the checkpoint.

The second validation is not redundant. A reviewer with write authority can break the artifact contract exactly as an author can — strand an edit mid-sentence, delete a required section.

Then run the escalation gate:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py escalations <slug>
```

Exit `0` means continue — absent, empty, and whitespace-only all count as nothing escalated, and absent is the ordinary case because neither the script nor a clean review creates the file. Exit `1` means the reviewer escalated, and the command has already printed the contents for you; see *Error handling*. Do not read or test for the file yourself: what counts as "non-empty" belongs to the script, for the same reason the validators do.

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

Bracket the dispatch with `git rev-parse HEAD` exactly as in step 7, and read the review commit the same way. When it returns:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate plan "<plan path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 9 complete --slug <slug> --commit <review sha>
```

Unchanged HEAD is handled the same way: no `--commit`, "no changes" in place of the plan's diff range.

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

`complete` is the only status that advances the run. `autonom.py` computes `next_step` by counting `step N complete` lines and nothing else, so the other two statuses are annotations on top of it, not alternatives to it.

- **`complete`** — record it whenever a step's work actually finished, every time, without exception. It is the only thing stopping a post-compaction resume from re-dispatching a reviewer over an already-reviewed artifact and minting a duplicate review commit.
- **`escalated`** — an *additional* line, written immediately after that step's `complete` line, never instead of it. A review that finished and escalated is still a finished review; recording only `escalated` pins `next_step` at that step forever and the resume re-runs it.
- **`failed`** — written on its own, *without* a `complete` line, because the step's work did not finish. Not advancing is the point here: the artifact is unreviewed and the step has to run again.

## Error handling

| Condition | Behavior |
|---|---|
| Validator fails on a freshly authored artifact (step 6 or 8) | One repair attempt by the same author, targeted at the reported findings. If it fails again, stop and report both findings sets. No loop. |
| Validator fails after a review pass (step 7 or 9) | Stop. Report the findings and the review diff. No repair attempt — the reviewer subagent is gone, and a main-session rewrite of a Fable edit would silently undo the escalation it was making. |
| Fable subagent dies, errors, or returns nothing | Stop. `ledger <step> failed` and **no** `complete` line — the step did not finish, so the run must not advance past an unreviewed artifact. |
| `escalations` exits `1` after either review | Stop before `superpowers:subagent-driven-development`, **in both modes**. Record `ledger <step> complete` first — the review itself finished — then `ledger <step> escalated` as the additional marker, per *Ledger statuses*. Print the contents the gate emitted and hand the decision to oiler. Full-auto authorizes skipping a routine checkpoint; it does not authorize ignoring a flagged scope conflict, which is the one decision in this pipeline that was never a human's to delegate. |
| Session compacts mid-run | Re-invoke `/autonom`. `autonom.py status` prints the resume point from the ledger, and committed artifacts are recoverable from git regardless of context. Never re-run a step the ledger records complete. |

## Ending

**checkpoint mode** — stop and print, in one message: both artifact paths, both review diff ranges (`git diff <author-sha>..<review-sha>` for the spec and for the plan, or "no changes" for a review that committed nothing), and the instruction to resume into implementation by invoking `superpowers:subagent-driven-development` with the plan path. The diffs are the point of the checkpoint — they are what oiler reads to decide whether the reviews were right.

**auto mode** — invoke `superpowers:subagent-driven-development` with the plan path, then exit. SDD owns the task loop, its own ledger, per-task review, and the handoff to `finishing-a-development-branch`. Do not duplicate any of it and do not override its model selection.

## Narration

Emit one short line at each step transition — what just finished, what is starting. Fable turns run for many minutes with no output, so the ledger and those lines are the only signal that an unattended run is alive rather than hung. One line, not a status report; a running commentary defeats the purpose of an unattended pipeline.
