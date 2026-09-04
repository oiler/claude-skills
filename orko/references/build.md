# Build engagement

A build engagement runs from intake to close in one conductor session. You hold the goal and the boundaries, you author the spec, and you decide what happens to every finding that comes back. Seats report and never write. `orko.py` owns the paths, the ledger, the dispatch prompts, and the Linear payloads. Linear holds the record: every decision you make lands there as an issue, so a week later the run is readable without a checkout.

Every script call in this file is written as `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py <subcommand>`. If that substitution resolves to an empty string inside a Bash call, use `~/.claude/skills/orko/scripts/orko.py` instead, which is the machine-wide symlink to the same file. Never use shell command substitution anywhere in a run: the prefix matching behind `allowed-tools` cannot see through it, so a substituted command produces a permission prompt, and a permission prompt in the middle of a long dispatch is invisible. Where autonom wrote one command with a substituted SHA, write two — read the value, then pass it.

## Startup sequence

Run these in order, before authoring anything. The order matters: the run cannot be named until `init` has minted its slug, and the branch is named from that slug.

**1. Establish the run repository.**

The run operates on the repository your working directory is inside. Nothing else selects it. `orko.py` resolves the root with `git rev-parse --show-toplevel` from cwd, and every path it emits — run directory, spec, plan, ledger, escalations, findings — is derived from that root. So `cd` to the target project first, print `git rev-parse --show-toplevel`, and confirm that repository with oiler as part of intake rather than assuming the session started in it. orko is normally invoked to build something in a project, which is usually not the repository this session happens to be sitting in.

Confirm the run repository is writable by this session while a human is still present. A build writes to it from the main session and from every implementer `superpowers:subagent-driven-development` dispatches, and those run for many minutes. A permission stall inside a dispatch is invisible — no output, no prompt you can see, indistinguishable from a seat that is still thinking. Intake is the last moment anyone is watching, so raise it there rather than discovering it at minute nine.

**2. Look for an existing run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py status
```

This prints every run in that repository as JSON: mode, topic, resume point, last status, and the recorded Linear IDs. If one is incomplete and its topic matches what oiler just asked for, offer to resume it instead of starting fresh. Resume keys on the slug, so a topic phrased even slightly differently mints a duplicate run with a duplicate Linear Project. When you resume, copy the `topic` string out of the `status` JSON verbatim and pass that to `init`; after a compaction that JSON is the only place the original topic still exists.

**3. Ask the one intake round.**

Ask, in a single message and nothing else:

- Confirmation of the target repository you printed in step 1.
- The boundaries: what this run may and may not touch.
- **checkpoint** (stop after the plan review) or **auto** (continue straight into `superpowers:subagent-driven-development`)?

Every other decision in a build is yours to make afterwards, inside those boundaries. Ask nothing else.

**4. Create or resume the run.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py init build "<goal>" --team <KEY>
```

`--team` is the Linear team key: uppercase letters and digits, for example `JRF`. The mode is positional and fixed at `init`; a run created as `build` cannot later be resumed as `analysis`.

The topic string becomes both the slug and the Linear Project name, so write the goal as one sentence, with no trailing punctuation and no file paths in it. A topic carrying a path slugifies into something unreadable in the Project list and tells a human nothing a week later.

Read the slug, `run_dir`, `spec`, `plan`, `ledger`, `escalations`, `findings_dir`, `context_dir`, `unposted_dir`, and `next_step` out of the JSON. Never construct a path. The script derives all of them from the root and the slug; a hand-built path is a silently orphaned artifact that no other command will find.

`next_step` tells you where to start: `0` on a new run, a higher number on a resume, and `null` when every step is already complete. On `null`, author nothing and re-run nothing — go straight to *Ending*.

**5. Branch, then preflight.**

```bash
git checkout -b orko/<slug>      # new run
git checkout orko/<slug>         # resume: the branch already exists
```

