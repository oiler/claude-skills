# orko v2 build engagement design

## Summary

orko v2 turns orko from an analysis instrument into a conductor with two engagement types under one persona, one script, and one record. `/orko <question>` keeps the v1 analysis lifecycle. `/orko build <goal>` adds a build lifecycle that folds the `autonom` skill into orko: intake, spec, spec review, plan, plan review, execute through `superpowers:subagent-driven-development`, code review, close. Linear holds the record for both engagement types. Git holds code and nothing else. The run directory is scratch.

This spec implements the design recorded in `orko/references/upgrades.md` under "Build engagement (v2, agreed design)" on 2026-09-04. Where that design left a decision open, this spec closes it and says so.

Target-surface profile: `claude-code`. Public repo `~/files/repo/claude-skills/`, skill folder `orko/`, release `orko-v1.0.0`. The version jumps to 1.0.0 because the run directory moves and the record moves to Linear. A v0.2.0 trail under `docs/sessions/` is not read by v2.

## Problem and goals

### Problem

Today oiler runs two skills that share one shape and disagree on the details. orko dispatches seats and writes a `docs/sessions/` trail. autonom dispatches reviewers and writes a `.superpowers/autonom/` ledger, commits product docs into the target repo, and hands reviewers write authority that then needs a separate-commit safeguard. Neither leaves a record a human can open a week later without a checkout. Decisions the conductor makes mid-run, including every reviewer finding it accepts or rejects, live only in a transcript.

### Goals

- One skill, one persona, one script, one trail convention for analysis and build work.
- Every decision kicked up to the conductor lands as a Linear issue with one of four outcomes, so nothing is decided only in a transcript.
- Product docs stop being committed to project repos. The spec and plan live in the run directory as working copies and in Linear as the record.
- Reviewer seats report only. The conductor is the sole writer to the artifacts and to Linear.
- The script keeps owning every deterministic surface it owned in autonom, and gains the Linear payloads.
- autonom's ledger, resume logic, validators, escalation gate, and one-question onboarding survive the merge intact.

### Non-goals

- Calling Linear from the script. The script emits payloads; the conductor posts them through the Linear MCP tools. This keeps every side effect visible in the transcript.
- Persistent seats, a curated agent cast, or a Workflow DAG. Those stay documented upgrades in `references/upgrades.md`.
- Changing `superpowers:subagent-driven-development`. Execution is delegated to it unchanged.
- Backfilling v0.2.0 analysis trails into Linear.
- A trigger eval. The skill stays `disable-model-invocation: true`, so the instrument is a live clean-room smoke engagement.

## Background

orko v0.2.0 (`orko/SKILL.md`, 117 lines) defines the conductor, the gate before dispatch, six-seat rounds, per-seat verifiers, delivery checks, and the FINDINGS schema in `references/seats.md`. autonom v0.1.0 (`autonom/SKILL.md`, 294 lines) defines a four-step relay backed by `scripts/autonom.py` (615 lines, 11 test classes in `scripts/test_autonom.py`): `init`, `ledger`, `status`, `validate`, `prompt`, `escalations`. Its v0.2.0 backlog carries three documented defects: an escalation-step ambiguity, an undocumented fallback when `${CLAUDE_SKILL_DIR}` resolves empty inside Bash, and no topic-string guidance. All three are closed by this spec.

Linear is confirmed configured. The workspace has one team, key `JRF`, with issue states `Backlog`, `Todo`, `In Progress`, `In Review`, `Done`, `Canceled`, `Duplicate`. There is no "Blocked" state, so the design's fourth outcome maps to a label plus the `Todo` state, described under "Linear contract".

## Architecture

### Skill layout

```
orko/
├── SKILL.md                      # conductor persona, both lifecycles, routing; stays under 300 lines
├── references/
│   ├── seats.md                  # unchanged: catalog, FINDINGS schema, seat and verifier templates
│   ├── build.md                  # build lifecycle step by step; validator contract; error table
│   ├── linear.md                 # the Linear contract: entities, outcomes, attribution, payload shapes
│   ├── upgrades.md               # v2 section rewritten from "agreed design" to "shipped" pointers
│   ├── spec-reviewer.md          # reviewer seat charter, report-only
│   └── plan-reviewer.md          # reviewer seat charter, report-only
└── scripts/
    ├── orko.py                   # autonom.py renamed and extended
    └── test_orko.py              # test_autonom.py renamed and extended
```

