---
lens: accuracy
doc: /workshop/docs/superpowers/specs/2026-09-25-orko-review-design.md
---

# accuracy review

## Verdict

ready with changes

## Findings

### F-1 [major] The session-survey claim ("18 distinct prompts on 2026-09-25") has no command, can't be reproduced, and its quoted examples aren't from that date

- Where: Problem, paragraph 1 (line 19)
- Evidence: I reran the stated criteria over `~/.claude/projects/**/*.jsonl`. I took only top-level session files, `type: user` messages with text content not starting with `<`, containing "review", plus one of subagent/independent/fresh, plus spec or plan, and deduplicated them on their first 300 characters. That matched 161 distinct messages (159 excluding the current session), not 18. The three quoted prompts come from other dates. Quote 1 is `-Users-USER-files-projects-ajp-llmtfn/73cad597-….jsonl` at 2026-08-24T21:10:38Z. Quote 2 is `-Users-USER-files-repo-local-bt1-2026-07/9df64501-….jsonl` at 2026-09-08T20:46:26Z. Quote 3 is `-Users-USER-files-projects-afactory-rfs-campsight-lite-v1/7ae5af09-….jsonl` at 2026-08-24T20:48:41Z.
- Problem: The count doesn't match what the stated criteria return. "On 2026-09-25" reads as the date of the prompts, but the examples are from August and early September. The survey also doesn't give its command, and this spec's own accuracy lens treats that as a finding in its own right.
- Fix: Give the exact command and filter, and either correct the count or say what narrowed 161 down to 18 (for example, manual deduplication of near-duplicates). Change "on 2026-09-25" to "searched 2026-09-25; prompts dated 2026-08-24 to 2026-09-08", or to whatever range the real command returns.

### F-2 [minor] The line references for the observed `**Spec:**` forms are wrong: the headers are on line 11, not line 9

- Where: Platform facts, "New for this skill" paragraph (line 71)
- Evidence: `grep -n 'Spec:'` shows `2026-09-22-orko-sdd.md:11`, `2026-08-26-design-sys.md:11`, and `2026-09-25-orko-sdd-v0.1.1.md:11`. Line 9 in each file is `**Tech Stack:**` (for example, `2026-09-22-orko-sdd.md:9`).
- Problem: All three citations point at the wrong line.
- Fix: Change `:9` to `:11` in all three citations.

### F-3 [minor] "With or without backticks" isn't what the plans show. An unlisted form, trailing prose after the path, is common

- Where: Platform facts, line 71. Also Verification hooks, the row "Plan headers carry `**Spec:**` in the observed forms"
- Evidence: `grep -n '\*\*Spec:\*\*' docs/superpowers/plans/*.md` returns 22 lines. Every real plan header wraps the path in backticks. The only unwrapped values are a list-item URL at `2026-05-24-skill-engineering-refresh.md:273` (`- **Spec:** https://agentskills.io/specification`) and template placeholders (`{{ARTIFACT_PATH}}`, `{{SPEC_PATH}}`) deep inside plans. Several headers carry prose after the path, for example `2026-07-18-wordpress-plugins-test-harness.md:13` (`… (in the workshop repo — read it if any task's rationale is unclear).`), `2026-08-04-executable-release-gate.md:11`, `2026-08-05-cowork-builder-v0.4.0-upgrade.md:11` (a trailing `.`), and `2026-09-08-orko-v2-scaffold.md:11`.
- Problem: The observed-forms statement names a form the plans don't contain (no backticks) and leaves out one they do (backticked path followed by prose or punctuation). The verification hook only tests "all three observed forms", so it wouldn't pin the case "strip … surrounding text" exists to handle.
- Fix: Reword to: "Observed values are backticked and absolute (`/Users/…`), `~`-prefixed, or repo-relative, sometimes followed by a parenthetical or a trailing period (`2026-07-18-wordpress-plugins-test-harness.md:13`, `2026-08-05-cowork-builder-v0.4.0-upgrade.md:11`)." Add a fixture for the trailing-prose form to the hook row.

### F-4 [minor] Doc-type rule 3 matches this spec's own `**Spec:**` mention

