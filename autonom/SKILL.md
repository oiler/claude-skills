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
  Bash(git rev-parse *) Bash(git log *) Read Write Edit Agent Skill
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

Read the slug, both artifact paths, the run directory, the ledger path, the escalations path, and `next_step` from its JSON output. **Never construct an artifact path.** The script derives them from the date and slug so that every other superpowers skill can find them; a hand-built path is a silently orphaned artifact.

If `next_step` comes back higher than 6, this is a resume. Start at that step. Never re-run a step the ledger records as complete.

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

Dispatch one subagent with `model: "fable"`. **Its entire prompt is that stdout, passed byte-for-byte.** Add nothing: no summary of the spec, no authoring rationale, no brainstorming Q&A, no list of areas you are worried about, no "focus especially on…".

The reason is the whole reason step 7 exists. You wrote the spec, so you cannot see what you failed to consider — that blind spot is exactly what a fresh reader finds. Every sentence of context you add narrows where the reviewer looks and pre-loads your framing, and a primed reviewer returns an echo of the author rather than a critique of the artifact. The prompt already tells the reviewer to read the repository cold and where its write authority begins and ends. Adding to it can only subtract.

The reviewer edits the spec in place and commits it itself. When it returns:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate spec "<spec path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 7 complete --slug <slug> --commit <sha>
```

The second validation is not redundant. A reviewer with write authority can break the artifact contract exactly as an author can — strand an edit mid-sentence, delete a required section.

Then check `escalations.md` in the run directory. See *Error handling*.

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

Same dispatch discipline as step 7, without exception: `model: "fable"`, the stdout as the entire prompt, byte-for-byte, nothing added. The plan reviewer's prompt already carries the spec path — it judges the plan against the spec, not against your intent for it.

When it returns:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py validate plan "<plan path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/autonom.py ledger 9 complete --slug <slug> --commit <sha>
```

Then check `escalations.md` again.

## Reading the script's exit codes

| Exit | Meaning | What you do |
|---|---|---|
| `0` | Success; all checks passed | Continue |
| `1` | Validation failures, one finding per line with its line number | A real defect in the artifact — repair per the table below |
| `2` | Usage or IO error (bad arguments, no such run, not in a git repo, missing dependency) | Stop and report. No repair can fix a malformed invocation, and retrying a `2` in a loop just burns the run |

Never treat `2` as a validation failure. `1` means the artifact is wrong; `2` means the command was wrong.

## Error handling

| Condition | Behavior |
|---|---|
| Validator fails on a freshly authored artifact (step 6 or 8) | One repair attempt by the same author, targeted at the reported findings. If it fails again, stop and report both findings sets. No loop. |
| Validator fails after a review pass (step 7 or 9) | Stop. Report the findings and the review diff. No repair attempt — the reviewer subagent is gone, and a main-session rewrite of a Fable edit would silently undo the escalation it was making. |
| Fable subagent dies, errors, or returns nothing | Stop. `ledger <step> failed`. Never advance with an unreviewed artifact. |
| `escalations.md` is non-empty after either review | Stop before `superpowers:subagent-driven-development`, **in both modes**. `ledger <step> escalated`, then print the escalation contents and hand the decision to oiler. Full-auto authorizes skipping a routine checkpoint; it does not authorize ignoring a flagged scope conflict, which is the one decision in this pipeline that was never a human's to delegate. |
| Session compacts mid-run | Re-invoke `/autonom`. `autonom.py status` prints the resume point from the ledger, and committed artifacts are recoverable from git regardless of context. Never re-run a step the ledger records complete. |

## Ending

**checkpoint mode** — stop and print, in one message: both artifact paths, both review diff ranges (`git diff <author-sha>..<review-sha>` for the spec and for the plan), and the instruction to resume into implementation by invoking `superpowers:subagent-driven-development` with the plan path. The diffs are the point of the checkpoint — they are what oiler reads to decide whether the reviews were right.

**auto mode** — invoke `superpowers:subagent-driven-development` with the plan path, then exit. SDD owns the task loop, its own ledger, per-task review, and the handoff to `finishing-a-development-branch`. Do not duplicate any of it and do not override its model selection.

## Narration

Emit one short line at each step transition — what just finished, what is starting. Fable turns run for many minutes with no output, so the ledger and those lines are the only signal that an unattended run is alive rather than hung. One line, not a status report; a running commentary defeats the purpose of an unattended pipeline.
