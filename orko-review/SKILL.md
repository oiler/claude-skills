---
name: orko-review
description: >-
  oiler's independent-review battery for a written spec, plan, or project doc.
  Dispatches fresh-context Opus reviewers, one per lens, each writing a full
  report to the project's reviews folder; then verifies every finding and applies
  the accepted ones to the doc (default), or stops after the reports (--file-only).
  Invoke only as /orko-review <doc-path> [--apply | --file-only] [--spec <spec-path>], or
  /orko-review --run <run-dir> --apply to apply an earlier file-only run.
argument-hint: "<doc-path> [--apply | --file-only] [--spec <spec-path>] | --run <run-dir> --apply"
disable-model-invocation: true
allowed-tools: >-
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py preflight *)
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py start *)
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py check *)
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py decide *)
  Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py summary *)
---

# orko-review

Run one round of independent review on one document: fresh-context reviewers, one per lens, each writing a full report to disk. Then apply the findings to the document (the default) or stop after the reports (`--file-only`). Never a second round, and never a commit: oiler commits.

Below, `<run-dir>` is the `run:` path that `start` prints (or the `resume:` path from preflight). The `allowed-tools` grant covers the script's five subcommands only until oiler's next message; after that, a call may ask for permission.

## Models and effort

Each reviewer runs as the `orko-review-reviewer` agent on Opus, at high effort, in a fresh context. The agent file pins `effort: high`, so reviewers run at high whatever the session's effort, and preflight blocks if the installed agent doesn't pin it. Review is where extra effort pays off most. Independence comes from the fresh context, not a different model: move to a Fable review only when the document turns on a novel decision.

The session stays at its current effort. Preflight adds a one-line note when it's below high; it never blocks on it.

## 1. Preflight

!`python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py preflight --effort '${CLAUDE_EFFORT}' $ARGUMENTS`

If that block ends in `STATUS: blocked`, report its `problem:` and `hint:` lines and stop. Pass its `note:` line, if any, on to oiler in one line. If it shows a `resume:` line, go to step 7 with that run directory; its table is the findings index.

## 2. Choose specialists

Read the document. For each section that needs expertise the core lenses (preflight's `lenses:` line) don't cover, pick a lens from its `extras-available:` line: at most two, each with a one-line reason. Zero is normal. Don't pick one because the document mentions the topic in passing.

## 3. Start

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py start --doc <doc> --mode <mode> [--spec <spec>] [--extra <lens> --why '<reason>']…
```

Use preflight's `doc:` and `mode:` values, and pass `--spec` only if oiler passed it. Each `--extra` is followed immediately by its `--why`. `start` prints `run: <run-dir>`, then one line per lens: `<lens>: <prompt>`.

## 4. Dispatch

In one message, make one Agent call per lens, all in parallel: `subagent_type: orko-review-reviewer`, `model: opus`, and as the prompt the text after `<lens>: ` on that lens's line, unchanged. Add nothing to the prompt: no summary of the document, no concerns of your own, no mention of the other lenses. The review is worth something only because the reviewer sees just what its brief lists.

## 5. Check

When every reviewer has returned, run `python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py check --run <run-dir>`.

- Exit 0: it prints the findings index. Continue.
- Exit 2: for each `retry:` line, dispatch that lens again, once, with the same prompt as before, then run `check` again. A lens that fails twice is read leniently: its findings join the index, marked malformed, and `check` then exits 0.
- Exit 3 (`STATUS: blocked`): report the problem lines and stop. Don't apply and don't dispatch again. It means the document changed (the reviews may describe a different text) or no lens produced any finding.

## 6. File-only stop

In `file-only` mode, run `python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py summary --run <run-dir>`, paste its output unchanged, and stop.

## 7. Apply

For each finding in the index, open the document and the evidence the finding cites (read the full report at `<run-dir>/<lens>.md`), check the claim yourself, and decide:

- `accept`: the finding is correct and its fix improves the document. Make the edit. If you apply only part of the fix, `--why` says what you left out and why.
- `reject`: the evidence doesn't hold, the fix is worse than the current text, or it contradicts another accepted finding. Say which.
- `defer`: the finding needs oiler. That covers a product decision (two reasonable readings produce different observable behavior, and neither the document nor an evergreen doc picks one), a conflict with an evergreen doc that the evergreen doc may be the stale side of, and a fix that belongs in a file other than the document.

When the document contradicts an evergreen doc and the document is the side at fault, bring it into line: that's an `accept` whose `--why` names the evergreen doc and the rule. Either way, a conflict is never resolved silently.

A finding whose title starts with `malformed:` is decided like any other: read it in the report and judge it on its content. Its missing bullets aren't a reason to reject it.

Record each one with its own Bash call, and issue the calls in parallel in one message. Don't batch them into a loop, a script, or a shell function: each call must match the skill's `allowed-tools` pattern.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py decide --run <run-dir> --finding <lens>/F-<n> --verdict <accept|reject|defer> --why '<one line>'
```

For `accept`, `--why` states the change you made. Findings from different lenses that describe the same problem get the same verdict and a `--why` that names the other ID. Edit only the document under review.

Single-quote each `--why` and write `'\''` for a literal single quote: double quotes let `$` and backticks run. Single-quote every path argument the same way: the doc, the spec, and the run directory.

## 8. Summary

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py summary --run <run-dir>`. Exit 2 lists findings still undecided: decide them, then run it again. Paste its output unchanged, then write at most three items under `## Recommended`, in place of the HTML comment. Include only items that would change what oiler does next. A document that turns on a novel decision belongs here, because that case moves to a Fable review (see Models and effort). Then stop. Don't run a second round, and don't commit.
