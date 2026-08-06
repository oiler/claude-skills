---
instrument: clean-room
satisfies: [clean-room]
skill_content_hash: a3c6f383c2842dcb8f813eb911af22be8cf2037a6b35556dc2713ab56fad5f4c
repo_commit: 6de8ac91222b8ea6568f0609ad7f5e7d1b8c45ab
date: 2026-08-05
verdict: pass
---

# claude-cowork-builder v0.4.0 — clean-room smoke report

## Task given (verbatim)

> Execute the skill's workflow end-to-end on this task, in the workspace
> /Users/jrf1039/files/projects/001-claude-skills-creator/.workspaces/cowork-builder-v0.4.0/clean-room/: A nontechnical customer-success lead wants a Cowork plugin that drafts quarterly business review briefs from meeting notes in the working folder. Build it end-to-end: charter, distribution decision, component plan, scaffold, author the skills, audit, and package to a .plugin.

Sources available to this run: only the files under `/Users/jrf1039/files/repo/claude-skills-v040/claude-cowork-builder`. No workshop docs, specs, plans, git history, or evals were read.

## What happened

Read `SKILL.md`, then every file it routes to: all eight `references/*.md`, all nine `assets/templates/*`, `scripts/validate_plugin.py`, and `integrations/google-drive/recipe.md` plus its two fragments. The build menu resolved to **entry 1 (New plugin from scratch)**, so the full Phase 0→5 spine ran.

### Phase 0 · Charter

A customer-success lead needs a quarterly business review brief written for each account from the meeting notes accumulated over the quarter. Audience is nontechnical — a CS lead in Cowork, not an operator. External tools touched: none required (notes live in the working folder); an optional file-storage connector is the additive path. Invocation is interactive, not scheduled — decided in Phase 2 and stated in the README, because the charter's working-folder input has no scheduled-run equivalent (`cowork-runtime.md` § Scheduled tasks).

### Phase 1 · Distribution

Both defaults taken together per the coupling rule: **Private + Individual → concrete config**. Repo shape is plugin-is-its-own-repo, which makes the Makefile the packaging path (Phase 4 step 6) and, per `distribution.md` §4 / item 10, the **self-marketplace** the default layout. So the plugin ships `.claude-plugin/marketplace.json` beside `plugin.json` with `source: "./"`. `~~category` tokens stay in the skill bodies at this profile on purpose (the standalone/supercharged mechanism), and no `~~` token appears in any `description`.

### Phase 2 · Component plan

| Component | Included? | Reason |
|---|---|---|
| Command skill(s) | Yes | `draft-qbr-brief` (the deliverable) and `check-qbr-note-coverage` (readiness before drafting) |
| Knowledge skill(s) | Yes | `qbr-brief-standards` — the pairing idiom; section structure and sourcing rules, `user-invocable: false` |
| Router skill | No | Skill count 3, below the house threshold of 8 |
| Agent | No | Linear, short, single-source work — none of the four `agent-playbook.md` §2 shapes; gate fails |
| MCP connector | Yes | One category, `~~file storage`, shipped as the empty-url native-connector stub |
| Custom UI | No | A one-off brief is a file the skill writes; `live-artifacts.md` §3 row one says neither surface |
| Mutable state | None | `qbr-preferences.md` is user-owned config the plugin reads and never writes; briefs are immutable dated outputs |

Cowork gates recorded: (a) the native file-storage tool surface is create-and-read only — fallback is that the brief always lands in the working folder and connected-storage filing only ever creates a new dated file; (b) whether a session has a working folder at all — fallback is the paste/upload path with a session deliverable.

### Phase 3 · Component design

Triggers, inputs, and the standalone/supercharged split specified per command skill; no `references/` needed at this size (depth lives in the paired knowledge skill); no tool scoping (no agents). Deliberate call: **no MANDATORY FIRST STEP working-folder guard**, because the guard would dead-end the web/mobile path that `cowork-runtime.md`'s design floor requires, and the skill writes exactly one new dated file with no overwrite risk.

### Phase 4 · Scaffold

```
qbr-brief-builder/
├── .claude-plugin/{plugin.json, marketplace.json}
├── skills/{draft-qbr-brief, check-qbr-note-coverage, qbr-brief-standards}/SKILL.md
├── .mcp.json
├── CONNECTORS.md
├── README.md
└── Makefile          (copied verbatim from assets/templates/)
```

