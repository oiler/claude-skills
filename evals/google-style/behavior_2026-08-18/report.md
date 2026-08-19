---
instrument: behavior
satisfies: [behavior]
skill_content_hash: 1cc583e5ea1c768f44878bdb6844231973a851934b1026556aa7509b1c2d9ec0
repo_commit: ab4eb6f2d23d9a1c3b1ba2be5494ac806176da6f
date: 2026-08-18
verdict: pass
---

# google-style behavior comparison, 2026-08-18

This instrument is not required for change class `new`. It exists because the skill's entire claim is output quality, and the trigger eval measures invocation rather than quality. Trigger success is never evidence that the prose improved.

The frontmatter binds this report to the frozen skill content so that a later `behavioral` change class can compare against it. A report written without a hash cannot be reused.

## What ran

Five documentation prompts, listed in `eval_set.json`, each run twice on `--model opus`:

- **With skill.** A byte-identical copy of the frozen skill sits at `./google-style/` in the arena, and the prompt carries a prefix that tells the model to read and follow `./google-style/SKILL.md`, loading the reference files the routing table points to. The copy keeps the subprocess away from the repository, so no run could write inside `google-style/`. The directory hash was verified before and after the ten runs and did not change.
- **Without skill.** The bare prompt in an empty arena.

Both arms share the rest of the setup: a fresh temporary project root per run, a working directory outside every repository, `--setting-sources project`, `CLAUDECODE` and `ANTHROPIC_API_KEY` stripped from the environment, and a tool allowlist of `Read`, `Write`, `Glob`, `Grep`, and `Bash(python3:*)`. Two probes confirmed the isolation: the arena loads no user `CLAUDE.md` and exposes no user skills, only the built-in ones. Both arms received the same closing instruction to write the document to `output.md`.

The ten outputs live in the workshop's gitignored `.workspaces/google-style-behavior/`. They are hashed in this report rather than committed.

## Mechanical scores

Counts come from `scripts/style_check.py <file> --json`, summed by severity.

| Prompt | Artifact | With skill | Without skill |
|---|---|---|---|
| 1 | README for a CSV-to-JSON CLI | 0 errors, 0 warnings | 0 errors, 5 warnings |
| 2 | Contributor guide setup section | 0 errors, 0 warnings | 2 errors, 14 warnings |
| 3 | Release notes for a logging library | 0 errors, 1 warning | 1 error, 13 warnings |
| 4 | Paginated REST endpoint reference | 0 errors, 0 warnings | 3 errors, 28 warnings |
| 5 | Troubleshooting page for a stale lockfile | 0 errors, 1 warning | 3 errors, 45 warnings |
| | **Total** | **0 errors, 2 warnings** | **9 errors, 105 warnings** |

The with-skill arm gates clean on every prompt. Its two warnings are both `passive`, which the checker reports and does not block, because the guide permits passive voice where it reads best.

The nine errors in the without-skill arm break down as four `latin`, all of them `e.g.`, two `oxford-comma`, two `headings` for title case, and one `please` in an instruction. The `via` hits fire at warning severity and are not among the nine errors. The 105 warnings concentrate in `contractions` (28), `em-dash` (32), and `passive` (31).

## Output hashes

| File | SHA-256 |
|---|---|
| `with-skill_p1.md` | `36e19757eace9166c9b3b9f1cee531cfb7e737373e8865a562f3eb3e16fcb817` |
| `with-skill_p2.md` | `0ff20a0b633e579cb25c4ca6b308d17b49fbede8b9defdcd43a193ff31858db5` |
| `with-skill_p3.md` | `aae45ec9a70fd07d3b7d0d9c51b97f62d702c26ea1beea93aff8a572687505cb` |
| `with-skill_p4.md` | `f67eddea586feee4f1fac26a1223ce4fa344c78d9cce699f66dc0a4bb41fc83b` |
| `with-skill_p5.md` | `35e158ea356202b4d40d41200ad1fb2ffc3507702f39c22cebe367e7f803a2bd` |
| `without-skill_p1.md` | `b7da59ed2643513c01b6a9b316dfb791ec204bb1460f86e069d824b146cce3ae` |
| `without-skill_p2.md` | `2e705cc2c3d22fad33d889acf631500d08eeace9e6f25d1274bb33f19e53d65d` |
| `without-skill_p3.md` | `0c3a959d33110662470878fe0bb6320b2107202f8b333e159fda847654f8c0d6` |
| `without-skill_p4.md` | `193a7665ffc7e8c466b1fe53f2eccc8109881ac81bbeebd8da755d10111f1a3a` |
| `without-skill_p5.md` | `e9b7bcb236206f47af36c361cc144654ec5e96788f85f12bce8c9d20eb7c2ff0` |

