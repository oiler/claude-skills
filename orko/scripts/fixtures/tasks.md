# orko v2 Build Engagement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship orko v1.0.0: one skill with an analysis and a build engagement, backed by `scripts/orko.py` (autonom's script renamed and extended), with Linear as the record and the run directory as scratch.

**Architecture:** `autonom/scripts/autonom.py` moves to `orko/scripts/orko.py` and gains a mode, a team, Linear ID storage in the ledger, `post` payload emitters, a `preflight`, and five `prompt` kinds emitted from charter files in `orko/references/`. Reviewer seats become report-only orko seats. `SKILL.md` grows a build lifecycle section and routes detail to `references/build.md` and `references/linear.md`. `autonom/` becomes a deprecation stub.

**Tech Stack:** Python 3.12 via `uv` (PEP 723 script, stdlib only), pytest, Claude Code skills, Linear MCP tools.

**Spec:** `/Users/jrf1039/files/projects/001-claude-skills-creator/docs/superpowers/specs/2026-09-04-orko-v2-build-design.md`

## Global Constraints

- Repo: `/Users/jrf1039/files/repo/claude-skills/`. Work on branch `feat/orko-v2` off `master`. `main` is not a valid base.
- Every command below runs with cwd `/Users/jrf1039/files/repo/claude-skills/` unless the step says otherwise.
- Tests run with `uv run --with pytest pytest orko/scripts/test_orko.py -q`. The suite must be green at the end of every task from Task 2 onward. Task 1 leaves the header-format tests red by design; Task 2 turns them green.
- `orko.py` stays stdlib-only (`dependencies = []` in the PEP 723 block) and keeps exit codes `0` success, `1` validation findings, `2` usage or IO error.
- Run directory is `.orko/<slug>/` under the target repo root. No path under `docs/sessions/`, `docs/superpowers/`, or `.superpowers/` may appear in shipped orko files after Task 1.
- Linear state names in any prose file (`SKILL.md`, `references/*.md`, this plan) go in backticks, because the validators' placeholder scan is case-insensitive and matches `Todo`.
- The word `Todo` and the state list come from the JRF team: `Backlog`, `Todo`, `In Progress`, `In Review`, `Done`, `Canceled`, `Duplicate`.
- `SKILL.md` stays under 300 lines. Frontmatter `version: 1.0.0`, `disable-model-invocation: true`.
- Commit after every task with the message given in the task. Do not commit `__pycache__/` or `.pytest_cache/` (both already gitignored).
- Prose in skill files: neutral technical voice, no emoji, never hard-wrapped.
- Never use `$(...)` in commands shown to the conductor in `SKILL.md` or `references/build.md`; prefix matching in `allowed-tools` cannot see through command substitution.

---

### Task 1: Move the script into orko and rebase its paths

**Files:**
- Create: `orko/scripts/orko.py` (from `autonom/scripts/autonom.py`)
- Create: `orko/scripts/test_orko.py` (from `autonom/scripts/test_autonom.py`)
- Modify: `orko/scripts/orko.py` functions `compute_paths`, `_run_dir_root`, `ensure_gitignored`, `_header`, `_parse_header`, and every `"autonom:"` message prefix

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Produces: `compute_paths(root, slug, date) -> dict` with keys `slug`, `date`, `root`, `run_dir`, `ledger`, `escalations`, `spec`, `plan`, `brief`, `synthesis`, `findings_dir`, `context_dir`, `unposted_dir`. `spec` is `<run_dir>/spec.md`, `plan` is `<run_dir>/plan.md`.
- Produces: `_run_dir_root(root) -> root / ".orko"`.

- [ ] **Step 1: Move the files with git so history follows**

```bash
git checkout -b feat/orko-v2 master
mkdir -p orko/scripts
git mv autonom/scripts/autonom.py orko/scripts/orko.py
git mv autonom/scripts/test_autonom.py orko/scripts/test_orko.py
sed -i '' 's/import autonom/import orko/; s/autonom\./orko./g' orko/scripts/test_orko.py
```

- [ ] **Step 2: Write the failing tests for the new paths**

Replace the body of `class TestComputePaths` in `orko/scripts/test_orko.py` with:

```python
class TestComputePaths:
    def test_builds_every_path_under_the_run_dir(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        run_dir = tmp_path / ".orko/demo"
        assert paths["run_dir"] == str(run_dir)
        assert paths["ledger"] == str(run_dir / "progress.md")
        assert paths["escalations"] == str(run_dir / "escalations.md")
        assert paths["spec"] == str(run_dir / "spec.md")
        assert paths["plan"] == str(run_dir / "plan.md")
        assert paths["brief"] == str(run_dir / "brief.md")
        assert paths["synthesis"] == str(run_dir / "synthesis.md")
        assert paths["findings_dir"] == str(run_dir / "findings")
        assert paths["context_dir"] == str(run_dir / "context")
        assert paths["unposted_dir"] == str(run_dir / "unposted")

    def test_no_shipped_path_points_outside_the_run_dir(self, tmp_path):
        paths = orko.compute_paths(tmp_path, "demo", "2026-09-04")
        for key, value in paths.items():
            if key in {"slug", "date", "root"}:
                continue
            assert value.startswith(str(tmp_path / ".orko/demo")), key
```

Then, across the test file, replace every `.superpowers/autonom/` with `.orko/` and every `.superpowers/` gitignore assertion with `.orko/`:

```bash
sed -i '' 's#\.superpowers/autonom/#.orko/#g; s#"\.superpowers/"#".orko/"#g; s#\.superpowers/\\n#.orko/\\n#g' orko/scripts/test_orko.py
```

Tests that assert the old `docs/superpowers/specs/<date>-<slug>-design.md` path (in `TestPrompt` and `TestInit`) change to `.orko/<slug>/spec.md` and `.orko/<slug>/plan.md`. Edit each assertion by hand; there are four in `TestPrompt` and none elsewhere.

- [ ] **Step 3: Run the suite to see the path tests fail**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: FAIL in `TestComputePaths` and the `.orko/` assertions; other tests may also fail on the old header text, which Task 2 fixes.

- [ ] **Step 4: Rebase the paths in the script**

In `orko/scripts/orko.py` replace `compute_paths` and `_run_dir_root`:

```python
def compute_paths(root: Path, slug: str, date: str) -> dict[str, str]:
    """Every path a run touches, derived from root and slug alone.

    The run directory is scratch and Linear is the record, so artifacts need
    no date in their filename; stability for the validators and seats is all
    that matters.
    """
    run_dir = root / ".orko" / slug
    return {
        "slug": slug,
        "date": date,
        "root": str(root),
        "run_dir": str(run_dir),
        "ledger": str(run_dir / "progress.md"),
        "escalations": str(run_dir / "escalations.md"),
        "spec": str(run_dir / "spec.md"),
        "plan": str(run_dir / "plan.md"),
        "brief": str(run_dir / "brief.md"),
        "synthesis": str(run_dir / "synthesis.md"),
        "findings_dir": str(run_dir / "findings"),
        "context_dir": str(run_dir / "context"),
        "unposted_dir": str(run_dir / "unposted"),
    }
```

```python
def _run_dir_root(root: Path) -> Path:
    return root / ".orko"
```

Replace `ensure_gitignored` so the line it appends is `.orko/`:

```python
def ensure_gitignored(root: Path) -> None:
    """Append `.orko/` to the target's .gitignore once. The run directory is
    scratch; a trail that commits by accident is the failure this prevents."""
    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if any(line.strip() == ".orko/" for line in existing.splitlines()):
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    with gitignore.open("a", encoding="utf-8") as handle:
        handle.write(f"{prefix}.orko/\n")
```

Rename every `"autonom:"` stderr prefix to `"orko:"`, the argparse `prog` to `"orko"`, and the module docstring's usage block to `orko.py`. Delete `superpowers_present` and the `--plugin-cache` argument and its check in `cmd_init`; orko already requires superpowers through `SKILL.md`, and Task 7's `preflight` takes over the check in code. Delete `class TestDependencyCheck` from the test file.

```bash
sed -i '' 's/"autonom: /"orko: /g; s/f"autonom: /f"orko: /g; s/prog="autonom"/prog="orko"/' orko/scripts/orko.py
```

- [ ] **Step 5: Run the suite**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: `TestComputePaths` PASS; `TestInit` and `TestLedgerAndStatus` still fail on the header format (Task 2). Confirm no failure mentions `.superpowers`.

- [ ] **Step 6: Commit**

```bash
git add orko/scripts autonom/scripts
git commit -m "refactor(orko): move autonom.py to orko/scripts/orko.py and rebase the run directory to .orko/"
```

---

### Task 2: Modes, team, and per-mode steps

**Files:**
- Modify: `orko/scripts/orko.py` (`STEPS`, `_header`, `_parse_header`, `cmd_init`, `cmd_ledger`, `_next_step`, `_describe_run`, `build_parser`)
- Modify: `orko/scripts/test_orko.py` (`TestInit`, `TestLedgerAndStatus`, new `TestModes`)

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Consumes: `compute_paths`, `_run_dir_root` from Task 1.
- Produces: `MODES: dict[str, dict[int, str]]`; ledger header `# orko run — mode: <mode> — team: <KEY> — topic: <topic> — slug: <slug> — date: <date>`; `_parse_header` returns keys `mode`, `team`, `topic`, `slug`, `date`; `_next_step(ledger, mode)`; `_describe_run` output gains `mode`, `team`.

- [ ] **Step 1: Write the failing tests**

In `orko/scripts/test_orko.py`, change every `_init` helper and direct `init` call to the new signature. The pattern is `["init", "build", "Demo Topic", "--team", "JRF", "--root", str(tmp_path), "--date", "2026-09-04"]`. Replace the header assertion in `TestInit.test_creates_run_dir_and_ledger_header_and_prints_json` with:

```python
        assert payload["mode"] == "build"
        assert payload["team"] == "JRF"
        assert payload["next_step"] == 0
        ledger = tmp_path / ".orko/demo-topic/progress.md"
        assert ledger.read_text().splitlines()[0] == (
            "# orko run — mode: build — team: JRF — topic: Demo Topic "
            "— slug: demo-topic — date: 2026-09-04"
        )
```

Every ledger step number in the existing tests shifts: autonom's `6, 7, 8, 9` become build `1, 2, 3, 4`. Update them. Then add:

