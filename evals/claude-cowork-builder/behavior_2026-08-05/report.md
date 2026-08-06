---
instrument: behavior
satisfies: [behavior]
skill_content_hash: 1507df243b129b8833b36c82f99a3c766a9be6bf5d9329277cc72bd30a3f47ed
repo_commit: 00570c4ce67b20106826f058754db8eb94ccf9ae
date: 2026-08-05
verdict: pass
---

# claude-cowork-builder — behavior eval vs v0.3.2 (2026-08-05)

One iteration, six runs: three prompts (new-plugin build, add-connector, audit+package) × two configs (candidate at `00570c4` vs the `claude-cowork-builder-v0.3.2` tag exported by `git archive`), executor model opus, one run per cell. Committed fixtures: `evals/claude-cowork-builder/fixtures/base-plugin` (add-connector input) and `fixtures/imperfect-plugin` + defects manifest (audit input/grading key).

**Content note:** the runs exercised the branch at `00570c4` (post drift-sweep, validator V1–V8, test relocation, fixtures). Later branch commits (behavior fix batch, description tightening, final-review fixes) postdate these runs, so this report's hash intentionally binds to `00570c4`'s content, not the release hash — a behavior instrument is development evidence and the structural gate does not consume it (plan Task 8 note).

## Scores

All 22 assertions passed in all six runs (deterministic rows script-checked: manifest path/shape, validator exits, archive-root listings, planted-defect greps; judgment rows graded from transcripts + outputs by an independent grader). Benchmark delta with_skill − old_skill: pass rate +0.00, time −44.6 s, tokens +1707. Every assertion was non-discriminating at one opus run per cell — both configs clear the mechanical floor.

## Where the versions actually differed (transcript evidence)

- **Validator regression fixed (V1 live):** on the audit fixture the v0.3.2 validator caught 3 of 4 planted script defects — its `~~` regex cannot match `~~CRM` in a description; the candidate's caught all 4.
- **Coupling contradiction removed (V2 live):** the old-config add-connector run independently hit "the bundled recipe fails the bundled validator" (body tokens failing item 10 under a private profile) and had to route around it; the candidate profile passes by design.
- **Install experience:** the candidate run wired the CRM through `userConfig` (install-time prompts, `sensitive: true` → keychain); the old run shipped hand-edit-`.mcp.json` + env-var instructions to a nontechnical audience. No assertion measured this; it is the largest real quality gap observed.

## Defects the runs surfaced in the candidate (all fixed on-branch before freeze)

Marketplace template missing strict-required top-level `description`; `userConfig.<KEY>.title` undocumented (hard schema requirement); audit item 2's `--strict` scope on self-marketplace layouts; multi-category `## With ~~category connected` guidance; packaging path for a plugin directory that is neither its own repo nor inside a container marketplace; false "`--strict` flags `color`" claim (two locations).

## Operator review

oiler reviewed all six runs in the eval viewer: one positive note (eval-0 output format and `## After` commands read clear and action-oriented), no change requests. Recorded instrument limitation: eval-prompt domains (recruiting, CRM) are outside the operator's subject-matter expertise; future sets should draw domains from the operator's own work areas.

## Artifacts

`eval_set.json` (the three prompts + assertions), `output-hashes.txt` (SHA-256 of all nine produced `.plugin` archives). Full workspaces (transcripts, grading JSON, benchmark, viewer) remain in the workshop's gitignored `.workspaces/cowork-builder-v0.4.0/iteration-1/`, prunable.
