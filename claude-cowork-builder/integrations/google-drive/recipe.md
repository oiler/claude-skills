# Recipe: Google Drive integration

Drop-in recipe for wiring the `~~file storage` category into any Cowork
plugin, backed by Google Drive. Use this from menu entry 2 (Add an
integration) — it jumps straight to Phase 3/4, no re-charter needed.

This recipe ships four things, all in this folder: `mcp-fragment.json` (the
server entry), `connectors-row.md` (the CONNECTORS.md table row), and two
starter skills (`skills/read-drive-file/`, `skills/find-in-drive/`) that
give the plugin a working `~~file storage` command/knowledge pair on day
one.

**From-scratch builds (menu entry 1):** the merge language below assumes an
existing plugin. When the recipe rides along on a new scaffold, there's
nothing to merge — the fragment becomes the initial `.mcp.json`, the row
becomes the initial `CONNECTORS.md` table content, and steps 1–2 collapse
to "use as-is."

**Why tokens even though private:** the starter skills ship
`~~file storage`-tokenized bodies plus `CONNECTORS.md` although private
plugins may hardcode product names and skip `CONNECTORS.md` entirely
(`distribution.md` §3). Deliberate — it makes a later flip to Public a
metadata change instead of a re-tokenizing pass. A private build may still
swap the tokens for concrete names if oiler prefers; do it in all four
sync locations at once.

## Steps

1. **Merge the MCP server into the plugin's `.mcp.json`.**
   Copy the `google-drive` entry out of `mcp-fragment.json` into the
   target plugin's `.mcp.json`, under `mcpServers`. If the plugin already
   has other servers, add this as a sibling key — don't replace the file.

2. **Add the connectors row.**
   Copy the row from `connectors-row.md` into the target plugin's
   `CONNECTORS.md`, under the existing table. If `CONNECTORS.md` doesn't
   have a `~~file storage` row yet, this is that row. If one already
   exists (e.g. the plugin already ships Dropbox under the same category),
   merge the "Included servers" cell instead of adding a duplicate row —
   `File storage | ~~file storage | Google Drive, Dropbox | Box, OneDrive`
   — rather than two rows for one category. Copy the `*` footnote too, if
   not already present.

3. **Copy the two starter skills into `skills/`.**
   Copy `skills/read-drive-file/` and `skills/find-in-drive/` wholesale
   into the target plugin's `skills/` directory. They're already written
   to the command/knowledge templates and use the `~~file storage` token,
   so no renaming is needed unless the plugin already has a
   differently-named category for file storage — in that case, rename the
   `~~file storage` token in both skill bodies (and the CONNECTORS row) to
   match, per the four-places-in-sync rule in `connectors-and-mcp.md`.

4. **Resolve the build-time endpoint decision.**
   `mcp-fragment.json` ships as an **empty-url stub** —
   `"url": ""` — because this recipe doesn't hardcode a specific Cowork
   Google Drive connector URL. At build time, pick one:
   - **Real URL known:** replace `""` with the current Cowork Google
     Drive connector URL, and drop the `*` from the connectors row (the
     server is live, not a placeholder).
   - **Real URL not known:** leave the stub as-is and keep the `*`
     footnote in `CONNECTORS.md`. This is not a broken state — the plugin
     still packages and installs, and both starter skills already have a
     standalone fallback that works with zero connector configured.

## Going public with this recipe

The starter skills name Google Drive in their `description` frontmatter —
deliberate, and correct for the private default lean, because "Drive" is
what users actually type. If the host plugin goes Public, genericize those
descriptions along with everything else: drop "Google Drive"/"Drive"
phrasing to category language ("connected file storage") in the same pass
that genericizes skill bodies (`distribution.md` §4, `connectors-and-mcp.md`
§ `~~` tokens and descriptions).

## Standalone fallback

Neither starter skill hard-depends on Google Drive being connected. When
`~~file storage` isn't wired up (stub URL, or the plugin owner hasn't
authorized it yet), both skills fall back to asking the user to upload or
paste the file/content directly into the chat. Confirm this fallback still
reads cleanly after any renaming in step 3 — it's the floor every copy of
this recipe must clear, connected or not.

## Drive production facts (verified 2026-07)

Facts from running a Drive-backed plugin in real Cowork sessions — they bound what a consumer of this recipe can design:

- **The native Drive connector is create-and-read only.** No file update, no delete, no Sheets cell writes. Follow the append-only design rule in `connectors-and-mcp.md` § Native connectors — capability model. A self-run Google MCP server (this recipe's route) is the opt-in power path for in-place writes — never a requirement.
- **Workspace Shared Drives are unreachable through the native connector** — requests omit `supportsAllDrives` / `includeItemsFromAllDrives` / `corpora=allDrives`, so reads come back empty or 404 (anthropics/claude-code#53442). Until fixed, a team's shared home is a **My Drive folder shared with the team**. Accept a pasted folder URL agnostically so a Shared Drive URL "just works" once the connector supports it.
- **The Drive-for-Desktop sync trap:** if the user points their *working folder* at a locally-synced Google Drive folder, sync conflicts can replace files with stub JSON. Onboarding copy should steer the working folder to a plain local folder, not a synced one.
