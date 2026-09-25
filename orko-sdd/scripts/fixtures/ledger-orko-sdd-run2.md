# SDD ledger — plan: /nonexistent/textkit/docs/plan.md

No spec named by the plan; rulings are provisional.

## Preflight scan
| Tasks | Shared file/interface | Produces vs consumes | Finding |
|---|---|---|---|
| 1 ↔ 2 | `textkit.slug.slugify` | T1 produces `slugify(text) -> str` joining with `-`; T2 consumes it and swaps `-` for `--sep` | consistent |
| 2 ↔ 3 | `textkit/__init__.py` | T2 exports `slugify`, `main`; T3 adds no export | consistent |
| 3 ↔ 4 | `textkit/titles.py`, `tests/test_titles.py` | T3 produces `fetch_title`; T4 wraps it in `cached_title` | T4 depends on T3 |
| 1 | self | tests ("Hello World"→"hello-world", "Hi, there!"→"hi-there") match the given regex impl | consistent |
| 2 | self | prose spec: main(argv)->int, stdin lines, skip blanks, --sep; listed tests match | consistent |
| 3 | self vs CLAUDE.md | adds `requests`, `beautifulsoup4` to pyproject dependencies | CONFLICT with CLAUDE.md:3 (stdlib only, never add third-party deps) |
| 4 | self | cached_title via lru_cache(128); test counts fetch_title calls | consistent; builds on T3 |

Task 3: skipped — evergreen conflict — CLAUDE.md:3 — plan requires adding `requests` and `beautifulsoup4` to pyproject.toml dependencies; CLAUDE.md forbids any third-party dependency
Task 4: skipped — depends on Task 3
Follow-up: Tasks 3-4 (URL titles, title cache) not built — plan requires requests/beautifulsoup4, which CLAUDE.md:3 forbids. Decide: rewrite Task 3 on stdlib (urllib.request + html.parser) or amend CLAUDE.md.
Ruling: Task 2 `--sep` replaces every `-` in slugify's output with the given string, and `main` returns 0 — the plan's only conventional reading — cost if wrong: a one-line change in cli.py
Task 1: dispatch implementer-scoped sonnet/high — Plan text contains the complete test and implementation code
Task 1: dispatch reviewer opus/low — Per-task review of a two-file transcription diff
Task 1: minor (deferred): slug.py:5 drops non-ASCII letters ("Café"→"caf") — plan-specified regex; unicodedata normalization is a stdlib option
Task 1: minor (deferred): test_slug.py lacks edge cases (empty input, all punctuation, leading/trailing separators); test_strips_punctuation name undersells coverage
Task 1: complete (commits de45212..cc6f101, review clean)
Task 2: dispatch implementer-gap opus/low — Prose-specified small CLI with one conventional reading; --sep ruling recorded in ledger
Task 2: dispatch reviewer opus/low — Per-task review of a small CLI diff
Task 2: minor (deferred): cli.py:12-13 an all-punctuation line (e.g. "!!!") prints an empty line; filter on the slug, not the raw line
Task 2: minor (deferred): cli.py:9 --sep accepts any string incl. "" (consistent with the ruling; brief said <char>)
Task 2: minor (deferred): test_cli.py:12 helper uses `argv or []`; cosmetic
Task 2: complete (commits cc6f101..379f2f5, review clean)
Task final: dispatch final-reviewer opus/high — Ordinary whole-branch review of a small two-task branch
Ruling: Final #1 (filter not runnable from a shell; `python3 -m textkit.cli` prints nothing) — fix by adding textkit/__main__.py so `python3 -m textkit` runs main, plus one subprocess test; no [project.scripts] entry — the plan's goal names a command-line filter — cost if wrong: one small file to remove
Ruling: Final #2 (slug.py drops non-ASCII letters, "Café"→"caf") — fix with stdlib unicodedata NFKD + ASCII fold before the regex, one test — plan fixed the regex but is silent on accented input, and a user expects "cafe" — cost if wrong: revert one line and one test
Ruling: Final #3 (all-punctuation line prints a blank line) — fix: print only non-empty slugs, one test — consistent with the rule that blank lines are skipped — cost if wrong: a two-line revert
Ruling: Final #6 (no .gitignore for __pycache__) — fix: add .gitignore with `__pycache__/` — cost if wrong: none
Ruling: Final #7 (--sep accepts any string) — keep behavior per the Task 2 ruling; fixer rewords help text to "string" — cost if wrong: none
Task final: parked — #4 edge-case test gaps (empty/all-punctuation slugify, separator runs, multi-hyphen --sep) — Ruling: tests match the plan and cover each stated behavior; fixes #2/#3 add their own tests — cost if wrong: a later regression in untested edges goes unnoticed
Task final: parked — #5 non-UTF-8 stdin raises UnicodeDecodeError traceback — Ruling: acceptable for a text filter; no stated requirement for byte-tolerant input — cost if wrong: an uglier error on bad input
Task final: dispatch final-fixer opus/medium — Single final-review fix wave: __main__.py, unicode fold, skip empty slugs, .gitignore, help text
Task final: dispatch re-reviewer opus/low — Scoped re-review of the final fix wave
Task final: parked — test_cli.py:33 subprocess.run has no timeout — Ruling: child reads a closed stdin pipe and exits; a hang needs a new bug; no second fix wave — cost if wrong: a hung test run instead of a failure
Task final: parked — `python3 -m textkit --help` shows prog as `__main__.py` (cli.py:8) — Ruling: cosmetic usage text; `prog="textkit"` is a one-line follow-up — cost if wrong: a confusing usage line
Task final: complete (commits 379f2f5..587a753, 4 parked)
Verify: python3 -m unittest discover -s tests -q — exit 0 — OK
