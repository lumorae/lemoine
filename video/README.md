# Lemoine explosion → video renderer

Turns the site's logo pixel-explosion animation (`../lemoine-explosion-github.js`)
into MP4 intro/outro clips for YouTube (16:9) and Instagram reels/stories (9:16).

The animation is captured **deterministically**: the browser's clock and
`requestAnimationFrame` are virtualized, so each captured frame advances exactly
1/FPS seconds. Output is perfectly smooth even on a machine with no GPU.
A scripted virtual pointer presses and drags on the lemon to trigger the bursts.

## Setup (once)

```sh
cd video
npm install
npx playwright install chromium   # skip if Chromium is already provided (CHROMIUM_PATH)
```

## Render

```sh
npm run proof           # quick 720p30 8s check
npm run youtube-intro   # 1920x1080 @ 60fps, 10s
npm run youtube-outro   # 1920x1080 @ 60fps, 12s
npm run reel-intro      # 1080x1920 @ 60fps, 10s
npm run reel-outro      # 1080x1920 @ 60fps, 12s
```

Output lands in `video/out/`.

## Tuning

- Timing of the bursts: edit `CHOREO` in `capture.mjs` (press windows in seconds).
- Resolution/duration/fps/quality: `CAP_W`, `CAP_H`, `CAP_FPS`, `CAP_SECONDS`,
  `CAP_CRF` env vars (see `package.json` scripts).
- 4K: `CAP_W=3840 CAP_H=2160` — slower, but works the same way.
- In a managed Claude Code cloud session, point at the preinstalled browser with
  `CHROMIUM_PATH=/opt/pw-browsers/chromium` instead of running `playwright install`.

Note: the animation randomizes particle colors/trajectories per run, so every
render is a unique take — re-run until you like the take, or set a fixed seed
by stubbing `Math.random` in `harness.html` if you want reproducible output.
