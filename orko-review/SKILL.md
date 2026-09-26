---
name: orko-review
description: >-
  oiler's independent-review battery for a written spec, plan, or project doc.
  Dispatches fresh-context Opus reviewers, one per lens, each writing a full
  report to the project's reviews folder; then verifies every finding and applies
  the accepted ones to the doc (default), or stops after the reports (--file-only).
  Invoke only as /orko-review <doc-path> [--apply | --file-only], or
  /orko-review --run <run-dir> --apply to apply an earlier file-only run.
argument-hint: "<doc-path> [--apply | --file-only] | --run <run-dir> --apply"
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

## 1. Preflight

!`python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py preflight --effort '${CLAUDE_EFFORT}' $ARGUMENTS`

If that block ends in `STATUS: blocked`, report its `problem:` and `hint:` lines and stop. Pass each `warning:` line on to oiler in one line. If it shows a `resume:` line, go to step 7 with that run directory; its table is the findings index.

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
- Exit 2: for each `retry:` line, dispatch that lens again, once, with the same prompt as before, then run `check` again. A lens that fails twice is dropped for the run, and `check` then exits 0 with the rest.
- Exit 3 (`STATUS: blocked`): report the problem lines and stop. Don't apply and don't dispatch again. A changed document means the reviews may describe a different text.

## 6. File-only stop

In `file-only` mode, run `python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py summary --run <run-dir>`, paste its output unchanged, and stop.

## 7. Apply

For each finding in the index, open the document and the evidence the finding cites (read the full report at `<run-dir>/<lens>.md`), check the claim yourself, and decide:

- `accept`: the finding is correct and its fix improves the document. Make the edit.
- `reject`: the evidence doesn't hold, the fix is worse than the current text, or it contradicts another accepted finding. Say which.
- `defer`: the finding needs oiler. That covers a product decision, a conflict with an evergreen doc (a stop sign, never resolved silently), and a fix that belongs in a file other than the document.

Record each one:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py decide --run <run-dir> --finding <lens>/F-<n> --verdict <accept|reject|defer> --why '<one line>'
```

For `accept`, `--why` states the change you made. Findings from different lenses that describe the same problem get the same verdict and a `--why` that names the other ID. Edit only the document under review.

Single-quote each `--why` and write `'\''` for a literal single quote: double quotes let `$` and backticks run. Single-quote every path argument the same way: the doc, the spec, and the run directory.

## 8. Summary

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/orko_review.py summary --run <run-dir>`. Exit 2 lists findings still undecided: decide them, then run it again. Paste its output unchanged, then write at most three items under `## Recommended`, in place of the HTML comment. Include only items that would change what oiler does next. A document that turns on a novel decision belongs here, because `MODELS.md` escalates that case to a Fable review. Then stop. Don't run a second round, and don't commit.