`autonom/` becomes a one-release deprecation stub: a `SKILL.md` under 20 lines with `disable-model-invocation: true`, no `allowed-tools`, no scripts, whose body says the skill moved to `/orko build` and names the last full version tag `autonom-v0.1.0`. The stub ships as `autonom-v0.2.0`. `evals/autonom/` stays as history. The machine-wide symlink `~/.claude/skills/autonom` is removed at release.

### The run directory

Both engagement types write scratch to `.orko/<slug>/` under the target repository root. `init` appends `.orko/` to the target's `.gitignore` when absent, using autonom's `ensure_gitignored`. The `docs/sessions/` and `.superpowers/autonom/` locations are gone.

```
.orko/<slug>/
├── progress.md          # ledger: header, Linear IDs, step records
├── brief.md             # analysis: request, seats, dispatch plan
├── findings/            # analysis and build reviews: <seat>.md, <seat>.verdict.md
├── spec.md              # build: working copy
├── plan.md              # build: working copy
└── escalations.md       # build: appended only by `orko.py post escalation`, never by a seat or by hand
```

The spec and plan no longer carry a date in their filename. The run directory is scratch and the Linear document is the record, so the filename only needs to be stable for the validators and the seats.

### The script

`scripts/orko.py` keeps every autonom subcommand and its exit-code contract: `0` success, `1` validation findings, `2` usage or IO error. Changes:

| Subcommand | Change |
|---|---|
| `init <mode> <topic> --team <key>` | Gains a positional `mode` of `analysis` or `build` and a required `--team`. Writes the mode and team into the ledger header and emits the run paths. The Project payload is a separate `post project` call, because the goal and boundaries are settled at intake, after `init` has minted the slug. |
| `ledger <step> <status>` | Steps are per mode: analysis `1..6`, build `0..7` as in the lifecycle table. Statuses unchanged: `dispatched`, `complete`, `escalated`, `failed`. |
| `status [<slug>]` | Reports `mode`, `team`, and the recorded Linear IDs alongside the resume point. |
| `validate {spec\|plan} <path>` | Unchanged rules. Fixtures named under "Validators". |
| `prompt <kind> <slug> ...` | `kind` is one of `spec-review`, `plan-review`, `plan-write`, `seat`, `verifier`. The first three emit a charter file from `references/` with paths substituted; `--lens <name>` picks one row of the review charter's lens table so each parallel reviewer gets one question. `seat` and `verifier` emit the v1 templates from `references/seats.md` with `--seat <name>`, `--question <text>`, and `--context-file <path>` substituted, so analysis dispatches are script-assembled too. Any unsubstituted token exits `2`. |
| `escalations <slug>` | Unchanged gate. |
| `linear set <key> <id>` / `linear get` | New. Records and reads `project`, `spec_doc`, `plan_doc` IDs in the ledger so a resumed session can re-fetch. |
| `post <entity> ...` | New. Emits `{"posts": [{"tool", "args", "then"}]}`, one entry per Linear MCP call, shaped for the named tool. Entities: `project`, `document`, `finding`, `escalation`, `close`. See "Linear contract". |
| `preflight` | New. Checks in code what autonom's prose asked the orchestrator to check: inside a git repo, `uv` on PATH, not on `master` or `main` for build mode, run directory gitignored, Linear IDs present when the ledger is past step 0. Exit `1` with one finding per line. |

The script cannot call Linear. Every `post` payload passes through the conductor, who calls the MCP tool with the payload's `args` verbatim and then records the returned ID with `linear set` where the payload says to. This is the bright-line contract autonom used for reviewer prompts, applied to Linear writes: the conductor can add to a payload, and nothing would catch it, but doing so is an overt violation of a written contract rather than a judgment call.

### Reviewer seats are report-only

autonom's reviewers edited the artifact in place and committed. v2 reviewers are orko seats: they read the artifact and the repository, write a findings file in the FINDINGS schema to `.orko/<slug>/findings/<seat>.md`, and return a receipt. They have no write authority on the artifact, no git access, and no Linear access. The separate-review-commit safeguard is deleted with the authority that required it.

Spec review and plan review each dispatch two to four reviewer seats in parallel, one lens each. The lens table lives in each charter file and the conductor picks lenses at the step, not at intake. Default lenses for a spec: requirements coherence, architecture against the actual code, testability, security. Default lenses for a plan: spec coverage, task independence and interface consistency, placeholder and vagueness scan, test design. The conductor may drop a lens that has nothing to examine and must say so in the Linear step summary.