A resume switches, it does not create; `checkout -b` fails on an existing branch. The slug guarantees two runs cannot collide on a branch name, and it lets a human reading `git branch` see what each one is for. Then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py preflight --slug <slug>
```

`preflight` checks in code what prose used to ask you to check: `uv-missing`, `on-default-branch`, `run-dir-not-ignored`, `project-id-missing`, and `blocked-escalation`. Exit `1` prints one finding per line and stops intake — fix the named condition and run it again. Exit `2` means you are not inside a git repository or named a run that does not exist. Run `preflight` after the branch switch, not before: `on-default-branch` is the finding it exists for, and on `master` it would fire on every run.

**On a resume, reconcile before you author.**

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py status <slug>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py escalations <slug>
```

A `last_status` of `dispatched` means a round started and the ledger never recorded it finishing. That is what a compaction mid-dispatch looks like, and it is not proof the seats never delivered: list `findings_dir` first and read what is there. Re-dispatching a seat whose findings file already exists spends a second dispatch and produces a second copy of the same review. Run `escalations <slug>` before authoring anything regardless of where you are resuming — `escalated` is recorded alongside `complete`, so `next_step` still points forward past an unresolved scope conflict, and a resume that trusts `next_step` alone walks straight into building against it.

## Why two stock gates are skipped

orko build deliberately overrides two places where stock superpowers stops for a human:

- `superpowers:brainstorming` → the **User Review Gate**, which asks the human to review the spec before a plan is written.
- `superpowers:writing-plans` → the **Execution Handoff**, which asks which execution approach to use.

This is authorized, not a workaround. `superpowers:using-superpowers` states that user instructions take precedence over skills, and the `/orko build` invocation and the intake answers *are* that instruction — oiler pre-authorizes both gates by invoking this skill and answering the intake round. Nothing is being slipped past anyone.

Do not "correct" this back. A future reader who sees the gates skipped and restores them turns orko build into an ordinary two-pause workflow with extra machinery, which is the one outcome it exists to prevent. The gate that genuinely cannot be pre-authorized — a reviewer flagging a scope conflict — is preserved below and stops the run in both modes.

## The steps

Each step ends with its ledger line. `complete` is the only status that advances the run, so record it every time a step's work actually finished.

### 0 Intake

Startup has already run `init`, created the branch, and cleared `preflight`. Create the Linear Project:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post project --slug <slug> --goal "<goal>" --boundaries "<boundaries>" --branch orko/<slug>
```

The output is `{"posts": [...]}`. Call the tool named in each entry with exactly the object in its `args`, then run the entry's `then` command with `<returned id>` replaced by the id the tool gave back — for a first `post project` that is `linear set project <returned id> --slug <slug>`, which is what makes every later `post` work. The full protocol, including what to do when a call fails, is in `references/linear.md`.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 0 complete --slug <slug>
```

### 1 Spec

Author the spec at the `spec` path from `init`, from the goal and the intake answers, in the shape *What the validators require* prescribes below. That section is the authority on what a passing spec contains; author to it the first time rather than discovering it through repair attempts.

Do not invoke `superpowers:brainstorming` here. Invoking it starts its discovery Q&A and its own gate, and the intake round has already settled what that Q&A would ask. If you want its conventions, read its SKILL.md.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py validate spec "<spec path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post document spec --slug <slug>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 1 complete --slug <slug>
```

Exit `1` from `validate` is a real defect: one repair attempt against the reported findings, then stop if it fails again. `post document spec` emits `save_document` with a `then` of `linear set spec_doc <returned id> --slug <slug>`; run it, or every later update creates a second document instead of revising the first.

### 2 Spec review

Pick the lenses. The default is all four in `references/spec-reviewer.md`: `requirements`, `architecture`, `testability`, `security`. Drop one only when it has nothing to examine, and say which you dropped and why in the step summary you post at close.

Record the dispatch before it goes out, then emit one prompt per lens:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 2 dispatched --slug <slug>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt spec-review <slug> --lens <lens>
```

