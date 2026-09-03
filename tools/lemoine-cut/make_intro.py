#!/usr/bin/env python3
"""Generate the lemoine pixel-explosion intro overlay (.mov with alpha).

The above-the-fold moment from johnnylemoine.com, as a video intro:
charcoal opens empty, the logo pixelates in cell by cell, holds a beat, then
EXPLODES the way the site's lemon does — a radial burst of rotating squares in
the digital palette, chunky blocks crumbling through a 4x4 sub-cell dissolve
(the exact mechanic in lemoine-explosion-github.js) — while the charcoal
dissolves through to the footage. Every particle then arcs over and falls out
of frame under gravity and air. Nothing pops off; the overlay only ends after
the last pixel has left the screen.

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

from make_outro import (extract_logo, h01, smoothstep, CHARCOAL, PALETTE,
                        dissolve_field, dissolve_alpha, charcoal_layer)

import brand

FPS = 30
DURATION = 7.0
N_FRAMES = int(round(FPS * DURATION))
SAFETY_FADE = (6.3, 6.85)   # ease any straggler out while it is still moving

ASSEMBLE = (0.15, 1.35)   # logo pixelates in, like the site's above-the-fold logo
BURST_AT = 2.0            # logo explodes (site lemon-press moment)
DISSOLVE = (2.2, 3.9)     # charcoal -> footage

def _rot3(px, py, pz, ax, ay):
    """Rotate a 3D point around x then y; return projected (x, y) and depth."""
    cy_, sy_ = math.cos(ay), math.sin(ay)
    cx_, sx_ = math.cos(ax), math.sin(ax)
    y2 = py * cx_ - pz * sx_
    z2 = py * sx_ + pz * cx_
    x3 = px * cy_ + z2 * sy_
    z3 = -px * sy_ + z2 * cy_
    return x3, y2, z3


_CUBE_V = [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
_CUBE_EDGES = [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6),
               (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]
_CUBE_FACES = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4),
               (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]


class Shard:
    """A burst particle with site-explosion character and real-world exit.

    Radial launch, rotation, gravity arc with terminal velocity and air wobble.
    Chunky shards crumble through a 4x4 sub-cell dissolve while flying, down to
    a last few cells that ride until they leave the frame.
    """

    def __init__(self, rng, x, y, cx, cy, color):
        self.x0, self.y0 = x, y
        ang = math.atan2(y - cy, x - cx) + rng.uniform(-0.45, 0.45)
        spd = rng.uniform(120, 780)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd - rng.uniform(40, 220)   # a lift of energy
        self.t0 = BURST_AT + rng.uniform(0, 0.3)
        r = rng.random()
        if r < 0.55:
            self.s = rng.randint(3, 6)
        elif r < 0.85:
            self.s = rng.randint(7, 11)
        else:
            self.s = rng.randint(12, 18)
        m = self.s / 18.0
        self.g = 300 + 420 * m + rng.uniform(-40, 40)
        self.vterm = 280 + 360 * m + rng.uniform(-30, 30)
        self.dead = False
        self.wob_amp = max(0.0, 8.0 - 0.45 * self.s) * rng.uniform(0.6, 1.4)
        self.wob_f = rng.uniform(0.7, 1.9) * 2 * math.pi
        self.wob_ph = rng.uniform(0, 2 * math.pi)
        self.rot0 = rng.uniform(0, math.pi)
        self.rot_w = rng.uniform(-3.0, 3.0)                    # site: rotationSpeed ±
        self.c = color
        self.seed = rng.random()
        # crumble pacing: big shards start shedding sub-cells mid-flight
        self.crumble_t0 = rng.uniform(0.5, 1.1)
        self.crumble_dur = rng.uniform(0.9, 1.8)
        # kind: flat square / solid 3d cube / wireframe cube (site cube language)
        kr = rng.random()
        self.kind = "flat" if kr < 0.62 else ("cube" if kr < 0.83 else "wire")
        if self.kind != "flat":
            self.s = max(self.s, 10)
            self.faces = brand.coral_faces(rng)
            self.rx0, self.ry0 = rng.uniform(0, math.pi), rng.uniform(0, math.pi)
            self.rwx, self.rwy = rng.uniform(-2.4, 2.4), rng.uniform(-2.4, 2.4)

    def draw(self, pd, t, W, H):
        if self.dead:
            return False
        a = t - self.t0
        if a < 0:
            return False
        # velocity integration with terminal-velocity cap on the way down
        vy_t = self.vy + self.g * a
        if vy_t > self.vterm:
            t_cap = (self.vterm - self.vy) / self.g
            y = self.y0 + self.vy * t_cap + 0.5 * self.g * t_cap ** 2 \
                + self.vterm * (a - t_cap)
        else:
            y = self.y0 + self.vy * a + 0.5 * self.g * a * a
        x = self.x0 + self.vx * a + self.wob_amp * math.sin(self.wob_f * a + self.wob_ph)
        if y > H + 24 or x < -24 or x > W + 24 or y < -24:
            # leaving any edge (including up, mid-launch) is a real exit
            self.dead = True
            return False
        alpha = 240
        if t > SAFETY_FADE[0]:
            alpha = int(240 * (1.0 - smoothstep((t - SAFETY_FADE[0]) / (SAFETY_FADE[1] - SAFETY_FADE[0]))))
            if alpha <= 2:
                return False
        if self.kind != "flat":
            ax = self.rx0 + self.rwx * a
            ay = self.ry0 + self.rwy * a
            r = self.s / 2.0
            pts = [_rot3(vx_ * r, vy_ * r, vz_ * r, ax, ay) for vx_, vy_, vz_ in _CUBE_V]
            if self.kind == "wire":
                for e0, e1 in _CUBE_EDGES:
                    pd.line([(x + pts[e0][0], y + pts[e0][1]),
                             (x + pts[e1][0], y + pts[e1][1])],
                            fill=(*self.c, alpha), width=2)
            else:
                dark, base, light = self.faces
                order = sorted(range(6), key=lambda f: sum(pts[i][2] for i in _CUBE_FACES[f]))
                for rank, f in enumerate(order[3:]):
                    col = (dark, base, light)[rank]
                    poly = [(x + pts[i][0], y + pts[i][1]) for i in _CUBE_FACES[f]]
                    pd.polygon(poly, fill=(*col, alpha))
            return True
        if self.s < 7:
            pd.rectangle([x, y, x + self.s, y + self.s], fill=(*self.c, alpha))
            return True
        # rotating square, crumbling into 4x4 sub-cells as it flies
        integrity = 1.0 - smoothstep((a - self.crumble_t0) / self.crumble_dur)
        th = self.rot0 + self.rot_w * a
        ct, st = math.cos(th), math.sin(th)
        sub = self.s / 4.0
        for ii in range(4):
            for jj in range(4):
                r = h01(int(self.seed * 1e6), ii, jj)
                if r > max(integrity, 0.12):       # last cells never vanish mid-air
                    continue
                lx = (ii - 1.5) * sub
                ly = (jj - 1.5) * sub
                px_ = x + lx * ct - ly * st
                py_ = y + lx * st + ly * ct
                pd.rectangle([px_, py_, px_ + sub, py_ + sub], fill=(*self.c, alpha))
        return True



def reframe_logo(logo_im, logo_mask, size, fill=0.34):
    """Re-centre the extracted logo on a canvas of another shape.

    The logo is lifted from the brand outro master, which is 1080x1920, so the
    intro inherits that shape unless told otherwise. Nothing about the mark is
    vertical though — only the frame is. This crops to the logo itself, scales
    it once, and re-centres it on the requested canvas, so a landscape intro is
    the same artwork in a wider frame rather than a redrawn one.

    `fill` is the logo height as a fraction of the canvas. It is lower than the
    end-card's because the intro logo stands alone with nothing beneath it.
    """
    W, H = size
    ys, xs = np.where(logo_mask)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    cw, ch = x1 - x0, y1 - y0

    scale = (H * fill) / ch
    if cw * scale > W * 0.46:
        scale = (W * 0.46) / cw
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))

    crop = logo_im.crop((x0, y0, x1, y1)).resize((nw, nh), Image.LANCZOS)
    m = Image.fromarray((logo_mask[y0:y1, x0:x1] * 255).astype(np.uint8)
                        ).resize((nw, nh), Image.LANCZOS)

    canvas = Image.new("RGB", (W, H), CHARCOAL)
    newmask = Image.new("L", (W, H), 0)
    ox, oy = (W - nw) // 2, (H - nh) // 2
    canvas.paste(crop, (ox, oy))
    newmask.paste(m, (ox, oy))
    return canvas, np.asarray(newmask) > 128


def build(template, outdir, keep_frames=False, size=None):
    work = tempfile.mkdtemp()
    logo_im, logo_mask = extract_logo(template, work)
    if size and tuple(size) != logo_im.size:
        logo_im, logo_mask = reframe_logo(logo_im, logo_mask, size)
    W, H = logo_im.size
    logo_px = np.asarray(logo_im)

    solid_arr = np.zeros((H, W, 4), dtype=np.uint8)
    solid_arr[..., :3] = logo_px
    solid_arr[..., 3] = np.where(logo_mask, 255, 0)
    solid_logo = Image.fromarray(solid_arr)

    rng = random.Random(2432)
    ys, xs = np.where(logo_mask)
    cx, cy = xs.mean(), ys.mean()

    # shards from the logo body (site colors, coral-forward, some keep logo color)
    step = 7
    shards = []
    for y in range(0, H, step):
        for x in range(0, W, step):
            if logo_mask[y:y + step, x:x + step].mean() > 0.3:
                if rng.random() < 0.45:
                    c = tuple(int(v) for v in logo_px[min(y + 3, H - 1), min(x + 3, W - 1)])
                else:
                    c = brand.pick(rng, coral=0.45, charcoal=0.12, cream=0.38)
                shards.append(Shard(rng, x, y, cx, cy, c))

    # blocky assembly grid over the logo (the site's pixelate-in dissolve)
    acell = 10
    logo_cells = []
    for i in range(math.ceil(W / acell)):
        for j in range(math.ceil(H / acell)):
            if logo_mask[j * acell:(j + 1) * acell, i * acell:(i + 1) * acell].mean() > 0.02:
                logo_cells.append((i, j))

    # pixel dissolve grid; fine dust drifts loose as each patch erodes
    grid, dcell = dissolve_field(W, H, "intro")
    SOFT = 0.055
    fallers = []
    for _ in range(440):
        fx_, fy_ = rng.uniform(0, W - 1), rng.uniform(0, H - 1)
        drop = DISSOLVE[0] + float(grid[int(fy_ // dcell), int(fx_ // dcell)]) * (DISSOLVE[1] - DISSOLVE[0])
        f = Shard(rng, fx_, fy_, W / 2, -H,
                  brand.pick(rng, coral=0.36, charcoal=0.34, cream=0.25))
        f.t0 = drop + rng.uniform(0, 0.15)
        f.vx = rng.uniform(-24, 24)
        f.vy = rng.uniform(4, 34)
        f.s = rng.choice([2, 2, 3, 3, 4, 4, 5, 6])
        f.kind = "flat"
        f.wob_amp = rng.uniform(3.0, 9.0)
        fallers.append(f)

    frame_dir = os.path.join(outdir, "frames-intro")
    os.makedirs(frame_dir, exist_ok=True)

    for n in range(N_FRAMES):
        t = n / FPS
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fxd = ImageDraw.Draw(fx)

        # charcoal erodes away to the footage — crisp cells, organic cloud timing
        p = (t - DISSOLVE[0]) / (DISSOLVE[1] - DISSOLVE[0]) * (1 + SOFT)
        if t < DISSOLVE[0]:
            d.rectangle([0, 0, W, H], fill=(*CHARCOAL, 255))
        elif p < 1 + SOFT + 0.05:
            a8 = dissolve_alpha(grid, dcell, W, H, p, appearing=False, soft=SOFT)
            if a8.max() > 0:
                frame.alpha_composite(charcoal_layer(W, H, a8))

        # logo: pixelates in cell by cell, holds, then explodes site-style
        if t < ASSEMBLE[1]:
            ap_ = (t - ASSEMBLE[0]) / (ASSEMBLE[1] - ASSEMBLE[0])
            if ap_ > 0:
                lmask = Image.new("L", (W, H), 0)
                lmd = ImageDraw.Draw(lmask)
                for i, j in logo_cells:
                    appear = 0.02 + smoothstep(h01(i, j, "asm")) * 0.92
                    if ap_ >= appear:
                        x0, y0 = i * acell, j * acell
                        fresh = (ap_ - appear) < 0.08
                        jx = int((h01(i, j, n, "ax") - 0.5) * 8) if fresh else 0
                        jy = int((h01(i, j, n, "ay") - 0.5) * 8) if fresh else 0
                        lmd.rectangle([x0 + jx, y0 + jy, x0 + acell + jx, y0 + acell + jy], fill=255)
                assembling = solid_logo.copy()
                assembling.putalpha(Image.composite(
                    solid_logo.split()[3], Image.new("L", (W, H), 0), lmask))
                frame.alpha_composite(assembling)
        elif t < BURST_AT:
            frame.alpha_composite(solid_logo)
        else:
            # the logo body breaks apart fast; shards carry it away
            k = smoothstep((t - BURST_AT) / 0.2)
            if k < 1:
                tmp = solid_logo.copy()
                tmp.putalpha(tmp.split()[3].point(lambda v: int(v * (1 - k))))
                frame.alpha_composite(tmp)
            for sh in shards:
                sh.draw(fxd, t, W, H)

        for f in fallers:
            f.draw(fxd, t, W, H)

        frame.alpha_composite(fx)
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
    ap.add_argument("--size", default=None,
                    help="target canvas WxH, e.g. 1920x1080; default is the "
                         "template's own shape")
    args = ap.parse_args()
    sz = None
    if args.size:
        sz = tuple(int(v) for v in args.size.lower().split("x"))
    print(build(args.template, args.outdir, keep_frames=args.keep_frames, size=sz))