Review seats run at `opus`. This is a deliberate exception to orko's default-down tiering: a spec or plan review is the judgment-heavy step in a build, and autonom escalated to Fable for the same reason. The conductor may raise a single seat to `fable` when the artifact carries a design decision it cannot evaluate itself and must say why in the step summary. Verifiers are not dispatched on review seats; the conductor's per-finding decision, recorded in Linear, is the check.

### Build lifecycle

| Step | Conductor | Dispatches | Linear |
|---|---|---|---|
| 0 Intake | Reads goal and init docs. Asks one round of clarifying questions, including autonom's checkpoint-or-auto question and the target repo. Confirms branch and boundaries. Runs `init build`, creates branch `orko/<slug>`, then runs `preflight` (which rejects a build on a default branch). | none | Project created. Description carries goal, boundaries, repo, branch, run directory, slug. |
| 1 Spec | Writes `.orko/<slug>/spec.md`. Runs `validate spec`. | none | Document "Spec" created. `linear set spec_doc`. |
| 2 Spec review | Dispatches reviewers. Checks delivery. Decides per finding, edits the spec, re-validates. | 2 to 4 reviewer seats at `opus` | One issue per finding. Document "Spec" updated. |
| 3 Plan | Dispatches one plan-writer seat that drafts `.orko/<slug>/plan.md` from the spec. Edits the draft. Runs `validate plan`. | one plan-writer at `opus` | Document "Plan" created. `linear set plan_doc`. |
| 4 Plan review | As step 2 against the plan. | reviewer seats | As step 2. Document "Plan" updated. |
| 5 Execute | Checkpoint mode stops here with the resume instruction. Auto mode invokes `superpowers:subagent-driven-development` with the plan path. | SDD owns implementers | Issue per escalation only, never per task. |
| 6 Code review | Dispatches review seats over the branch diff, including one seat that runs `/code-review` and one that runs `/security-review`. Fixes or backlogs each finding. | review seats at `sonnet`, `opus` for the two tool-running seats | One issue per finding. |
| 7 Close | Writes the summary. Links the PR when one exists. | none | Project state Completed. Backlog issues remain open. |

After intake the conductor is in charge within the declared boundaries. autonom's pre-authorization to skip the brainstorming User Review Gate and the writing-plans Execution Handoff applies to build engagements only, and only after intake. `references/build.md` carries the "do not correct this back" paragraph from autonom verbatim.

The plan-writer in step 3 is a seat because the plan is long, mechanical against a fixed spec, and benefits from a fresh reader who has not been arguing with reviewers. The spec in step 1 is the conductor's own because it holds the intake context and the boundaries. This mirrors autonom, which authored both on the session, in one direction only.

The escalation gate is unambiguous in v2. A finding the conductor classifies as outside boundaries goes through `post escalation`, which emits the blocked issue and appends the finding to `escalations.md`; the conductor then records `ledger <step> complete` then `ledger <step> escalated`, and the run stops before the next step in both modes. Only oiler empties `escalations.md`. The autonom rule that a step-7 escalation still left `next_step` pointing forward is preserved, and the resume sequence runs the gate before authoring anything, exactly as autonom's startup step 6 did.

### Analysis lifecycle

The v1 protocol stands with three changes. The trail moves to `.orko/<slug>/`. `init analysis` runs at the Open step and creates the Project. At Synthesize, each verified finding becomes one Linear issue through `post finding`, and `synthesis.md` is posted as a Project document "Synthesis". Verifier verdicts feed the issue: a finding a verifier labeled overstated or unsubstantiated is posted with the verdict's corrected version and the seat's original in a quoted block.

### Linear contract

One Project per engagement, on the team `init --team` names. The project name is the slug. The Project description is rebuilt from the ledger header on every `post project` call, so a lost run directory can be reconstructed from Linear alone: goal, mode, repo root, branch, run directory, slug, boundaries.

Documents attach to the Project. Build: "Spec", "Plan". Analysis: "Brief", "Synthesis". `post document` emits `save_document` with the file contents as `content`; on update it passes the recorded document ID.

Every decision kicked up to the conductor is one issue. Reviewer findings are decisions under this rule, one issue per finding, not one per seat. The four outcomes:

| Outcome | Linear state | Extra | Effect on the run |
|---|---|---|---|
| Handled now | Done | Description carries reasoning, action taken, and the resolving edit or commit | continues |
| Deferred | Backlog | Description carries enough context to pick up cold: file paths, the finding's evidence, the reason it waited | continues |
| Rejected | Canceled | Description carries why | continues |
| Outside boundaries | `Todo` with label `blocked` | Description carries the finding and the boundary it crosses | stops; escalation gate |