All names kebab-case. Both command skills carry the seven template sections in order, the CONNECTORS banner, and exactly one `## With ~~file storage connected` section. No intra-plugin runtime file operations exist, so no `${CLAUDE_PLUGIN_ROOT}` reference was needed.

### Phase 5 · Audit + package

`uv run …/scripts/validate_plugin.py ./qbr-brief-builder` → `profile: self-marketplace (marketplace.json beside plugin.json)` / `script checks: all pass`, exit 0 on the first run.

Both CLI forms, as item 2 mandates on a self-marketplace:

- `claude plugin validate . --strict` → `Validating marketplace manifest` … `✔ Validation passed`
- `claude plugin validate ./.claude-plugin/plugin.json --strict` → `Validating plugin manifest` … `✔ Validation passed`

(CLI 2.1.223.)

Judgment items walked: 0 no deviations file and none warranted; 3 all three descriptions third-person, trigger-dense, `Use when…`; 4 SKILL.md files 52/62/36 lines, routing-shaped; 5 both command skills carry a working zero-connector floor plus the never-degrade-silently clause for a configured-but-unreachable connector; 6 `~~file storage` verified identical across body / CONNECTORS Placeholder column / README MCP section / `.mcp.json` entry, `*` footnote defined in both files that carry a `*`, no `~~` in any description; 7 working folder, no relative paths, no `open`/`xdg-open`, path told last, no-folder mode covered; 8 no hardcoded `/Users/` or `/home/`, no runtime intra-plugin paths at all; 9 no secrets, no `${VAR}` references, stub URL is not a plaintext remote, no agents, no artifacts; 11 two command skills with disjoint trigger territory, no scratch directories; 12 judged exempt (see below); 14 no in-place connector writes anywhere.

Packaging via the shipped Makefile (item 13, plugin-is-its-own-repo): `git init` + one commit, then `make verify` →

```
Built dist/qbr-brief-builder-0.1.0-c853420.plugin  (v0.1.0, HEAD=c853420, 12K)
verify OK: dist/qbr-brief-builder-0.1.0-c853420.plugin is well-formed and leaked nothing
```

15 entries, `.claude-plugin/plugin.json` at the archive root, denylist clean.

## Ambiguities and guesses

1. **CONNECTORS banner placement — the reference and the template disagree.** `skill-authoring.md` § The CONNECTORS.md banner says the line is emitted "near the top of its body (after `## Trigger`, before the skill gets into its own process)". `assets/templates/command-SKILL.md` puts it *before* `## Trigger`, directly under the H1. **Guessed: followed the template**, on the grounds that the same reference calls the template the canonical shape that "reproduces it exactly" and says the template keys off section order.

2. **`${CLAUDE_SKILL_DIR}` is never defined in the shipped files.** Both `build-spine.md` Phase 5 and `audit-checklist.md`'s header give the validator invocation as `uv run ${CLAUDE_SKILL_DIR}/scripts/validate_plugin.py <plugin-dir>`, but the skill's Hard rules define only `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`, and nothing explains what sets `CLAUDE_SKILL_DIR` or whether it is available. **Guessed: substituted the literal absolute path to the skill directory.**

3. **Which layout the Phase 1 "Individual" default actually implies.** Phase 1 defaults install to Individual, and `distribution.md` §3 presents the bare no-marketplace tree as the `private-individual` profile. But item 10 and §4 say a private plugin *that is its own repo* defaults to the self-marketplace, and Phase 4 step 6 makes plugin-is-its-own-repo the default packaging path — so the default build lands on a layout the Phase 1 default never names. §3 does reconcile it ("different install mechanisms, both valid for a private plugin"), three references away from the decision point. **Guessed: self-marketplace**, because the packaging default implies the repo shape that triggers it.

4. **Where `marketplace.json` gets written.** Phase 4's order of operations (steps 1–6) never mentions it. **Guessed: alongside `plugin.json` in `.claude-plugin/`**, from §4 and the validator's `infer_profile`.

5. **Progressive disclosure when the pairing idiom is used.** Audit item 4 says detail is "pushed into `references/`". This plugin's depth lives in a paired knowledge skill instead, which is the shape `skill-authoring.md` calls "the default shape for anything with real depth". **Guessed: the pairing idiom satisfies item 4's intent** (SKILL.md as router, not manual).