- Where: Doc-type detection, rule 3 (line 174)
- Evidence: Line 13 of this spec is `| Upstream pin | \`superpowers:writing-plans\` 6.4.1 plan header (\`**Spec:**\` line) |`, which is inside the first 40 lines. Real plan headers put `**Spec:**` at the start of the line (all 22 grep hits above).
- Problem: As written ("the first 40 lines contain a `**Spec:**` line"), a non-plan doc that mentions the marker in a table or prose, and isn't caught by rules 1 or 2, is classified as `plan`. Preflight then blocks it for an unresolvable spec path. This spec escapes only because rules 1 and 2 match first.
- Fix: Change rule 3 to "the first 40 lines contain a line that starts with `**Spec:**`", and add a test with a mid-line mention that must stay `generic`.

### F-5 [minor] Machine-wide activation is decided up front, but the evergreen project CLAUDE.md says to ask

- Where: Release plan (line 358), "machine-wide activation (skill and agent; daily-use, so yes by default)". Only "Merge, push, and tag" need confirmation.
- Evidence: Project `CLAUDE.md`, "When oiler asks to do skill work", step 5: "For any **new** skill, ask whether to symlink it into `~/.claude/skills/<name>` for machine-wide activation (daily-use → yes; workshop-only/experimental → no)."
- Problem: The evergreen doc requires a question, and the spec leaves activation off its list of confirmation stops. The parenthetical default agrees with the spec's answer, so this is a missing ask, not a contrary decision. Arguably oiler approving the spec counts as the ask. Record that explicitly if so.
- Fix: Change the last sentence to: "Merge, push, tag, and machine-wide activation (skill and agent; recommended yes, daily-use) need oiler's confirmation." Or state in Decisions taken that oiler approved activation when he approved the spec.

### F-6 [minor] The dispatch prompt is classified as tier 2, but the skill-engineering checklist allows only tier 1 or tier 4 for a dispatch

- Where: Determinism ledger, "Dispatch prompt | 2". Also Spec checklist, line 364
- Evidence: `docs/skill-engineering.md:180`: "Every subagent dispatch the skill will make is itself classified as an output surface (model-composed = tier 4 + waiver; script-assembled = tier 1)". Line 96 says the same thing.
- Problem: The spec invents a middle classification that the checklist doesn't recognize. The session types a fixed sentence with a slot, which is tier 2 by the ladder's definition (line 103), but the dispatch rule treats a dispatch as either tier 1 or tier 4. The gap is easy to close: `start` could print the exact prompt string for each lens.
- Fix: Have `start` print `<lens>: Read <brief path> and follow it.` (the full prompt) and classify the dispatch prompt as tier 1: "script emits the exact prompt; the session passes it unchanged; the live engagement checks it." Otherwise, keep tier 2 and add a one-line note that it departs from `skill-engineering.md:180`, with the reason.

### F-7 [nit] "Carried from the orko-sdd spec … re-used unchanged" includes facts the orko-sdd spec doesn't state that way

- Where: Platform facts, line 61, bullets 2 and 7
- Evidence: `2026-09-22-orko-sdd-design.md:65` says "`~/.claude/agents/` and `.claude/agents/` are scanned recursively", and the symlink-following probe (`:73`) covered "a symlinked directory under `.claude/agents/`", the project level, not `~/.claude/agents/`. The `!cmd` nonzero-exit bullet cites `docs/skill-reference.md` §3 (`skill-reference.md:87`, which is correct: "Any non-zero exit fails, except exit 1 from search/comparison commands"). It isn't among the orko-sdd platform facts. The user-level symlink claim does hold in practice: `~/.claude/agents/orko-sdd -> …/claude-skills/orko-sdd/agents` exists, and its `orko-sdd-*` agents resolve in this session.
- Problem: The provenance line claims every bullet came unchanged from one source.
- Fix: Change bullet 2 to "`~/.claude/agents/` and `.claude/agents/` are scanned recursively; a symlinked directory is followed (probed at project level 2026-09-22; user level observed working with `~/.claude/agents/orko-sdd` since 2026-09-23)". Move the `!cmd` bullet under its own "from `docs/skill-reference.md` §3" lead-in.

### F-8 [nit] The platform facts were verified on Claude Code 2.1.280, but 2.1.283 is installed