`post finding` takes `--seat`, `--outcome`, `--title`, and reads the finding body from stdin. It emits `save_issue` with the team, the project ID from the ledger, the mapped state, the label when blocked, and a description whose first line is `Seat: <seat>` followed by the body. Attribution by seat is structural: the conductor cannot post a finding without naming the seat that raised it. The `blocked` label is a workspace label created once, on first use. `post finding --outcome blocked` emits a preceding `save_issue_label` payload (`name` and `color` only; the tool has no team parameter) when the ledger does not record the label; before sending it the conductor checks `list_issue_labels` for an existing `blocked` label and, if one exists, records its id instead of creating a duplicate.

`post escalation` is `post finding --outcome blocked` and additionally appends the title, seat, and body to `escalations.md` itself, so the gate file is script-written. `post close` emits `save_project` with state `Completed` and a `patch` that appends a closing line, so the reconstruction block in the description survives the close. It runs once per run, because project links are append-only.

Seats never write to Linear. The conductor posts, attributed by seat.

### Frontmatter decisions

```yaml
name: orko
description: >-
  (v1 description extended with the build engagement and Linear record;
  final text set at the description pass, budget 1,536 chars)
disable-model-invocation: true
argument-hint: "[question] | build <goal> [init docs]"
allowed-tools: >-
  Agent Task Read Write Edit Grep Glob Skill
  Bash(uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py *)
  Bash(git rev-parse *) Bash(git log *) Bash(git status *) Bash(git diff *)
  Bash(git checkout -b orko/*) Bash(git checkout orko/*) Bash(git branch *)
  mcp__linear__save_project mcp__linear__get_project
  mcp__linear__save_document mcp__linear__get_document
  mcp__linear__save_issue mcp__linear__get_issue mcp__linear__list_issues
  mcp__linear__save_issue_label mcp__linear__list_issue_labels
  mcp__linear__save_comment
metadata:
  author: oiler
  version: 1.0.0
```

The `Bash(uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py *)` rule relies on the documented substitution inside `allowed-tools` (Claude Code v2.1.129+, per `docs/skill-reference.md`). In the body, every script invocation is written as `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py`, and SKILL.md states the fallback once: if the substitution yields an empty string in a Bash call, use `~/.claude/skills/orko/scripts/orko.py`, which is the machine-wide symlink. This closes the autonom defect.

No `Bash(git add *)` or `Bash(git commit *)`. The conductor commits nothing in v2. SDD's implementers commit under their own permissions.

### Determinism ledger

| Output surface | Tier | Mechanism or waiver |
|---|---|---|
| Run paths, slug, ledger lines, `next_step` | 1 | `orko.py init`, `ledger`, `status` |
| Reviewer seat dispatch prompts (spec, plan) | 1 | `orko.py prompt`, verbatim charter plus substituted paths and lens |
| Linear payloads: project, document, finding, escalation, close | 1 | `orko.py post`; conductor passes `args` verbatim |
| Spec and plan | 3 | conductor and plan-writer author; `orko.py validate` gates every write including post-review edits |
| Analysis seat and verifier dispatch prompts | 1 | `orko.py prompt seat` and `prompt verifier`, verbatim templates from `references/seats.md` with the seat name, scoped question, and a context file substituted. v1 left these at tier 2; v2 can promote them because every analysis engagement now runs `init` before the first dispatch. The context file is the conductor's one authored input and is written to `.orko/<slug>/context/<seat>.md`. |
| Plan-writer dispatch prompt | 1 | `orko.py prompt plan-write`, verbatim charter |
| Code-review seat prompts | 2 | seat template from `references/seats.md` with the diff range and tool name filled; Waiver: the lens per code-review seat varies by what the branch touched, so a fixed charter would either over-constrain or say nothing. The template's frame is verbatim; only the scoped question is authored. |
| Per-finding decision text inside a Linear issue | 4 | Waiver: the reasoning for handling, deferring, or rejecting a finding is the conductor's judgment and is the thing the record exists to capture. The frame (`Seat:` line, outcome, state) is tier 1. |
| Project description, step summaries, close summary | 4 | Waiver: same reason. The required fields are enforced by `post project` and `post close`, which refuse to emit without them. |
| Synthesis (analysis) | 4 | Waiver: unchanged from v1; the verdict-beats-finding rule is prose. |

### Validators

Rules are unchanged from autonom. Fixtures:

