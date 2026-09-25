# SDD ledger — plan: /nonexistent/textkit/docs/plan.md
No spec named by the plan; rulings are provisional against the plan and evergreen docs (CLAUDE.md).

## Preflight scan
| Rows | Produces / consumes | Finding |
|---|---|---|
| Task 1 (self) | tests vs code | Consistent: both test cases pass under the given regex. |
| Task 2 (self) | tests vs prose | Consistent: `--sep _` on `Hello World` = slugify then replace `-`. |
| Task 3 (self) | deps vs CLAUDE.md | Conflict: requires `requests` + `beautifulsoup4` in pyproject.toml; CLAUDE.md:3 forbids third-party deps. |
| Task 4 (self) | tests vs code | Consistent internally; depends on Task 3's `fetch_title`. |
| Task 1 ↔ Task 2 | T1 produces `slugify(text) -> str`; T2 imports it and re-exports it from `textkit/__init__.py` | Compatible. |
| Task 3 ↔ Task 4 | T3 produces `fetch_title` in `textkit/titles.py`; T4 wraps it in same file | Compatible, but inherits T3's conflict. |

Task 3: skipped — evergreen conflict — CLAUDE.md:3 — plan requires adding `requests` and `beautifulsoup4` to pyproject.toml dependencies; CLAUDE.md says standard library only, never add third-party dependencies.
Task 4: skipped — depends on Task 3
Follow-up: Tasks 3-4 (URL titles + cache) skipped for CLAUDE.md:3 stdlib-only conflict. Decide: rewrite Task 3 on stdlib (`urllib.request` + `html.parser`), or amend CLAUDE.md to allow those deps.
Ruling: Task 2 `--sep` replaces every `-` in each slug via `str.replace`, accepting any string without length validation — the only hyphens in a slug are separators, and the plan's `<char>` is descriptive — cost if wrong: add a one-char check.
Ruling: Task 2 "blank lines" means lines empty after `strip()`; a non-blank line whose slug is empty (e.g. `!!!`) still prints an empty line, per the plan's literal "slug of each non-empty line" — cost if wrong: one extra condition.
Ruling: Task 2 `main` returns 0 and parses args with `argparse` (stdlib) — conventional CLI shape — cost if wrong: trivial.
Task 1: dispatch implementer-scoped sonnet/high — plan text contains complete code for slugify and tests
Task 1: dispatch reviewer opus/low — per-task review of slugify diff
Task 1: minor (deferred): slugify drops non-ASCII letters (`Café` -> `caf`), per plan code
Task 1: minor (deferred): no tests for empty / punctuation-only / repeated-separator input
Task 1: complete (commits d0b0b8f..1faf472, review clean)
Task 2: dispatch implementer-gap opus/low — small prose CLI task, one conventional reading; gaps ruled in ledger
Ruling: Task 2 ships no `__main__` block or console-script entry point — the plan asks only for `main(argv)` — cost if wrong: add `if __name__ == "__main__"` or a `[project.scripts]` entry.
Task 2: dispatch reviewer opus/low — per-task review of CLI diff
Task 2: minor (deferred): no test pins the empty-slug ruling (`!!!` prints an empty line)
Task 2: minor (deferred): `--sep` tested only on a single-hyphen slug; no multi-word case
Task 2: minor (deferred): `--sep` help text says "separator" though any string is accepted
Task 2: minor (deferred): `__init__.py` imports `cli` before `slug`; safe today, fragile if `slug.py` imports from `textkit`
Task 2: complete (commits 1faf472..2f270cf, review clean)
Task final: dispatch final-reviewer opus/high — ordinary whole-branch review, small branch
Ruling: Final review reverses the Task 2 no-entry-point ruling — add `textkit/__main__.py` so `python3 -m textkit` runs the filter; a "command-line filter" users can't invoke fails reasonable expectation — cost if wrong: one file to delete.
Ruling: Final review reverses the Task 2 empty-slug ruling — skip any line whose slug is empty (covers blank and punctuation-only lines), so output is one real slug per line for pipelines — cost if wrong: one condition to restore.
Ruling: Final fix adds a `.gitignore` with `__pycache__/` and `*.pyc` — test runs leave untracked bytecode — cost if wrong: none.
Task final: dispatch final-fixer opus/medium — single final-review fix wave: __main__, empty-slug skip, gitignore, tests
Task final: dispatch re-reviewer opus/low — scoped re-review of final fix wave
Task final: parked — slugify drops or truncates non-ASCII letters (`Café` -> `caf`, CJK -> empty) — Ruling: the plan's Task 1 code prescribes this regex, and choosing NFKD vs transliteration is a product call; defer to a follow-up task — cost if wrong: accented input yields truncated slugs until fixed.
Task final: parked — no BrokenPipeError / UnicodeDecodeError handling in the CLI — Ruling: pipeline rough edge, not a correctness bug; outside the plan's scope — cost if wrong: traceback on `| head` or badly encoded input.
Task final: parked — `test_runs_as_module` calls `subprocess.run` with no timeout — Ruling: real but minor; the child reads finite stdin and exits — cost if wrong: a hang would stall the suite.
Task final: parked — `--sep ""` merges words (`A--B` -> `ab`) — Ruling: consistent with the any-string `--sep` ruling; intended — cost if wrong: add validation.
Follow-up: Consider a follow-up task for Unicode-aware slugify (stdlib `unicodedata` NFKD) and BrokenPipeError handling in `textkit/__main__.py`.
Task final: complete (commits 2f270cf..9cd7deb, 4 parked)
Verify: python3 -m unittest discover -s tests -q — exit 0 — OK