`dispatched` does not advance the run; it is what tells a resumed session that a round started, so it can check `findings_dir` instead of blindly dispatching again.

Dispatch one `general-purpose` subagent per lens at `opus`, with that stdout as the entire prompt, byte for byte. Add nothing: no summary of the spec, no authoring rationale, no list of areas you are worried about. You wrote the spec, so you cannot see what you failed to consider, and that blind spot is exactly what a fresh reader finds. Every sentence of context you add narrows where the reviewer looks and returns you an echo of your own framing. Send all the dispatches in one message so the seats run in parallel.

Review seats run at `opus` rather than orko's default-down tier because the spec review is the judgment-heavy step of a build. You may raise a single seat to `fable` when the spec carries a design decision you cannot evaluate yourself; say why in the step summary.

When they return, check delivery: each seat's findings file must exist at `<findings_dir>/<lens>.md` and carry the FINDINGS schema. A seat that returned a receipt but wrote no file gets one re-dispatch with the same prompt from `prompt spec-review`. A seat that fails twice is recorded as failed in the step summary and the step proceeds with the seats that delivered.

Then decide every finding, one at a time. Four outcomes: handled now, deferred, rejected, or outside boundaries. For a handled finding, edit the spec first, then post:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post finding --slug <slug> --seat <lens> --outcome handled --title "<title>"
```

The body comes from stdin — the finding's evidence and your reasoning, piped in. An empty body exits `2`. Call the tool with the emitted `args`; a `blocked` finding emits a label payload first, and its `then` must be run before the issue payload.

For a finding that falls outside the boundaries, use `post escalation` and not `post finding --outcome blocked`. The two emit the same issue, but only `post escalation` appends to `escalations.md`, and `escalations.md` is what stops the run and what `preflight` reads on a resume. A blocked issue with no gate file is a decision nothing enforces.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post escalation --slug <slug> --seat <lens> --title "<title>"
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 2 complete --slug <slug>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 2 escalated --slug <slug>
```

Then stop, in both modes. Post `escalation` exactly once per escalation: it appends, so a re-run stacks a second section under the same title. That append-only shape is deliberate — the gate log is the history of everything that ever blocked the run, and only oiler empties it.

With no escalation, re-validate the edited spec, push it to Linear, and record the step:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py validate spec "<spec path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post document spec --slug <slug>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 2 complete --slug <slug>
```

The second `post document spec` updates the recorded document in place, because `spec_doc` is now in the ledger. The second validation is not redundant: folding several findings into a spec can strand an edit mid-sentence or delete a required section as easily as authoring can.

### 3 Plan

The plan is drafted by a seat, not by you. It is long, mechanical against a fixed spec, and benefits from a reader who has not spent a step arguing with reviewers.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt plan-write <slug>
```

Dispatch one `general-purpose` seat at `opus` with that stdout as the entire prompt. Check delivery: the plan must exist at the `plan` path from `init`. Then read the draft and edit it yourself — the plan is your artifact, and the seat's draft is a draft.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py validate plan "<plan path>"
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post document plan --slug <slug>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 3 complete --slug <slug>
```

Run the `then` from `post document plan` to record `plan_doc`.

### 4 Plan review

Identical to step 2, against the plan. The command is `prompt plan-review`, the default lenses are the four in `references/plan-reviewer.md` — `coverage`, `interfaces`, `placeholders`, `tests` — and the artifact you edit, re-validate with `validate plan`, and re-post with `post document plan` is the plan. The `ledger 4 dispatched` line before the round, the delivery checks, the one re-dispatch, the per-finding decisions, the escalation path, and the `ledger 4 complete` then `ledger 4 escalated` ordering are all the same.

The plan reviewer's prompt already carries the spec path: it judges the plan against the spec, not against your intent for it.

### 5 Execute

**Checkpoint mode.** Stop here. Print, in one message: the plan path, the Linear Project URL, and the instruction to resume by invoking `superpowers:subagent-driven-development` with that plan path. The resumed session records `ledger 5 complete` after SDD finishes; do not record it now, because the step has not happened.

**Auto mode.** Invoke `superpowers:subagent-driven-development` with the plan path. SDD owns the task loop, its own ledger, per-task review, and its model selection; do not duplicate or override any of it. When it returns:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 5 complete --slug <slug>
```