- `validate spec` passing fixture: this document. It carries a level-1 title and headings matching `problem` or `goal`, `architecture` or `design`, `error`, and `test`, each with a body, and no placeholder markers outside code.
- `validate plan` passing fixture: the implementation plan for this spec, `docs/superpowers/plans/2026-09-04-orko-v2-build.md`, written to `superpowers:writing-plans` with the mandatory header lifted out of the fence.

Both fixtures are copied into `orko/scripts/fixtures/spec.md` and `orko/scripts/fixtures/plan.md` and run through the validators in the test suite, so a rule change that rejects a real artifact fails a test. The copies are refreshed whenever the workshop originals change.

One rule interacts with the Linear contract: the placeholder scan is case-insensitive, so the Linear state name `Todo` is a validator hit in live prose. Every mention of a Linear state name in a spec, plan, or reference file goes in backticks, which the scan strips. The plan and `references/linear.md` follow this.

## Error handling

| Condition | Behavior |
|---|---|
| `validate` fails on a freshly authored spec or plan | One repair by the same author against the findings. Second failure stops the run and reports both findings sets. |
| `validate` fails after the conductor folds in review findings | The conductor repairs its own edit. The reviewer never touched the file, so autonom's "stop, no repair" rule no longer applies. |
| A reviewer seat returns without a findings file | Re-dispatch once, naming what failed, with the same prompt from `orko.py prompt`. Second failure records the seat as failed in the step summary and the step proceeds with the seats that delivered. |
| A Linear MCP call fails | Retry once. On second failure, stop, write the unposted payload to `.orko/<slug>/unposted/<n>.json`, record `ledger <step> failed`, and report. The run does not proceed past a step whose record did not land. |
| A finding is outside boundaries | Blocked issue, `escalations.md`, `complete` then `escalated`, stop in both modes. |
| Session compacts mid-run | Re-invoke `/orko`. `orko.py status` names the mode, the resume step, and the Linear IDs. The resume sequence from autonom applies: reconcile `dispatched` entries, run the escalation gate before authoring. |
| `${CLAUDE_SKILL_DIR}` empty in Bash | Fall back to `~/.claude/skills/orko/scripts/orko.py`. |
| `preflight` exit `1` | Stop at intake and print the findings. A build never starts on `master`, outside a git repo, or without `uv`. |
| Script exit `2` | Stop and report. Never retry a usage error. |

## Testing

Script tests in `orko/scripts/test_orko.py`, run with `uv run pytest`. The autonom suite carries over renamed, and new tests cover:

- `init` with each mode writes the mode and team to the header; missing `--team` exits `2`.
- `ledger` accepts the per-mode step range and rejects a build step on an analysis run.
- `linear set` and `linear get` round-trip; `status` reports the IDs.
- `post project` refuses to emit without goal, repo, branch; `post finding` maps each outcome to the right state and adds the `blocked` label; `post finding` output always starts its description with `Seat: <seat>`; every payload's `args` keys are a subset of the named MCP tool's documented parameters, checked against a fixture list in the test file.
- `prompt spec-review --seat <lens>` substitutes every token and leaves none; an unknown lens exits `2`.
- `preflight` reports each failing condition by name, using a temporary repo on `master` and a repo with no `.orko/` gitignore line.
- The two named fixtures pass their validators.

Mutation verification: for `post finding`, the outcome-to-state mapping folds four conditions into one function. One test per outcome, each named to the outcome, so removing one branch turns exactly one test red.

Eval instrument: a live clean-room smoke engagement. A subagent that has read only the shipped `orko/` files runs `/orko build` against a small throwaway repository with a two-task goal, in checkpoint mode, and a second subagent runs `/orko <question>` analysis against the same repository. Both post to real Linear Projects named by their slugs; the report records the Project URLs, and the Projects are archived after the report is bound. The report goes to `evals/orko/smoke-<date>.md` with `satisfies: [live-engagement, clean-room]`. Release runs `preflight orko --change-class structural --candidate-version 1.0.0`.

## Release

- Branch `feat/orko-v2` off `master` in `~/files/repo/claude-skills/`.
- `docs/changelogs/orko.md` gains v1.0.0; `docs/changelogs/autonom.md` gains v0.2.0 (deprecation stub).
- Tags `orko-v1.0.0` and `autonom-v0.2.0` per the per-skill release convention.
- Remove `~/.claude/skills/autonom`. `~/.claude/skills/orko` already exists.
- Workshop: regenerate `docs/library-status.md`; add a `docs/workshop-state.md` decision entry for "Linear is the record, git is for code".
