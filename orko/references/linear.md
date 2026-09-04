# The Linear contract

Linear is the record. Git holds code and nothing else, and the run directory is scratch that any run can lose without losing the engagement. `orko.py` never calls Linear: each `post` subcommand emits a JSON payload, the conductor sends it through the Linear MCP tools, and every side effect is therefore visible in the transcript. Seats never write to Linear at all — they report to a findings file, the conductor decides, and the conductor posts the decision attributed to the seat that raised it.

## Entities

| Entity | Shape |
|---|---|
| Project | One per engagement. Its name is the slug. It lives on the team `init --team` named, and the key is uppercase letters and digits, for example `JRF`. The description is rebuilt from the ledger header on every `post project` call: goal, mode, slug, repository, branch, run directory, boundaries. |
| Documents | Attached to the Project. A build has `Spec` and `Plan`; an analysis has `Brief` and `Synthesis`. `post document <kind>` sends the file's contents as `content`, and on an update it sends the recorded document id so the document is revised rather than duplicated. |
| Issues | One per decision kicked up to the conductor. Never one per seat, never one per task. The first line of the description is `Seat: <name>`. |
| Label | `blocked`, created once per team. `post finding --outcome blocked` and `post escalation` emit the label payload ahead of the issue payload when the ledger does not yet record the label id. |

## Posting protocol

Every `post` subcommand prints one object: `{"posts": [...]}`. Work the list in order. For each entry:

1. Call the tool named in `tool` with exactly the object in `args`. Never add a key, never drop one, never rename one. You could add to a payload and nothing would catch it, which is precisely why doing so is an overt violation of a written contract rather than a judgment call you get to make in the moment.
2. If `then` is non-null, run it as an `orko.py` command with `<returned id>` replaced by the id the tool just returned. That is what records the Project, document, and label ids in the ledger, and every later `post` fails without them.

A payload whose `then` you skip is worse than a failed call: the next `post document` creates a second document instead of updating the first, and nothing reports the divergence.

When a tool call fails, retry it once. On the second failure, write the whole `posts` object to `<run_dir>/unposted/<step>-<n>.json` with Write, record `ledger <step> failed --slug <slug>`, and stop. The run does not proceed past a step whose record did not land, because the record is the deliverable.

`post finding` and `post escalation` read the issue body from stdin. Pipe in the finding's evidence and your reasoning; an empty body exits `2` rather than posting an issue nobody can act on.

## The four outcomes

Every decision is one of four, and each maps to a Linear state:

| Outcome | State | What the description must carry |
|---|---|---|
| `handled` | `Done` | The reasoning, the action taken, and the resolving edit or commit. |
| `deferred` | `Backlog` | Enough to pick up cold: file paths, the finding's evidence, and why it waited. |
| `rejected` | `Canceled` | Why the finding was not acted on. |
| `blocked` | `Todo` plus the `blocked` label | The finding and the boundary it crosses. |

Reviewer findings are decisions under this rule: one issue per finding, never a single issue summarizing a seat's report. A seat that raised four findings produces four issues, which may carry four different outcomes.

`post finding --outcome blocked` and `post escalation` emit the same issue. Only `post escalation` also appends to `escalations.md`, and only `escalations.md` stops the run and trips `preflight`'s `blocked-escalation` check on a resume. So use `post escalation` whenever the finding actually blocks the engagement, and reserve `post finding --outcome blocked` for recording a blocking condition that someone else owns and that is not stopping this run. `post escalation` appends rather than replaces, so posting the same escalation twice stacks a second section under the same title; that append-only shape is the gate log, and only oiler empties it.

## Attribution

`post finding` cannot run without `--seat`, and the first line of every issue description is `Seat: <name>`. Attribution is structural rather than a convention you have to remember: there is no way to post a decision without naming where it came from.

- A reviewer finding carries the lens name as the seat: `requirements`, `coverage`, `security`, and so on.
- A decision you reached yourself, with no seat behind it, uses `--seat conductor`.
- An escalation raised by an implementer inside `superpowers:subagent-driven-development` uses `--seat implementer`.

## Analysis engagements

The v1 analysis protocol stands. What changes is that it now opens and closes through Linear.

At the Open step, run `init analysis "<question>" --team <KEY>`, then `post project --slug <slug> --goal "<question>" --boundaries "<boundaries>"` with no `--branch`: an analysis is read-only and the Project description records that in place of a branch. Then post the brief with `post document brief --slug <slug>` and run its `then`.

At the Synthesize step, each verified finding becomes one issue through `post finding`. Where a verifier corrected a seat, the issue body carries the corrected version first, and the seat's original goes underneath in a quoted block headed "Seat's original, corrected by verifier" — the verdict is the finding, and the original is kept so a reader can see what was corrected rather than taking the correction on trust.

Outcomes map differently in an analysis, because an analysis recommends rather than acts:

- A confirmed finding oiler should act on is `deferred`, landing in `Backlog`. Nothing was fixed during the engagement, so `handled` would be false.
- A finding the verifier struck is `rejected`, landing in `Canceled`. It is recorded rather than dropped, because the fact that a seat raised it and a verifier overturned it is itself part of the record.
- A finding that changes the engagement's own question is `blocked` and goes through `post escalation`.

Then `post document synthesis --slug <slug>` and `post close --slug <slug> --summary "<summary>"`.

## Reconstruction

A lost run directory costs nothing that matters. The Project description carries the goal, mode, slug, repository, branch, run directory, and boundaries; the documents carry the spec and plan, or the brief and synthesis; the issues carry every decision. `status <slug>` prints the recorded ids, and `get_project` and `get_document` fetch the content back.

The one thing to keep true is the description. `post project` re-sends the whole description on every call, and `save_project` replaces it on update — so when the boundaries or the branch change during a run, re-run `post project` to refresh it. Do that before `post close`, which sends only its closing line: closing over a stale description freezes the stale version as the permanent record.

Run `post close` once per run. `links` on a Linear project is append-only, so a second close carrying `--pr` links the same pull request twice.

## Smoke engagements

A smoke engagement creates a real Project like any other run: same slug, same documents, same issues. Do not special-case it and do not skip the posts, because posting is the surface being smoked.

Archive the Project after the evidence report is bound. Never delete it — the report links to it, and a deleted Project turns the evidence into a dead link.
