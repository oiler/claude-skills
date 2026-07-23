# Cowork Builder — Connector Route Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Also required:** this plan edits a skill (claude-cowork-builder). The implementing session must invoke `superpowers:writing-skills` before editing any skill file, and follow its verification guidance.

**Goal:** Make the builder skill teach exclusive connector route binding — every plugin built with it uses exactly the declared connector for a product family (Google Drive first), with named fences against every alternative route and a scripted hand-off at the connector's capability boundary.

**Architecture:** Doc-only changes to `claude-cowork-builder` — one new generic section in `references/connectors-and-mcp.md` (route binding), one new behavior rule in its native-connectors section (capability-boundary hand-off), one new consequence bullet in `references/skill-authoring.md` (scripted edit flow for user-owned config), a new copyable I/O-contract fragment in `integrations/google-drive/` wired into the recipe, one-line fences in the two starter skills, and a new Phase 5 audit item. No Python, no schema changes.

**Tech Stack:** Markdown reference docs in `~/files/repo/claude-skills/claude-cowork-builder/`. Verification is grep + read-through; there is no test framework for these docs.

## Production evidence motivating this plan (context for every task)

A sitecheck (Drive-backed Cowork plugin, built with this builder) live session on 2026-07-23: the user asked to add a site; the plugin's design makes the config Sheet user-edited and read-only to the plugin; the runtime, unable to edit a Sheet cell through the create-and-read-only native connector, went shopping for another write path, settled on the Chrome browser extension, found it unconnected, and told the user: *"the Chrome extension isn't connected in this session, so I couldn't add the row to your shared config Sheet myself."* Three defects in one sentence: an undeclared route was treated as legitimate, a by-design boundary was framed as the plugin's failure, and which route gets tried varies per session — nondeterminism. The builder currently has no rule against any of this; these tasks add it.

## Global Constraints

- Follow the existing voice and conventions of the builder's reference docs: rules stated as imperatives, production origins cited in parentheses, cross-references by `` `file.md` § Section name ``.
- New prose is NOT hard-wrapped — one line per paragraph/bullet, even though some existing files in this repo wrap at ~75 columns (oiler's global instruction overrides local file style; do not re-wrap existing text you aren't otherwise editing).
- `~~category` tokens appear in skill bodies only, never in `description` frontmatter (existing rule — `connectors-and-mcp.md` § The `~~category` system).
- Section names introduced here are load-bearing cross-references. Use exactly: `Route binding — one category, one route` (connectors-and-mcp.md) and the audit item title `Route binding fenced.` Any deviation must be applied everywhere in the same pass.
- Commit style (from repo history): `feat(claude-cowork-builder): <what>` for rule additions, `docs(claude-cowork-builder): <what>` for changelog.
- Work on `master` unless the repo's current branch says otherwise; one commit per task.

---

### Task 1: Generic route-binding rule in connectors-and-mcp.md

**Files:**
- Modify: `claude-cowork-builder/references/connectors-and-mcp.md` (insert a new `##` section between `## The ~~category system` and `## CONNECTORS.md — the lookup table`, i.e. after current line 50)

**Interfaces:**
- Produces: section heading `## Route binding — one category, one route`, referenced by Tasks 2, 3, 4, 5, 6 as `` `connectors-and-mcp.md` § Route binding ``.

- [ ] **Step 1: Confirm the section doesn't already exist**

Run: `grep -n "Route binding" ~/files/repo/claude-skills/claude-cowork-builder/references/connectors-and-mcp.md`
Expected: no output.

- [ ] **Step 2: Insert the new section**

Insert immediately before the line `## CONNECTORS.md — the lookup table`:

