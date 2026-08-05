# Cowork runtime — where plugins actually run

Facts from Anthropic's Cowork support collection (https://support.claude.com/en/collections/19667525-claude-cowork; per-section article IDs cited). Articles 14479288, 15520349, 13345190, 14729249, 13854387, and 14128542 checked 2026-08-05. Articles 13364135 (approval modes) and 14116274 (projects) were last checked 2026-07-22 and are carried forward unverified. Install surfaces come from article 13837440, "Use plugins in Claude" (updated 2026-05-29) — it sits outside the Cowork collection index, which is why collection-scoped sweeps miss it. These are runtime realities every emitted plugin inherits. Product surface moves fast — re-verify against the collection before relying on a fact here in a dispute.

## Sessions: remote by default, local when needed (14479288, 15520349)

Cowork runs on desktop (macOS/Windows), web, and mobile. Sessions run in the cloud on Anthropic infrastructure **by default**, and the cloud model itself is **in beta** — each session gets an isolated, temporary sandbox, created at session start and destroyed at end. That's what makes background continuation and scheduled tasks work. **Local execution remains available for existing desktop deployments**: a local session runs in an isolated VM on the user's device (Apple Virtualization.framework on macOS, Hyper-V on Windows). Author for the cloud default; treat local execution as the legacy path, not the one to design around.

What that means concretely:

- **Local file access is bounded by connected folders**, and each local tool call is permission-checked. A remote session reaches local folders only while the Claude Desktop app is open on that computer, over an Anthropic-brokered connection.
- **Remote-session network egress is allow-listed.** All traffic leaves through a mandatory proxy the sandbox can't reconfigure or bypass; Enterprise defaults to no network at all. A remote `http`/`sse` connector your plugin declares is not guaranteed reachable in every org.
- **Connector calls happen server-side in remote sessions** — authorization tokens never enter the sandbox; the sandbox holds only session-scoped tokens that expire within hours. Good for plugin authors: you never handle tokens; env-var references in `.mcp.json` are configuration, not runtime secrets your skill touches. It is also why a plugin must never try to persist a credential it observed at runtime — the thing it captured is already expiring.
- **Local MCP servers don't run in remote sessions.** See the stdio caveat in `connectors-and-mcp.md` — this is the single biggest portability trap for a plugin.

## Platform matrix (15520349)

| Capability | Desktop | Web | Mobile |
|---|---|---|---|
| Start/steer tasks, resume across surfaces | yes | yes | yes |
| Connectors | yes | yes | yes |
| Skills and plugins | yes | yes | yes |
| Preview created files | yes | yes | yes |
| Projects | yes | yes | yes |
| Scheduled tasks | yes (run remotely) | yes | yes |
| Local files, local connectors, browser use | yes | via desktop app | via desktop app |
| Computer use (research preview) | yes | via desktop app | via desktop app |
| Live Artifacts | yes (only) | no | no |

Design floor: a plugin should be fully useful from web/mobile — which means connector-fed or paste/upload-fed, not local-folder-dependent. The standalone+supercharged rule (`skill-authoring.md`) already enforces most of this.

## Scheduled tasks — plugins are a first-class target (13854387)

Scheduled tasks run recurring or on-demand work and *"have access to the same capabilities as regular Cowork tasks, including connected tools, skills, and installed plugins."* Recurring briefs, reports, and summaries — the flagship Cowork use case — can and should be built as plugin command skills.

Constraints that change how you author a schedulable skill:

- **They run remotely** — on cadence even when the computer is asleep or the app is closed. A task that requires local files or apps runs locally only.
- **They can't be tied to a local folder.** They work with connectors and files saved to the user's Claude account.
- Users configure: name, prompt, approval mode, frequency (hourly, daily, weekly, weekdays, or manual), model, optional folder.
- Available on **all paid plans** — Pro, Max, Team, Enterprise. The *beta* label belongs to Cowork on web and mobile (rolling out starting with Max), not to scheduled tasks themselves; don't tell a user their scheduled task is a beta feature.

**Rules for a skill meant to be schedulable:**

1. No working-folder guard — the MANDATORY FIRST STEP block (`skill-authoring.md`) would dead-end every scheduled run.
2. Outputs surface as **session deliverables** (preview/download in the session), not files at a told path. Say the file's name and what it contains; don't fabricate a filesystem path.
3. Inputs come from connectors or the prompt itself — there is no user mid-run to paste content. The standalone floor still applies at authoring time (the skill must also work interactively with zero connectors), but the *scheduled* path should name its `~~category` sources explicitly.

