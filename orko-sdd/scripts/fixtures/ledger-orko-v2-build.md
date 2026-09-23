# SDD ledger — plan: ~/files/projects/001-claude-skills-creator/docs/superpowers/plans/2026-09-04-orko-v2-build.md
Spec: ~/files/projects/001-claude-skills-creator/docs/superpowers/specs/2026-09-04-orko-v2-build-design.md
Repo: ~/files/repo/claude-skills, branch feat/orko-v2 off master (68d9ba9) + cherry-pick of c19f28c (v2 design in upgrades.md, from branch claude/ai-workflow-lead-subagents-isz2co)

## Pre-flight conflict scan

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 → T2 | compute_paths keys, _run_dir_root | T2 consumes both; T1 leaves header tests red, T2 fixes. Global Constraints already permit. Clean |
| T2 → T3 | _describe_run dict | T3 adds linear=_linear_ids(ledger). Clean |
| T3 → T4/T5 | run["linear"], _linear_ids | _load_run in T4 consumed by T5 and T6. Clean |
| T4 → T6 | _load_run, references_dir | T6 cmd_prompt uses _load_run. Clean |
| T4 test MCP_PARAMS → T5 | assert_posts_are_well_formed | T5 tests call it; defined at module top in T4. Clean |
| T5 → T7 | escalations.md written by post escalation | T7 preflight reads it. Clean |
| T6 → T9/T10 | prompt kinds and flags | docs must name them exactly; T9 step 3 --help loop checks. Clean |
| T8 → T10 | fixtures | plan fixture is a snapshot; plan edits after T8 need re-copy. Ruling below |
| T2 self | test expects next_step==0 for build; _describe_run uses 'is not None' | consistent |
| T5 self | args.entity dest set on post_sub | consistent |
| T6 self | LENS_ROW_RE vs table header/separator | header 'Lens' capitalized → no match; separator '---' → no match. consistent |
| T7 self | symbolic-ref on unborn branch | verified 'master' on a fresh git init -b master. consistent |
| T11 self | rm -rf autonom/scripts after git mv | git mv already moved tracked files; rm hits only untracked pycache. consistent |

Ruling: fixtures copied in T8 are refreshed once more after T11 if the workshop plan changed — why: spec says copies refresh when originals change — cost if wrong: stale fixture, no behavior impact.
Ruling: pre-flight scan clean; proceed to Task 1.