```markdown
## Route binding — one category, one route

A `~~category` token is an exclusive binding, not a hint. When a skill names `~~file storage`, every read and write to that product family goes through the connector `CONNECTORS.md` maps for that category — and through nothing else. A live session may expose other tools that can reach the same product: a browser or browser extension that can drive its web UI, a locally-synced folder that mirrors it on disk, a generic web-fetch tool that can hit its URLs. To the skill, those routes do not exist.

Why this must be written down: a runtime agent holding a goal and an unfenced toolbox shops for whichever tool completes the goal — and which tools a session exposes varies, so unfenced access is nondeterministic access. (Production origin: a Drive-backed plugin's runtime, unable to edit a Sheet cell through the create-and-read-only native connector, reached for a browser extension it noticed in the session, found it unconnected, and reported that absence to the user as the plugin's failure.)

Rules for the consuming plugin:

- **State the I/O contract in the main skill body.** One short block per connector category enumerating every operation the plugin performs through it — reads and creates, named concretely ("read the config Sheet's two tabs", "create dated Docs in `reports/`"). Anything not listed is out of scope by design, not an unmet need.
- **Fence the alternative routes by name.** The contract block names what the skill must never use for that product family: browser or extension automation against the product's web UI, reading or writing a locally-synced mirror folder, fetching the product's URLs with a generic web-fetch tool. A bare "use only the connector" does not hold at runtime; the forbidden routes must be named.
- **A capability the connector lacks is a design boundary, not an obstacle.** The behavior at that boundary is scripted — see § Native connectors — capability model.
- **Alternate routes are offered, never improvised.** If the plugin owner wants a second route (say, a self-run Google MCP server for in-place writes), it enters the build the same way the first one did: an entry in `.mcp.json`, a row in `CONNECTORS.md`, a line in the I/O contract. The runtime never picks a route the build didn't declare.

Integration recipes under `integrations/` ship a ready-made contract block for their product (see `integrations/google-drive/io-contract.md`); a plugin wiring a category by hand writes its own to the same shape.
```

- [ ] **Step 3: Verify insertion and cross-reference integrity**

Run: `grep -n "^## " ~/files/repo/claude-skills/claude-cowork-builder/references/connectors-and-mcp.md`
Expected: `## Route binding — one category, one route` appears between `## The ~~category system` and `## CONNECTORS.md — the lookup table`.

Note: this section forward-references `integrations/google-drive/io-contract.md`, created in Task 4. That's acceptable within one plan; Task 7's final check confirms the file exists.

- [ ] **Step 4: Commit**

```bash
cd ~/files/repo/claude-skills && git add claude-cowork-builder/references/connectors-and-mcp.md && git commit -m "feat(claude-cowork-builder): connectors — exclusive route binding per category"
```

---

### Task 2: Capability-boundary behavior rule in the native-connectors section

**Files:**
- Modify: `claude-cowork-builder/references/connectors-and-mcp.md` § `## Native connectors — capability model` (currently lines 189–195; line numbers will have shifted after Task 1 — anchor on text, not numbers)

**Interfaces:**
- Consumes: `§ Route binding — one category, one route` (Task 1).
- Produces: the boundary-behavior bullet, referenced by Task 3 and Task 6.

- [ ] **Step 1: Locate the anchor bullet**

Run: `grep -n "Probe capability from the tool surface" ~/files/repo/claude-skills/claude-cowork-builder/references/connectors-and-mcp.md`
Expected: one hit, inside § Native connectors — capability model.

- [ ] **Step 2: Insert the new bullet**

Insert directly after the "Probe capability from the tool surface, never by writing." bullet (before the "The exact tool surface is live Cowork behavior…" bullet):

```markdown
- **At the capability boundary, hand the action to the user — never route around it.** When the task needs something outside the connector's surface or the plugin's declared I/O contract (edit a spreadsheet cell, delete a file), the scripted response is: say plainly that this piece is the user's to do — by design, not by failure — hand them the exact action ready to paste (the full row, the cell value, the filename), confirm it landed by re-reading through the connector, then continue. Never frame the boundary as the plugin's failure or a missing tool, never name another tool that could have done the write, and never attempt one (§ Route binding — one category, one route).
```

- [ ] **Step 3: Verify**

Run: `grep -c "capability boundary" ~/files/repo/claude-skills/claude-cowork-builder/references/connectors-and-mcp.md`
Expected: at least 1. Read the full § Native connectors section once to confirm the bullet order reads: capability facts → design rule → probe rule → boundary behavior → Cowork-gate note.

- [ ] **Step 4: Commit**

```bash
cd ~/files/repo/claude-skills && git add claude-cowork-builder/references/connectors-and-mcp.md && git commit -m "feat(claude-cowork-builder): connectors — scripted hand-off at the capability boundary"
```

---

### Task 3: Scripted edit flow for user-owned config in skill-authoring.md

**Files:**
- Modify: `claude-cowork-builder/references/skill-authoring.md` § `## Where mutable state lives` (consequences list, currently lines 156–160)

