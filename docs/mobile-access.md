# Working on High Spirits from your phone

## TL;DR

The chats you run on your **desktop** (Claude Code in the terminal / IDE, bridged
to Framer over MCP) are **local sessions**. They run on your machine and are never
uploaded anywhere, so your **phone has nothing to show**. The mobile app and
`claude.ai/code` only list **cloud sessions** ("Claude Code on the web").

To participate from your phone you have two paths:

1. **Remote-control the live desktop session** — keeps Framer MCP working, desktop
   must stay on. Best for steering in-progress High Spirits work.
2. **Run the work as a cloud session** — syncs to your phone and persists, but the
   cloud container has no Framer MCP bridge.

---

## Why desktop chats don't show up on mobile

There are two different kinds of Claude Code session, and they don't share a list:

| | **Local session** (terminal / IDE / MCP) | **Cloud session** ("on the web") |
|---|---|---|
| Runs on | Your desktop machine | Anthropic-managed container |
| Visible on phone | **No** | **Yes** |
| Persists after you close it | No | Yes |
| Access to local tools & Framer MCP | **Yes** | No |
| Needs GitHub | No | Yes |

When you work on High Spirits "within Framer and MCP connect," you're in a **local
session**. The MCP connection is a live tunnel between Claude Code *on your machine*
and the Framer plugin *on your machine*. It is local-only by design — there is no
copy of that conversation in the cloud for the phone to load.

Cloud sessions are the opposite: they live on Anthropic infrastructure, so opening
`claude.ai/code` or the Claude app on any device shows the same session list. (This
session, the one writing these docs, is a cloud session — which is exactly why you
can see it on your phone.)

---

## Option 1 — Remote control (recommended for Framer work)

This exposes your **already-running local desktop session** to your phone while the
code keeps executing on the desktop, so the Framer MCP bridge stays intact.

1. On the desktop, in the running session, start remote control:
   ```
   claude remote-control
   ```
2. Open the URL it prints (or scan the QR code) on your phone — either in the
   browser at `claude.ai/code` or in the Claude app.
3. You now see the same conversation on both devices and can send messages / steer
   from the phone. The desktop continues to run Framer + MCP.

**Caveat:** the desktop terminal/process must stay open. Close it and the remote
session ends.

## Option 2 — Cloud session ("Claude Code on the web")

If you want always-on, persistent access from the phone and don't need Framer
connected for that particular task:

1. Go to `claude.ai/code`, connect this GitHub repo, and start a session.
2. It appears on your phone automatically and survives you closing the browser.

**Caveat:** the cloud container has no Framer MCP integration, so it can't drive
the Framer canvas — it's best for code/docs work, not live design steering.

## Option 3 — Hybrid (what most High Spirits work wants)

- Do the deep Framer design work in a **local** session on the desktop.
- When you want to chime in from the phone, run `claude remote-control` and keep
  the desktop process alive.
- Use **cloud sessions** for code/doc tasks that don't need Framer, since those are
  the ones that show up on your phone with no extra steps.

---

## References

- Claude Code on the web — https://code.claude.com/docs/en/claude-code-on-the-web
- Remote control — https://code.claude.com/docs/en/remote-control
- Web quickstart — https://code.claude.com/docs/en/web-quickstart
