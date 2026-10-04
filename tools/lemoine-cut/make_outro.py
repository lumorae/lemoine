#!/usr/bin/env python3
"""Generate the lemoine pixel-explosion outro overlay (.mov with alpha).

Plays AFTER the footage ends (the pipeline freezes the last frame under it):
the frame dissolves into charcoal cell by cell while pixels fall with
per-particle gravity, then particles gather into the end-card's lemon mark and
wordmark, the tagline pixelates in, and the URL pill lands last. The end-card
artwork comes straight from the brand SVGs (endcards/), rasterized 1:1.

Usage:
  python3 make_outro.py --endcard endcards/endcard-dont-blend-in-1080x1920.png \
      --name dont-blend-in --outdir out/
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

import brand

FPS = 30
DURATION = 6.2
N_FRAMES = int(round(FPS * DURATION))

CHARCOAL = (25, 25, 25)
PALETTE = [
    (204, 54, 102), (242, 56, 107), (245, 112, 66), (230, 173, 56),
    (82, 173, 133), (56, 143, 199), (122, 92, 199), (224, 122, 173),
    (199, 140, 115), (140, 166, 140), (242, 207, 200), (243, 239, 225),
]

DISSOLVE = (0.0, 1.8)      # footage -> charcoal
GATHER = (1.3, 3.6)        # particles -> lemon + wordmark
LOGO_SOLID = 3.7
TAG_REVEAL = (3.5, 4.05)   # tagline pixelates in
PILL_REVEAL = (3.85, 4.4)  # url pill pixelates in
# y boundaries between end-card layers (logo | tagline | url pill), in the
# 1080x1920 card these were measured from. A card of another shape puts its
# bands somewhere else, so they are defaults rather than constants: the
# landscape card passes its own, carried through the same transform that
# re-framed the artwork. Getting these wrong does not error, it just animates
# the wrong slice of the card, so they travel with the card that needs them.
LAYER_SPLIT_TAG = 1050
LAYER_SPLIT_PILL = 1250


def h01(*key):
    d = hashlib.md5(":".join(str(k) for k in key).encode()).digest()
    return d[0] / 255.0


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)




def dissolve_field(W, H, seed_salt, cell=12):
    """Cell threshold grid for a pixelated-but-organic dissolve.

    Timing flows in cloud-shaped patches, but the medium stays crisp square
    cells — no per-pixel mist. Returns (grid float32 (rows, cols), cell).
    """
    rng = np.random.default_rng(abs(hash(seed_salt)) % (2 ** 31))
    cols, rows = math.ceil(W / cell), math.ceil(H / cell)
    clouds = Image.fromarray((rng.random((max(2, rows // 16), max(2, cols // 16))) * 255
                              ).astype(np.uint8)).resize((cols, rows), Image.BILINEAR)
    th = 0.72 * np.asarray(clouds, np.float32) / 255.0 + 0.28 * rng.random((rows, cols)).astype(np.float32)
    # a few straggler cells hang on a beat longer — organic, not uniform
    th += (rng.random((rows, cols)) < 0.08) * 0.07
    th -= th.min()
    th /= max(th.max(), 1e-6)
    return (0.02 + 0.93 * th).astype(np.float32), cell


def dissolve_alpha(grid, cell, W, H, p, appearing, soft=0.055):
    """Upsample the cell grid to a crisp per-pixel alpha for progress p."""
    if appearing:
        a = np.clip((p - grid) / soft, 0, 1)
    else:
        a = np.clip((grid - p) / soft + 1, 0, 1)
    a8 = (a * 255).astype(np.uint8)
    full = np.kron(a8, np.ones((cell, cell), dtype=np.uint8))
    return full[:H, :W]


def charcoal_layer(W, H, alpha_arr):
    """Opaque-charcoal RGBA layer with a per-pixel alpha array (uint8)."""
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 0] = CHARCOAL[0]
    arr[..., 1] = CHARCOAL[1]
    arr[..., 2] = CHARCOAL[2]
    arr[..., 3] = alpha_arr
    return Image.fromarray(arr)


def extract_logo(template, work):
    """Grab the clean final logo frame from the brand outro template (intro uses this)."""
    frame = os.path.join(work, "logo.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "6.0", "-i", template,
                    "-frames:v", "1", frame], check=True)
    im = Image.open(frame).convert("RGB")
    a = np.asarray(im).astype(int)
    bg = np.median(a[a.shape[0] // 10, :], axis=0)
    mask = (np.abs(a - bg).sum(axis=2) > 40)
    return im, mask


def layer_image(px, mask, W, H, y0, y1):
    m = np.zeros_like(mask)
    m[y0:y1] = mask[y0:y1]
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., :3] = px
    arr[..., 3] = np.where(m, 255, 0)
    return Image.fromarray(arr), m


def blocky_reveal(frame, layer_img, cells, p, n, acell):
    """Site-style pixelate-in of a layer, with settle jitter on fresh cells."""
    if p <= 0:
        return
    if p >= 1:
        frame.alpha_composite(layer_img)
        return
    W, H = layer_img.size
    lmask = Image.new("L", (W, H), 0)
    lmd = ImageDraw.Draw(lmask)
    for i, j in cells:
        appear = 0.02 + smoothstep(h01(i, j, "rv")) * 0.92
        if p >= appear:
            x0, y0 = i * acell, j * acell
            fresh = (p - appear) < 0.1
            jx = int((h01(i, j, n, "rx") - 0.5) * 8) if fresh else 0
            jy = int((h01(i, j, n, "ry") - 0.5) * 8) if fresh else 0
            lmd.rectangle([x0 + jx, y0 + jy, x0 + acell + jx, y0 + acell + jy], fill=255)
    part = layer_img.copy()
    part.putalpha(Image.composite(layer_img.split()[3], Image.new("L", layer_img.size, 0), lmask))
    frame.alpha_composite(part)


def build(endcard, outdir, name, keep_frames=False,
          split_tag=LAYER_SPLIT_TAG, split_pill=LAYER_SPLIT_PILL):
    card = Image.open(endcard).convert("RGB")
    W, H = card.size
    px = np.asarray(card)
    bg = np.array(CHARCOAL)
    mask = (np.abs(px.astype(int) - bg).sum(axis=2) > 30)

    logo_img, logo_mask = layer_image(px, mask, W, H, 0, split_tag)
    tag_img, tag_mask = layer_image(px, mask, W, H, split_tag, split_pill)
    pill_img, pill_mask = layer_image(px, mask, W, H, split_pill, H)

    # particle targets for the lemon + wordmark gather
    rng = random.Random(1919)
    step = 5
    ys, xs = np.where(logo_mask)
    cx, cy = xs.mean(), ys.mean()
    targets = []
    for y in range(0, split_tag, step):
        for x in range(0, W, step):
            if logo_mask[y:y + step, x:x + step].mean() > 0.3:
                c = tuple(int(v) for v in px[min(y + step // 2, H - 1), min(x + step // 2, W - 1)])
                sx = cx + (x - cx) * rng.uniform(1.6, 3.4) + rng.uniform(-90, 90)
                sy = cy + (y - cy) * rng.uniform(1.6, 3.4) + rng.uniform(-140, 90)
                targets.append(dict(tx=x, ty=y, sx=sx, sy=sy, c=c,
                                    t0=GATHER[0] + rng.uniform(0, 0.9),
                                    dur=rng.uniform(0.7, 1.3)))

    # blocky reveal grids for tagline and pill
    acell = 10
    def grid_cells(m):
        cells = []
        for i in range(math.ceil(W / acell)):
            for j in range(math.ceil(H / acell)):
                if m[j * acell:(j + 1) * acell, i * acell:(i + 1) * acell].mean() > 0.02:
                    cells.append((i, j))
        return cells
    tag_cells = grid_cells(tag_mask)
    pill_cells = grid_cells(pill_mask)

    # pixel dissolve grid + falling dust released as each patch turns (brand ramps)
    grid, dcell = dissolve_field(W, H, "outro-" + name)
    SOFT = 0.055
    fallers = []
    for _ in range(380):
        fx_, fy_ = rng.uniform(0, W - 1), rng.uniform(0, H - 1)
        flip = DISSOLVE[0] + float(grid[int(fy_ // dcell), int(fx_ // dcell)]) * (DISSOLVE[1] - DISSOLVE[0])
        fallers.append(dict(
            x=fx_, y=fy_,
            vx=rng.uniform(-18, 18), vy=rng.uniform(4, 30),
            g=rng.uniform(120, 620), vterm=rng.uniform(110, 480),
            t0=flip + rng.uniform(0, 0.2), life=rng.uniform(1.0, 2.4),
            s=rng.choice([2, 3, 3, 4, 4, 5, 7]),
            c=brand.pick(rng, coral=0.38, charcoal=0.32, cream=0.25),
        ))

    frame_dir = os.path.join(outdir, f"frames-outro-{name}")
    os.makedirs(frame_dir, exist_ok=True)

    for n in range(N_FRAMES):
        t = n / FPS
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # particles layer
        fxd = ImageDraw.Draw(fx)

        # 1) footage dissolves to charcoal — crisp cells, organic cloud timing
        p = (t - DISSOLVE[0]) / (DISSOLVE[1] - DISSOLVE[0]) * (1 + SOFT)
        if t >= DISSOLVE[1]:
            d.rectangle([0, 0, W, H], fill=(*CHARCOAL, 255))
        elif p > 0:
            frame.alpha_composite(charcoal_layer(W, H, dissolve_alpha(grid, dcell, W, H, p, appearing=True, soft=SOFT)))

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
            fxd.rectangle([x, y, x + f["s"], y + f["s"]], fill=(*f["c"], int(235 * fade)))

        # 3) lemon + wordmark: particles gather, then the exact artwork
        if t >= LOGO_SOLID:
            k = smoothstep((t - LOGO_SOLID) / 0.3)
            if k >= 1:
                frame.alpha_composite(logo_img)
            else:
                tmp = logo_img.copy()
                tmp.putalpha(tmp.split()[3].point(lambda v: int(v * k)))
                frame.alpha_composite(tmp)
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
                    fxd.rectangle([x, y, x + s, y + s], fill=(*tg["c"], alpha))

        frame.alpha_composite(fx)

        # 4) tagline, then the url pill, pixelate in
        blocky_reveal(frame, tag_img, tag_cells,
                      (t - TAG_REVEAL[0]) / (TAG_REVEAL[1] - TAG_REVEAL[0]), n, acell)
        blocky_reveal(frame, pill_img, pill_cells,
                      (t - PILL_REVEAL[0]) / (PILL_REVEAL[1] - PILL_REVEAL[0]), n, acell)

        frame.save(os.path.join(frame_dir, f"f{n:04d}.png"))

    out_mov = os.path.join(outdir, f"lemoine-outro-pixel-{name}-{W}x{H}-alpha.mov")
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
    ap.add_argument("--endcard", required=True, help="end-card PNG (from endcards/*.svg)")
    ap.add_argument("--name", required=True, help="variant name for the output file")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--keep-frames", action="store_true")
    ap.add_argument("--split-tag", type=int, default=LAYER_SPLIT_TAG,
                    help="y where the tagline band starts in this end-card")
    ap.add_argument("--split-pill", type=int, default=LAYER_SPLIT_PILL,
                    help="y where the url pill band starts in this end-card")
    args = ap.parse_args()
    print(build(args.endcard, args.outdir, args.name, keep_frames=args.keep_frames,
                split_tag=args.split_tag, split_pill=args.split_pill))
