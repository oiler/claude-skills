# PLUGIN_NAME

Designed for Claude Cowork; also works in Claude Code.

## Installation
In Claude, open the **Customize** menu → the **Plugins** tab → **Browse plugins**, then **Install**. Plugins you add yourself are saved locally to your computer.

Two ways to get this plugin into that list:

- **Upload the plugin file.** If you were handed a `.plugin` file, add it as a custom plugin from the same Plugins tab.
- **Add the marketplace it lives in.** Sync from a GitHub repository or git URL, then install it from that listing.

## Commands
| Command | What it does |
|---|---|
| /COMMAND_NAME | … |

## Standalone + Supercharged
| Works with no connectors | Supercharged when connected |
|---|---|
| … | … |

## MCP Integrations
<!-- authoring note, delete on fill: this is the "connectors this plugin uses" section audit item 6 syncs against — one line per ~~category token used anywhere in the plugin -->
- `~~file storage` (Google Drive, …): …

## Settings
<!-- authoring note, delete on fill: keep this section even with nothing to configure — write "None required" rather than dropping it. Personalization values go in the manifest's `userConfig` block: Claude prompts for them when the plugin is enabled, substitutes them as ${user_config.KEY} into .mcp.json and hook commands, and routes `sensitive: true` values to the OS keychain. Never point users at .claude/settings.json or .claude/settings.local.json — project settings files are ignored for plugin config, and the plugin's own settings.json supports only the `agent` and `subagentStatusLine` keys. -->
None required.