**Interfaces:**
- Consumes: `connectors-and-mcp.md` § Route binding (Task 1) and the boundary bullet (Task 2).
- Produces: the "scripted edit flow" consequence, referenced by audit item 15 (Task 6).

- [ ] **Step 1: Locate the anchor**

Run: `grep -n "Consequences to surface in the design" ~/files/repo/claude-skills/claude-cowork-builder/references/skill-authoring.md`
Expected: one hit (currently line 156).

- [ ] **Step 2: Append a consequence bullet**

Add as the final bullet of that consequences list (after the "immutable versioned snapshots" bullet):

```markdown
- **"Plugin reads, never writes" is a flow to script, not a fact to state.** Wherever the user can ask for a config change mid-session ("add a site", "change my brief", "pause that one"), the skill body scripts the hand-off: give the user the exact edit ready to paste (the full row or cell value), wait, re-read the config through the connector to confirm it landed, then proceed. An unscripted edit request is an improvisation magnet — the runtime will hunt the session for some other tool that can write (`connectors-and-mcp.md` § Route binding — one category, one route). Set the expectation at onboarding too: tell the user up front which pieces they own and edit themselves, before they ever ask.
```

- [ ] **Step 3: Verify**

Run: `grep -n "improvisation magnet" ~/files/repo/claude-skills/claude-cowork-builder/references/skill-authoring.md`
Expected: one hit inside § Where mutable state lives.

- [ ] **Step 4: Commit**

```bash
cd ~/files/repo/claude-skills && git add claude-cowork-builder/references/skill-authoring.md && git commit -m "feat(claude-cowork-builder): authoring — user-owned config gets a scripted edit hand-off"
```

---

### Task 4: Google Drive I/O contract fragment + recipe wiring

**Files:**
- Create: `claude-cowork-builder/integrations/google-drive/io-contract.md`
- Modify: `claude-cowork-builder/integrations/google-drive/recipe.md` (the "four things" intro at lines 7–11, the `## Steps` list, and `## Drive production facts (verified 2026-07)`)

**Interfaces:**
- Consumes: `connectors-and-mcp.md` § Route binding (Task 1).
- Produces: `io-contract.md` — the file Task 1's closing paragraph forward-references; recipe step 5.

- [ ] **Step 1: Create `io-contract.md`**

Full file content:

```markdown
# Google I/O contract — copyable block

Ship this block into the consuming plugin's main `SKILL.md` (its own `## Google I/O contract` section, or folded into `## Guardrails`). Edit the operations list to the plugin's real designed surface — every operation it performs, and only those. The fences below are not editable boilerplate; keep them verbatim.

This is the per-product concretization of `references/connectors-and-mcp.md` § Route binding — one category, one route.

---

## Google I/O contract

All Google access in this plugin goes through the user's Google Drive connector (`~~file storage`) — no other route, in any session.

The complete list of operations this plugin performs through it:

- Read the `<config sheet name>` Sheet (all tabs).
- Open the folder at `folder_url` and list its contents.
- Create dated files (report Docs, exports) in the `<subfolder>/` subfolder.

Everything else is out of scope by design. In particular, this plugin never edits or deletes anything in Drive, and never writes to the config Sheet — the user owns it; when they ask for a config change, hand them the exact row or cell to paste, confirm by re-reading the Sheet, then continue.

Never, in any session, for any reason:

- Drive a browser or browser extension against `drive.google.com`, `docs.google.com`, or `sheets.google.com` — not to write, not to read, not to check.
- Read or write a "Google Drive for Desktop" locally-synced folder as a way to reach Drive.
- Fetch Drive/Docs/Sheets URLs with a generic web-fetch tool.
- Suggest any of those routes to the user as something that would have worked, or report their absence as a failure — a capability the connector lacks is a design boundary, not a missing tool.
```

- [ ] **Step 2: Update the recipe's shipped-contents intro**

In `recipe.md`, replace:

```markdown
This recipe ships four things, all in this folder: `mcp-fragment.json` (the
server entry), `connectors-row.md` (the CONNECTORS.md table row), and two
starter skills (`skills/read-drive-file/`, `skills/find-in-drive/`) that
give the plugin a working `~~file storage` command/knowledge pair on day
one.
```

with:

```markdown
This recipe ships five things, all in this folder: `mcp-fragment.json` (the server entry), `connectors-row.md` (the CONNECTORS.md table row), `io-contract.md` (the Google I/O contract block for the consuming plugin's SKILL.md), and two starter skills (`skills/read-drive-file/`, `skills/find-in-drive/`) that give the plugin a working `~~file storage` command/knowledge pair on day one.
```

- [ ] **Step 3: Add recipe step 5**

Append to the `## Steps` list in `recipe.md`, after step 4:

```markdown
5. **Add the Google I/O contract to the main skill.**
   Copy the contract block out of `io-contract.md` into the consuming plugin's main `SKILL.md` and edit its operations list to the plugin's real designed surface. The fence lines (browser/extension, synced folder, web fetch) stay verbatim. This block is what audit item 15 checks for (`references/audit-checklist.md`).
```

- [ ] **Step 4: Add the production fact**

Append to `## Drive production facts (verified 2026-07)` in `recipe.md`:

```markdown
- **Unfenced sessions tool-shop.** Observed live (2026-07): asked to add a config row the connector can't write, a runtime reached for the Chrome browser extension, found it unconnected, and reported that absence to the user as the plugin's failure. The I/O contract block (`io-contract.md`) plus the scripted edit hand-off (`references/skill-authoring.md` § Where mutable state lives) exist to close exactly this.
```

- [ ] **Step 5: Verify**

Run: `grep -rn "io-contract" ~/files/repo/claude-skills/claude-cowork-builder/ | grep -v "\.git"`
Expected: hits in `connectors-and-mcp.md` (Task 1's closing paragraph), `recipe.md` (intro + step 5 + production fact), and the file itself.

- [ ] **Step 6: Commit**

```bash
cd ~/files/repo/claude-skills && git add claude-cowork-builder/integrations/google-drive/ && git commit -m "feat(claude-cowork-builder): google-drive recipe ships an I/O contract block"
```

---

### Task 5: Route fences in the two starter skills

**Files:**
- Modify: `claude-cowork-builder/integrations/google-drive/skills/read-drive-file/SKILL.md` (the `**With ~~file storage connected.**` paragraph in `## Rules`, currently lines 32–34)
- Modify: `claude-cowork-builder/integrations/google-drive/skills/find-in-drive/SKILL.md` (the `## With ~~file storage connected` section, currently lines 36–41)

**Interfaces:**
- Consumes: `connectors-and-mcp.md` § Route binding (Task 1).

- [ ] **Step 1: Add the fence to `read-drive-file`**

In `## Rules`, directly after the paragraph beginning `**With ~~file storage connected.** Fetch the file through the connected source…` (and before the format list), insert:

```markdown
The connected source is the *only* route. If the file can't be reached through it, the answer is the standalone fallback (upload or paste) — never a browser or extension against the product's web UI, never a locally-synced mirror folder, never a generic web fetch of its URLs (`connectors-and-mcp.md` § Route binding — one category, one route).
```

- [ ] **Step 2: Add the fence to `find-in-drive`**

At the end of `## With ~~file storage connected`, append:

```markdown
The connected source is the only search route — if it can't be searched this session, use the standalone fallback (ask for an upload or paste); never a browser, an extension, a synced folder, or a web fetch of the product's URLs.
```

- [ ] **Step 3: Verify**

Run: `grep -rn "only route\|only search route" ~/files/repo/claude-skills/claude-cowork-builder/integrations/google-drive/skills/`
Expected: one hit per skill.

- [ ] **Step 4: Commit**

```bash
cd ~/files/repo/claude-skills && git add claude-cowork-builder/integrations/google-drive/skills/ && git commit -m "feat(claude-cowork-builder): starter skills — connector is the only route"
```

---

### Task 6: Audit item 15 — route binding fenced

**Files:**
- Modify: `claude-cowork-builder/references/audit-checklist.md` (append after item 14)

**Interfaces:**
- Consumes: `connectors-and-mcp.md` § Route binding (Task 1), boundary bullet (Task 2), scripted-edit-flow bullet (Task 3).

- [ ] **Step 1: Append the item**

After item 14 (`**State writes are connector-safe.**`), append:

```markdown
15. **Route binding fenced.** Every connector category a skill body references has an I/O contract block in the consuming plugin's main skill body: the complete list of operations the plugin performs through that category, plus named fences against the alternative routes (browser/extension automation of the product's web UI, locally-synced mirror folders, generic web fetch of the product's URLs) — a bare "use only the connector" is a fail. Additionally, every user-editable resource the plugin declares read-only (a config sheet, a settings doc) has a scripted edit hand-off somewhere in the skill body — the exact edit given to the user, confirmed by re-read — not just a "the plugin never writes it" statement. See `connectors-and-mcp.md` § Route binding — one category, one route and `skill-authoring.md` § Where mutable state lives.
```

- [ ] **Step 2: Verify numbering and cross-references**

Run: `grep -n "^[0-9]*\." ~/files/repo/claude-skills/claude-cowork-builder/references/audit-checklist.md | tail -3`
Expected: items 13, 14, 15 in order.

Run: `grep -n "Route binding — one category, one route" ~/files/repo/claude-skills/claude-cowork-builder/references/*.md`
Expected: hits in `connectors-and-mcp.md` (the heading + Task 2's bullet) and `audit-checklist.md` (item 15).

- [ ] **Step 3: Commit**

```bash
cd ~/files/repo/claude-skills && git add claude-cowork-builder/references/audit-checklist.md && git commit -m "feat(claude-cowork-builder): audit — item 15, route binding fenced"
```

---

### Task 7: Changelog + final consistency pass

**Files:**
- Modify: `claude-cowork-builder/CHANGELOG.md` (new version section at top, keep-a-changelog format matching the existing file)

- [ ] **Step 1: Final cross-reference sweep**

Run each; every expectation must hold before the changelog is written:

- `test -f ~/files/repo/claude-skills/claude-cowork-builder/integrations/google-drive/io-contract.md && echo OK` → `OK` (Task 1's forward-reference resolves).
- `grep -c "§ Route binding" ~/files/repo/claude-skills/claude-cowork-builder/references/skill-authoring.md` → ≥ 1.
- `grep -rn "Route binding" ~/files/repo/claude-skills/claude-cowork-builder/ | grep -v "\.git" | wc -l` → ≥ 6 (heading, Task 2 bullet, Task 3 bullet, io-contract.md, both starter-skill fences or recipe references; investigate if lower).
- Read the new § Route binding section and audit item 15 back to back: the operation-list requirement and the fence-list wording must agree (same three named routes).

- [ ] **Step 2: Add the changelog entry**

Match the existing `CHANGELOG.md` version/heading format (read the top of the file first; bump the minor version from whatever is current). Entry content:

```markdown
### Added
- Route binding — one category, one route (`connectors-and-mcp.md`): a `~~category` is an exclusive binding; alternative routes (browser/extension, synced folders, web fetch) are fenced by name; alternate routes are declared, never improvised.
- Capability-boundary hand-off (`connectors-and-mcp.md` § Native connectors): out-of-surface actions go to the user as a scripted exact-edit hand-off, confirmed by re-read — never framed as failure, never routed around.
- Scripted edit flow for user-owned config (`skill-authoring.md` § Where mutable state lives): "plugin reads, never writes" must ship as a flow, not a statement.
- Google Drive recipe now ships `io-contract.md`, a copyable Google I/O contract block; recipe step 5 wires it into the consuming plugin's SKILL.md; starter skills carry one-line route fences.
- Audit item 15: route binding fenced.

### Production origin
- sitecheck live session 2026-07-23: runtime reached for the Chrome extension to write a Sheet row the native connector can't, and reported the extension's absence as the plugin's failure.
```

- [ ] **Step 3: Commit**

```bash
cd ~/files/repo/claude-skills && git add claude-cowork-builder/CHANGELOG.md && git commit -m "docs(claude-cowork-builder): changelog — route binding, capability-boundary hand-off, io-contract"
```

---

## Out of scope (deliberately)

- **Applying any of this to sitecheck** — happens at the project level in a separate session, after these builder changes land (per the decision of 2026-07-23). The sitecheck round will consume audit item 15 and `io-contract.md` directly.
- **The artifact-determinism work** (sitecheck bugs-3 item 2: `--artifact` mode, assembly instruction, self-verify loop) — separately planned; it touches `live-artifacts.md`, not the connector docs.
- **Other integrations** (Slack, Gmail): § Route binding is written generically and the recipe pattern (`io-contract.md`) is reusable, but authoring their concrete contract fragments waits until one is actually needed.
