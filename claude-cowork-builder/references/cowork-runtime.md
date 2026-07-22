# Cowork runtime — where plugins actually run

Facts from Anthropic's Cowork support collection (https://support.claude.com/en/collections/19667525-claude-cowork, checked 2026-07-22; per-section article IDs cited). These are runtime realities every emitted plugin inherits. Product surface moves fast — re-verify against the collection before relying on a fact here in a dispute.

## Sessions: remote by default, local when needed (14479288, 15520349)

Cowork runs on desktop (macOS/Windows), web, and mobile. Sessions run **remotely** on Anthropic infrastructure on all platforms — each session gets an isolated, temporary sandbox, created at session start and destroyed at end. That's what makes background continuation and scheduled tasks work. **Local sessions** run in an isolated VM on the user's device (Apple Virtualization.framework on macOS, Hyper-V on Windows).

What that means concretely:

- **Local file access is bounded by connected folders**, and each local tool call is permission-checked. A remote session reaches local folders only while the Claude Desktop app is open on that computer, over an Anthropic-brokered connection.
- **Remote-session network egress is allow-listed.** All traffic leaves through a mandatory proxy the sandbox can't reconfigure or bypass; Enterprise defaults to no network at all. A remote `http`/`sse` connector your plugin declares is not guaranteed reachable in every org.
- **Connector calls happen server-side in remote sessions** — authorization tokens never enter the sandbox. Good for plugin authors: you never handle tokens; env-var references in `.mcp.json` are configuration, not runtime secrets your skill touches.
- **Local MCP servers don't run in remote sessions.** See the stdio caveat in `connectors-and-mcp.md` — this is the single biggest portability trap for a plugin.

## Platform matrix (15520349)

| Capability | Desktop | Web | Mobile |
|---|---|---|---|
| Start/steer tasks, resume across surfaces | yes | yes | yes |
| Local files, local connectors, browser use | yes | via desktop app | via desktop app |
| Live Artifacts | yes (only) | no | no |
| Computer use | research preview | no | no |
| Scheduled tasks | yes (run remotely) | yes | yes |

Design floor: a plugin should be fully useful from web/mobile — which means connector-fed or paste/upload-fed, not local-folder-dependent. The standalone+supercharged rule (`skill-authoring.md`) already enforces most of this.

## Scheduled tasks — plugins are a first-class target (13854387)

Scheduled tasks run recurring or on-demand work and *"have access to the same capabilities as regular Cowork tasks, including connected tools, skills, and installed plugins."* Recurring briefs, reports, and summaries — the flagship Cowork use case — can and should be built as plugin command skills.

Constraints that change how you author a schedulable skill:

- **They run remotely** — on cadence even when the computer is asleep or the app is closed. A task that requires local files or apps runs locally only.
- **They can't be tied to a local folder.** They work with connectors and files saved to the user's Claude account.
- Users configure: name, prompt, approval mode, frequency, model, optional folder. Beta, paid plans.

**Rules for a skill meant to be schedulable:**

1. No working-folder guard — the MANDATORY FIRST STEP block (`skill-authoring.md`) would dead-end every scheduled run.
2. Outputs surface as **session deliverables** (preview/download in the session), not files at a told path. Say the file's name and what it contains; don't fabricate a filesystem path.
3. Inputs come from connectors or the prompt itself — there is no user mid-run to paste content. The standalone floor still applies at authoring time (the skill must also work interactively with zero connectors), but the *scheduled* path should name its `~~category` sources explicitly.

## Computer use — exists, never depend on it (14128542)

Computer use in Cowork lets Claude control the user's actual computer — clicking, typing, opening apps, *"no sandbox between Claude and your applications"* — gated by per-app approval prompts and default blocklists. It is a **research preview**, Pro/Max plans, desktop only.

Rule for emitted plugins: **author as if it doesn't exist.** The `open`/`xdg-open` ban and tell-the-user-the-path rule stand — not because opening things is impossible everywhere, but because a plugin that depends on a gated, plan-limited preview feature breaks for most of its users. If computer use happens to be active, Claude may use it at runtime on its own judgment; plugin instructions never require it.

## Approval modes and trust (13364135)

Three modes: **Manually approve** (recommended for sensitive files/accounts or hard-to-undo actions), **Automatically approve** (Claude safety-reviews each action, blocks or asks), **Skip all approvals**. Two constants regardless of mode:

- **File deletion always prompts.** Don't design a skill flow that hinges on silently deleting or replacing the user's files — expect an interruption there.
- Users are told to evaluate a plugin's requested permissions before installing, and extensions run with the same permissions as any local program. Keep the README's connector and env-var story complete and honest (`audit-checklist.md` item 9) — it's the trust surface a cautious user actually reads.

(Live Artifacts are the exception to the approval model: they read connectors without prompts — `live-artifacts.md` §2.)

## Projects — no plugin scoping exists (14116274)

Projects group tasks into workspaces with their own **instructions**, **context** (folder/chat/URL), **memory** (project-scoped, doesn't transfer), and **scheduled tasks**. There is **no documented plugin-to-project scoping** — plugins are install-wide. Don't design per-project plugin behavior or invent a scoping mechanism; per-project tailoring belongs in project instructions, which compose with your skill's behavior at runtime for free.
