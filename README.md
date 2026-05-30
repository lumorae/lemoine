# lemoine

Source for `lemoine-explosion-github.js`.

## Working from mobile

The High Spirits chats you run on your **desktop** (Claude Code in the terminal or
IDE, connected to Framer over MCP) are **local sessions** — they run on your machine
and aren't uploaded, so they don't appear on your phone. The Claude app and
`claude.ai/code` only show **cloud sessions**.

To chime in from your phone:

- **Keep Framer working:** run `claude remote-control` in the desktop session, then
  open the printed URL / QR on your phone. The desktop keeps running Framer + MCP.
- **Always-on, persistent:** start the work as a cloud session at `claude.ai/code`
  (it syncs to your phone), accepting that the cloud container has no Framer MCP.

Full explanation and the hybrid workflow: [docs/mobile-access.md](docs/mobile-access.md).
