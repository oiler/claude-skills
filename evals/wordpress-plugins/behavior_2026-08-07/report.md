---
instrument: behavior-comparison
satisfies: [behavior]
skill_content_hash: fde4e456855765f009d669691694dc6be0c58a9c3b44da9938028f26a3589ac9
repo_commit: 7c59dd1572a598ece204b11d1e66cd1575b11981
baseline_commit: 5c10ac8ee9da2948901b00d2ea6a943d4c8ee200
date: 2026-08-07
verdict: pass
---

# wordpress-plugins v0.2.0 — behavior comparison vs master snapshot

Candidate (branch `wordpress-plugins-v0.2.0` at the repo_commit above) versus a `git archive` snapshot of master (baseline_commit) — three eval cases, one run per arm per iteration, executor and grader on opus. Full workspaces (transcripts, workdirs, per-run grading) are ephemeral under the workshop's gitignored `.workspaces/wordpress-plugins-v0.2.0/`; `output_hashes.txt` in this bundle pins SHA-256 of every generated artifact, and `eval_set.json` is the exact prompt/assertion set that produced them.

## Results

| Eval | Candidate | Baseline |
|---|---|---|
| scaffold-and-run-harness | 4/4 | 0/4 |
| a7-broken-harness-audit | 2/2 | 2/2 |
| admin-settings-sortable-column | 4/5 (iteration-1) → **5/5 (iteration-2, after fix `7c59dd1`)** | 4/5 |

Aggregate (iteration-1): candidate 93.3%, baseline 60.0%. With the iteration-2 supersession of the admin-UI arm, the candidate passes every assertion in the set.

## Per-eval findings

**scaffold-and-run-harness — fully discriminating.** Candidate: scaffold → `composer install` → `composer lint` → `composer test` all exit 0 with zero intervention (PHPUnit 10.5, 2 tests green; VIPCS clean). Baseline: first `composer install` exits 1 (no `config.allow-plugins`), `composer lint` exits 1 with 4 errors in virgin scaffolder output (`flush_rewrite_rules()` ×2, two doc-style errors), `composer test` exits 1 ("Command \"test\" is not defined"), and no `tests/` exists despite `phpunit.xml.dist` referencing it. The grader re-ran both toolchains rather than trusting transcripts, and graded the baseline against pristine scaffolder source because the runner had mutated its workdir composer.json to get past the install failure.

**a7-broken-harness-audit — non-discriminating by construction, qualitative delta real.** Both arms found the broken harness on a pre-fix scaffold (fixture reproducible from baseline_commit's scaffolder: `scaffold_plugin.py --name "Broken Fixture"`). The candidate reported it as first-class checklist finding **A7** with all three sub-checks; the baseline, whose checklist has no such rule, filed the same facts out-of-taxonomy ("X2") and closed by proposing exactly the rule v0.2.0 institutionalizes. The assertion's "any equivalent finding counts" clause deliberately credits the baseline; a future eval set that wants this delta measurable should require an in-taxonomy ID.

**admin-settings-sortable-column — the eval's most valuable finding.** Iteration-1: both arms passed `'autoload' => false` inside `register_setting()` args, citing a hallucinated "WP 6.6+" argument (ground truth re-verified against developer.wordpress.org: `$args` supports type/label/description/sanitize_callback/show_in_rest/default; no autoload key in any WordPress version). The candidate did this despite a factually correct correction — placed in a VIP-Platform-only blockquote, which failed to steer a model whose prior says otherwise. Fix `7c59dd1` promoted the fact into the main Settings API flow as a named trap and added the missing `alloptions` section to `vip-performance.md`. Iteration-2 rerun: 5/5 — the generated `Settings.php` passes only real args, opts out of autoload via `add_option( …, '', false )` on activation, and states the correct rule in its own docblock. Lesson recorded: a correct fact in a scoped callout does not steer; placement in the main flow of the pattern being generated does.

## Analyst notes

- Single run per arm per iteration: no variance statistics; deltas rest on assertion evidence, not repetition.
- Candidate arms cost more tokens/time on the build evals (admin-UI: 494s/111k vs 283s/88k) and produced richer deliverables (PHPUnit tests alongside the feature code).
- Baseline eval-1 quality shows opus covers taxonomy gaps ad hoc; the value of A7 is consistency and auditability, not raw detection.

## Approval

Viewer generated from iteration-1 (`generate_review.py`, benchmark attached); results and the two pre-freeze fixes presented to oiler in-session 2026-08-07 and approved ("continue"), fixes applied as `7c59dd1` and re-verified by the iteration-2 rerun above.
