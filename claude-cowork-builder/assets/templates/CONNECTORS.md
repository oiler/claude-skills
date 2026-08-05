# Connectors

## How tool references work

Plugin files use `~~category` as a placeholder for whatever tool the user connects in that category. For example, `~~file storage` might mean Google Drive, Dropbox, or any other storage service with an MCP server.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (file storage, chat, project tracker, etc.) rather than specific products. The `.mcp.json` pre-configures specific MCP servers, but any MCP server in that category works.

## Connectors for this plugin

| Category | Placeholder | Included servers | Other options |
|---|---|---|---|
| File storage | `~~file storage` | Google Drive * | Dropbox, Box, OneDrive |

\* Placeholder — MCP URL not yet configured.