```python
class TestModes:
    def _init(self, tmp_path, capsys, mode="build"):
        orko.main(["init", mode, "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        capsys.readouterr()

    def test_init_requires_a_team(self, tmp_path):
        with pytest.raises(SystemExit) as raised:
            orko.main(["init", "build", "Demo Topic", "--root", str(tmp_path)])
        assert raised.value.code == 2

    def test_init_rejects_a_lowercase_team_key(self, tmp_path, capsys):
        rc = orko.main(["init", "build", "Demo Topic", "--team", "jrf",
                        "--root", str(tmp_path)])
        assert rc == 2
        assert "team key" in capsys.readouterr().err

    def test_analysis_run_starts_at_step_one(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        run = json.loads(capsys.readouterr().out)
        assert run["mode"] == "analysis"
        assert run["next_step"] == 1
        assert run["next_step_name"] == "open"

    def test_build_run_starts_at_intake(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        run = json.loads(capsys.readouterr().out)
        assert run["next_step"] == 0
        assert run["next_step_name"] == "intake"

    def test_ledger_rejects_a_step_outside_the_runs_mode(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["ledger", "7", "complete", "--slug", "demo-topic",
                        "--root", str(tmp_path)])
        assert rc == 2
        assert "analysis" in capsys.readouterr().err

    def test_ledger_rejects_step_zero_on_analysis(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["ledger", "0", "complete", "--slug", "demo-topic",
                        "--root", str(tmp_path)])
        assert rc == 2

    def test_reinit_with_a_different_mode_is_an_error(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["init", "analysis", "Demo Topic", "--team", "JRF",
                        "--root", str(tmp_path), "--date", "2026-09-04"])
        assert rc == 2
        assert "mode" in capsys.readouterr().err

    def test_run_is_done_after_the_last_step_of_its_mode(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        for step in range(1, 7):
            orko.main(["ledger", str(step), "complete", "--slug", "demo-topic",
                       "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["next_step"] is None
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: FAIL on `init` argument parsing and header text.

- [ ] **Step 3: Implement modes and team**

Replace `STEPS` in `orko/scripts/orko.py`:

```python
# Steps per engagement type. Only `complete` advances a run; the names are what
# `status` prints so a resumed conductor knows where it is without the table.
MODES: dict[str, dict[int, str]] = {
    "analysis": {
        1: "open", 2: "propose", 3: "dispatch",
        4: "verify", 5: "synthesize", 6: "close",
    },
    "build": {
        0: "intake", 1: "spec", 2: "spec review", 3: "plan",
        4: "plan review", 5: "execute", 6: "code review", 7: "close",
    },
}
TEAM_RE = re.compile(r"^[A-Z][A-Z0-9]{0,9}$")
```

Replace `_header` and `_parse_header`:

```python
def _header(mode: str, team: str, topic: str, slug: str, date: str) -> str:
    return (f"# orko run — mode: {mode} — team: {team} — topic: {topic} "
            f"— slug: {slug} — date: {date}")


HEADER_LINE_RE = re.compile(
    r"# orko run — mode: (?P<mode>analysis|build) — team: (?P<team>[A-Z0-9]+) "
    r"— topic: (?P<topic>.*) — slug: (?P<slug>[a-z0-9-]+) "
    r"— date: (?P<date>\d{4}-\d{2}-\d{2})$"
)


def _parse_header(ledger: Path) -> dict[str, str] | None:
    """Read mode/team/topic/slug/date out of a ledger's first line, or None if
    unreadable. Empty is unreadable, not a crash: callers turn None into exit 2."""
    if not ledger.exists():
        return None
    lines = ledger.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None
    match = HEADER_LINE_RE.match(lines[0])
    return match.groupdict() if match else None
```

Replace `_next_step` and update `_describe_run`:

```python
def _next_step(ledger: Path, mode: str) -> int | None:
    """Lowest step of `mode` not recorded complete; None when the run is done."""
    done = {
        int(entry["step"])
        for entry in _ledger_entries(ledger)
        if entry["status"] == "complete"
    }
    remaining = [step for step in sorted(MODES[mode]) if step not in done]
    return remaining[0] if remaining else None


def _describe_run(root: Path, slug: str) -> dict | None:
    ledger = _run_dir_root(root) / slug / "progress.md"
    header = _parse_header(ledger)
    if header is None:
        return None
    entries = _ledger_entries(ledger)
    next_step = _next_step(ledger, header["mode"])
    steps = MODES[header["mode"]]
    return dict(
        compute_paths(root, slug, header["date"]),
        mode=header["mode"],
        team=header["team"],
        topic=header["topic"],
        next_step=next_step,
        next_step_name=steps.get(next_step) if next_step is not None else None,
        last_status=entries[-1]["status"] if entries else None,
        dispatched_base=_dispatched_base(entries, next_step),
    )
```

Note `next_step is not None`: build starts at step `0`, which is falsy, and autonom's `if next_step` would report the intake step as done.

Rewrite `cmd_init`:

```python
def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else find_repo_root(Path.cwd())
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    if not TEAM_RE.match(args.team):
        print(f"orko: team key {args.team!r} must be the Linear team key, "
              "uppercase letters and digits (for example JRF)", file=sys.stderr)
        return 2
    if CONTROL_RE.search(args.topic):
        print("orko: topic contains a newline or control character; the ledger "
              "header is a single line and could not be read back", file=sys.stderr)
        return 2
    date = args.date or _dt.date.today().isoformat()
    try:
        slug = slugify(args.topic)
    except ValueError as error:
        print(f"orko: {error}", file=sys.stderr)
        return 2
    paths = compute_paths(root, slug, date)
    ledger = Path(paths["ledger"])
    ensure_gitignored(root)

    resumed = False
    if ledger.exists():
        existing = _parse_header(ledger)
        if existing is None:
            print(f"orko: unreadable ledger header in {ledger}", file=sys.stderr)
            return 2
        if existing["topic"] != args.topic:
            print(f"orko: topic {args.topic!r} collides with the existing run "
                  f"{existing['topic']!r} (both slugify to {slug!r}). Choose a "
                  "distinct topic or resume the existing run.", file=sys.stderr)
            return 2
        if existing["mode"] != args.mode:
            print(f"orko: run {slug!r} is a {existing['mode']} engagement; "
                  f"cannot resume it as {args.mode}. A run's mode is fixed at init.",
                  file=sys.stderr)
            return 2
        resumed = True
        paths = compute_paths(root, slug, existing["date"])
    else:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        for key in ("findings_dir", "context_dir"):
            Path(paths[key]).mkdir(parents=True, exist_ok=True)
        ledger.write_text(
            _header(args.mode, args.team, args.topic, slug, date) + "\n",
            encoding="utf-8",
        )

    header = _parse_header(ledger)
    payload = dict(paths, mode=header["mode"], team=header["team"],
                   topic=args.topic, resumed=resumed,
                   next_step=_next_step(ledger, header["mode"]))
    print(json.dumps(payload, indent=2))
    return 0
```

Rewrite `cmd_ledger` to check the step against the run's mode:

```python
def cmd_ledger(args: argparse.Namespace) -> int:
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    ledger = _run_dir_root(root) / args.slug / "progress.md"
    header = _parse_header(ledger)
    if header is None:
        print(f"orko: no run named {args.slug!r}; run init first", file=sys.stderr)
        return 2
    if args.step not in MODES[header["mode"]]:
        valid = ", ".join(str(step) for step in sorted(MODES[header["mode"]]))
        print(f"orko: step {args.step} is not a step of a {header['mode']} run "
              f"(valid: {valid})", file=sys.stderr)
        return 2
    line = f"step {args.step} {args.status}"
    if args.commit:
        line += f" commit={args.commit}"
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return 0
```

In `build_parser`, change `init` and `ledger`:

```python
    p_init = sub.add_parser("init", help="start or resume a run")
    p_init.add_argument("mode", choices=sorted(MODES))
    p_init.add_argument("topic")
    p_init.add_argument("--team", required=True, help="Linear team key, e.g. JRF")
    p_init.add_argument("--root", help="repo root (default: git toplevel of cwd)")
    p_init.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p_init.set_defaults(func=cmd_init)

    p_ledger = sub.add_parser("ledger", help="append a step record")
    p_ledger.add_argument("step", type=int)
    p_ledger.add_argument(
        "status", choices=["dispatched", "complete", "failed", "escalated"])
    p_ledger.add_argument("--slug", required=True)
    p_ledger.add_argument("--root")
    p_ledger.add_argument("--commit")
    p_ledger.set_defaults(func=cmd_ledger)