- Where: Platform facts, line 61
- Evidence: `claude --version` prints `2.1.283 (Claude Code)`.
- Problem: The carried facts haven't been re-probed on the version the live engagement will run. Nothing I checked contradicts them.
- Fix: Add "(installed 2.1.283 at spec time; the live engagement re-exercises the agent resolution and effort facts)". The live engagement already covers most of them.

## Checked and sound

- `~/.claude/MODELS.md:3` quote, "raised to high for spec and plan work, brownfield bug fixes, and verification passes", matches word for word. The session default is now Opus 5.5 at medium (MODELS.md:3, global CLAUDE.md:68). The file's mtime is 2026-09-25 19:36, which fits "since the 2026-09-25 update".
- `MODELS.md:32` quote, "Subagents without an `effort:` in their definition inherit the session level at dispatch", matches word for word.
- The MODELS.md Spec review and Plan review rows (lines 11 and 14): Opus 5.5, high, fresh context. "Independence comes from a fresh context, not a different model" and "move to Fable only if the spec turns on a novel decision" both match word for word.
- The writing-plans 6.4.1 `**Spec:**` header is at `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.4.1/skills/writing-plans/SKILL.md:69`, and the quoted text matches. 6.4.1 is the installed version (`installed_plugins.json`).
- The three past-prompt quotes in Problem match the session transcripts; the `…` in quote 2 elides "have them report back to you at when all reports are in,". The drift examples `revisions/`, "the reviews folder for this version" (ajp-resource-hub-build sessions), and `planning/reviews/` (ajp-resource-hub-build sessions) all appear in past sessions.
- The platform facts carried from `2026-09-22-orko-sdd-design.md:59-76` hold: `effort` frontmatter, model resolution order, `disallowedTools: Agent`, `omitClaudeMd`, `disable-model-invocation`, the lifetime of an `allowed-tools` grant, and "subagent transcripts don't record effort".
- `docs/skill-reference.md` §2 lists `${CLAUDE_EFFORT}` ("Current effort level") and `${CLAUDE_SKILL_DIR}`. Line 64 confirms `${CLAUDE_SKILL_DIR}` substitutes inside `allowed-tools`, and `argument-hint` is a documented frontmatter field (line 27).
- `claude --help` lists both `--effort <level>` and `--model <model>`, as the eval plan's `claude -p --model opus --effort medium` needs.
- The evergreen filename list (`CLAUDE.md`, `AGENTS.md`, `PROJECT.md`, `OBJECTIVE.md`, `DESIGN.md`, `ARCHITECTURE.md`) matches global CLAUDE.md "Document authority" (line 106).
- Linking non-negotiable #8 to priming is supported by `docs/skill-engineering.md:96` and `:171` ("never prime a verifier with the conclusions — or the context — of the pass it's checking").
- The determinism tier definitions (1 script owns write, 2 verbatim template, 3 script-validated, 4 pinned prose, with waivers for tier 4) match `docs/skill-engineering.md:100-107`.
- The eval plan for change class `new` (invocation instrument, which is live engagement for slash-only skills, plus clean-room smoke plus script tests) matches `docs/skill-engineering.md:122-135`. So does one report satisfying both through `satisfies: [live-engagement, clean-room]`.
- The release gate shorthand agrees with `skill-engineering.md:214` (`scripts.preflight <skill> --change-class … --candidate-version …`).
- The public repo has `master` and `docs/changelogs/` (holding orko-sdd.md among others), so `docs/changelogs/orko-review.md` fits the convention.
- The quoting rule (single-quote, `'\''`) matches `orko-sdd/SKILL.md:50`. The `$ARGUMENTS` interpolation risk matches `2026-09-22-orko-sdd-design.md:258`. The Recommended-last rationale matches orko-sdd spec line 55 (Verified dropped when it sat after the model slot).
- The drafted `agents/orko-review-reviewer.md` in the `feat/orko-review` worktree matches the spec's Agent block word for word. All 14 lens files in the File structure exist under `references/lenses/`.
- The run directory layout and reviews-dir rule 1 (the nearest `superpowers/` ancestor) match the location of this review run: `docs/superpowers/reviews/2026-09-25-orko-review-design/2026-09-25-195039/`.
