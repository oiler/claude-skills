# Recipe: Google Drive integration

Drop-in recipe for wiring the `~~file storage` category into any Cowork
plugin, backed by Google Drive. Use this from menu entry 2 (Add an
integration) — it jumps straight to Phase 3/4, no re-charter needed.

This recipe ships four things, all in this folder: `mcp-fragment.json` (the
server entry), `connectors-row.md` (the CONNECTORS.md table row), and two
starter skills (`skills/read-drive-file/`, `skills/find-in-drive/`) that
give the plugin a working `~~file storage` command/knowledge pair on day
one.

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

## Standalone fallback

Neither starter skill hard-depends on Google Drive being connected. When
`~~file storage` isn't wired up (stub URL, or the plugin owner hasn't
authorized it yet), both skills fall back to asking the user to upload or
paste the file/content directly into the chat. Confirm this fallback still
reads cleanly after any renaming in step 3 — it's the floor every copy of
this recipe must clear, connected or not.