Task 1: implementer done fcc0685 (7 failing as expected: header + TestPrompt). BASE b41d456.
Ruling: the "no stale paths in shipped orko files" constraint is a branch end-state check (Task 10 step 4), not a per-task gate — why: v1 SKILL.md/seats.md/upgrades.md are rewritten in Tasks 6 and 10 — cost if wrong: none, Task 10 greps for it.
Ruling: deleting the two workshop-fixture validator tests in Task 1 is accepted — why: they pointed at v1 artifact paths and Task 8 replaces the coverage with in-repo fixtures — cost if wrong: validator unpinned between Tasks 1 and 8 only.
Task 1: minor (deferred): test_orko.py continuation-line indentation over-indented after sed (E127, ~40 sites) — reflow once before branch review
Task 1: minor (deferred): TestSlugify still slugifies "Autonom Pipeline" — rename the input
Task 1: minor (deferred): compute_paths and _run_dir_root both hold the ".orko" literal
Task 1: complete (commits b41d456..fcc0685, review clean)
Task 2: implementer done 375efbb. BASE fcc0685. Concern: TestPrompt xfail strict — Task 6 dispatch must remove markers.
Task 2: review — 1 Important (plan-mandated: TEAM_RE `$` admits trailing newline → None deref in cmd_init), 6 minor.
Ruling: plan-mandated TEAM_RE finding is fixed, not parked — why: spec requires exit codes 0/1/2 and the plan's regex breaks that; `fullmatch` is the one-token fix — cost if wrong: none.
Task 2: minor (deferred): cmd_ledger says "no run named; run init first" for a corrupt-header ledger (plan-mandated message)
Task 2: minor (deferred): HEADER_LINE_RE team group looser than TEAM_RE (accepted: hand-edited ledgers still parse)
Task 2: minor (deferred): a differing --team on resume is silently ignored; header wins with no signal
Task 2: minor (deferred): no test exercises dispatched_base at build step 0
Task 2: note: SKILL.md still documents autonom-era init signature — Task 10 rewrites SKILL.md
Task 2: fix round 1/5 (2 addressed, 0 open; commits 375efbb..dbb8317)
Task 2: complete (commits fcc0685..dbb8317, review clean)
Task 3: implementer done a480ca0. BASE dbb8317.
Task 3: review — 2 Important (both plan-mandated: whitespace guard misses Unicode whitespace → silent ID loss; unknown-key test asserts only exit code), 3 minor.
Ruling: both plan-mandated findings are fixed in round 1 — why: silent loss of the Project ID defeats the ledger's reconstruction purpose; the test fix makes the choices rejection discriminating — cost if wrong: none.
Task 3: minor (deferred): positional `id` cannot start with `-` (argparse); theoretical for Linear IDs
Task 3: minor (deferred): fifth copy of the root/no-run preamble across cmd_* — whole-file cleanup candidate for branch review
Task 3: minor (deferred): "no run named" message inconsistently carries "; run init first"
Task 3: fix round 1/5 (2 addressed, 0 open; commits a480ca0..0e4122e)
Task 3: complete (commits dbb8317..0e4122e, review clean)
Task 4: implementer done 15cb08a. BASE 0e4122e.
Ruling: `--boundaries` on `post project` is an optional argparse arg checked in cmd_post_project (exit 2 with orko: message) rather than required=True — why: the plan's own verbatim test asserts a returned rc==2 without --boundaries, which argparse's SystemExit cannot satisfy; the spec only requires refusal — cost if wrong: none, contract identical.
Task 4: note for Task 9: linear.md must state `post project` precedes `post close` when the description needs refreshing (close replaces description).
Task 4: review — 1 Important (no test on the --boundaries refusal branch), 5 minor. Payload keys verified against live MCP schemas by reviewer.
Task 4: minor (deferred): _load_run added but the four older cmd_* still inline the same preamble — whole-file cleanup candidate
Task 4: minor (deferred): test_refuses_without_goal_or_branch only exercises the branch half (goal is argparse-required)
Task 4: note for Task 9: linear.md — `post close` once per run (links append-only), and `post project` before `post close` to refresh the description
Task 4: fix round 1/5 (1 addressed, 0 open; commits 15cb08a..8028443)
Task 4: complete (commits 0e4122e..8028443, review clean)
Task 5: implementer done 61af599. BASE 8028443. Mutations: handled/deferred/rejected each killed exactly one test.
Task 5: note for Task 9/10: docs must say `post finding --outcome blocked` does not write the gate file; only `post escalation` does. Script docstring Usage block needs the post/linear/preflight subcommands (Task 7 or 11).
Task 5: minor (deferred): escalation/blocked tests don't call assert_posts_are_well_formed; empty-body and missing-project guards untested via post escalation
Task 5: minor (deferred): escalation append is non-idempotent (append-only gate log; document rather than change)
Task 5: complete (commits 8028443..61af599, review clean)
Task 6: implementer done 858cbd8. BASE 61af599. Suite 122 passed, xfails gone.
Ruling: reviewer charters reworded from "You have no write authority on the spec..." to "You may not write to the spec..." — why: the plan's own test forbids the substring "write authority on the spec/plan" (it was written to catch autonom's grant); meaning unchanged — cost if wrong: none.
Task 6: review — 2 Important (stale Usage block; plan-mandated leftover scan over assembled text misfires on operator text containing {{TOKENS}}), 2 minor.
Ruling: leftover-token check moves to the raw template (template tokens minus subs keys) — why: operator-authored context legitimately quotes tokens when the seat investigates orko itself; the raw-template check still guarantees no token survives — cost if wrong: none.
Task 6: minor (deferred): --question required but unused for verifier; cross-kind flags silently ignored
Task 6: fix round 1/5 (2 addressed, 0 open; commits 858cbd8..5e46ddb)
Task 6: complete (commits 61af599..5e46ddb, review clean)
Task 7: implementer done 4df7aea. BASE 5e46ddb.
Task 7: minor (deferred): preflight exit-2 paths "slug names no run" and "neither --slug nor --mode" untested
Task 7: minor (deferred): --root pointing into a subdirectory is accepted unnormalized (pre-existing _resolved_root convention)
Task 7: minor (deferred): cmd_preflight docstring cites autonom review counts — reword to age better
Task 7: complete (commits 5e46ddb..4df7aea, review clean)
Task 8: implementer done 543a796. BASE 4df7aea.
Task 8: complete (commits 4df7aea..543a796, review clean)
Task 9: implementer done bcc0856. BASE 543a796.
Ruling: Task 10 adds `Bash(git merge-base *)` to allowed-tools — why: build.md step 6 needs the merge base for the code-review diff range and the spec's list omitted it — cost if wrong: one extra read-only git grant.
Task 9: review — 3 Important (git merge-base not allowed and redundant; post close replaces the description, voiding reconstruction; steps 3 and 6 lack `dispatched` lines and --commit/dispatched_base undocumented), 5 minor.
Ruling (supersedes the merge-base ruling above): build.md drops `git merge-base`; `git diff master...HEAD` suffices; no new allowed-tool — why: three-dot diff already uses the merge base — cost if wrong: none.
Ruling: `post close` sends `patch: [{op: append, text: "\n\n**Closed.** <summary>\n"}]` instead of `description` — why: the spec's "summary description" wording, taken literally, destroys the reconstruction block the same spec guarantees; append preserves both — cost if wrong: the Linear MCP rejects `patch` on save_project (it is documented as supported).
Task 9: parked — em-dashes across orko/references and SKILL.md (34 in the two new files) — Ruling: branch-wide house style question, decided at final review, not per task.
Task 9: controller verified against the live mcp__linear__save_project schema (loaded this session): patch accepts op=append. Concern closed.
Task 9: fix round 1/5 (6 addressed, 0 open; commits bcc0856..10f5f4d)
Task 9: complete (commits 543a796..10f5f4d, review clean)
Task 10: implementer done 721007c. BASE 10f5f4d. SKILL.md 172 lines, description 1027 chars.
Ruling: the branch end-state stale-path grep excludes orko/scripts/fixtures/ and the test assertion string — why: fixtures are verbatim copies of the spec and plan, which name the old paths on purpose — cost if wrong: none.
Ruling: analysis mode has six ledger steps (1..6); SKILL.md's seven prose steps map Re-ground+Close onto `ledger 6 complete` — why: MODES["analysis"] was fixed at six in Task 2 and the spec's table has six — cost if wrong: none.
Task 10: note for Task 11: orko.py:706 cmd_preflight docstring still cites autonom review counts (Task 7 deferred minor) — Task 11 rewords it.
Task 10: review — 1 Important (step 0 cell orders preflight before branch creation; inherited from the spec's table), 4 minor.
Task 10: minor (deferred): allowed-tools carries four Linear tools nothing calls (get_issue, list_issues, list_issue_labels, save_comment) — decide at final review whether to trim
Task 10: note: spec's lifecycle table step 0 has the same ordering slip; correct the workshop spec at close-out.
Task 10: fix round 1/5 (3 addressed, 0 open; commits 721007c..c8d2903)
Task 10: complete (commits 10f5f4d..c8d2903, review clean)
Controller: workshop spec corrected (step 0 ordering; post close patch/append; post payload shape). Task 11 refreshes the fixture copies.
Task 11: implementer done 63d6119 (public) + 70ae15a (workshop). BASE c8d2903.
Task 11: complete (commits c8d2903..63d6119 + workshop 70ae15a, review clean)
Final review (fable): 1 Critical (save_issue_label payload carries `team`, not a schema param — controller confirmed against the live schema), 4 Important (label bootstrap per-run not per-team; SKILL.md analysis post project omits --boundaries; team-key resolution unverified until smoke; upgrades.md claims unshipped competing-implementation judge), 9 minor. Verdict: mergeable after fixes. Report: final-review-report.md.
Ruling: one fix wave covers C1, I1, I2, I4, triage 62, M3, M8; M2 (preamble consolidation), M4, M5, M6 go to the v1.0.1 backlog — why: they reshape nothing a conductor runs — cost if wrong: none.
Ruling: em-dashes in skill prose stay (M1) — why: oiler's rule governs replies to oiler; the library already uses them; a one-off strip creates inconsistency — cost if wrong: a later library-wide pass.
Ruling: I3 (team key "TEAM" resolving in addTeams/team) is the smoke engagement's first checkpoint — why: cannot be verified without a live Linear call — cost if wrong: init --team takes the team name instead and TEAM_RE relaxes.
