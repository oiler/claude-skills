---
name: AGENT_NAME
description: >
  What this agent does and when to dispatch it.
  <example>
  Context: …
  user: "…"
  assistant: "…"
  <commentary>Why this triggers the agent.</commentary>
  </example>
model: sonnet
color: cyan   # corpus convention, not a documented field — the runtime ignores it, and no validator catches it either
maxTurns: 15
tools: [Read, Glob, Grep]
---

System prompt: instructions for the agent's autonomous job. Output contract: return … .

<!-- Also supported on a plugin agent, all optional: `effort`, `disallowedTools`
     (the negative counterpart to `tools`), `skills`, `memory`, `background`,
     `isolation`. FORBIDDEN on a plugin-shipped agent, for security reasons:
     `hooks`, `mcpServers`, `permissionMode`. See references/agent-playbook.md §3. -->

