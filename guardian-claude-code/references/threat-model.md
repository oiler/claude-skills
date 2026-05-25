# Threat Model

What `guardian-claude-code` protects against, and what it doesn't.

## In scope

1. **Compromised package update.** A trusted MCP server or plugin pushes an update within hours of an attacker gaining publish access. Detected by the 7-day `cooldown` signal.
2. **Capability expansion attack.** An existing trusted item updates and adds new tools, hooks, or permissions (e.g., a "docs reader" suddenly requesting shell exec). Detected by `capability_diff`. Highest-signal category.
3. **Typosquatting / repo hijack.** An MCP's declared README/repo URL doesn't match the actual install source. Detected by `url_mismatch`.
4. **Maintainer change.** Ownership of an npm/PyPI package transferred recently — the "I sold my package" attack vector. Detected by `maintainer_change`.
5. **Silent drift between sessions.** A new MCP server, plugin, or hook appeared without conscious approval — possibly added by another skill or via a settings.json merge. Detected by `new_item` + `removed_item`.

## Out of scope

- **Runtime exploitation of installed tools.** Guardian audits trust at install/update time, not runtime behavior. A malicious MCP that passed the audit can still misuse the tools you granted it.
- **Application-code vulnerabilities.** Covered by `web-security`.
- **OS-level privilege escalation.** Outside the Claude Code threat surface.
- **Network-level attacks** (MITM on registry/GitHub API calls). Mitigated by registry HTTPS but not actively defended against.
- **CLAUDE.md / settings.json hygiene.** Covered by `advisor-claude-code`.
- **Account-level claude.ai MCP connectors.** Not enumerable from local config; the skill prints a reminder to review them via `/mcp`.
- **Generic PyPI/npm packages used by your application code.** Handled at the package-manager level (e.g., uv cooldown).

## Trust assumptions

- The 7-day cooldown protects against drive-by compromise but does not protect against attackers who plant a malicious package and wait. Capability-diff catches that next layer.
- Registry APIs (npm, PyPI, GitHub) are trusted to return accurate metadata. If they're compromised or lying, all downstream signals are unreliable.
- The local snapshot file is trusted as the source of "what was here last time". If it's tampered with, all diff-based signals are unreliable. Treat `~/.claude/guardian/snapshot.json` like any other security-critical file on your system.