If SDD escalates — a task it cannot complete within the declared boundaries — that is an escalation like any other, raised by the implementer rather than a reviewer:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post escalation --slug <slug> --seat implementer --title "<title>"
```

Then `ledger 5 complete`, `ledger 5 escalated`, and stop.

### 6 Code review

Review the branch diff. The range is `master...HEAD`, or the branch's merge base when the repository's default branch is named something else — resolve it once with `git merge-base` and use the same range for every seat.

Dispatch, in one message:

- one `general-purpose` seat at `opus` whose job is to run `/code-review` over that range,
- one `general-purpose` seat at `opus` whose job is to run `/security-review` over that range,
- any domain seats the branch warrants, at `sonnet`, dispatched through `prompt seat`.

A domain seat needs a context file. Write it to `<run_dir>/context/<seat>.md` first — the diff range, the paths the seat should look at, the goal, and who the work is for — then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt seat <slug> --seat <name> --question "<one question>" --context-file <run_dir>/context/<name>.md
```

Decide every finding as in step 2, with one difference: a handled finding is fixed on the branch by dispatching an implementer, not by you editing code. The conductor decides and records; it does not implement. Post each decision with `post finding --seat <name>`, then:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 6 complete --slug <slug>
```

### 7 Close

If the boundaries or the branch changed during the run, re-run `post project` before closing. `save_project` replaces the description on update, and `post close` sends only the closing line — so a `post close` on a stale description is what the Project keeps.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post project --slug <slug> --goal "<goal>" --boundaries "<boundaries>" --branch orko/<slug>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py post close --slug <slug> --summary "<summary>" --pr <url>
uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py ledger 7 complete --slug <slug>
```

Omit `--pr` when there is no pull request. Run `post close` once per run: `links` on a Linear project is append-only, so a second close carrying `--pr` leaves the Project with the same pull request linked twice.

Finish by printing the Project URL, the branch, and the count of issues by outcome.

## What the validators require

Author to this contract the first time. *Error handling* below allows exactly one repair attempt, and it is meant for a real defect — not for discovering the schema by trial.

**Both artifacts** — no `TBD`, `TODO`, `FIXME`, or `XXX`; no `<placeholder>` or `[fill in]`.

**Spec** — one level-1 title, plus level-2-or-deeper headings whose text contains `problem` or `goal`, `architecture` or `design`, `error`, and `test`. Every matched section needs a body. No `**Open question`, `???`, or `[?]`: an unresolved question is an escalation, not a spec line.

**Plan** — a line carrying both `REQUIRED SUB-SKILL` and `superpowers:subagent-driven-development`; a heading that is exactly `## Global Constraints`; at least one `### Task N:` block; and inside every task block a `**Files:**` line and at least one `- [ ] **Step` checkbox. The validator also rejects the vague directives `Similar to Task N`, `add appropriate error handling`, `add validation`, `handle edge cases`, and a bare `Write tests for the above` line.

**Every structural marker must be live prose, never inside a fence or backticks.** The validator blanks fenced blocks and inline code spans before it scans, so that a document may *document* a forbidden marker without *containing* one. The cost is that a required marker written inside a fence is invisible too. This bites hardest on the plan: `superpowers:writing-plans` presents its mandatory header *inside* a ```` ```markdown ```` fence, so copying that template verbatim fails with "missing the mandatory REQUIRED SUB-SKILL header line" against a plan that visibly contains it. Lift the header, `## Global Constraints`, and the task blocks out of the fence.

The placeholder scan is case-insensitive, which makes the Linear state name `Todo` a validator hit when it appears in live prose. Every Linear state name in a spec, a plan, or a reference file goes in backticks, which the scan strips.

