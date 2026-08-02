#!/usr/bin/env python3
"""Generate a lemoine lower-third overlay (.mov with alpha) in the brand style.

Matches the lemoine-lower3-* templates (colors sampled from the BT.709-tagged
originals): #181818 charcoal box, #D54664 coral dot, Outfit Light text in brand
cream. Blocky left-to-right pixel wipe in/out, edge blocks jitter while
settling, and pixels flake off the box and fall with per-particle gravity —
same energy as the site's lemon-explosion effect.

Usage:
  python3 make_lower3.py --text "high spirits – 432hz spanish cedar" \
      --orientation both --outdir out/
"""
import argparse
import hashlib
import math
import os
import random
import subprocess

from PIL import Image, ImageDraw, ImageFont

FPS = 30
DURATION = 6.5
N_FRAMES = int(round(FPS * DURATION))

CHARCOAL = (24, 24, 24, 255)          # box, sampled from template
CORAL = (213, 70, 100, 255)           # dot, sampled from template
CREAM = (243, 239, 225, 255)          # #F3EFE1 brand cream
# digitalPalette from lemoine-explosion-github.js
PALETTE = [
    (204, 54, 102), (242, 56, 107), (245, 112, 66), (230, 173, 56),
    (82, 173, 133), (56, 143, 199), (122, 92, 199), (224, 122, 173),
    (199, 140, 115), (140, 166, 140), (242, 207, 200), (243, 239, 225),
]

# geometry measured off lemoine-lower3-walnut-flute-key-of-a templates
GEOM = {
    "landscape": dict(size=(1920, 1080), box_x=96, box_bottom=993, box_h=85,
                      dot_dx=37, dot_r=4, text_dx=59, font_size=35, pad_right=36),
    "vertical": dict(size=(1080, 1920), box_x=64, box_bottom=1593, box_h=101,
                     dot_dx=41, dot_r=5, text_dx=69, font_size=42, pad_right=41),
}

WIPE_IN = (0.15, 1.05)
WIPE_OUT = (5.15, 6.05)


def h01(*key):
    d = hashlib.md5(":".join(str(k) for k in key).encode()).digest()
    return d[0] / 255.0


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def wipe_progress(t, span):
    a, b = span
    if t <= a:
        return 0.0
    return smoothstep((t - a) / (b - a))


class Faller:
    """A pixel block detaching from the box and falling under gravity."""

    def __init__(self, rng, x, y, t0, chunky_bias=0.0):
        self.t0 = t0
        self.x0 = x
        self.y0 = y
        self.vx = rng.uniform(-18, 18)
        self.vy = rng.uniform(4, 38)
        self.g = rng.uniform(180, 720)          # different paces
        self.vterm = rng.uniform(110, 520)
        self.life = rng.uniform(1.3, 3.0)
        r = rng.random() - chunky_bias
        if r < 0.62:
            self.s = rng.randint(3, 6)
        elif r < 0.9:
            self.s = rng.randint(7, 10)
        else:
            self.s = rng.randint(11, 16)
        cr = rng.random()
        if cr < 0.42:
            self.c = CHARCOAL[:3]               # flakes of the box itself
        elif cr < 0.52:
            self.c = CORAL[:3]
        elif cr < 0.60:
            self.c = CREAM[:3]
        else:
            self.c = PALETTE[rng.randrange(len(PALETTE))]

    def pos(self, t):
        a = t - self.t0
        if a < 0 or a > self.life:
            return None
        # integrate capped-velocity fall analytically enough for the eye
        t_cap = max(0.0, (self.vterm - self.vy) / self.g)
        ta = min(a, t_cap)
        y = self.y0 + self.vy * ta + 0.5 * self.g * ta * ta
        if a > t_cap:
            y += self.vterm * (a - t_cap)
        x = self.x0 + self.vx * a
        fade = 1.0 - smoothstep((a / self.life - 0.55) / 0.45) if a / self.life > 0.55 else 1.0
        return x, y, fade


