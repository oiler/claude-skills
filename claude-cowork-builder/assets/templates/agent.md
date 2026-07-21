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
color: cyan
maxTurns: 15
tools: [Read, Glob, Grep]
---

System prompt: instructions for the agent's autonomous job. Output contract: return … .