6. **"Tell the user the path" vs. "no file paths."** § Cowork output hygiene requires "a real, resolved path rooted in the working folder" and "tell the user the path"; § Nontechnical voice forbids paths in user-facing copy and models the reply as "I've saved this to your working folder as `summary.md`". `SKILL.md`'s hard rule splits the difference ("the exact path — or file name"). **Guessed: instruct the skill to name the folder and the file name, not an absolute path string.**

7. **The charter is folder-shaped; the design floor says don't be.** `cowork-runtime.md` states a plugin "should be fully useful from web/mobile — which means connector-fed or paste/upload-fed, not local-folder-dependent," but the requested plugin's stated input is the working folder. No reference covers that collision. **Guessed: working folder as the default source, paste/upload + session deliverable as an equal-status branch, and non-schedulability stated plainly in the README.**

8. **The MANDATORY FIRST STEP guard has no tiebreaker for input-side folder dependence.** The guidance keys the guard to *output* risk ("writes many files, could overwrite existing work"). A skill whose *input* lives in the working folder is not addressed. **Guessed: no guard**, since it would dead-end the web/mobile path required by finding 7.

9. **Item 12's "finance" boundary.** A QBR brief carries renewal, ARR, and commercial-risk content. Nothing in the checklist says whether "finance" means financial advice or any financial subject matter. **Guessed: exempt** — no investment/legal/medical advice is given — and hardened the never-invent-a-metric rule in the knowledge skill instead of adding a disclaimer.

10. **Minor.** Audit item 6 names "the 'connectors this plugin uses' section of `README.md`"; `assets/templates/README.md` calls that section `## MCP Integrations` and only reconciles the two inside an HTML authoring comment that the template tells you to delete. A builder working from the checklist alone would guess the heading.

## Defects found

- **D1 — Contradiction, banner placement.** `skill-authoring.md` § The CONNECTORS.md banner ("after `## Trigger`") vs. `assets/templates/command-SKILL.md` (before `## Trigger`). One of the two is wrong; a builder following the reference produces files that disagree with the shipped template. Severity: low mechanically, but it is a verbatim-block rule, and verbatim rules that disagree with the artifact they govern erode the determinism claim.
- **D2 — Omission, Phase 4 scaffold order.** The six-step order of operations in `build-spine.md` Phase 4 emits no `marketplace.json`, even though on the default layout (plugin-is-its-own-repo, step 6) audit item 10 expects one and the validator's profile inference keys on it. Following Phase 4 literally scaffolds a plugin that item 10's own default-layout sentence says is incomplete. Fix: add it as step 2b, conditioned on the Phase 1 outcome.
- **D3 — Undefined variable in an executable instruction.** `${CLAUDE_SKILL_DIR}` appears in the two places that tell you how to run the validator and is defined nowhere in the skill. The skill is explicit that plugin-root references use `${CLAUDE_PLUGIN_ROOT}`; this second variable arrives unexplained in the one command the operator must actually run.
- **D4 — Audit item 4 hardcodes `references/`.** It cannot express the pairing idiom the skill itself calls the default shape for depth, so a correctly-built plugin reads as a partial miss on item 4.

Nothing above blocked a phase. No defect surfaced in the validator, the Makefile, or the templates' emitted structure.

## Verdict rationale

**Pass.** Every phase of the documented spine completed as written, from a cold read of the shipped files only. Phase 5's two authorities both returned clean on the first attempt with no rework: `validate_plugin.py` exited 0 (`script checks: all pass`) and `make verify` produced `dist/qbr-brief-builder-0.1.0-c853420.plugin` with the manifest at the archive root and the denylist clean; both mandated `claude plugin validate --strict` forms passed. The deterministic surfaces — templates, validator, Makefile — did their jobs without interpretation, which is the load-bearing part.

The four defects are documentation defects: one internal contradiction, one omitted scaffold step, one undefined variable, one checklist item too narrow for the skill's own recommended shape. Each cost a decision, none cost a step. The nine ambiguities are mostly judgment calls the skill deliberately leaves open, and in every case except D1–D4 the files gave enough to decide — several of them (the Phase 1/item 10 layout question, the path-vs-no-path tension) are reconciled in the text, just at a distance from the point of use.
