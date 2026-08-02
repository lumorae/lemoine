#!/usr/bin/env python3
"""Generate the lemoine pixel-explosion outro overlay (.mov with alpha).

Plays AFTER the footage ends (the pipeline freezes the last frame under it):
the frame dissolves into charcoal cell by cell while pixels fall with
per-particle gravity, then particles gather into the Lemoine logo — taken
verbatim from the original brand outro template's final frame — and hold.

Usage:
  python3 make_outro.py --template lemoine-outro-vertical-1080x1920-alpha-iphone.mov \
      --outdir out/
"""
import argparse
import hashlib
import math
import os
import random
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw

FPS = 30
DURATION = 5.2
N_FRAMES = int(round(FPS * DURATION))

CHARCOAL = (25, 25, 25)
PALETTE = [
    (204, 54, 102), (242, 56, 107), (245, 112, 66), (230, 173, 56),
    (82, 173, 133), (56, 143, 199), (122, 92, 199), (224, 122, 173),
    (199, 140, 115), (140, 166, 140), (242, 207, 200), (243, 239, 225),
]

DISSOLVE = (0.0, 1.8)     # footage -> charcoal
GATHER = (1.3, 3.6)       # particles -> logo
LOGO_SOLID = 3.7          # exact logo from here on


def h01(*key):
    d = hashlib.md5(":".join(str(k) for k in key).encode()).digest()
    return d[0] / 255.0


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def extract_logo(template, work):
    """Grab the clean final logo frame from the brand outro template."""
    frame = os.path.join(work, "logo.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "6.0", "-i", template,
                    "-frames:v", "1", frame], check=True)
    im = Image.open(frame).convert("RGB")
    a = np.asarray(im).astype(int)
    bg = np.median(a[a.shape[0] // 10, :], axis=0)  # top strip = background
    mask = (np.abs(a - bg).sum(axis=2) > 40)
    return im, mask


def build(template, outdir, keep_frames=False):
    work = tempfile.mkdtemp()
    logo_im, logo_mask = extract_logo(template, work)
    W, H = logo_im.size
    logo_px = np.asarray(logo_im)

    # particle targets: logo sampled on a coarse pixel grid
    step = 5
    targets = []
    rng = random.Random(1919)
    ys, xs = np.where(logo_mask)
    x0m, x1m, y0m, y1m = xs.min(), xs.max(), ys.min(), ys.max()
    for y in range(0, H, step):
        for x in range(0, W, step):
            block = logo_mask[y:y + step, x:x + step]
            if block.mean() > 0.3:
                c = tuple(int(v) for v in logo_px[min(y + step // 2, H - 1), min(x + step // 2, W - 1)])
                # scatter start: inflated logo bbox
                cx, cy = (x0m + x1m) / 2, (y0m + y1m) / 2
                sx = cx + (x - cx) * rng.uniform(1.6, 3.4) + rng.uniform(-90, 90)
                sy = cy + (y - cy) * rng.uniform(1.6, 3.4) + rng.uniform(-140, 90)
                targets.append(dict(
                    tx=x, ty=y, sx=sx, sy=sy, c=c,
                    t0=GATHER[0] + rng.uniform(0, 0.9),
                    dur=rng.uniform(0.7, 1.3),
                ))

    # dissolve grid + falling pixels
    cell = max(24, H // 48)
    cols, rows = math.ceil(W / cell), math.ceil(H / cell)
    fallers = []
    for i in range(cols):
        for j in range(rows):
            # min 0.05 keeps frame 0 fully transparent (overlay extends it backward)
            flip = DISSOLVE[0] + (0.05 + smoothstep(h01(i, j, "flip")) * 0.85) * (DISSOLVE[1] - DISSOLVE[0])
            if rng.random() < 0.5:
                fallers.append(dict(
                    x=i * cell + rng.uniform(0, cell), y=j * cell + cell,
                    vx=rng.uniform(-22, 22), vy=rng.uniform(6, 44),
                    g=rng.uniform(180, 760), vterm=rng.uniform(130, 560),
                    t0=flip, life=rng.uniform(0.9, 2.2),
                    s=rng.choice([3, 4, 4, 5, 6, 8, 10]),
                    c=CHARCOAL if rng.random() < 0.35 else PALETTE[rng.randrange(len(PALETTE))],
                ))

    solid_logo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    solid_arr = np.zeros((H, W, 4), dtype=np.uint8)
    solid_arr[..., :3] = logo_px
    solid_arr[..., 3] = np.where(logo_mask, 255, 0)
    solid_logo = Image.fromarray(solid_arr)

    frame_dir = os.path.join(outdir, "frames-outro")
    os.makedirs(frame_dir, exist_ok=True)

    for n in range(N_FRAMES):
        t = n / FPS
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)

        # 1) dissolve: cells flip to opaque charcoal in organic order
        p = (t - DISSOLVE[0]) / (DISSOLVE[1] - DISSOLVE[0])
        if t >= DISSOLVE[1]:
            d.rectangle([0, 0, W, H], fill=(*CHARCOAL, 255))
        elif p > 0:
            for i in range(cols):
                for j in range(rows):
                    flip = 0.05 + smoothstep(h01(i, j, "flip")) * 0.85
                    if p >= flip:
                        x0, y0 = i * cell, j * cell
                        jitter = (p - flip) < 0.08
                        jx = int((h01(i, j, n, "x") - 0.5) * 6) if jitter else 0
                        jy = int((h01(i, j, n, "y") - 0.5) * 6) if jitter else 0
                        d.rectangle([x0 + jx, y0 + jy, x0 + cell + jx, y0 + cell + jy],
                                    fill=(*CHARCOAL, 255))

        # 2) falling pixels
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

        # 3) logo: particles gather, then the exact template logo
        if t >= LOGO_SOLID:
            k = smoothstep((t - LOGO_SOLID) / 0.3)
            if k >= 1:
                frame.paste(solid_logo, (0, 0), solid_logo)
            else:
                tmp = solid_logo.copy()
                tmp.putalpha(tmp.split()[3].point(lambda v: int(v * k)))
                frame.paste(tmp, (0, 0), tmp)
        if GATHER[0] <= t < LOGO_SOLID + 0.3:
            fadeout = 1.0 if t < LOGO_SOLID else 1.0 - smoothstep((t - LOGO_SOLID) / 0.3)
            for tg in targets:
                a = (t - tg["t0"]) / tg["dur"]
                if a < 0:
                    continue
                e = smoothstep(a)
                x = tg["sx"] + (tg["tx"] - tg["sx"]) * e
                y = tg["sy"] + (tg["ty"] - tg["sy"]) * e
                s = 3 + 2 * e
                alpha = int(255 * min(1.0, 0.25 + 0.75 * e) * fadeout)
                if alpha > 3:
                    d.rectangle([x, y, x + s, y + s], fill=(*tg["c"], alpha))

        frame.save(os.path.join(frame_dir, f"f{n:04d}.png"))

    out_mov = os.path.join(outdir, f"lemoine-outro-pixel-{W}x{H}-alpha.mov")
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
    ap.add_argument("--template", required=True, help="original brand outro .mov (logo source)")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--keep-frames", action="store_true")
    args = ap.parse_args()
    print(build(args.template, args.outdir, keep_frames=args.keep_frames))