## Reading the script's exit codes

| Exit | Meaning | What you do |
|---|---|---|
| `0` | Success; all checks passed | Continue |
| `1` | Validation failures, one finding per line with its line number | A real defect in the artifact — repair per the table below |
| `2` | Usage or IO error (bad arguments, no such run, not in a git repo, missing dependency) | Stop and report. No repair can fix a malformed invocation, and retrying a `2` in a loop just burns the run |

Never treat `2` as a validation failure. `1` means the artifact is wrong; `2` means the command was wrong.

## Ledger statuses

`complete` is the only status that advances the run. `orko.py` computes `next_step` by counting `step N complete` lines and nothing else, so the other three statuses are annotations on top of it, not alternatives to it.

- **`dispatched`** — written immediately before a round of seats goes out, so a compaction mid-dispatch leaves a record that the round started. It records that a step started, which is deliberately not the same as finishing it.
- **`complete`** — record it whenever a step's work actually finished, every time, without exception. It is the only thing stopping a post-compaction resume from re-dispatching a whole review round over an artifact that has already been reviewed.
- **`escalated`** — an *additional* line, written immediately after that step's `complete` line, never instead of it. A review that finished and escalated is still a finished review; recording only `escalated` pins `next_step` at that step forever and the resume re-runs it.
- **`failed`** — written on its own, *without* a `complete` line, because the step's work did not finish. Not advancing is the point here: the step has to run again.

## Error handling

| Condition | Behavior |
|---|---|
| `validate` fails on a freshly authored spec or plan | One repair by the same author against the findings. Second failure stops the run and reports both findings sets. |
| `validate` fails after the conductor folds in review findings | Repair your own edit. The reviewer never touched the file, so there is no reviewer intent to undo. |
| A reviewer seat returns without a findings file | Re-dispatch once, naming what failed, with the same prompt from `orko.py prompt`. Second failure records the seat as failed in the step summary and the step proceeds with the seats that delivered. |
| A Linear MCP call fails | Retry once. On second failure, stop, write the unposted payload to `<run_dir>/unposted/<step>-<n>.json`, record `ledger <step> failed`, and report. The run does not proceed past a step whose record did not land. |
| A finding is outside boundaries | Blocked issue through `post escalation`, then `complete`, then `escalated`, and stop in both modes. |
| Session compacts mid-run | Re-invoke `/orko build` from the run repository. `orko.py status` names the mode, the resume step, and the Linear IDs. Reconcile `dispatched` entries against `findings_dir` and run the escalation gate before authoring. |
| `${CLAUDE_SKILL_DIR}` empty in Bash | Fall back to `~/.claude/skills/orko/scripts/orko.py`. |
| `preflight` exit `1` | Stop at intake and print the findings. A build never starts on a default branch, outside a git repository, or without `uv`. |
| Script exit `2` | Stop and report. Never retry a usage error. |

## Ending

**checkpoint mode** — stop after step 4 and print, in one message: the plan path, the Linear Project URL, the lenses that ran and any that were dropped, and the instruction to resume into implementation by invoking `superpowers:subagent-driven-development` with the plan path.

**auto mode** — run through step 7 and print the Project URL, the branch, and the count of issues by outcome. SDD's own handoff to `superpowers:finishing-a-development-branch` still applies; do not duplicate it.

**An outstanding escalation overrides both, in either mode.** Print the artifact paths, the Project URL, and the escalation contents, state that the run is blocked on it and that clearing it means emptying `escalations.md`, then stop. Do **not** print a resume-into-implementation instruction and do not invoke `subagent-driven-development` — implementation is precisely what the escalation is blocking, and an ending that offers a resume line alongside an unresolved scope conflict invites someone to take it.

## Narration

Emit one short line at each step transition — what just finished, what is starting. Seat rounds run for many minutes with no output, so the ledger and those lines are the only signal that a long run is alive rather than hung. One line, not a status report; a running commentary defeats the purpose.
