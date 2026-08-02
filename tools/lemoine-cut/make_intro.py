#!/usr/bin/env python3
"""Generate the lemoine pixel-explosion intro overlay (.mov with alpha).

Opens fully opaque: charcoal + the Lemoine logo (taken verbatim from the brand
outro template's final frame). The logo bursts into particles, then the
charcoal dissolves cell by cell — pixels falling with per-particle gravity —
revealing the footage underneath. Final frames are fully transparent.

Usage:
  python3 make_intro.py --template lemoine-outro-vertical-1080x1920-alpha-iphone.mov \
      --outdir out/
"""
import argparse
import math
import os
import random
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw

from make_outro import extract_logo, h01, smoothstep, CHARCOAL, PALETTE

FPS = 30
DURATION = 3.4
N_FRAMES = int(round(FPS * DURATION))

LOGO_HOLD = 1.0           # solid logo on charcoal
BURST = (1.0, 2.0)        # logo particles fly apart
DISSOLVE = (1.25, 3.0)    # charcoal -> footage


def build(template, outdir, keep_frames=False):
    work = tempfile.mkdtemp()
    logo_im, logo_mask = extract_logo(template, work)
    W, H = logo_im.size
    logo_px = np.asarray(logo_im)

    solid_arr = np.zeros((H, W, 4), dtype=np.uint8)
    solid_arr[..., :3] = logo_px
    solid_arr[..., 3] = np.where(logo_mask, 255, 0)
    solid_logo = Image.fromarray(solid_arr)

    rng = random.Random(2432)
    step = 5
    ys, xs = np.where(logo_mask)
    cx, cy = xs.mean(), ys.mean()
    shards = []
    for y in range(0, H, step):
        for x in range(0, W, step):
            if logo_mask[y:y + step, x:x + step].mean() > 0.3:
                c = tuple(int(v) for v in logo_px[min(y + step // 2, H - 1), min(x + step // 2, W - 1)])
                ang = math.atan2(y - cy, x - cx) + rng.uniform(-0.5, 0.5)
                spd = rng.uniform(90, 420)
                shards.append(dict(
                    x=x, y=y, c=c,
                    vx=math.cos(ang) * spd, vy=math.sin(ang) * spd - rng.uniform(0, 80),
                    g=rng.uniform(220, 700),
                    t0=BURST[0] + rng.uniform(0, 0.35),
                    life=rng.uniform(0.7, 1.6),
                    s=rng.choice([3, 4, 4, 5, 6]),
                ))

    cell = max(24, H // 48)
    cols, rows = math.ceil(W / cell), math.ceil(H / cell)
    fallers = []
    for i in range(cols):
        for j in range(rows):
            drop = DISSOLVE[0] + (0.03 + smoothstep(h01(i, j, "idrop")) * 0.9) * (DISSOLVE[1] - DISSOLVE[0])
            if rng.random() < 0.45:
                fallers.append(dict(
                    x=i * cell + rng.uniform(0, cell), y=j * cell + cell,
                    vx=rng.uniform(-22, 22), vy=rng.uniform(6, 44),
                    g=rng.uniform(180, 760), vterm=rng.uniform(130, 560),
                    t0=drop, life=rng.uniform(0.8, 1.8),
                    s=rng.choice([3, 4, 4, 5, 6, 8, 10]),
                    c=CHARCOAL if rng.random() < 0.35 else PALETTE[rng.randrange(len(PALETTE))],
                ))

    frame_dir = os.path.join(outdir, "frames-intro")
    os.makedirs(frame_dir, exist_ok=True)

    for n in range(N_FRAMES):
        t = n / FPS
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)

        # charcoal base dissolving away (cells flip to transparent)
        p = (t - DISSOLVE[0]) / (DISSOLVE[1] - DISSOLVE[0])
        if t < DISSOLVE[0]:
            d.rectangle([0, 0, W, H], fill=(*CHARCOAL, 255))
        elif t < DISSOLVE[1] + 0.2:
            for i in range(cols):
                for j in range(rows):
                    drop = 0.03 + smoothstep(h01(i, j, "idrop")) * 0.9
                    if p < drop:
                        x0, y0 = i * cell, j * cell
                        jitter = (drop - p) < 0.08
                        jx = int((h01(i, j, n, "x") - 0.5) * 6) if jitter else 0
                        jy = int((h01(i, j, n, "y") - 0.5) * 6) if jitter else 0
                        d.rectangle([x0 + jx, y0 + jy, x0 + cell + jx, y0 + cell + jy],
                                    fill=(*CHARCOAL, 255))

        # falling pixels shed by dissolving cells
        for f in fallers:
            a = t - f["t0"]
            if a < 0 or a > f["life"]:
                continue
            t_cap = max(0.0, (f["vterm"] - f["vy"]) / f["g"])
            ta = min(a, t_cap)
            y = f["y"] + f["vy"] * ta + 0.5 * f["g"] * ta * ta
            if a > t_cap:
                y += f["vterm"] * (a - t_cap)
            x = f["x"] + f["vx"] * a
            if y > H:
                continue
            fade = 1.0 - smoothstep((a / f["life"] - 0.5) / 0.5) if a / f["life"] > 0.5 else 1.0
            d.rectangle([x, y, x + f["s"], y + f["s"]], fill=(*f["c"], int(235 * fade)))

        # logo: solid, then bursting outward with gravity
        if t < BURST[0]:
            frame.paste(solid_logo, (0, 0), solid_logo)
        else:
            k = smoothstep((t - BURST[0]) / 0.25)
            if k < 1:
                tmp = solid_logo.copy()
                tmp.putalpha(tmp.split()[3].point(lambda v: int(v * (1 - k))))
                frame.paste(tmp, (0, 0), tmp)
            for sh in shards:
                a = t - sh["t0"]
                if a < 0 or a > sh["life"]:
                    continue
                x = sh["x"] + sh["vx"] * a
                y = sh["y"] + sh["vy"] * a + 0.5 * sh["g"] * a * a
                if not (-20 < x < W + 20 and y < H + 20):
                    continue
                fade = 1.0 - smoothstep((a / sh["life"] - 0.4) / 0.6) if a / sh["life"] > 0.4 else 1.0
                d.rectangle([x, y, x + sh["s"], y + sh["s"]], fill=(*sh["c"], int(245 * fade)))

        frame.save(os.path.join(frame_dir, f"f{n:04d}.png"))

    out_mov = os.path.join(outdir, f"lemoine-intro-pixel-{W}x{H}-alpha.mov")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
        "-i", os.path.join(frame_dir, "f%04d.png"),
        "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
        out_mov,
    ], check=True)
    if not keep_frames:
        for f in os.listdir(frame_dir):
            os.remove(os.path.join(frame_dir, f))
        os.rmdir(frame_dir)
    return out_mov


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, help="brand outro .mov (logo source)")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--keep-frames", action="store_true")
    args = ap.parse_args()
    print(build(args.template, args.outdir, keep_frames=args.keep_frames))