## The rubric read

The counter sees rules. This section records what a reader sees.

### Heading case and heading shape

Both arms mostly reach sentence case on their own, so the two `headings` errors understate the difference. The gap is in heading *shape*. The with-skill arm writes task headings that name the reader's goal: `Set the field delimiter`, `Format the output for a reader`, `Paginate through the result set`, `Fix a lockfile that lags the manifest`, and `Fix a build that fails only in continuous integration`. The without-skill arm writes noun labels for the same material: `Flags`, `Usage`, `Paginating`, `Causes and fixes`, and `Fast path`. Prompt 5 is the clearest case, where the without-skill title is `Troubleshooting: Build Fails with a Stale Lockfile` and the with-skill title is `Troubleshoot a stale lockfile`.

### Link text

Neither arm produced a `here` or a `read more` link, so the worst failure the rule targets did not appear. The difference is smaller and still real. The with-skill arm names destinations as noun phrases that stand alone: `[uv documentation]`, `[dependency resolution guide]`, and ``[`forge lock` command reference]``. The without-skill arm links a bare term inside a running sentence, as in `This project uses [uv](https://docs.astral.sh/uv/) to manage Python versions`, which reads correctly in place and carries nothing when a screen reader lists the links on the page. The without-skill arm also produced fewer links overall: two across five documents against three in the with-skill arm.

### Conditions before instructions

The checker flagged one `condition-order` warning in each of two without-skill outputs, and none in the with-skill arm. The flagged lines show the pattern: `Use compact output (the default) when piping into another tool` and `Stop when page.has_more is false`. The with-skill arm leads with the condition instead, as in `If the input file separates fields with a character other than a comma, pass that character to the --delimiter flag` and `If the mismatch persists, check whether the maintainer republished the version`. The counter catches only the `when` construction, so the rubric read matters more here than the count does.

### Timeless phrasing

One pre-announcement appeared, in the without-skill release notes: `The --log-format CLI flag is deprecated and will be removed in 3.0`. The with-skill release notes state the deprecation and the replacement without naming a future version. No output in either arm used `currently` or `at this time`.

### Directional language

This is the finding the counter cannot reach at all, because no rule covers it. The without-skill arm used directional references four times: `Reserved keys are emitted first in the order above`, `note the timestamp format fix above`, `Prefer the lock-only / no-update variants shown above`, and `go to "Environment-specific causes" below`. The with-skill arm used none. It names the section or the command instead.

### Structure and scope

The with-skill arm produced shorter, tighter documents on the two prompts with the most room to sprawl: 142 lines against 250 for the REST reference, and 169 lines against 357 for the troubleshooting page. The without-skill troubleshooting page answered a question nobody asked, covering npm, pnpm, Yarn, Cargo, Poetry, uv, Bundler, and Go for a prompt that named one build tool. The with-skill page stayed with one tool and organized around symptom, confirmation, and fix.

One more structural difference falls outside the checker: the with-skill arm never hard-wrapped a paragraph, while two without-skill outputs did, at 97 and 137 columns.

### Where the skill did not win

`passive` is the only rule on which the with-skill arm is not clean, at two warnings across the set. The same two prompts without the skill carry 8 and 10 passive warnings, so the with-skill arm wins that rule too. The without-skill README scored zero errors, matching the with-skill README on the gating rules. Prompt 1 is the smallest artifact in the set, which suggests the delta grows with document size rather than holding flat.

## The honest limitation

The checker scoring both arms is the same checker the skill tells one arm to run, so the mechanical delta is partly circular. The rubric read is what makes the comparison worth anything.

The circularity is concrete rather than theoretical: the with-skill runs ran `style_check.py` and fixed what it reported before finishing, so a score of zero errors partly measures whether the loop ran, not whether the prose is better. Read the score table as evidence that the skill's loop works end to end, and read the rubric section as the evidence about quality. Two further limits apply. Each cell is a single run, so nothing here separates the skill's effect from run-to-run variance. The rubric read was performed by the same session that ran the comparison, which is a weaker arrangement than the one the clean-room smoke test used.

A third limit governs reuse. The with-skill arm is a skill-read-on-instruction arrangement, where a prompt prefix points the model at `SKILL.md`, not a natively triggered skill. A later `behavioral` comparison has to reproduce the same arrangement, or the delta between the two reports measures the invocation path rather than the content change.

## Verdict

`pass`. The comparison ran on all ten cells, both arms scored, and the result is reported as measured, including the rows where the skill did not win. The verdict records that the instrument ran honestly, not that the skill won every row.