## Computer use — exists, never depend on it (14128542)

Computer use in Cowork lets Claude control the user's actual computer — clicking, typing, opening apps, *"no sandbox between Claude and your applications"* — gated by per-app approval prompts and default blocklists (which cover investment/trading and cryptocurrency apps out of the box). It is a **research preview**, Pro/Max plans, and requires the desktop app running — web and mobile reach it only through that app. Team and Enterprise plans have no access to computer use at all, which is most of the audience a distributed plugin lands in front of.

Rule for emitted plugins: **author as if it doesn't exist.** The `open`/`xdg-open` ban and tell-the-user-the-path rule stand — not because opening things is impossible everywhere, but because a plugin that depends on a gated, plan-limited preview feature breaks for most of its users. If computer use happens to be active, Claude may use it at runtime on its own judgment; plugin instructions never require it.

## Probe the real path — capability checks that don't lie

Two production facts about egress make settings-based inference worthless:

- **The Settings → Capabilities "network access" toggle does not govern a plugin's own fetch path.** It gates Claude's open-ended browsing tools (web fetch / web search). A bundled subprocess (curl, a Python fetcher) egresses through the sandbox proxy regardless — a plugin can work with the toggle off and fail with it on. A skill can't read the toggle anyway.
- **The sandbox proxy can reset specific TLS client fingerprints** while passing others — so a probe using a different client than the real fetch path can false-negative (or false-positive). If the plugin bundles a fetch layer with its own retry/impersonation logic, the probe must run through that same layer.

The rule: **capability truth comes from one honest probe of the exact path the plugin uses** — front-loaded (an egress failure is the one restart-class problem a user can't fix mid-session), run once per session, silent on success. Never infer capability from settings a skill can't read, environment sniffing, or product documentation. If the probe isn't the same code path as the real work, its answer is about a different question.

## Approval modes and trust (13364135)

Three modes: **Manually approve** (recommended for sensitive files/accounts or hard-to-undo actions), **Automatically approve** (Claude safety-reviews each action, blocks or asks), **Skip all approvals**. Two constants regardless of mode:

- **File deletion always prompts.** Don't design a skill flow that hinges on silently deleting or replacing the user's files — expect an interruption there.
- Users are told to evaluate a plugin's requested permissions before installing, and extensions run with the same permissions as any local program. Keep the README's connector and env-var story complete and honest (`audit-checklist.md` item 9) — it's the trust surface a cautious user actually reads.

(Live Artifacts are the exception to the approval model: a user approves connectors once, at creation or update, and the artifact then uses those connectors without prompting — even in a session mode that would normally require approval. `live-artifacts.md` §2.)

## How plugins actually get installed (13837440)

The user-facing path is **Customize menu → Plugins tab → Browse plugins → Install**, and *"plugins you add yourself are saved locally to your computer"* — install is per-machine, not per-account. Three ways a plugin reaches that list:

- **A curated marketplace.** Anthropic ships four: Knowledge Work, Life Sciences, Financial Services, and Legal. Nothing this builder emits appears there without publishing to one.
- **A marketplace the user adds** — *"Sync from GitHub repository or git URL"*, straight from the Plugins tab. This is the Cowork-native equivalent of Claude Code's `/plugin marketplace add`, and it is what makes the self-marketplace layout (`distribution.md` §4) install cleanly in both clients.
- **A custom plugin file** — *"upload a custom plugin file if you built one yourself."* This is the `.plugin` upload path (`distribution.md` §6).

Consequences for what you emit: the README's install instructions should name the Plugins tab rather than a vague "app settings"; a private plugin that is its own git repo is installable from **both** clients without a file hand-off; and because installs are local to a machine, a plugin cannot assume state or config follows a user across devices.

## Projects — no plugin scoping exists (14116274)

Projects group tasks into workspaces with their own **instructions**, **context** (folder/chat/URL), **memory** (project-scoped, doesn't transfer), and **scheduled tasks**. There is **no documented plugin-to-project scoping** — plugins are install-wide. Don't design per-project plugin behavior or invent a scoping mechanism; per-project tailoring belongs in project instructions, which compose with your skill's behavior at runtime for free.