def build(text, orientation, font_path, outdir, basename=None, keep_frames=False):
    g = GEOM[orientation]
    W, H = g["size"]
    font = ImageFont.truetype(font_path, g["font_size"])

    label = f"[ {text} ]"
    bb = font.getbbox(label)
    box_w = g["text_dx"] + (bb[2] - bb[0]) + g["pad_right"]
    box_h = g["box_h"]
    box_x, box_y = g["box_x"], g["box_bottom"] - box_h
    cy = box_y + box_h / 2

    design = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(design)
    d.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=CHARCOAL)
    dx, r = box_x + g["dot_dx"], g["dot_r"]
    d.ellipse([dx - r, cy - r, dx + r, cy + r], fill=CORAL)
    d.text((box_x + g["text_dx"], cy), label, font=font, anchor="lm", fill=CREAM)

    cell = max(10, round(box_h / 6))            # chunkier pixels
    cols = math.ceil((box_w + 2) / cell)
    rows = math.ceil((box_h + 2) / cell)

    rng = random.Random(432)
    fallers = []
    # wipe-in: blocks shake loose under the traveling edge
    for i in range(cols):
        u = (i + 0.5) / cols
        t_edge = WIPE_IN[0] + u * (WIPE_IN[1] - WIPE_IN[0])
        for _ in range(rng.choice([0, 1, 1, 2])):
            fallers.append(Faller(rng, box_x + u * box_w + rng.uniform(-8, 8),
                                  box_y + box_h - 2, t_edge + rng.uniform(0, 0.25)))
    # hold: an organic trickle flaking off the bottom edge
    t = WIPE_IN[1]
    while t < WIPE_OUT[0]:
        t += rng.uniform(0.10, 0.45)
        fallers.append(Faller(rng, box_x + rng.uniform(4, box_w - 4),
                              box_y + box_h - 2, t))
    # wipe-out: heavier shed, chunkier
    for i in range(cols):
        u = (i + 0.5) / cols
        t_edge = WIPE_OUT[0] + u * (WIPE_OUT[1] - WIPE_OUT[0])
        for _ in range(rng.choice([1, 2, 2, 3])):
            fallers.append(Faller(rng, box_x + u * box_w + rng.uniform(-10, 10),
                                  box_y + rng.uniform(box_h * 0.4, box_h),
                                  t_edge + rng.uniform(0, 0.2), chunky_bias=0.18))

    frame_dir = os.path.join(outdir, f"frames-{orientation}")
    os.makedirs(frame_dir, exist_ok=True)

    for n in range(N_FRAMES):
        t = n / FPS
        p_in = wipe_progress(t, WIPE_IN)
        p_out = wipe_progress(t, WIPE_OUT)

        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if p_in > 0 and p_out < 1:
            # jitter only while a wipe is actually running — never during hold
            wipe_active = t <= WIPE_IN[1] + 0.1 or t >= WIPE_OUT[0] - 0.1
            mask = Image.new("L", (W, H), 0)
            md = ImageDraw.Draw(mask)
            edge_cells = []                     # cells mid-transition jitter
            for i in range(cols):
                xc = (i + 0.5) / cols
                for j in range(rows):
                    thr = xc * 0.75 + 0.25 * h01(i, j, "w")
                    on = (p_in >= thr) and not (p_out > 0 and p_out >= thr)
                    if not on:
                        continue
                    x0 = box_x + i * cell
                    y0 = box_y + j * cell
                    x1 = min(x0 + cell, box_x + box_w)
                    y1 = min(y0 + cell, box_y + box_h)
                    if x1 <= x0 or y1 <= y0:
                        continue
                    settling = wipe_active and (
                        (p_in - thr) < 0.12 or (0 < p_out and (thr - p_out) < 0.12))
                    if settling:
                        edge_cells.append((x0, y0, x1, y1, i, j))
                    else:
                        md.rectangle([x0, y0, x1, y1], fill=255)
            # displaced settling blocks go UNDER the settled design so they
            # never eat into legible text
            for x0, y0, x1, y1, i, j in edge_cells:
                jx = int((h01(i, j, n, "jx") - 0.5) * cell * 0.9)
                jy = int((h01(i, j, n, "jy") - 0.5) * cell * 0.9)
                block = design.crop((x0, y0, x1, y1))
                frame.paste(block, (x0 + jx, y0 + jy), block)
            frame.paste(design, (0, 0), mask)

        pd = ImageDraw.Draw(frame)
        for f in fallers:
            p = f.pos(t)
            if p is None:
                continue
            x, y, fade = p
            if y > H:
                continue
            c = (*f.c, int(235 * fade))
            pd.rectangle([x, y, x + f.s, y + f.s], fill=c)

        frame.save(os.path.join(frame_dir, f"f{n:04d}.png"))

    name = basename or f"lemoine-lower3-{text.replace(' ', '-')}-{W}x{H}-alpha"
    name = "".join(ch for ch in name if ch.isalnum() or ch in "-_")
    out_mov = os.path.join(outdir, name + ".mov")
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
    ap.add_argument("--text", required=True, help="lower-third text, without brackets")
    ap.add_argument("--orientation", choices=["landscape", "vertical", "both"], default="both")
    ap.add_argument("--font", default=os.path.join(os.path.dirname(__file__), "Outfit-300.ttf"))
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--keep-frames", action="store_true")
    args = ap.parse_args()

    todo = ["landscape", "vertical"] if args.orientation == "both" else [args.orientation]
    for o in todo:
        print(build(args.text, o, args.font, args.outdir, keep_frames=args.keep_frames))