```

`cmd_prompt` and `cmd_escalations` call `_parse_header` or `_describe_run` and need no change beyond what Task 6 does to `cmd_prompt`.

- [ ] **Step 4: Run the suite**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: PASS except `TestPrompt`, which Task 6 rewrites. If `TestPrompt` blocks the run, mark those tests `@pytest.mark.xfail(reason="rewritten in Task 6", strict=True)` for now.

- [ ] **Step 5: Commit**

```bash
git add orko/scripts
git commit -m "feat(orko): init takes a mode and a Linear team; ledger steps are per mode"
```

---

### Task 3: Linear IDs in the ledger

**Files:**
- Modify: `orko/scripts/orko.py` (new `LINEAR_LINE_RE`, `_linear_ids`, `cmd_linear`; `_describe_run`, `build_parser`)
- Modify: `orko/scripts/test_orko.py` (new `TestLinearIds`)

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Produces: ledger lines `linear <key> <id>` where key is one of `project`, `spec_doc`, `plan_doc`, `brief_doc`, `synthesis_doc`, `blocked_label`; `_linear_ids(ledger) -> dict[str, str]` (last write wins); `status` output gains `"linear": {...}`; CLI `linear set <key> <id> --slug S` and `linear get --slug S` (prints JSON).

- [ ] **Step 1: Write the failing tests**

```python
class TestLinearIds:
    def _init(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        capsys.readouterr()

    def test_set_then_get_round_trips(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        assert orko.main(["linear", "set", "project", "proj_123",
                          "--slug", "demo-topic", "--root", str(tmp_path)]) == 0
        assert orko.main(["linear", "get", "--slug", "demo-topic",
                          "--root", str(tmp_path)]) == 0
        assert json.loads(capsys.readouterr().out) == {"project": "proj_123"}

    def test_set_appends_a_ledger_line(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["linear", "set", "spec_doc", "doc_9", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        lines = (tmp_path / ".orko/demo-topic/progress.md").read_text().splitlines()
        assert lines[-1] == "linear spec_doc doc_9"

    def test_last_write_wins(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        for value in ("a", "b"):
            orko.main(["linear", "set", "project", value, "--slug", "demo-topic",
                       "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["linear", "get", "--slug", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["project"] == "b"

    def test_unknown_key_is_a_usage_error(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        with pytest.raises(SystemExit) as raised:
            orko.main(["linear", "set", "wiki", "x", "--slug", "demo-topic",
                       "--root", str(tmp_path)])
        assert raised.value.code == 2

    def test_status_reports_the_ids(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["linear", "set", "project", "proj_123", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["linear"] == {"project": "proj_123"}

    def test_linear_lines_do_not_disturb_step_parsing(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["ledger", "0", "complete", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        orko.main(["linear", "set", "project", "p", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["status", "demo-topic", "--root", str(tmp_path)])
        assert json.loads(capsys.readouterr().out)["next_step"] == 1
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py::TestLinearIds -q`
Expected: FAIL, `linear` is not a subcommand.

- [ ] **Step 3: Implement**

Add after `LEDGER_LINE_RE`:

```python
LINEAR_KEYS = ("project", "spec_doc", "plan_doc", "brief_doc",
               "synthesis_doc", "blocked_label")
LINEAR_LINE_RE = re.compile(
    r"^linear (?P<key>" + "|".join(LINEAR_KEYS) + r") (?P<id>\S+)$"
)


def _linear_ids(ledger: Path) -> dict[str, str]:
    """Recorded Linear IDs, last write wins. Lives in the ledger so a resumed
    session can re-fetch the Project and documents without the transcript."""
    ids: dict[str, str] = {}
    if not ledger.exists():
        return ids
    for line in ledger.read_text(encoding="utf-8").splitlines()[1:]:
        match = LINEAR_LINE_RE.match(line.strip())
        if match:
            ids[match.group("key")] = match.group("id")
    return ids


def cmd_linear(args: argparse.Namespace) -> int:
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return 2
    ledger = _run_dir_root(root) / args.slug / "progress.md"
    if _parse_header(ledger) is None:
        print(f"orko: no run named {args.slug!r}", file=sys.stderr)
        return 2
    if args.action == "set":
        if CONTROL_RE.search(args.id) or " " in args.id:
            print("orko: a Linear ID cannot contain whitespace", file=sys.stderr)
            return 2
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(f"linear {args.key} {args.id}\n")
        return 0
    print(json.dumps(_linear_ids(ledger), indent=2))
    return 0
```

In `_describe_run`, add `linear=_linear_ids(ledger),` to the returned dict. In `build_parser`:

```python
    p_linear = sub.add_parser("linear", help="record or read Linear IDs")
    linear_sub = p_linear.add_subparsers(dest="action", required=True)
    p_set = linear_sub.add_parser("set")
    p_set.add_argument("key", choices=LINEAR_KEYS)
    p_set.add_argument("id")
    p_set.add_argument("--slug", required=True)
    p_set.add_argument("--root")
    p_set.set_defaults(func=cmd_linear)
    p_get = linear_sub.add_parser("get")
    p_get.add_argument("--slug", required=True)
    p_get.add_argument("--root")
    p_get.set_defaults(func=cmd_linear)
```

`_ledger_entries` already skips lines that do not match `LEDGER_LINE_RE`, so `linear` lines are invisible to step parsing.

- [ ] **Step 4: Run the suite**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: PASS (with the Task 6 xfails, if any).

- [ ] **Step 5: Commit**

```bash
git add orko/scripts
git commit -m "feat(orko): record Linear project and document IDs in the ledger"
```

---

### Task 4: `post project`, `post document`, `post close`

**Files:**
- Modify: `orko/scripts/orko.py` (new `_emit_posts`, `cmd_post_project`, `cmd_post_document`, `cmd_post_close`, `build_parser`)
- Modify: `orko/scripts/test_orko.py` (new `TestPostProject`, `TestPostDocument`, `TestPostClose`, and the `MCP_PARAMS` fixture table)

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Consumes: `_linear_ids`, `_parse_header`, `compute_paths`.
- Produces: stdout JSON `{"posts": [{"tool": "<mcp tool name>", "args": {...}, "then": "<orko.py command to run with the returned id, or null>"}]}`. Tool names: `mcp__linear__save_project`, `mcp__linear__save_document`. Document kinds: `spec`, `plan`, `brief`, `synthesis`, mapping to titles `Spec`, `Plan`, `Brief`, `Synthesis` and ledger keys `<kind>_doc`.

- [ ] **Step 1: Write the failing tests**

Add at module top of the test file, after imports:

```python
# Documented parameter names of the Linear MCP tools orko posts to. A payload
# whose args carry a key not in this set would fail at the MCP boundary, after
# the conductor has already committed to posting it.
MCP_PARAMS = {
    "mcp__linear__save_project": {
        "id", "name", "addTeams", "description", "summary", "state", "links",
    },
    "mcp__linear__save_document": {
        "id", "title", "project", "content",
    },
    "mcp__linear__save_issue": {
        "team", "project", "title", "description", "state", "labels", "links",
    },
    "mcp__linear__save_issue_label": {
        "id", "name", "color", "description", "isGroup", "parent", "teamId",
    },
}


def assert_posts_are_well_formed(payload):
    assert list(payload) == ["posts"]
    for post in payload["posts"]:
        assert set(post) == {"tool", "args", "then"}
        assert post["tool"] in MCP_PARAMS, post["tool"]
        assert set(post["args"]) <= MCP_PARAMS[post["tool"]], post["args"].keys()
```

Then:

```python
class TestPostProject:
    def _init(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        capsys.readouterr()

    def _post(self, tmp_path, capsys, *extra):
        rc = orko.main(["post", "project", "--slug", "demo-topic",
                        "--root", str(tmp_path), *extra])
        out = capsys.readouterr()
        return rc, out

    def test_emits_save_project_for_the_team_named_at_init(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc, out = self._post(tmp_path, capsys, "--goal", "Ship it",
                             "--branch", "orko/demo-topic",
                             "--boundaries", "Only src/")
        assert rc == 0
        payload = json.loads(out.out)
        assert_posts_are_well_formed(payload)
        post = payload["posts"][0]
        assert post["tool"] == "mcp__linear__save_project"
        assert post["args"]["name"] == "demo-topic"
        assert post["args"]["addTeams"] == ["JRF"]
        assert "id" not in post["args"]
        assert post["then"] == "linear set project <returned id> --slug demo-topic"

    def test_description_carries_every_reconstruction_field(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        _, out = self._post(tmp_path, capsys, "--goal", "Ship it",
                            "--branch", "orko/demo-topic", "--boundaries", "Only src/")
        description = json.loads(out.out)["posts"][0]["args"]["description"]
        for needle in ("Ship it", "build", str(tmp_path), "orko/demo-topic",
                       ".orko/demo-topic", "demo-topic", "Only src/"):
            assert needle in description, needle

    def test_refuses_without_goal_or_branch(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc, out = self._post(tmp_path, capsys, "--goal", "Ship it")
        assert rc == 2
        assert "branch" in out.err

    def test_updates_in_place_once_a_project_id_is_recorded(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["linear", "set", "project", "proj_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        _, out = self._post(tmp_path, capsys, "--goal", "Ship it",
                            "--branch", "orko/demo-topic", "--boundaries", "none")
        post = json.loads(out.out)["posts"][0]
        assert post["args"]["id"] == "proj_1"
        assert "addTeams" not in post["args"]
        assert post["then"] is None

    def test_analysis_project_needs_no_branch(self, tmp_path, capsys):
        orko.main(["init", "analysis", "Demo Q", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        capsys.readouterr()
        rc = orko.main(["post", "project", "--slug", "demo-q", "--root", str(tmp_path),
                        "--goal", "Why is it slow?", "--boundaries", "read-only"])
        assert rc == 0


class TestPostDocument:
    def _init(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        orko.main(["linear", "set", "project", "proj_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()

    def test_emits_save_document_with_file_contents(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        (tmp_path / ".orko/demo-topic/spec.md").write_text("# Spec\n\nbody\n")
        rc = orko.main(["post", "document", "spec", "--slug", "demo-topic",
                        "--root", str(tmp_path)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert_posts_are_well_formed(payload)
        post = payload["posts"][0]
        assert post["tool"] == "mcp__linear__save_document"
        assert post["args"] == {"title": "Spec", "project": "proj_1",
                                "content": "# Spec\n\nbody\n"}
        assert post["then"] == "linear set spec_doc <returned id> --slug demo-topic"

    def test_updates_when_the_document_id_is_recorded(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        (tmp_path / ".orko/demo-topic/plan.md").write_text("# Plan\n")
        orko.main(["linear", "set", "plan_doc", "doc_2", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        orko.main(["post", "document", "plan", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        post = json.loads(capsys.readouterr().out)["posts"][0]
        assert post["args"]["id"] == "doc_2"
        assert "project" not in post["args"]
        assert post["then"] is None

    def test_refuses_before_the_project_exists(self, tmp_path, capsys):
        orko.main(["init", "build", "Other", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        (tmp_path / ".orko/other/spec.md").write_text("# Spec\n")
        capsys.readouterr()
        rc = orko.main(["post", "document", "spec", "--slug", "other",
                        "--root", str(tmp_path)])
        assert rc == 2
        assert "project" in capsys.readouterr().err

    def test_refuses_when_the_file_is_missing(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["post", "document", "synthesis", "--slug", "demo-topic",
                        "--root", str(tmp_path)])
        assert rc == 2


class TestPostClose:
    def test_emits_completed_state_with_summary(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        orko.main(["linear", "set", "project", "proj_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        rc = orko.main(["post", "close", "--slug", "demo-topic", "--root", str(tmp_path),
                        "--summary", "Two tasks shipped.", "--pr",
                        "https://github.com/x/y/pull/1"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert_posts_are_well_formed(payload)
        post = payload["posts"][0]
        assert post["args"]["id"] == "proj_1"
        assert post["args"]["state"] == "Completed"
        assert post["args"]["links"] == [{"url": "https://github.com/x/y/pull/1",
                                          "title": "Pull request"}]
        assert "Two tasks shipped." in post["args"]["description"]

    def test_refuses_without_summary(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        orko.main(["linear", "set", "project", "proj_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        with pytest.raises(SystemExit):
            orko.main(["post", "close", "--slug", "demo-topic", "--root", str(tmp_path)])
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -k "TestPost" -q`
Expected: FAIL, `post` is not a subcommand.

- [ ] **Step 3: Implement**

Add to `orko/scripts/orko.py`:

```python
DOC_KINDS = {"spec": "Spec", "plan": "Plan", "brief": "Brief", "synthesis": "Synthesis"}


def _emit_posts(posts: list[dict]) -> int:
    """The one place payloads leave the script. Every `post` subcommand ends
    here so the shape the conductor relays is identical across entities."""
    print(json.dumps({"posts": posts}, indent=2))
    return 0


def _load_run(args: argparse.Namespace) -> tuple[Path, dict] | None:
    root = _resolved_root(args)
    if root is None:
        print(f"orko: not inside a git repository: {Path.cwd()}", file=sys.stderr)
        return None
    run = _describe_run(root, args.slug)
    if run is None:
        print(f"orko: no run named {args.slug!r}", file=sys.stderr)
        return None
    return root, run


def _project_description(run: dict, goal: str, boundaries: str,
                         branch: str | None) -> str:
    lines = [
        f"**Goal:** {goal}",
        "",
        f"- Mode: {run['mode']}",
        f"- Slug: `{run['slug']}`",
        f"- Repository: `{run['root']}`",
        f"- Branch: `{branch}`" if branch else "- Branch: none (analysis, read-only)",
        f"- Run directory: `{run['run_dir']}`",
        f"- Boundaries: {boundaries}",
        "",
        "Record kept by orko. Issues in this project are decisions kicked up to "
        "the conductor, one per decision, attributed by seat in the first line "
        "of each description. Documents hold the working artifacts.",
    ]
    return "\n".join(lines) + "\n"


def cmd_post_project(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    if run["mode"] == "build" and not args.branch:
        print("orko: a build project needs --branch (the orko/<slug> branch the "
              "run works on)", file=sys.stderr)
        return 2
    description = _project_description(run, args.goal, args.boundaries, args.branch)
    existing = run["linear"].get("project")
    if existing:
        post_args = {"id": existing, "description": description}
        then = None
    else:
        post_args = {"name": run["slug"], "addTeams": [run["team"]],
                     "summary": args.goal[:255], "description": description}
        then = f"linear set project <returned id> --slug {run['slug']}"
    return _emit_posts([{"tool": "mcp__linear__save_project",
                         "args": post_args, "then": then}])


def cmd_post_document(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    project = run["linear"].get("project")
    if not project:
        print("orko: no Linear project recorded for this run; post project first "
              "and record its id with `linear set project`", file=sys.stderr)
        return 2
    source = Path(run[args.kind])
    try:
        content = source.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {source}: {error}", file=sys.stderr)
        return 2
    key = f"{args.kind}_doc"
    existing = run["linear"].get(key)
    if existing:
        post_args = {"id": existing, "content": content}
        then = None
    else:
        post_args = {"title": DOC_KINDS[args.kind], "project": project,
                     "content": content}
        then = f"linear set {key} <returned id> --slug {run['slug']}"
    return _emit_posts([{"tool": "mcp__linear__save_document",
                         "args": post_args, "then": then}])


def cmd_post_close(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    project = run["linear"].get("project")
    if not project:
        print("orko: no Linear project recorded for this run", file=sys.stderr)
        return 2
    post_args: dict = {
        "id": project,
        "state": "Completed",
        "description": f"**Closed.** {args.summary}\n",
    }
    if args.pr:
        post_args["links"] = [{"url": args.pr, "title": "Pull request"}]
    return _emit_posts([{"tool": "mcp__linear__save_project",
                         "args": post_args, "then": None}])
```

Note that `save_project` on update replaces `description`. The close payload therefore deliberately does not re-send the reconstruction block; the conductor runs `post project` again before `post close` when the description needs refreshing, and `references/linear.md` (Task 9) says so.

In `build_parser`:

```python
    p_post = sub.add_parser("post", help="emit a Linear payload for the conductor to send")
    post_sub = p_post.add_subparsers(dest="entity", required=True)

    p_pp = post_sub.add_parser("project")
    p_pp.add_argument("--slug", required=True)
    p_pp.add_argument("--root")
    p_pp.add_argument("--goal", required=True)
    p_pp.add_argument("--boundaries", required=True)
    p_pp.add_argument("--branch")
    p_pp.set_defaults(func=cmd_post_project)

    p_pd = post_sub.add_parser("document")
    p_pd.add_argument("kind", choices=sorted(DOC_KINDS))
    p_pd.add_argument("--slug", required=True)
    p_pd.add_argument("--root")
    p_pd.set_defaults(func=cmd_post_document)

    p_pc = post_sub.add_parser("close")
    p_pc.add_argument("--slug", required=True)
    p_pc.add_argument("--root")
    p_pc.add_argument("--summary", required=True)
    p_pc.add_argument("--pr")
    p_pc.set_defaults(func=cmd_post_close)
```

- [ ] **Step 4: Run the suite**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add orko/scripts
git commit -m "feat(orko): post project, document, and close payloads for Linear"
```

---

### Task 5: `post finding` and `post escalation`

**Files:**
- Modify: `orko/scripts/orko.py` (new `OUTCOMES`, `cmd_post_finding`, `cmd_post_escalation`, `build_parser`)
- Modify: `orko/scripts/test_orko.py` (new `TestPostFinding`, `TestPostEscalation`)

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Consumes: `_load_run`, `_emit_posts`, `_linear_ids`.
- Produces: `OUTCOMES: dict[str, str]` mapping `handled -> Done`, `deferred -> Backlog`, `rejected -> Canceled`, `blocked -> Todo`; CLI `post finding --slug S --seat NAME --outcome O --title T` with the body on stdin; `post escalation` same arguments, forces `blocked`, and appends the body to `escalations.md` itself.

- [ ] **Step 1: Write the failing tests, one per outcome**

```python
class TestPostFinding:
    def _init(self, tmp_path, capsys):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        orko.main(["linear", "set", "project", "proj_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()

    def _post(self, tmp_path, capsys, monkeypatch, outcome, body="Evidence here.\n"):
        monkeypatch.setattr("sys.stdin", io.StringIO(body))
        rc = orko.main(["post", "finding", "--slug", "demo-topic", "--root", str(tmp_path),
                        "--seat", "security-reviewer", "--outcome", outcome,
                        "--title", "Token in query string"])
        return rc, capsys.readouterr()

    def test_handled_maps_to_done(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        rc, out = self._post(tmp_path, capsys, monkeypatch, "handled")
        assert rc == 0
        payload = json.loads(out.out)
        assert_posts_are_well_formed(payload)
        assert payload["posts"][-1]["args"]["state"] == "Done"

    def test_deferred_maps_to_backlog(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        _, out = self._post(tmp_path, capsys, monkeypatch, "deferred")
        assert json.loads(out.out)["posts"][-1]["args"]["state"] == "Backlog"

    def test_rejected_maps_to_canceled(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        _, out = self._post(tmp_path, capsys, monkeypatch, "rejected")
        assert json.loads(out.out)["posts"][-1]["args"]["state"] == "Canceled"

    def test_blocked_maps_to_todo_with_label(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        orko.main(["linear", "set", "blocked_label", "lbl_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        _, out = self._post(tmp_path, capsys, monkeypatch, "blocked")
        posts = json.loads(out.out)["posts"]
        assert len(posts) == 1
        assert posts[0]["args"]["state"] == "Todo"
        assert posts[0]["args"]["labels"] == ["blocked"]

    def test_blocked_bootstraps_the_label_when_unrecorded(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        _, out = self._post(tmp_path, capsys, monkeypatch, "blocked")
        posts = json.loads(out.out)["posts"]
        assert [p["tool"] for p in posts] == ["mcp__linear__save_issue_label",
                                              "mcp__linear__save_issue"]
        assert posts[0]["args"] == {"name": "blocked", "color": "#eb5757"}
        assert posts[0]["then"] == "linear set blocked_label <returned id> --slug demo-topic"

    def test_description_starts_with_the_seat_line(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        _, out = self._post(tmp_path, capsys, monkeypatch, "handled")
        description = json.loads(out.out)["posts"][-1]["args"]["description"]
        assert description.startswith("Seat: security-reviewer\n")
        assert "Evidence here." in description

    def test_issue_targets_team_and_project(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        _, out = self._post(tmp_path, capsys, monkeypatch, "handled")
        args = json.loads(out.out)["posts"][-1]["args"]
        assert args["team"] == "JRF"
        assert args["project"] == "proj_1"
        assert args["title"] == "Token in query string"

    def test_empty_body_is_a_usage_error(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        rc, out = self._post(tmp_path, capsys, monkeypatch, "handled", body="  \n")
        assert rc == 2
        assert "body" in out.err

    def test_unknown_outcome_is_rejected_by_argparse(self, tmp_path, capsys, monkeypatch):
        self._init(tmp_path, capsys)
        with pytest.raises(SystemExit):
            self._post(tmp_path, capsys, monkeypatch, "maybe")


class TestPostEscalation:
    def test_escalation_is_a_blocked_finding_that_writes_the_gate_file(
        self, tmp_path, capsys, monkeypatch
    ):
        orko.main(["init", "build", "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        orko.main(["linear", "set", "project", "proj_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        orko.main(["linear", "set", "blocked_label", "lbl_1", "--slug", "demo-topic",
                   "--root", str(tmp_path)])
        capsys.readouterr()
        monkeypatch.setattr("sys.stdin", io.StringIO("Scope grows to billing.\n"))
        rc = orko.main(["post", "escalation", "--slug", "demo-topic",
                        "--root", str(tmp_path), "--seat", "architecture-reviewer",
                        "--title", "Billing is outside boundaries"])
        assert rc == 0
        posts = json.loads(capsys.readouterr().out)["posts"]
        assert posts[-1]["args"]["state"] == "Todo"
        assert posts[-1]["args"]["labels"] == ["blocked"]
        gate = (tmp_path / ".orko/demo-topic/escalations.md").read_text()
        assert "Billing is outside boundaries" in gate
        assert "Scope grows to billing." in gate
        assert orko.main(["escalations", "demo-topic", "--root", str(tmp_path)]) == 1
```

Add `import io` at the top of the test file.

- [ ] **Step 2: Run the tests to see them fail**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -k "Finding or Escalation" -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# Decision outcomes and the JRF team state each maps to. The team has no
# "Blocked" state, so an out-of-boundaries finding is a Todo carrying the
# `blocked` label, and the run stops on it (see cmd_post_escalation).
OUTCOMES: dict[str, str] = {
    "handled": "Done",
    "deferred": "Backlog",
    "rejected": "Canceled",
    "blocked": "Todo",
}
BLOCKED_LABEL = {"name": "blocked", "color": "#eb5757"}


def _finding_posts(run: dict, seat: str, outcome: str, title: str,
                   body: str) -> list[dict]:
    posts: list[dict] = []
    labels: list[str] = []
    if outcome == "blocked":
        labels = [BLOCKED_LABEL["name"]]
        if not run["linear"].get("blocked_label"):
            posts.append({
                "tool": "mcp__linear__save_issue_label",
                "args": dict(BLOCKED_LABEL),
                "then": f"linear set blocked_label <returned id> --slug {run['slug']}",
            })
    issue_args: dict = {
        "team": run["team"],
        "project": run["linear"]["project"],
        "title": title,
        "state": OUTCOMES[outcome],
        "description": f"Seat: {seat}\n\n{body.rstrip()}\n",
    }
    if labels:
        issue_args["labels"] = labels
    posts.append({"tool": "mcp__linear__save_issue", "args": issue_args,
                  "then": None})
    return posts


def _read_body() -> str | None:
    body = sys.stdin.read()
    return body if body.strip() else None


def cmd_post_finding(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    if not run["linear"].get("project"):
        print("orko: no Linear project recorded for this run", file=sys.stderr)
        return 2
    body = _read_body()
    if body is None:
        print("orko: the finding body (stdin) is empty; pipe the finding's "
              "evidence and the conductor's reasoning", file=sys.stderr)
        return 2
    outcome = "blocked" if args.entity == "escalation" else args.outcome
    if args.entity == "escalation":
        gate = Path(run["escalations"])
        with gate.open("a", encoding="utf-8") as handle:
            handle.write(f"## {args.title}\n\nSeat: {args.seat}\n\n{body.rstrip()}\n\n")
    return _emit_posts(_finding_posts(run, args.seat, outcome, args.title, body))
```

In `build_parser`:

```python
    for entity in ("finding", "escalation"):
        p_pf = post_sub.add_parser(entity)
        p_pf.add_argument("--slug", required=True)
        p_pf.add_argument("--root")
        p_pf.add_argument("--seat", required=True)
        p_pf.add_argument("--title", required=True)
        if entity == "finding":
            p_pf.add_argument("--outcome", required=True, choices=sorted(OUTCOMES))
        p_pf.set_defaults(func=cmd_post_finding)
```

- [ ] **Step 4: Run the suite**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: PASS.

- [ ] **Step 5: Mutation check on the outcome map**

Temporarily change `"deferred": "Backlog"` to `"deferred": "Todo"` and run the suite. Expected: exactly `test_deferred_maps_to_backlog` fails. Revert. Repeat for `handled` and `rejected`; each must turn exactly its own test red. Record the three results in the commit message body.

- [ ] **Step 6: Commit**

```bash
git add orko/scripts
git commit -m "feat(orko): post finding and escalation payloads, one issue per decision

Mutation check: each outcome row in OUTCOMES turns exactly one test red
(handled, deferred, rejected). blocked is pinned by the label tests."
```

---

### Task 6: Prompt kinds and charter files

**Files:**
- Create: `orko/references/spec-reviewer.md` (report-only, with a Lenses table)
- Create: `orko/references/plan-reviewer.md` (report-only, with a Lenses table)
- Create: `orko/references/plan-writer.md`
- Create: `orko/references/seat-prompt.md`
- Create: `orko/references/verifier-prompt.md`
- Delete: `autonom/references/spec-reviewer.md`, `autonom/references/plan-reviewer.md`
- Modify: `orko/references/seats.md` (replace the two inline templates with pointers)
- Modify: `orko/scripts/orko.py` (`cmd_prompt`, `_lenses`, `build_parser`)
- Modify: `orko/scripts/test_orko.py` (rewrite `TestPrompt`)

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Produces: CLI `prompt <kind> <slug> [--lens NAME] [--seat NAME --question TEXT --context-file PATH]`. Kinds `spec-review`, `plan-review` require `--lens`; `plan-write` takes no extra; `seat` and `verifier` require `--seat`, `--question`, `--context-file`. Tokens: `{{ARTIFACT_PATH}}`, `{{SPEC_PATH}}`, `{{PLAN_PATH}}`, `{{RUN_DIR}}`, `{{ROOT}}`, `{{SLUG}}`, `{{LENS_NAME}}`, `{{LENS_QUESTION}}`, `{{FINDINGS_PATH}}`, `{{VERDICT_PATH}}`, `{{SEAT}}`, `{{QUESTION}}`, `{{CONTEXT}}`. Any leftover `{{...}}` exits `2`.
- Produces: `_lenses(text) -> dict[str, str]` parsed from a markdown table under a `## Lenses` heading with columns `Lens | Question`.

- [ ] **Step 1: Write the charter files**

`orko/references/spec-reviewer.md`:

````markdown
You are a reviewer seat on an orko build engagement. You did not write this spec and have no stake in it. Your value is a fresh reading against the repository as it actually exists.

**Spec:** {{ARTIFACT_PATH}}
**Repository root:** {{ROOT}}
**Run directory:** {{RUN_DIR}}

Your lens is **{{LENS_NAME}}**. The one question you own: {{LENS_QUESTION}}

Read the spec, then read the code, conventions, and docs it describes. Judge the spec against the codebase, not against how you would have written it.

Rules:
- Report only. You have no write authority on the spec, the repository, or anything in Linear. Do not edit, do not run git, do not commit.
- Substantiate every finding against a tool result: a file and line, a command's output, a quoted sentence of the spec. State what you did not check.
- Leave alone wording you would have phrased differently and structure you would have organized differently.
- A finding that would change what is being built rather than how it is described is a scope finding. Mark it `scope:` at the start of its verdict line so the conductor can route it to the human.
- Be concise: findings are evidence, not prose.

When done:
1. Write your findings to {{FINDINGS_PATH}} using this schema exactly:

### FINDINGS — Seat: {{LENS_NAME}}
- Verdict: <one line>
- Evidence: <each point tied to a file:line, a quoted spec line, or a tool result>
- Recommendations: <ordered; each one a concrete edit the conductor could make>
- Confidence & gaps: <what is uncertain or unchecked>

2. Return to the conductor ONLY the file path, your one-line verdict, and your confidence (high/medium/low). Do not paste the findings into your return.

## Lenses

| Lens | Question |
|---|---|
| requirements | Do the goals, non-goals, and requirements agree with each other, and is every requirement testable as written? |
| architecture | Does the architecture work against the code that exists at the repository root: real module names, real interfaces, real constraints? |
| testability | Can each requirement be verified by a test the plan could name, and does the testing section cover the risky surfaces? |
| security | Where does this design accept input, hold secrets, cross a trust boundary, or write to disk or a third-party service, and is each of those handled? |
````

`orko/references/plan-reviewer.md`:

````markdown
You are a reviewer seat on an orko build engagement. You did not write this plan and have no stake in it.

**Plan:** {{ARTIFACT_PATH}}
**Spec the plan must satisfy:** {{SPEC_PATH}}
**Repository root:** {{ROOT}}
**Run directory:** {{RUN_DIR}}

Your lens is **{{LENS_NAME}}**. The one question you own: {{LENS_QUESTION}}

Read the spec first, then the plan, then the repository the plan will change. The spec is the contract: judge the plan against what the spec asks for.

Rules:
- Report only. You have no write authority on the plan, the repository, or anything in Linear. Do not edit, do not run git, do not commit.
- Substantiate every finding against a tool result. State what you did not check.
- A finding that would change what is being built is a scope finding. Mark it `scope:` at the start of its verdict line.
- Be concise: findings are evidence, not prose.

When done:
1. Write your findings to {{FINDINGS_PATH}} using this schema exactly:

### FINDINGS — Seat: {{LENS_NAME}}
- Verdict: <one line>
- Evidence: <each point tied to a task number and line, a quoted spec line, or a file:line>
- Recommendations: <ordered; each one a concrete edit to a named task>
- Confidence & gaps: <what is uncertain or unchecked>

2. Return to the conductor ONLY the file path, your one-line verdict, and your confidence (high/medium/low). Do not paste the findings into your return.

## Lenses

| Lens | Question |
|---|---|
| coverage | Is every spec requirement implemented by a named task, and does any task build something the spec does not ask for? |
| interfaces | Do the names, signatures, and types a later task consumes match what an earlier task produces, and can each task be rejected without rejecting its neighbor? |
| placeholders | Does any step describe what to do without showing how, defer content, or reference a function no task defines? |
| tests | Does each task's test actually pin the behavior the task claims, and would a plausible wrong implementation pass it? |
````

`orko/references/plan-writer.md`:

````markdown
You are the plan-writer seat on an orko build engagement. You draft the implementation plan; the conductor edits and owns it.

**Spec:** {{SPEC_PATH}}
**Write the plan to:** {{PLAN_PATH}}
**Repository root:** {{ROOT}}

Read the spec, then the repository it changes. Then write the plan following `superpowers:writing-plans` exactly: the mandatory header line with `REQUIRED SUB-SKILL` and `superpowers:subagent-driven-development`, a `## Global Constraints` section, and `### Task N:` blocks each carrying `**Files:**`, `**Interfaces:**`, and `- [ ] **Step` checkboxes with real code. Lift the header out of any fence; a fenced header is invisible to the validator.

Rules:
- Do not touch the repository, git, or Linear. Your only write is the plan file.
- No placeholders: never `TBD`, `TODO`, `Similar to Task N`, `add appropriate error handling`, `add validation`, `handle edge cases`, or a bare `Write tests for the above`.
- Every task ends in an independently testable deliverable and a commit step.
- Where the spec is silent, choose the option that touches the least code and say so in the task.

When done:
1. Save the plan at the path above.
2. Return to the conductor ONLY the path and the task count. Do not paste the plan into your return.
````

`orko/references/seat-prompt.md` (the v1 seat template with slots):

````markdown
You are the {{SEAT}} on an orko engagement. Investigate ONLY: {{QUESTION}}

Context (you inherit no prior conversation; everything you need is here):
{{CONTEXT}}

Rules:
- Substantiate every claim against a tool result (cite file:line or command output). State explicitly what you did NOT check.
- Do not change anything. Report findings only.
- Stay within your seat's scope; flag adjacent issues in one line, don't chase them.
- Be concise: findings are evidence, not prose. No preamble, no restating the task, no narrating your steps.

When done:
1. Write your full findings to {{FINDINGS_PATH}} using this schema exactly:

### FINDINGS — Seat: {{SEAT}}
- Verdict: <one line>
- Evidence: <each point tied to a file:line or tool result>
- Recommendations: <ordered>
- Confidence & gaps: <what is uncertain or unchecked>

2. Return to the conductor ONLY: the file path, your one-line verdict, and your confidence (high/medium/low). Do not paste the findings into your return.
````

`orko/references/verifier-prompt.md`:

````markdown
You are an independent verifier on an orko engagement. You did not author these findings and have no stake in them.

Read ONLY:
- The findings file: {{FINDINGS_PATH}}
- The same source material it cites:
{{CONTEXT}}

For EACH finding, re-check it against the actual evidence and label it:
- confirmed — evidence supports it as stated
- overstated — real but exaggerated (give the accurate version)
- unsubstantiated — evidence does not support it
- missing-context — true but omits something that changes the conclusion

Check severity, not just existence. A seat reproduces a problem under conditions it chose; ask whether the documented, normal usage path reaches it at all. A real bug that only fires under conditions the tool never encounters is `overstated`, and saying so is the job.

Do not rewrite the findings or investigate beyond checking the claims.

When done:
1. Write your verdicts to {{VERDICT_PATH}} using this schema exactly:

### VERDICTS — Seat: {{SEAT}}
- <finding> -> <label>: <one-line reason, cite evidence>

2. Return to the conductor ONLY a one-line tally (e.g. "3 confirmed, 1 overstated, 0 unsubstantiated"). Do not paste your verdicts into the return.
````

In `orko/references/seats.md`, delete the "Dispatch-prompt template" and "Verifier-prompt template" sections and their closing paragraph, and append:

```markdown
## Dispatch and verifier prompts

Both prompts are emitted by the script, never composed by hand:

    uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt seat <slug> --seat <name> --question "<one question>" --context-file <run_dir>/context/<name>.md
    uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py prompt verifier <slug> --seat <name> --question "<same question>" --context-file <run_dir>/context/<name>.md

The context file is the conductor's one authored input per seat: paths, constraints, the larger goal, and who the work is for. The templates live in `seat-prompt.md` and `verifier-prompt.md` beside this file. Both end with a numbered write-then-return close, because a subagent treats its returned message as the answer and a file instruction buried mid-prompt gets skipped. Keep any new template structurally parallel.
```

Delete the autonom charter files:

```bash
git rm autonom/references/spec-reviewer.md autonom/references/plan-reviewer.md
```

- [ ] **Step 2: Write the failing tests**

Replace `class TestPrompt` in the test file:

```python
class TestPrompt:
    def _init(self, tmp_path, capsys, mode="build"):
        orko.main(["init", mode, "Demo Topic", "--team", "JRF",
                   "--root", str(tmp_path), "--date", "2026-09-04"])
        capsys.readouterr()

    def test_spec_review_substitutes_every_token_including_the_lens(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        assert orko.main(["prompt", "spec-review", "demo-topic", "--lens", "security",
                          "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert "{{" not in out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out
        assert str(tmp_path / ".orko/demo-topic/findings/security.md") in out
        assert "Your lens is **security**" in out
        assert "trust boundary" in out
        assert "## Lenses" not in out

    def test_plan_review_carries_the_spec_path(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        orko.main(["prompt", "plan-review", "demo-topic", "--lens", "coverage",
                   "--root", str(tmp_path)])
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/plan.md") in out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out
        assert "{{" not in out

    def test_unknown_lens_is_a_usage_error_naming_the_valid_ones(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["prompt", "spec-review", "demo-topic", "--lens", "vibes",
                        "--root", str(tmp_path)])
        assert rc == 2
        err = capsys.readouterr().err
        for lens in ("requirements", "architecture", "testability", "security"):
            assert lens in err

    def test_review_kinds_require_a_lens(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        rc = orko.main(["prompt", "plan-review", "demo-topic", "--root", str(tmp_path)])
        assert rc == 2

    def test_plan_write_names_both_artifact_paths(self, tmp_path, capsys):
        self._init(tmp_path, capsys)
        assert orko.main(["prompt", "plan-write", "demo-topic",
                          "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/spec.md") in out
        assert str(tmp_path / ".orko/demo-topic/plan.md") in out
        assert "{{" not in out

    def test_seat_prompt_inlines_the_context_file(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("Look at src/hot.py\n")
        assert orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                          "--question", "Where is the N+1?",
                          "--context-file", str(ctx), "--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert "You are the perf on an orko engagement" in out
        assert "Where is the N+1?" in out
        assert "Look at src/hot.py" in out
        assert str(tmp_path / ".orko/demo-topic/findings/perf.md") in out
        assert "{{" not in out

    def test_verifier_prompt_names_findings_and_verdict_paths(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        ctx = tmp_path / ".orko/demo-topic/context/perf.md"
        ctx.write_text("src/hot.py\n")
        orko.main(["prompt", "verifier", "demo-topic", "--seat", "perf",
                   "--question", "Where is the N+1?",
                   "--context-file", str(ctx), "--root", str(tmp_path)])
        out = capsys.readouterr().out
        assert str(tmp_path / ".orko/demo-topic/findings/perf.md") in out
        assert str(tmp_path / ".orko/demo-topic/findings/perf.verdict.md") in out
        assert "{{" not in out

    def test_seat_kinds_require_seat_question_and_context(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                        "--root", str(tmp_path)])
        assert rc == 2

    def test_missing_context_file_is_an_io_error(self, tmp_path, capsys):
        self._init(tmp_path, capsys, mode="analysis")
        rc = orko.main(["prompt", "seat", "demo-topic", "--seat", "perf",
                        "--question", "q", "--context-file", str(tmp_path / "nope.md"),
                        "--root", str(tmp_path)])
        assert rc == 2

    def test_no_charter_mentions_git_or_write_authority(self):
        for name in ("spec-reviewer.md", "plan-reviewer.md"):
            text = (orko.references_dir() / name).read_text(encoding="utf-8")
            assert "git -C" not in text
            assert "write authority on the spec" not in text
            assert "write authority on the plan" not in text
            assert "Report only" in text

    def test_lens_table_parses(self):
        text = (orko.references_dir() / "spec-reviewer.md").read_text(encoding="utf-8")
        lenses = orko._lenses(text)
        assert set(lenses) == {"requirements", "architecture", "testability", "security"}
        assert lenses["security"].endswith("handled?")
```

- [ ] **Step 3: Run the tests to see them fail**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py::TestPrompt -q`
Expected: FAIL.

- [ ] **Step 4: Implement**

Replace `cmd_prompt` and add `_lenses`:

```python
PROMPT_SOURCES = {
    "spec-review": "spec-reviewer.md",
    "plan-review": "plan-reviewer.md",
    "plan-write": "plan-writer.md",
    "seat": "seat-prompt.md",
    "verifier": "verifier-prompt.md",
}
REVIEW_KINDS = ("spec-review", "plan-review")
SEAT_KINDS = ("seat", "verifier")
LENS_ROW_RE = re.compile(r"^\|\s*([a-z][a-z0-9-]*)\s*\|\s*(.+?)\s*\|\s*$")


def _lenses(text: str) -> dict[str, str]:
    """Rows of the `## Lenses` table: name -> question. The table lives in the
    charter so the lens list is prose the conductor can read, and parsing it
    here keeps the script the only thing that assembles a dispatch."""
    lenses: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## Lenses":
            in_table = True
            continue
        if not in_table:
            continue
        match = LENS_ROW_RE.match(line)
        if not match or match.group(1) == "lens":
            continue
        if set(match.group(2)) <= {"-", " "}:
            continue
        lenses[match.group(1)] = match.group(2)
    return lenses


def _strip_lenses(text: str) -> str:
    """The dispatched prompt carries one lens, not the menu."""
    head, _, _ = text.partition("\n## Lenses")
    return head.rstrip() + "\n"


def cmd_prompt(args: argparse.Namespace) -> int:
    loaded = _load_run(args)
    if loaded is None:
        return 2
    _, run = loaded
    source = references_dir() / PROMPT_SOURCES[args.kind]
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        print(f"orko: cannot read {source}: {error}", file=sys.stderr)
        return 2

    findings_dir = Path(run["findings_dir"])
    subs = {
        "{{SPEC_PATH}}": run["spec"],
        "{{PLAN_PATH}}": run["plan"],
        "{{RUN_DIR}}": run["run_dir"],
        "{{ROOT}}": run["root"],
        "{{SLUG}}": run["slug"],
    }

    if args.kind in REVIEW_KINDS:
        if not args.lens:
            print(f"orko: {args.kind} needs --lens", file=sys.stderr)
            return 2
        lenses = _lenses(text)
        if args.lens not in lenses:
            print(f"orko: unknown lens {args.lens!r}; valid: {', '.join(lenses)}",
                  file=sys.stderr)
            return 2
        subs["{{ARTIFACT_PATH}}"] = run["spec" if args.kind == "spec-review" else "plan"]
        subs["{{LENS_NAME}}"] = args.lens
        subs["{{LENS_QUESTION}}"] = lenses[args.lens]
        subs["{{FINDINGS_PATH}}"] = str(findings_dir / f"{args.lens}.md")
        text = _strip_lenses(text)
    elif args.kind in SEAT_KINDS:
        if not (args.seat and args.question and args.context_file):
            print(f"orko: {args.kind} needs --seat, --question, and --context-file",
                  file=sys.stderr)
            return 2
        try:
            context = Path(args.context_file).read_text(encoding="utf-8")
        except OSError as error:
            print(f"orko: cannot read {args.context_file}: {error}", file=sys.stderr)
            return 2
        subs["{{SEAT}}"] = args.seat
        subs["{{QUESTION}}"] = args.question
        subs["{{CONTEXT}}"] = context.rstrip()
        subs["{{FINDINGS_PATH}}"] = str(findings_dir / f"{args.seat}.md")
        subs["{{VERDICT_PATH}}"] = str(findings_dir / f"{args.seat}.verdict.md")

    for token, value in subs.items():
        text = text.replace(token, value)
    leftover = re.search(r"\{\{[A-Z_]+\}\}", text)
    if leftover:
        print(f"orko: unsubstituted token {leftover.group(0)} in {source}",
              file=sys.stderr)
        return 2
    sys.stdout.write(text)
    return 0
```

In `build_parser`, replace the `prompt` parser:

```python
    p_prompt = sub.add_parser("prompt", help="emit a dispatch prompt")
    p_prompt.add_argument("kind", choices=sorted(PROMPT_SOURCES))
    p_prompt.add_argument("slug")
    p_prompt.add_argument("--lens")
    p_prompt.add_argument("--seat")
    p_prompt.add_argument("--question")
    p_prompt.add_argument("--context-file")
    p_prompt.add_argument("--root")
    p_prompt.set_defaults(func=cmd_prompt)
```

Remove any `xfail` markers added in Task 2.

- [ ] **Step 5: Run the suite**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add orko/references orko/scripts autonom/references
git commit -m "feat(orko): script-emitted prompts for review lenses, plan-writer, seats, and verifiers"
```

---

### Task 7: `preflight`

**Files:**
- Modify: `orko/scripts/orko.py` (new `cmd_preflight`, `_current_branch`, `build_parser`)
- Modify: `orko/scripts/test_orko.py` (new `TestPreflight`)

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Produces: CLI `preflight [--slug S] [--root R] [--mode M]`. Exit `0` clean, `1` with one finding per line on stdout, `2` when not in a git repo. Findings by name: `uv-missing`, `on-default-branch`, `run-dir-not-ignored`, `project-id-missing`, `blocked-escalation`.

- [ ] **Step 1: Write the failing tests**

```python
class TestPreflight:
    def _repo(self, tmp_path, branch="feat/x"):
        subprocess.run(["git", "init", "-q", "-b", branch, str(tmp_path)], check=True)
        return tmp_path

    def test_clean_repo_on_feature_branch_passes(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 0

    def test_master_fails_for_build(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 1
        assert "on-default-branch" in capsys.readouterr().out

    def test_master_is_fine_for_analysis(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "analysis"]) == 0

    def test_missing_uv_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        (root / ".gitignore").write_text(".orko/\n")
        monkeypatch.setattr(orko.shutil, "which", lambda name: None)
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 1
        assert "uv-missing" in capsys.readouterr().out

    def test_unignored_run_dir_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        assert orko.main(["preflight", "--root", str(root), "--mode", "build"]) == 1
        assert "run-dir-not-ignored" in capsys.readouterr().out

    def test_run_past_intake_without_project_id_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        orko.main(["init", "build", "Demo", "--team", "JRF", "--root", str(root),
                   "--date", "2026-09-04"])
        orko.main(["ledger", "0", "complete", "--slug", "demo", "--root", str(root)])
        capsys.readouterr()
        assert orko.main(["preflight", "--root", str(root), "--slug", "demo"]) == 1
        assert "project-id-missing" in capsys.readouterr().out

    def test_slug_supplies_the_mode(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path, branch="master")
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        orko.main(["init", "build", "Demo", "--team", "JRF", "--root", str(root),
                   "--date", "2026-09-04"])
        capsys.readouterr()
        assert orko.main(["preflight", "--root", str(root), "--slug", "demo"]) == 1
        assert "on-default-branch" in capsys.readouterr().out

    def test_outstanding_escalation_is_reported(self, tmp_path, capsys, monkeypatch):
        root = self._repo(tmp_path)
        monkeypatch.setattr(orko.shutil, "which", lambda name: "/usr/bin/uv")
        orko.main(["init", "build", "Demo", "--team", "JRF", "--root", str(root),
                   "--date", "2026-09-04"])
        (root / ".orko/demo/escalations.md").write_text("## Scope\n\nbody\n")
        capsys.readouterr()
        assert orko.main(["preflight", "--root", str(root), "--slug", "demo"]) == 1
        assert "blocked-escalation" in capsys.readouterr().out

    def test_not_a_repo_is_exit_two(self, tmp_path, capsys):
        assert orko.main(["preflight", "--root", str(tmp_path), "--mode", "build"]) == 2
```

Add `import subprocess` to the test imports.

- [ ] **Step 2: Run the tests to see them fail**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py::TestPreflight -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

Add `import shutil` to the script imports, then:

```python
DEFAULT_BRANCHES = {"master", "main"}


def _current_branch(root: Path) -> str | None:
    # symbolic-ref, not rev-parse --abbrev-ref: the latter fails on a branch
    # with no commits yet, and a fresh `git init -b master` is exactly the
    # repo a first build engagement is most likely to start in.
    result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _is_git_repo(root: Path) -> bool:
    return find_repo_root(root) is not None


def cmd_preflight(args: argparse.Namespace) -> int:
    """Check in code what the prose used to ask the conductor to check.

    Four of autonom's last five review findings were SKILL.md prescribing an
    action nothing verified. Each condition here is one of those.
    """
    root = Path(args.root).resolve() if args.root else find_repo_root(Path.cwd())
    if root is None or not _is_git_repo(root):
        print(f"orko: not inside a git repository: {root or Path.cwd()}",
              file=sys.stderr)
        return 2

    mode = args.mode
    run = None
    if args.slug:
        run = _describe_run(root, args.slug)
        if run is None:
            print(f"orko: no run named {args.slug!r}", file=sys.stderr)
            return 2
        mode = run["mode"]
    if mode is None:
        print("orko: preflight needs --mode or --slug", file=sys.stderr)
        return 2

    findings: list[str] = []
    if shutil.which("uv") is None:
        findings.append("uv-missing: `uv` is not on PATH; every script call needs it")
    branch = _current_branch(root)
    if mode == "build" and branch in DEFAULT_BRANCHES:
        findings.append(f"on-default-branch: HEAD is {branch}; a build runs on "
                        "orko/<slug>, never on a default branch")
    gitignore = root / ".gitignore"
    ignored = gitignore.exists() and any(
        line.strip() == ".orko/" for line in gitignore.read_text(encoding="utf-8").splitlines()
    )
    if not ignored:
        findings.append("run-dir-not-ignored: .gitignore lacks `.orko/`; init adds it")
    if run is not None:
        past_intake = run["mode"] == "build" and run["next_step"] != 0
        past_open = run["mode"] == "analysis" and run["next_step"] != 1
        if (past_intake or past_open) and not run["linear"].get("project"):
            findings.append("project-id-missing: the run is past its first step and "
                            "no Linear project id is recorded; post project and "
                            "`linear set project`")
        gate = Path(run["escalations"])
        if gate.exists() and gate.read_text(encoding="utf-8").strip():
            findings.append("blocked-escalation: escalations.md is non-empty; only "
                            "oiler may empty it, and the run stays stopped until then")

    for finding in findings:
        print(finding)
    return 1 if findings else 0
```

In `build_parser`:

```python
    p_pre = sub.add_parser("preflight", help="check repo, branch, tooling, and record state")
    p_pre.add_argument("--slug")
    p_pre.add_argument("--mode", choices=sorted(MODES))
    p_pre.add_argument("--root")
    p_pre.set_defaults(func=cmd_preflight)
```

- [ ] **Step 4: Run the suite**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add orko/scripts
git commit -m "feat(orko): preflight checks repo, branch, uv, gitignore, project id, and the escalation gate in code"
```

---

### Task 8: Validator fixtures from real artifacts

**Files:**
- Create: `orko/scripts/fixtures/spec.md` (copy of the workshop spec)
- Create: `orko/scripts/fixtures/plan.md` (copy of this plan)
- Modify: `orko/scripts/test_orko.py` (new `TestFixtures`)

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Consumes: `validate_spec`, `validate_plan`.

- [ ] **Step 1: Copy the fixtures**

```bash
mkdir -p orko/scripts/fixtures
cp /Users/jrf1039/files/projects/001-claude-skills-creator/docs/superpowers/specs/2026-09-04-orko-v2-build-design.md orko/scripts/fixtures/spec.md
cp /Users/jrf1039/files/projects/001-claude-skills-creator/docs/superpowers/plans/2026-09-04-orko-v2-build.md orko/scripts/fixtures/plan.md
```

- [ ] **Step 2: Write the tests**

```python
class TestFixtures:
    """The validators' required shapes derive from real artifacts, not an
    imagined structure. A rule change that rejects either fixture fails here."""

    def test_spec_fixture_passes(self):
        text = (Path(orko.__file__).parent / "fixtures/spec.md").read_text(encoding="utf-8")
        assert orko.validate_spec(text) == []

    def test_plan_fixture_passes(self):
        text = (Path(orko.__file__).parent / "fixtures/plan.md").read_text(encoding="utf-8")
        assert orko.validate_plan(text) == []

    def test_fixtures_carry_no_stale_run_paths(self):
        for name in ("spec.md", "plan.md"):
            text = (Path(orko.__file__).parent / f"fixtures/{name}").read_text(encoding="utf-8")
            assert "docs/sessions/" not in orko.strip_code(text).replace(
                "`docs/sessions/`", ""), name
```

The third test tolerates the spec's own backticked mention of the old path; `strip_code` already removes inline code, so the `.replace` is belt and braces.

- [ ] **Step 3: Run the tests**

Run: `uv run --with pytest pytest orko/scripts/test_orko.py::TestFixtures -q`
Expected: PASS. If `test_plan_fixture_passes` fails, the finding names the line; fix the plan in the workshop, re-copy, and re-run. Do not weaken the validator.

- [ ] **Step 4: Commit**

```bash
git add orko/scripts/fixtures orko/scripts/test_orko.py
git commit -m "test(orko): pin the validators to the v2 spec and plan as real fixtures"
```

---

### Task 9: `references/build.md` and `references/linear.md`

**Files:**
- Create: `orko/references/build.md`
- Create: `orko/references/linear.md`

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Consumes: every CLI surface from Tasks 2 through 7, named exactly as implemented.

- [ ] **Step 1: Write `orko/references/build.md`**

Write the file with these sections, in this order. Each section's content is specified; write it as prose, not as a copy of this list.

1. **Title and purpose.** "Build engagement" and one paragraph: the conductor runs intake through close; seats report, the conductor decides, Linear records.

2. **Startup sequence.** Five numbered steps, adapted from autonom's startup with the v2 commands:
   - Establish the run repository: `cd` to it, print `git rev-parse --show-toplevel`, confirm it with oiler. Confirm the repo is writable while a human is present. Carry autonom's paragraph on why a permission stall inside a dispatch is invisible.
   - Look for an existing run: `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py status`. Resume when a topic matches; pass the `topic` string verbatim.
   - Ask the one onboarding round: target repo confirmation, boundaries, and **checkpoint** (stop after plan review) or **auto** (continue into `superpowers:subagent-driven-development`). Ask nothing else.
   - Create or resume: `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py init build "<goal>" --team <KEY>`. Read every path from the JSON. Never construct a path. Topic-string guidance: the goal in one sentence, no trailing punctuation, no file paths; it becomes the slug and the Project name.
   - Branch: `git checkout -b orko/<slug>` on a new run, `git checkout orko/<slug>` on a resume. Then `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py preflight --slug <slug>`; exit `1` stops intake.
   Then the resume reconciliation paragraph: on a resume, run `status <slug>`; a `dispatched` last status means a review round may already have delivered findings files, so check `findings/` before re-dispatching; run `escalations <slug>` before authoring anything.

3. **Why two stock gates are skipped.** autonom's "Why this supersedes two stock gates" section, verbatim, with `autonom` replaced by `orko build` and "the `/autonom` invocation" replaced by "the `/orko build` invocation and the intake answers".

4. **The steps.** One subsection per step 0 through 7. Each names the ledger step, the exact commands, the dispatches, and the Linear posts. Required content per step:
   - **0 Intake.** After preflight passes: `post project --slug <slug> --goal "<goal>" --boundaries "<boundaries>" --branch orko/<slug>`, call the tool with the emitted `args`, run the `then` command with the returned id. `ledger 0 complete`.
   - **1 Spec.** Author `<run_dir>/spec.md` in the shape the validators require (link to the validator section). `validate spec <path>`; one repair on exit `1`. `post document spec`, run `then`. `ledger 1 complete`.
   - **2 Spec review.** Pick lenses (default all four). For each: `prompt spec-review <slug> --lens <lens>`, dispatch `general-purpose` at `opus` with the stdout as the entire prompt, all in one message. Delivery check per seat; re-dispatch once with the same prompt; record a seat that fails twice as failed in the step summary. Then, per finding in each findings file: decide handled, deferred, rejected, or blocked; for handled, edit the spec; `post finding --seat <lens> --outcome <o> --title "<title>"` with the evidence and reasoning on stdin; call the tool. For blocked use `post escalation`, then `ledger 2 complete`, `ledger 2 escalated`, and stop. Otherwise `validate spec` again, `post document spec` (updates in place), `ledger 2 complete`.
   - **3 Plan.** `prompt plan-write <slug>`, dispatch one `general-purpose` seat at `opus`. Delivery check. Edit the draft. `validate plan`. `post document plan`, run `then`. `ledger 3 complete`.
   - **4 Plan review.** As step 2 with `prompt plan-review` and the plan lenses (default all four).
   - **5 Execute.** Checkpoint mode: print the plan path, the Linear Project URL, and the instruction to resume with `superpowers:subagent-driven-development` and the plan path; `ledger 5 complete` is recorded by the resumed session after SDD finishes. Auto mode: invoke `superpowers:subagent-driven-development` with the plan path; when it returns, `ledger 5 complete`. An SDD escalation (a task it cannot complete within boundaries) becomes `post escalation --seat implementer` and stops the run.
   - **6 Code review.** Dispatch review seats over `git diff master...HEAD` (or the branch's merge base): one seat that runs `/code-review`, one that runs `/security-review`, both at `opus`, plus any domain seats at `sonnet` via `prompt seat` with a context file naming the diff range. Decide per finding as in step 2; handled findings are fixed on the branch by dispatching an implementer, not by the conductor editing code. `ledger 6 complete`.
   - **7 Close.** `post close --slug <slug> --summary "<summary>" [--pr <url>]`. `ledger 7 complete`. Print the Project URL, the branch, and the count of issues by outcome.

5. **What the validators require.** autonom's section verbatim, including the fenced-marker rule and the note that `Todo` inside prose is a validator hit.

6. **Reading the script's exit codes** and **Ledger statuses.** autonom's two sections verbatim with step numbers removed from examples.

7. **Error handling.** The spec's error table, as a markdown table.

8. **Ending.** Three cases: checkpoint, auto, outstanding escalation. autonom's rule that an outstanding escalation prints no resume-into-implementation line.

9. **Narration.** autonom's paragraph verbatim.

- [ ] **Step 2: Write `orko/references/linear.md`**

Sections:

1. **The contract in one paragraph.** Linear is the record; git is for code; the script emits payloads, the conductor sends them, seats never write to Linear.

2. **Entities.** A table: Project (one per engagement, name is the slug, team from `init --team`), Documents (`Spec`, `Plan` for build; `Brief`, `Synthesis` for analysis), Issues (one per decision), Label `blocked`.

3. **Posting protocol.** Every `post` prints `{"posts": [...]}`. For each entry in order: call the tool named in `tool` with exactly the object in `args`; if `then` is non-null, run it as an `orko.py` command with `<returned id>` replaced by the id the tool returned. Never add, drop, or rename an `args` key. If a call fails, retry once; on the second failure write the whole `posts` object to `<run_dir>/unposted/<step>-<n>.json` with Write, record `ledger <step> failed`, and stop.

4. **The four outcomes.** The spec's table with states in backticks and a sentence on what each description must contain. Reviewer findings are decisions: one issue per finding, never one per seat.

5. **Attribution.** `post finding` cannot run without `--seat`, and the first line of every issue description is `Seat: <seat>`. Conductor-originated decisions use `--seat conductor`. Implementer escalations from SDD use `--seat implementer`.

6. **Analysis engagements.** At Open: `init analysis`, `post project` (no `--branch`), `post document brief`. At Synthesize: one `post finding` per verified finding. Where a verdict corrected a seat, the issue body carries the corrected version first and the seat's original in a quoted block under "Seat's original, corrected by verifier". Outcome mapping for analysis: confirmed findings the user should act on are `deferred` (`Backlog`), findings the verifier struck are `rejected` (`Canceled`), and a finding that changes the engagement's question is `blocked`. Then `post document synthesis` and `post close`.

7. **Reconstruction.** Everything needed to rebuild a lost run directory is in the Project description and its documents; `status` prints the recorded ids; `get_project` and `get_document` fetch them. `post project` re-sends the description on every call, so run it before `post close` if boundaries or branch changed.

8. **Smoke engagements.** A smoke run creates a real Project like any other. Archive it after the evidence report is bound; never delete it, because the report links to it.

- [ ] **Step 3: Check both files against the script**

Run each command string that appears in the two files with `--help` to confirm the subcommand and flags exist:

```bash
for cmd in "init --help" "status --help" "ledger --help" "validate --help" "prompt --help" "escalations --help" "linear set --help" "linear get --help" "post project --help" "post document --help" "post finding --help" "post escalation --help" "post close --help" "preflight --help"; do
  uv run orko/scripts/orko.py $cmd > /dev/null || echo "MISSING: $cmd"
done
```

Expected: no `MISSING` lines.

- [ ] **Step 4: Commit**

```bash
git add orko/references/build.md orko/references/linear.md
git commit -m "docs(orko): build lifecycle and Linear contract references"
```

---

### Task 10: `SKILL.md`, `upgrades.md`, and the analysis lifecycle update

**Files:**
- Modify: `orko/SKILL.md`
- Modify: `orko/references/upgrades.md`

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- Consumes: `references/build.md`, `references/linear.md`, `references/seats.md` and the CLI.

- [ ] **Step 1: Rewrite the frontmatter**

```yaml
---
name: orko
description: >-
  Run an on-demand multi-expert engagement with Linear as the record. Two
  engagement types under one conductor: `/orko <question>` decomposes an
  analysis, review, audit, or research task into role-specialized expert seats,
  dispatches each to a tier-appropriate model, verifies findings with a
  fresh-context check, and reports an attributed synthesis; `/orko build <goal>`
  runs a full build — intake, spec, spec review, plan, plan review, execution via
  subagent-driven-development, code review, close — with report-only reviewer
  seats and one Linear issue per decision. User-invoked. Use when asked to
  coordinate experts, run a multi-expert review, assemble a panel, get attributed
  findings, or run a build engagement, orko build, or the spec-to-code pipeline
  (this replaces the retired autonom skill). NOT for independent parallel tasks
  with no shared synthesis (use dispatching-parallel-agents), executing an
  already-written plan (use subagent-driven-development directly), or routing
  within one thread to a single domain skill.
disable-model-invocation: true
argument-hint: "[question] | build <goal> [init docs]"
allowed-tools: >-
  Agent Task Read Write Edit Grep Glob Skill
  Bash(uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py *)
  Bash(git rev-parse *) Bash(git log *) Bash(git status *) Bash(git diff *)
  Bash(git checkout -b orko/*) Bash(git checkout orko/*) Bash(git branch *)
  mcp__linear__save_project mcp__linear__get_project
  mcp__linear__save_document mcp__linear__get_document
  mcp__linear__save_issue mcp__linear__get_issue mcp__linear__list_issues
  mcp__linear__save_issue_label mcp__linear__list_issue_labels
  mcp__linear__save_comment
metadata:
  author: oiler
  version: 1.0.0
---
```

Confirm the description is under 1,536 characters:

```bash
python3 -c "import re,sys; t=open('orko/SKILL.md').read(); d=re.search(r'description: >-\n((?:  .*\n)+)', t).group(1); print(len(' '.join(l.strip() for l in d.splitlines())))"
```

- [ ] **Step 2: Rewrite the body**

Keep these v1 sections with the edits named, and add the new ones. Target under 300 lines total.

- **orko** (intro): one paragraph; add "Two engagement types, one conductor, one record in Linear."
- **When to use**: keep the table; add a row "A goal to build from spec through code review | `/orko build <goal>`". Keep the "what orko buys" paragraph.
- **The conductor**: keep verbatim.
- **The script** (new, short): `scripts/orko.py` owns paths, the ledger, validators, every dispatch prompt, and every Linear payload. Prose is yours; structure is the script's. Every command in this skill is `uv run ${CLAUDE_SKILL_DIR}/scripts/orko.py <subcommand>`; if `${CLAUDE_SKILL_DIR}` is empty in a Bash call, use `~/.claude/skills/orko/scripts/orko.py`. Exit codes `0`, `1`, `2` and what each means, three lines.
- **Analysis engagement** (renamed from "The engagement protocol"): keep the seven steps, with these changes. Step 1 Open adds: `init analysis "<question>" --team <KEY>`, then `post project` and send it. Step 2 Propose writes `brief.md` to the run dir path from `init` and posts it with `post document brief`. Step 3 Dispatch: seat prompts come from `prompt seat` with a context file the conductor writes to `<run_dir>/context/<seat>.md`; drop the "use the dispatch template" wording. Step 4 Verify: verifier prompts from `prompt verifier`; re-dispatch re-runs the same command. Step 5 Synthesize adds: one `post finding` per verified finding per `references/linear.md`, then `post document synthesis`. Step 7 Close: `post close`. Record `ledger <n> complete` at each step. Keep the delivery-check, latency, and blind-re-dispatch rules verbatim.
- **Build engagement** (new): the lifecycle table from the spec (steps 0 to 7, columns Step / Conductor / Dispatches / Linear), the sentence on post-intake authority and the two skipped gates, the report-only reviewer rule, review seats at `opus` with the reason, and a pointer: "Step-by-step commands, the validator contract, error handling, and ending rules: `references/build.md`. Read it before step 0."
- **Model tiering**: keep the table; add a row "Spec and plan review seats, plan-writer, the two tool-running code-review seats | `opus` — the judgment-heavy steps of a build; say so at the gate" and keep the default-down paragraph.
- **Paper trail and record** (replaces "Paper trail"): the `.orko/<slug>/` tree from the spec; `init` gitignores it; seats write to the absolute paths the prompts carry; Linear is the record and `references/linear.md` is the contract. Remove the `.gitignore` editing instructions; the script does it.
- **Limits**: keep, and change the first bullet's pointer to `references/upgrades.md`; add "The script cannot call Linear. Every payload passes through you, and only the written contract stops you from altering it."
- **More**: list `references/seats.md`, `references/build.md`, `references/linear.md`, `references/upgrades.md`.

- [ ] **Step 3: Rewrite the v2 section of `references/upgrades.md`**

Replace everything from `## Build engagement (v2, agreed design — not yet built)` to the end of the file with:

```markdown
## Build engagement (shipped in v1.0.0)

The build engagement designed here on 2026-09-04 shipped as orko v1.0.0. The lifecycle lives in `build.md`, the Linear contract in `linear.md`, and the script surface in `scripts/orko.py --help`. Two design points worth keeping in view:

- **Linear is the record, git is for code.** Artifacts never commit. Every decision kicked up to the conductor is one issue with one of four outcomes; reviewer findings are decisions under that rule. Seats never write to Linear; the conductor posts, attributed by seat, from payloads the script emits.
- **The judge is tuned per task.** Analysis gets a prose verifier. Code gets a judge that runs the tests: when the conductor dispatches competing implementations for one task, it keeps the candidate whose patch passes the suite and records the other as rejected.
```

- [ ] **Step 4: Verify line count, paths, and style**

```bash
wc -l orko/SKILL.md
grep -rn "docs/sessions\|\.superpowers\|autonom\.py\|docs/superpowers" orko/ && echo "STALE PATHS" || echo "clean"
grep -rn '\$(' orko/SKILL.md orko/references/build.md && echo "COMMAND SUBSTITUTION" || echo "clean"
```

Expected: under 300 lines; `clean` twice. The only permitted mention of `autonom` in `orko/` is the description's "replaces the retired autonom skill" and the upgrades history.

- [ ] **Step 5: Commit**

```bash
git add orko/SKILL.md orko/references/upgrades.md
git commit -m "feat(orko): v1.0.0 SKILL.md with analysis and build engagements on a Linear record"
```

---

### Task 11: Deprecate autonom, changelogs, and workshop pointers

**Files:**
- Modify: `autonom/SKILL.md` (replace with the stub)
- Modify: `docs/changelogs/orko.md`
- Modify: `docs/changelogs/autonom.md`
- Delete: `autonom/.pytest_cache/`, `autonom/scripts/` leftovers if any remain untracked
- Modify (workshop repo): `/Users/jrf1039/files/projects/001-claude-skills-creator/docs/workshop-state.md`

**Acceptance:** `uv run pytest -q`

**Interfaces:**
- None consumed; this task is documentation and cleanup.

- [ ] **Step 1: Replace `autonom/SKILL.md` with the stub**

```markdown
---
name: autonom
description: >-
  Retired. The unattended spec-and-plan pipeline moved into orko as
  `/orko build <goal>`. Use ONLY when explicitly invoked as /autonom; it prints
  the redirect and does nothing else. Last full version: autonom-v0.1.0.
disable-model-invocation: true
metadata:
  author: oiler
  version: 0.2.0
---

# autonom (retired)

autonom's relay — author spec, review spec, author plan, review plan, then stop or continue into `superpowers:subagent-driven-development` — now runs as the build engagement of the `orko` skill. Invoke `/orko build <goal>` instead. Reviewer seats there are report-only and every decision lands as a Linear issue; see `orko/references/build.md`.

Nothing else in this folder is live. The last full release is tagged `autonom-v0.1.0`; its evidence reports remain under `evals/autonom/`.

Tell the user this skill is retired and name the replacement. Do not run any pipeline.
```

```bash
rm -rf autonom/.pytest_cache autonom/scripts autonom/.DS_Store
git add -A autonom
```

- [ ] **Step 2: Changelog entries**

Prepend to `docs/changelogs/orko.md` under the title:

```markdown
## v1.0.0 — 2026-09-04

Build engagement and a Linear record. Folds the `autonom` skill into orko. Breaking: the run directory moves from `docs/sessions/<slug>/` to `.orko/<slug>/`, and Linear replaces the disk trail as the record for both engagement types.

### Added

- `/orko build <goal>`: intake, spec, spec review, plan, plan review, execute via `subagent-driven-development`, code review, close. Reviewer seats are report-only; the conductor is the only writer to artifacts and to Linear.
- `scripts/orko.py` (from `autonom.py`): `init <mode> --team`, per-mode ledger steps, `linear set|get`, `post project|document|finding|escalation|close`, `prompt spec-review|plan-review|plan-write|seat|verifier`, `preflight`.
- Every decision kicked up to the conductor is one Linear issue with one of four outcomes: handled (`Done`), deferred (`Backlog`), rejected (`Canceled`), outside boundaries (`Todo` + `blocked`, run stops).
- Analysis seat and verifier prompts are now script-emitted (determinism tier 1, up from tier 2).
- Validators pinned to real fixtures under `scripts/fixtures/`.

### Changed

- Spec and plan live in the run directory as working copies and in Linear as documents. Nothing commits to the target repository except code.
- Review seats run at `opus`; verifiers are not dispatched on review seats because the conductor's per-finding decision is the check, and it is recorded.

### Removed

- Reviewer write authority and the separate-review-commit safeguard that existed for it.
- `docs/sessions/` trail and the `.gitignore` editing instructions; `init` gitignores `.orko/`.

### Fixed (from the autonom v0.2.0 backlog)

- Escalation gate is unambiguous: a blocked finding stops the run before the next step in both modes, and `preflight` reports a non-empty `escalations.md` on resume.
- `${CLAUDE_SKILL_DIR}` empty in Bash: documented fallback to `~/.claude/skills/orko/scripts/orko.py`.
- Topic-string guidance in `references/build.md`.
```

Prepend to `docs/changelogs/autonom.md` under the title:

```markdown
## v0.2.0 — 2026-09-04

Retired. The skill is now a redirect stub pointing at `/orko build`. Scripts, references, and tests moved to `orko/` (see orko v1.0.0). Evidence reports under `evals/autonom/` are kept as history.
```

- [ ] **Step 3: Workshop decision entry**

Append one bullet to the end of the `## Decisions worth remembering` list in `/Users/jrf1039/files/projects/001-claude-skills-creator/docs/workshop-state.md` (the list is bold-lead bullets, one per decision, no sub-headings):

```markdown
- **Linear is the record, git is for code (2026-09-04)** — product artifacts a skill produces during an engagement (briefs, specs, plans, syntheses, decisions) go to Linear: one Project per engagement, documents for artifacts, one issue per decision with a fixed outcome vocabulary (handled / deferred / rejected / blocked). Project repos receive code and the documentation that supports the code, nothing else. A script that cannot call Linear emits payloads and the conductor sends them verbatim, so every side effect is in the transcript. First applied in orko v1.0.0, which absorbed autonom; canonical statement in `orko/references/linear.md`.
```

Also update the `### \`orko\`` entry under `## Per-skill notes` to say v1.0.0 added the build engagement and retired autonom, and update `**Last reviewed:**` to 2026-09-04.

- [ ] **Step 4: Full suite and a final grep**

```bash
uv run --with pytest pytest orko/scripts/test_orko.py -q
git status --short
```

Expected: all tests pass; only intended files modified.

- [ ] **Step 5: Commit**

```bash
git add autonom docs/changelogs/orko.md docs/changelogs/autonom.md
git commit -m "chore(autonom): retire as a redirect stub; changelogs for orko v1.0.0 and autonom v0.2.0"
cd /Users/jrf1039/files/projects/001-claude-skills-creator && git add docs/workshop-state.md && git commit -m "docs: workshop-state — Linear is the record, git is for code"
```

---

## After the plan: eval and release (owned by /skill-creator, not by this plan)

These steps are the skill-creator eval and distribution phases and run after Task 11 with the branch complete.

1. Clean-room smoke: a subagent that has read only `orko/` runs `/orko build` in checkpoint mode against a throwaway repo with a two-task goal, and a second runs `/orko <question>` against the same repo. Both create real Linear Projects on JRF. Report to `evals/orko/smoke-2026-09-<dd>.md` with `satisfies: [live-engagement, clean-room]`, Project URLs recorded, Projects archived afterwards.
2. Release gate: from a neutral cwd, `PYTHONPATH=<workshop>/tools/skill-evals python3 -m scripts.preflight orko --change-class structural --candidate-version 1.0.0 --out ~/files/repo/claude-skills/evals/orko/preflight_1.0.0.json`, and the same for `autonom --change-class trivial --candidate-version 0.2.0`.
3. Merge `feat/orko-v2` to `master`, tag `orko-v1.0.0` and `autonom-v0.2.0`, GitHub releases per skill.
4. `rm ~/.claude/skills/autonom`. Regenerate `docs/library-status.md` in the workshop.
